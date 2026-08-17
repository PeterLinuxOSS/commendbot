

import calendar
import datetime
import os
import platform

import nextcord
from nextcord import Colour, Embed, TextChannel
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from nextcord.utils import get

import config
from cogs.commend import *
from cogs.commend_menu import commend_menu, commendbotbutton
from cogs.helpers import *
from cogs.resellers import resellers
from utils import *


class deflanguage_settings(nextcord.ui.Select):
    def __init__(self, bot:Bot,lang):
        
        self.bot = bot
        selectOption = [
            
            nextcord.SelectOption(label=lang["menu-english"], emoji="🇬🇧",value="eng" ),
            nextcord.SelectOption(label=lang["menu-german"], emoji="🇩🇪", value="ger"),
            nextcord.SelectOption(label=lang["menu-sk/cz"], emoji="🇸🇰", value="sk"),
            nextcord.SelectOption(label=lang["menu-pt"], emoji="🇵🇹", value="pt"),
            nextcord.SelectOption(label=lang["menu-hu"], emoji="🇭🇺", value="hu"),
            #nextcord.SelectOption(label=lang["menu-pl"], emoji="🇵🇱", value="pl"),
            
            
           

        ]
        super().__init__(placeholder=lang["menu-title"], min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        value = self.values[0]
        
        
        
        await interaction.send(f"Language was changed to {self.values[0]}")
        await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"default_lang":value}})
        
        await commend_menu.refreshguild(self,interaction.guild)

        


class guild_settings(nextcord.ui.Select):
    def __init__(self,bot:Bot):
        self.bot = bot
        selectOption = [
            nextcord.SelectOption(label="Set visibility", emoji="📖" ,value=1 ),
            nextcord.SelectOption(label="Set default language", emoji="📖" ,value=2 ), 
            nextcord.SelectOption(label="logging menu", emoji="📖" ,value=3 ), 
            nextcord.SelectOption(label="commend channel menu", emoji="📖" ,value=4 ), 
            nextcord.SelectOption(label="change-log menu", emoji="📖" ,value=5 ), 
            nextcord.SelectOption(label="Stats menu", emoji="📖" ,value=6 ), 
            nextcord.SelectOption(label="AutoClose menu", emoji="📖" ,value=7 ), 
            nextcord.SelectOption(label="End message menu", emoji="📖" ,value=8 ), 
            
            
            

            
         
            
            
           

        ]
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        
        
        if value == 1:
            guilddb =await db.guildsetting.find_one({"guildid":interaction.guild_id})
            if "public" in guilddb and guilddb["public"]:
                value = False
                description =(
                    "**Hey, be careful!** The following actions will be taken on this server and can not be undone:\n"
                    f"- Server will be **blocked** from **CommendBot network** {config.EMOJI_NO}\n"
                    f"- Someone **features** ll be **blocked** {config.EMOJI_NO}\n"
                    f"- {config.BRAND_NAME} ll __never__ **share** this **server**! {config.EMOJI_NO}\n")
            else:
                value = True
                description =(
                    "**Hey, be careful!** The following actions will be taken on this server and can not be undone:\n"
                    f"- Server will be **un-blocked** from **CommendBot network** {config.EMOJI_YES}\n"
                    f"- Someone **features** ll be **enabled** {config.EMOJI_YES}\n"
                    f"- {config.BRAND_NAME} ll __always__ **share** this **server**! {config.EMOJI_YES}\n")

            embed=Embed(description=description)
            embed.set_author(name="Warning", icon_url=config.IMAGE_WARNING_ICON)
            view = Confirm_clear(False)
            await interaction.send(embed=embed, view=view)
            # Wait for the View to stop listening for input...
            await view.wait()
            if view.value is None:
                embed=Embed(description=description)
                embed.set_author(name="Warning", icon_url=config.IMAGE_WARNING_ICON)
                await interaction.edit_original_message(embed=embed, view=None)
            elif view.value:
                await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"public":value}})
                

                print("Confirmed...")
        elif value == 2:
            await interaction.send(embed=build_embed(title="Default language menu",description="Set default language for your server.",colour=bluepr),view=sview(self.bot,deflanguage_settings,interaction.user,120,translates.eng))


        elif value == 3:
            selectOption = []
            guilddb =  await db.guildsetting.find_one({"guildid":interaction.guild_id})
            selectOption.append(nextcord.SelectOption(label="enable/disable logging ", emoji="📁" ,value=1))
            if guilddb["logonoff"]:
                selectOption.append(nextcord.SelectOption(label="change log channel", emoji="🗂️" ,value=2))
 
            embed = nextcord.Embed(title="Logs setup", description="Select what you need in the `Selection` down Below!", color=Colour.darker_gray(), timestamp=timestamp,)
            await interaction.send(embed=embed,view=sview(self.bot,logsmenu,interaction.user,120,selectOption,guilddb))
            
        elif value == 4:
            await interaction.send(view=sview(self.bot,privatechannel, interaction.user,120))
        elif value == 7:
            selectOption = []
            selectOption.append(nextcord.SelectOption(label="enable/disable autoclose", emoji="🗂️" ,value=1))
            selectOption.append(nextcord.SelectOption(label="mention", emoji="🗂️" ,value=2))
            embed = nextcord.Embed(title="Auto-Close Menu", description="Select what you need in the `Selection` down Below!", color=Colour.darker_gray(), timestamp=timestamp,)
            await interaction.send(embed=embed,view=sview(self.bot,autoclose_menu,interaction.user,120,selectOption))
            
            

  
  
