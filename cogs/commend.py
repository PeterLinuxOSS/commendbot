

import asyncio
import datetime
import re
import subprocess

import nextcord
import pymongo
from nextcord import Embed, Interaction, User
from nextcord.ext import commands
from nextcord.ext.commands import Bot

import config
import utils.translates as translates
from cogs.helpers import helpers
from utils import (
    bluepr,
    convert_lang,
    db,
    get_lang,
    get_user_avatar,
    logger,
    queue_vip,
    sview,
    user_template,
)


class language(nextcord.ui.Select):
    def __init__(self, bot:Bot,lang,private:bool=False):
        self.private =private
        self.bot = bot 
        if not lang:
            lang = translates.eng
        selectOption = [
            nextcord.SelectOption(label=lang["menu-english"], emoji="🇬🇧",value="eng" ),
            nextcord.SelectOption(label=lang["menu-german"], emoji="🇩🇪", value="ger"),
            nextcord.SelectOption(label=lang["menu-sk/cz"], emoji="🇸🇰", value="sk"),
            nextcord.SelectOption(label=lang["menu-pt"], emoji="🇵🇹", value="pt"),
            nextcord.SelectOption(label=lang["menu-hu"], emoji="🇭🇺", value="hu"),
            nextcord.SelectOption(label=lang["menu-pl"], emoji="🇵🇱", value="pl"),
            
            
           

        ]
        super().__init__(placeholder=lang["menu-title"], min_values=1, max_values=1, options=selectOption,custom_id="language-menu")

    async def callback(self, interaction: nextcord.Interaction):

        lang = convert_lang(self.values[0])
        

        userdb = await db.usersdb.find_one({"userid":interaction.user.id})
        if userdb is None:
            await db.usersdb.insert_one(user_template(interaction.user,True,language=self.values[0]))
            
        else:
            await db.usersdb.update_one({"userid":interaction.user.id}, {"$set": {"language":self.values[0]}})
        embed,view =await commend.embed_helpmenu(self,lang,interaction.user)
        
        await interaction.message.edit(embed=embed,view=view)
        await interaction.send(lang["lang-update"],ephemeral=True)



    


            
                
        
            

class Confirm(nextcord.ui.Button):
    def __init__(self, bot:Bot , label):
        self.bot = bot 
    
        super().__init__(
            label=label, style=nextcord.ButtonStyle.green
        )
        
    async def callback(self, interaction: nextcord.Interaction):
            
        
            await interaction.response.defer() 
            
            await db.serverusers.update_one({"channelid":interaction.channel.id, "status":"w8connect"},[{"$set":{"button":False}}])
            
            
            ticketsdsb = await db.ticketsdb.find_one({"channelid":interaction.channel.id})
            if not ticketsdsb:
                logger.error(f"ticketdb isn none : {ticketsdsb}")
                await interaction.send("Your ticket is corrupted, please contact admin or developer of this bot")
                return
            msg =  await interaction.channel.fetch_message(ticketsdsb.get("msgid"))
            if not msg:
                
                logger.error(f"msgid is none: {ticketsdsb}","red")
                return
            logger.debug(f"Request of start commending for {interaction.channel_id} via Confirm")
            await commend.Request_start_Commending(self,interaction.user,interaction,interaction.channel,interaction.guild,msg)
            return
        











            
    



class StopCommending(nextcord.ui.View):
    def __init__(self,bot:Bot):
        super().__init__()
        self.value = None
        self.bot = bot 
    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @nextcord.ui.button(label="Stop Commending", style=nextcord.ButtonStyle.red)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.defer()
        langdb = await db.usersdb.find_one({"userid":interaction.user.id})
        await get_lang(langdb,interaction.guild)
    
            
            
        
            
            




