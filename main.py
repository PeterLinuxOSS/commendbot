"""CommendBot entry point.

Loads every cog in ./cogs, wires up the owner-only maintenance commands and
runs the two daily cron jobs (restart alerts and the nightly counter reset).
"""

import asyncio
import datetime
import time
from itertools import cycle
from pathlib import Path

import aiocron
import asyncstdlib as a
import cooldowns
import nextcord
from nextcord import Embed, Interaction, SlashOption
from nextcord.ext import commands
from termcolor import cprint

import config
from utils import (
    can_dm_user,
    db,
    find_command,
    get_lang,
    logger,
    logo,
    utc_to_local,
)

config.validate()

CWD = Path(__file__).resolve().parent
TZ = datetime.timezone.utc
VERSION = "7.0.0"
# Balances on this slot expire; customers get one warning before the reset.
RESET_WARNING_SLOT_ID = config.RESET_WARNING_SLOT_ID
RESET_WARNING_WINDOW = datetime.timedelta(days=7)

intents = nextcord.Intents.all()
bot = commands.AutoShardedBot(
    command_prefix="c!",
    case_insensitive=True,
    owner_id=config.OWNER_ID,
    intents=intents,
)
bot.pause = True
bot.cwd = str(CWD)
bot.version = VERSION
bot.statuses = cycle([config.BRAND_NAME, "/help | 0 guilds", "Freemium Bot"])
bot.slotsready = False
bot.slottrans_ready = False


# Listed explicitly rather than globbing ./cogs: several modules there are
# mixins and view collections, not extensions, and `from cogs.helpers import *`
# leaks helpers' setup() into their namespace - globbing would load the same
# cog several times over. Comment a line out to disable that feature.
EXTENSIONS = (
    "cogs.ai",
    "cogs.bot_tasks",
    "cogs.commands",
    "cogs.commend",
    "cogs.commend_menu",
    "cogs.events",
    "cogs.helpers",
    "cogs.keygen",
    "cogs.logs",
    "cogs.news",
    "cogs.resellers",
    "cogs.rewards",
    "cogs.settings",
    "cogs.setup_c",
    "cogs.slot",
    "cogs.slottrans",
    "cogs.transactions_logs",
    "cogs.ui",
)


def load_extensions() -> None:
    for extension in EXTENSIONS:
        bot.load_extension(extension)
        print(f"loaded {extension}")


@bot.event
async def on_application_command_error(inter: nextcord.Interaction, error, *args):
    error = getattr(error, "original", error)

    if not isinstance(error, cooldowns.CallableOnCooldown):
        raise error

    retry_after = round(error.retry_after, 2)
    if error.cooldown.cooldown_id == "spamcheck":
        await inter.send(
            f"You are being rate-limited for spamming! Retry in `{retry_after}` seconds.",
            ephemeral=True,
        )
        error_channel = bot.get_channel(config.ERROR_LOG_CHANNEL_ID)
        if error_channel:
            await error_channel.send(
                f"User {inter.user.id} was caught in a spamming frenzy in "
                f"channel {inter.channel} and guild {inter.guild_id}"
            )
    else:
        await inter.send(
            f"You are being rate-limited! Retry in `{retry_after}` seconds.",
            ephemeral=True,
        )


async def warn_about_balance_reset() -> None:
    """DM everyone whose balance on the expiring slot is about to be wiped.

    Runs on startup and again from the nightly cron; the ``reset_alert`` flag
    on the slot makes sure each reset is only ever announced once.
    """
    slotdb = await db.slotsdb.find_one({"_id": RESET_WARNING_SLOT_ID})
    if not slotdb:
        return

    ex_dt = slotdb.get("reset_1m")
    if not ex_dt or slotdb.get("reset_alert"):
        return

    ex_dt = ex_dt.replace(tzinfo=TZ)
    time_left = ex_dt - datetime.datetime.now(tz=TZ)
    if not datetime.timedelta(0) <= time_left <= RESET_WARNING_WINDOW:
        return

    reset_time = f"<t:{int(time.mktime(utc_to_local(ex_dt).timetuple()))}:D>"
    report_c = find_command(bot, "report")
    countermax = await db.balancesdb.count_documents(
        {"slot_id": RESET_WARNING_SLOT_ID, "active": False}
    )
    balances = db.balancesdb.find({"slot_id": RESET_WARNING_SLOT_ID, "active": False})

    async for index, bdb in a.enumerate(balances, 1):
        embed = nextcord.Embed(
            title="Warning!",
            description=(
                f"Your balance from slot **{slotdb['name']}**({slotdb['_id']}) will be "
                f"**reset** on {reset_time}.\n To prevent the **reset**, please use a "
                f"minimum of **10 commends** during this time or send {report_c} via bot "
                "to request postponement with a **valid reason**!"
            ),
            color=nextcord.Colour.red(),
            timestamp=datetime.datetime.now(tz=TZ),
        )
        embed.add_field(
            name="Your Balance", value=f"**{bdb['amount']}** commends", inline=False
        )
        embed.add_field(
            name="Kind Regards,",
            value=f"[{config.BRAND_NAME}]({config.BRAND_URL})",
            inline=False,
        )
        embed.set_footer(text=config.BRAND_FOOTER, icon_url=config.BRAND_LOGO_URL)

        cprint(f"Please don't turn off script {index}/{countermax}", "red")
        customer = bot.get_user(bdb["userid"])
        if customer and await can_dm_user(customer):
            try:
                await customer.send(embed=embed)
            except nextcord.HTTPException:
                logger.warning(f"{index}/{countermax} - could not DM {bdb['userid']}")
            else:
                await asyncio.sleep(1)

    await db.slotsdb.update_one(
        {"_id": slotdb["_id"]}, {"$set": {"reset_alert": True}}
    )