class autoclose_menu(nextcord.ui.Select):
    def __init__(self,bot,selectOption):
        self.bot:Bot = bot
        
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):  
        value = int(self.values[0]) 
        guilddb:dict = await db.guildsetting.find_one({"guildid":interaction.guild_id})
        if value == 1:   
        
            if guilddb["autodelete"]:
                await interaction.send({"AutoDelete was Disabled "})
            else:
                await interaction.send({"AutoDelete was Enabled "})
            await db.guildsetting.update_one({'_id': guilddb["_id"]}, {'$set': {'autodelete': not guilddb["autodelete"]}})  
        elif value == 2:   
            selectOption = []
            def_option  =guilddb.get("autodelete_mention",1)
            if def_option == 1 :
                selectOption.append(nextcord.SelectOption(label="ping", emoji="🗂️" ,value=1,description="ex. @yournames",default=True))
            else:
                selectOption.append(nextcord.SelectOption(label="ping", emoji="🗂️" ,value=1,description="ex. @yournames",default=False))
            if def_option == 2 :
                selectOption.append(nextcord.SelectOption(label="nickname", emoji="🗂️" ,value=2,description="ex. yournames#0",default=True))
            else:
                selectOption.append(nextcord.SelectOption(label="nickname", emoji="🗂️" ,value=2,description="ex. yournames#0",default=False))
            embed = nextcord.Embed(title="Auto-Close Menu - Mention", description="Select what you need in the `Selection` down Below!", color=Colour.darker_gray(), timestamp=timestamp,)
            await interaction.send(embed=embed,view=sview(self.bot,autoclose_menu_mention,interaction.user,120,selectOption))
  
  
  
class autoclose_menu_mention(nextcord.ui.Select):
    def __init__(self,bot,selectOption):
        self.bot:Bot = bot
        
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):          
        await interaction.send(f"Option was changed to {self.values[0]}")
        await db.guildsetting.update_one({"guildid":interaction.guild_id}, {'$set': {'autodelete_mention': int(self.values[0])}})  
        

