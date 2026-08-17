import datetime

from nextcord.ext import commands, tasks
from nextcord.ext.commands import Bot

from cogs.commend import *
from cogs.helpers import *

datetime_utc = datetime.datetime.now(tz=tz)

class ai(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
        
    @commands.Cog.listener()
    async def on_ready(self):
        if not ai.check.is_running():
            ai.check.start(self)
            
    
    @tasks.loop(minutes=5)
    async def check(self):
        slotsdb = db.slotsdb.find({})
        commending = await db.serverusers.find({}).to_list(None)
        
        async for slotdb in slotsdb:
            serverusers = list(filter(lambda i: i["slot_id"]==slotdb["_id"],commending))
            
            steamids = [i["steamID64"]for i in serverusers]
            await db.learn.insert_one({"datetime":datetime_utc,"users":len(serverusers),"week":datetime_utc.isoweekday(),"slot_id":slotdb["_id"],"currency":slotdb["currency"],"update_currency":slotdb["update_currency"],"steamids":steamids})
            if "ai-balance" in slotdb and slotdb["ai-balance"]:
            
                max_commends = slotdb["max_commends"]
                max_daily_commends = slotdb["max_daily_commends"]
                currency = slotdb["currency"] 
                currency_limit = slotdb["update_currency"]
                users = len(serverusers)
                free = (currency/currency_limit)*100
                weekend = True if datetime_utc.isoweekday() == 6 or datetime_utc.isoweekday() == 7 else False
                print(weekend)
                print(free)
                freee = datetime_utc.replace(hour=20,minute=0)
                if datetime_utc.time() <= freee.time():
                    if free >= 90  and not weekend or users <= 0 and free >= 80 and not weekend:
                        
                        max_commends = 1000
                        max_daily_commends = 1000
                    elif free >= 80 and not weekend or users <= 4 and free >= 70 and not weekend:
                        max_commends = 500
                        if max_daily_commends > 500:
                            max_daily_commends = 500
                    elif free >= 70 or users <= 4 and free >= 50:
                        max_commends = 250
                        max_daily_commends = 300
                    elif free >= 50 or users <= 4 and free >= 35:
                        max_commends = 150
                        
                        max_daily_commends = 250
                    elif free >= 35 or users <= 4 and free >= 10:
                        max_commends = 100
                        max_daily_commends = 150
                    else:
                        
                        max_daily_commends = 100
                        max_commends = 50 
                else:
                    max_commends = 99999
                    max_daily_commends = 99999
                if max_daily_commends != slotdb["max_daily_commends"] or max_commends != slotdb["max_commends"]:
                    await db.slotsdb.update_one({'_id': slotdb["_id"]}, {'$set': {'max_daily_commends': max_daily_commends,"max_commends":max_commends}})
                    
                    
                
    
    
    

def setup(bot: Bot) -> None:
    bot.add_cog(ai(bot))