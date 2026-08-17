"""Reseller subscription management."""

import calendar
import datetime

import asyncstdlib as a
import cooldowns
import humanfriendly
import nextcord
import pymongo
from dateutil.relativedelta import relativedelta
from nextcord import Colour, Embed, Interaction, SlashOption, User

from cogs.commend import *
from cogs.helpers import *
from utils import *

script_top = datetime.datetime.now(tz=tz)


class SubscriptionsCommands:
    """Mix into bot_commands; see cogs/commands.py."""

    @nextcord.slash_command(name="mysubscriptions", description="show my subscriptions",)
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def mysubscriptions_command(self, interaction: Interaction,
                                      member: User = SlashOption(
                                          name="user", required=False)
                                      ):
        if not member:
            member = interaction.user

        await interaction.response.defer()
        usersubdb = db.subdb.find({"ownerid": member.id})
        usavatar = get_user_avatar(member)

        count = 0
        embed = Embed(title="", color=0xd5f245)

        embed.set_author(
            name=f"{member.name} Subscriptions", icon_url=usavatar)
        async for subd in usersubdb:
            if not subd["disabled"]:
                count = count + 1
                if "guildid" in subd:
                    server = self.bot.get_guild(subd["guildid"])
                    if server:

                        datetime = subd["datetime"]

                        value = f"<t:{int(calendar.timegm(datetime.timetuple()))}:R>"
                        value2 = f"<t:{int(calendar.timegm(datetime.timetuple()))}:f>"

                        embed.add_field(
                            name=f"Server {server} - {count}", value=f"Server name: {server}\nServer id: `{server.id}`\nSub Plan: {sub_types(subd.get('subtype'))}\nSub slots: {subd['slotcount']}\nExpire: {value}\nStatus: __**Activated till {value2}**__ ")
                    else:
                        datetime = subd["datetime"]

                        value = f"<t:{int(calendar.timegm(datetime.timetuple()))}:R>"
                        value2 = f"<t:{int(calendar.timegm(datetime.timetuple()))}:f>"
                        embed.add_field(
                            name=f"Sub {count}.", value=f"ID: {subd['_id']}\nSub Plan: {sub_types(subd.get('subtype'))}\nExpire: {value}\nStatus: __**Activated till {value2}**__ ")
                else:
                    datetime = subd["datetime"]

                    value = f"<t:{int(calendar.timegm(datetime.timetuple()))}:R>"
                    value2 = f"<t:{int(calendar.timegm(datetime.timetuple()))}:f>"
                    embed.add_field(
                        name=f"Sub {count}.", value=f"ID: {subd['_id']}\nSub Plan: {sub_types(subd.get('subtype'))}\nSub Plan: {sub_types(subd.get('subtype'))}\nExpire: {value}\nStatus: __**Activated till {value2}**__ ")

            else:
                if "guildid" in subd:

                    server = self.bot.get_guild(subd["guildid"])
                    if server:
                        count = count + 1
                        embed.add_field(
                            name=f"Server {server} - {count}", value=f"Server name: {server}\nServer id: `{server.id}`\nStatus: __**License Expired**__")

                else:
                    embed.add_field(
                        name=f"Sub {count}.", value=f"ID: {subd['_id']}\nStatus: __**License Expired**__")
        if count == 0:
            embed = Embed(
                title="User dont have any Subscriptions!", color=0xd5f245)
            if member.avatar:
                embed.set_author(
                    name=f"{member.name} Subscriptions", icon_url=usavatar)
            else:
                embed.set_author(
                    name=f"{member.name} Subscriptions", icon_url=usavatar)
        await interaction.send(embed=embed)

    @nextcord.slash_command(
        name="subcheck",
        description="only bozo",

    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def subcheck_command(self, interaction: Interaction,):
        if interaction.user.id == self.bot.owner_id:
            sub = await db.subdb.find_one({"guildid": interaction.guild_id})
            subtype = sub["subtype"]
            slotcount = sub["slotcount"]
            datetimes = sub["datetime"]
            user = self.bot.get_user(sub["ownerid"])
            embed = nextcord.Embed(title="Subscription", color=0xca1c1c)
            embed.add_field(name="Sub Owner:",
                            value=f"{user.mention} - `{user.id}`", inline=False)
            embed.add_field(
                name="Expire:", value=f"<t:{int(calendar.timegm(datetimes.timetuple()))}:R>", inline=False)
            embed.add_field(name="Subscription type:",
                            value=subtype, inline=False)
            embed.add_field(name="Slots:", value=slotcount, inline=False)
            await interaction.send(embed=embed)

    @nextcord.slash_command(
        name="addsub_user",
        description="add sub for user",

    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def addsub_user_command(self,
                            interaction: Interaction,
                            user: User = SlashOption(
                                name="new-owner", 
                                description="User", 
                                ),
                            timenow: str = SlashOption(
                                name="time", 
                                description="Paste here in days",),
                            
                            plan: int = SlashOption(
                                name="plans", 
                                description="plans", 
                                choices={ "Standard_Personal": 3, }),                      
    ):
        datetime_utc = datetime.datetime.now(tz=tz)
        slotcount = 10 
        if not (interaction.user.id == self.bot.owner_id or interaction.user.id in admins):
            await interaction.send("only the bot owner can use this command")
            return
            
        await interaction.response.defer()
        
        if "m" in timenow.lower():
            months = int(timenow.lower().split("m")[0])
            delta = relativedelta(months=months)
            tim2 = datetime_utc  + delta
            timenow = f'{months} months'
        else:
            timenow = humanfriendly.parse_timespan(timenow)
            delta = datetime.timedelta(seconds=timenow)
            tim2 = datetime_utc  + delta
            
        subdbs = await db.subdb.find_one({"ownerid": user.id,"guildid":None})
        if subdbs:
            olddatetime: datetime.datetime = subdbs["datetime"]
            if not(olddatetime == 0 or  olddatetime.replace(tzinfo=datetime.timezone.utc) < datetime_utc):
                tim2 = olddatetime + delta
                
                
            cfg = {
                "datetime": tim2,
                "subtype": plan,
                "slotcount": slotcount,
                "disabled": False,
                "alert": False,
                "pay": True
            }

            
            
            exdb = await db.subdb.find_one_and_update(
                {"_id": subdbs["_id"]}, {"$set": cfg}, return_document=pymongo.ReturnDocument.AFTER
            )
                
                
        else:
            exdb = {
                "guildid": None,
                "datetime": tim2,
                "slotcount": slotcount,
                "subtype": plan,
                "disabled": False,
                "alert": False,
                "pay": True,
                "ownerid":  user.id 
            }
            await db.subdb.insert_one(exdb)
        delta_dict = {
            "years": delta.years,
            "months": delta.months,
            "days": delta.days,
            "hours": delta.hours,
            "minutes": delta.minutes,
            "seconds": delta.seconds,
        }
            
        await db.sellsds.insert_one({

            "datetime": datetime_utc,
            "sellerid":interaction.user.id,
            "customerid": user.id,
            "delta":delta_dict,
            "expire_new":tim2,
            "type": "addsub_user"

        })
        
        embed = nextcord.Embed(
            title="Activated/Extended resell subscription",
            color=Colour.gold(),
            timestamp=timestamp
        )
        embed.add_field(name="Subscription type:", value=f"{sub_types(plan)}", inline=False)
        
        embed.add_field(name="Owner:", value=f"{user} - `{user.id}`", inline=False)
        embed.add_field(name="Extended for:", value=f"{timenow}", inline=False)
        embed.add_field(name="Expire at:", value=f"<t:{int(calendar.timegm(tim2.timetuple()))}:f>", inline=False)
        embed.add_field(name="Rate limit", value=f"{slotcount} users", inline=False)

        await interaction.send(embed=embed)

        if await can_dm_user(user):
            await user.dm_channel.send(embed=embed)

        if await can_dm_user(interaction.user):
            await interaction.user.dm_channel.send(embed=embed)

        owner = self.bot.get_user(OWNERID)
        await owner.send(embed=embed)

    @nextcord.slash_command(
        name="addsub",
        description="add sub for guild",
    )
    @cooldowns.cooldown(1, 15, bucket=cooldowns.SlashBucket.author)
    async def addsub_command(self,
                            interaction: Interaction,
                            guildid: str = SlashOption(
                                name="guildid", description="Paste here guild id"),
                            timenow: str = SlashOption(
                                name="time", description="Paste here in days"),
                            number: int = SlashOption(
                                name="number", description="int"),
                            plan: int = SlashOption(name="plans", description="plans", choices={
                                "Free": 4, "Standard_Personal": 3, "Standard_Server": 2, "Premium": 1, "Local": 0}),
                            user: User = SlashOption(
                                name="buyer", description="User", required=True),
                            ):
        datetime_utc = datetime.datetime.now(tz=tz)
        guild = self.bot.get_guild(int(guildid))

        if not guild:
            await interaction.send("This guild id does not exist.", ephemeral=True)
            return

        if interaction.user.id != self.bot.owner_id and interaction.user.id not in admins:
            await interaction.send("This command can only be used by the bot owner or admins.")
            return

        if plan == 3:
            await interaction.send("You need to use command addsub_user for personal sub.")
            return

        await interaction.response.defer()

        # Calculate tim2 based on timenow
        if "m" in timenow.lower():
            months = int(timenow.lower().split("m")[0])
            delta = relativedelta(months=months)
            print(delta)
            tim2 = datetime_utc + delta 
            timenow = f'{months} months'
        else:
            timenow = humanfriendly.parse_timespan(timenow)
            delta = datetime.timedelta(seconds=timenow)
            tim2 = datetime_utc + delta
            
        
        subdbs = await db.subdb.find_one({"guildid": guild.id})

        

        if subdbs:
            olddatetime: datetime.datetime = subdbs["datetime"]
            if olddatetime == 0 or  olddatetime.replace(tzinfo=datetime.timezone.utc) <datetime_utc:
                olddatetime = datetime_utc
            else:
                tim2 = olddatetime + delta
                
                
            cfg = {
                "datetime": tim2,
                "subtype": plan,
                "slotcount": number,
                "disabled": False,
                "alert": False,
                "pay": True
            }

            if user:
                cfg["ownerid"] = user.id
            
            exdb = await db.subdb.find_one_and_update(
                {"_id": subdbs["_id"]}, {"$set": cfg}, return_document=pymongo.ReturnDocument.AFTER
            )
            
                
        else:
            exdb = {
                "guildid": guild.id,
                "datetime": tim2,
                "slotcount": number,
                "subtype": plan,
                "disabled": False,
                "alert": False,
                "pay": True,
                "ownerid": guild.owner_id if not user else user.id
            }
            await db.subdb.insert_one(exdb)

        if "ownerid" in exdb:
            await db.usersdb.update_one({'userid': exdb["ownerid"]}, {'$set': {'reseller': True}})
        else:
            await interaction.channel.send(f"ownerid is none in {exdb}")
            
        delta_dict = {
            "years": delta.years,
            "months": delta.months,
            "days": delta.days,
            "hours": delta.hours,
            "minutes": delta.minutes,
            "seconds": delta.seconds,
        }
            
        await db.sellsds.insert_one({

            "datetime": datetime_utc,
            "sellerid":interaction.user.id,
            "guildid":guild.id,
            "customerid": user.id,
            "delta":delta_dict,
            "expire_new":tim2,
            "type": "addsub"

        })

        owner = user

        embed = nextcord.Embed(
            title="Activated/Extended resell subscription",
            color=Colour.gold(),
            timestamp=timestamp
        )
        embed.add_field(name="Subscription type:", value=f"{sub_types(plan)}", inline=False)
        embed.add_field(name="Guild:", value=f"{guild} - `{guild.id}`", inline=False)
        embed.add_field(name="Owner:", value=f"{owner} - `{owner.id}`", inline=False)
        embed.add_field(name="Extended for:", value=f"{timenow}", inline=False)
        embed.add_field(name="Expire at:", value=f"<t:{int(calendar.timegm(tim2.timetuple()))}:f>", inline=False)
        embed.add_field(name="Rate limit", value=f"{number} users", inline=False)

        await interaction.send(embed=embed)

        if await can_dm_user(owner):
            await owner.dm_channel.send(embed=embed)

        if await can_dm_user(interaction.user):
            await interaction.user.dm_channel.send(embed=embed)

        owner = self.bot.get_user(OWNERID)
        await owner.send(embed=embed)

    @nextcord.slash_command(
        name="active_resell",


    )
    async def active_resell(self,
                            interaction: Interaction):
        if interaction.user.id == self.bot.owner_id:
            await interaction.response.defer()
            embed = nextcord.Embed(title="Active resell", description="",
                                   color=nextcord.Colour.blurple(), timestamp=timestamp,)
            resellers = db.subdb.find({"disabled": False}).sort(
                [("pay", pymongo.ASCENDING), ("subtype", pymongo.ASCENDING)])
            premium = ""
            trys = ""
            async for id, sub in a.enumerate(resellers):
                if "guildid" in sub and sub["guildid"] is not None:
                    guild = self.bot.get_guild(sub["guildid"])
                    if sub["pay"]:
                        premium += f"{id}. **{guild}** - {subdecoder[sub['subtype']]} - <t:{ int(calendar.timegm(sub['datetime'].timetuple())) if 'datetime' in sub else None }:f>\n"
                    else:
                        trys += f"{id}. **{guild}** - {subdecoder[sub['subtype']]} - <t:{ int(calendar.timegm(sub['datetime'].timetuple())) if 'datetime' in sub else None }:f>\n"
                else:
                    premium += f"{id}. **{sub['ownerid']}** - {subdecoder[sub['subtype']]} - <t:{ int(calendar.timegm(sub['datetime'].timetuple())) if 'datetime' in sub else None }:f>\n"

            embed.add_field(name="Premium", value=premium, inline=False)
            embed.add_field(name="Trial", value=trys, inline=False)
            await interaction.send(embed=embed)