class logsmenu(nextcord.ui.Select):
    def __init__(self,selectOption,guildb):
        
        self.guildb =guildb
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        value = int(self.values[0])
        guildb =self.guildb
        if value == 1:
            if "logonoff" in guildb and not guildb["logonoff"]:
                other = nextcord.utils.get(interaction.guild.categories, name="CommendBot")
                if not other:
                    
                    overwrites = {interaction.guild.default_role: nextcord.PermissionOverwrite(read_messages=False)}
                    other = await interaction.guild.create_category("CommendBot",overwrites=overwrites)
                    if "supportroleid" in guildb:
                        role = get(interaction.guild.roles, id=guildb["supportroleid"])
                    if role is None:
                        role = await interaction.guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))
                    else:
                        role = await interaction.guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))
                    if role:
                        other.set_permissions(role,send_messages=True,read_message_history=True, read_messages=True, manage_messages=True, embed_links=True, attach_files=True, mention_everyone=True, use_external_emojis= True,add_reactions=True,connect=True,speak=True, mute_members=True, deafen_members=True, move_members=True,priority_speaker=True, send_messages_in_threads=True, use_slash_commands=True)
                channel = await other.create_text_channel("commendbot-logs")
                if channel:
                    await channel.edit(sync_permissions=True)
                    await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"logid":channel.id,"logonoff":True}})
                    await interaction.send(embed=embed_success("Successfully Enabled","Logging was successfully Enabled!"))
                else:
                    await interaction.send(embed=embed_error("Missing permissions","For someone reason we cant create channels/catgories on ur server!"))
            else:
                await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"logonoff":True}} ,{"$unset": {"logid":""}})
                await interaction.send(embed=embed_success("Successfully Disabled","Logging was successfully disabled!"))
                
                
        elif value == 2 :
            embed=Embed(title="Please ping a channel for commendbot logs", description="Just ping channel in the Chat", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            channel , msg  = await helpers.waitforrespon(self,interaction.channel, interaction.user,"channel")
            if channel:
                channel : TextChannel = channel
                
                await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"logid":channel.id,"logonoff":True}})
            
        
        
        
        

class privatechannel(nextcord.ui.Select):
    def __init__(self,bot:Bot):
        selectOption = [
            nextcord.SelectOption(label="Change-panel-channel", emoji="📁" ,value=2),
            nextcord.SelectOption(label="Change-private-channels-category", emoji="🗂️" ,value=3),
           
            

            
         
            
            
           

        ]
        self.bot = bot
       
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        
        
            


            
            
        if value == 2:
            embed=Embed(title="Please ping a channel to send the panel..", description="Just ping channel in the Chat or send id of channel", color=bluepr)
            embed.set_image(url=config.IMAGE_TUTORIAL_SETUP)
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            channel , msg = await helpers.waitforrespon(self,interaction.channel, interaction.user,"channel")
            if channel:
                channel : TextChannel = channel
                 
                await interaction.send(f"**{config.EMOJI_YES}  Successfully updated channel for panel**")           

                   
                pause = self.bot.pause
                if  pause:
                        value = await db.guildsetting.find_one({"guildid":config.SUPPORT_GUILD_ID})
                        timeg : datetime.datetime = value["time"]
                        
                        timeg = timeg.astimezone(tz=tzsk) + datetime.timedelta(hours=2)
                        print(timeg)
                        embed=Embed(title="Maintenance break", description=f"Bot is currently **unable**\nWill be available <t:{int(calendar.timegm(timeg.timetuple()))}:R>", color=0xcda618)
                        embed.add_field(name="Kind Regards,", value="r4p Services developers", inline=False)
                        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                        msg = await channel.send(embed=embed,view=None)
                        

                else:
                        
                        
                        lang =await get_lang(guild=channel.guild)
                        embed=nextcord.Embed(title=lang["create-title"], description=lang["create-description"], color=bluepr, timestamp=datetime.datetime.now())
                        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                        msg = await channel.send(content=None,embed=embed,view=commendbotbutton(self.bot))
            
            
            await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"setupbot":True, "startupid":channel.id, "startupid-msg":msg.id}})
            
            
        elif value == 3:
            await interaction.send('Just change category name to "CommendBot" ')
                    
                    
                

        

            
            
            

class user_settings(nextcord.ui.Select):
    def __init__(self,bot:Bot):
        self.bot = bot 
        selectOption = [
            nextcord.SelectOption(label="Change Language", emoji="📖" ,value=1 ),
            nextcord.SelectOption(label="About me", description="setup everything about private channels",emoji="⚒️" ,value=2 ), # transaction logs  + user infos + current balance on slots
            
            

            
         
            
            
           

        ]
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        
        
        if value == 1:
            pass



        

