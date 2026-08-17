"""Everything that moves commends between balances."""

import datetime

import asyncstdlib as a
import cooldowns
import nextcord
from nextcord import Color, Colour, Interaction, Member, SlashOption, User

import config
from cogs.commands_views import removebal, selectaddslot, selectgiftslot, selectremoveslot

# (nothing needed from cogs.commend)
from cogs.helpers import helpers
from utils import (
    admins,
    bluepr,
    convert_value,
    db,
    embed_error,
    emebd_remove,
    feescalc,
    sview,
    timestamp,
    tz,
)

script_top = datetime.datetime.now(tz=tz)


class BalanceCommands:
    """Mix into bot_commands; see cogs/commands.py."""

    @nextcord.slash_command(
        name="removebalance",
        description="remove balance from specific user",

    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def removebalance_command(self, interaction: Interaction,
                                    member: nextcord.User = SlashOption(
                                        name="user", description="User to remove balance", required=True),
                                    amount: int = SlashOption(
                                        name="amount", description="Choose a amount of commends to remove", required=True),
                                    reason: str = SlashOption(
                                        name="reason", description="Reason why u want remove balance", required=True),
                                    ):

        amount = abs(amount)

        if interaction.user.id == self.bot.owner_id:
            slotsdb = await db.slotsdb.find({}).to_list(None)
        else:
            slotsdb = await db.slotsdb.find({"admins": { "$in":[interaction.user.id] }}).to_list(None)
        balances = db.balancesdb.find({"userid": member.id})
        counter = 0
        selectOption = []
        async for baldb in balances:

            slot_id = baldb["slot_id"]
            slotdb = list(
                filter(lambda i: i['_id'] == baldb["slot_id"], slotsdb))
            if len(slotdb) != 0:

                counter += 1

                selectOption.append(nextcord.SelectOption(
                    label=f"{counter}. {slotdb[0]['name']}", value=slot_id))

        if counter == 1:

            usertest = baldb

            oldamount = int(usertest["amount"])
            if oldamount < 0:
                oldamount = 0

            newamount = oldamount - amount

            # mb extend it here request
            await db.balancesdb.update_one({"userid": member.id, "slot_id": slot_id}, {"$inc": {"amount": -amount, "onhold": amount}})
            if "onhold" not in usertest:
                onhold = 0
            else:
                onhold = usertest["onhold"]
            embed = emebd_remove(member, interaction.user,
                                 amount, oldamount, newamount, onhold)
            await interaction.send(embed=embed, ephemeral=False)
            if member.id != self.bot.user.id:
                await member.send(embed=embed)
            await helpers.logembed(self, embed, interaction.guild, slot_id)
            await self.remove_request(member, interaction.user, amount, reason, slot_id)
        elif len(balances) == 0:
            embed = nextcord.Embed(
                title="Error", description="This user dont have any balance!", color=Colour.red, timestamp=timestamp,)
            await interaction.send(embed=embed, ephemeral=True)

        elif counter == 0:
            embed = nextcord.Embed(
                title="error", description="Only the **admin** of slot or **developer** of bot can use this command.", color=0xff0000)
            await interaction.send(embed=embed, ephemeral=True)

        else:
            embed = nextcord.Embed(
                title="Select Slot", description="Please select a slot you would like gift balance from:", color=nextcord.Color.orange())
            await interaction.send(embed=embed, ephemeral=True, view=sview(self.bot, selectremoveslot, interaction.user, 120, selectOption, amount, reason, member))

    async def remove_request(self, customer: User or Member, admin: User or Member, amount, reason: str, slotid):
        print("remove_request hre e")
        requestchannel = self.bot.get_channel(config.REQUEST_CHANNEL_ID)
        embed = nextcord.Embed(
            title="Remove balance request", color=bluepr, timestamp=timestamp,)
        embed.add_field(name="Remove admin", value=admin, inline=False)
        embed.add_field(name="Remove from", value=customer, inline=False)
        embed.add_field(name="Amount to remove", value=amount, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        msg = await requestchannel.send(embed=embed, view=removebal(self.bot, amount, customer, slotid, admin))
        await db.refresh.insert_one({"msgid": msg.id, "channelid": requestchannel.id, "view": "removebal", "values": [amount, customer.id, slotid, admin.id]})

    @nextcord.slash_command(
        name="transfer",
        description="transfer command",



    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def transfer_command(self,
                               interaction: Interaction, user: User, amount: int, slot_id: int, delother: bool

                               ):
        if interaction.user.id == self.bot.owner_id or interaction.user.id in admins:
            baldb = await db.balancesdb.find_one({"userid": user.id, "slot_id": slot_id})
            if baldb:
                if newonhold := (baldb["onhold"] - amount) > 0:

                    if delother:
                        await db.balancesdb.update_one({"_id": baldb["_id"]}, {'$set': {"onhold": 0}, '$inc': {"amount": +amount}})

                    else:
                        await db.balancesdb.update_one({"_id": baldb["_id"]}, {'$inc': {"onhold": -amount, "amount": +amount}})

                    await interaction.send("ok", ephemeral=True)

                else:
                    await interaction.send(f"onhold balance cant be negative {newonhold}", ephemeral=True)

            else:
                await interaction.send("This user or slot doesnt exist", ephemeral=True)

    @nextcord.slash_command(name="transferbalance", description="transfer from user to next user balance",)
    async def transferbalance_command(self,
                                      interaction: Interaction,
                                      gifter: nextcord.Member = SlashOption(
                                          name="transferfrom", description="transfer balance", required=True),
                                      member: nextcord.Member = SlashOption(
                                          name="transferto", description="add balance", required=True),
                                      amount: int = SlashOption(
                                          name="amount", description="Choose a amount of commends", required=True),
                                      ):
        if interaction.user.id == self.bot.owner_id:
            gifterbalance = await db.balancesdb.find_one({"userid": gifter.id})
            if gifterbalance is not None:
                oldamountg = gifterbalance["amount"]
                newamountg = oldamountg - amount
                if newamountg < 0:
                    await interaction.send("You u don't have enough commends!", ephemeral=True)
                else:

                    usertest = await db.balancesdb.find_one({"userid": member.id})
                    logowner = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
                    if usertest is None:
                        await db.balancesdb.insert_one({"userid": member.id, "guildid": interaction.guild.id, "lastid": gifter.id, "amount": amount, "slot_id": 1, "today_used": 0, "onhold": 0, "active": True})
                        await db.balancesdb.update_one({"userid": gifter.id}, {"$set": {"amount": newamountg}})
                        embed = nextcord.Embed(
                            title="Balance gifted!", description="Balance has been gifted to the user.", color=bluepr, timestamp=datetime.datetime.now())
                        embed.add_field(name="Balance gifted to:",
                                        value=member.mention, inline=False)
                        embed.add_field(name="Balance gifted by:",
                                        value=gifter.mention, inline=False)
                        embed.add_field(name="Amount gifted:",
                                        value=f"{amount} commends", inline=False)
                        embed.add_field(name="Gifted's old balance:",
                                        value="0 commends", inline=False)
                        embed.add_field(
                            name="Gifted's current balance:", value=f"{amount} commends", inline=False)
                        embed.add_field(
                            name="Transfer's old balance:", value=f"{oldamountg} commends", inline=False)
                        embed.add_field(name="Transfer's current balance:",
                                        value=f"{newamountg} commends", inline=False)
                        if interaction.guild.icon is not None:
                            embed.set_footer(
                                text=interaction.guild, icon_url=interaction.guild.icon.url)

                        await interaction.send(embed=embed, ephemeral=False)
                        await logowner.send(embed=embed)
                    else:
                        oldamount = int(usertest["amount"])
                        if oldamount < 0:
                            await logowner.send(f"error: User: {member.mention} `{member.id}` , Guild: {interaction.guild} `{interaction.guild.id}` , Adminby: {interaction.user.mention} `{interaction.user.id}` try add user commends but user have {oldamount} commends and bot automaticly regenerated userdb to 0 + {amount} !  ")
                            oldamount = 0
                        newamount = oldamount + amount
                        await db.balancesdb.update_one({"userid": member.id}, {"$set": {"amount": newamount}})
                        await db.balancesdb.update_one({"userid": gifter.id}, {"$set": {"amount": newamountg}})
                        embed = nextcord.Embed(
                            title="Balance gifted!", description="Balance has been gifted to the user.", color=bluepr, timestamp=datetime.datetime.now())
                        embed.add_field(name="Balance gifted to:",
                                        value=member.mention, inline=False)
                        embed.add_field(name="Balance gifted by:",
                                        value=gifter.mention, inline=False)
                        embed.add_field(name="Amount gifted:",
                                        value=f"{amount} commends", inline=False)
                        embed.add_field(name="Gifted's old balance:",
                                        value=f"{oldamount} commends", inline=False)
                        embed.add_field(
                            name="Gifted's current balance:", value=f"{newamount} commends", inline=False)
                        embed.add_field(
                            name="Transfer's old balance:", value=f"{oldamountg} commends", inline=False)
                        embed.add_field(name="Transfer's current balance:",
                                        value=f"{newamountg} commends", inline=False)
                        if interaction.guild.icon is not None:
                            embed.set_footer(
                                text=interaction.guild, icon_url=interaction.guild.icon.url)
                        await interaction.send(embed=embed, ephemeral=False)
                        await logowner.send(embed=embed)
            else:
                await interaction.send("You u don't have enough commends to gift!(You have 0 commends)", ephemeral=True)
        else:
            embed = nextcord.Embed(
                title="error", description="Only the **Administrator** can use this command.", color=0xff0000)
            await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="addbalance", description="add balance to specific user",)
    async def addbalance_command(self,
                                 interaction: Interaction,
                                 member: nextcord.User = SlashOption(
                                     name="user", description="User to add balance", required=True),
                                 amount: int = SlashOption(
                                     name="amount", description="Choose a amount of commends", required=True),
                                 price: float = SlashOption(
                                     name="price", description="set price for commends in €", required=True),
                                 note: str = SlashOption(
                                     name="note", description="set note", required=False),
                                 ):
        if amount is None and price is not None:
            amount = convert_value(price)
            
        
        elif amount < 0:
            embed = nextcord.Embed(
            title="Error", description="U cant use negative number!", color=0xff0000)
            await interaction.send(embed=embed, ephemeral=True)
            
        
           

        if interaction.user.id == self.bot.owner_id:
            slotsdb = db.slotsdb.find({})
        else:
            slotsdb = db.slotsdb.find({"admins": { "$in":[interaction.user.id] }})
        
        if  0 <= price:
            counter = 0
            selectOption = []
            # idk if number 1 ll not write in to counter when 0 files in slotsdb
            async for counter, slotdb in a.enumerate(slotsdb, 1):

                slot_id = slotdb["_id"]
                selectOption.append(nextcord.SelectOption(
                    label=f"{counter}. {slotdb['name']}", value=slot_id))

            if counter == 1:
                await interaction.response.defer()
                await helpers.addbal(self, amount, member, slot_id, interaction.user, interaction, price, note)

            elif counter is None or counter == 0:
                embed = nextcord.Embed(
                    title="error", description="Only the **admin** of slot or **developer** of bot can use this command.", color=0xff0000)
                await interaction.send(embed=embed, ephemeral=True)

            else:
                embed = nextcord.Embed(
                    title="Select Slot", description="Please select a slot you would like gift balance from:", color=nextcord.Color.orange())
                customer = member
                await interaction.send(embed=embed, ephemeral=True, view=sview(self.bot, selectaddslot, interaction.user, 120, selectOption, price, note, customer, amount))
        else:
            embed = nextcord.Embed(
                title="Error", description="Price cant be negative number!", color=0xff0000)
            await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="giftbalance",
        description="transfer your balance to specific user",

    )
    @cooldowns.cooldown(20, 1800, bucket=cooldowns.SlashBucket.author,cooldown_id="spamcheck")
    async def giftbalance_command(self,
                                  interaction: Interaction,
                                  member: nextcord.Member = SlashOption(
                                      name="user", description="gif to add balance", required=True),
                                  amount: int = SlashOption(
                                      name="amount", description="Choose a amount of commends", required=True),
                                  ):
        if member.id in config.BLOCKED_BALANCE_USER_IDS:
            embed = nextcord.Embed(title="Error", description="you cant add balance to this user", color=Color.red(), )
            await interaction.send(embed=embed,ephemeral=True)
            return
        
        if amount > 0:
            
            counter = 0
            selectOption = []
            gifterbalances = db.balancesdb.find(
                {"userid": interaction.user.id})
            slotlist = await db.slotsdb.find({}).to_list(None)
            description = "Please select a slot you would like gift balance from:\n\n"

            blacklistdb = await db.blacklistdb.find_one({"userid": interaction.user.id})
            if not blacklistdb:
                blacklistud = await db.blacklistdb.find_one({"userid": member.id})
                if not blacklistud:
                    reselldb = await db.subdb.find_one({"ownerid": interaction.user.id, "disabled": False, "pay": True})
                    if reselldb:
                        reseller = True
                        

                    else:
                        reseller = False

                        

                    async for balanced in gifterbalances:
                        slotdb = list(
                            filter(lambda i: i['_id'] == balanced["slot_id"], slotlist))
                        if len(slotdb) != 0:
                            slotdb=slotdb[0]
                            slot_id = slotdb["_id"]
                            feesg = feescalc(amount)
                            if reseller:
                                fees = 0

                            else:
                                fees = feesg

                            newamountg = balanced["amount"] - amount - fees

                            counter += 1
                            if not newamountg < 0:

                                if slotdb["enable"]:
                                    description += f"{config.EMOJI_YES} {counter}. **{str(slotdb['name'])}** slot — **{balanced['amount']}** commends\n"
                                    selectOption.append(nextcord.SelectOption(
                                        label=f"{counter}. {slotdb['name']}", value=slot_id))
                                else:
                                    description += f"⛔ {counter}. ~~**{str(slotdb['name'])}** slot — **{balanced['amount']}** commends~~ — __**Slot is Disabled!**__\n"
                            else:
                                description += f"{config.EMOJI_NO} {counter}. ~~**{str(slotdb['name'])}** slot — **{balanced['amount']}** commends~~ — __**Not enough balance!**__\n"

                    if counter == 1:
                        await interaction.response.defer(ephemeral=False)
                        await helpers.giftbal(self=self, reseller=reseller,  gifterdb=balanced, amount=amount, interaction=interaction, gifter=interaction.user, customer=member, guild=interaction.guild)

                    elif counter == 0:
                        await interaction.send(embed=embed_error("Enough Commends", "You u don't have enough commends to gift!(You have 0 commends)"), ephemeral=True)
                    else:
                        embed = nextcord.Embed(
                            title="Select Slot", description=description, color=nextcord.Color.orange())

                        if len(selectOption) != 0:
                            customer = member
                            reselldb = await db.subdb.find_one({"ownerid": interaction.user.id})
                            if reselldb:
                                print("reseller is anybody")
                                reseller = True
                                fees = 0

                            else:
                                fees = feescalc(amount)
                                reseller = False
                            embed.add_field(
                                name="Fees for transaction", value=f"{fees} commend/s", inline=True)
                            await interaction.send(embed=embed, ephemeral=True, view=sview(self.bot, selectgiftslot, interaction.user, 200, selectOption, customer, amount, fees, reseller))
                        else:
                            await interaction.send(embed=embed, ephemeral=True)
                else:
                    embed = nextcord.Embed(
                        title="Error", description=f"{member} is blacklisted!", color=0xff0000)
                    await interaction.send(embed=embed, ephemeral=True)
            else:
                embed = nextcord.Embed(
                    title="Error", description="You are blacklisted!", color=0xff0000)
                embed.add_field(
                    name="Reason", value=blacklistdb["reason"], inline=True)
                await interaction.send(embed=embed, ephemeral=True)

        else:

            embed = nextcord.Embed(
                title="Error", description="U cant use negative number!", color=0xff0000)
            await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="syncbalance", description="sync slots balance ",)
    async def syncbalance_command(self, interaction: Interaction,):
        if interaction.user.id == self.bot.owner_id:
            date = nextcord.utils.utcnow()

            logchannel = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
            await interaction.send(f"Processing at {date}")
            allslots = db.slotsdb.find({})
            sumcurrency = 0
            async for slot in allslots:
                if slot["enable"]:

                    pass
            await logchannel.send("Finished!")
            localvalue = await db.guildsetting.find_one({"guildid": config.SUPPORT_GUILD_ID})
            dbcurrency = localvalue["sumcurrency"]

            if dbcurrency != sumcurrency:
                pass

        else:
            await interaction.send("This command can only use administrator of bot!", ephemeral=True)