class commend(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
        
  
                   
    async def stop_commending_all(self,slot_id):
        
        users =  db.serverusers.find({"status":"confirmed","slot_id":slot_id})
       

        async for userchannel in users:
            channel = self.bot.get_channel(userchannel["channelid"])
            langdb = await db.usersdb.find_one({"userid":userchannel["userid"]})
            await get_lang(langdb,channel.guild)
            if "CommendBot" in channel.category.name:
                
                commenddb = await db.serverusers.find_one({"channelid":channel.id})
                if commenddb is not None:
                    
                    steamID64 = commenddb["steamID64"]
                    
                    await helpers.req_stop_commend(commenddb["slot_id"],commenddb['steamID64'],commenddb["userid"])   
                    
                    await channel.send(f"Sending request for stop commending for {steamID64} ! by admins(Maintenance breakout)")
                        
                else:
                    await channel.send("error")
            await asyncio.sleep(5)
        
    
        


    
                   

        
    async def Request_start_Commending(self,customer : nextcord.User | nextcord.Member,channel : nextcord.TextChannel | nextcord.Interaction,real_channel:nextcord.TextChannel,guild: nextcord.Guild,msg =None  ):
            startcommending = False 
            userdb = await db.usersdb.find_one({"userid":customer.id})
            
            
            lang = await get_lang(userdb, guild)
            if isinstance(channel,Interaction):
                await channel.send(lang["Confirm-Confirm"], ephemeral=True)
            servercheck = await db.serverusers.find_one({"channelid":real_channel.id, "status":"w8connect"})
            
            
            if servercheck :

                amount = servercheck["amount"]
                steamID64 = str(servercheck["steamID64"])
                
                startcommending = True
                subdbsr = await db.subdb.find_one({"guildid":guild.id,"disabled":False,"pay":True})
                if subdbsr:
                    guildusers =  await db.serverusers.count_documents({"guildid":guild.id, "commended":True})
                    slotcount = int(subdbsr["slotcount"])
                    
                    
                    
                        
                    serveruserscont = slotcount - guildusers
                    if not serveruserscont >= 0:
                        error_code = "error4"
                        embed=nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
                        embed.set_footer(text=error_code)
                        await channel.send(embed=embed)
                    else:
                        if await db.waitinglist.find_one({"steamID64":steamID64}) is None:
                            
                            await helpers.req_start_commend(servercheck["slot_id"],steamID64,amount,real_channel,customer)
                        else:
                            embed=nextcord.Embed(title=lang["on_error"], description="This user is in a wait queue(bot is stucked), Please wait!", color=0xe74c3c)
                            await channel.send(embed=embed)
                            subprocess.run(["pm2", "restart", "0","1"])
                        
                else:
                    embed=nextcord.Embed(title=lang["on_error"], description="This server dont have activated commendbot sub or using free version!", color=0xe74c3c)
                    await channel.send(embed=embed)
                    

                
            if not startcommending:
                error_code = "error11"
                embed=nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
                embed.set_footer(text=error_code)
                await channel.send(embed=embed)
                if servercheck:
                    await db.serverusers.delete_one({"_id":servercheck["_id"]})
                
                

  
        
    async def commendingqueue(self):
        
        

        # Fetch necessary data from the database
        slotdbs = await db.slotsdb.find({}).to_list(None)
        guildsdbs = db.guildsetting.find({"queuechannelid": {"$exists": True}, "queuemsgid": {"$exists": True}})
        guildusers = db.serverusers.find({"slot_id":{"$exists": True}}).sort("slot_id", pymongo.ASCENDING)
        

        # Initialize classictext with a base message
        classictext = f"Here you can see all the customers with the amount of commends they requested.\n {config.EMOJI_COMMENDING} means currently commending \n {config.EMOJI_QUEUED}  waiting for connect to server. \n {config.EMOJI_NOT_COMMENDING} commending was stopped/error"

        count = 0
        
        async for guilduser in guildusers:
            
            slotdb = next((i for i in slotdbs if i['_id'] == guilduser["slot_id"]), None)
            if not slotdb["_id"] == 4:

                if slotdb and slotdb["name"] not in classictext:
                    classictext += f"\n\n**{slotdb['name']}** Slot : **{slotdb['currency']}** commends left for today:\n\n"

            user = self.bot.get_user(guilduser['userid'])
            if user or "hwid" in guilduser:
                if "hwid" in guilduser:
                    user_data = await db.usersdb.find_one({'hwid': guilduser["hwid"]})
                    username = user_data["login"] if user_data else None
                else:
                    username = (re.sub(r'[^\w]', ' ', user.name)) + "#" + user.discriminator
                    
                
                vpidb = queue_vip.get(user.id) if user else None
                emoji = config.EMOJI_COMMENDING
                if vpidb:
                    username = f"**{username} - {vpidb['role']}**"

                if guilduser["status"] == "w8connect":
                    emoji = config.EMOJI_QUEUED
                elif guilduser["status"] != "confirmed":
                    emoji = config.EMOJI_NOT_COMMENDING

                classictext += f"> {emoji} {username} - `{guilduser['steamID64']}` — `{guilduser['actualamount']}`**/**`{guilduser['amount']}`\n"
                count += 1
            else:
                logchannel = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
                await logchannel.send(f"<@{self.bot.owner_id}> I can't find user {guilduser['userid']} via bot. Try manually! Guild user: {guilduser['guildsid']}")

        if count == 0:
            classictext = "Currently the bot is free for new commend orders.\n\n"
        classictext += "\n".join([f"\n**{slotdb['name']}** Slot: **{slotdb['currency']}** commends left for today." for slotdb in slotdbs if slotdb["name"] not in classictext])
        classictext+="\n‎ "
        async for guildsdb in guildsdbs:
            
            channel = self.bot.get_channel(guildsdb["queuechannelid"])
            if not channel:
                await commend.queue_count_dc(self,guildsdb)
                continue

            try:
                msg = await channel.fetch_message(guildsdb["queuemsgid"])
            except nextcord.NotFound:
                await commend.queue_count_dc(self,guildsdb)
                continue
            except Exception:
                logger.exception("")
                
            
            zero = await commend.build_status_embed(0,9,0)        

            embed = Embed(title="🕦・CommendBot Queue", description=classictext, color=0xFFA500, timestamp=datetime.datetime.now())
            embed.set_footer(text=config.BRAND_FOOTER, icon_url=config.BRAND_LOGO_URL)

            try:
                await msg.edit(embeds=[zero,embed])
            except Exception:
                msg2 = await channel.send(embeds=[zero,embed])
                await db.guildsetting.update_one({"guildid": guildsdb["guildid"]}, {"$set": {"queuemsgid": msg2.id}})
                await msg.delete()
            

        
            

        await commend.jobbots(self)


    async def build_status_embed(client:int=9,panel:int=9,slots_mg:int=9) -> Embed:
        working = config.EMOJI_COMMENDING
        starting = config.EMOJI_QUEUED
        error = config.EMOJI_NOT_COMMENDING
        client_emoji = working if client == 0 else starting if  client == 1 else error
        panel_emoji = working if panel == 0 else starting if  panel == 1 else error
        slots_mg_emoji = working if slots_mg == 0 else starting if  slots_mg == 1 else error
        embed = nextcord.Embed(title="Commendbot Status", color=0x00ff00)  # Green color
        sl =""
        slots =  db.slotsdb.find({})
        async for slot in slots:
            if slot["enable"]:
                if slot["ready"]:
                    status = working
                else:
                    status = starting
            else:
                status = error  
            sl+=f"> {status}・{slot['name']} Slot \n"
            
            
        

        embed.description = f"{working}・Working {starting}・Starting {error}・Not Working/Disabled\n\n"\
                            f"{client_emoji}・Discord Client Status\n" \
                            f"{panel_emoji}・Panel Status\n"\
                            f"{slots_mg_emoji}・Slot Manager Status\n"\
                            f"{sl}"
                            
        return embed                        


        
    
    async def queue_count_dc(self,guildsdb:dict):
        if "queue_count" in guildsdb and guildsdb["queue_count"] > 3:
            await db.guildsetting.update_one({"guildid": guildsdb["guildid"]}, {"$unset": {"queuechannelid": "", "queuemsgid": "", "queue_count": ""}})
            if "logid" in guildsdb:
                channel = self.bot.get_channel(guildsdb["logid"])
                if channel:
                    await channel.send("I can't find channels for commending queue - use /setup to setup commending queue!")
        else:
            await db.guildsetting.update_one({"guildid": guildsdb["guildid"]}, {"$inc": {"queue_count": 1}})
        
        
        
                    
        
            
            
        
        
            
            
        
    
    
    
    
    
        

    
    async def embed_helpmenu(self,lang,member:User) -> Embed : # + view
        view  = None
        description = lang['helpmenu-description']
        
        for command, command_id in self.bot.global_commands.items():
            description = description.replace(f"/{command} ", f"</{command}:{command_id}>")
        
        embed=nextcord.Embed(title=lang["helpmenu-title2"], description=description, color=bluepr, timestamp=datetime.datetime.now())
        embed.set_author(name=lang["helpmenu-author"], icon_url=config.BRAND_LOGO_URL)
        embed.set_footer(text='\u200b',icon_url=get_user_avatar(member))
        
        view =sview(self.bot,language,member,None,lang)
        
        return embed,view

    async def jobbots(self):
    
        guildssetup =  db.guildsetting.find({"voicechannelid":{"$exists":True}})
        
        
        async for guildsetup in guildssetup:
            
            allonserver =  await db.serverusers.count_documents({"status":"confirmed"})
            
            voicechannel = self.bot.get_channel(guildsetup["voicechannelid"])
            
            if voicechannel is not None:

                chname = voicechannel.name
                chname = [int(s) for s in chname.split() if s.isdigit()]
                if  [0] in chname:
                
                    origoname = voicechannel.name.replace(str(chname[0]), str(allonserver))
                    print(f"nejaka value: {chname} a dialšia: {origoname}")
                    await voicechannel.edit(name=origoname)
            else:
                await db.guildsetting.update_one({"voicechannelid":guildsetup["voicechannelid"]}, {"$unset": {"voicechannelid": ""}})




def setup(bot: Bot) -> None:
    bot.add_cog(commend(bot))
    