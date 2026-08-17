"""Owner and staff tooling: slots, blacklist, panels, diagnostics."""

import calendar
import datetime

import cooldowns
import humanfriendly
import nextcord
import pymongo
from nextcord import ChannelType, Colour, Interaction, SlashOption, User
from nextcord.utils import get
from steam import steamid

import config
from cogs.commend import *
from cogs.commend_menu import commend_menu
from cogs.helpers import *
from utils import *

script_top = datetime.datetime.now(tz=tz)


class AdminCommands:
    """Mix into bot_commands; see cogs/commands.py."""

    @nextcord.slash_command(name="eval", description="owner only",)
    async def eval_command(self, interaction: Interaction,
                           command: str = SlashOption(
                               name="code", required=True),
                           ephemeral: bool = SlashOption(
                               name="ephemeral", required=True),
                           filter: str = SlashOption(
                               name="filter-pymongo", required=False),
                           ):
        if interaction.user.id == self.bot.owner_id:
            br = False

            try:
                command = eval(command)
            except Exception as e:
                await interaction.send(f"Exception: {e}", ephemeral=ephemeral)
            else:
                if type(command) == pymongo.cursor.Cursor:
                    send = ""
                    for value in command:
                        if filter:
                            try:
                                send += f"{value[filter]}\n"
                            except Exception as e:
                                await interaction.send(f"Exception2: {e}", ephemeral=ephemeral)
                                br = True
                                break
                        else:
                            send += f"{value}\n"

                else:
                    send = command

                if not br:
                    await interaction.send(f"{send}", ephemeral=ephemeral)

    @nextcord.slash_command(name="deleteall", description="only bozo",)
    async def deleteall(self, interaction: Interaction,
                        guildid: str = SlashOption(required=False)
                        ):
        if not (interaction.user.id == self.bot.owner_id or interaction.user.id in admins):
            await interaction.send("only the bot owner can use this command")
            return

        await interaction.send("ok")
        if guildid:
            guildid = int(guildid)
            channels = db.ticketsdb.find({"guildid": guildid})
        else:
            channels = db.ticketsdb.find()
        async for channeldb in channels:
            channel = self.bot.get_channel(channeldb["channelid"])
            await commend_menu.close_ticket(self, channel, interaction.channel, channeldb,agressive=True)

        await interaction.channel.send("Finished!")

    @nextcord.slash_command(name="setslotcurrency", description="only bozo")
    async def setslotcurrency(self, interaction: Interaction,
                              number: int = SlashOption(
                                  name="currency", description="currency", required=True),
                              slot: int = SlashOption(
                                  name="slot_id", description="slot_id", required=True),
                              ):
        if interaction.user.id in admins:
            await db.slotsdb.update_one({"_id": slot}, {"$set": {"currency": number}})
            logger.debug("Updated slot currency to " + str(number))
            await interaction.send(f"ok {number}", ephemeral=True)
        else:
            await interaction.send("Nope", ephemeral=True)

    @nextcord.slash_command(
        name="leave",
        description="leave from server",
        guild_ids=TESTING_GUILD_ID

    )
    @cooldowns.cooldown(1, 10, bucket=cooldowns.SlashBucket.author)
    async def leave_command(self, interaction: Interaction, guild_id: str = SlashOption(name="guild_id", required=True)):

        if interaction.user.id == self.bot.owner_id:

            guild = self.bot.get_guild(int(guild_id))

            if guild is None:
                await interaction.send("I don't recognize that guild.")
                return
            else:
                await guild.leave()
                await interaction.send(f":ok_hand: Left guild: {guild.name} ({guild.id})")

    @nextcord.slash_command(name="add_blacklist", description="only support",)
    async def addtoblacklist(self, interaction: Interaction,
                             member: nextcord.User = SlashOption(
                                 name="user", description="to blacklist him", required=True),
                             reason: str = SlashOption(
                                 name="reason", description="reason", required=True),
                             steal: bool = SlashOption(
                                 name="steal_bal", description="get user balance", required=False),
                             ):
        if interaction.user.id == self.bot.owner_id or interaction.user.id in admins:
            await commend_menu.addtoblacklist(self,interaction,member,interaction.user,interaction.guild,reason,steal)

        else:
            await interaction.send("nope!")

    @nextcord.slash_command(name="reset_limt", description="only support",)
    
    async def reset_limt(self, interaction: Interaction,
                         member: nextcord.Member = SlashOption(name="user", description="User to reset", required=True)):

        if interaction.user.id == self.bot.owner_id or interaction.user.id in admins:
            userdb = await db.usersdb.find_one({"userid": member.id})
        
            if userdb:
                accs:list = userdb.get("accs",list())
                if "all_accs" not in userdb:
                    await db.usersdb.update_one({'_id': userdb["_id"]}, {'$set': {'all_accs': []}})
                else:
                    all_accs = userdb.get("all_accs", [])
                    if len(all_accs) + len(userdb.get("accs", [])) >= 10:
                        await interaction.send(embed=embed_error("Limit exceeded!", f"Limit was exceeded, {member} needs to create a ticket for verification or buy an unban and also resell a sub :*"))
                        return
               
                
                await db.usersdb.update_one({'_id': userdb["_id"]}, {'$set': {'accs': []}, '$push': {'all_accs': { '$each': accs }}})
                await interaction.send(f"Limit reset for {member.mention}.")
            else:
                await interaction.send("User not found in the database.")
        else:
            await interaction.send("You do not have permission to use this command.")

    @nextcord.slash_command(name="unban", description="only support",)
    async def unban(self, interaction: Interaction,
                    member: nextcord.User = SlashOption(
                        name="user", description="to blacklist him", required=True),

                    accs: bool = SlashOption(
                        name="clearaccs", description="cl dc", required=True),
                    ):
        if interaction.user.id == self.bot.owner_id or interaction.user.id in admins:
            bkdb = await db.blacklistdb.find_one({"userid": member.id})
            if bkdb:
                if not bkdb.get("freeze",False):
                    if accs:

                        await db.usersdb.update_one({'userid': member.id}, {'$set': {'accs': []}})
                    banchannel = self.bot.get_channel(config.BAN_LOG_CHANNEL_ID)
                    await banchannel.send(f"user: {member} was unbanned by {interaction.user}")
                    await db.blacklistdb.delete_one({"_id": bkdb["_id"]})
                    await interaction.send("User unbanned")
                else:
                    await interaction.send("This user cant be unbanned, because in it currently running process.")

    @nextcord.slash_command(name="sumprivbalance", description="sum of every customer balance", guild_ids=TESTING_GUILD_ID)
    async def sumprivbalance_command(self, interaction: Interaction,):
        if interaction.user.id == self.bot.owner_id:
            privchannels = await db.balancesdb.find({})
            amount = 0
            for privcahnnel in privchannels:
                if not privcahnnel["userid"] == config.OWNER_ID:
                    slotmm = privcahnnel["amount"]
                    amount = amount + slotmm
            slotzero = await db.guildsetting.find_one({"guildid": config.SUPPORT_GUILD_ID})
            await interaction.send(f"all users balance {amount} all slot balance {slotzero['sumcurrency']}")

    @nextcord.slash_command(
        name="showactualslots",
        description="show stats",

    )
    async def showactualslots_command(self,
                                      interaction: Interaction,

                                      ):
        if interaction.user.id == self.bot.owner_id:
            await interaction.send("Processing!", ephemeral=True)
            guildsett = await db.guildsetting.find_one({"guildid": interaction.guild_id})
            logchannel = self.bot.get_channel(guildsett["logid"])
            embed = nextcord.Embed(title="Active Slots", color=0xff0000)
            allslots = await db.slotsdb.find({})
            async for slot in allslots:
                if slot["enable"]:
                    if "guildsid" in slot:
                        if interaction.guild_id in slot["guildsid"]:
                            embed.add_field(
                                name=slot["name"], value=f"Slot_ID: {slot['_id']} \nCommending: {slot['free']} \nCurrency: {slot['currency']} commends", inline=False)
                    else:
                        embed.add_field(
                            name=slot["name"], value=f"Slot_ID: {slot['_id']} \nCommending: {slot['free']} \nCurrency: {slot['currency']} commends", inline=False)

            await interaction.channel.send(embed=embed)
            await logchannel.send(embed=embed)
        else:
            await interaction.send("This command can only use administrator of bot!", ephemeral=True)

    @nextcord.slash_command(name="showallslots", description="show stats2",)
    async def showallslots_command(self, interaction: Interaction):
        if interaction.user.id == self.bot.owner_id:
            await interaction.send("Processing!", ephemeral=True)
            guildsett = await db.guildsetting.find_one({"guildid": interaction.guild_id})
            logchannel = self.bot.get_channel(guildsett["logid"])
            embed = nextcord.Embed(title="All slots", color=0xff0000)
            allslots = db.slotsdb.find({})
            async for slot in allslots:
                if slot["_id"] != 0:
                    embed.add_field(
                        name=slot["name"], value=f"Slot_ID: {slot['_id']} \nCommending: {slot['enable']} \nCurrency: {slot['currency']} commends", inline=False)

            await interaction.channel.send(embed=embed)
            await logchannel.send(embed=embed)
        else:
            await interaction.send("This command can only use administrator of bot!", ephemeral=True)

    @nextcord.slash_command(name="change-logchannel", description="Change log channel for reportbot",)
    async def logchannelchange_command(self, interaction: Interaction,
                                       secondarg: nextcord.abc.GuildChannel = SlashOption(
            name="channel",
            channel_types=[ChannelType.text, ChannelType.public_thread],
            description="Choose a channel for logs",
            required=True,
                                           ),
    ):

        if interaction.user.guild_permissions.administrator or interaction.user.id == self.bot.owner_id:

            await db.guildsetting.update_one({"guildid": interaction.guild.id}, {"$set": {"logid": secondarg.id, "logonoff": True}})
            await interaction.send(f"Successfully saved channel {secondarg}! ", ephemeral=True)

            guildsett = await db.guildsetting.find_one({"guildid": interaction.guild.id})
            role = get(interaction.guild.roles, id=guildsett["supportroleid"])
            try:

                owner = interaction.guild.get_member(self.bot.owner_id)

            except Exception:
                pass
            else:
                await owner.add_roles(role)

        else:
            embed = nextcord.Embed(
                title="error", description="Only the **Administrator** can use this command.", color=0xff0000)
            await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="change-stats", description="turn on stats", guild_ids=TESTING_GUILD_ID,)
    async def statschannel_command(self,
                                   interaction: Interaction,
                                   enable: str = SlashOption(name="enable", description="enable or disable stats", choices={
                                                             "enable", "disable"}, required=False),
                                   channelname: str = SlashOption(
            name="channelname", description="set stats channel name(example Now commending)", required=False),

    ):
        if interaction.user.guild_permissions.administrator or interaction.user.id == self.bot.owner_id:
            if enable is None or enable == "enable":
                other = nextcord.utils.get(
                    interaction.guild.categories, name="CommendBot")
                allonserver = await db.serverusers.count_documents({"commended": True})
                if other is not None:

                    if channelname is None:
                        channel = await interaction.guild.create_voice_channel(name=f"Now commending: {allonserver}", category=other, user_limit=0)
                        await db.guildsetting.update_one({"guildid": interaction.guild_id}, {"$set": {"voicechannelid": channel.id}})
                        await interaction.send(f"The channel has been successfully created!({channel.mention})", ephemeral=True)
                    else:
                        channel = await interaction.guild.create_voice_channel(name=f"{channelname}: {allonserver}", category=other, user_limit=0)
                        await db.guildsetting.update_one({"guildid": interaction.guild_id}, {"$set": {"voicechannelid": channel.id}})
                        await interaction.send(f"The channel has been successfully created!!({channel.mention})", ephemeral=True)

                else:
                    embed = nextcord.Embed(
                        title=translates.eng["on_error"], description="To run this command you need to have setuped bot (`/setup`) or you changed name of the CommendBot category", color=0xe74c3c)
                    await interaction.send(embed=embed, ephemeral=True)
            else:
                guildsettingsdb = await db.guildsetting.find_one_and_update({"guildid": interaction.guild_id}, {"$unset": {"voicechannelid": ""}})
                if "voicechannelid" in guildsettingsdb:

                    channel = interaction.guild.get_channel(
                        guildsettingsdb["voicechannelid"])
                    if channel:
                        await channel.delete()
                        await interaction.send("Stats  has been successfully disabled", ephemeral=True)
                    else:
                        await interaction.send("Channel is none!", ephemeral=True)

    @nextcord.slash_command(
        name="addpanel",
        description="add panel for user",

    )
    async def addpanel_command(self,
                               interaction: Interaction,

                               timenow: str = SlashOption(
                                   name="time", description="Paste here in days",),

                               user: User = SlashOption(
                                   name="user", description="User", required=True),
                               ):
        if interaction.user.id == self.bot.owner_id or interaction.user.id in admins:
            await interaction.response.defer()

            userdb = await db.usersdb.find_one({"userid": user.id})
            if userdb:
                olddatetime: datetime.datetime = userdb["expire"]
                if olddatetime == 0 or olddatetime.replace(tzinfo=datetime.timezone.utc) < datetime.datetime.now(tz=tz):

                    if "m" not in timenow.lower():

                        timenow = humanfriendly.parse_timespan(timenow)

                        tim2 = datetime.datetime.now(
                            tz=tz)+datetime.timedelta(seconds=timenow)
                    else:
                        tim2 = datetime.datetime.now(tz=tz)
                        months = int(timenow.lower().split("m")
                                     [0]) + (tim2.month)
                        years = tim2.year
                        while months > 12:

                            months -= 12
                            years += 1

                        tim2 = tim2.replace(month=months, year=years)
                        timenow = f'{timenow.lower().split("m")[0]} months'

                else:
                    if "m" not in timenow.lower():

                        timenow = humanfriendly.parse_timespan(timenow)

                        tim2 = olddatetime+datetime.timedelta(seconds=timenow)
                    else:

                        months = int(timenow.lower().split("m")
                                     [0]) + (olddatetime.month)
                        years = olddatetime.year
                        while months > 12:

                            months -= 12
                            years += 1

                        tim2 = olddatetime.replace(month=months, year=years)
                        timenow = f'{timenow.lower().split("m")[0]} months'

                await db.usersdb.find_one_and_update({"_id": userdb["_id"]}, {"$set": {"expire": tim2, "expired": False}}, return_document=pymongo.ReturnDocument.AFTER)

                embed = nextcord.Embed(
                    title="Extended panel subscription",  color=Colour.gold(), timestamp=timestamp,)
                embed.add_field(
                    name="User:", value=f"{user} - {user.id}", inline=False)
                embed.add_field(name="Extended for:",
                                value=f"{timenow}", inline=False)
                embed.add_field(
                    name="Expire at:", value=f"<t:{int(calendar.timegm(tim2.timetuple()))}:f>", inline=False)

                await interaction.send(embed=embed)

                if await can_dm_user(interaction.user):
                    await interaction.user.dm_channel.send(embed=embed)
                botow = self.bot.get_user(self.bot.owner_id)
                if botow != interaction.user:
                    if await can_dm_user(botow):
                        await botow.dm_channel.send(embed=embed)

                if await can_dm_user(user):
                    embed.add_field(
                        name="Login", value=userdb["login"], inline=False)
                    embed.add_field(name="Password",
                                    value=userdb["password"], inline=False)
                    await user.dm_channel.send(embed=embed)

        else:
            await interaction.send("only the bot owner or an admin can use this command")

    @nextcord.slash_command(
        name="debug_check",
        description="debug_check",

    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def debug_check(self, interaction: Interaction,

                          ):
        if interaction.user.id == self.bot.owner_id:
            await interaction.send(f"on {interaction.guild.name} is debug mode off")

    @nextcord.slash_command(
        name="check",
        description="check_user",
        guild_ids=TESTING_GUILD_ID,

    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def check_on(self, interaction: Interaction,
                       user: str = SlashOption(
                           name="user", description="user link", required=True)
                       ):
        if interaction.user.id == self.bot.owner_id:
            steamidg = None
            if "/id/" in user or "/profiles/" in user:
                steam64id = steamid.from_url(user, http_timeout=60)
                if steam64id:
                    steamidg = steam64id.as_64
            else:
                try:
                    steamidg = int(steam64id)
                except Exception:
                    await interaction.send("error incorrect profile", ephemeral=True)
            if steamidg:
                tryuser = await db.serverusers.find_one({"steamID64": steamidg})
                if tryuser:
                    await interaction.send(f"user is on server! and status is {tryuser['status']}, need to get {tryuser['amount']}", ephemeral=True)
                else:
                    await interaction.send("user is none", ephemeral=True)

        else:
            await interaction.send("Only dev of bot can use it!", ephemeral=True)
