import datetime

import nextcord
from nextcord import Embed, Interaction
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from nextcord.utils import get

import config
from cogs.commend_menu import commendbotbutton
from cogs.settings import settings

# (nothing needed from cogs.helpers)
from utils import bluepr, build_embed, convert_lang, db, embed_error, get_lang, sview


class deflanguage_auto(nextcord.ui.Select):
    def __init__(self,bot : Bot,lang):
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

    async def callback(self , interaction: nextcord.Interaction):
        value = self.values[0]
        
        await interaction.response.defer(ephemeral=False)
        
        lang =convert_lang(value)
                
        category = get(interaction.guild.categories, name="CommendBot")
        if category is None:
                bot = interaction.guild.get_member(self.bot.user.id)
                if bot.guild_permissions.administrator:
                    category = await interaction.guild.create_category("CommendBot")
                else:
                    await interaction.send(f"I dont have administrator permission, invite me again with the administrator permission > {config.BRAND_NAME}/botinvite")
                    await interaction.guild.leave()
                    return
        logchannel = get(interaction.guild.text_channels, name="commendbot-logs")
        if logchannel is None:
            logchannel  = await interaction.guild.create_text_channel('commendbot-logs', category=category)
        
        channel  = await interaction.guild.create_text_channel('commend', category=category)
        
        

        embed=nextcord.Embed(title=lang["create-title"], description=lang["create-description"], color=bluepr, timestamp=datetime.datetime.now())
        if interaction.guild.icon is None:
            embed.set_footer(text=interaction.guild)
        else:
            embed.set_footer(text=interaction.guild,icon_url=interaction.guild.icon.url)
        
        
        gstt = await db.guildsetting.find_one({"guildid":interaction.guild.id})
        if gstt:
            if "supportroleid" in gstt:
                role = get(interaction.guild.roles, id=gstt["supportroleid"])
                if role is None:
                    role = await interaction.guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))
            else:
                role = await interaction.guild.create_role(name="CommendBot-Support-Role", colour=nextcord.Colour(0x0000FF))

            
            


            await category.set_permissions(interaction.guild.default_role, read_messages=False, connect=False)
            await category.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True)
            await logchannel.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True,read_message_history=True)
            await channel.set_permissions(role, read_messages=True, send_messages=True, connect=True, speak=True)
            
            msg = await channel.send(embed=embed , view=commendbotbutton(self.bot))
            
            await logchannel.edit(sync_permissions=True)
            await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"setupbot":True, "startupid":channel.id, "startupid-msg":msg.id, "logid":logchannel.id, "logonoff":True, "supportroleid":role.id,"categoryid":category.id}})
            
            await interaction.send(f"**{config.EMOJI_YES}  Successfully created channels/categorys**")
        else:
            await interaction.send("error")

    
  
class voicestats(nextcord.ui.Select):
    def __init__(self,bot:Bot):
        self.bot = bot
        selectOption = [
            nextcord.SelectOption(label="Automatic-setup", description="setup ",emoji="🤖" ,value=1, ),
            nextcord.SelectOption(label="Change-voice-channel", emoji="📁" ,value=2),

            

            
         
            
            
           

        ]
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        
        


        
        if value == 1:
            category = nextcord.utils.get(interaction.guild.categories, name="CommendBot")
            if category is not None:
                voice = await category.create_voice_channel(name="Commending 0 customers")
            else:
                voice = await interaction.guild.create_voice_channel(name="Commending 0 customers")
                

            await interaction.send("please send channel name example: Commending 0 customers (if u want use default just send `0` or `no` in the Chat)")
            try:
                text = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and  message.author == interaction.user, timeout=180)
            except Exception:
                embed=Embed(title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                await interaction.send(embed=embed)
            else:
                if "0" == text.content  or "no" == text.content:
                    pass
                else:
                    await voice.edit(name=text.content)
                await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"voicechannelid":voice.id}})
        
                await interaction.send(f"**{config.EMOJI_YES}  Successfully set up voicestats ({voice.mention})**")
            

            

                        

        elif value == 2:
            embed=Embed(title="Please ping or send channel id a voice/text channel ", description="Just ping channel in the Chat", color=bluepr)
            embed.set_image(url=config.IMAGE_TUTORIAL_SETUP)
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)

            try:
                text : nextcord.Message = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and  message.author == interaction.user, timeout=180)
            except Exception:
                embed=Embed(title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                await interaction.send(embed=embed)
            else:
                if [0] not in text.channel_mentions :
                    if not text.content.isnumeric():
                        embed=Embed(title="error | invalid channel!", description="Cancelled the Operation!", color=0xff0000)
                        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                        await interaction.send(embed=embed)
                    else: 
                        setupchannel = int(text.content)
                        channel = self.bot.get_channel(setupchannel)
                        if channel is None:
                            embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                            await interaction.send(embed=embed)
                        else:
                            await interaction.send("please send channel name example: Commending 0 customers (if u want use default just send `0` or `no` in the Chat)")
                            try:
                                text = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and  message.author == interaction.user, timeout=180)
                            except Exception:
                                embed=Embed(title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                                if interaction.guild is not None or interaction.guild.icon.url is not None:
                                    embed.set_footer(text=interaction.guild , icon_url=interaction.guild.icon.url)
                                await interaction.send(embed=embed)
                            else:
                                if "0" == text.content  or "no" == text.content:
                                    await channel.edit(name="Commending 0 customers")
                                else:
                                    await channel.edit(name=text.content)
                                await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"voicechannelid":setupchannel}})
                        
                                await interaction.send(f"**{config.EMOJI_YES}  Successfully updated channel for status**")
                    
                    
                else:
                    setupchannel= text.channel_mentions[0].id
                    channel = self.bot.get_channel(setupchannel)
                    if channel is None:
                        embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                        await interaction.send(embed=embed)
                    else:
                        await interaction.send("please send channel name (if u want use default just send `0` or `no` in the Chat)")
                        try:
                            text = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and  message.author == interaction.user, timeout=180)
                        except Exception:
                            embed=Embed(title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                            await interaction.send(embed=embed)
                        else:
                            if "0" == text.content  or "no" == text.content:
                                await channel.edit(name="Commending 0 customers")
                            else:
                                await channel.edit(name=text.content)
                        
                        await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"voicechannelid":setupchannel}})
                        
                        await interaction.send(f"**{config.EMOJI_YES}  Successfully updated channel for status**")

                    
                    
                    
