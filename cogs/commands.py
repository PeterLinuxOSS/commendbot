"""Customer-facing slash commands.

The cog is assembled from mixins so no single file has to hold all ~60
commands. nextcord's CogMeta walks the MRO, so a command defined on a mixin
registers exactly as if it were written here.
"""

import datetime
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
import asyncstdlib as a
import cooldowns
import nextcord
from disposable_email_domains import blocklist
from key_generator.key_generator import generate as generate_id
from nextcord import ChannelType, Color, Colour, Embed, Interaction, Member, SlashOption, User
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from numpy.random import choice
from pymongo import ReturnDocument

import config
from cogs.commands_admin import AdminCommands
from cogs.commands_balance import BalanceCommands
from cogs.commands_profile import ProfileCommands
from cogs.commands_subscriptions import SubscriptionsCommands
from cogs.commands_views import (
    Confirm_req,
    Spin_wheel,
    wheel_spin_select,
)
from cogs.commend import commend, language
from cogs.commend_menu import closebutton, commend_menu, promo_view
from cogs.helpers import address_button, helpers, re_address_button
from utils import (
    TESTING_GUILD_ID,
    admins,
    can_dm_user,
    convert_lang,
    db,
    embed_error,
    find_command,
    find_wallets,
    get_lang,
    get_rules,
    html_recovery,
    logger,
    mail_regex,
    promotion_embed,
    smtp,
    sview,
    timestamp,
    tz,
    user_template,
)

script_top = datetime.datetime.now(tz=tz)






















