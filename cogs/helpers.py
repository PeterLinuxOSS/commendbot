import datetime
import math
import re
import typing
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import nextcord
from bson import ObjectId
from disposable_email_domains import blocklist
from key_generator.key_generator import generate as generate_id
from nextcord import Colour, Embed, Guild, Interaction, Member, TextChannel, User
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from random_object_id import generate
from termcolor import cprint

import config
from utils import (
    bluepr,
    can_dm_user,
    db,
    embed_error,
    favoriteguilds,
    feescalc,
    get_datetime_utc,
    get_rules,
    html_verify,
    is_number,
    logger,
    logo,
    mail_regex,
    server_name,
    smtp,
    timestamp,
    user_template,
)


class Add_mail(nextcord.ui.Modal):
    def __init__(self,bot):
        self.bot:Bot = bot
        super().__init__(
            "Fill Required Information About Your Account",
            timeout=None
        )
        self.first_name = nextcord.ui.TextInput(
            label="Your First Name",
            min_length=1,
            max_length=50,
            placeholder="e.g. Peter",
            required=True
        )
        self.add_item(self.first_name)
        self.last_name = nextcord.ui.TextInput(
            label="Your Last Name(not requried)",
            min_length=2,
            max_length=50,
            placeholder="e.g. Mrkvička",
            
            required=False
        )
        self.add_item(self.last_name)

        self.mail = nextcord.ui.TextInput(
            label="Your Mail adress",
            min_length=4,
            max_length=321,
            placeholder=f"e.g. example@{config.MAIL_DOMAIN}",
            required=True
        )
        self.add_item(self.mail)
        

        

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.edit(content="Please Wait!",view=nextcord.ui.View(),embed=None)
        mail = self.mail.value.strip()
        first_name = self.first_name.value.strip()
        last_name = (self.last_name.value.strip() if self.last_name.value else None)
        if(re.fullmatch(mail_regex, mail)):
            if not any(name in first_name for name in ["test","try","troll"]):
                if mail.partition('@')[2] not in blocklist and mail.partition('@')[2] not in {"test.com","test.try"}:
                    verification_code = generate_id(2,"-",4,4,capital="all").get_key()
                    html = html_verify(verification_code)

                    # Create a multipart message container
                    message = MIMEMultipart()
                    message['From'] = config.MAIL_FROM_NOREPLY
                    message['To'] = mail
                    message['Subject'] = 'Email Verification'

                    # Attach the HTML content to the email
                    message.attach(MIMEText(html, 'html'))
                    try: 
                        await smtp.sendmail(config.MAIL_NOREPLY, mail, message.as_string())   
                    except aiosmtplib.SMTPServerDisconnected: 
                        await smtp.connect()
                        await smtp.sendmail(config.MAIL_NOREPLY, mail, message.as_string())
                    
                    await db.usersdb.update_one({'userid': interaction.user.id}, {'$set': {'mail': mail,"first_name":first_name,"last_name":last_name,"verify":verification_code}})
                    await interaction.edit_original_message(content="Please check your email inbox.",view=address_button(self.bot))
                    
                else:
                    await interaction.send("Please enter your permanent email address!!",view=address_button(self.bot))
            else:
                await interaction.send("Please enter your real first and last Name!!! ",view=address_button(self.bot))
        else:
            await interaction.send("Your email address is Invalid!",view=address_button(self.bot))    


class address_button(nextcord.ui.View):
    def __init__(self,bot):
        super().__init__(timeout=None)
        self.bot = bot
        
 
    @nextcord.ui.button(label="Fill Now!", style=nextcord.ButtonStyle.green,custom_id="startform")
    async def address_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        button.disabled=True
        await interaction.response.send_modal(Add_mail(self.bot))
        
        
        
