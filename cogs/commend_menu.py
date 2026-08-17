"""Ticket lifecycle and the customer-facing commend menu.

The interactive components live in cogs/commend_menu_views.py and the commend
session lifecycle in cogs/commend_menu_lifecycle.py; both are re-exported here
so `from cogs.commend_menu import closebutton, commend_menu, promo_view`
keeps working.
"""

import asyncio
import calendar
import datetime
import io
import random
import re

import asyncstdlib as a
import chat_exporter
import nextcord
import pymongo.collection
from nextcord import Colour, Embed, Guild, Interaction, TextChannel, User
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from steam_web_api import Steam

import config
from cogs.commend import Confirm, commend
from cogs.commend_menu_lifecycle import MenuLifecycleCommands

# Re-exported for the rest of the codebase, which imports the views from here.
from cogs.commend_menu_views import (  # noqa: F401
    Button_StopCommending,
    Select_StopCommending,
    View_human_readable,
    balance_human_readable,
    balance_menu,
    closebutton,
    commendbotbutton,
    language_header,
    menu_View,
    promo_view,
    redeem_ke_modal,
    selectbalance,
    selectcommend,
    start_commend,
)
from cogs.helpers import helpers
from utils import (
    bluepr,
    cprint,
    db,
    delete_autodelete,
    get_lang,
    logger,
    logo,
    millify,
    prettify,
    pview,
    sview,
    timestamp,
    tz,
    tzsk,
)

steam = Steam(config.STEAM_API_KEY)


































