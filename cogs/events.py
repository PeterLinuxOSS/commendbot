import asyncio
import datetime
import io

import nextcord
import pymongo
import requests
from nextcord import Guild, Member, TextChannel
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from nextcord.utils import get
from termcolor import colored

import config
from cogs.bot_tasks import *
from cogs.commend import *
from cogs.commend_menu import commendbotbutton
from cogs.helpers import *
from cogs.slottrans import slottrans
from utils import *

print("start events")

class events(commands.Cog):

    def __init__(self, bot: Bot) -> None:
        self.bot = bot 
        
    async def check_guild(self):
        settingsdb =  await db.guildsetting.find().to_list(None)
        
        for guild in self.bot.guilds:
            settings = list(filter(lambda i: i["guildid"] ==guild.id,settingsdb))
            
            if len(settings) == 0: 
                await events.add_guild(self,guild)
            
        
    @commands.Cog.listener()
    async def on_ready(self):
        
        ip = requests.get('https://checkip.amazonaws.com').text.strip()
        if  await db.bot.find_one({"ip":ip}) is None:
        
            while True:
                botdb:dict = await db.bot.find_one({"_id":0})
                activity:datetime.datetime = botdb.get("activity").replace(tzinfo=tz)
                datetime_utc = get_datetime_utc()  
                msg_secs = (datetime_utc - activity).total_seconds()
                if msg_secs> 61:
                    await db.bot.update_one({"_id":0},{'$set': {'activity': datetime_utc,"botid":self.bot.user.id,"uptime":0,"ip":ip}}, )
                    break
                else:
                    await asyncio.sleep(1)
                    cprint(f"Bot is still online, waiting... {msg_secs}")
        else:
            datetime_utc = get_datetime_utc()  
            await db.bot.update_one({"_id":0},{'$set': {'activity': datetime_utc,"botid":self.bot.user.id,"uptime":0}}, )
        await db.slotsdb.update_many({}, {"$set": {"ready": False}})
        guildsdbs = db.guildsetting.find({"queuechannelid": {"$exists": True}, "queuemsgid": {"$exists": True}})
        async for guildsdb in guildsdbs:
            channel = self.bot.get_channel(guildsdb["queuechannelid"])
            if channel:
                msg = await channel.fetch_message(guildsdb["queuemsgid"])
                if msg:
                    embeds = msg.embeds
                    
                    embeds[0] = await commend.build_status_embed(1,9,1)      
                    await msg.edit(embeds=embeds)  
        
                
        
        
        msgs = "Stats:\n"   
        channel = self.bot.get_channel(config.WELCOME_CHANNEL_ID)        
        
        st = db.slottrans.find({}).sort("_id",pymongo.ASCENDING)
        cprint("statrting slottrans","yellow")
        async for tr in st:
            await slottrans.trans_update(self,tr)
            msgs+=f"{tr}  \n"
            await asyncio.sleep(1)
        cprint("finished slottrans","yellow") 
        
        
          
        self.bot.slottrans_ready =True
         
        
        
                    
                    
                
               
               
        await db.slotsdb.update_many({}, {"$set": {"ready": True}})
        lines = msgs.split("\n")
        if len(lines) > 10:
            file_object = io.BytesIO(msgs.encode())        
            file = nextcord.File(file_object,filename="record.txt")
            await channel.send(file=file)
                    
                
        else:        
            await channel.send(msgs)
    
        
        self.bot.slotsready = True
        
        
        
        

        logowner = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
        guild = self.bot.get_guild(config.LEGACY_GUILD_ID)
        

        hlist =  db.ticketsdb.find()
        async for userpr in hlist:
            guild  = self.bot.get_guild(userpr["guildid"])
            if guild:
                if not guild.get_member(userpr["userid"]): #when user left from the server
                    channel = self.bot.get_channel(userpr["channelid"])
                    await commend_menu.close_ticket(self,channel,channel,userpr,"Auto-Close-Left")
                        

                
        await logowner.send(f"commendbot is on {self.bot.version} at {timestamp}")        
        
          
                
            
        await events.check_guild(self)
        logger.debug(colored("bot is on","magenta"))       
        
                
                
        
        
                   
                   
    @commands.Cog.listener()
    async def on_message(self,message : nextcord.Message):      
        
        
        if "<@self.bot.user.id>" in message.content:
            await message.reply("Please use `/help` in slash commands")
            
        

        if message.guild is not None:
            if message.channel.id == config.NEWS_CHANNEL_ID:
                count, username, user_id, reason = extract_information(message.content.strip())
                if count:
                    await db.blacklistdb.insert_one({"datetime":message.created_at,"userid":int(user_id),"username":username,"reason":reason,"message":message.content,"count":int(count)})
                else:
                    logger.error(f"blacklist is none {message.content}")   
                                 
        if "transferbot" in message.content:                     
            if message.author.id == self.bot.owner_id or message.author.id in config.TRUSTED_BOT_IDS:
                msg = message.content.split(" ")
                user = self.bot.get_user(int(msg[3]))
                owner = self.bot.get_user(int(msg[1]))
                reselldb = await db.subdb.find_one({"ownerid":owner.id,"disabled":False,"pay":True})
                print("transferbot1")
                if user:
                    if reselldb:
                        reseller = True
                    
                        blacklistdb = await db.blacklistdb.find_one({"userid":int(msg[1])})
                        if not blacklistdb:
                            blacklistud = await db.blacklistdb.find_one({"userid":user.id})
                            if not blacklistud:
                                amount = int(msg[2])
                                if "-" in msg[4]: 
                                    slots = msg[4].split("-")
                                    userbalances =  db.balancesdb.find({"userid":int(msg[1])})
                                    found = False 
                                    async for mydb in userbalances:
                                        if str(mydb["slot_id"]) in slots:
                                            
                                        
                                            newamountg = mydb["amount"] - amount 
                                            
                                                
                                            
                                            if not (newamountg ) < 0:
                                                found = True
                                                await helpers.giftbal(self,reseller,mydb,int(msg[2]),message.channel,owner,user,message.guild,True) 
                                                break
                                            
                                            
                                            
                                                
                                            
                                        
                                            
                                    if not found:
                                        await message.channel.send("balance")
                                                                            
                                elif int(msg[4]) == 0:
                                    userbalances =  db.balancesdb.find({"userid":int(msg[1])})
                                    found = False 
                                    async for mydb in userbalances:
                                        
                                            
                                        
                                        newamountg = mydb["amount"] - amount 
                                        

                                        if not (newamountg ) < 0:
                                            found = True
                                            await helpers.giftbal(self,reseller,mydb,int(msg[2]),message.channel,owner,user,message.guild,True) 
                                            break
                                    
                                    if not found:
                                        await message.channel.send("balance")         
                                
                                
                                        
                                else:
                                    mydb = await db.balancesdb.find_one({"userid":int(msg[1]),"slot_id":int(msg[4])})
                                    await helpers.giftbal(self,reseller,mydb,int(msg[2]),message.channel,owner,user,message.guild,True) 
                            else:
                                await message.channel.send("blacklist-c")             
                        else:
                            await message.channel.send("blacklist-g")   
                    else:
                        pass   
                else:
                    await message.channel.send("user-invalid")     
            
                    
                
                    
                        
                

                
                    
                

        if message.guild is not None:
            if message.channel.category is not None:
                
                dbg = await db.timedb.find_one({"error_channelid": message.channel.id, "userid":message.author.id})
                if  dbg :
                    await db.timedb.delete_one({"channelid": message.channel.id})
                    await message.reply("Nice!")

    print("half events")
    @commands.Cog.listener()
    async def on_member_join(self,member: nextcord.Member):
        if member.id == self.bot.owner_id:
            guild = member.guild
            guildsett = await db.guildsetting.find_one({"guildid":guild.id})
            role = get(guild.roles, id=guildsett["supportroleid"])
            try:
                
                await member.add_roles(role)
            except Exception as ex:
                
                await member.send(f"server {guild.name} dont have enought perms: {ex}")
                await guild.leave()
        elif ticketdb:= await db.ticketsdb.find_one({"userid":member.id,"guildid":member.guild.id}):
            ticket:TextChannel = self.bot.get_channel(ticketdb["channelid"])
            if ticket:
                await ticket.set_permissions(member, send_messages=True, view_channel=True, read_messages=True,use_slash_commands=True,embed_links=True,attach_files=True,read_message_history=True)
                if await can_dm_user(member):
                    await member.send(f"We reconnected your existing ticket!({ticket.mention})")
                else:
                    await ticket.send("We reconnected your existing ticket!(Please enable dms)")

    @commands.Cog.listener()
    async def on_member_leave(self,member: nextcord.Member):
        channels =  db.ticketsdb.find({"guildid":member.guild.id})
        
        async for channeldb in channels:
            channel = self.bot.get_channel(channeldb["channelid"])
            await commend_menu.close_ticket(self,channel,channel,channeldb,"Auto-Close")
    
                

    @commands.Cog.listener()
    async def on_guild_join(self,guild: nextcord.Guild):
        await events.add_guild(self,guild)
    
    async def add_guild(self,guild:Guild):
        logowner = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
        
        for channel in guild.channels:  
            try:
                await channel.send("\u200b", delete_after=1)
            except Exception:
                try:
                    invchannel =await  guild.create_text_channel("setup-bot")
                except nextcord.errors.Forbidden:
                    logger.exception(f"Missing perms in setup-bot - addbot {guild.id}")
                    await guild.leave()
                    
            else:
                invchannel = channel
                break
        member_count = len(guild.members)
        true_member_count = len([m for m in guild.members if not m.bot])
        link = await invchannel.create_invite(max_age = 0)
        if link is None:
                link = await guild.system_channel.create_invite(max_age = 0)
        await logowner.send(f"Bot joined to server {guild.name} - {guild.id} , owner is {guild.owner.mention} - {guild.owner.id} , users + bots on server: {member_count} , only real members: {true_member_count} invite: {link}")
        role = get(guild.roles, name="CommendBot-Support-Role")
        if role is None:
            bot = guild.get_member(self.bot.user.id)
            if bot:
                if bot.guild_permissions.administrator:
                    try:
                        role = await guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF),hoist=True)
                    except Exception:
                        for channel in guild.channels:
                            try:
                                await channel.send("I dont have administrator permisions to manage your server,When you repair it you can invite me back!")
                            except Exception:
                                continue
                            else:
                                break
                        await guild.leave()
                else:
                    for channel in guild.channels:
                        try:
                            await channel.send("I dont have administrator permisions to manage your server,When you repair it you can invite me back!")
                        except Exception:
                            continue
                        else:
                            break
                    await guild.leave()
            else:
                for channel in guild.channels:
                    try:
                        await channel.send("I dont have administrator permisions to manage your server,When you repair it you can invite me back!")
                    except Exception:
                        continue
                    else:
                        break
                await guild.leave()
        tryfound = await db.subdb.find_one({"guildid":guild.id})
        if   tryfound :
            await db.guildsetting.insert_one({"guildid":guild.id,"ownerid":guild.owner.id,"setupbot":bool(False),  "autodelete": bool(True), "logonoff":bool(False), "supportroleid":role.id,"public":True})
            member = guild.owner
            
        else:
            
            tim2= nextcord.utils.utcnow()
            inviter = db.invitepool.find({}).sort("_id",pymongo.DESCENDING)
            member = None
            async for invite in inviter:
                _member = guild.get_member(invite["userid"])
                if _member:
                    if _member.guild_permissions.administrator or _member.id == guild.owner_id:
                        await db.invitepool.delete_many({"userid":inviter["userid"]})
                        member = _member
                        break
            if member is None:
                member = guild.owner
            docs = await db.subdb.count_documents({"userid":member.id})
            
            
            
            await db.subdb.insert_one({"guildid":guild.id, "datetime":tim2, "slotcount":1, "disabled":False, "ownerid":member.id, "subtype":2 if docs <=1 else 4,"pay":True if docs <=1 else False,"datetime":(datetime.datetime.now(tz=tz)+datetime.timedelta(days=30))})
            gstt ={"guildid":guild.id,"ownerid":member.id,"setupbot":bool(False),  "autodelete": bool(True), "logonoff":bool(False), "supportroleid":role.id,"public":True,}
            await db.guildsetting.insert_one(gstt)
            db_list = user_template(member,False,0,True if docs <=1 else False,"eng")
            await db.usersdb.insert_one(db_list)
            
            await events.auto_setup(self,guild,member,gstt)
        owner = self.bot.get_user(self.bot.owner_id)
        if owner and owner in guild.members:
        

            owner = guild.get_member(self.bot.owner_id)
            await owner.send(f"Bot joined to server {guild.name} - {guild.id} , owner is {guild.owner.mention} and set {member.mention} , users + bots on server: {member_count} , only real members: {true_member_count}, invite:  {link}")
            
        else:

            await owner.send(f"dBot joined to server {guild.name} - {guild.id} , owner is {guild.owner.mention}  and set {member.mention} , users + bots on server: {member_count} , only real members: {true_member_count}, invite:  {link}")

            
        
        
    async def auto_setup(self,guild:Guild,inviter:Member,gstt:dict):
        
                    
            
        
        bot = guild.get_member(self.bot.user.id)
        if not bot.guild_permissions.administrator:
            
       
            await inviter.send(f"I dont have administrator permission, invite me again with the administrator permission > {config.BRAND_NAME}/botinvite")
            await guild.leave()
            return
        
        embed = nextcord.Embed(
        title="Welcome to our Discord server!",
        description=f"Read all rules on [our rules page]({config.BRAND_RULES_URL}).",
        color=nextcord.Color.green()
        )
    
        embed.add_field(
            name="Subscription Status",
            value="Your free trial subscription has been activated for 1 month. Check your subscription status using `/mysubscriptions`.",
            inline=False
        )
        
        embed.add_field(
            name="CSGO Commends",
            value=f"Interested in buying CS:GO commends? Join our server [here]({config.BRAND_DISCORD_URL}).",
            inline=False
        )
        
        embed.add_field(
            name="Extend/Buy Resell Subscription",
            value=f"Want to extend or buy a resell subscription? Join our Discord [here]({config.BRAND_DISCORD_URL}).",
            inline=False
        )
        
        embed.add_field(
            name="Need Help?",
            value=f"Feel free to join our Discord and ask for assistance! [discord]({config.BRAND_DISCORD_URL})",
            inline=False
        )
        
        await inviter.send(embed=embed)
        
        
        
        lang =convert_lang("eng")
        
                
        category = get(guild.categories, name="CommendBot")
        if category is None:
            
                
            category = await guild.create_category("CommendBot")
                
        logchannel = get(guild.text_channels, name="commendbot-logs")
        if logchannel is None:
            logchannel  = await guild.create_text_channel('commendbot-logs', category=category)
        
        channel  = await guild.create_text_channel('commend', category=category)
        
        

        embed=nextcord.Embed(title=lang["create-title"], description=lang["create-description"], color=bluepr, timestamp=datetime.datetime.now())
        if guild.icon is None:
            embed.set_footer(text=guild)
        else:
            embed.set_footer(text=guild,icon_url=guild.icon.url)
        
        
         
        
        if "supportroleid" in gstt:
            role = get(guild.roles, id=gstt["supportroleid"])
            if role is None:
                role = await guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))
        else:
            role = await guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))

        
        


        await category.set_permissions(guild.default_role, read_messages=False, connect=False)
        await category.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True)
        await logchannel.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True,read_message_history=True)
        await channel.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True)
        
        msg = await channel.send(embed=embed , view=commendbotbutton(self.bot))
        
        await logchannel.edit(sync_permissions=True)
        await db.guildsetting.update_one({"guildid":guild.id}, {"$set": {"setupbot":True, "startupid":channel.id, "startupid-msg":msg.id, "logid":logchannel.id, "logonoff":True, "supportroleid":role.id,"categoryid":category.id}})
            
            
      
            
            
        
        

        
    @commands.Cog.listener()
    async def on_guild_remove(self,guild:Guild):
        if guild.name:
            subdb =await db.subdb.find_one({"guildid":guild.id})
            await db.serverusers.delete_many({"guildid":guild.id})
            owner = self.bot.get_user(self.bot.owner_id)
            sub = await db.subdb.find_one({"ownerid":subdb["ownerid"],"pay":True,"disabled":False})
            if not sub:
                userdb = await db.usersdb.find_one({'userid': subdb["ownerid"]})
                if userdb:
                    await db.usersdb.update_one({'userid': subdb["ownerid"]}, {'$set': {'reseller': False}})
            if guild.owner:
                await owner.send(f" left to server {guild.name} - {guild.id} , owner is {guild.owner.mention} - {guild.owner.id} , users + bots on server: {guild.member_count} , only real members: {guild.max_members}, invite:  0")
            else:
                await owner.send(f" left to server {guild.name} - {guild.id} , owner is none -  , users + bots on server: {guild.member_count} , only real members: {guild.max_members}, invite:  0")
            await db.guildsetting.delete_one({"guildid":guild.id})
            logowner = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
            if guild.owner:
                await logowner.send(f"Bot left from server {guild.name} - {guild.id} , owner is {guild.owner.mention} - {guild.owner.id} , users + bots on server: {guild.member_count} , only real members: {guild.max_members} ")
            else:
                await logowner.send(f"Bot left from server {guild.name} - {guild.id} , owner is none  , users + bots on server: {guild.member_count} , only real members: {guild.max_members} ")
            
        

def setup(bot: Bot) -> None:
    bot.add_cog(events(bot))
    