@bot.event
async def on_ready():
    support_guild = bot.get_guild(config.SUPPORT_GUILD_ID)
    bot.support_guild = support_guild
    bot.customer_role = support_guild.get_role(config.CUSTOMER_ROLE_ID) if support_guild else None
    bot.trusted_role = support_guild.get_role(config.TRUSTED_ROLE_ID) if support_guild else None
    if support_guild is None:
        logger.warning(
            f"support guild {config.SUPPORT_GUILD_ID} not found - "
            "role-gated features will be inactive"
        )

    bot.global_commands = {
        command.name: command.command_ids[None]
        for command in bot._get_global_commands()
        if None in command.command_ids
    }

    while not bot.slottrans_ready:
        await asyncio.sleep(2)

    print("ready is on")
    await warn_about_balance_reset()


def owner_only(interaction: Interaction) -> bool:
    return interaction.user.id == bot.owner_id


@bot.slash_command(name="banuser", guild_ids=config.TESTING_GUILD_IDS)
async def ban_user(interaction: Interaction, user: nextcord.Member):
    """Ban a user from every guild the bot is in."""
    if not owner_only(interaction):
        return await interaction.send("Owner only.", ephemeral=True)

    await interaction.response.defer()
    failed = []
    for guild in bot.guilds:
        try:
            await guild.ban(user, reason="broke commendbot rules")
        except nextcord.Forbidden:
            failed.append(guild.name)
    message = "finished"
    if failed:
        message += f" (no permission in: {', '.join(failed)})"
    await interaction.send(message)


@bot.slash_command(name="ping", guild_ids=config.TESTING_GUILD_IDS)
async def ping(interaction: Interaction):
    await interaction.send("Pong!")


@bot.slash_command(name="reload", guild_ids=config.TESTING_GUILD_IDS)
async def reload_extension(
    interaction: Interaction,
    extension: str = SlashOption(name="extension", description="extension name(.py)"),
):
    if not owner_only(interaction):
        return await interaction.send("Owner only.", ephemeral=True)
    bot.reload_extension(f"cogs.{extension}")
    await interaction.send(
        embed=Embed(
            title="Reload",
            description=f"{extension} successfully reloaded",
            color=0xFF00C8,
        )
    )


@bot.slash_command(name="kill", guild_ids=config.TESTING_GUILD_IDS)
async def kill(interaction: Interaction):
    if not owner_only(interaction):
        return await interaction.send("Owner only.", ephemeral=True)
    await interaction.send("w8")
    await bot.close()


@bot.slash_command(name="left", guild_ids=config.TESTING_GUILD_IDS)
async def leave_guild(
    interaction: Interaction, s: str = SlashOption(name="server")
):
    if not owner_only(interaction):
        return await interaction.send("Owner only.", ephemeral=True)
    guild = bot.get_guild(int(s))
    if guild is None:
        return await interaction.send(f"Not in guild `{s}`.", ephemeral=True)
    await guild.leave()
    await interaction.send(
        embed=Embed(
            title="bot left", description=f"from {guild} - {guild.id}", color=0xFF00C8
        )
    )


@aiocron.crontab("0 0 * * *")
async def alert_pending_restarts():
    """Remind customers whose session survived a bot restart to reconnect."""
    already_sent = set()
    count = 0

    async for seruserdb in db.serverusers.find({"status": "confirmed"}):
        if "hwid" in seruserdb or seruserdb["userid"] in already_sent:
            continue
        if "guildsid" not in seruserdb:
            continue

        already_sent.add(seruserdb["userid"])
        customer = bot.get_user(seruserdb["userid"])
        if customer is None:
            continue

        userdb = await db.usersdb.find_one({"userid": customer.id})
        lang = await get_lang(userdb, bot.get_guild(seruserdb["guildsid"]))
        embed = Embed(
            title=lang["restartalert-title"],
            description=lang["restartalert-description"],
            color=0xFF6700,
            timestamp=datetime.datetime.now(),
        )
        embed.set_author(name="​", icon_url=logo)

        try:
            await customer.send(embed=embed)
        except nextcord.HTTPException:
            logchannel = bot.get_channel(seruserdb.get("error_channelid"))
            if logchannel:
                await logchannel.send(customer.mention, embed=embed)
        count += 1

    logchannel = bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
    if logchannel:
        await logchannel.send(f"send to {count}")


@aiocron.crontab("1 0 * * *", tz=TZ)
async def reset_daily_counters():
    """Roll over the daily quotas and ask every live slot to repost its status."""
    await db.usersdb.update_many({}, {"$set": {"daily": 0}})
    await db.balancesdb.update_many({}, {"$set": {"today_used": 0}})

    async for slotdb in db.slotsdb.find({"enable": True, "ready": True}):
        await db.slottrans.insert_one(
            {"type": "info", "push": "post", "slot_id": slotdb["_id"]}
        )

    async for serverdb in db.serverusers.find({}):
        await db.serverusers.update_one(
            {"_id": serverdb["_id"]}, {"$set": {"cut": serverdb["actualamount"]}}
        )

    await warn_about_balance_reset()


if __name__ == "__main__":
    load_extensions()
    bot.run(config.DISCORD_TOKEN)
