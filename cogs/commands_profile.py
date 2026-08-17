"""Profile, balance display and the graphs that go with them."""

import datetime
import io
from itertools import cycle

import asyncstdlib as a
import cooldowns
import matplotlib.dates as mdates
import nextcord
import pymongo
from matplotlib import dates as mpl_dates
from matplotlib import pyplot as plt
from nextcord import Colour, Embed, Interaction, Member, SlashOption, User

import config
from cogs.commands_views import profile, showslotsgraphs

# (nothing needed from cogs.commend)
# (nothing needed from cogs.helpers)
from utils import (
    admins,
    db,
    delete_autodelete,
    get_user_avatar,
    logger,
    millify,
    prettify,
    sview,
    timestamp,
    tz,
)

script_top = datetime.datetime.now(tz=tz)


class ProfileCommands:
    """Mix into bot_commands; see cogs/commands.py."""

    @nextcord.slash_command(
        name="profile",
        description="Profile command",


    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def profile_command(self, interaction: Interaction,
                              member: nextcord.User = SlashOption(name="user", required=False),):
        await interaction.response.defer()
        if not member:
            member = interaction.user
        embed = Embed(timestamp=timestamp)
        userdb = await db.usersdb.find_one({"userid": member.id})
        resellerdb = await db.subdb.find_one({"ownerid": member.id, "disabled": False, "pay": True})
        bldb = await db.blacklistdb.find_one({"userid": member.id})
        slotdb = await db.slotsdb.find_one({"admins":{ "$in":[member.id] }})
        status = "Member"
        if userdb:
            status = "Customer"
        if resellerdb:
            status = "Reseller"
        if slotdb:
            status = "Slot Admin"
        if bldb:
            status = "Blacklisted"
        if member.id == self.bot.owner_id:
            status = "Owner"

        aurl = get_user_avatar(member)
        embed.set_author(name=member, url=aurl, icon_url=aurl)
        embed.set_thumbnail(url=aurl)
        embed.add_field(name="Role", value=f"`{status}`", inline=False)
        embed.set_footer(text=config.BRAND_FOOTER,
                         icon_url=config.BRAND_LOGO_URL)
        SelectOption = []

        if userdb and bldb is None or userdb and interaction.user.id == self.bot.owner_id:

            SelectOption.append(nextcord.SelectOption(
                label="Transactions History", emoji="🗃️", value="1"))
            embed.add_field(name="✰ Points",
                            value=f"`✰ {int(userdb['points'])}`", inline=False)
            baldbs = await db.balancesdb.find({"userid": member.id}).to_list(None)
            slotsdb = await db.slotsdb.find({}).to_list(None)
            graph, ballist = await self.multigrap(member, baldbs, slotsdb)
            embed.add_field(name="Current Balance", value=ballist)
            embed.set_image(url="attachment://transactions.png")
        else:
            graph = None
        if slotdb or self.bot.owner_id == interaction.user.id:
            SelectOption.append(nextcord.SelectOption(
                label="Slot Stats", emoji="🗃️", value="2"))
        view = sview(self.bot, profile, interaction.user,
                     180, SelectOption, member)

        if graph:
            await interaction.send(file=graph, embed=embed, view=view)
        elif len(SelectOption) != 0:

            await interaction.send(embed=embed, view=view)
        else:
            await interaction.send(embed=embed)

    @nextcord.user_command(name="profile")
    async def profile_user_command(self, interaction: Interaction, member: Member):
        await interaction.response.defer(ephemeral=False)

        embed = Embed(timestamp=timestamp)
        userdb = await db.usersdb.find_one({"userid": member.id})
        resellerdb = await db.subdb.find_one({"ownerid": member.id, "disabled": False, "pay": True})
        bldb = await db.blacklistdb.find_one({"userid": member.id})
        slotdb = await db.slotsdb.find_one({"admins": member.id})
        status = "Member"
        if userdb:
            status = "Customer"
        if resellerdb:
            status = "Reseller"
        if slotdb:
            status = "Slot Admin"
        if bldb:
            status = "Blacklisted"
        if member.id == self.bot.owner_id:
            status = "Owner"

        aurl = get_user_avatar(member)
        embed.set_author(name=member, url=aurl, icon_url=aurl)
        embed.set_thumbnail(url=aurl)
        embed.add_field(name="Role", value=f"`{status}`", inline=False)
        embed.set_footer(text=config.BRAND_FOOTER,
                         icon_url=config.BRAND_LOGO_URL)
        SelectOption = []

        if userdb and bldb is None or userdb and interaction.user.id == self.bot.owner_id:

            SelectOption.append(nextcord.SelectOption(
                label="Transactions History", emoji="🗃️", value="1"))
            embed.add_field(name="✰ Points",
                            value=f"`✰ {int(userdb['points'])}`", inline=False)
            baldbs = await db.balancesdb.find({"userid": member.id}).to_list(None)
            slotsdb = await db.slotsdb.find({}).to_list(None)
            graph, ballist = await self.multigrap(member, baldbs, slotsdb)
            embed.add_field(name="Current Balance", value=ballist)
            embed.set_image(url="attachment://transactions.png")
        else:
            graph = None
        if slotdb or self.bot.owner_id == interaction.user.id:
            SelectOption.append(nextcord.SelectOption(
                label="Slot Stats", emoji="🗃️", value="2"))
        view = sview(self.bot, profile, interaction.user,
                     180, SelectOption, member)

        if graph:
            await interaction.send(file=graph, embed=embed, view=view)
        elif len(SelectOption) != 0:

            await interaction.send(embed=embed, view=view)
        else:
            await interaction.send(embed=embed)

    async def multigrap(self, member: Member, baldbs: list, slotsdb: list) -> nextcord.File and str:
        data_stream = io.BytesIO()
        colors = cycle(["#08F7FE", "#C27C0E", '#00FFFF', '#0000FF', '#DC143C',
                       '#A52A2A', '#7FFF00', '#8A2BE2', '#000000', '#D2691E'])
        alldates = []
        slots_names = []
        balances = ""
        balcount = 0
        plt.style.use("dark_background")


        for baldb in baldbs:
            color = next(colors)
            slotdb = list(
                filter(lambda i: i['_id'] == baldb["slot_id"], slotsdb))[0]
            balances += f"**{baldb['amount']}** commends from **{slotdb['name']}** slot\n"
            balcount += baldb["amount"]
            glist = db.sellsds.find({"$or": [{"customerid": member.id, "slot_id": baldb["slot_id"]}, {
                                    "gifterid": member.id, "slot_id": baldb["slot_id"]}]}).sort("_id")

            dates = []
            values = []

            async for sell in glist:

                if "gifterid" in sell and sell["gifterid"] == member.id:

                    values.append(sell["g_new-amount"])
                    dates.append(sell["datetime"])
                if sell["customerid"] == member.id:
                    if "u_new-amount" in sell:
                        values.append(sell["u_new-amount"])
                        dates.append(sell["datetime"])

            dates.append(datetime.datetime.now(tz=tz))
            values.append(baldb["amount"])
            alldates = dates

            plt.plot_date(dates, values,
                          fmt="o-", linewidth=2,
                          tz=tz,

                          color=color)
            slots_names.append(slotdb["name"])

        firstdate: datetime.datetime = alldates[0]
        firstdate = firstdate.replace(tzinfo=None)
        lastdate: datetime.datetime = alldates[-1]
        lastdate = lastdate.replace(tzinfo=None)

        plt.grid(color='#2A3459')

        plt.xlabel("Dates")
        plt.ylabel("Balance")
        plt.gcf().autofmt_xdate()
        plt.legend(slots_names)

        if len(alldates) > 7:
            date_format = mpl_dates.DateFormatter("%d %b %Y")
            bettwene = (lastdate - firstdate).total_seconds()

            if 7 < len(values):

                if bettwene <= 2629743:

                    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
                elif bettwene <= 7889231:
                    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
                elif bettwene <= 94670777:
                    plt.gca().xaxis.set_major_locator(mdates.YearLocator())
                else:
                    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))

        else:
            date_format = mpl_dates.DateFormatter('%Y-%m-%d %H %Z')

        plt.gca().xaxis.set_major_formatter(date_format)
        plt.tight_layout()

        plt.savefig(data_stream, format='png', bbox_inches="tight", dpi=80)

        data_stream.seek(0)
        plt.clf()
        chart = nextcord.File(data_stream, filename="transactions.png")
        balances += f"\nTotal balance: **{balcount}** commends"
        return chart, balances

    @nextcord.slash_command(
        name="userinfo",
        description="User info",


    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def userinfo_command(self, interaction: Interaction,
                               member: nextcord.User = SlashOption(
                                   name="user", description="User", required=False),
                               ):
        await interaction.response.defer(ephemeral=False)
        if member is None:
            member = interaction.user
        await self.userinfo(member, interaction)

    async def userinfo(self, member: User, interaction: Interaction, msg: nextcord.Message = None):
        embed = Embed(timestamp=timestamp)
        userdb = await db.usersdb.find_one({"userid": member.id})
        resellerdb = await db.subdb.find_one({"ownerid": member.id, "disabled": False, "pay": True})
        bldb = await db.blacklistdb.find_one({"userid": member.id})
        status = "Member"
        if userdb:
            status = "Customer"
        if resellerdb:
            status = "Reseller"
        if bldb:
            status = "Blacklisted"
        if member.id == self.bot.owner_id:
            status = "Owner"

        aurl = get_user_avatar(member)
        embed.set_author(name=member, url=aurl, icon_url=aurl)
        embed.set_thumbnail(url=aurl)
        embed.add_field(name="Role", value=f"`{status}`", inline=False)
        embed.set_footer(text=config.BRAND_FOOTER,
                         icon_url=config.BRAND_LOGO_URL)
        if userdb and bldb is None:
            SelectOption = []
            embed.add_field(name="✰ Points",
                            value=f"`✰ {int(userdb['points'])}`", inline=False)
            baldbs = db.balancesdb.find({"userid": member.id})
            slots = await db.slotsdb.find({}).to_list(None)
            balance = 0
            emojilist = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪"]
            lastnum = None
            async for id, baldb in a.enumerate(baldbs):
                slotdb = list(
                    filter(lambda i: i['_id'] == baldb["slot_id"], slots))[0]
                balance += baldb["amount"]
                SelectOption.append(nextcord.SelectOption(
                    label=f"{slotdb['name']} Slot", emoji=emojilist[id], value=baldb["slot_id"]))
                lastnum = id

            if lastnum:
                embed.add_field(
                    name="Balance", value=f"`{balance} commends`", inline=False)
                evb, view = embed, sview(
                    self.bot, showslotsgraphs, interaction.user, 130, SelectOption, member)

            else:

                evb = embed
                view = nextcord.ui.View()

        else:
            evb = embed
        if msg:
            await msg.edit(embed=evb, view=view, files=[])

        else:
            await interaction.send(embed=evb, view=view)

    @staticmethod
    async def getgraph(member: User, slot_id, baldb):
        data_stream = io.BytesIO()

        glist = db.sellsds.find({"$or": [{"gifterid": member.id}, {"customerid": member.id}, {
                                "sellerid": member.id}]}).sort("_id", pymongo.DESCENDING)

        dates = []
        values = []

        async for sell in glist:
            dates.append(sell["datetime"])
            if "g_new-amount" in sell:
                values.append(sell["g_new-amount"])
            else:
                if "u_new-amount" in sell:
                    values.append(sell["u_new-amount"])
                else:
                    values.append(0)

        dates.append(datetime.datetime.now(tz=tz))
        values.append(baldb["amount"])
        plt.style.use("dark_background")

        colors = "#08F7FE"
        firstdate: datetime.datetime = dates[0]
        firstdate = firstdate.replace(tzinfo=None)
        lastdate: datetime.datetime = dates[-1]
        lastdate = lastdate.replace(tzinfo=None)

        if len(dates) > 7:
            date_format = mpl_dates.DateFormatter("%d %b %Y")
            bettwene = (lastdate - firstdate).total_seconds()

            if 7 < len(values):

                if bettwene <= 2629743:

                    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
                elif bettwene <= 7889231:
                    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
                else:
                    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))

        else:
            date_format = mpl_dates.DateFormatter('%Y-%m-%d %H %Z')

        plt.plot_date(dates, values,
                      fmt="o-", linewidth=2,
                      tz=tz,

                      color=colors)
        plt.fill_between(dates, values,
                         color=colors,
                         alpha=0.1)
        plt.grid(color='#2A3459')
        plt.xlabel("Date")
        plt.ylabel("Balance")
        plt.gcf().autofmt_xdate()

        plt.gca().xaxis.set_major_formatter(date_format)
        plt.tight_layout()

        plt.savefig(data_stream, format='png', bbox_inches="tight", dpi=80)

        data_stream.seek(0)
        plt.clf()
        chart = nextcord.File(data_stream, filename="transactions.png")

        return chart

    @nextcord.slash_command(
        name="balance",
        description="User balance",


    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def balance_command(self, interaction: Interaction,
                              member: nextcord.Member = SlashOption(
                                  name="user", description="User", required=False),
                              human_readable: bool = SlashOption(
                                  name="human_readable", required=False),
                              ):
        admin =False
        try:
            await interaction.response.defer(ephemeral=False)
        except nextcord.errors.NotFound:
            await interaction.channel.send(f"Sorry {interaction.user}, the interaction has timed out. Please try again(Please contact bot dev if you see this message many times).")
            logger.error(
                f"Error with interaction {interaction.user.id} at balance command")
        else:
            
            await delete_autodelete(interaction.channel)
            if member is None:
                member = interaction.user
            else:
                if interaction.user.id in admins:
                    admin = True    
                
                    

            if human_readable is None:
                human_readable = True

            balancedb = db.balancesdb.find({"userid": member.id})
            description = ""
            run = 0

            vf = False
            bldb = await db.blacklistdb.find_one({"userid": member.id})

            htslist = await db.slotsdb.find({}).to_list(length=None)

            allbalance = 0
            async for balanced in balancedb:
                

                slotdb = list(
                    filter(lambda i: i['_id'] == balanced["slot_id"], htslist))
                if len(slotdb) != 0:
                    run += 1
                    slotdb = slotdb[0]

                    amount = int(balanced["amount"])
                    allbalance = int(allbalance + amount)

                    description += f"Avaliable : **{millify(amount)if human_readable else prettify(amount)}** | On Hold : **{millify(int(balanced['onhold']))if human_readable else prettify(int(balanced['onhold']))}** commends by **{str(slotdb['name'])}** slot\n"
            if not bldb:
                description += f"\n**Total balance:** **{millify(allbalance)if human_readable else prettify(allbalance)}** commends"
            else:
                description += "\n**Total balance:** **0** commends(banned)"
            color = 0xffcccb
            if bldb:
                color = nextcord.Color.dark_red()
            elif allbalance >= 1000:
                color = 0x0a8f82

            elif allbalance >= 750:
                color = 0x008000

            elif allbalance >= 500:
                color = 0x90ee90

            elif allbalance >= 250:
                color = 0xFFA500
            elif allbalance >= 100:
                color = 0xFFD580

            if run == 0:

                if bldb:
                    description = description + \
                        f"\nYour balance was **permanently removed** because appeal period has **expired**\nBan reason: {bldb['reason']}"
                    color = Colour.red()

                else:

                    color = 0xffcccb

            embed = nextcord.Embed(
                title=f"User {member.name} balance:", description=description, color=color)
            dbp = await db.usersdb.find_one({"userid": member.id})
            if dbp:
                point = int(dbp['points'])
                embed.add_field(
                    name="Your Star Points", value=f"**{millify(point)if human_readable else prettify(point)}** points", inline=False)
            if admin:
                
                embed.add_field(name="Multal servers",value="\n".join(i.name for i in member.mutual_guilds))
            embed.set_footer(text=config.BRAND_FOOTER,
                             icon_url=config.BRAND_LOGO_URL)
            await interaction.send(embed=embed)
            """if userdb:=await db.usersdb.find_one({"userid":interaction.user.id,}):
                if userdb["tr212_promo"] % 2 == 0:
                    try:
                        await interaction.user.send(embed=promotion_embed(),view=promo_view())
                    except Exception:
                        logger.exception("balance exeption")  
                    else:
                        await db.usersdb.update_one({'_id': userdb["_id"]}, {'$inc': {'tr212_promo': 1}})
                else:
                    await db.usersdb.update_one({'_id': userdb["_id"]}, {'$inc': {'tr212_promo': 1}})  
            else:
                try:
                    await interaction.user.send(embed=promotion_embed(),view=promo_view())
                except Exception:
                    logger.exception("balance exeption ex")      """

    @nextcord.user_command(name="balance")
    async def balance_user_command(self, interaction: nextcord.Interaction, member: nextcord.Member):

        human_readable = True

        balancedb = db.balancesdb.find({"userid": member.id})
        description = ""
        run = 0

        vf = False
        bldb = await db.blacklistdb.find_one({"userid": member.id})

        htslist = await db.slotsdb.find({}).to_list(length=None)

        allbalance = 0
        async for balanced in balancedb:
            run += 1

            slotdb = list(
                filter(lambda i: i['_id'] == balanced["slot_id"], htslist))
            slotdb = slotdb[0]

            amount = int(balanced["amount"])
            allbalance = int(allbalance + amount)

            description += f"Avaliable : **{millify(amount)if human_readable else prettify(amount)}** | On Hold : **{millify(int(balanced['onhold']))if human_readable else prettify(int(balanced['onhold']))}** commends by **{str(slotdb['name'])}** slot\n"
        if not bldb:
            description += f"\n**Total balance:** **{millify(allbalance)if human_readable else prettify(allbalance)}** commends"
        else:
            description += "\n**Total balance:** **0** commends(banned)"
        color = 0xffcccb
        if bldb:
            color = nextcord.Color.dark_red()
        elif allbalance >= 1000:
            color = 0x0a8f82

        elif allbalance >= 750:
            color = 0x008000

        elif allbalance >= 500:
            color = 0x90ee90

        elif allbalance >= 250:
            color = 0xFFA500
        elif allbalance >= 100:
            color = 0xFFD580

        if run == 0:

            if bldb:
                description = description + \
                    f"\nYour balance was **permanently removed** because appeal period has **expired**\nBan reason: {bldb['reason']}"
                color = Colour.red()

            else:

                color = 0xffcccb

        embed = nextcord.Embed(
            title=f"User {member.name} balance:", description=description, color=color)
        dbp = await db.usersdb.find_one({"userid": member.id})
        if dbp:
            point = int(dbp['points'])
            embed.add_field(name="Your Star Points",
                            value=f"**{millify(point)if human_readable else prettify(point)}** points", inline=False)
        embed.set_footer(text=config.BRAND_FOOTER,
                         icon_url=config.BRAND_LOGO_URL)
        await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(
        name="adminbalance",
        description="aUser balance",

    )
    async def abalance_command(
        self,
        interaction: Interaction,
        user: nextcord.User = SlashOption(
            name="user", description="whose balance to look up"
        ),
    ):
        # The original took no argument and always reported one hardcoded
        # account's balance, which made the command useless to anyone else.
        if interaction.user.id != self.bot.owner_id and interaction.user.id not in config.ADMIN_IDS:
            return await interaction.send("only bot staff can use this command", ephemeral=True)

        balancedb = await db.balancesdb.find_one({"userid": user.id})
        amount = balancedb["amount"] if balancedb else 0

        color = 0xBC4E4E
        for threshold, shade in (
            (1000, 0x0A8F82),
            (750, 0x008000),
            (500, 0x90EE90),
            (250, 0xFFA500),
            (100, 0xFFD580),
            (1, 0xFFCCCB),
        ):
            if amount >= threshold:
                color = shade
                break

        embed = nextcord.Embed(
            title=f"Balance of {user}", description=f"{amount} commends", color=color
        )
        embed.set_footer(text=config.BRAND_FOOTER, icon_url=config.BRAND_LOGO_URL)
        await interaction.send(embed=embed)

    @nextcord.slash_command(
        name="showprbalance",
        description="show stats",
        guild_ids=[config.SUPPORT_GUILD_ID]

    )
    async def showprbalance_command(self,
                                    interaction: Interaction,

                                    ):
        if interaction.user.id == self.bot.owner_id:
            balancesdb = db.balancesdb.find({})
            async for userdb in balancesdb:
                amount = userdb["amount"]
                if not amount == 0:
                    member = self.bot.get_user(userdb["userid"])
                    if member:
                        embed = nextcord.Embed(
                            title=f"User {member}  balance:", description=f"{amount} commends", )
                        embed.add_field(name="user infos",
                                        value=member.mention)
                        await interaction.channel.send(embed=embed)

        else:
            await interaction.send("This command can only use administrator of bot!", ephemeral=True)