class queuestats(nextcord.ui.Select):
    def __init__(self,bot:Bot,):
        self.bot = bot 
        selectOption = [
            nextcord.SelectOption(label="Automatic-setup", description="setup ",emoji="🤖" ,value=1, ),
            nextcord.SelectOption(label="Change-queue-channel", emoji="📁" ,value=2),

            

            
         
            
            
           

        ]
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        
        


        
        if value == 1:
            

            category = nextcord.utils.get(interaction.guild.categories, name="CommendBot")
            if category is not None:
                bot = interaction.guild.get_member(self.bot.user.id)
                if bot.guild_permissions.administrator:
                    channel = await category.create_text_channel(name="🕒・Commending queue")
                else:
                    await interaction.send(f"I dont have administrator permission, invite me again with the administrator permission > {config.BRAND_NAME}/botinvite")
                    await interaction.guild.leave()
                    return
            else:
                channel = await interaction.guild.create_text_channel(name="🕒・Commending queue")
                

            
            classictext = f"Here you can see all the customers with the amount of commends they requested.\n {config.EMOJI_COMMENDING} means currently commending | {config.EMOJI_QUEUED}  commending has stopped/paused.\n\n"
            embed=Embed(title="🕦・CommendBot Queue", description=classictext, color=0xFFA500)
            msg = await channel.send(embed=embed)
            await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"queuechannelid":channel.id, "queuemsgid":msg.id}})

            
    
            await interaction.send(f"**{config.EMOJI_YES}  Successfully set up queuestats ({channel.mention})**")

        elif value == 2:
            embed=Embed(title="Please ping or send channel id of text channel ", description="Just ping channel in the Chat", color=bluepr)
            
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)

            try:
                text : nextcord.Message = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and  message.author == interaction.user, timeout=180)
            except Exception:
                embed=Embed(title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                await interaction.send(embed=embed)
            else:
                if [0] not in text.channel_mentions :
                    if not text.content.isnumeric():
                        embed=Embed(title="error | invalid channel!", description="Cancelled the Operation!", color=0xff0000)
                        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                        await interaction.send(embed=embed)
                    else: 
                        setupchannel = int(text.content)
                        channel = self.bot.get_channel(setupchannel)
                        if channel is None:
                            embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                            await interaction.send(embed=embed)
                        else:
                            await interaction.send("please send channel name (if u want use default just send `0` or `no` in the Chat)")
                            try:
                                text = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and  message.author == interaction.user, timeout=180)
                            except Exception:
                                embed=Embed(title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                                if interaction.guild is not None or interaction.guild.icon.url is not None:
                                    embed.set_footer(text=interaction.guild , icon_url=interaction.guild.icon.url)
                                await interaction.send(embed=embed)
                            else:
                                classictext = f"Here you can see all the customers with the amount of commends they requested.\n {config.EMOJI_COMMENDING} means currently commending | {config.EMOJI_QUEUED}  commending has stopped/paused.\n\n"
                                embed=Embed(title="🕦・CommendBot Queue", description=classictext, color=0xFFA500)
                                msg = await channel.send(embed=embed)
                                await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"queuechannelid":channel.id, "queuemsgid":msg.id}})
                    
                    
                else:
                    setupchannel= text.channel_mentions[0].id
                    channel = self.bot.get_channel(setupchannel)
                    if channel is None:
                        embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                        await interaction.send(embed=embed)
                    else:
                        
                        classictext = f"Here you can see all the customers with the amount of commends they requested.\n {config.EMOJI_COMMENDING} means currently commending | {config.EMOJI_QUEUED}  commending has stopped/paused.\n\n"
                        embed=Embed(title="🕦・CommendBot Queue", description=classictext, color=0xFFA500)
                        msg = await channel.send(embed=embed)
                        await db.guildsetting.update_one({"guildid":interaction.guild.id}, {"$set": {"queuechannelid":channel.id, "queuemsgid":msg.id}})
                        await interaction.send(f"**{config.EMOJI_YES}  Successfully updated channel for status**")

                    
                        
                    
            
            
            
  
    
