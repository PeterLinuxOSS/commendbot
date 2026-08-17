"""The commend session lifecycle: queueing, progress updates, completion."""

import calendar
import datetime
import random

import asyncstdlib as a
import nextcord
import pymongo.collection
from nextcord import Colour, TextChannel
from steam_web_api import Steam

import config
from cogs.commend import Confirm
from cogs.commend_menu_views import (
    Select_StopCommending,
    balance_menu,
    language_header,
    start_commend,
)
from cogs.helpers import helpers
from utils import (
    best_server,
    cprint,
    db,
    embed_error,
    get_datetime_utc,
    get_lang,
    howitworksemb,
    logger,
    logo,
    pview,
    support_server_link,
    sview,
    tz,
)

steam = Steam(config.STEAM_API_KEY)


class MenuLifecycleCommands:
    """Mix into commend_menu; see cogs/commend_menu.py."""

    async def commend_task(self,interaction: nextcord.Interaction ,lang,slotid, steamID64,amount, editmsg=None,userdb:dict=None ,raise_error=None,**args):
        datetime_utc = get_datetime_utc()
        if not userdb:
            userdb = await db.usersdb.find_one({"userid":interaction.user.id})
        if userdb.get("free",False):
            test = await db.usersdb.find_one({
                                "accs": { "$in": [int(steamID64)] },
                                "userid": { "$ne": interaction.user.id }
                            })
            if test:
                await self.addtoblacklist(interaction,interaction.user,self.bot.user,interaction.guild,f"Suspicious-Activity {steamID64}")
                return
                
            
        balancedb = await db.balancesdb.find_one({"userid":interaction.user.id,"slot_id":slotid})
        oldamount = balancedb["amount"]
        newamount = oldamount - amount
        if editmsg is None:
            editmsg = interaction.message.edit
        if raise_error is None:
            raise_error = interaction.send
        
        if newamount < 0:
            embed= embed_error("Balance Error",lang["error9"])
                
            await raise_error(embed=embed ,content="")# view=Check_show_cbprices_header(self.bot)
        else:

                subdbsr = await db.subdb.find_one({"guildid":interaction.guild_id})
            
                if not subdbsr["disabled"]:
                    guilduser = await db.serverusers.count_documents({"guildid":interaction.guild_id})
                    slotcount = int(subdbsr["slotcount"])

                    if  slotcount - guilduser >= 0:
                        
                        
                        
                        slotdb = await db.slotsdb.find_one({"_id":slotid})      
                        if slotdb["enable"]:
                            if amount >=  slotdb["min_commends"]:   
                                
                                resellerdb = await db.subdb.find_one({"ownerid":interaction.user.id,"disabled":False,"pay":True})    
                                if not resellerdb:
                                    if "accs" in userdb and len(userdb["accs"]) >= 5  :
                                        if steamID64 not in userdb["accs"]:
                                            faccs = '\n'.join(str(acc) for acc in userdb['accs'])
                                            
                                            embed = nextcord.Embed(
                                                title=lang["on_error"],
                                                description=(
                                                    f"You are being rate limited, so you can't commend this Steam profile.\n"
                                                    f"Please commend on one of these Steam accounts:\n{faccs}\n"
                                                    f"To reset the rate limit, you need to create a ticket on the CommendBot support server or you can buy a resell sub:\n"
                                                    f"{support_server_link}"
                                                ),
                                                color=0xe74c3c
                                            )
                                            
                                            embed.set_footer(text="004548")
                                            await interaction.send( embed=embed,ephemeral=True)
                                            return    
                                
                                
                                
                                if  resellerdb and "max_rcommends" in slotdb and slotdb["max_rcommends"] :
                                    max_commends = (slotdb["max_rcommends"] if slotdb["max_rcommends"] != 0 else 9999999999) 
                                else:
                                    max_commends = (slotdb["max_commends"] if slotdb["max_commends"] != 0 else 9999999999) 
                                if amount <= max_commends: 
                                    
                                    
                                    gvalue = slotdb["currency"]  - amount
                                    if  gvalue >= 0:
                                        
                                        if  resellerdb and "max_daily_rcommends" in slotdb and slotdb["max_daily_rcommends"] :
                                            max_daily_commends = (slotdb["max_daily_rcommends"] if slotdb["max_daily_rcommends"] != 0 else 99999999)
                                        else:
                                            max_daily_commends = (slotdb["max_daily_commends"] if slotdb["max_daily_commends"] != 0 else 99999999)

                                        today_used = balancedb["today_used"] +amount
                                        if today_used <= max_daily_commends:
                                                     
                                            
                                                blacklist2 = await db.blacklistdb.find_one({"steamID64":steamID64})
                                                if blacklist2 is None:
                                                    commenddb = await db.serverusers.find_one({"steamID64":steamID64})
                                                    
                                                    if commenddb is None :
                                                        tdb = await db.serverusers.count_documents({"channelid":interaction.channel.id})
                                                        if tdb <= 3 or interaction.user.id == self.bot.owner_id:
                                                            view = sview(self.bot,Confirm,interaction.user,None, lang["howitworkis-button"])
                                                            
                                                            
                                                            if tdb == 0 or resellerdb:
                                                                start = False
                                                                if resellerdb and tdb !=0:
                                                                    servercheck = await db.serverusers.find({"channelid":interaction.channel.id,"status":"w8connect"}).to_list(None)
                                                                    if len(servercheck) == 0:
                                                                       start = True 
                                                                    else:
                                                                        start = False
                                                                        duser = servercheck[0]
                                                                        
                                                                            
                                                                else:
                                                                    
                                                                    start = True 
                                                                if start:
                                                                     
                                                                    getserver = best_server

                                                                    
                                                                    slotdb = await db.slotsdb.find_one_and_update({"_id":slotid}, {"$inc": {"currency": -amount}},return_document = pymongo.ReturnDocument.AFTER)       
                                                                    
                                                                    embed = howitworksemb(lang,getserver,steamID64)
                                                                    embed.title = f"Session - {steamID64} "
                                                                    msg : nextcord.Message=await editmsg(embed=embed, view=view)
                                                                    await db.balancesdb.update_one({"userid":interaction.user.id},{"$inc": {"onhold": +amount,"amount":-amount}})
                                                                    await db.serverusers.insert_one({"userid":interaction.user.id, "channelid":interaction.channel.id, "amount": amount, "steamID64": steamID64, "status":"w8connect", "pendingmany":0, "commended":False,"lastup":datetime_utc, "guildsid": interaction.guild_id, "msgid":msg.id, "slot_id":slotid, "howitworkis-button":lang["howitworkis-button"],"button":True, "chunk":"#0","chunk-info":"[0/0]","actualamount":0, "lastpending":0,"auto":False,"old_balance":oldamount})
                                                                    return   
                                                                    
                                                                    
                                                                else:
                                                                    embed=nextcord.Embed(title="Multi-commend error", description=f"you cant start commending when we waiting u connect to server, first connect with {duser['steamID64']} and then can start next!", color=0xe74c3c)
                                                                    await raise_error(embed=embed,content="",**args)
                                                            else:
                                                                error_code = "error2"
                                                                embed=nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
                                                                embed.set_footer(text=error_code)
                                                                await raise_error(embed=embed,content="",**args)
                                                                
                                                        else:
                                                            error_code = "max_limit"
                                                            embed=nextcord.Embed(title=lang["on_error"], description="You reach maximal limit of multicommending!", color=0xe74c3c)
                                                            embed.set_footer(text=error_code)
                                                            await raise_error(embed=embed,content="",**args)
                                                    else:
                                                        error_code = "error3"
                                                        embed=nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
                                                        embed.set_footer(text=error_code)
                                                        await raise_error(embed=embed,content="",**args)    
                                                else:       
                                                    embed=nextcord.Embed(title=lang["on_error"], description=f"This steam account is blacklisted!\nTo unban this profile [join]({support_server_link}) in to support server {support_server_link}", color=0xe74c3c)
                                                    embed.add_field(name="Ban Reason", value=blacklist2["reason"], inline=True)
                                                    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
                                                    await raise_error(embed=embed,content="",**args)
                                        else:
                                            error_code = "error14"
                                            msg =  lang[error_code]
                                            
                                            msg = msg.replace("0c", str(amount))
                                            calc = slotdb["max_daily_commends"] -balancedb["today_used"]
                                            msg = msg.replace("0u",str(calc))
                                            msg = msg.replace("0s",str(slotdb["max_daily_commends"]))
                                            embed=nextcord.Embed(title=lang["on_error"], description=msg, color=0xFFA500)
                                            embed.set_footer(text=error_code)
                                            await raise_error(embed=embed,content="",**args)

                                    else:
                                        error_code = "error13"
                                        msg : str= lang[error_code]
                                        amount = str(amount)
                                        msg = msg.replace("0c", amount)
                                        lsh =  str(slotdb["currency"])
                                        msg = msg.replace("0s",lsh)
                                        trs = (datetime.datetime(datetime_utc.year, datetime_utc.month, datetime_utc.day, 0,1,0,0,tzinfo=tz) + datetime.timedelta(days=1))
                                        msg = msg.replace("00:00 UTC",f"<t:{int(trs.timestamp())}:R>")
                                        embed=nextcord.Embed(title=lang["on_error"], description=msg, color=0xFFA500)
                                        embed.set_footer(text=error_code)
                                        await raise_error(embed=embed,content="",**args)
                                else:
                                    error_code = "error5"
                                    embed=nextcord.Embed(title=lang["on_error"], description=(str(lang[error_code]).replace("0x",str(max_commends))), color=0xe74c3c)
                                    embed.set_footer(text=error_code)
                                    await raise_error(embed=embed,content="",**args)# view=Check_show_cbprices_header(self.bot)

                                

                            else:   
                    

                                embed=nextcord.Embed(title=lang["on_error"], description=f"You cant use less than {slotdb['min_commends']} commends", color=0xe74c3c)
                                await raise_error(embed=embed,content="",**args) 
                        else:
                                embed=nextcord.Embed(title=lang["on_error"], description="This Slot is disabled", color=0xe74c3c)
                                await raise_error(embed=embed,content="",**args)
                    else:
                        error_code = "error4"
                        embed=nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
                        embed.set_footer(text=error_code)
                        await raise_error(embed=embed,content="",**args)
                else:   
                    error_code = "error12"  
                    embed=nextcord.Embed(title=lang["on_error"], description=lang[error_code], color=0xe74c3c)
                    embed.set_footer(text=error_code)
                    await raise_error(embed=embed,content="",**args)         
        ticketdb = await db.ticketsdb.find_one({"channelid": interaction.channel.id})
        msg = await interaction.channel.fetch_message(ticketdb.get("msgid"))
        if msg:
            error_thread = self.bot.get_channel(
                ticketdb["error_channelid"])
            userdb = await db.usersdb.find_one({"userid": ticketdb["userid"]})

            lang = await get_lang(userdb, interaction.channel.guild)
            embed, view = await self.show(self.bot.get_user(ticketdb["userid"]), lang, error_thread)

            await msg.edit(embed=embed, view=view)
        else:
            cprint(f"also msgid is nones {ticketdb}", "red")

    async def CommendsStarted(self, channel: nextcord.TextChannel, lang, steamID64, slotcurrency):
        datetime_utc = get_datetime_utc()
        
        ticketdb = await db.ticketsdb.find_one({"channelid": channel.id})
        serverusrs = await db.serverusers.find_one({"steamID64": steamID64})

        if not serverusrs:
            logger.error(f"steamid: {steamID64} not found in serverusers db, channelid: {channel.id} error: 1432")
            return

        customer = self.bot.get_user(ticketdb["userid"])
        guild = channel.guild
        msg = await channel.fetch_message(ticketdb["msgid"])

        amount = serverusrs["amount"]
        slotid = serverusrs["slot_id"]

        userbalancedb = await db.balancesdb.find_one({"userid": customer.id, "slot_id": slotid})

        oldbalance = int(userbalancedb["amount"])
        newbalance = oldbalance - amount
        sl = slotcurrency + amount

        await db.balancesdb.update_one({"_id": userbalancedb["_id"]}, {"$inc": {"today_used": amount}})

        timeestart = calendar.timegm(datetime_utc.timetuple())
        afterend = datetime_utc + datetime.timedelta(seconds=150 * amount)
        timeedit_eta = calendar.timegm(afterend.timetuple())

        selldb = {
            "datetime": datetime_utc,
            "customerid": serverusrs["userid"],
            "slot_id": serverusrs["slot_id"],
            "commend-amount": amount,
            "u_old-amount": serverusrs["old_balance"],
            "type": "commend",
            "steamID64": serverusrs["steamID64"],
            "start_datetime": datetime_utc
        }

        _id = (await db.sellsds.insert_one(selldb)).inserted_id
        await db.serverusers.update_one({"channelid": channel.id, "status": "w8connect"}, 
                                        {"$set": {"status": "confirmed", "commended": True, 
                                                "startedat": timeestart, "endeta": timeedit_eta, 
                                                "lastup": datetime_utc, "tr_id": _id}})

        embeds = await self.stats(db.serverusers.find({"channelid": channel.id}), lang)

        await msg.edit(view=pview(self.bot, Select_StopCommending, balance_menu, start_commend, language_header, customer, None), 
                    content=None, embeds=embeds)

        # logging
        embed = nextcord.Embed(title="Commending started!", description="", color=Colour.blurple(), timestamp=datetime.datetime.now())
        embed.add_field(name="Customer:", value=f"{customer.mention} - `{customer.id}`", inline=False)
        embed.add_field(name="SteamID:", value=steamID64, inline=False)
        embed.add_field(name="Server:", value=f"{guild} - `{guild.id}`", inline=False)
        embed.add_field(name="Commending ", value=f"```fix\n{amount} ```", inline=False)
        embed.add_field(name="User new balance:", value=f"```css\n{newbalance} ```", inline=False)
        embed.add_field(name="User old balance:", value=f"```css\n{oldbalance} ```", inline=False)
        embed.add_field(name="Slot new balance:", value=f"```ini\n[{slotcurrency}]```", inline=False)
        embed.add_field(name="Slot old balance:", value=f"```ini\n[{sl}]```", inline=False)

        await helpers.logembed(self, embed, guild, slotid)

    async def commend_process(self, doc: dict):
        datetime_utc = get_datetime_utc()
        steamID64 = int(doc["steamID64"])
        chunk = int(doc["chunk_id"])
        perchunk = doc["chunkstats"]
        targetpending = doc["pending_commends"]
        getcommends = int(perchunk.split("/")[0])

        serverclient = await db.serverusers.find_one({"steamID64": steamID64})

        if not serverclient:
            ch = self.bot.get_channel(config.SLOT_LOG_CHANNEL_ID)
            cb = await db.sellsds.find_one({"type": "commend", "steamID64": steamID64}, sort=[("_id", -1)])

            if cb and "end-datetime" in cb:
                await ch.send(cb)
                cp_time = (datetime_utc - datetime.timedelta(minutes=6))
                dt = (cb["end-datetime"]).replace(tzinfo=tz)
                if dt > cp_time:
                    await ch.send("ok")
                    await db.balancesdb.update_one({"userid": cb["customerid"]}, {"$inc": {"amount": -getcommends, "today_used": -getcommends}})
                    await db.slotsdb.find_one_and_update({"_id": cb["slot_id"]}, {"$inc": {"currency": -getcommends}}, return_document=pymongo.ReturnDocument.AFTER)
                    await db.sellsds.update_one({"_id": cb["_id"]}, {"$set": {"extraupt": datetime_utc, "extra-add": getcommends}})
            return

        currentamount = serverclient["actualamount"]
        amount = serverclient["amount"]
        realcurrent = amount - targetpending

        update_data = {
            "pendingmany": 0,
            "lastpending": targetpending,
            "actualamount": realcurrent,
            "chunk": chunk,
            "chunk-info": f"[{perchunk}]"
        }

        timenow = datetime.datetime.now(tz=tz)

        if targetpending == 0:
            await db.serverusers.update_one({"steamID64": steamID64}, {"$set": update_data})
        else:
            await db.serverusers.update_one({"steamID64": steamID64}, {"$set": {**update_data, "lastup": timenow}})

        currentamount += getcommends

        if "channelid" in serverclient:
            channel:TextChannel = self.bot.get_channel(serverclient["channelid"])

            if channel and serverclient["status"] != "w8connect":
                if chunk != serverclient["chunk"]:
                    ticketdb = dict(await db.ticketsdb.find_one({"channelid": channel.id}))
                    langdb = await db.usersdb.find_one({"userid": serverclient["userid"]})
                    customer = self.bot.get_user(serverclient["userid"])
                    lang = await get_lang(langdb, channel.guild)

                    if "startedat" in serverclient or "endeta" in serverclient:
                        database = db.serverusers.find({"channelid": channel.id})

                        embeds = await self.stats(database, lang)

                        if msgid := ticketdb.get("msgid"):
                            msge = await channel.fetch_message(int(msgid))
                            await msge.edit(embeds=embeds, view=pview(self.bot, Select_StopCommending, balance_menu, start_commend, language_header, customer, None))
                        else:
                            logger.warning("MSGID is NONE")

                        logchannel2 = self.bot.get_channel(config.TRANSACTION_LOG_2_CHANNEL_ID)

                        embed = nextcord.Embed(title="Commends Pending for Target", description="", color=nextcord.Color.blurple(), timestamp=datetime.datetime.now())
                        embed.add_field(name="Steam ID", value=steamID64, inline=False)
                        embed.add_field(name="Channel", value=f"{channel.mention} - {channel.id}", inline=False)
                        embed.add_field(name="Chunk", value=chunk, inline=False)
                        embed.add_field(name="Chunk Info", value=perchunk, inline=False)
                        embed.add_field(name="Current Balance", value=realcurrent, inline=False)
                        embed.add_field(name="Pending Commends", value=targetpending, inline=False)
                        embed.add_field(name="Total Commends", value=amount, inline=False)

                        await logchannel2.send(content=f"{steamID64}", embed=embed)

                        logger.debug(f"Commends pending for target {steamID64}")
                        logger.debug(f"Chunk: {chunk}, Chunk Info: {perchunk}, Current Balance: {realcurrent}, Pending Commends: {targetpending}, Total Commends: {amount}")
                    else:
                        await channel.threads[0].edit("There is any problem, please wait for support (commending started but idk how)", embed=None)
                else:
                    await channel.threads[0].send("There is any problem, please wait for support (started commending from another session)", embed=None)

    async def commend_done(self, commenddb: dict, steam64id: int, amountofget: int):
        steamdb = steam.users.get_user_details(steam64id)
        print("running done")
        datetime_utc = get_datetime_utc()
        userid = commenddb["userid"]

        amount = (commenddb["amount"])
        userdb = await db.usersdb.find_one({"userid": userid})

        if userdb:

            gpoints = amountofget / random.randint(10, 15)
            if "auto" in commenddb and commenddb["auto"]:
                gpoints *= random.uniform(0.8, 2)

            points = userdb["points"] + gpoints
            subdb = await db.subdb.find_one({"ownerid": userid, "disabled": False, "pay": True})
            await db.usersdb.update_one({"userid": userid}, {"$inc": {"points": gpoints}})
            # 4 = free , 2 = standard server
            if not subdb or subdb and subdb.get("subtype", 4) == [4, 2]:

                if "accs" in userdb:
                    if steam64id not in userdb["accs"]:
                        await db.usersdb.update_one({"userid": userid}, {"$set": {"points": points}, "$push": {"accs": steam64id}})
                else:
                    await db.usersdb.update_one({"userid": userid}, {"$set": {"points": points}, "$push": {"accs": steam64id}},)
        userbalancedb = await db.balancesdb.find_one({"userid": userid, "slot_id": commenddb["slot_id"]})

        status = commenddb["status"]
        totoalvalue = amount - amountofget
        newamount = userbalancedb["amount"]+totoalvalue
        await db.balancesdb.update_one(
            {"userid": userid, "slot_id": commenddb["slot_id"]},
            {"$inc": {"amount": totoalvalue, "today_used": -totoalvalue, "onhold": -amount},
             "$set": {"active": True, "last_activity": datetime_utc}},
        )
        selldb = {

            "end-datetime": datetime_utc,


            "commend-amount": amount,
            "got-amount": amountofget,
            "add-amount": totoalvalue,
            "u_new-amount": newamount,


        }

        if "channelid" in commenddb:

            user = self.bot.get_user(userid)
            channel: TextChannel = self.bot.get_channel(commenddb["channelid"])
            if channel:
                selldb["guildid"] = channel.guild.id
                ticketdb = await db.ticketsdb.find_one({"channelid": channel.id})

                lang = await get_lang(userdb, channel.guild)
                await db.serverusers.delete_one({"steamID64": steam64id})
            else:
                await db.serverusers.delete_one({"steamID64": steam64id})
                logger.error("Channel is nontype in commendone")
                return

        else:
            await db.serverusers.update_one({"steamID64": steam64id}, {'$set': {'status': "done", "lastup": datetime.datetime.now(tz=tz)}})

        try:
            await db.sellsds.update_one({"_id": commenddb["tr_id"]}, {"$set": selldb})
        except Exception as ex:
            cprint(ex, "red")
        if "cut" in commenddb:
            add = totoalvalue-commenddb["cut"]
        else:
            add = totoalvalue

            await db.slotsdb.find_one_and_update({"_id": commenddb["slot_id"]}, {"$inc": {"currency": +add}}, return_document=pymongo.ReturnDocument.AFTER)

        if "channelid" in commenddb:
            if commenddb["status"] == "w8connect":
                logger.error(f"{commenddb} is done even never started process(mb slot was stucked)")
                return
            timeedit = commenddb["startedat"]
            timeedit_eta = commenddb["endeta"]

            newbalance = userbalancedb["amount"] + totoalvalue

            if totoalvalue <= 0:

                restart_time = calendar.timegm(((get_datetime_utc(
                ) + datetime.timedelta(hours=1)).replace(minute=0, second=0)).timetuple())
                embed = nextcord.Embed(title=lang["on_message_finished-title"],
                                       description=lang["on_message_finished-description"], color=0x007e8f, timestamp=datetime.datetime.now())
                embed.add_field(name=lang["commend_stats-1-name"],
                                value=f"```css\n{amountofget}\n```", inline=True)
                embed.add_field(name=lang["commend_stats-2b-name"],
                                value=f"```css\n{totoalvalue}\n```", inline=True)
                embed.add_field(
                    name=lang["commend_stats-3-name"], value=f"```fix\n{amount}\n```", inline=True)
                embed.add_field(name=lang["on_message_finished_field-title"],
                                value=f"```ini\n[{userbalancedb['amount']}]\n```", inline=True)
                embed.add_field(name=lang["commend_stats-5-name"],
                                value=f"[{steam64id}](https://steamcommunity.com/profiles/{steam64id}/)", inline=False)
                embed.add_field(
                    name=lang["commend_stats-7-name"], value=f"<t:{timeedit}:R>", inline=True,)
                embed.add_field(
                    name=lang["commend_stats-8-name"], value=f"<t:{restart_time}:R>", inline=True)
                embed.set_thumbnail(steamdb['player']["avatarfull"])

                embed.set_author(
                    icon_url=steamdb['player']["avatar"], name=steamdb['player']["personaname"])

                embed.set_footer(text=config.BRAND_FOOTER,
                                 icon_url=config.BRAND_LOGO_URL)
                try:
                    await user.send(embed=embed)
                except Exception:
                    await channel.threads[0].send(embed=embed)

            else:
                timeedit = commenddb["startedat"]

                if status == "stoped":

                    embed = nextcord.Embed(
                        title=lang["on_message-stopped-title"], description="**Reason:** Bot been stopped via stop command", color=0xFFA500, timestamp=datetime.datetime.now())

                    embed.add_field(
                        name=lang["commend_stats-1-name"], value=f"```css\n{amountofget}\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-2b-name"], value=f"```css\n{totoalvalue}\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-3-name"], value=f"```fix\n{amount}\n```", inline=True)
                    embed.add_field(name=lang["on_message-stopped_field-title"],
                                    value=f"```ini\n[{newbalance}]\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-5-name"], value=f"[{steam64id}](https://steamcommunity.com/profiles/{steam64id}/)", inline=False)
                    embed.add_field(
                        name=lang["commend_stats-7-name"], value=f"<t:{timeedit}:R>", inline=True,)
                    embed.set_thumbnail(steamdb['player']["avatarfull"])

                    embed.set_author(
                        icon_url=steamdb['player']["avatar"], name=steamdb['player']["personaname"])
                    embed.set_footer(text=config.BRAND_FOOTER,
                                     icon_url=config.BRAND_LOGO_URL)

                elif status == "error":

                    embed = nextcord.Embed(
                        title=lang["on_message-error-title"], description=f"**Reason:** {commenddb['reason']}", color=nextcord.Color.brand_red(), timestamp=datetime.datetime.now())

                    embed.add_field(
                        name=lang["commend_stats-1-name"], value=f"```css\n{amountofget}\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-2b-name"], value=f"```css\n{totoalvalue}\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-3-name"], value=f"```fix\n{amount}\n```", inline=True)
                    embed.add_field(name=lang["on_message-error_field-title"],
                                    value=f"```ini\n[{newbalance}]\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-5-name"], value=f"[{steam64id}](https://steamcommunity.com/profiles/{steam64id}/)", inline=False)
                    embed.add_field(
                        name=lang["commend_stats-7-name"], value=f"<t:{timeedit}:R>", inline=True,)
                    embed.set_thumbnail(steamdb['player']["avatarfull"])

                    embed.set_author(
                        icon_url=steamdb['player']["avatar"], name=steamdb['player']["personaname"])
                    embed.set_footer(text=config.BRAND_FOOTER,
                                     icon_url=config.BRAND_LOGO_URL)

                else:

                    embed = nextcord.Embed(title=lang["on_message-disconnect-title"],
                                           description="**Reason:** Didn't reconnect in time.", color=0xFF0000, timestamp=datetime.datetime.now())
                    embed.add_field(
                        name=lang["commend_stats-1-name"], value=f"```css\n{amountofget}\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-2b-name"], value=f"```css\n{totoalvalue}\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-3-name"], value=f"```fix\n{amount}\n```", inline=True)
                    embed.add_field(name=lang["on_message-disconnect_field-title"],
                                    value=f"```ini\n[{newbalance}]\n```", inline=True)
                    embed.add_field(
                        name=lang["commend_stats-5-name"], value=f"[{steam64id}](https://steamcommunity.com/profiles/{steam64id}/)", inline=False)
                    embed.add_field(
                        name=lang["commend_stats-7-name"], value=f"<t:{timeedit}:R>", inline=True,)
                    embed.set_thumbnail(steamdb['player']["avatarfull"])

                    embed.set_author(
                        icon_url=steamdb['player']["avatar"], name=steamdb['player']["personaname"])
                    embed.set_footer(text=config.BRAND_FOOTER,
                                     icon_url=config.BRAND_LOGO_URL)
                try:
                    await user.send(embed=embed,)
                except Exception:

                    await channel.threads[0].send(embed=embed,)

            count = await db.serverusers.count_documents({"channelid": channel.id})

            if count == 0:
                msg = await channel.fetch_message(int(ticketdb["msgid"]))
                error_channel = self.bot.get_channel(
                    ticketdb["error_channelid"])

                embed, view = await self.show(user, lang, error_channel)

                await msg.edit(embed=embed, view=view)
            else:

                database = db.serverusers.find(
                    {"channelid": channel.id, "status": "confirmed"})

                embeds = await self.stats(database, lang)

                msgg = await channel.fetch_message(ticketdb["msgid"])
                await msgg.edit(embeds=embeds, view=pview(self.bot, Select_StopCommending, balance_menu, start_commend, language_header, user, None))
            if count == 0:
                embed = nextcord.Embed(color=0xff0000)
                embed.set_author(name=config.BRAND_NAME,
                                 url=config.BRAND_URL, icon_url=logo)
                embed.set_thumbnail(url=logo)
                if channel.guild.id == config.COMMUNITY_GUILD_ID:
                    embed.add_field(
                        name="Thank You 💖", value=f"Thanks for using CommendBot. We'll be very happy if you share us\non social media or join our [steam group]({config.BRAND_STEAM_GROUP_URL}).\n\nDon\`t forget to leave a feedback on⁠ <#1099636327135313964> channel.\nExample: `+rep <@839124828232744970> 250 CS:GO Commends` ", inline=False)

                else:
                    embed.add_field(
                        name="Thank You 💖", value="Thanks for using CommendBot. We'll be very happy if you share us on social media or join our steam group.  Also visit feedback  and write something about us.  ", inline=False)
                embed.add_field(
                    name="Server links:", value=f"https://www.trustpilot.com/review/{config.BRAND_NAME}", inline=False)
                try:
                    await user.send(embed=embed,)
                except Exception:
                    logger.error(f"I cant send message to {user.id} 1793")
                

        logchannel2 = self.bot.get_channel(config.TRANSACTION_LOG_2_CHANNEL_ID)

        embedd = nextcord.Embed(title="Commending done", description="",
                                color=nextcord.Color.green(), timestamp=datetime.datetime.now(),)
        embedd.add_field(name="Steam id", value=steam64id, inline=True)
        if "channelid" in commenddb:
            embedd.add_field(
                name="channel", value=f"{channel.mention} - {channel.id}", inline=True)
        embedd.add_field(name="kolko dostal", value=amountofget, inline=False)
        embedd.add_field(name="kolko nedostal",
                         value=totoalvalue, inline=False)
        embedd.add_field(name=" kolko mal dostať", value=amount, inline=False)
        await logchannel2.send(content=f"{steam64id}", embed=embedd)
        cprint((
            f"Commending done for {steam64id}\n "
            f"kolko dostal: {amountofget} , kolko nedostal: {totoalvalue} , kolko mal dostať : {amount}"

        ), "green")

    @staticmethod
    async def stats(database: dict, lang: dict) -> list[nextcord.Embed]:
        embeds = []
        restart_time = calendar.timegm(((get_datetime_utc() + datetime.timedelta(days=1)).replace(minute=0, second=0,hour=0)).timetuple())

        async for count, accountdb in a.enumerate(database, 1):
            steamdb = steam.users.get_user_details(accountdb["steamID64"])

            embed = nextcord.Embed(color=0x67e65c, timestamp=datetime.datetime.now())

            embed.add_field(name=lang["commend_stats-1-name"], value=f"```css\n{accountdb['actualamount']}\n```", inline=True)
            embed.add_field(name=lang["commend_stats-2-name"], value=f"```css\n{accountdb['lastpending']}\n```", inline=True)
            embed.add_field(name=lang["commend_stats-3-name"], value=f"```fix\n{accountdb['amount']}\n```", inline=True)
            embed.add_field(name=lang["commend_stats-4-name"], value=f"```cs\n{accountdb['chunk']}\n```", inline=True)
            embed.add_field(name=lang["commend_stats-5-name"], value=f"```ini\n{accountdb['chunk-info']}\n```", inline=True)
            embed.add_field(name=lang["commend_stats-6-name"], value=f"[{accountdb['steamID64']}](https://steamcommunity.com/profiles/{accountdb['steamID64']}/)", inline=False)
            embed.add_field(name=lang["commend_stats-7-name"], value=f"<t:{accountdb['startedat']}:R>", inline=True)
            embed.add_field(name=lang["commend_stats-8-name"], value=f"<t:{restart_time}:R>", inline=True)
            embed.add_field(name="ㅤ", value=lang["commend_stats-9"], inline=False)

            embed.set_thumbnail(steamdb['player']["avatarfull"])
            embed.set_author(icon_url=steamdb['player']["avatar"], name=steamdb['player']["personaname"])
            embed.set_footer(text=config.BRAND_FOOTER, icon_url=config.BRAND_LOGO_URL)

            embeds.append(embed)

        return embeds
