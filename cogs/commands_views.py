"""Interactive views and selects used by the bot_commands cog."""

import datetime

import asyncstdlib as a
import nextcord
import pymongo
from nextcord import Embed, Member, User
from nextcord.ext.commands import Bot
from pymongo import ReturnDocument

import config

# (nothing needed from cogs.commend)
from cogs.helpers import helpers
from cogs.slot import slots_stats
from cogs.transactions_logs import logs
from utils import (
    bluepr,
    can_dm_user,
    db,
    emebd_remove,
    get_user_avatar,
    is_number,
    sview,
    timestamp,
    tz,
    user_template,
)

script_top = datetime.datetime.now(tz=tz)


class Confirm_req(nextcord.ui.View):
    def __init__(self, user: User):
        super().__init__()
        self.value = None
        self._user = user

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Confirming", ephemeral=True)
        self.value = True
        self.stop()

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Cancelling", ephemeral=True)
        self.value = False
        self.stop()

    async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
        if self._user is not None:
            variable = interaction.user == self._user
            if not variable:
                embed = nextcord.Embed(
                    title="error", description=f"**This `button` only can use {self._user.mention}**", color=nextcord.Colour.orange())
                await interaction.send(embed=embed, ephemeral=True)

            return variable
        return True

class Spin_wheel(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=10)
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @nextcord.ui.button(label="Spin", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_message("Spinning", ephemeral=True)
        self.value = True
        self.stop()

class wheel_spin_select(nextcord.ui.Select):
    def __init__(self, bot: Bot, selectOption):
        self.bot = bot

        super().__init__(placeholder="Select wallet",
                         min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):

        slot_id = int(self.values[0])
        # The original passed `interaction` as `self` here, so this path
        # always raised; go through the cog instance instead.
        await self.bot.get_cog("bot_commands").wheel_spin(interaction, slot_id)

class showslotsgraphs(nextcord.ui.Select):
    def __init__(self, bot: Bot, selectOption, member):
        self.bot = bot
        self.member: Member = member

        super().__init__(placeholder="Select Slot",
                         min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        member = self.member
        if int(self.values[0]) == 0:
            await self.bot.get_cog("bot_commands").userinfo(member, interaction, interaction.message)

        else:
            slot_id = int(self.values[0])
            baldbg = await db.balancesdb.find_one({"userid": member.id, "slot_id": slot_id})
            graph = await self.bot.get_cog("bot_commands").getgraph(interaction.user, slot_id, baldbg)
            aurl = get_user_avatar(member)
            embed = nextcord.Embed(color=bluepr, timestamp=timestamp,)
            embed.set_author(name=member, url=aurl, icon_url=aurl)
            embed.set_thumbnail(url=aurl)

            embed.set_footer(text=config.BRAND_FOOTER,
                             icon_url=config.BRAND_LOGO_URL)

            embed.add_field(name="Slot Balance",
                            value=f"`{baldbg['amount']} commends`", inline=False)

            embed.set_image(url="attachment://transactions.png")
            embed.set_footer(text=config.BRAND_FOOTER,
                             icon_url=config.BRAND_LOGO_URL)
            baldbs = db.balancesdb.find({"userid": member.id})
            slots = await db.slotsdb.find({}).to_list(None)

            SelectOption = []
            emojilist = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪"]
            SelectOption.append(nextcord.SelectOption(
                label="Back to profile", emoji="👤", value=0))
            async for id, baldb in a.enumerate(baldbs):
                slotdb = list(
                    filter(lambda i: i['_id'] == baldb["slot_id"], slots))[0]

                if baldb["slot_id"] == slot_id:

                    embed.add_field(
                        name="Daily Limit", value=f"`{baldbg['today_used']}`**/**`{slotdb['max_daily_commends']} commends`", inline=False)
                else:
                    SelectOption.append(nextcord.SelectOption(
                        label=f"{slotdb['name']} Slot", emoji=emojilist[id], value=baldb["slot_id"]))

            await interaction.message.edit(file=graph, embed=embed, view=sview(self.bot, showslotsgraphs, interaction.user, 130, SelectOption, member))

class selectaddslot(nextcord.ui.Select):
    def __init__(self, bot: Bot, selectOption, price, note, customer: User or Member, amount):
        self.bot = bot
        self.price = price
        self.note = note
        self.customer = customer
        self.amount = amount

        super().__init__(placeholder="Select Option",
                         min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):

        slot_id = int(self.values[0])

        price = self.price
        note = self.note
        member = self.customer
        amount = self.amount
        await helpers.addbal(self, amount, member, slot_id, interaction.user, interaction, price, note)

class selectgiftslot(nextcord.ui.Select):
    def __init__(self, bot: Bot, selectOption, customer: Member or User, amount: int, fees: float, reseller: bool):
        self.customer = customer
        self.bot = bot
        self.amount = amount
        self.fees = fees
        self.reseller = reseller
        super().__init__(placeholder="Select Option",
                         min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):

        value = self.values[0]
        reseller = self.reseller
        member = self.customer

        amount = self.amount

        slot_id = int(value)
        gifter = interaction.user
        gifterbalance = await db.balancesdb.find_one({"userid": gifter.id, "slot_id": slot_id})
        usertest = await db.balancesdb.find_one({"userid": member.id, "slot_id": slot_id})

        logowner = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
        oldamountg = gifterbalance["amount"]
        if reseller:
            fees = 0

        else:
            fees = self.fees
            feesdb = await db.balancesdb.find_one({"userid": self.bot.user.id, "slot_id": slot_id})
            feesbal = feesdb["amount"] + fees

        newamountg = oldamountg - amount - fees

        if not newamountg < 0:
            userdb = await db.usersdb.find_one({"userid": member.id})
            if not userdb:
                try:
                    embeds = await helpers.welcom_message(self, member)
                    await member.send(embeds=embeds)
                    print("after embed")
                except Exception:
                    await db.usersdb.insert_one(user_template(member, False))
                else:
                    await db.usersdb.insert_one(user_template(member, True))
                print("user got embed")

            if usertest is None:
                await db.balancesdb.insert_one({"userid": member.id, "guildid": interaction.guild.id, "lastid": interaction.user.id, "amount": amount, "slot_id": slot_id, "today_used": 0, "onhold": 0, "active": True})
                await db.balancesdb.update_one({"userid": interaction.user.id, "slot_id": slot_id}, {"$set": {"amount": newamountg}})
                newamount = amount
                oldamount = 0

            else:

                oldamount = int(usertest["amount"])
                if oldamount < 0:
                    await logowner.send(f"error: User: {member.mention} `{member.id}` , Guild: {interaction.guild} `{interaction.guild.id}` , Adminby: {interaction.user.mention} `{interaction.user.id}` try add user commends but user have {oldamount} commends and bot automaticly regenerated userdb to 0 + {amount} !  ")
                    oldamount = 0
                newamount = oldamount + amount
                await db.balancesdb.update_one({"userid": member.id, "slot_id": slot_id}, {"$set": {"amount": newamount}})
                await db.balancesdb.update_one({"userid": interaction.user.id, "slot_id": slot_id}, {"$set": {"amount": newamountg}})

            embed = nextcord.Embed(title="Balance gifted!", description="Balance has been gifted to the user.",
                                   color=bluepr, timestamp=datetime.datetime.now())
            embed.set_footer(text=config.BRAND_FOOTER,
                             icon_url=config.BRAND_LOGO_URL)
            embed.add_field(name="Balance gifted by:",
                            value=interaction.user.mention, inline=False)
            embed.add_field(name="Balance gifted to:",
                            value=member.mention, inline=False)

            embed.add_field(name="Amount gifted:",
                            value=f"{amount} commends", inline=False)
            embed.add_field(name="Fees for transaction",
                            value=f"{fees} commends", inline=False)
            embed.add_field(name="User's old balance:",
                            value=f"{oldamount} commends", inline=False)
            embed.add_field(name="User's current balance:",
                            value=f"{newamount} commends", inline=False)
            await interaction.send(embed=embed, ephemeral=False)

            try:

                await member.send(embed=embed)
            except Exception:
                if interaction.channel.permissions_for(member).view_channel and interaction.channel.permissions_for(member).read_message_history and interaction.channel.permissions_for(member).read_messages:

                    await interaction.channel.send(f"{member.mention} please unlock me in dms or bot cant work correctly!")

            embed.add_field(name="Gifter's old balance:",
                            value=f"{oldamountg} commends", inline=False)
            embed.add_field(name="Gifter's current balance:",
                            value=f"{newamountg} commends", inline=False)

            await helpers.logembed(self, embed, interaction.guild, slot_id)
            if not reseller:
                await db.balancesdb.update_one({"userid": self.bot.user.id, "slot_id": slot_id}, {"$set": {"amount": feesbal}})
        else:
            await interaction.send("You u don't have enough commends!(ojebavač)", ephemeral=True)

class Sequencemenu(nextcord.ui.Select):
    def __init__(self, bot: Bot, userid):
        self.bot = bot
        selectOption = [
            nextcord.SelectOption(
                label="reset every month at ...", value=f"{userid}-1", ),
            nextcord.SelectOption(
                label="reset every 3 months at ...", value=f"{userid}-2", ),
            nextcord.SelectOption(
                label="reset every year at ...", value=f"{userid}-3", ),
            nextcord.SelectOption(
                label="reset when resell sub ends", value=f"{userid}-4", ),
            nextcord.SelectOption(label="Never reset",
                                  emoji="❌", value=f"{userid}-5", ),









        ]
        super().__init__(placeholder="Select Option",
                         min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):

        value = self.values[0]
        value = value.split("-")
        if interaction.user.id == int(value[0]):
            if int(value[6]) == 1:
                embed = Embed(title="Please set a day when u want to reset balance.(it ll reset every 1 month at 00:00UTC customers balance )",
                              description="Just type day(1-31) e.g. 12", color=nextcord.Color.greyple())
                embed.set_footer(text=config.BRAND_FOOTER,
                                 icon_url=config.BRAND_LOGO_URL)
                await interaction.send(embed=embed)
                try:
                    msg: nextcord.Message = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and message.author.id == interaction.user.id, timeout=180)

                except Exception:

                    embed = nextcord.Embed(
                        title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,
                                     icon_url=config.BRAND_LOGO_URL)

                    await interaction.channel.send(embed=embed, delete_after=60)
                else:
                    if msg.content.isnumeric():

                        await db.slotsdb.update_one({"_id": int(value[4])}, {"$unset": {"reset_bysub": "", "reset_1y": "", "reset_3m": "", "reset_1m": ""}})
                        await db.slotsdb.update_one({"_id": int(value[4])}, {"$set": {"reset_1m": int(msg.content)}})
                        await msg.delete()
                        await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set pm2id to { msg.content}**")
                    else:
                        embed = Embed(title="error | value isn't numeric",
                                      description="Cancelled the Operation!", color=0xff0000)
                        embed.set_footer(text=config.BRAND_FOOTER,
                                         icon_url=config.BRAND_LOGO_URL)
                        await interaction.channel.send(embed=embed, delete_after=60)
            elif int(value[6]) == 2:
                embed = Embed(title="Please set a day when u want to reset balance.(it ll reset every 3months at 00:00UTC customers balance )",
                              description="Just type day(1-31) e.g. 12", color=nextcord.Color.greyple())
                embed.set_footer(text=config.BRAND_FOOTER,
                                 icon_url=config.BRAND_LOGO_URL)
                await interaction.send(embed=embed)
                try:
                    msg: nextcord.Message = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and message.author.id == interaction.user.id, timeout=180)

                except Exception:

                    embed = nextcord.Embed(
                        title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,
                                     icon_url=config.BRAND_LOGO_URL)

                    await interaction.channel.send(embed=embed, delete_after=60)
                else:
                    if msg.content.isnumeric():

                        # can be better
                        await db.slotsdb.update_one({"_id": int(value[4])}, {"$unset": {"reset_bysub": "", "reset_1y": "", "reset_3m": "", "reset_1m": ""}})
                        await db.slotsdb.update_one({"_id": int(value[4])}, {"$set": {"reset_3m": int(msg.content)}})
                        await msg.delete()
                        await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set pm2id to { msg.content}**")
                    else:
                        embed = Embed(title="error | value isn't numeric",
                                      description="Cancelled the Operation!", color=0xff0000)
                        embed.set_footer(text=config.BRAND_FOOTER,
                                         icon_url=config.BRAND_LOGO_URL)
                        await interaction.channel.send(embed=embed, delete_after=60)
            elif int(value[6]) == 3:
                embed = Embed(title="Please set a day and month when u want to reset balance.(it ll reset every year specific day & month at 00:00UTC customers balance )",
                              description="Just type day(1-31).month(1-12) e.g. 14.5", color=nextcord.Color.greyple())
                embed.set_footer(text=config.BRAND_FOOTER,
                                 icon_url=config.BRAND_LOGO_URL)
                await interaction.send(embed=embed)
                try:
                    msg: nextcord.Message = await self.bot.wait_for('message', check=lambda message: message.channel == interaction.channel and message.author.id == interaction.user.id, timeout=180)

                except Exception:

                    embed = nextcord.Embed(
                        title="error | Your Time ran out", description="Cancelled the Operation!", color=0xff0000)
                    embed.set_footer(text=config.BRAND_FOOTER,
                                     icon_url=config.BRAND_LOGO_URL)

                    await interaction.channel.send(embed=embed, delete_after=60)
                else:
                    if is_number(msg.content):

                        await db.slotsdb.update_one({"_id": int(value[4])}, {"$unset": {"reset_bysub": "", "reset_1y": "", "reset_3m": "", "reset_1m": ""}})
                        await db.slotsdb.update_one({"_id": int(value[4])}, {"$set": {"reset_1y": msg.content}})
                        await msg.delete()
                        await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set reset to every year at {msg.content}:00:00UTC**")
                    else:
                        embed = Embed(title="error | value isn't numeric",
                                      description="Cancelled the Operation!", color=0xff0000)
                        embed.set_footer(text=config.BRAND_FOOTER,
                                         icon_url=config.BRAND_LOGO_URL)
                        await interaction.channel.send(embed=embed, delete_after=60)
            elif int(value[6]) == 4:
                slotdb = await db.slotsdb.find_one({"_id": int(value[4])})
                botspam = self.bot.get_channel(slotdb["bot_logchannelid"])
                try:
                    msg: nextcord.Message = await self.bot.wait_for('message', check=lambda message: message.channel == botspam.channel and message.embeds and slotdb["userid"] in message.embeds[0].fields[0].value, timeout=30)

                except Exception:

                    await interaction.channel.send("Call bot support")
                else:
                    datetimeds = msg.embeds[0].fields[4].value
                    datetimedsd = datetimeds.split(":")
                    datetimedsd = datetimedsd[1].split(">")[0]
                    value = datetime.datetime.utcfromtimestamp(
                        int(datetimedsd)).replace(tzinfo=datetime.timezone.utc)
                    await db.slotsdb.update_one({"_id": int(value[4])}, {"$unset": {"reset_bysub": "", "reset_1y": "", "reset_3m": "", "reset_1m": ""}})
                    await db.slotsdb.update_one({"_id": int(value[4])}, {"$set": {"reset_bysub": f"{value.day}.{value.month}"}})

                    await interaction.channel.send(f"**{config.EMOJI_YES}  Successfully set reset to every resell sub end on sub end next reset {datetimeds}")

        else:
            user = interaction.guild.get_member(int(value[0]))
            embed = Embed(
                title="error", description=f"**This `Selection` only can use {user.mention}**", color=0xfffff0)
            await interaction.send(embed=embed, ephemeral=True)