class stats(nextcord.ui.Select):
    def __init__(self,bot:Bot ):
        self.bot = bot 
        selectOption = [
            nextcord.SelectOption(label="Voice-commending", description="setup information how many user now commending ",emoji="📊" ,value=1, ),
            nextcord.SelectOption(label="Commending Queue", description="setup Commending Queue",emoji="⏳" ,value=2, ),
    
            

            
         
            
            
           

        ]
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        
        
        lang = await get_lang(guild=interaction.guild)


        
        if value == 1:
            embed=Embed(title="Voice-commending", description=lang["menu-setup-description"], color=bluepr)
            await interaction.send(embed=embed,view=sview(self.bot , voicestats, interaction.user,120))
        elif value == 2:
            embed=Embed(title="Commending Queue", description=lang["menu-setup-description"], color=bluepr)
            await interaction.send(embed=embed,view=sview(self.bot, queuestats, interaction.user,120))

                
                        
                        
                    

        
            
                
    
class setupg(nextcord.ui.Select):
    def __init__(self,bot:Bot, lang):
        self.bot = bot 
        self.lang =lang  
        selectOption = [
            nextcord.SelectOption(label="Automatic setup",emoji="🤖" ,value=1, ),
            #nextcord.SelectOption(label="Setup-private channels", description="setup everything about private channels",emoji="📩" ,value=f"{userid}-22", ),
            nextcord.SelectOption(label="Setup-stats", emoji="📊" ,value=2),
            nextcord.SelectOption(label="Setup-settings", emoji="⚙️" ,value=3),

            
        
            
            
        

        ]
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        value = int(self.values[0])
        
        
            
        lang = convert_lang(self.lang)

        
        print(value)
        if value == 1:
            
            if interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.administrator or interaction.user.id == self.bot.owner_id:
                
                await interaction.send(embed=build_embed(title="Select default language.", description="Select default language for your guild",colour=bluepr),view=sview(self.bot, deflanguage_auto,interaction.user,120,lang))
            else:
            
                await interaction.send(embed=embed_error("Missing Permissions","Only the **Administrator** can use this command."), ephemeral=True)

            
        
        elif value == 2:

            embed=Embed(title=lang["menu-setup-title-stats"], description=lang["menu-setup-description"], color=bluepr)
            await interaction.send(embed=embed,view=sview(self.bot, stats, interaction.user, 120))
        elif value == 3:
            embed=Embed(title=lang["menu-setup-title"], description="settings", color=bluepr)
            await interaction.send(embed=embed, view= sview(self.bot, settings,interaction.user,120))
    
        
                

        

class setup_c(commands.Cog):

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        
        
    
            
        
    
        
    @nextcord.slash_command(name="setup",description="Select channel for startup",force_global=True,dm_permission=False)
    async def setup_command(self,interaction: Interaction,):
        if interaction.user.guild_permissions.administrator or interaction.user.id == self.bot.owner_id:
            
            
            userdb = await db.usersdb.find_one({"userid":interaction.user.id})
            if userdb is None:
                
                lang = "eng"
            else:
                lang = userdb["language"]
                    
            embed=Embed(title="Select what you need in the `Selection` down Below!", color=0x0a8f82)
            embed.set_author(name="Setup-Systems", icon_url="https://images-ext-2.discordapp.net/external/0myGg1NtjeFXS1h0AhHtiWa02x5hbn2aZzscmtAuJkw/https/emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/lg/57/gear_2699.png")
            await interaction.send(embed=embed, view=sview(self.bot,setupg,interaction.user,120, lang))
            
        else:
            embed=Embed(title=f"{config.EMOJI_NO}  You are not allowed to run this command!", color=0xff0000)
            embed.add_field(name="You need these Permissions:", value="> `ADMINISTRATOR`", inline=False)
            if interaction.guild.icon and interaction.guild:
                embed.set_footer(text=interaction.guild,icon_url=interaction.guild.icon.url)
            await interaction.send(embed=embed, ephemeral=True)



def setup(bot: Bot) -> None:
    bot.add_cog(setup_c(bot))
    