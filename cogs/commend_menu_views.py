"""Interactive views and selects used by the commend_menu cog."""

import datetime

import nextcord
from nextcord import Colour, Interaction
from nextcord.ext.commands import Bot
from steam_web_api import Steam

import config
from cogs.commend import *
from cogs.helpers import helpers
from cogs.keygen import keygen
from utils import *

steam = Steam(config.STEAM_API_KEY)


class commendbotbutton(nextcord.ui.View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @nextcord.ui.button(label='Create private channel!', emoji="✔️", style=nextcord.ButtonStyle.blurple, custom_id="commendbot")
    async def commendbot(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        guild = interaction.guild
        member = interaction.user
        is_error = True

        file = await db.ticketsdb.insert_one({"username": member.name, "userid": member.id, "guildid": guild.id,  "status": True})
        _id = file.inserted_id
        serversub: dict = await db.subdb.find_one({"guildid": interaction.guild_id})
        if serversub and not serversub.get("disabled", True) and serversub.get("pay", False):
            blacklist = await db.blacklistdb.find_one({"userid": interaction.user.id})

            userdb = await db.usersdb.find_one({"userid": interaction.user.id})
            if userdb:

                lang = await get_lang(userdb, interaction.guild)
                if lang:
                    if blacklist is None:

                        tickets = await db.ticketsdb.find_one({"userid": interaction.user.id, "_id": {"$ne": _id}})

                        if tickets is None:

                            if await can_dm_user(interaction.user):

                                try:
                                    msg = lang["commendbotbutton-msg"]
                                    await interaction.send(msg, ephemeral=True)

                                except nextcord.errors.NotFound:

                                    return

                                except Exception as ex:

                                    await interaction.send(f"{interaction.user.mention} Please contact <@{config.OWNER_ID}> - Error 1188\n\n{ex}")
                                else:

                                    other = nextcord.utils.get(
                                        guild.categories, name="CommendBot")
                                    if not other:

                                        await interaction.send("Not found category named CommendBot! Please contact server administrator.")
                                    else:

                                        others = other
                                        overwrites = {guild.default_role: nextcord.PermissionOverwrite(
                                            read_messages=False)}
                                        retries = 1
                                        category_name = "CommendBot"
                                        other = nextcord.utils.get(
                                            guild.categories, name=category_name)

                                        while retries < 5 and (other is None or len(other.text_channels) >= 50):
                                            retries += 1
                                            if len(other.text_channels) >= 50:
                                                category_name = f"{category_name}{'' if retries == 0 else retries}"
                                            else:

                                                category_name = f"{category_name}{'' if (retries-1) == 0 else retries-1}"
                                            logger.debug(
                                                f"Category name: {category_name}")
                                            other = nextcord.utils.get(
                                                guild.categories, name=category_name)

                                            if other is None:
                                                other = await guild.create_category(name=category_name, overwrites=others.overwrites)

                                        if other and len(other.text_channels) < 50:

                                            try:
                                                channel = await guild.create_text_channel(name=f'📂・c-{member.name}', category=other, overwrites=overwrites)
                                            except Exception as ex:

                                                await interaction.edit_original_message(content=f'Error(please contact admin/bot dev): {ex}')
                                            else:

                                                
                                                
                                                
                                                
                                                message = await channel.send(f'{member.mention}')
                                                error_channel = await message.create_thread(name="logs")
                                                

                                                cprint(
                                                    f"Created channel user: - {member} - {member.id} . channel: {channel} - {channel.id} guild: {guild} - {guild.id}", "cyan")

                                                try:
                                                    await channel.edit(sync_permissions=True)
                                                except Exception as ex:

                                                    await interaction.edit_original_message(content=f'Error2(please contact admin/bot dev): {ex}')
                                                await channel.set_permissions(member, send_messages=False, view_channel=True, read_messages=True, use_slash_commands=True, embed_links=True, attach_files=True, read_message_history=True,)
                                                msg = await interaction.edit_original_message(content=f'{member.mention} {lang["commendbotbutton-msg-edit"]} {channel.mention}')

                                                embed, view = await self.bot.get_cog("commend_menu").show(interaction.user, lang, error_channel)
                                                await message.edit(f'{member.mention}{lang["commendbotbutton-ping"]}', embed=embed, view=view)

                                                await db.ticketsdb.update_one({"_id": _id}, {"$set": {"guildid": guild.id, "channelid": channel.id, "date": datetime.datetime.now(tz), "msgid": message.id, "error_channelid": error_channel.id}})
                                                is_error = False

                                                guildsett = await db.guildsetting.find_one({"guildid": interaction.guild_id})
                                                embed = nextcord.Embed(title="Created new private channel", description="", color=Colour.dark_magenta(
                                                ), timestamp=datetime.datetime.now(),)
                                                embed.add_field(
                                                    name="User:", value=f"{interaction.user} -`{interaction.user.id}`", inline=False)
                                                embed.add_field(
                                                    name="Channel:", value=f"{channel.mention} - `{channel.id}`", inline=False)
                                                if guildsett["logonoff"] is True:

                                                    logchannelb = self.bot.get_channel(
                                                        guildsett["logid"])
                                                    if logchannelb:

                                                        await logchannelb.send(embed=embed)
                                                    else:
                                                        await db.guildsetting.update_one({'_id': guildsett["_id"]}, {'$set': {'logonoff': False}})
                                                if not guild.id == config.SUPPORT_GUILD_ID:
                                                    logchannel = self.bot.get_channel(
                                                        config.OWNER_LOG_CHANNEL_ID)
                                                    await logchannel.send(embed=embed)
                                                role = nextcord.utils.get(
                                                    guild.roles, name="CommendBot-Support-Role")
                                                if role is not None:

                                                    await channel.set_permissions(role, send_messages=True, read_messages=True, manage_messages=True, embed_links=True, attach_files=True, mention_everyone=True, use_external_emojis=True, add_reactions=True, connect=True, speak=True, mute_members=True, deafen_members=True, move_members=True, priority_speaker=True, send_messages_in_threads=True, use_slash_commands=True, read_message_history=True)

                                                if not userdb["rules"]:
                                                    embeds = await helpers.welcom_message(self, member)
                                                    await member.send(f"{member.mention}  Please read rules, you have close dms so i cant send rules in to your dms.", embeds=embeds)
                                                    await db.usersdb.update_one({"userid": member.id}, {"$set": {"rules": True, "u_rules": True}})
                                                elif "u_rules" not in userdb or not userdb["u_rules"]:
                                                    embed = get_rules()
                                                    await member.send("Thank you for continuing to use our services. We have made a few updates to our rules, which are as follows:", embed=embed)
                                                    await db.usersdb.update_one({"userid": member.id}, {"$set": {"u_rules": True}})
                                                    

                                        else:

                                            await interaction.send("You cant create ticket because this server have full categorys! ", ephemeral=True)

                            else:

                                embed = nextcord.Embed(
                                    title=lang["on_error"], description=f"Please enable direct messages or just send {self.bot.user.mention} any message and then try again!", color=0xe74c3c)
                                await interaction.send(ephemeral=True, embed=embed)

                        else:
                            if tickets.get("channelid"):
                                cprint(tickets, "yellow")
                                view = closebutton(self.bot)
                                view.bot = self.bot
                                await interaction.send(f"You cant create more than 1 ticket, Just use in <#{tickets.get('channelid')}>", ephemeral=True, view=view)
                            else:
                                await interaction.send("Please stop spamming!", ephemeral=True)
                                await db.ticketsdb.delete_many({"userid": interaction.user.id})
                    else:

                        embed = nextcord.Embed(
                            title=lang["on_error"], description=f"You are on blacklist\nto get unban [join]({support_server_link}) in to support server {support_server_link}", color=0xe74c3c)
                        embed.add_field(name="Ban Reason",
                                        value=blacklist["reason"], inline=True)
                        embed.set_footer(text=config.BRAND_FOOTER,
                                         icon_url=config.BRAND_LOGO_URL)
                        await interaction.send(ephemeral=True, embed=embed)

                else:

                    await interaction.send(f"{interaction.user.mention} Please contact <@{config.OWNER_ID}> - Error 276-lang")
            else:
                guilddb: dict = await db.guildsetting.find_one({"guildid": guild.id})
                if guilddb and (channel_id := guilddb.get("buyid")):
                    add_msg = f"Buy now in <#{channel_id}>"
                else:
                    add_msg = ""
                await interaction.send(embed=embed_error("Missing Permissions", f"You don't have the permissions to use commendbot! Firstly, you need to buy CS:GO commends before you can use it.\n{add_msg}"), ephemeral=True)
        elif serversub.get("pay", False):

            embed = nextcord.Embed(
                title="Subscription Error",
                description=f"This server has an expired resell subscription. Please contact <@{serversub.get('ownerid', 'ownerid')}> to extend the resell subscription or feel free to use your/buy balance on [{config.BRAND_NAME}]({config.BRAND_DISCORD_URL}).",
                color=Colour.red(),
                timestamp=timestamp
            )
            embed.set_footer(
                text="If a seller has sold a commend to use in a close time, they are potentially a scammer. Please contact the bot staff or just use /report in CommendBot.")
            await interaction.send(embed=embed, ephemeral=True)

        else:

            embed = nextcord.Embed(
                title="Subscription Invalid",
                description=f"This server has not active any subscription. Please contact <@{serversub.get('ownerid', 'ownerid')}> to buy the resell subscription or feel free to buy balance on [{config.BRAND_NAME}]({config.BRAND_DISCORD_URL}).",
                color=Colour.red(),
                timestamp=timestamp
            )
            embed.set_footer(
                text="If a seller has sold a commend to use in a close time, they are potentially a scammer. Please contact the bot staff or just use /report in CommendBot.")
            await interaction.send(embed=embed, ephemeral=True)
        if is_error:
            await db.ticketsdb.delete_one({"_id": _id})

    @nextcord.ui.button(label='Redeem balance key', emoji="🔑", style=nextcord.ButtonStyle.green, custom_id="redeem_cb")
    async def commendbot_redeem(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(redeem_ke_modal(self.bot))

class selectcommend(nextcord.ui.Modal):
    def __init__(self,bot,lang=None):
        super().__init__(
            "Start Commending",
            timeout=None,  
        )

        self.amount = nextcord.ui.TextInput(
            label="How many commends do you want use?",
            
            min_length=2,
            max_length=6,
            
        )
        self.add_item(self.amount)

        self.steamlink = nextcord.ui.TextInput(
            label="What is your Steam profile link?",
            min_length=2,
            
            
        )
        self.add_item(self.steamlink)
        self.lang = lang
        self.bot = bot

    async def callback(self, interaction: nextcord.Interaction) -> None:
        await interaction.response.send_message(content="Please Wait!",ephemeral=True)
        lang =self.lang
        user = interaction.user
        steamlink = self.steamlink.value
        if lang is None:
            langdb = await db.usersdb.find_one({"userid": interaction.user.id})
            lang = await get_lang(langdb, interaction.guild)
        
        
        
            
        if str(self.amount.value).isnumeric():
 
            amount = int(self.amount.value)

            baldb = await db.balancesdb.find({"userid": user.id}).to_list(None)
            steamID64 = get_steamID64(steamlink)
            if  steamID64 is None:
                error_code = "error1"
                embed=nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
                embed.set_footer(text=error_code)
                await interaction.send( embed=embed,ephemeral=True)
                return
                
                
            
            if len(baldb) == 1:
                slotid = baldb[0]["slot_id"]
                await self.bot.get_cog("commend_menu").commend_task(interaction, lang, slotid, steamID64, amount,)
                
                
            elif len(baldb) == 0:
                error_code = "error6"
                embed = nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
                embed.set_footer(text=error_code)
                await interaction.send( embed=embed,ephemeral=True,) # view=Check_show_cbprices_header(self.bot)
                
            else:
                selectOption, number = [], 0
                description = lang["commend-error-select-description"]
                
                
                slots = await db.slotsdb.find({}).to_list(None)
                for balancedb in baldb:
                    slot = next(filter(lambda i: i['_id'] == balancedb["slot_id"], slots), None)
                    
                    if slot and slot["enable"]:
                        newamount = balancedb["amount"] - amount
                        
                        if newamount >= 0:
                            description += f"\n{emojilist[number]}-{slot['_id']}. {slot['name']}・ {balancedb['amount']} commends"
                            selectOption.append(nextcord.SelectOption(
                                label=f"{slot['_id']}. {slot['name']} - {balancedb['amount']} commends",
                                emoji=emojilist[number], value=f"{slot['_id']}"))
                        else:
                            description += f"\n{config.EMOJI_NO} ~~{slot['_id']}. {slot['name']}・ {balancedb['amount']} commends ~~ — __**Not enough balance!**__"
                    else:
                        description += f"\n__**{lang['commend-error-select-description-d']}**__ = ~~{emojilist[number]}-{balancedb['slot_id']}. EXPIRED・ {balancedb['amount']} commends~~ "
                    
                    number += 1
                
                embed = nextcord.Embed(title=lang["commend-error-select-title"], description=description, color=nextcord.Color.dark_gold())
                
                if len(selectOption) != 0:
                    await interaction.message.edit(embed=embed, view=sview(self.bot, selectbalance, user, 200, selectOption, lang, steamID64, amount))
                else:
                    await interaction.send(embed=embed,ephemeral=True)
 
        else:
            error_code = "error1"
            embed=nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
            embed.set_footer(text=error_code)
            
            await interaction.edit_original_message(embed=embed)

class selectbalance(nextcord.ui.Select):
    def __init__(self,bot:Bot,selectOption,lang, steamlink,amount):
        self.bot = bot 
        self.lang = lang
        self.amount = amount
        self.steamlink = steamlink
        
        super().__init__(placeholder="Select balance:", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        slotid = int(self.values[0])
        
        lang = self.lang
        await interaction.response.defer()
        await self.bot.get_cog("commend_menu").commend_task(interaction,lang, slotid, self.steamlink,self.amount,interaction.edit_original_message,ephemeral=True)

class redeem_ke_modal(nextcord.ui.Modal):
    def __init__(self, bot: Bot):
        super().__init__("Topup balance via key")  # Modal title
        self.bot = bot

        # Create a text input and add it to the modal
        self.key = nextcord.ui.TextInput(
            label="Your key/code",
            min_length=23,
            max_length=23,
            placeholder="A84AE-77141-H8D58-BDC85"
        )
        self.add_item(self.key)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        key = self.key.value
        key.strip()
        keydb = await db.keysdb.find_one({"key": key})
        if keydb and "active" in keydb and keydb["active"]:
            await interaction.response.defer(ephemeral=False)
            await db.keysdb.update_one({"_id": keydb["_id"]}, {'$set': {'active': False, "activatedby": interaction.user.id}})
            await keygen.redeem_bal(self, interaction, keydb, True)

        else:

            embed = nextcord.Embed(
                title="Failure", description="The license key you entered is invalid/deactivated.", color=0xe74c3c)
            await interaction.response.send_message(embed=embed, ephemeral=True)

class language_header(nextcord.ui.Select):
    def __init__(self, bot: Bot, lang=translates.eng, action: str = None):
        self.action = action
        self.bot = bot

        selectOption = [
            nextcord.SelectOption(
                label=lang["menu-english"], emoji="🇬🇧", value="eng"),
            nextcord.SelectOption(
                label=lang["menu-german"], emoji="🇩🇪", value="ger"),
            nextcord.SelectOption(
                label=lang["menu-sk/cz"], emoji="🇸🇰", value="sk"),
            nextcord.SelectOption(
                label=lang["menu-pt"], emoji="🇵🇹", value="pt"),
            nextcord.SelectOption(
                label=lang["menu-hu"], emoji="🇭🇺", value="hu"),
            nextcord.SelectOption(
                label=lang["menu-pl"], emoji="🇵🇱", value="pl"),




        ]
        super().__init__(placeholder=lang["menu-title"], min_values=1,
                         max_values=1, options=selectOption, custom_id="language-menu-header")

    async def callback(self, interaction: nextcord.Interaction):

        lang = convert_lang(self.values[0])

        userdb = await db.usersdb.find_one({"userid": interaction.user.id})
        if userdb is None:
            await db.usersdb.insert_one(user_template(interaction.user, True, language=self.values[0]))

        else:
            await db.usersdb.update_one({"userid": interaction.user.id}, {"$set": {"language": self.values[0]}})

        await interaction.send(lang["lang-update"], ephemeral=True)
        if self.action == "menu":
            pass
        elif self.action == "commend":
            database = db.serverusers.find(
                {"channelid": interaction.channel.id})
            embedss = await self.bot.get_cog("commend_menu").stats(database, lang)
            await interaction.edit(embeds=embedss)

class View_human_readable(nextcord.ui.View):
    def __init__(self, **arg):
        super().__init__(timeout=None)

        # Adds the dropdown to our view object.
        self.add_item(balance_human_readable(**arg))

class menu_View(nextcord.ui.View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.bot = bot

        # Adds the dropdown to our view object.
        self.add_item(language_header(self.bot, action="menu"))
        self.add_item(balance_menu(self.bot))
        self.add_item(start_commend(self.bot))

class balance_menu(nextcord.ui.Button["balance_menu"]):
    def __init__(self, bot: Bot):
        super().__init__(style=nextcord.ButtonStyle.primary,
                         label="My Balance", custom_id="balance_menu")
        self.bot = bot

    async def callback(self, interaction: nextcord.Interaction):
        await self.bot.get_cog("commend_menu").show_balance(interaction, True)

class balance_human_readable(nextcord.ui.Select):
    def __init__(
        self,
        bot: Bot,
        *,
        default=True,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
    ) -> None:
        options = [
            SelectOption(
                label="Human Readable",
                value="1",
                description="e.g. 1k, 20M, 4.5k...",
                emoji="👀",
                default=default,
            ),
            SelectOption(
                label="Clean Numbers",
                value="0",
                description="e.g. 10000, 520445, 454544...",
                emoji="🔢",
                default=not default,
            ),
        ]
        self.bot = bot
        super().__init__(
            custom_id="balance_human_readable",
            placeholder="Select balance type",
            min_values=min_values,
            max_values=max_values,
            options=options,
            disabled=disabled,
        )

    async def callback(self, interaction: nextcord.Interaction):
        result = bool(self.values[0])
        await self.bot.get_cog("commend_menu").show_balance(interaction, result, True)

class start_commend(nextcord.ui.Button["start_commend"]):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__(style=nextcord.ButtonStyle.green,
                         label="Start Commending", custom_id="start_commend")

    async def callback(self, interaction: nextcord.Interaction):
        
        await interaction.response.send_modal(selectcommend(self.bot))
        await delete_autodelete(interaction.channel)

class Select_StopCommending(nextcord.ui.Button):
    def __init__(self, bot: Bot):
        self.bot = bot

        super().__init__(custom_id="button-stop",
                         label="Stop Commending", style=nextcord.ButtonStyle.red)

    async def callback(self, interaction: nextcord.Interaction):
        database = db.serverusers.find({"channelid": interaction.channel.id})
        SelectOption = []
        async for counte, accountdb in a.enumerate(database, 1):

            SelectOption.append(nextcord.SelectOption(
                label=f"{counte}. {accountdb['steamID64']}  ", value=accountdb['steamID64']))
        if len(SelectOption) > 1:
            await interaction.send(view=sview(self.bot, Button_StopCommending, interaction.user, None, SelectOption), ephemeral=True)
        elif len(SelectOption) == 1:
            await self.bot.get_cog("commend_menu").stop_request(interaction, accountdb, interaction.send)
        else:
            await interaction.send("There is not any commending session!", ephemeral=True)

class Button_StopCommending(nextcord.ui.Select):
    def __init__(self, bot: Bot, selectOption: list[nextcord.SelectOption]):
        self.bot = bot

        super().__init__(placeholder="Select account/s to stop...",
                         min_values=1, max_values=len(selectOption), options=selectOption)

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()

        for steamID64 in self.values:

            serverdb = await db.serverusers.find_one({"steamID64": int(steamID64)})

            if serverdb:
                await self.bot.get_cog("commend_menu").stop_request(interaction, serverdb, interaction.send)

class closebutton(nextcord.ui.View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @nextcord.ui.button(label="Close ticket", style=nextcord.ButtonStyle.red, custom_id="closebutton-ss")
    async def closebutton(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):

        button.disabled = True

        ticketsdb = await db.ticketsdb.find_one({"userid": interaction.user.id})
        if ticketsdb:

            channel = self.bot.get_channel(ticketsdb.get("channelid"))
            await self.bot.get_cog("commend_menu").close_ticket(channel, interaction, reason="button_command", ticketsdb=ticketsdb, agressive=False, edit_message=True)

        else:

            await interaction.response.edit_message(view=self, content="Channel is Non Commendbot type")

class promo_view(nextcord.ui.View):
    """Single link button pointing at the configured referral offer."""

    def __init__(self):
        super().__init__(timeout=None)
        if config.PROMO_INVITE_URL:
            self.add_item(
                nextcord.ui.Button(label="Join Now!", url=config.PROMO_INVITE_URL)
            )
