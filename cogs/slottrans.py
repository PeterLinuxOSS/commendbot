import asyncio
import calendar
import datetime
import time

import nextcord
from dateutil.relativedelta import relativedelta
from nextcord import Colour, TextChannel, User
from nextcord.ext import commands
from nextcord.ext.commands import Bot

import config
from cogs.commend import *
from cogs.commend_menu import commend_menu
from cogs.helpers import *
from utils import *


class slottrans(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        
        self.loop = asyncio.get_event_loop()
        self.task = self.loop.create_task(self.watch_mongodb())
        self.task = self.loop.create_task(self.watch_usersdb())
        
    async def watch_usersdb(self):
        while not self.bot.slottrans_ready :
            await asyncio.sleep(0)
            
        
        
      
        cprint("watch_usersdb is started!")
        # Process the changes in the main thread
        async with self.loop.run_in_executor(None, db.users_database.watch) as changes:
            async for change in changes:
                db_name = change["ns"]["coll"]
                if db_name == "balancesdb":
                    if change["operationType"] == "update":
                        amount =  change['updateDescription']['updatedFields'].get("amount")
                        if amount:
                            object_id = change['documentKey']['_id']
                            
                            baldb = await db.balancesdb.find_one({"_id":object_id})
                            
                            ticket = await db.ticketsdb.find_one({"userid":baldb["userid"]})
                            if ticket:
                                
                                count:int = await db.serverusers.count_documents({"userid":baldb["userid"]})
                                if count == 0:
                                    
                                    channel = self.bot.get_channel(ticket.get("channelid"))
                                    if channel:
                                        
                                        msg = await channel.fetch_message(ticket.get("msgid"))
                                        if msg:
                                            
                                            embed = msg.embeds[0]
                                            embed.timestamp = datetime.datetime.now()
                                            embed.set_field_at(0,value=amount,name=embed.fields[0].name,inline=False)
                                            
                                            await msg.edit(embed=embed)
                                        
                                        
                        
                    
        
        
    async def watch_mongodb(self):
        while not self.bot.slottrans_ready :
            await asyncio.sleep(2)
            
            
        
            
        
        cprint("watch_mongodb is started!")
        
        # Run the blocking operation in a separate thread
        changes = await self.loop.run_in_executor(None, db.servers.watch)
        
        # Process the changes in the main thread
        async for change in changes:
            db_name = change["ns"]["coll"]
            
            if db_name == "waitinglist":   
                if change["operationType"] == "insert":
                    
                    doc:dict = change["fullDocument"]
                    
                    
                    if doc["type"] == "start":
                        if doc["status"] == "wait":
                            if not await db.waitinglist.find_one({"type":"start","status":"go"}):
                                
                                await db.waitinglist.update_one({"_id":doc["_id"]},{"$set":{"status":"go"}})
                                if  await db.slottrans.find_one({"steamID64":doc['steamID64'],"push":"post"}) is None: # check if is not slot stucked 
                                    await db.slottrans.insert_one({"slot_id":doc["slot_id"],"steamID64":doc['steamID64'],"push":"post","type":"start","amount":doc['amount']})
                                
                                    
                        else:
                            if  await db.slottrans.find_one({"steamID64":doc['steamID64'],"push":"post"}) is None: # check if is not slot stucked 
                                await db.slottrans.insert_one({"slot_id":doc["slot_id"],"steamID64":doc['steamID64'],"push":"post","type":"start","amount":doc['amount']})
                                print("slot error-watch_mongodb - waitlist")
                            else:
                                logger.error("SLOT IS STUCKED start")
                    elif doc["type"] == "stop":
                        if doc["status"] == "wait":
                            if not await db.waitinglist.find_one({"type":"stop","status":"go"}):
                                
                                await db.waitinglist.update_one({"_id":doc["_id"]},{"$set":{"status":"go"}})
                                if  await db.slottrans.find_one({"steamID64":doc['steamID64'],"push":"post"}) is None: # check if is not slot stucked 
                                    await db.slottrans.insert_one({"slot_id":doc["slot_id"],"steamID64":doc['steamID64'],"push":"post","type":"stop"})
                                else:
                                    logger.error("SLOT IS STUCKED stop")
                                
            elif db_name == "slottrans":
                if change["operationType"] == "insert":
                    doc:dict = change["fullDocument"]
                    try:
                        await slottrans.trans_update(self,doc)
                    except Exception:
                        logger.exception("Slottransit-exeption")
                    
            elif db_name == "paypal":
                if change["operationType"] == "insert":
                    
                    doc:dict = change["fullDocument"]
                    
                    
                    if doc.get("json") is None:
                        print("json is None")
                        continue
                    print(doc)
                    jfile:dict = json.loads(doc["json"])
                    memo:str = jfile.get("memo",None)
                    if memo and memo.isnumeric():
                        user = self.bot.get_user(int(memo))
                        if user:
                            await slottrans.payment_update(self,user,jfile)
                        else:
                            
                            mail:str = jfile.get("payer_email")
                            userdb = await db.usersdb.find_one({"mail":mail,"verify":True})
                            if userdb:
                                user = self.bot.get_user(userdb["userid"])
                                if user:
                                    await slottrans.payment_update(self,user,jfile)
                            else:
                                print(" user is unknown")    
                    else:
                        mail:str = jfile.get("payer_email")
                        userdb = await db.usersdb.find_one({"mail":mail,"verify":True})
                        if userdb:
                            user = self.bot.get_user(userdb["userid"])
                            if user:
                                await slottrans.payment_update(self,user,jfile)
                        else:
                            print(" user is unknow")       
                                
                
                            
                            
                                
    async def payment_update(self,user:User,jfile:dict):
        
        blacklistdb = await db.blacklistdb.find_one({"userid":user.id})
        auto_paych = self.bot.get_channel(config.AUTO_PAYOUT_CHANNEL_ID)
        if not blacklistdb:
            
            eligibilit :str= jfile.get("protection_eligibility")
            
            if  eligibilit == "Ineligible":
                currency :str= jfile.get("mc_currency")
                if currency == "EUR":
                    
                    result = float(jfile.get("mc_gross",0))
                    amount = result * 100 if result <= 1 else result * 100 * 100 / 83 if result <= 1.83 else result * 100 * 100 / 72 if result <= 2.55 else result * 100 * 100 / 65 if result <= 3.075 else result * 100 * 100 / 50 if result <= 5.0 else result * 100 * 100 / 45 if result <= 5.55556 else result * 100 * 100 / 40 if result <= 7.14286 else result * 100 * 100 / 35 if result <= 8.92857 else result * 100 * 100 / 30 if result <= 10.7143 else result * 100 * 100 / 27

                    amount = math.floor(amount)
                    mydb = await db.balancesdb.find_one({"userid":self.bot.user.id})
                    await helpers.giftbal(self,True,mydb,amount,auto_paych,self.bot.user,user,auto_paych.guild,True) 
                else:
                    try:
                        await user.send(embed=embed_error("Error Express-Auto-Pay","Your transaction was in non EUR currency. Your order was automatically cancelled, without refund due to our policy!"))
                    except Exception:pass
                    await auto_paych.send(embed=embed_error("Error Express-Auto-Pay",f"Your transaction was in non EUR currency. Your order was automatically cancelled, without refund due to our policy! for {user.id}"))
                        
            else:
                try:
                    await user.send(embed=embed_error("Error Express-Auto-Pay","Your transaction was sent as Goods for a Product, we are not accepting payment on this way! Your order was automatically cancelled, without refund due to our policy!"))
                except Exception:pass
                await auto_paych.send(embed=embed_error("Error Express-Auto-Pay",f"Your transaction was sent as Goods for a Product, we are not accepting payment on this way! Your order was automatically cancelled, without refund due to our policy! {user.id}"))
        else:
            try:
                await user.send(embed=embed_error("Error Express-Auto-Pay","Your account is blacklisted! Your order was automatically cancelled, without refund due to our policy!"))
            except Exception:pass
            await auto_paych.send(embed=embed_error("Error Express-Auto-Pay",f"Your account is blacklisted! Your order was automatically cancelled, without refund due to our policy! {user.id}"))
                                             
              
    

    async def trans_update(self, doc: dict):
        timestamp = datetime.datetime.now()
        datetime_utc = get_datetime_utc()  

        if doc["push"] == "respond":
            await db.slottrans.delete_one({"_id": doc["_id"]})
            
            

            if doc["type"] == "commend_done":
                steamID64 = int(doc["steamID64"])
                cprint(f"sttarting cb done for: {steamID64} {datetime.datetime.now(tz=tzsk)}", "green")
                total_commends = int(doc["total_commends"])
                commenddb = await db.serverusers.find_one({"steamID64": steamID64})
                if commenddb:
                    asyncio.create_task(commend_menu.commend_done(self, commenddb, steamID64, total_commends))
                else:
                    cprint(f"cb done for: {steamID64} commenddb is None", "red")
                return

            elif doc["type"] == "commend_process":
                asyncio.create_task(commend_menu.commend_process(self, doc))

            elif doc["type"] == "info":
                slotdb = await db.slotsdb.find_one({"_id": doc["slot_id"]})
                replacedict = {}

                if slotdb["expire"] != doc["expire"]:
                    replacedict["expire"] = doc["expire"]
                    replacedict["alert"] = False
                    replacedict["alert_members"] = False

                commend_count = await db.serverusers.count_documents({})

                if commend_count == 0 and slotdb["currency"] != doc["currency"]:
                    replacedict["currency"] = doc["update_currency"] - doc["currency"]
                    logger.info(f"slot currency was updated to: {replacedict['currency']}")

                if "update_currency" in slotdb and slotdb["update_currency"] != doc["update_currency"]:
                    replacedict["update_currency"] = doc["update_currency"]
                elif "update_currency" not in slotdb:
                    replacedict["update_currency"] = doc["update_currency"]

                await db.slotsdb.update_one({"_id": slotdb["_id"]}, {"$set": replacedict})

                if datetime_utc.hour == 0 and "update_currency" in slotdb:
                    await db.slotsdb.update_one({"_id": slotdb["_id"]}, {"$set": {"currency": doc["update_currency"]}})
                    logger.debug("Updated slot " + str(slotdb["_id"]))

                if "expire" in slotdb:
                    exp_date = slotdb["expire"].replace(tzinfo=tz)
                    datetime_utc = get_datetime_utc()  
                    msg_secs = (exp_date - datetime_utc).total_seconds()

                    if 777600 < msg_secs and ("alert" not in slotdb or not slotdb["alert"]):
                        await db.slotsdb.update_one({"_id": slotdb["_id"]}, {"$set": {"alert": True}})
                        embed = nextcord.Embed(title="Slot Alert", description="Please pay for your resell sub or after 48hr all users of our slot ll get warning message", color=Colour.red(), timestamp=timestamp,)
                        embed.add_field(name="Slot ID", value=slotdb["_id"], inline=False)
                        embed.add_field(name="Slot name", value=slotdb["name"], inline=False)

                        for adminid in slotdb["admins"]:
                            admin = self.bot.get_user(adminid)
                            if await can_dm_user(admin):
                                await admin.send(embed=embed)
                            else:
                                bot_owner = self.bot.get_user(self.bot.owner_id)
                                await bot_owner.send(f"i cant send msg to owner of slot named {admin}", embed=embed)

                    elif 604800 <= msg_secs and ("alert_members" not in slotdb and "stop" not in slotdb) or (604800 <= msg_secs and not slotdb["alert_members"] and "stop" not in slotdb):
                        balances = db.balancesdb.find({"slot_id": slotdb["_id"]})
                        ts_datetime = utc_to_local(balances)
                        ts = f"<t:{int(time.mktime(ts_datetime.timetuple()))}:D>"
                        all_balances = len(balances)

                        async for id, g in a.enumerate(balances):
                            embed = nextcord.Embed(title="Urgent info", description=f"Your balance from slot {slotdb['name']} ll reset {ts}, please use your balance or u ll lose it!", color=Colour.red(), timestamp=timestamp,)
                            embed.add_field(name="Balance", value=f"{g['amount']} commends", inline=False)
                            embed.add_field(name="Kind Regards,", value=f"[{config.BRAND_NAME}]({config.BRAND_URL})", inline=False)
                            embed.set_footer(text=config.BRAND_FOOTER, icon_url=config.BRAND_LOGO_URL)
                            cprint(f"Please don't turn off script {id}/{all_balances}", "red")
                            customer = self.bot.get_user(g["userid"])

                            if await can_dm_user(customer):
                                try:
                                    await customer.send(embed=embed)
                                except Exception:
                                    logger.warning(f" {id}/{all_balances} - error with {g['userid']}")
                                else:
                                    await asyncio.sleep(5)
                            await db.slotsdb.update_one({"_id": slotdb["_id"]}, {"$set": {"alert_members": True}})
                if datetime_utc.hour == 0:
                    if "reset_1m" in slotdb and datetime_utc.day == slotdb["reset_1m"].day and datetime_utc.month == slotdb["reset_1m"].month:
                        await db.usersdb.update_many({}, {'$set': {'points': 0}})
                        deleted = db.balancesdb.find({"slot_id": slotdb["_id"],"active":False})
                        async for id,userdb in a.enumerate(deleted,1):
                            deleted_amount = userdb.get("amount")
                            user_id = userdb.get("userid")
                            await db.sellsds.insert_one({

                                "datetime": datetime_utc,

                                "customerid": user_id,
                                "slot_id": slotdb["_id"],
                                "remove-amount": deleted_amount,
                                "u_old-amount": (deleted_amount),
                                "u_new-amount": 0,
                                "type": "remove",
                                "note":"inactivity"

                            })
                            await db.balancesdb.delete_one({"_id":userdb["_id"]}) 
                            user = self.bot.get_user(user_id) 
                            
                            if user and await can_dm_user(user):
                                
                                embed = nextcord.Embed(title="Your Balance was deleted!",  color=Colour.brand_red(), timestamp=timestamp,)
                                embed.add_field(name="Reason",value="Your account was inactive for 2 or more weeks",inline=False)
                                embed.add_field(name="Old Balance",value=str(deleted_amount),inline=False)
                                embed.add_field(name="New Balance",value=str(0),inline=False)
                                cprint(f"DONT TURN OFF SCRIPT!!! {id}/xxxx","red")
                                try:
                                    await user.send(embed=embed)
                                except Exception:
                                    logger.warning(f" {id}/xxxx - error with {userdb['userid']}")
                                else:
                                    await asyncio.sleep(6)
                            else:
                                logger.error(f"user is none in monthly reset: {userdb}")
                        
                        logchannel = self.bot.get_channel(slotdb["logchannelid"])
                        await logchannel.send(f"Balance db was reset(monthly reset) on slot {slotdb['_id']}")
                        datetimeto = datetime_utc + relativedelta(months=+1)
                        await db.slotsdb.update_one({"_id": slotdb["_id"]}, {"$set": {"reset_1m": datetimeto,"reset_alert":False}})
                        
                        

                    elif "reset_3m" in slotdb and datetime_utc.day == int(slotdb["reset_3m"]):
                        await db.balancesdb.delete_many({"slot_id": slotdb["_id"]})
                        logchannel = self.bot.get_channel(slotdb["logchannelid"])
                        await logchannel.send("Balance db was reset(3- monthly reset)")
                        datetimeto = datetime_utc + relativedelta(months=+3)
                        await db.slotsdb.update_one({"_id": slotdb["_id"]}, {"$set": {"reset_3m": datetimeto}})

                    elif "reset_1y" in slotdb and datetime_utc.day == int(slotdb["reset_1y"].split(".")[0]) and datetime_utc.month == int(slotdb["reset_1y"].split(".")[1]):
                        await db.balancesdb.delete_many({"slot_id": slotdb["_id"]})
                        logchannel = self.bot.get_channel(slotdb["logchannelid"])
                        await logchannel.send("Balance db was reset(year reset)")
                        datetimeto = datetime_utc + relativedelta(years=+1)
                        await db.slotsdb.update_one({"_id": slotdb["_id"]}, {"$set": {"reset_1y": datetimeto}})

                    elif "reset_bysub" in slotdb and datetime_utc.day == int(slotdb["reset_bysub"].split(".")[0]) and datetime_utc.month == int(slotdb["reset_bysub"].split(".")[1]):
                        await db.balancesdb.delete_many({"slot_id": slotdb["_id"]})
                        logchannel = self.bot.get_channel(slotdb["logchannelid"])
                        await logchannel.send("Balance db was reset (by resell sub end)")

            elif doc["type"] == "sessions":
                print("in session")
                accounts = doc["accounts"]
                serverdb = db.serverusers.find()
                logchannel = self.bot.get_channel(config.TRANSACTION_LOG_CHANNEL_ID)

                async for item in serverdb:
                    acc = item["steamID64"]

                    if str(item["steamID64"]) in accounts:
                        if item["status"] == "confirmed":
                            print("accis ok")
                            await db.serverusers.update_one({"steamID64": acc}, {"$set": {"lastup": datetime_utc}})
                        elif item["status"] == "w8connect":
                            channel = self.bot.get_channel(item.get("channelid"))
                            if channel:
                                asyncio.create_task(slottrans.process_f_start(self, channel, item))
                            else:
                                cprint("channel is none lol none ")
                    else:
                        if item["status"] == "confirmed":
                            userons = await db.serverusers.find_one({"steamID64": acc})
                            asyncio.create_task(commend_menu.commend_done(self, userons, acc, userons["actualamount"]))
                            await logchannel.send(userons)

            elif doc["type"] in ["commend_started", "limit_reached"] or ("msg" in doc and any(item in doc["msg"] for item in ["active subscription.", "Failed to find session.", "The session should stop immediately.","An error occurred:"])):
                type_mapping = {
                    "commend_started": "start",
                    "limit_reached": "start",
                    "active subscription.": "stop",
                    "failed_find_session": "stop",
                    "The session should stop immediately.": "stop",
                    "target_is_commended":"start",
                    "other":"stop"
                }
                logger.info(doc)
                logger.info("type of session is : "+type_mapping[doc["type"]])
                if doc["type"] == "other":
                    if "active subscription." in doc["msg"]:
                        slot_id  = doc["slot_id"]
                        await db.slotsdb.update_one({"_id":slot_id},{"$set":{"enable":False}})
                        logger.error(f"Slot {slot_id} expired subscription on sinl.")
                        
                    logchannel = self.bot.get_channel(config.SLOT_LOG_CHANNEL_ID)
                    
                    
                status_mapping = {
                    "commend_started": "go",
                    "limit_reached": "go",
                    "active subscription.": "go",
                    "Failed to find session.": "go",
                    "The session should stop immediately.": "go",
                }

                if waitls := await db.waitinglist.find_one({"slot_id": doc["slot_id"], "status": "go", "type": type_mapping[doc["type"]]}):
                    await db.waitinglist.delete_one({"_id": waitls["_id"]})

                    search = db.waitinglist.find({"slot_id": doc["slot_id"], "type": type_mapping[doc["type"]]})
                    async for wait in search:
                        if wait["status"] != "go":
                            await db.waitinglist.update_one({'_id': wait["_id"]}, {'$set': {'status': "go", "datetime": datetime_utc}})
                            if  await db.slotsdb.find_one({"steamID64":wait['steamID64'],"push":"post"}) is None: # check if is not slot stucked 
                                await db.slottrans.insert_one({"slot_id": doc["slot_id"], "steamID64": wait['steamID64'], "push": "post", "type": type_mapping[doc["type"]], "amount": wait.get('amount')})
                            else:
                                
                                logger.error(f"SLOT IS STUCKED for-l {type_mapping[doc['type']]}")
                            break
                        else:
                            break

                    channel = self.bot.get_channel(waitls.get("channelid")) if "channelid" in waitls else None

                    if doc["type"] == "commend_started":
                        if channel:
                            asyncio.create_task(slottrans.process_f_start(self, channel, waitls))
                        else:
                            cprint("error channel is none idk lol","red")
                        return
                    elif doc["type"] == "target_is_commended":
                        
                        steamID64 = int(waitls["steamID64"])
                        sb = await db.serverusers.find_one({"steamID64": steamID64})
                        rses = "Target is already being commended! "
                        
                        
                        asyncio.create_task(commend_menu.stop_waiting(self, sb, rses))
                    
                    elif doc["type"] == "limit_reached":
                        limit = doc["limit"]
                        steamID64 = int(waitls["steamID64"])
                        sb = await db.serverusers.find_one({"steamID64": steamID64})
                        rses = "Sorry, For today we don't have commends. You need to wait until 00:00 UTC"
                        logchannel = self.bot.get_channel(config.OWNER_LOG_CHANNEL_ID)
                        await logchannel.send(f"For some reason, the slot doesn't have a balance when the DB had a balance <@{config.OWNER_ID}> `{sb}`")
                        asyncio.create_task(commend_menu.stop_waiting(self, sb, rses, limit))
                    elif any(item in doc["msg"] for item in ["active subscription."]):
                        steamID64 = int(waitls["steamID64"])
                        sb = await db.serverusers.find_one({"steamID64": steamID64})

                        if doc["type"] == "active subscription.":
                            rses = "Slot doesn't have an active subscription. Please contact admin."
                            await db.slotsdb.update_one({"_id": sb["slot_id"]}, {'$set': {'enable': False}})
                            asyncio.create_task(commend_menu.stop_waiting(self, sb, rses))
                        
                        
                    elif any(item in doc["msg"] for item in [ "The session should stop immediately.", "Failed to find session."]):
                        steamID64 = int(waitls["steamID64"])
                        sb = await db.serverusers.find_one({"steamID64": steamID64})
                        if doc["type"] == "The session should stop immediately.":
                            if sb and "actualamount" in sb:
                                asyncio.create_task(commend_menu.commend_done(self, sb, steamID64, sb["actualamount"]))
                            else:
                                raise BaseException(f"Database for {steamID64} does not exist or the actualamount is invalid")
                            
                        if   "The session should stop immediately." in doc["type"]:
                            pass
                else:
                    vl = {"slot_id": doc["slot_id"], "status": "go", "type": type_mapping[doc["type"]]}
                    cprint(f"not exist {vl}", "yellow")       
            else:
                cprint(f"else exit: {doc}", "yellow")


       
    def cog_unload(self):
        self.task.cancel()
        
    async def process_f_start(self,channel:TextChannel,waitinglist):
        datetime_utc = get_datetime_utc()  
        print("here- commend_started")
                        
        vs = await db.slotsdb.find_one({"_id":waitinglist["slot_id"]})
        slotcurrency =vs["currency"]
        
        

        if channel:
            userdb = await db.usersdb.find_one({"userid":waitinglist["userid"]})
            lang = await get_lang(userdb, channel.guild)
            await commend_menu.CommendsStarted(self,channel,lang,int(waitinglist["steamID64"]),slotcurrency )
        else:
            wuser = await db.serverusers.find_one({"steamID64":waitinglist["steamID64"]})
            amount =wuser["amount"]
            await db.balancesdb.update_one({"userid":wuser["userid"]}, {"$inc": {"amount":-amount,"today_used":amount,"onhold":amount}})
            timeedit = calendar.timegm(datetime_utc.timetuple())
            calc =  30 * amount # eta calc
            afterend =datetime_utc +datetime.timedelta(seconds=calc)
            timeedit_eta = calendar.timegm(afterend.timetuple())
            selldb = {
        
                    "datetime":datetime_utc,    
                    "customerid":wuser["userid"],
                    "slot_id":wuser["slot_id"],
                    "commend-amount":amount, 
                    "u_old-amount":wuser["old_balance"],
                    "type":"commend",
                    "steamID64":wuser["steamID64"],
                    "start_datetime":datetime_utc
                    
                    

                }
            
            
            _id = (await db.sellsds.insert_one(selldb)).inserted_id
            await db.serverusers.update_one({"_id":wuser["_id"]}, {"$set": {"status":"confirmed", "commended":True,"startedat":timeedit,"endeta":timeedit_eta,"lastup":datetime_utc,"tr_id":_id}})
                     



def setup(bot: Bot) -> None:
    bot.add_cog(slottrans(bot))