class re_address_button(nextcord.ui.Button):
    def __init__(self, bot:Bot):
        self.bot = bot
        

        super().__init__(
            label="ReSend Mail", style=nextcord.ButtonStyle.green,custom_id="mail_address"
        )
        
    
    async def callback(self, interaction: nextcord.Interaction):    
        data = await db.usersdb.find_one({"userid":interaction.user.id,"verify":{"$exists":True}})
        if data:
            if isinstance(data["verify"],str):
                mail = data["mail"]
                verification_code = generate_id(2,"-",4,4,capital="all").get_key()
                html = html_verify(verification_code)

                # Create a multipart message container
                message = MIMEMultipart()
                message['From'] = config.MAIL_FROM_NOREPLY
                message['To'] = mail
                message['Subject'] = 'Email Verification'

                # Attach the HTML content to the email
                message.attach(MIMEText(html, 'html'))
                try: 
                    await smtp.sendmail(config.MAIL_NOREPLY, mail, message.as_string())   
                except aiosmtplib.SMTPServerDisconnected: 
                    await smtp.connect()
                    try:
                        await smtp.sendmail(config.MAIL_NOREPLY, mail, message.as_string())
                    except Exception:
                        logger.exception("exeption in send mail") 
                
                await db.usersdb.update_one({'userid': interaction.user.id}, {'$set': {"verify":verification_code}})
                await interaction.edit(content="Please check your email inbox,we resent it",view=nextcord.ui.View())
            else:
                if data["verify"]:
                    await interaction.send("👍You are verified!👍",view=nextcord.ui.View(),embed=None)     
                else:
                    await interaction.send("You arent verified!",view=nextcord.ui.View(),embed=None)     
        else:
           
            await interaction.send("Error - report that via /report -err 191vr")     
class Confirm_clear(nextcord.ui.View):
    def __init__(self, ephemeral):
        super().__init__()
        self.value = None
        self.ephemeral = ephemeral

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Confirming", ephemeral=self.ephemeral)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Cancelling", ephemeral=self.ephemeral)
        self.value = False
        self.stop()


class Check_show_cbprices_header(nextcord.ui.View):
    def __init__(self,bot:Bot):
        super().__init__(timeout=None)
        self.bot = bot
        
    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @nextcord.ui.button(label="Buy Now!", style=nextcord.ButtonStyle.blurple)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await helpers.buy_commends_header(self,interaction,interaction.user)