class selectremoveslot(nextcord.ui.Select):
    def __init__(self, bot: Bot, selectOption, amount, reason, member: User):
        self.bot = bot
        self.reason = reason
        self.amount = amount

        self.member = member
        super().__init__(placeholder="Select Option",
                         min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):

        value = int(self.values[0])

        member = self.member

        amount = self.amount
        slot_id = value

        usertest = await db.balancesdb.find_one({"userid": member.id, "slot_id": slot_id})

        oldamount = int(usertest["amount"])
        if oldamount < 0:
            oldamount = 0
        if "onhold" not in usertest:
            onhold = 0
        else:
            onhold = usertest["onhold"]
        newamount = oldamount - amount
        await db.balancesdb.update_one({"userid": member.id, "slot_id": slot_id}, {"$inc": {"amount": -amount, "onhold": amount}})
        embed = emebd_remove(member, interaction.user,
                             amount, oldamount, newamount, onhold)
        await interaction.send(embed=embed, ephemeral=False)
        await self.bot.get_cog("bot_commands").remove_request(member, interaction.user, amount, self.reason, slot_id)
        await helpers.logembed(self, embed, interaction.guild, slot_id)

class profile(nextcord.ui.Select):
    def __init__(self, bot: Bot, selectOption, member):
        self.bot = bot
        self.member = member

        super().__init__(placeholder="Select ", min_values=1,
                         max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        if self.member:
            member = self.member
        else:
            member = interaction.user
        option = int(self.values[0])
        if option == 1:
            glist = await db.sellsds.find({"$or": [{"gifterid": member.id}, {"customerid": member.id}, {"sellerid": member.id}]}).sort("_id", pymongo.DESCENDING).to_list(None)
            await logs.transaction(self, interaction, member, 0, glist)
        elif option == 2:
            await slots_stats.pre_stats(self, interaction)

class removebal(nextcord.ui.View):
    def __init__(self, bot: Bot, amount, customer: User, slotid: int, admin: User):
        self.customer = customer
        self.amount = amount
        self.slotid = slotid
        self.bot = bot
        self.admin = admin
        super().__init__(timeout=None)

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.

    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        datetime_utc = datetime.datetime.now(tz=tz)
        customerid = self.customer
        adminid = self.admin
        if isinstance(customerid, int):

            customer = self.bot.get_user(customerid)
        else:
            customer = customerid

        if type(adminid) == int:
            admin = await self.bot.get_user(adminid)
        else:
            admin = adminid

        await interaction.response.send_message("Confirming", ephemeral=True)
        await db.refresh.delete_one({"msgid": interaction.message.id})
        await interaction.message.edit(content="Confirmed", view=None)
        amount = self.amount
        slotid = self.slotid
        baldb = await db.balancesdb.find_one_and_update({"userid": customer.id, "slot_id": slotid}, {"$inc": {"onhold": -amount}}, return_document=ReturnDocument.AFTER)
        await db.sellsds.insert_one({

            "datetime": datetime_utc,

            "customerid": customer.id,
            "slot_id": slotid,
            "remove-amount": amount,
            "u_old-amount": (baldb["amount"]+amount),
            "u_new-amount": baldb["amount"],
            "type": "remove"

        })

        dm = await can_dm_user(admin)
        if dm:
            await admin.send(f"Admins of commendbot Confirm remove balance from {customer}")
        dm2 = await can_dm_user(customer)
        if dm2:
            await customer.send(f"Admins of commendbot accept remove balance from you so was removed  {amount} commends")
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        
        
        if isinstance(self.customer,int):
            customer =  self.bot.get_user(self.customer)
        else:
            customer = self.customer
        if isinstance(self.admin,int):
            admin =  self.bot.get_user(self.admin)
        else:
            admin = self.admin
        await interaction.response.send_message("Canceling", ephemeral=True)
        await db.refresh.delete_one({"msgid": interaction.message.id})
        await interaction.message.edit(content="Canceled", view=None)
        amount = self.amount
        
        slotid = self.slotid
        await db.balancesdb.update_one({"userid": customer.id, "slot_id": slotid}, {"$inc": {"onhold": -amount, "amount": amount}})
        dm = await can_dm_user(admin)
        if dm:
            await admin.send(f"Admins of commendbot reject remove balance from {customer}")
        dm2 = await can_dm_user(customer)
        if dm2:
            await customer.send(f"Admins of commendbot reject remove balance from you so u have back {amount} commends")

        self.stop()
