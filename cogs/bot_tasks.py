import asyncio
import calendar
import datetime
import io
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiocron
import aiosmtplib
import asyncstdlib as a
import nextcord
import pymongo
from nextcord import Colour, TextChannel, User
from nextcord.ext import commands, tasks
from nextcord.ext.commands import Bot
from nextcord.utils import get

import config
from cogs.commend import *
from cogs.commend_menu import closebutton, commend_menu
from cogs.resellers import resellers
from utils import *


class taskss(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def refresh_customers(self):
        cprint("refresh_customers", "red")
        b0guild = self.bot.get_guild(config.COMMUNITY_GUILD_ID)
        bo_role = b0guild.get_role(config.COMMUNITY_ROLE_ID)
        for member in b0guild.members:
            if member:
                if baldb:=await db.balancesdb.find_one({"userid":member.id}):
                    if bo_role and bo_role not in member.roles:
                        await member.add_roles(bo_role, reason="He is customer")
                        await asyncio.sleep(1)
                        
        
        for member in self.bot.support_guild.members:
            if baldb:=await db.balancesdb.find_one({"userid":member.id}):
                
                
                
                if self.bot.customer_role and self.bot.customer_role not in member.roles:
                    await member.add_roles(self.bot.customer_role, reason="He is customer")
                    await asyncio.sleep(0.2)
                if self.bot.trusted_role and self.bot.trusted_role not in member.roles:
                    if baldb.get("lastid") == OWNERID and baldb.get("guildid") == self.bot.support_guild.id:
                    
                        await member.add_roles(self.bot.trusted_role, reason="Trusted customer")

                        cprint("is loyal")

    async def mail_add(self):
        notify_counter = 0
        users = db.usersdb.find({"alert_verify": {"$exists": False}}).sort(
            "_id", pymongo.ASCENDING)
        usecoutrs = await db.usersdb.count_documents({})
        counter = 0
        close_dms = 0
        async for ID, userdb in a.enumerate(users):
            if not userdb.get("alert_verify", False) and counter < 30:
                cprint(f"{counter} of {ID}/{usecoutrs} ppls", "yellow")
                user = self.bot.get_user(userdb.get("userid"))
                if user and user.id != self.bot.user.id:
                    if await can_dm_user(user):
                        counter += 1
                        await db.usersdb.update_one({'_id': userdb["_id"]}, {'$set': {'alert_verify': True}})
                        embed = nextcord.Embed(
                            title="Add More Information!",
                            description=f"Please fill out the short form to provide more information about yourself in case you encounter a ban or require other recovery features.\n\n If you have any problem, **please contact:** <@{config.OWNER_ID}>.\n\n This verification **isn't required**, but in case you need to recover your account or find a new link to the bot and your email isn't linked, **you won't be able to recover your account!!**",
                            # Using nextcord.Colour.gold() to set the color to yellow/gold
                            color=nextcord.Colour.gold(),
                            timestamp=datetime.datetime.now()  # Current timestamp
                        )
                        embed.add_field(
                            name="Attention!", value="Please ensure that you provide accurate information. Any **inaccurate** or **fake** information may result in a **timeout or blacklisting**.", inline=False)
                        embed.set_footer(
                            text="Please provide a permanent email address.")
                        await user.send(embed=embed, view=address_button(self.bot))
                        await asyncio.sleep(5)
                    else:
                        close_dms += 1
            elif counter > 40:
                break

        cprint(f"BASIC EVENT END {close_dms}", "red")
        usersdb = db.usersdb.find({"verify": True}).sort(
            "_id", pymongo.ASCENDING)
        blackdb = await db.blacklistdb.find({"userid": {"$exists": True}}).to_list(None)
        async for ID, userdb in a.enumerate(usersdb):
            cprint(f"{ID}/xxxxxxx bs")
            if not userdb.get("alert_recovery", False):
                user_id: int = userdb.get("userid")
                user = self.bot.get_user(user_id)

                if user is None and user_id:
                    black = list(
                        filter(lambda i: i["userid"] == user_id, blackdb))
                    if len(black) != 0:
                        await db.usersdb.update_one({'_id': userdb["_id"]}, {'$set': {'alert_recovery': True}})
                        continue

                    baldbs = await db.balancesdb.count_documents({"userid": user_id, "amount": {"$gt": 10}})
                    logger.warn(
                        f"User {user_id} , isnt on any commendbot server!!! bldb: {baldbs}")
                    if baldbs != 0:

                        mail = userdb.get("mail")
                        html = html_notify()

                        # Create a multipart message container
                        message = MIMEMultipart()
                        message['From'] = config.MAIL_FROM_NOREPLY
                        message['To'] = mail
                        message['Subject'] = 'Notify'

                        # Attach the HTML content to the email
                        message.attach(MIMEText(html, 'html'))
                        notify_counter += 1
                        await db.usersdb.update_one({'_id': userdb["_id"]}, {'$set': {'alert_recovery': True}})
                        try:
                            await smtp.sendmail(config.MAIL_NOREPLY, mail, message.as_string())
                        except aiosmtplib.SMTPServerDisconnected:
                            await smtp.connect()
                            await smtp.sendmail(config.MAIL_NOREPLY, mail, message.as_string())
                elif not user_id:
                    logger.error(
                        f"database {userdb} doesnt include id of user !!!!")

        cprint(f"recovery notifications sent: {notify_counter}", "red")

    async def free_promo():
        usersdb = db.usersdb.find({"verify": True}).sort(
            "_id", pymongo.ASCENDING)
        blackdb = await db.blacklistdb.find({"userid": {"$exists": True}}).to_list(None)
        async for ID, userdb in a.enumerate(usersdb):
            user_id: int = userdb.get("userid")

            free: int = userdb.get("free")
            if free:
                continue

            black = list(filter(lambda i: i["userid"] == user_id, blackdb))
            if len(black) != 0:
                continue

            name = userdb.get("first_name", "Unknown")
            mail = userdb.get("mail")
            msg = f"""

                Hello {name},

                We're thrilled to see your enthusiasm for our CS:GO commend bot! As a gesture of gratitude, we're excited to offer you a generous supply of CS:GO commends and an array of commendation packages. The power to enhance your CS:GO experience is now in your hands!

                Don't miss out on this fantastic opportunity! Hurry and fill out our form <a href="{config.PROMO_FORM_URL}" >here</a> , and watch as we work our magic to amplify your CS:GO profile.

                Embrace the commendation journey and level up your gaming persona!

                Warm regards,
                <a href="{config.BRAND_URL}" >{config.BRAND_NAME}</a>

                """

            # Create a multipart message container
            message = MIMEMultipart()
            message['From'] = config.MAIL_FROM_PROMO
            message['To'] = mail
            message['Subject'] = 'Would you like free CS:GO commends?'

            # Attach the HTML content to the email
            message.attach(MIMEText(msg, 'plain'))

            try:
                await smtp.sendmail(config.MAIL_PROMO, mail, message.as_string())
            except aiosmtplib.SMTPServerDisconnected:
                await smtp.connect()
                await smtp.sendmail(config.MAIL_PROMO, mail, message.as_string())
            except Exception:
                logger.exception()
            await db.usersdb.update_one({'_id': userdb["_id"]}, {'$set': {'free': True}})

            print("mail send")

    @commands.Cog.listener()
    async def on_ready(self):
        while not self.bot.slottrans_ready :
            await asyncio.sleep(2)
            
        
        
        
        cprint("Starting bot_tasks", "yellow")

        # Prepare Message

        if not taskss.autoreport.is_running():
            taskss.autoreport.start(self)

        if not taskss.subcheck.is_running():
            taskss.subcheck.start(self)

        

        if not taskss.autostart.is_running():
            taskss.autostart.start(self)
        if not taskss.roleaddjob.is_running():
            taskss.roleaddjob.start(self)
            
            
        
            
            
        if not taskss.change_status.is_running():
            taskss.change_status.start(self)

        cprint("Started bot_tasks!", "green")

    @tasks.loop(hours=1)
    async def roleaddjob(self):
        datetime_utc = get_datetime_utc()
        print("roleaddjob running")
        
        await taskss.auto_close_check(self)
        await taskss.refresh_customers(self)
        logchannel = self.bot.get_channel(config.TRANSACTION_LOG_CHANNEL_ID)
        resellersdb = await db.subdb.find({"pay": True, "disabled": False}).to_list(None)
        blacklistdb = await db.blacklistdb.find({"userid": {"$exists": True}}).to_list(None)
        dbusers = db.usersdb.find({"giftaccs": {"$exists": True}})
        async for id, userdb in a.enumerate(dbusers):

            bldb = list(filter(lambda i:  i.get("userid")
                        == userdb["userid"], blacklistdb))

            member = self.bot.get_user(userdb["userid"])
            if member:
                user_mention = member
            else:
                user_mention = userdb["userid"]

            if len(bldb) == 0:

                reseller_pesonal = list(filter(
                    lambda i: "ownerid" in i and i["ownerid"] == userdb["userid"] and i["subtype"] in [3, 1, 0], resellersdb))

                if len(reseller_pesonal) == 0:

                    if "giftaccs" in userdb:
                        giftaccs = userdb["giftaccs"]
                        if len(giftaccs) >= 5:

                            reason = "Reselling without reselling sub"
                            await db.blacklistdb.insert_one({"userid": userdb["userid"], "reason": reason, "datetime": datetime.datetime.now(tz=tz), "removed": False, "freeze": True})
                            embed = nextcord.Embed(title=" AutoMod was add to blacklist, from now u cant use commendbot forever!",
                                                   description=f"Reason: {reason} , Admin: AutoMod", color=bluepr)
                            embed.add_field(
                                name="UnBan Server:", value=f"[{support_server_link}]({support_server_link})", inline=True)
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

                            await logchannel.send(f"User {user_mention} was banned cuz he reselling/lim")

        blacklistdb = db.blacklistdb.find({"userid": {"$exists": True}})
        async for bluser in blacklistdb:
            if "datetime" in bluser:
                bldatetime: datetime.datetime = (
                    bluser["datetime"]).replace(tzinfo=datetime.timezone.utc)

                if bldatetime <= (datetime.datetime.now(tz=tz) - datetime.timedelta(days=7)):
                    balancedb = db.balancesdb.find(
                        {"userid": bluser["userid"]})

                    async for bl in balancedb:
                        if "userid" in bl:
                            banchannel = self.bot.get_channel(
                                config.BAN_LOG_CHANNEL_ID)

                            mybal = await db.balancesdb.find_one({"userid": self.bot.owner_id, "slot_id": bl["slot_id"]})
                            if mybal:

                                await db.balancesdb.update_one({"userid": self.bot.owner_id, "slot_id": bl["slot_id"]}, {"$inc": {"amount": bl["amount"]}})
                                await db.balancesdb.delete_one({"userid": bl["userid"], "slot_id": bl["slot_id"]})
                            else:
                                await db.balancesdb.insert_one({"userid": self.bot.owner_id, "guildid": config.SUPPORT_GUILD_ID, "lastid": self.bot.user.id, "amount": bl["amount"], "slot_id": bl["slot_id"], "today_used": 0, "onhold": 0, "active": True})
                                await db.balancesdb.delete_one({"userid": bl["userid"], "slot_id": bl["slot_id"]})
                            owner = self.bot.get_user(self.bot.owner_id)
                            member = self.bot.get_user(bl["userid"])
                            await banchannel.send(f"Balance is not logner available for {member if member else bl['userid']} in {bl['amount']} of {bl['slot_id']} slot")
                            if member:
                                await owner.send(f"u have new balance! add {bl['amount']} from {member} slot: {bl['slot_id']}")
                            else:
                                await owner.send(f"u have new balance! add {bl['amount']} from {bl['userid']} slot: {bl['slot_id']}")
                            await db.blacklistdb.update_one({'userid': bluser["userid"]}, {'$set': {'removed': True}})

                    else:
                        await db.blacklistdb.update_one({'userid': bluser["userid"]}, {'$set': {'removed': True}})

        guilddbs = await db.guildsetting.find({}).to_list(None)
        async for subdb in db.subdb.find({"disabled": False}):

            if "guildid" in subdb:
                guildb = list(
                    filter(lambda i: i["guildid"] == subdb["guildid"], guilddbs))
                if len(guildb) != 0:
                    guildb = guildb[0]
                    if subdb["guildid"] != self.bot.support_guild.id:
                        guild = self.bot.get_guild(subdb["guildid"])
                        if guild:
                            botg = guild.get_member(self.bot.user.id)

                            if botg.guild_permissions.administrator:

                                if "supportroleid" in guildb:

                                    try:
                                        role = get(
                                            guild.roles, id=guildb["supportroleid"])

                                    except Exception:

                                        role = get(
                                            guild.roles, name="CommendBot-Support-Role")
                                        if role.position > botg.top_role.position:

                                            role = await guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))

                                        if role is None:
                                            role = await guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))
                                        await db.guildsetting.update_one({"guildid": guild.id}, {"$set": {"supportroleid": role.id}})
                                        for memberid in admins:
                                            bowner = guild.get_member(memberid)
                                            if bowner:
                                                try:
                                                    await bowner.add_roles(role)
                                                    cprint(
                                                        f"Add role to {bowner}", "green")
                                                except Exception:

                                                    pass
                                    else:
                                        for memberid in admins:
                                            bowner = guild.get_member(memberid)
                                            if bowner and role not in bowner.roles:
                                                if role.position > botg.top_role.position:

                                                    role = await guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))

                                                    await db.guildsetting.update_one({"guildid": guild.id}, {"$set": {"supportroleid": role.id}})
                                                try:
                                                    await bowner.add_roles(role)
                                                except nextcord.errors.Forbidden:
                                                    logger.exception(
                                                        "Missing perms add_role to admin")
                                                    await guild.leave()
                                                except Exception:
                                                    logger.exception(
                                                        "Other  add_role to admin")
                                                cprint(
                                                    f"Add role to {bowner}", "green")
                                    if datetime_utc.day == 1 and datetime_utc.hour in range(1, 2):
                                        croles = len(guild.roles)
                                        print(guild.name)
                                        while croles != 1:

                                            try:
                                                await role.edit(position=croles)

                                            except nextcord.errors.Forbidden as ex:
                                                if "edit a message authored by another user" in ex:
                                                    role = await guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))

                                            except Exception:
                                                cprint(
                                                    f"failed to ct {croles}")
                                                croles -= 1

                                            else:
                                                cprint(f"role is on {croles}")
                                                break
                                        cprint("finished roles!", "green")

                            else:
                                print(f"eroor with this guild {guild.name}")

                            if subdb["disabled"]:

                                if subdb["disabled"] and not subdb["pay"]:
                                    await guild.leave()
                                print(f"deleted {guild.name}")
                        else:
                            await db.guildsetting.delete_one({"guildid": subdb["guildid"]})
                            print(f"deleted {subdb['guildid']}")

            if "ownerid" in subdb:
                owner = self.bot.support_guild.get_member(subdb["ownerid"])
                if owner:
                    if "subtype" in subdb:
                        if 1 == subdb["subtype"]:
                            premium = get(self.bot.support_guild.roles,
                                          id=config.TICKET_CATEGORY_ID)
                            if premium not in owner.roles:
                                await owner.add_roles(premium, reason="He is premium reseller of commendbot")
                        elif 2 == subdb["subtype"]:
                            basic = get(self.bot.support_guild.roles,
                                        id=config.TICKET_ARCHIVE_CATEGORY_ID)
                            if basic not in owner.roles:
                                await owner.add_roles(basic, reason="He is standard reseller of commendbot")
                        elif 3 == subdb["subtype"]:
                            basic = get(self.bot.support_guild.roles,
                                        id=config.TICKET_ARCHIVE_CATEGORY_ID)
                            if basic not in owner.roles:
                                await owner.add_roles(basic, reason="He is standard reseller of commendbot")
        guildssetup = db.guildsetting.find({})

        async for guildsetup in guildssetup:
            if "voicechannelid" in guildsetup:

                allonserver = await db.serverusers.count_documents({"status": "confirmed"})

                voicechannel = self.bot.get_channel(
                    guildsetup["voicechannelid"])

                if voicechannel is not None:

                    chname = voicechannel.name
                    chname = [int(s) for s in chname.split() if s.isdigit()]
                    if [0] in chname:

                        origoname = voicechannel.name.replace(
                            str(chname[0]), str(allonserver))
                        print(f"nejaka value: {chname} a dialšia: {origoname}")
                        await voicechannel.edit(name=origoname)
                else:
                    await db.guildsetting.update_one({"voicechannelid": guildsetup["voicechannelid"]}, {"$unset": {"voicechannelid": ""}})

        reselllist = await db.guildsetting.find({}).to_list(None)

        await resellers.leaderboard(self, reselllist)

    async def auto_close_check(self):
        listof = db.ticketsdb.find({})
        guilds = await db.guildsetting.find({}).to_list(None)

        async for channeldata in listof:

            channel_id = channeldata.get("channelid")
            guild = list(
                filter(lambda i:  i["guildid"] == channeldata["guildid"], guilds))
            if len(guild) != 0:
                auto_on = guild[0].get("autodelete", False)
            else:
                auto_on = False
            # logg:nextcord.Thread = self.bot.get_channel(channeldata["error_channelid"])
            channel: TextChannel = self.bot.get_channel(channel_id)
            if channel:
                if len(channel.threads) == 0:
                    logger.error(f"Missing thread for {channeldata}")
                    await commend_menu.close_ticket(self, channel, channel, channeldata, "Missing thread")
                    return
                if msg := channel.last_message:
                    if channel.threads[0].last_message:
                        if channel.threads[0].last_message.created_at > msg.created_at:
                            msg = channel.last_message
                    msg_secs = (datetime.datetime.now(tz=tz) -
                                msg.created_at).total_seconds()

                elif msg := channel.threads[0].last_message:
                    msg_secs = (datetime.datetime.now(tz=tz) -
                                msg.created_at).total_seconds()
                else:
                    msgs = (await channel.history(limit=1).flatten())
                    if msgs and len(msgs) != 0:
                        msg = msgs[0]
                        msg_secs = (datetime.datetime.now(tz=tz) -
                                    msg.created_at).total_seconds()

                    else:

                        await db.ticketsdb.delete_one({"channelid": channel_id})
                        await channel.delete()

                if auto_on:

                    ivalue = await db.timedb.find_one({"channelid": channel_id})
                    if ivalue is None:

                        if not await db.serverusers.find_one({"channelid": channel_id}):

                            if int(msg_secs) >= 43200:

                                member = channel.guild.get_member(
                                    channeldata["userid"])
                                
                                    
                                mention_check = guild[0].get(
                                    "autodelete_mention", 1)
                                if  not  member:
                                    member_mention = None
                                elif mention_check == 1:
                                    member_mention = member.mention
                                elif mention_check == 2:
                                    member_mention = member
                                else:
                                    member_mention = None

                                tim2 = datetime.datetime.now(
                                    tz=tz)+datetime.timedelta(hours=12)
                                
                                if member:
                                    await db.timedb.insert_one({"userid": member.id, "channelid": channel_id, "error_channelid": channel.threads[0].id, "guildid": channel.guild.id, "datetime": tim2})
                                    datetimes = datetime.datetime.now(
                                        tz=tzsk)+datetime.timedelta(hours=12)
                                    view = closebutton(self.bot)
                                    view.bot = self.bot
                                    await channel.threads[0].send(f"Hello {member_mention}\n\n> If you want to keep this channel, send here any message or channel will be after <t:{int(time.mktime(datetimes.timetuple()))}:R> automatically deleted!\n\n**Kind Regards,**\n> {channel.guild.name}\n\n**Provided by**\n> {config.BRAND_URL}", view=view)
                                    logger.info(
                                        f"Request for close a ticket: {channeldata['channelid']} was sent and add to queue!")
                                else:
                                    tim2 = datetime.datetime.now(
                                        tz=tz)+datetime.timedelta(hours=1)
                                    await db.timedb.insert_one({"channelid": channel_id, "error_channelid": channel.threads[0].id, "guildid": channel.guild.id, "datetime": tim2})
                                    logger.warn(
                                        f"Member is None {channeldata['userid']} in auto_close_check, was add to queue")
                else:
                    if int(msg_secs) >= 604800:
                        print(f" must close {channel.name} ")
                        await commend_menu.close_ticket(self, channel, channel, channeldata, "Must-Close")

            else:
                await db.ticketsdb.delete_one({"channelid": channel_id})

        logowner = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)

        allprvchannels = db.ticketsdb.find({})
        txtvalue = "x"
        async for privchannel in allprvchannels:

            bi = self.bot.get_channel(privchannel.get("channelid"))
            if bi is None:
                txtvalue = txtvalue + \
                    f"\nthis channel not found: {privchannel.get('channelid')} deleting..."
                print(
                    f"this channel not found: {privchannel.get('channelid')} deleting...")
                await db.ticketsdb.delete_one({"channelid": privchannel.get('channelid')})

        if txtvalue == "x":

            pass
        else:
            await asyncio.sleep(10)
            await logowner.send(txtvalue)

    @tasks.loop(minutes=2)
    async def autoreport(self):
        print("autoreport running")
        datetime_utc = get_datetime_utc()

        

        allusersons = db.serverusers.find({})

        

        async for userons in allusersons:
            if userons["status"] == "confirmed":
                if "error" in userons:
                    userlastupt = userons["lastup"]
                    userlastupt = userlastupt.replace(
                        tzinfo=datetime.timezone.utc)
                    if userlastupt < (datetime.datetime.now(tz=tz) - datetime.timedelta(minutes=20)):
                        steamID64 = userons["steamID64"]

                        await helpers.req_stop_commend(userons["slot_id"], steamID64, userons["userid"])

                else:

                    if "lastup" in userons:

                        userlastupt = userons["lastup"].replace(
                            tzinfo=datetime.timezone.utc)
                        seconds = abs(
                            (datetime_utc-userlastupt).total_seconds())
                        if seconds > 1000:

                            # if not "whid" in  userons:
                            # always error when anybody delete commend channel what is active

                            check = await db.slottrans.find_one({"type": "sessions", "push": "post"})
                            if check is None:
                                await db.slottrans.insert_one({"type": "sessions", "push": "post", "slot_id": userons["slot_id"]})
                            else:
                                logger.error("SLOT IS STUCKED sessions")

                            break

            elif userons["status"] == "w8connect":

                if "lastup" in userons:

                    userlastupt: datetime.datetime = userons["lastup"]
                    userlastupt = userlastupt.replace(
                        tzinfo=datetime.timezone.utc)
                    seconds = abs((datetime_utc-userlastupt).total_seconds())

                    if seconds >= 480 and "hwid" not in userons or "hwid" in userons and seconds >= 600:
                        print("deleted from wlist")
                        reason = "TimeOut - time left to connect in to server"
                        await commend_menu.stop_waiting(self, userons, reason)

            elif userons["status"] == "done":
                userlastupt: datetime.datetime = userons["lastup"]
                userlastupt = userlastupt.replace(tzinfo=datetime.timezone.utc)
                seconds = abs((datetime_utc-userlastupt).total_seconds())

                if seconds >= 300:
                    await db.serverusers.delete_one({"_id": userons["_id"]})
            elif userons["status"] == "error" and "hwid" in userons:
                userlastupt: datetime.datetime = userons["lastup"]
                userlastupt = userlastupt.replace(tzinfo=datetime.timezone.utc)
                seconds = abs((datetime_utc-userlastupt).total_seconds())
                if seconds >= 480:
                    await db.serverusers.delete_one({"_id": userons["_id"]})

        await commend.commendingqueue(self)

    @tasks.loop(minutes=1)
    async def change_status(self):

        await self.bot.wait_until_ready()
        
        datetime_utc = get_datetime_utc()
        await db.bot.update_one({"_id": 0}, {'$set': {'activity': datetime_utc}, '$inc': {'uptime': 1}})

        
        activity = next(self.bot.statuses)

        if "Commending" in activity:
            allonserver = await db.serverusers.count_documents({})

            activity = f"Commending users: {allonserver}"
            activity_G = nextcord.Game(name=activity)

            await self.bot.change_presence(status=nextcord.Status.dnd, activity=activity_G)

        elif "guilds" in activity:
            activity = f"/help | {len(self.bot.guilds)} guilds"
            activity_G = nextcord.Game(name=activity)

            await self.bot.change_presence(status=nextcord.Status.dnd, activity=activity_G)
        else:
            activity_G = nextcord.Game(name=activity)
            await self.bot.change_presence(status=nextcord.Status.dnd, activity=activity_G)

    @aiocron.crontab('00 00 * * *', tz=tz)
    async def cornjobdayly():
        await db.statsdb.update_one({"_id": 0}, {"$set": {"daylycommended": 0, "daylycommended-users": 0, }})

    @aiocron.crontab('00 00 * * 7', tz=tz)
    async def cornjobweekly():
        await db.statsdb.update_one({"_id": 0}, {"$set": {"weeklycommended": 0, "weeklycommended-users": 0}})

    @aiocron.crontab('00 1 1 * *', tz=tz)
    async def cornjobmonthly():
        await db.statsdb.update_one({"_id": 0}, {"$set": {"monthlycommended": 0, "monthlycommended-users": 0}})

    @tasks.loop(minutes=1)
    async def autostart(self):
        print("autostart running")
        datetime_utc = get_datetime_utc()
        

        

        start = await db.waitinglist.find_one({"type": "start", "status": "go"})
        if start is None:
            async for start in db.waitinglist.find({"type": "start"}):
                dt: datetime.datetime = start["datetime"]
                dt = dt.replace(tzinfo=tz)
                different = abs((datetime_utc - dt).total_seconds())
                if different >= 15:
                    if await db.waitinglist.find_one({"_id": start["_id"]}):
                        if  await db.slotsdb.find_one({"steamID64":start['steamID64'],"push":"post"}) is None: # check if is not slot stucked 
                            await db.slottrans.insert_one({"slot_id": start["slot_id"], "steamID64": start['steamID64'], "push": "post", "type": "start", "amount": start["amount"]})
                        else:
                            logger.error("SLOT IS STUCKED sessions - start")
        else:
            await db.waitinglist.update_one({'_id': start["_id"]}, {'$set': {'status': "go", "datetime": datetime_utc}})
            if await db.waitinglist.find_one({"_id": start["_id"]}):
                if  await db.slotsdb.find_one({"steamID64":start['steamID64'],"push":"post"}) is None: # check if is not slot stucked 
                    await db.slottrans.insert_one({"slot_id": start["slot_id"], "steamID64": start['steamID64'], "push": "post", "type": "start", "amount": start["amount"]})
                else:
                    logger.error("SLOT IS STUCKED sessions - start ")

        stop = await db.waitinglist.find_one({"type": "stop", "status": "go"})

        if stop is None:
            async for stop in db.waitinglist.find({"type": "stop"}):
                cprint(f"checking stop {stop}", "yellow")
                dt: datetime.datetime = stop["datetime"]
                dt = dt.replace(tzinfo=tz)
                different = abs((datetime_utc - dt).total_seconds())
                print(different)
                if different >= 15:
                    if await db.waitinglist.find_one({"_id": stop["_id"]}):
                        if  await db.slotsdb.find_one({"steamID64":stop['steamID64'],"push":"post"}) is None: # check if is not slot stucked 
                            await db.slottrans.insert_one({"slot_id": stop["slot_id"], "steamID64": stop['steamID64'], "push": "post", "type": "stop"})
                        else:
                            logger.error("SLOT IS STUCKED sessions - stop")
        else:           
            if await db.waitinglist.find_one({"_id": stop["_id"]}):
                await db.waitinglist.update_one({'_id': stop["_id"]}, {'$set': {'status': "go", "datetime": datetime_utc}})
                if  await db.slotsdb.find_one({"steamID64":stop['steamID64'],"push":"post"}) is None: # check if is not slot stucked 
                    await db.slottrans.insert_one({"slot_id": stop["slot_id"], "steamID64": stop['steamID64'], "push": "post", "type": "stop"})
                else:
                    logger.error("SLOT IS STUCKED sessions - stop ")

    async def check_delete_keys(self, owner: User):
        if owner is None:
            return
        owner_id = owner.id
        backuplist = ""
        addbalance = {}
        keys = db.keysdb.find({"gifterid": owner_id})
        async for key in keys:

            wallet = key.get('wallet')
            amount = key.get('amount')
            slot_id = key.get('slot_id')
            active = key.get('active')
            backuplist += f"{key.get('key')}:{amount}:{key.get('slot_id')}:{wallet}:{active}\n"
            if wallet:
                if active:
                    if slot_id not in addbalance:
                        addbalance[slot_id] = 0
                    addbalance[slot_id] += amount
        file_object = io.BytesIO(backuplist.encode())
        file = nextcord.File(file_object, filename=f"{owner_id}.txt")
        backup_codes_keys = self.bot.get_channel(config.KEY_BACKUP_CHANNEL_ID)

        await backup_codes_keys.send(file=file, content="backup")
        await db.keysdb.delete_many({"gifterid": owner_id})

        for slot_id, bal in addbalance.items():

            if bal != 0:

                await helpers.addbal(self, bal, owner, slot_id, self.bot.user, None, 0, "Expired resell sub the all keys was refunded!")

    @tasks.loop(hours=1)
    async def subcheck(self):
        print("subcheck running")
        datetime_utc = get_datetime_utc()

        dt = datetime_utc.replace(tzinfo=None)

        subdbs = db.subdb.find({"disabled": False})

        async for sub in subdbs:

            if sub["datetime"] != 0:
                datetimes = sub["datetime"]
                tim2 = datetimes-datetime.timedelta(days=7)
                if dt >= datetimes:
                    await db.usersdb.update_one({'userid': sub["ownerid"]}, {'$set': {'reseller': False}})
                    if "guildid" in sub:
                        guild = self.bot.get_guild(sub["guildid"])
                        if guild:
                            logchannel = self.bot.get_channel(config.SUBSCRIPTION_LOG_CHANNEL_ID)
                            owner = self.bot.get_user(sub["ownerid"])
                            # idk if self can be
                            await taskss.check_delete_keys(self, owner)
                            await db.subdb.update_one({"guildid": sub["guildid"]}, {"$set": {"disabled": True, "expired": datetime_utc}})

                            # was there error: 'NoneType' object has no attribute 'id'
                            await logchannel.send(f"server expired sub for cb guild: {guild} - `{guild.id}` owner: {guild.owner.mention} `{guild.owner.id}`")
                            defguild = self.bot.get_guild(config.SUPPORT_GUILD_ID)

                            try:
                                owner = defguild.get_member(sub["ownerid"])
                            except Exception:
                                pass
                            else:
                                if owner:
                                    role = get(defguild.roles,
                                            id=config.TICKET_ARCHIVE_CATEGORY_ID)

                                    await owner.remove_roles(role)

                                    await logchannel.send(f"removed from {owner} `{owner.id}`")

                    else:

                        logchannel = self.bot.get_channel(config.SUBSCRIPTION_LOG_CHANNEL_ID)
                        owner = self.bot.get_user(sub["ownerid"])
                        # idk if self can be
                        await taskss.check_delete_keys(self, owner)
                        await db.subdb.update_one({"_id": sub["_id"]}, {"$set": {"disabled": True, "expired": datetime_utc}})

                        await logchannel.send(f"expired sub for cb ID: {sub['_id']}  owner: <@{sub['ownerid']}>")
                        defguild = self.bot.get_guild(config.SUPPORT_GUILD_ID)

                        try:
                            owner = defguild.get_member(sub["ownerid"])
                        except Exception:
                            pass
                        else:
                            if owner:
                                role = get(defguild.roles,
                                           id=config.TICKET_ARCHIVE_CATEGORY_ID)

                                await owner.remove_roles(role)

                                await logchannel.send(f"removed from {owner} `{owner.id}`")

                elif dt >= tim2:
                    if "alert" in sub and not sub["alert"] or "alert" not in sub:

                        if "guildid" in sub:
                            guild = self.bot.get_guild(sub["guildid"])
                            if guild:
                                subtype = sub["subtype"]
                                slotcount = sub["slotcount"]
                                if "buyer" in sub:
                                    buyer = self.bot.get_user(sub["buyer"])

                                    try:
                                        await buyer.send(f"**You need to pay in <t:{int(calendar.timegm(datetimes.timetuple()))}:D> (Payed at: lastpay, Expire at: <t:{int(calendar.timegm(datetimes.timetuple()))}:R>) for CommendBot resell subscription!**\n> Guild: {guild} - `{guild.id}`, Subscription type: {subtype}, Slots: {slotcount}\n> **Please go to <#925719726208978994> and open a Ticket, otherwise Bot will be disabled on your server!**(If you arent on support server join to server {config.BRAND_DISCORD_URL})")
                                    except Exception:
                                        logger.exception(" ")

                                else:
                                    buyer = self.bot.get_user(sub["ownerid"])

                                    channel = await buyer.create_dm()
                                    try:
                                        await channel.send(f"**You need to pay in <t:{int(calendar.timegm(datetimes.timetuple()))}:D> (Payed at: lastpay, Expire at: <t:{int(calendar.timegm(datetimes.timetuple()))}:R>) for CommendBot resell subscription!**\n> Guild: {guild} - `{guild.id}`, Subscription type: {subtype}, Slots: {slotcount}\n> **Please go to <#925719726208978994> and open a Ticket, otherwise Bot will be disabled on your server!**(If you arent on support server join to server {config.BRAND_DISCORD_URL})")
                                    except Exception:
                                        logger.exception(" ")

                                await db.subdb.update_one({"guildid": sub["guildid"]}, {"$set": {"alert": True}})

                        else:
                            subtype = sub["subtype"]
                            slotcount = sub["_id"]
                            if "buyer" in sub:
                                buyer = self.bot.get_user(sub["buyer"])

                                try:
                                    await buyer.send(f"**You need to pay in <t:{int(calendar.timegm(datetimes.timetuple()))}:D> (Payed at: lastpay, Expire at: <t:{int(calendar.timegm(datetimes.timetuple()))}:R>) for CommendBot resell subscription!**\n> ID: {slotcount}\n> **Please go to <#925719726208978994> and open a Ticket, otherwise Bot will be disabled on your server,all feature ll be dissabled and all generated keys ll be deleted!**(If you arent on support server join to server {config.BRAND_DISCORD_URL})")
                                except Exception:
                                    logger.exception(" ")
                            else:
                                buyer = self.bot.get_user(sub["ownerid"])

                                try:
                                    await buyer.send(f"**You need to pay in <t:{int(calendar.timegm(datetimes.timetuple()))}:D> (Payed at: lastpay, Expire at: <t:{int(calendar.timegm(datetimes.timetuple()))}:R>) for CommendBot resell subscription!**\n> ID: {slotcount}\n> **Please go to <#925719726208978994> and open a Ticket, otherwise Bot will be disabled on your server,all feature ll be dissabled and all generated keys ll be deleted!**(If you arent on support server join to server {config.BRAND_DISCORD_URL})")
                                except Exception:
                                    logger.exception(" ")
                            await db.subdb.update_one({"_id": sub["_id"]}, {"$set": {"alert": True}})
        panelsdb = db.usersdb.find({"expired": False})
        async for panel in panelsdb:
            datetimes = panel["expire"]
            if dt >= datetimes:
                await db.usersdb.update_one({"_id": panel["_id"]}, {"$set": {"expired": True}})

        timedbs = db.timedb.find({})

        async for tidb in timedbs:

            datetimes = tidb["datetime"]

            if dt >= datetimes:

                guild = self.bot.get_guild(tidb["guildid"])
                if guild:

                    channel = guild.get_channel(tidb["channelid"])
                    if not channel:

                        await db.timedb.delete_one({"channelid": tidb["channelid"]})
                    else:
                        print(f" auto close {channel.name} {guild.name}")
                        await commend_menu.close_ticket(self, channel, channel, tidb, "Auto-Close")
                else:
                    await db.timedb.delete_one({"channelid": tidb["channelid"]})


def setup(bot: Bot) -> None:
    bot.add_cog(taskss(bot))