class settings(nextcord.ui.Select):
    def __init__(self,bot: Bot):
        self.bot = bot 
        selectOption = [
            nextcord.SelectOption(label="User-settings", description="setup everything about private channels",emoji="🔨" ,value=1 ),
            nextcord.SelectOption(label="Server-settings", description="setup everything about private channels",emoji="⚒️" ,value=2 ),
            nextcord.SelectOption(label="Sub-settings", description="setup everything about private channels",emoji="⚙️" ,value=3 ),
            
 

        ]
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        
        
        if value == 1:
            await interaction.send(embed=build_embed(title="User Settings", description="Select what you need in the `Selection` down Below!",colour=0x0a8f82),view=sview(self.bot, user_settings, interaction.user,120 ))
        elif value == 2:
            if interaction.user.guild_permissions.administrator or interaction.user.id == self.bot.owner_id:
                await interaction.send(embed=build_embed(title="Server Settings", description="Select what you need in the `Selection` down Below!",colour=0x0a8f82),view=sview(self.bot,guild_settings,interaction.user, 120))
            else:
                
                await interaction.send(embed=embed_error("Missing Permissions","Only the **Administrator** can use this command."), ephemeral=True)

        elif value == 3:
            selectOption = []
            if interaction.user.id == self.bot.owner_id:
                subsdb =  db.slotsdb.find({})
                selectOption.append(nextcord.SelectOption(label="add_slot" ,value="add" ))
            else:
                subsdb =  db.slotsdb.find({"admins":interaction.user.id})
            emojilist = ["🔴","🟠","🟡","🟢","🔵","🟣","🟤","⚫","⚪"]
            number = 1
            async for subdb in subsdb:
                selectOption.append(nextcord.SelectOption(label=subdb["name"],emoji=emojilist[number] ,value=subdb['_id'] ))
                number += 1
            if number != 1:
                
                await interaction.send("this function is in beta test",view= sview(self.bot, choose_sub,interaction.user,120,selectOption))
            else:
                await interaction.send(embed=embed_error("Missing Permissions","You dont have any slot to manage it "), ephemeral=True)
    
    
    
                    
class choose_sub(nextcord.ui.Select):
    def __init__(self,bot:Bot, selectOption: list[nextcord.SelectOption]):
        self.bot = bot 
        
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        if self.values[0] == "add":
            await interaction.send("Please ping or send id of customer ")
            customer,msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"user",120)
            if customer:
                await interaction.channel.send("Please ping or send id of bot")
                selfbot,msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"user",120)
                if selfbot:
                    await interaction.channel.send("Please send a t_ke_n")
                    msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"msg",120)
                    if msg:
                        
                        await resellers.addpremiumr(self,interaction.channel,customer,selfbot,msg.content)
            
        else:
            value = int(self.values[0])
            
            
            slotdb = await db.slotsdb.find_one({"_id":value})
            
            if interaction.user.id in slotdb["admins"] or interaction.user.id == self.bot.owner_id:
                await settings_c.slot_settings(self,interaction,value)
                


            else:
                await interaction.send("You dont have access to this slot!", ephemeral=True)


            
                