class Check_cbprice(nextcord.ui.View):
    def __init__(self,bot:Bot):
        super().__init__(timeout=888)
        self.bot = bot
        
    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @nextcord.ui.button(label="Check Pricing", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(Show_cbprice(self.bot))
        
        
        
class Show_cbprice(nextcord.ui.Modal):
    def __init__(self,bot:Bot):
        super().__init__(
            "CS:GO/CS2 commends calculator",
            timeout=None
        )

        self.budget = nextcord.ui.TextInput(
            label="What is your budget?(in €)",
            min_length=1,
            max_length=20,
            placeholder="5.5"
        )
        self.add_item(self.budget)
        self.bot = bot
        

    async def callback(self, interaction: nextcord.Interaction) -> None:
        value = self.budget.value
        value = value.replace("€","").replace(",",".")
        respond = is_number(value)
        if respond:
            result = float(value)
            if result > 0:
                
                
                amount = result * 100 if result <= 1 else result * 100 * 100 / 90 if result <= 1.83 else result * 100 * 100 / 85 if result <= 2.55 else result * 100 * 100 / 80 if result <= 3.075 else result * 100 * 100 / 75 if result <= 5.0 else result * 100 * 100 / 70 if result <= 5.55556 else result * 100 * 100 / 65 if result <= 7.14286 else result * 100 * 100 / 60 if result <= 8.92857 else result * 100 * 100 / 55 if result <= 10.7143 else result * 100 * 100 / 50
                amount = math.floor(amount)
                
                await interaction.send(f"For **{value}€** you ll get **{amount}** commends",ephemeral=True)
            else:
                await interaction.send(f"Budget: **{value}** cant be negative number!!",ephemeral=True)  
        else:
            await interaction.send(f"Budget: **{value}** is not numeric!!",ephemeral=True)      
                
class waitforresponse():
    def __init__(self,bot,channel:TextChannel,user:User,timeout:float = 180) -> typing.Tuple[typing.Union[None,TextChannel,User,Member,int,float],nextcord.Message]:
        self.check = "msg"
        self.bot:Bot = bot
        self.channel: TextChannel = channel
        self.timeout = timeout
    
    async def msg(self):
        self.check = "msg"
        await waitforresponse.f(self)
    
    async def channel(self):
        self.check = "channel"
        await waitforresponse.f(self)
    
    async def user(self):
        self.check = "user"
        await waitforresponse.f(self)
    
    async def member(self):
        self.check = "member"
        await waitforresponse.f(self)
    async def int(self):
        self.check = "int"
        await waitforresponse.f(self)
    async def float(self):
        self.check = "float"
        await waitforresponse.f(self)
    
    
    
    async def f(self):
        check = self.check
        channel = self.channel
        timeout = self.timeout
        try:
            msg : nextcord.Message = await self.bot.wait_for('message', check=lambda message: message.channel == channel and  message.author.id == user.id  , timeout=timeout)
            
        except Exception:
            
            
            embed=nextcord.Embed(title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                
            await channel.send(embed=embed)
            return None
        else:
            if check == "msg":
                return msg 
            elif check == "channel":
                if msg.channel_mentions:
                    channelg = msg.channel_mentions[0]
                    

                    return channelg , msg 

                else:
                    if is_number(msg.content):
                        channelg = self.bot.get_channel(int(msg.content))
                        if channelg:
                            return channelg , msg 
                        else:
                            return None, msg 


                    embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg 
            elif check == "user":
                if msg.mentions:
                    user = msg.mentions[0]
                    

                    return user , msg 

                else:
                    if is_number(msg.content):
                        userg = self.bot.get_user(int(msg.content))
                        if userg:
                            return userg, msg 
                        else:
                            return None, msg 


                    embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg 
            elif check == "member":
                if msg.mentions:
                    member = msg.mentions[0]
                    

                    return member ,msg

                else:
                    if is_number(msg.content):
                        member = channel.guild.get_member(int(msg.content))
                        if member:
                            return member, msg
                        else:
                            return None, msg 


                    embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg 
            elif check == "int":
                if msg.content.isnumeric():
                    number = int(msg.content)
                    return number, msg
                else:
                    embed=Embed(title="error | value isn't numeric(only integers)", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg
                
            elif check == "float":
                if is_number(msg.content):
                    number = float(msg.content)
                    return number, msg
                
                else:
                    embed=Embed(title="error | value isn't numeric", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg                
    

        
      




class helpers(commands.Cog):
    
    

    def __init__(self, bot: Bot) -> None:
        self.bot = bot 
        
     
    TESTING_GUILD_ID = [config.SUPPORT_GUILD_ID] 
    
    async def req_start_commend(slot_id:int,steamID64:int,amount:int,channel:TextChannel,customer:User):
        datetime_utc = get_datetime_utc()  
         
        dictlist ={"slot_id":slot_id, "steamID64":steamID64,"amount":amount,"channelid":channel.id,"status":"wait", "userid":customer.id,"datetime":datetime_utc,"type":"start"}
        await db.waitinglist.insert_one(dictlist)
        
    async def req_stop_commend(slot_id:int,steamID64:int,customer_id:int):
        datetime_utc = get_datetime_utc()  
        dictlist ={"userid":customer_id,"slot_id":slot_id, "steamID64":steamID64,"status":"wait", "datetime":datetime_utc,"type":"stop"}
        await db.serverusers.update_one({'steamID64': steamID64}, {'$set': {'status': "stoped"}})
        await db.waitinglist.insert_one(dictlist)
        
 
    
    async def welcom_message(self,user:User) -> Embed:
        
        guildstts = await db.guildsetting.find({"setupbot": True}).to_list(None)
        
        
        servers = user.mutual_guilds
        
        servers.sort(key=favoriteguilds)
       

        for guild in servers:
            guildbs = list(filter(lambda i: i['guildid'] == guild.id, guildstts))
            if  len(guildbs) != 0:
                
                guildb = guildbs[0]

                if "startupid" in guildb:
                    channel = self.bot.get_channel(guildb['startupid'])
                    if channel:
                        
                            if guildb["public"]:
                                commendchannel = self.bot.get_channel(guildb["startupid"])
                                if commendchannel:
                                    
                                    channelname = commendchannel.mention
                                    break
                                else:
                                    await db.guildsetting.update_one({"guildid":guildb["guildid"]}, {"$set": {"setupbot": False}})
                                
                        
                    else:
                        await db.guildsetting.update_one({"guildid":guildb["guildid"]}, {"$set": {"setupbot": False}})
                else:
                    await db.guildsetting.update_one({"guildid":guildb["guildid"]}, {"$set": {"setupbot": False}})
                
                            
        embed = nextcord.Embed(title="Welcome to our community!", description=f"Join the commendbot support server so you don't lose your commendbot balance {config.BRAND_DISCORD_URL}", color=Colour.gold(), timestamp=timestamp,)
        
        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
        
        return [embed,get_rules()]
    
  
    async def logembed(self, embed: Embed, guild :Guild ,slot_id:int):
        
        logowner = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
        await logowner.send(embed=embed)
        if type(guild) == Guild:
            guildsett = await db.guildsetting.find_one({"guildid":guild.id})
            if guildsett["logonoff"] is True:
    
                channeloss = self.bot.get_channel(guildsett["logid"])
                if channeloss:
                    if channeloss.guild.id != logowner.guild.id:
                        await channeloss.send(embed=embed)
        substats = await db.slotsdb.find_one({"_id":slot_id})
        subchannel = self.bot.get_channel(substats["logchannelid"])
        if type(subchannel) == TextChannel:
            if  subchannel.guild.id != logowner.guild.id or channeloss and subchannel.guild.id != channeloss.guild.id and subchannel.guild.id != logowner.guild.id:
                await subchannel.send(embed=embed)
        return substats
    
    
    async def waitforrespon(self, channel : nextcord.TextChannel, user : nextcord.Member | nextcord.User ,check: str = "msg" ,timeout: float=180) -> typing.Tuple[typing.Union[None,TextChannel,User,Member,int,float],nextcord.Message]:
        """
            msg,user,member,int,float


        """
        try:
            msg : nextcord.Message = await self.bot.wait_for('message', check=lambda message: message.channel == channel and  message.author.id == user.id  , timeout=timeout)
            
        except Exception:
            
            
            embed=nextcord.Embed(title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
            embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                
            await channel.send(embed=embed)
            return None
        else:
            if check == "msg":
                return msg 
            elif check == "channel":
                if msg.channel_mentions:
                    channelg = msg.channel_mentions[0]
                    

                    return channelg , msg 

                else:
                    if is_number(msg.content):
                        channelg = self.bot.get_channel(int(msg.content))
                        if channelg:
                            return channelg , msg 
                        else:
                            return None, msg 


                    embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg 
            elif check == "user":
                if msg.mentions:
                    user = msg.mentions[0]
                    

                    return user , msg 

                else:
                    if is_number(msg.content):
                        userg = self.bot.get_user(int(msg.content))
                        if userg:
                            return userg, msg 
                        else:
                            return None, msg 


                    embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg 
            elif check == "member":
                if msg.mentions:
                    member = msg.mentions[0]
                    

                    return member ,msg

                else:
                    if is_number(msg.content):
                        member = channel.guild.get_member(int(msg.content))
                        if member:
                            return member, msg
                        else:
                            return None, msg 


                    embed=Embed(title="error | invalid channel!!", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg 
            elif check == "int":
                if msg.content.isnumeric():
                    number = int(msg.content)
                    return number, msg
                else:
                    embed=Embed(title="error | value isn't numeric(only integers)", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg
                
            elif check == "float":
                if is_number(msg.content):
                    number = float(msg.content)
                    return number, msg
                
                else:
                    embed=Embed(title="error | value isn't numeric", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                    await channel.send(embed=embed)
                    return None, msg 
                    
    
    
    
    
    async def buy_commends_header(self, sendas: TextChannel, customer: User):
        embed = nextcord.Embed(color=nextcord.Color.blurple())
        embed.set_author(name=server_name, url=logo, icon_url=logo)
        embed.set_thumbnail(url=logo)
        embed.add_field(name="Amount:", value="The amount of commends will be calculated based on the money you send. To calculate it, you can press the green button below.", inline=False)
        embed.add_field(name=f"Hey {customer.name}!", value=f"Please send the money using the **Friends & Family** option; otherwise, we will have to cancel your order without a refund. If you don't see this option, or if you have any questions, please do not send the **money** and contact <@{self.bot.owner_id}> in DMs for assistance.", inline=False)
        embed.add_field(name="Tutorial", value="[Watch Tutorial](https://youtube.com/watch?v=6M20RgpIgyI&feature=shares)", inline=False)
        embed.set_image(url=config.IMAGE_TUTORIAL_COMMEND)
        embed.add_field(name="Currency:", value="!Make sure you sent in **€** - **EUR** currency!", inline=False)
        embed.add_field(name="Paypal Mail:", value=config.PAYPAL_EMAIL, inline=False)
        embed.add_field(name="Paypal Link:", value="[Paypal Link](https://paypal.me/commendbotPR)", inline=False)
        embed.add_field(name="Paypal Note", value=f"Please set your secret **code** in the **PayPal note** (What’s this for?/Add note). Your **code** is  `{customer.id}`  .This is a crucial step to ensure proper processing of your order.", inline=False)
        
        await sendas.send(ephemeral=True, embed=embed, view=Check_cbprice(self.bot))
   

    
    async def addbal(self,amount:int,member:User,slot_id:int,gifter:User,interaction:Interaction = None,price:int=0,note:str=None):
        datetime_utc = get_datetime_utc()     
        usertest = await db.balancesdb.find_one({"userid":member.id,"slot_id":slot_id})
        
        if interaction:
            if interaction.guild:
                guild_id = interaction.guild.id
            else:
                guild_id = None
        else:
            guild_id =None
        if usertest is None:
            userdb = await db.usersdb.find_one({"userid":member.id})
            
            if not userdb :
                try:
                    embeds = await helpers.welcom_message(self,member)
                    await member.send(embeds=embeds)
                    print("after embed")
                except Exception:
                    usertest = user_template(member,False)
                    await db.usersdb.insert_one(usertest)
                else:
                    usertest = user_template(member,True)
                    await db.usersdb.insert_one(usertest)
            elif userdb.get("free",False):
                cprint("unban free","green")
                await db.usersdb.update_one({"userid":member.id}, {'$set': {'free': False}})
                
            oldamount = 0
            newamount = oldamount + amount
            
            
            await db.balancesdb.insert_one({"userid":member.id,"guildid":guild_id, "lastid":gifter.id, "amount":amount, "slot_id":slot_id,"today_used":0,"onhold":0,"active":True})
        else:
            await db.usersdb.update_one({"userid":member.id}, {'$set': {'free': False}})
            oldamount = int(usertest["amount"])
            await db.balancesdb.update_one({"userid":member.id,"slot_id":slot_id}, {"$inc": {"amount":amount}})
                
            newamount = oldamount + amount
        
        
        id = generate()
        
        embed=nextcord.Embed(title="Balance added!", description="Balance has been added to the user.", color=bluepr, timestamp=datetime.datetime.now())
        embed.add_field(name="TransactionID", value=id, inline=False)
        embed.add_field(name="Balance added to:", value=member.mention, inline=False)
        embed.add_field(name="Balance added by:", value=gifter.mention , inline=False)
        embed.add_field(name="Amount added:", value=f"{amount} commends", inline=False)
        embed.add_field(name="User's old balance:", value=f"{oldamount} commends", inline=False)
        embed.add_field(name="User's new balance:", value=f"{newamount} commends", inline=False)
        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
        embed.add_field(name="Price:", value=price, inline=False)
        if interaction:
            await interaction.send(embed=embed)
        
        
        sell = {
            "_id":ObjectId(id),
            "datetime":datetime_utc,
            "guildid":guild_id,
            "customerid":member.id,
            "sellerid":gifter.id,
            "slot_id":slot_id,
            "gifted-amount":amount,
            "u_old-amount":oldamount,
            "u_new-amount":newamount,
            "price":price,      
            "type":"add"
        }
        if note:
            sell["note"] = note
            embed.add_field(name="Note:", value=note, inline=False)
        else:
            embed.add_field(name="Note:", value="None", inline=False)
        await db.sellsds.insert_one(sell)
        slotdb = await db.slotsdb.find_one_and_update({"_id":slot_id}, {"$inc": {"price": price,"price-count":1}})
        
        if interaction and interaction.guild:
        
            print("its guildchannel")
            await helpers.logembed(self,embed,interaction.guild,slot_id) # idk if channel.guild ll not raise error there not in func
        else:
            await helpers.logembed(self,embed,None,slot_id) 
        try:
            await member.send(embed=embed)
        except Exception:
            pass
        
        if await can_dm_user(gifter):
            await gifter.send(embed=embed)
        
        
        
        
        logchannel = self.bot.get_channel(slotdb["logchannelid"])
        await logchannel.send(embed=embed)

    
    async def giftbal(self, reseller: bool, gifterdb, amount:int, interaction: Interaction | TextChannel ,gifter:Member | User,customer:Member | User ,guild:Guild,botlang =False):
        if  not gifterdb:
            raise BaseException("Missing parrameter gifterdb ")
            
        datetime_utc = get_datetime_utc()  
        userdb = await db.usersdb.find_one({"userid":gifter.id })
        if gifter.id != customer.id:
            if userdb:
                
                
                slot = await db.slotsdb.find_one({"_id":gifterdb["slot_id"]})
                if slot: 
                    if slot["enable"]:
                            if guild is None:
                                guild =  gifter
                            slot_id = gifterdb["slot_id"]
                            if not reseller:
                                if amount <=1:
                                    await interaction.send(embed=embed_error("Balance error", "You cant gift lower than 2 commends"), ephemeral=True)
                                    return
                                feesdb = await db.balancesdb.find_one({"userid":self.bot.user.id,"slot_id":slot_id})
                                fees = feescalc(amount)
                                feesbal = feesdb["amount"] + fees
                                print("reseller is none")
                            else:
                                fees = 0
                            oldamountg = gifterdb["amount"]    
                            newamountg = gifterdb["amount"] - (amount +fees)
                            
                
                            if (newamountg + fees) < 0:
                                if fees != 0: 
                                    fees2 = feescalc(gifterdb["amount"])
                                    usable =gifterdb['amount'] - fees2
                                    if not botlang:
                                        await interaction.send(embed=embed_error("You do not have enough commends to process this service!", f"you can max gift {usable} because {fees2} commends are fees!"), ephemeral=True)
                                    else:
                                        await interaction.send("balance")
                                else:
                                    if not botlang:
                                        await interaction.send(embed=embed_error("You do not have enough commends to process this service!","You do not have enough commends to process this gift."), ephemeral=True)
                                    else:
                                        await interaction.send("balance")  
                                
                            else:
                                if newamountg < 0:
                                    fees2 = feescalc(gifterdb["amount"])
                                    usable =gifterdb['amount'] - fees2
                                    if not botlang:
                                        await interaction.send(embed=embed_error("You do not have enough commends to process this service(fees)!", f"you can max gift {usable} because {fees2} commends are fees!"), ephemeral=True)
                                    else:
                                        await interaction.send("balance")
                                else:

                                    usertest = await db.balancesdb.find_one({"userid":customer.id,"slot_id":gifterdb["slot_id"]})
                                    
                                    
                                    if usertest is None:
                                        userdb = await db.usersdb.find_one({"userid":customer.id})
                                        
                                        if not userdb:
                                            result = await can_dm_user(customer)
                                            if result:
                                                try:
                                                    embeds = await helpers.welcom_message(self,customer)
                                                    await customer.dm_channel.send(embeds=embeds)
                                                except Exception:
                                                    userdb =user_template(customer,False)
                                                    await db.usersdb.insert_one(userdb)
                                                else:
                                                    userdb =user_template(customer,True)
                                                    await db.usersdb.insert_one(userdb)
                                            else:
                                                userdb = user_template(customer,False)
                                                await db.usersdb.insert_one(userdb)
                                        elif userdb.get("free",False):
                                            if reseller:
                                                await db.usersdb.update_one({"userid":customer.id}, {'$set': {'free': False}})
                                              
                                        
                                        await db.balancesdb.update_one({"userid":gifterdb["userid"],"slot_id":slot_id}, {"$inc": {"amount":-(amount +fees)}})
                                        await db.balancesdb.insert_one({"userid":customer.id, "lastid":gifterdb["userid"], "amount":amount, "slot_id":slot_id,"today_used":0,"onhold":0,"active":True})
                                        newamount = amount
                                        
                                        
                                        oldamount = 0
                                        
                                        
                                        
                                    else:
                                        if reseller:
                                            await db.usersdb.update_one({"userid":customer.id}, {'$set': {'free': False}})
                                        oldamount = int(usertest["amount"])
                                        
                                            
                                            
                                        newamount = oldamount + amount
                                        await db.balancesdb.update_one({"userid":gifterdb["userid"],"slot_id":slot_id}, {"$inc": {"amount":-(amount +fees)}})
                                        await db.balancesdb.update_one({"userid":customer.id,"slot_id":slot_id}, {"$set": {"amount":newamount}})
                                        
                                    await db.sellsds.insert_one({
                                            "datetime":datetime_utc, 
                                            "customerid":customer.id,
                                            "gifterid":gifterdb["userid"],
                                            "slot_id":gifterdb["slot_id"],
                                            "gifted-amount":amount,
                                            "g_old-amount":oldamountg,
                                            "g_new-amount":newamountg,
                                            "u_old-amount":oldamount,
                                            "u_new-amount":newamount,
                                            "fees":fees,
                                            "type":"gift"
                                        })
                                    embed=nextcord.Embed(title="Balance gifted!", description="Balance has been gifted to the user.", color=bluepr, timestamp=datetime.datetime.now())
                                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                                    embed.add_field(name="Balance gifted by:", value=gifter.mention , inline=False)
                                    embed.add_field(name="Balance gifted to:", value=customer.mention, inline=False)
                                    
                                    embed.add_field(name="Amount gifted:", value=f"{amount} commends", inline=False)
                                    embed.add_field(name="Fees for transaction", value=f"{fees} commends", inline=False)
                                    embed.add_field(name="User's old balance:", value=f"{oldamount} commends", inline=False)
                                    embed.add_field(name="User's current balance:", value=f"{newamount} commends", inline=False)
                                    
                                    if not botlang:
                                        
                                        await interaction.send(embed=embed)
                                    else:
                                        await interaction.send("gifted")
                                        
                                    if not reseller:
                                        
                                        
                                        if "giftaccs" in userdb:
                                            if customer.id not in userdb["giftaccs"]:
                                                await db.usersdb.update_one({"userid":gifter.id}, {"$push":{"giftaccs":customer.id}})
                                            
                                        else:
                                            await db.usersdb.update_one({"userid":gifter.id}, {"$set":{"giftaccs":[customer.id]}})  
                                    
                                        
                                    result = await can_dm_user(customer)
                                    if result:
                                        try:
                                            await customer.dm_channel.send(embed=embed)
                                            
                                        except Exception:
                                            if type(interaction) == Interaction:
                                                if type(customer) == Member and customer in interaction.guild.members and interaction.channel.permissions_for(customer).view_channel and interaction.channel.permissions_for(customer).read_message_history  and interaction.channel.permissions_for(customer).read_messages:
                                            
                                                
                                                    await interaction.channel.send(f"{customer.mention} please unlock me in dms or bot cant work correctly!")
                                            else:
                                                interaction :TextChannel  =interaction 
                                                if type(customer) == Member and customer in interaction.guild.members and interaction.permissions_for(customer).view_channel and interaction.permissions_for(customer).read_message_history  and interaction.permissions_for(customer).read_messages:
                                            
                                                    
                                                    await interaction.send(f"{customer.mention} please unlock me in dms or bot cant work correctly!")
                                                else:
                                                    await interaction.send(f"{customer.mention} have locked dms!")
                                    else:           
                                        await interaction.send(f"{customer.mention} have locked dms!")
                                    
                                        
                                    embed.add_field(name="Gifter's old balance:", value=f"{oldamountg} commends", inline=False)
                                    embed.add_field(name="Gifter's current balance:", value=f"{newamountg} commends", inline=False)
                                    
                                    if await can_dm_user(gifter):
                                        await gifter.dm_channel.send(embed=embed)
                                    if gifter.id in config.TRACKED_GIFTER_IDS:
                                        gift_channel = self.bot.get_channel(config.GIFT_CHANNEL_ID)
                                        if gift_channel:
                                            await gift_channel.send(f"{customer.id} got {amount} from {gifter}")
                                    
                                    await helpers.logembed(self,embed , guild,slot_id)
                                    if not reseller:
                                        await db.balancesdb.update_one({"userid":self.bot.user.id,"slot_id":slot_id}, {"$set": {"amount":feesbal}})
                                        print(f"feesbal {feesbal}")
                    else:
                        embed = nextcord.Embed(title="Error", description="This slot is currenty disabled!", color=Colour.red(), timestamp=timestamp,)
                        await interaction.send(embed=embed)
                else:
                    embed = nextcord.Embed(title="Error", description=f"I cant find specific slot with id {gifterdb['slot_id']}", color=Colour.red(), timestamp=timestamp,)
                    await interaction.send(embed=embed)
            else:
                await interaction.send("Error you dont have any balance!")
        else:
            await interaction.send("You cant gift balance to yourself!")    
    
    
    
    
    
    
    
    
    
    

       
    




        




def setup(bot: Bot) -> None:
    bot.add_cog(helpers(bot))