class commend_menu(MenuLifecycleCommands, commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):

        pausetry = await db.guildsetting.find_one({"guildid": config.SUPPORT_GUILD_ID})
        self.bot.pause = pausetry["pause"]
        self.bot.add_view(menu_View(self.bot))
        self.bot.add_view(pview(self.bot, Select_StopCommending,
                          balance_menu, start_commend, language_header, None, None))

        usersonsv = db.serverusers.find({})

        async for userdb in usersonsv:
            if "hwid" not in userdb:
                if userdb["status"] == "confirmed":
                    tdb = await db.ticketsdb.find_one({"channelid": userdb["channelid"]})
                    channel = self.bot.get_channel(userdb["channelid"])
                    if channel:
                        user = self.bot.get_user(userdb["userid"])
                        msg_id = tdb.get("msgid")
                        if msg_id:
                            msg = await channel.fetch_message(msg_id)

                            view = pview(self.bot, Select_StopCommending, balance_menu,
                                         start_commend, language_header, user, None, )
                            await msg.edit(view=view)
                        else:
                            logger.error(f"MSG_ID is none of {userdb}")

                elif userdb["status"] == "w8connect" and "button" in userdb and userdb["button"]:

                    channel = self.bot.get_channel(userdb["channelid"])
                    try:
                        msg = await channel.fetch_message(userdb["msgid"])
                    except Exception:
                        pass
                    try:
                        user = self.bot.get_user(userdb["userid"])
                    except Exception:

                        view = sview(self.bot, Confirm, None, None,
                                     userdb["howitworkis-button"], )
                    else:
                        view = sview(self.bot, Confirm, user, None,
                                     userdb["howitworkis-button"],)
                    await msg.edit(view=view)

        guildstt = db.guildsetting.find({"setupbot": True})

        async for guildst in guildstt:

            if "startupid" in guildst and "startupid-msg" in guildst:
                msgid = guildst["startupid-msg"]
                channelid = guildst["startupid"]

                channel = self.bot.get_channel(channelid)
                if channel:
                    try:
                        msg = await channel.fetch_message(msgid)

                    except Exception:
                        dt = datetime.datetime.now(tz=tz)
                        if rg := guildst.get("setupbot_counter-dt"):
                            rg = rg.replace(tzinfo=tz)
                            different = abs((dt - rg).total_seconds())
                            if different >= 20:
                                pass
                            else:
                                print(f"skipping timer {different}")
                                continue
                        if "setupbot_counter" in guildst and guildst["setupbot_counter"] > 4:
                            await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"setupbot": False}})
                        elif "setupbot_counter" in guildst and guildst["setupbot_counter"] > 3:
                            print("last recovery...")
                            lang = await get_lang(guild=channel.guild)

                            embed = nextcord.Embed(
                                title=lang["create-title"], description=lang["create-description"], color=bluepr, timestamp=datetime.datetime.now())
                            embed.set_image(
                                config.IMAGE_TUTORIAL_WELCOME)
                            embed.set_footer(text=config.BRAND_FOOTER,
                                             icon_url=config.BRAND_LOGO_URL)
                            msg = await channel.send(embed=embed, view=commendbotbutton(self.bot))
                            await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"startupid-msg": msg.id}})

                        elif "setupbot_counter" not in guildst:
                            await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"setupbot_counter": 1, "setupbot_counter-dt": dt}})
                        else:
                            await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$inc": {"setupbot_counter": +1}, "$set": {"setupbot_counter-dt": dt}})

                    else:

                        if self.bot.pause:
                            value = await db.guildsetting.find_one({"guildid": config.SUPPORT_GUILD_ID})
                            timeg: datetime.datetime = value["time"]

                            timeg = timeg.astimezone(
                                tz=tzsk) + datetime.timedelta(hours=2)

                            embed = Embed(
                                title="Maintenance break", description=f"Bot is currently **unable**\nWill be available <t:{int(calendar.timegm(timeg.timetuple()))}:R>", color=0xcda618)
                            embed.add_field(
                                name="Kind Regards,", value="r4p Services developers", inline=False)
                            await msg.edit(embed=embed, view=nextcord.ui.View())
                            if msg.channel.guild.id == config.SUPPORT_GUILD_ID:
                                try:

                                    await msg.edit(embed=embed, view=commendbotbutton(self.bot))

                                except nextcord.Forbidden:
                                    try:
                                        await msg.delete()
                                    except Exception:
                                        pass
                                    print("recovering... ")
                                    msg = await channel.send(embed=embed, view=commendbotbutton(self.bot))
                                    await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"startupid-msg": msg.id}})

                                except Exception:
                                    logger.exception()

                        else:

                            lang = await get_lang(guild=channel.guild)

                            embed = nextcord.Embed(
                                title=lang["create-title"], description=lang["create-description"], color=bluepr, timestamp=datetime.datetime.now())
                            embed.set_image(
                                config.IMAGE_TUTORIAL_WELCOME)
                            embed.set_footer(text=config.BRAND_FOOTER,
                                             icon_url=config.BRAND_LOGO_URL)
                            try:

                                await msg.edit(content=None, embed=embed, view=commendbotbutton(self.bot))
                            except nextcord.errors.Forbidden:
                                try:
                                    await msg.delete()
                                except Exception:
                                    pass
                                print("recovering... ")
                                msg = await channel.send(embed=embed, view=commendbotbutton(self.bot))
                                await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"startupid-msg": msg.id}})
                            except Exception:
                                logger.exception("Exeption in edit message")

                else:
                    dt = datetime.datetime.now(tz=tz)
                    if rg := guildst.get("setupbot_counter-dt"):
                        rg = rg.replace(tzinfo=tz)
                        different = abs((dt - rg).total_seconds())
                        if different >= 20:
                            pass
                        else:
                            print(f"skipping timer {different}")
                            return
                    if "setupbot_counter" in guildst and guildst["setupbot_counter"] > 4:
                        await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"setupbot": False}})
                    elif "setupbot_counter" in guildst and guildst["setupbot_counter"] > 3:

                        print("last recovery...     sssssssssssssss")

                    elif "setupbot_counter" not in guildst:
                        await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"setupbot_counter": 1, "setupbot_counter-dt": dt}})
                    else:
                        await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$inc": {"setupbot_counter": +1}, "$set": {"setupbot_counter-dt": dt}})

    async def close_guild_ch(self, guild_id):
        guild_channels = db.ticketsdb.find({"guildid": guild_id})
        async for guild_channel in guild_channels:
            channel = self.bot.get_channel(guild_channel)
            await self.close_ticket(channel, guild_channel, "Server subscription expired", agressive=True)

    async def refreshguild(self, guild: nextcord.Guild, ):
        self.bot: Bot = self.bot
        await commend.commendingqueue(self)
        guildst = await db.guildsetting.find_one({"guildid": guild.id})

        lang = await get_lang(guild=guild)

        if "startupid" in guildst and "startupid-msg" in guildst:
            msgid = guildst["startupid-msg"]
            channelid = guildst["startupid"]

            channel = self.bot.get_channel(channelid)
            if channel:
                try:
                    msg = await channel.fetch_message(msgid)

                except Exception:

                    await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"setupbot": False}})

                else:

                    if self.bot.pause:
                        value = await db.guildsetting.find_one({"guildid": config.SUPPORT_GUILD_ID})
                        timeg: datetime.datetime = value["time"]

                        timeg = timeg.astimezone(
                            tz=tzsk) + datetime.timedelta(hours=2)

                        embed = Embed(
                            title="Maintenance break", description=f"Bot is currently **unable**\nWill be available <t:{int(calendar.timegm(timeg.timetuple()))}:R>", color=0xcda618)
                        embed.add_field(
                            name="Kind Regards,", value="r4p Services developers", inline=False)
                        await msg.edit(embed=embed, view=nextcord.ui.View())
                        if msg.channel.guild.id == config.SUPPORT_GUILD_ID:
                            await msg.edit(view=nextcord.ui.View())

                    else:

                        lang = await get_lang(guild=channel.guild)
                        embed = nextcord.Embed(
                            title=lang["create-title"], description=lang["create-description"], color=bluepr, timestamp=datetime.datetime.now())
                        embed.set_image(
                            config.IMAGE_TUTORIAL_WELCOME)
                        embed.set_footer(text=config.BRAND_FOOTER,
                                         icon_url=config.BRAND_LOGO_URL)
                        try:
                            await msg.edit(content=None, embed=embed, view=commendbotbutton(self.bot))
                        except nextcord.Forbidden:
                            print("recovering... ")
                            try:
                                await msg.delete()
                            except Exception:
                                pass
                            msg = await channel.send(embed=embed, view=commendbotbutton(self.bot))
                            await db.guildsetting.update_one({"guildid": guildst["guildid"]}, {"$set": {"startupid-msg": msg.id}})

                        except Exception:
                            logger.exception(" ")

    async def show_balance(self, interaction: nextcord.Interaction, human_readable: bool = True, edit_message: bool = False
                           ,):
        await delete_autodelete(interaction.channel)
        member = interaction.user
        balancedb = db.balancesdb.find({"userid": member.id})
        description = ""
        run = 0

        htslist = await db.slotsdb.find({}).to_list(length=None)

        allbalance = 0
        async for run, balanced in a.enumerate(balancedb, 1):
            slotdb = next(
                (i for i in htslist if i["_id"] == balanced["slot_id"]), None)
            if not slotdb:
                continue

            amount = int(balanced["amount"])
            allbalance += amount

            description += f"Avaliable : **{millify(amount) if human_readable else prettify(amount)}** | On Hold : **{millify(int(balanced['onhold'])) if human_readable else prettify(int(balanced['onhold']))}** commends by **{str(slotdb['name'])}** slot\n"

        description += f"\n**Total balance:** **{millify(allbalance) if human_readable else prettify(allbalance)}** commends"

        color_ranges = {
            1000: 0x0a8f82,
            750: 0x008000,
            500: 0x90ee90,
            250: 0xFFA500,
            100: 0xFFD580,
        }
        color = next(
            (color for balance, color in color_ranges.items() if allbalance >= balance),
            0xffcccb,
        )

        if run == 0:
            description = "\n**Total balance: 0 commends**"
            color = 0xffcccb

        embed = nextcord.Embed(
            title="Your balance:", description=description, color=color
        )
        dbp = await db.usersdb.find_one({"userid": member.id})
        if dbp:
            point = int(dbp["points"])
            embed.add_field(
                name="Your Star Points",
                value=f"**{millify(point) if human_readable else prettify(point)}** points",
                inline=False,
            )
        embed.set_footer(
            text=config.BRAND_FOOTER,
            icon_url=config.BRAND_LOGO_URL,
        )

        if not edit_message:
            await interaction.send(embed=embed, ephemeral=True, view=View_human_readable(bot=self.bot))
        else:
            await interaction.edit(embed=embed, view=View_human_readable(bot=self.bot, default=False))

    async def show(self, user: User, lang, error_logs: nextcord.Thread, baldbs: dict = None):
        if user:
            if user.avatar:
                avatar_url = user.avatar.url
            else:
                avatar_url = user.default_avatar.url

            usertest = str(user).isprintable()
            if usertest:

                username = (re.sub(r'[^\w]', ' ', user.name))
            else:
                username = user.id
        else:
            avatar_url = logo
            username = "Unknown"

        greets = lang["greets"]
        selected_greet: str = random.choice(greets)

        welcome_message = selected_greet.format(username=username)
        embed = nextcord.Embed(
            title=welcome_message,
            description="Not used balance will be added back to your balance.\nThe commending process is not instant; you will receive 0-25 commends every 5-15 minutes.",
            color=nextcord.Colour.blurple(),
            timestamp=datetime.datetime.now(tz=None),

        )
        embed.set_thumbnail(avatar_url)
        embed.set_footer(icon_url=avatar_url)
        current_balance = 0
        if not baldbs:
            baldbs = db.balancesdb.find({"userid": user.id})

        async for baldb in baldbs:
            current_balance += baldb["amount"]

        embed.add_field(name="Current Balance:",
                        value=current_balance, inline=False)
        embed.add_field(name="Error-Logs:",
                        value=error_logs.mention, inline=False)

        return embed, menu_View(self.bot)
    async def addtoblacklist(self,sendas:TextChannel,member:User,bannedby:User,guild:Guild,reason,steal=False):
        commenddb = await db.ticketsdb.find_one({"userid": member.id})
        if commenddb:
            ticket = self.bot.get_channel(commenddb["channelid"])
            if ticket:
                await self.close_ticket(ticket, ticket, reason="button_command", ticketsdb=commenddb, agressive=True)
            else:
                await db.ticketsdb.delete_one({"userid": member.id})

        await db.blacklistdb.insert_one({"userid": member.id, "reason": reason, "datetime": datetime.datetime.now(tz=tz), "removed": False,"banned_by":bannedby.id})
        embed = nextcord.Embed(title=f" {bannedby} was add to blacklist, from now u cant use commendbot forever!",
                                description=f"Reason: {reason} , Admin: {bannedby}", color=bluepr)
        embed.add_field(
            name="UnBan Server:", value=f"[{config.BRAND_DISCORD_URL}]({config.BRAND_DISCORD_URL})", inline=True)
        embed.set_thumbnail(
            url=config.BRAND_LOGO_URL)
        embed.set_footer(text=config.BRAND_FOOTER,
                            icon_url=config.BRAND_LOGO_URL)
        embed2 = nextcord.Embed(title="Your Balance ll be removed in 7 days",
                                description="Your balance will be removed within 7 days.\nIn case your unban appeal gets declined we'll remove your balance", color=Colour.orange(), timestamp=timestamp,)
        try:
            await member.send(embeds=(embed, embed2))
        except Exception:
            pass
        await sendas.send(embed=embed)
        banchannel = self.bot.get_channel(config.BAN_LOG_CHANNEL_ID)
        await banchannel.send(f"user: {member} was banned by {bannedby} for {reason} his bal: {steal}")
        if steal and steal:
            bals = db.balancesdb.find({"userid": member.id})

            async for bal in bals:
                await banchannel.send(f"Balance(add_bl) is not logner available for {member if member else bal['userid']} in {bal['amount']} of {bal['slot_id']} slot")
                mybal = await db.balancesdb.find_one({"userid": bannedby.id, "slot_id": bal["slot_id"]})
                if mybal:

                    await db.balancesdb.update_one({"userid": bannedby.id, "slot_id": bal["slot_id"]}, {"$inc": {"amount": bal["amount"]}})
                    await db.balancesdb.delete_one({"userid": member.id, "slot_id": bal["slot_id"]})
                else:
                    await db.balancesdb.insert_one({"userid": bannedby.id, "guildid": guild.id, "lastid": self.bot.user.id, "amount": bal["amount"], "slot_id": bal["slot_id"], "today_used": 0, "onhold": 0, "active": True})
                    await db.balancesdb.delete_one({"userid": member.id, "slot_id": bal["slot_id"]})

    async def close_ticket(self, channel: TextChannel, sendas: Interaction | TextChannel, ticketsdb: dict = None, reason: str = "Close-ticket", agressive: bool = False, edit_message=False):
        if not channel:
            if ticketsdb:
                await db.timedb.delete_one({"channelid": ticketsdb["channelid"]})
                await db.ticketsdb.delete_one({"channelid": ticketsdb["channelid"]})
                return
        else:
            commended = db.serverusers.find({"channelid": channel.id})
            if len(await commended.to_list(None)) == 0 and not agressive or agressive:
                stop = False
                async for commend in commended:
                    result = await self.stop_request(channel, commend, agressive=True, reason="Close ticket")
                    if not result:
                        if edit_message:
                            await sendas.response.edit_message(content="We cant stop current commeding session, try later...", view=self)
                        else:
                            await sendas.send("We cant stop current commeding session, try later...")
                        stop = True
                        return
                    else:

                        asyncio.sleep(2)
                if stop:
                    return

                if not ticketsdb:
                    if isinstance(channel,nextcord.Thread):
                        channel = channel.parent
                    ticketsdb = await db.ticketsdb.find_one({"channelid": channel.id})
                if ticketsdb:
                    if edit_message:
                        await sendas.response.edit_message(content="deleteing in 5s", view=self)
                    else:
                        await sendas.send("deleteing in 5s")
                    transcript = await chat_exporter.export(
                        channel,
                        limit=0,
                        bot=self.bot,
                    )

                    if transcript is None:
                        return

                    transcript_file = nextcord.File(io.BytesIO(
                        transcript.encode()), filename=f"transcript-{channel.name}.html",)
                    logchannel = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
                    embed = nextcord.Embed(
                        title="Deleted channel", description=reason, color=0x00ff2a)
                    embed.set_thumbnail(url=logo)
                    embed.add_field(name="Channel Name: ",
                                    value=channel.name, inline=True)
                    embed.add_field(name="Opened By",
                                    value=ticketsdb["userid"], inline=True)
                    embed.add_field(
                        name="Server:", value=f"{channel.guild} - `{channel.guild.id}`", inline=True)
                    await logchannel.send(content=f'user:  <@{ticketsdb["userid"]}> - {ticketsdb["userid"]} , guildid: {channel.guild.id}', embed=embed, file=transcript_file)
                    await channel.delete()

                    await db.timedb.delete_one({"channelid": channel.id})
                    await db.ticketsdb.delete_one({"channelid": channel.id})
                else:
                    if edit_message:
                        await sendas.response.edit_message(content="We cant close non CommendBot channels!", view=self)
                    else:
                        await sendas.send("We cant close non CommendBot channels!")

            else:

                if edit_message:
                    await sendas.response.edit_message(content="You cant delete channel while commending is in process!", view=self)
                else:
                    await sendas.send("You cant delete channel while commending is in process!")

    async def stop_request(self, interaction: Interaction, serverdb: dict, send=None, agressive=False, reason="/stop command") -> bool:
        stopped = False
        if send is None:
            send = interaction.channel.threads[0]
        steamID64 = serverdb["steamID64"]
        check = await db.waitinglist.find_one({"steamID64": steamID64})
        if check is None:
            if serverdb["status"] == "confirmed":

                await helpers.req_stop_commend(serverdb["slot_id"], steamID64, serverdb["userid"])
                stopped = True

            else:
                await send("processing")

                await self.stop_waiting(serverdb, reason)

        else:
            await send("You cant stop commending for account that is in stop queue")
        return stopped

    async def stop_waiting(self, userons, reason, slotcurr: int = None, rr=None):
        if not userons:
            cprint("non userons ", "red")
            return
        slotcurrency = userons["amount"]
        await db.balancesdb.update_one({"userid":userons["userid"]},{"$inc": {"onhold": -slotcurrency,"amount":+slotcurrency}})
        if "channelid" in userons:
            await db.serverusers.delete_one({"_id": userons["_id"]})
            channel: TextChannel = self.bot.get_channel(userons["channelid"])
            if channel:

                embed = nextcord.Embed(title="Auto-stop", description="Your account was deleted from wait list.",
                                       color=Colour.brand_red(), timestamp=datetime.datetime.now())
                embed.add_field(name="Reason", value=reason, inline=True)
                count = await db.serverusers.count_documents({"channelid": channel.id})
                await channel.threads[0].send(embed=embed, delete_after=60)
                if count == 0:
                    ticketdb = await db.ticketsdb.find_one({"channelid": channel.id})
                    if ticketdb:
                        msg = await channel.fetch_message(ticketdb.get("msgid"))
                        if msg:
                            error_thread = self.bot.get_channel(
                                ticketdb["error_channelid"])
                            userdb = await db.usersdb.find_one({"userid": userons["userid"]})

                            lang = await get_lang(userdb, channel.guild)
                            embed, view = await self.show(self.bot.get_user(userons["userid"]), lang, error_thread)

                            await msg.edit(embed=embed, view=view)
                        else:
                            logger.error(f"also msgid is none {userons}")
                    else:
                        logger.error(f"For channel {channel.id} cannot find ticketsdb is None(stop_waiting)")
            else:
                logger.error(f"CHannel is not defined {userons}")
        else:
            await db.serverusers.update_one({"_id": userons["_id"]}, {"$set": {"status": "error", "reason": reason}})

        if not slotcurr:

            slotdb = await db.slotsdb.find_one_and_update({"_id": userons["slot_id"]}, {"$inc": {"currency": +slotcurrency}}, return_document=pymongo.ReturnDocument.AFTER)

        else:
            await db.slotsdb.find_one_and_update({"_id": userons["slot_id"]}, {"$set": {"currency": +slotcurr}}, return_document=pymongo.ReturnDocument.AFTER)

        await db.waitinglist.delete_many({"steamID64": userons["steamID64"]})
        await db.slottrans.delete_many({"steamID64": userons["steamID64"]})











def setup(bot: Bot) -> None:
    bot.add_cog(commend_menu(bot))