class sub_settings(nextcord.ui.Select):
    def __init__(self,bot:Bot,selectOption,slot_id:int):
        self.bot = bot 
        self.slot_id = slot_id
        
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        slot_id = self.slot_id


        
        if value == 0:
            embed=Embed(title="Reset Sequence Menu", description="**Select what you need in the `Selection` down Below!**", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)

        elif value == 1:
            await interaction.send("Send your name for slot")
            
            msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"msg",180)
            if msg:
                await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"name": msg.content}})
                await msg.delete()
                await interaction.delete_original_message()
                await interaction.channel.send(f"successfully changed name to: {msg.content}",delete_after=60)


        elif value == 2:
            embed=Embed(title="Please ping a channel for commendbot logs", description="Just ping channel in the Chat", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            channel ,  msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"channel")
            if channel:
                channel : TextChannel = channel
                await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"logchannelid": channel.id}})

                await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set log channel to { channel.mention}**")

               


        elif value == 3:
            embed=Embed(title="Please set a amount of commends per user every day(default value is 500)", description="Just type number/s in the Chat", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            number , msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"int")
            if number:
                
            
                await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"max_daily_commends": number}})
                await msg.delete()
                await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set max_daily_commends to { number}**")
            
        elif value == 4:
            embed=Embed(title="Please set a maximal amount of commends per user in one use (default value is 250)", description="Just type number/s in the Chat", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            number , msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"int")
            if number:
                slotdb = await db.slotsdb.find_one({"_id":slot_id})
                if slotdb["min_commends"] < number:
                    if number >= 10 :
        
                        await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"max_commends": int(msg.content)}})
                        await msg.delete()
                        await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set max_commends to { msg.content}**")
                    else:
                        await interaction.channel.send(embed=build_embed(title="Number cant be lower than 10!", description="Cancelled the Operation!", colour=Colour.red()), delete_after=60)
                else:
                    embed=Embed(title=f"error | number cant be lower than min_commends value({slotdb['min_commends']})", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await interaction.channel.send(embed=embed, delete_after=60)
                    
                



        elif value == 5:
            embed=Embed(title="Please set a minimal amount of commends per user in one use (default value is 10)", description="Just type number/s in the Chat", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            number , msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"int")
            if number:
                    slotdb = await db.slotsdb.find_one({"_id":slot_id})
                    if slotdb["max_commends"] < int(msg.content):
            
                        await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"min_commends": int(msg.content)}})
                        await msg.delete()

                        await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set min_commends to { msg.content}**")
                    else:
                        embed=Embed(title=f"error | number cant be lower than max_commends value({slotdb['max_commends']})", description="Cancelled the Operation!", color=0xff0000)
                        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                        await interaction.channel.send(embed=embed, delete_after=60)
                    
               


        elif value == 6:
            await interaction.send(f"Please send id of user to <@{config.OWNER_ID}> for delete or add admin to the commendbot")


        elif value == 7:
            slotdb = await db.slotsdb.find_one({"_id":slot_id})
            if slotdb["enable"]:
                await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"enable": False}})
                await interaction.channel.send(f"Slot with id {int(value[4])} was disabled now stopping commending user")
                await commend.stop_commending_all(int(value[4]))
                await interaction.channel.send("every process was stopped!")
            else:
                await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"enable": True}})
                await interaction.channel.send(f"Slot with id {int(value[4])} was enabled!")

        elif value == 8:
            embed=Embed(title="Please ping a channel for commend get/send", description="Just ping channel in the Chat", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            channel ,  msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"channel")
            if channel:
                channel : TextChannel = channel
                await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"commend_channelid": msg.channel_mentions[0].id}})

                await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set commend_channelid to { msg.channel_mentions[0].mention}**")

                
 

                
        elif value == 10:
            embed=Embed(title="Please set a slot pm2 id ", description="Just type number in the Chat", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            number ,  msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"int")
            if number:
                
                    
            
                await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"pm2id": int(msg.content)}})
                await msg.delete()
                await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set pm2id to { msg.content}**")
        elif value == 11:
            if "Linux" in platform.platform():
                embed=Embed(title="Please set a self-bot tok_en", description="Just type to_ken in the Chat", color=nextcord.Color.greyple())
                embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                await interaction.send(embed=embed)
                msg = await helpers.waitforrespon(self,interaction.channel,interaction.user,"msg")
                slotid = f"0{slot_id}"
                token = msg.content
                await msg.delete()
                with open(f'/root/selfbots/slot{slotid}/config.json', 'r+') as f:
                    data = json.load(f)
                    data['TOKEN'] = token
                    
                    f.seek(0)        
                    json.dump(data, f, indent=4)
                    f.truncate() 
                os.popen(f"pm2 restart slot{slotid}")
                await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"enable": True}})
                await interaction.channel.send("Nice we changed ur token")
                
                
            else:
                await interaction.send("Sorry we currently cant change ur token please contact developer of bot")
                
        elif value == 12:
            embed=Embed(title="Please set a amount of commends per user every day(default value is false) by resellers", description="Just type number in the Chat or false/False/x if you want to **disable** it!", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            msg:nextcord.Message = await helpers.waitforrespon(self,interaction.channel,interaction.user,"msg")
            if msg:
                if msg.content.isnumeric():
                    number = int(msg.content)
            
                    await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"max_daily_rcommends": number}})
                    await msg.delete()
                    await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set max_daily_commends to { number}**")         
                elif msg.content.strip().lower() in ["false", "x"]:
                     
                    await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"max_daily_rcommends": False}})
                    await msg.delete()
                    await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully disabled ")       
                else:
                    
                    embed=Embed(title="error | value isn't numeric(only integers)", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await interaction.channel.send(embed=embed)  
                    
        elif value == 13:
            embed=Embed(title="Please set a maximal amount of commends per reseller in one use (default value is False)", description="Just type number in the Chat or false/False/x if you want to **disable** it!", color=nextcord.Color.greyple())
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            msg:nextcord.Message = await helpers.waitforrespon(self,interaction.channel,interaction.user,"msg")
            if msg:
                if msg.content.isnumeric():
                    number = int(msg.content)
            
                    await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"max_rcommends": number}})
                    await msg.delete()
                    await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set max_rcommends to { number}**")         
                elif msg.content.strip().lower() in ["false", "x"]:
                     
                    await db.slotsdb.update_one({"_id":slot_id}, {"$set": {"max_rcommends": False}})
                    await msg.delete()
                    await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully disabled ")       
                else:
                    
                    embed=Embed(title="error | value isn't numeric(only integers)", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await interaction.channel.send(embed=embed)  
                    
            
                
                

                
            
                

        
        
        await settings_c.slot_settings(self,interaction,slot_id)
                
            
                
            

                

                

    
       

class settings_c(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 

    async def slot_settings(self,interaction :nextcord.Interaction, slot_id:int):
        
        embed=Embed(title="Slot-settings",  color=nextcord.Color.green())
        selectOption = []
        selectOption.append(nextcord.SelectOption(label="Set balance reset sequence",emoji="🔨" ,value=0 ))
        selectOption.append(nextcord.SelectOption(label="Set Name",emoji="🔨" ,value=1 ))
        selectOption.append(nextcord.SelectOption(label="Set log channel",emoji="🔨" ,value=2 ))
        selectOption.append(nextcord.SelectOption(label="Set max daily commends",description="Set maximum of daily used commends per user",emoji="🔨"  ,value=3 ))
        selectOption.append(nextcord.SelectOption(label="Set max daily reseller commends",description="Set maximum of daily used commends per reseller",emoji="🔨"  ,value=12 ))
        selectOption.append(nextcord.SelectOption(label="Set max commends",description="Set maximum of used commends one time",value=4 ))
        selectOption.append(nextcord.SelectOption(label="Set max reseller commends",description="Set maximum of used commends one time by reseller",emoji="🔨"  ,value=13 ))
        selectOption.append(nextcord.SelectOption(label="Set min commends",description="Set minimum of used commends one time", emoji="🔨" ,value=5 ))
        
        
        
        selectOption.append(nextcord.SelectOption(label="supervisor setup", emoji="🔨" ,value=6 ))
        selectOption.append(nextcord.SelectOption(label="change token",emoji="🔨" ,value=11 ))
        
        if interaction.user.id == self.bot.owner_id:
            selectOption.append(nextcord.SelectOption(label="Set enable status",emoji="🔨" ,value=7 ))
            selectOption.append(nextcord.SelectOption(label="Set commend channel",emoji="🔨" ,value=8 ))
            selectOption.append(nextcord.SelectOption(label="Set pm2 id",emoji="🔨" ,value=10 ))
            
            

        await interaction.message.edit(embed=embed, view=sview(self.bot,sub_settings,interaction.user,120,selectOption,slot_id))

def setup(bot: Bot) -> None:
    bot.add_cog(settings_c(bot))