class bot_commands(
    ProfileCommands,
    BalanceCommands,
    SubscriptionsCommands,
    AdminCommands,
    commands.Cog,
):

    def __init__(self, bot: Bot):
        self.bot = bot
        self.on_init = datetime.datetime.now(tz=tz)

    @commands.Cog.listener()
    async def on_ready(self):

        lang = convert_lang("eng")
        self.bot.add_view(sview(self.bot, language, None, None, lang))

        self.bot.add_view(promo_view())
        self.bot.add_view(address_button(self.bot))
        view = closebutton(self.bot)

        self.bot.add_view(view)

        refreshdb = db.refresh.find({})

        async for refresh in refreshdb:
            try:
                channel = self.bot.get_channel(refresh["channelid"])
            except Exception:
                await db.refresh.delete_one({"channelid": refresh["channelid"]})
            else:
                try:
                    msg = await channel.fetch_message(refresh["msgid"])
                except Exception:
                    await db.refresh.delete_one({"channelid": refresh["channelid"], "msgid": refresh["msgid"]})
                if "values" in refresh:

                    view = eval(refresh["view"])
                    values: list = refresh["values"]
                    await msg.edit(view=view(self.bot, *values))

    @commands.command(name="ping")
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def ping_command(self, ctx: commands.Context):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @nextcord.slash_command(name="promo")
    @cooldowns.cooldown(2, 30, bucket=cooldowns.SlashBucket.author)
    @cooldowns.cooldown(1, 10, bucket=cooldowns.SlashBucket.channel)
    async def promo_command(self, interaction: Interaction,):
        await interaction.send(embed=promotion_embed(), view=promo_view())

    @nextcord.slash_command(name="calldev", description="Call developer")
    async def calldev_command(self, interaction: Interaction,):
        embed = nextcord.Embed(description="**Hey, be careful!** The following actions will be taken back: \n> Using calldev command you are sure you read all of commendbot rules(`/rules`)\n> Abusing calldev command is being punished\n> Only problems about commendbot.", color=Colour.brand_red(), timestamp=timestamp,)
        embed.set_author(
            name="Warning", icon_url=config.IMAGE_WARNING_ICON)
        view = Confirm_req(interaction.user)
        await interaction.send(embed=embed, view=view)
        if await db.usersdb.find_one({"userid": interaction.user.id}):

            await view.wait()
            if view.value is None:
                pass
            elif view.value:
                try:
                    owner = interaction.guild.get_member(self.bot.owner_id)
                    await interaction.send(f"Hey, {owner.mention} there is a any problem")

                    await interaction.channel.set_permissions(owner, send_messages=True, read_messages=True, read_message_history=True, manage_messages=True, embed_links=True, attach_files=True, mention_everyone=True, use_external_emojis=True, add_reactions=True, connect=True, speak=True, mute_members=True, deafen_members=True, move_members=True, priority_speaker=True, send_messages_in_threads=True, use_slash_commands=True)
                    await owner.send(f"{owner.mention} - in channel {interaction.channel.mention} in guild {interaction.guild}")
                except Exception:
                    owner = self.bot.get_user(self.bot.owner_id)
                    await interaction.send(f"Bot dev is not on ur server! dm: {owner.mention} - {owner}")
        else:
            await interaction.send("You are not commendbot customer!!")













    @nextcord.slash_command(
        name="daily",
        description="daily wheel spin",
        dm_permission=False


    )
    @cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
    async def daily_command(self, interaction: Interaction):
        await interaction.response.defer()
        userdb = await db.usersdb.find_one({"userid": interaction.user.id})
        if userdb:
            if "daily" in userdb and userdb["daily"] <= 3:
                required = 50
                description = "Please select a slot you would like gift balance from:\n\n"
                selectOption, description, wallet_n = await find_wallets(interaction.user, required, description)
                if wallet_n == 1 and len(selectOption) == 1:

                    await bot_commands.wheel_spin(self, interaction, int(selectOption[0].value))
                elif wallet_n == 0:

                    await interaction.send(embed=embed_error("Error", "You dont have any balance in commendbot!"))
                else:
                    if wallet_n != 0 and len(selectOption) != 0:
                        embed = nextcord.Embed(
                            title="Select Wallet", description=description, color=nextcord.Color.orange())
                        await interaction.send(embed=embed, view=sview(self.bot, wheel_spin_select, interaction.user, 120, selectOption))
                    else:
                        embed = nextcord.Embed(
                            title="Select Wallet", description=description, color=nextcord.Color.orange())
                        await interaction.send(embed=embed)
            else:
                embed = nextcord.Embed(
                    title="Alert", description="You cant use for today more wheel spins please wait till 00:00 UTC to try again.", color=nextcord.Color.orange())
                await interaction.send(embed=embed)
        else:
            await interaction.send(embed=embed_error("Error", "You dont have any balance in commendbot!"))

    async def wheel_spin(self, interaction: Interaction, slot_id: int,):

        customer = interaction.user
        userdb = await db.usersdb.find_one_and_update({"userid": customer.id}, {'$inc': {"daily": +1}}, return_document=ReturnDocument.AFTER)
        if userdb["daily"] <= 3:
            payment = 50
            rewards = [25, 45, 50, 70, 100, 250, 500, 1000]

            baldb = await db.balancesdb.find_one_and_update({"userid": customer.id, "slot_id": slot_id}, {'$inc': {'amount': -payment, "onhold": +payment}}, return_document=ReturnDocument.AFTER)
            embed = nextcord.Embed(
                title="Wheel Spin", description="", color=Colour.purple(), timestamp=timestamp,)
            embed.add_field(name="Cost:", value="50 commends", inline=False)
            prizes = ""
            for id, reward in enumerate(reversed(rewards), 1):
                prizes += f"{config.EMOJI_QUEUED}・{reward} commends\n"

            embed.add_field(name="Prizes:", value=prizes, inline=False)
            embed.set_footer(text=f"{userdb['daily']}/3 spins")
            view = Spin_wheel()
            await interaction.send(embed=embed, view=view)
            await view.wait()
            if view.value is None:
                await db.balancesdb.update_one({"userid": customer.id, "slot_id": slot_id}, {'$inc': {'amount': +payment, "onhold": -payment, }})
                await db.usersdb.update_one({"userid": customer.id}, {'$inc': {"daily": -1}})
                embed3 = nextcord.Embed(
                    title="Wheel Spin - TimeOut", description="", color=Colour.red(), timestamp=timestamp,)
                prizes = ""
                embed3.add_field(
                    name="Cost:", value="50 commends", inline=False)
                for id, reward in enumerate(reversed(rewards), 1):

                    prizes += f"{config.EMOJI_NOT_COMMENDING}・{reward} commends\n"
                embed3.add_field(name="Prizes:", value=prizes, inline=False)
                embed3.set_footer(text=f"{userdb['daily']-1}/3 spins")

                await interaction.edit_original_message(view=None, embed=embed3)

            else:

                if "drop" in userdb:
                    drops = userdb["drop"]
                    waste = payment * drops
                    won = userdb["won"] - waste
                else:
                    drops = 0
                    waste = 0
                    won = 0
                print(f"user {interaction.user} - {won}")
                if won > 0:
                    probabilities = [0.55, 0.25, 0.20,
                                     0.00, 0.00, 0.00, 0.0, 0.0]
                else:
                    if won > -100:
                        probabilities = [0.56, 0.25, 0.18,
                                         0.01, 0.00, 0.000, 0.0, 0.0]
                    elif won > -240:
                        probabilities = [0.30, 0.28, 0.20,
                                         0.11, 0.10, 0.01, 0.0, 0.0]
                    elif won > -450:
                        probabilities = [0.30, 0.25, 0.20,
                                         0.12, 0.07, 0.05, 0.01, 0.0]
                    elif won > -950:
                        probabilities = [0.25, 0.21, 0.19,
                                         0.17, 0.10, 0.05, 0.02, 0.01]
                    elif won > -1200:
                        probabilities = [0.17, 0.18, 0.2,
                                         0.21, 0.1, 0.09, 0.03, 0.02]
                    else:
                        probabilities = [0.17, 0.18, 0.2,
                                         0.21, 0.1, 0.06, 0.03, 0.05]

                result = int(choice(rewards, p=probabilities))
                await db.usersdb.update_one({"userid": customer.id}, {'$inc': {"won": +result, "drop": +1}})
                prizes = ""
                embed2 = nextcord.Embed(
                    title="Wheel Spin", description="", color=Colour.purple(), timestamp=timestamp,)
                embed2.add_field(
                    name="Cost:", value="50 commends", inline=False)
                for id, reward in enumerate(reversed(rewards), 1):
                    if result == reward:
                        prizes += f"{config.EMOJI_COMMENDING}・{reward} commends\n"
                    else:
                        prizes += f"{config.EMOJI_NOT_COMMENDING}・{reward} commends\n"
                embed2.add_field(name="Prizes:", value=prizes, inline=False)
                embed2.set_footer(text=f"{userdb['daily']}/3 spins")
                await interaction.edit_original_message(embed=embed2)

                baldb = await db.balancesdb.find_one_and_update({"userid": customer.id, "slot_id": slot_id}, {'$inc': {"onhold": -payment}}, return_document=ReturnDocument.AFTER)
                await db.balancesdb.update_one({"userid": self.bot.user.id, "slot_id": slot_id}, {'$inc': {"amount": +payment}})
                await db.sellsds.insert_one({

                    "datetime": datetime.datetime.now(tz=tz),

                    "customerid": customer.id,
                    "slot_id": slot_id,
                    "remove-amount": payment,
                    "u_old-amount": (baldb["amount"]+payment),
                    "u_new-amount": baldb["amount"],
                    "type": "remove"

                })

                gifterdb = await db.balancesdb.find_one({"userid": self.bot.user.id, "slot_id": slot_id})

                owner = self.bot.get_user(self.bot.user.id)
                await helpers.giftbal(self, True, gifterdb, result, interaction.channel, owner, customer, interaction.guild, False)
        else:
            userdb = await db.usersdb.find_one_and_update({"userid": customer.id}, {'$inc': {"daily": -1}}, return_document=ReturnDocument.AFTER)
            embed = nextcord.Embed(
                title="Alert", description="You cant use for today more wheel spins please wait till 00:00 UTC to try again.", color=nextcord.Color.orange())
            await interaction.send(embed=embed)


    @nextcord.slash_command(
        name="check_iq",



    )
    async def check_iq_command(self, interaction: Interaction):
        if interaction.user.id in admins:
            result = await db.slotsdb.find_one({"_id": 3})
            await interaction.send(f"Price: {result.get('price')} \nCount:{result.get('price-count')}")
        else:
            await interaction.send("HaHaHa 0, No Admin perms...")
            
            
    @nextcord.slash_command(
        name="refresh",guild_ids=TESTING_GUILD_ID
        



    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def refresh_command(self,
                               interaction: Interaction, 

                               ):
        if interaction.user.id == self.bot.owner_id or interaction.user.id in admins:
            channel = interaction.channel
            ticketdb = await db.ticketsdb.find_one({"channelid": channel.id})
            msg = await channel.fetch_message(ticketdb.get("msgid"))
            if msg:
                error_thread = self.bot.get_channel(
                    ticketdb["error_channelid"])
                userdb = await db.usersdb.find_one({"userid": ticketdb["userid"]})

                lang = await get_lang(userdb, channel.guild)
                embed, view = await commend_menu.show(self, self.bot.get_user(ticketdb["userid"]), lang, error_thread)

                await msg.edit(embed=embed, view=view)
            else:
                logger.error(f"also msgid is none {ticketdb}", "red")


    @nextcord.slash_command(
        name="commands",


    )
    @cooldowns.cooldown(1, 60, bucket=cooldowns.SlashBucket.author)
    async def commands_command(self,
                               interaction: Interaction,
                               ):
        print(interaction.user)
        user = interaction.user
        userdb = await db.usersdb.find_one({"userid": interaction.user.id})
        await get_lang(userdb, interaction.guild)
        commands_list = ""
        command_ignore = {"adminbalance":"admin","debug_check":"admin","showactualslots":"admin","showallslots":"admin","stop-commend":"admin","transfer":"admin","add_blacklist":"admin","generate":"resell","setup":"server_admin","verify_now":"customer","balance":"customer","daily":"customer","removebalance":"admin","userinfo":"admin","profile":"customer","addbalance":"customer","giftbalance":"customer","report":"customer","change-language":"admin","mysubscriptions":"customer","deletechannel":"customer","commands":None,"calldev":"customer","unban":"admin","check_iq":"admin","addpanel":"admin","rewards":"customer","addsub":"admin","eval":"owner","change-logchannel":"admin","promo":"customer","transferbalance":"admin","active_resell":"admin","show":"customer","setslotcurrency":"admin","syncbalance":"admin","deleteall":"owner","subcheck":"admin","verify":None}
        if user.id == self.bot.owner_id:
            premisson = "owner"
        elif user.id in admins:
            
        
            premisson = "admin"  # Change this to the desired permission level
        elif isinstance(user,Member) and user.guild_permissions.administrator:
            premisson = "server_admin"
            
        elif await db.subdb.find_one({"ownerid":user.id,"pay":True,"disabled":False}):
            premisson = "resell"
        elif await db.usersdb.find_one({"userid":user.id}):
            premisson = "customer"
        else:
            premisson = "user"
            
        
        
        # Get all global commands from the bot
        global_commands = self.bot._get_global_commands()
        
        # Filter commands based on permission and visibility
        filtered_commands = [
            command
            for command in global_commands
            if list(command.command_ids.keys()) == [None]
            
            and (command.type == nextcord.ApplicationCommandType.chat_input)
            and (command.name not in command_ignore or (
                (premisson == "user" and command_ignore[command.name] not in ["admin", "owner" ,"customer", "resell","server_admin",None]) or
                (premisson == "resell" and command_ignore[command.name] in ["user","customer", "resell"]) or
                (premisson == "server_admin" and command_ignore[command.name] in ["user","customer", "resell","server_admin"]) or
                (premisson == "customer" and command_ignore[command.name] in ["user", "customer"]) or
                (premisson == "admin" and command_ignore[command.name] in ["admin", "customer","user"]) or
                (premisson == "owner")
            ))
        ]



        filtered_commands.sort(key=lambda cmd: cmd.name)
        
        for command in filtered_commands:
            
            
            commands_list += f"</{command.name}:{command.command_ids[None]}> ・ {command.description}\n"

        # Create and send the embed
        embed = nextcord.Embed(
            title="List of Commands",
            description=commands_list,
            color=Colour.blurple(),
            timestamp=datetime.datetime.now(),
        )
        # Replace 'interaction.send' with the actual function to send messages
        await interaction.send(embed=embed)

    @nextcord.slash_command(
        name="help",
        description="Help command"

    )
    @cooldowns.cooldown(1, 60, bucket=cooldowns.SlashBucket.author)
    async def help_command(self,
                           interaction: Interaction,
                           ):
        userdb = await db.usersdb.find_one({"userid": interaction.user.id})
        lang = await get_lang(userdb, interaction.guild)
        embed, view = await commend.embed_helpmenu(self, lang, interaction.user)
        await interaction.send(embed=embed, view=view)

    @nextcord.slash_command(
        name="verify",
        description="verify your mail adress",


    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def verify_command(self, interaction: Interaction, code: str = SlashOption(name="code", required=True)):
        data = await db.usersdb.find_one({"userid": interaction.user.id, "verify": {"$exists": True}})
        if data:
            if isinstance(data["verify"], str):
                if data["verify"] == code.strip():
                    await db.usersdb.update_one({"_id": data["_id"]}, {'$set': {'verify': True, "alert_verify": True}})
                    await interaction.send("✅You have been verified!✅",)

                else:
                    await interaction.send("❌Code is invalid, Try again or resend new mail.❌", view=sview(self.bot, re_address_button, interaction.user, None,))
            else:
                await interaction.send("👍You are verified!👍")
        elif data := await db.usersdb.find_one({"transfer": code.strip()}):
            await interaction.send("✅ Your account was transferred successfully. ✅")
            db.usersdb.update_one(
                {'_id': data["_id"]},
                {
                    '$set': {'userid': interaction.user.id, "olduserid": data["userid"]},
                    '$unset': {"transfer": ""}
                }
            )
            db.balancesdb.update_many({'userid': data["userid"]}, {
                                      '$set': {'userid': interaction.user.id}})
            db.sellsds.update_many({'customerid': data["userid"]}, {
                                   '$set': {'customerid': interaction.user.id}})
            db.sellsds.update_many({'gifterid': data["userid"]}, {
                                   '$set': {'gifterid': interaction.user.id}})
        else:
            await interaction.send("❌Code is invalid or you are not allowed to use this command❌")

    @nextcord.slash_command(
        name="verify_now",


    )
    @cooldowns.cooldown(1, 500, bucket=cooldowns.SlashBucket.author)
    async def verify_now_command(self, interaction: Interaction):
        if database := await db.usersdb.find_one({'userid': interaction.user.id}):
            if database.get("verify") is None:

                await db.usersdb.update_one({'userid': interaction.user.id}, {'$set': {'alert_verify': True}})
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
                if await can_dm_user(interaction.user):
                    await interaction.send("Check your dms", ephemeral=True)
                    await interaction.user.send(embed=embed, view=address_button(self.bot))
                else:
                    await interaction.send(embed=embed, view=address_button(self.bot))
            else:
                await interaction.send("👍You are verified!👍")
        else:
            await interaction.send("Your are not cb-customer")










    
        






    @nextcord.slash_command(
        name="change-language",
        description="Change your default language ",

    )
    async def change_language_command(self,
                                      interaction: Interaction,
                                      value: str = SlashOption(name="languages", description="select ur language", choices={
                                                               "English": "eng", "Slovak/Czech": "sk", "German": "ger", }, required=True),
                                      ):

        userdb = await db.usersdb.find_one({"userid": interaction.user.id})
        if userdb is None:
            await db.usersdb.insert_one(user_template(interaction.user, True, language=value))

            await interaction.send("Your language has been updated")

        else:
            await db.usersdb.update_one({"userid": interaction.user.id}, {"$set": {"language": value}})
            await interaction.send("Your language has been updated")

    @nextcord.slash_command(name="credits", description="Bot credits",)
    async def credits_command(self, interaction: Interaction):
        embed = Embed(title="© Bot Credits", color=nextcord.Color.gold())

        for role, credit in config.CREDITS:
            embed.add_field(name=f"{role}:", value=credit, inline=False)
        embed.add_field(
            name="Owner:", value=f"<@{self.bot.owner_id}>", inline=False)
        embed.add_field(
            name="Translation:",
            value="\n".join(
                f"**{language}** — {credit}"
                for language, credit in config.TRANSLATION_CREDITS
            ),
            inline=False,
        )
        await interaction.send(embed=embed)

    @nextcord.slash_command(name="stop-commend", description="stop commendinf for ")
    async def stop_commend(self,
                           interaction: Interaction,
                           user: User = SlashOption(
                               name="user",  required=True),

                           ):
        datetime_utc = datetime.datetime.now(tz=tz)
        if interaction.user.id == self.bot.owner_id or interaction.user.id == admins:
            await interaction.send("Processing!")
            sessions = db.serverusers.find({"userid": user.id})
            id = 0
            async for id, ses in a.enumerate(sessions, 1):

                dictlist = {"userid": user.id, "slot_id": ses["slot_id"], "steamID64": ses[
                    "steamID64"], "status": "wait", "datetime": datetime_utc, "type": "stop"}
                await db.waitinglist.insert_one(dictlist)
            await interaction.edit(content=f"We stop {id} sessions")


    @nextcord.slash_command(name="recovery", description="Recovery your banned or lost account in commendbot via linked mail")
    async def recovery_command(self, interaction: Interaction,

                               mail: str = SlashOption(
                                   name="mail", description="Linked_Mail", required=True),

                               ):
        mail = mail.strip()
        check = await db.usersdb.find_one({"userid": interaction.user.id})
        if check is None:

            if (re.fullmatch(mail_regex, mail)):

                if mail.partition('@')[2] not in blocklist and mail.partition('@')[2] not in {"test.com", "test.try"}:
                    userdb = await db.usersdb.find_one({"mail": mail.strip()})
                    if userdb:
                        await interaction.send("Please Wait")
                        if userdb.get("verify"):
                            verification_code = generate_id(
                                2, "-", 4, 4, capital="all").get_key()
                            html = html_recovery(verification_code)

                            # Create a multipart message container
                            message = MIMEMultipart()
                            message['From'] = config.MAIL_FROM_NOREPLY
                            message['To'] = mail
                            message['Subject'] = 'Account Recovery'

                            # Attach the HTML content to the email
                            message.attach(MIMEText(html, 'html'))
                            try:
                                await smtp.sendmail(config.MAIL_NOREPLY, mail, message.as_string())
                            except aiosmtplib.SMTPServerDisconnected:
                                await smtp.connect()
                                await smtp.sendmail(config.MAIL_NOREPLY, mail, message.as_string())

                            await db.usersdb.update_one({'userid': userdb["userid"]}, {'$set': {'mail': mail, "transfer": verification_code}})
                            await interaction.edit_original_message(content="Please check your email inbox.")
                        else:
                            await interaction.send(f"This mail is verified! please contact support {find_command(self.bot,'report')}")
                    else:
                        await interaction.send("This mail is not linked to any address!!")
                else:
                    await interaction.send("Please enter your permanent email address!!")

            else:
                await interaction.send("Your email address is Invalid!")
        else:
            await interaction.send(f"Your account already exists in CommandBot. You need to link your account to create a clean new account, or contact support. via {find_command(self.bot,'report')}")

            



    @nextcord.slash_command(name="deletechannel", description="delete private channel",)
    async def deletechannel_command(self, interaction: Interaction,):
        await interaction.response.defer()

        await commend_menu.close_ticket(self, interaction.channel, interaction)

    @nextcord.slash_command(name="rules", description="show bot rules",)
    async def rules(self, interaction: Interaction,):

        await interaction.send(embed=get_rules())

    @nextcord.slash_command(name="report", description="report a problem or user",)
    async def report_command(self, interaction: Interaction,
                             reason: str = SlashOption(
                                 name="reason_problem", description="please type there your problem or reason to report", required=True),
                             report_u: nextcord.User = SlashOption(
                                 name="reported_user", description="user", required=False),
                             r_channel:  nextcord.abc.GuildChannel = SlashOption(
                                 name="reported_channel", description="channel", required=False, channel_types=[ChannelType.text])
                             ):
        embed = nextcord.Embed(description="**Hey, be careful!** The following actions will be taken back: \n> Using report command you are sure you read all of commendbot rules(`/rules`)\n> Abusing report command is being punished\n> Only reports about commendbot.", color=Colour.brand_red(), timestamp=timestamp,)
        embed.set_author(
            name="Warning", icon_url=config.IMAGE_WARNING_ICON)
        view = Confirm_req(interaction.user)
        await interaction.send(embed=embed, view=view)

        await view.wait()
        if view.value is None:
            pass
        elif view.value:

            rchannel = self.bot.get_channel(config.REFUND_CHANNEL_ID)
            embed = nextcord.Embed(
                title="Report", color=Colour.dark_red(), timestamp=timestamp,)
            embed.add_field(
                name="Reported by", value=f"{interaction.user.mention} - `{interaction.user.id}` - {interaction.user}", inline=False)
            embed.add_field(
                name="Reported User", value=f"{report_u.mention} - `{report_u.id}` - {report_u}", inline=False) if report_u else ...
            embed.add_field(name="Repotred Chnanel",
                            value=f"{r_channel.mention} - `{r_channel.id}` - {r_channel}", inline=False) if r_channel else ...
            embed.add_field(name="Reason", value=f"{reason}", inline=False)
            await rchannel.send(embed=embed)
            if await can_dm_user(interaction.user):
                await interaction.user.send("We sent your report to admins of commendbot they working in working days at 10 - 20 UTC, in 48hr u ll get respond by any of admin.",)
            else:
                await interaction.channel.send(f"{interaction.user.mention}We sent your report to admins of commendbot they working in working days at 10 - 20 UTC, in 48hr u ll get respond by any of admin.",)





        


    @nextcord.slash_command(
        name="show",
        description="slow login details for panel",

    )
    async def show_command(self,
                           interaction: Interaction):
        userdb = await db.usersdb.find_one({"userid": interaction.user.id})
        if userdb:
            embed = nextcord.Embed(
                title="Panel details", description=f"Login: {userdb['login']}\nPassword: {userdb['password']}", color=Color.blurple(), timestamp=timestamp,)
            await interaction.send(embed=embed, ephemeral=True)
        else:
            await interaction.send("You are not customer of comendbot!", ephemeral=True)

    @nextcord.slash_command(
        name="buy",
        description="Easily&Fast order commends and pay via PayPal EU NOW",

    )
    @cooldowns.cooldown(20, 1800, bucket=cooldowns.SlashBucket.author,cooldown_id="spamcheck")
    async def buy(self,
        interaction: Interaction,
        ):
        await helpers.buy_commends_header(self,interaction,interaction.user)
        
        
        
        
        




def setup(bot: Bot) -> None:
    bot.add_cog(bot_commands(bot))
