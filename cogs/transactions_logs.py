import calendar
import datetime

import nextcord
import pymongo
from bson import ObjectId
from nextcord import Colour, Interaction, User
from nextcord.ext import commands
from nextcord.ext.commands import Bot

# (nothing needed from cogs.commend)
from cogs.helpers import helpers
from utils import (
    can_dm_user,
    create_bal,
    db,
    embed_error,
    embed_success,
    is_reseller,
    is_slot_admin,
    prettify,
    sview,
    timestamp,
    tz,
)


class properties(nextcord.ui.Select):
    def __init__(self,bot:Bot,selectOption,allist,filter,page):
        self.bot = bot
        self.allist = allist
        self.filter = filter
        self.page = page
        
        super().__init__(placeholder="Select", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        memebr = interaction.user
        selectOption = []
        tr_id = ObjectId(self.values[0])
        transactiondb = await db.sellsds.find_one({"_id":tr_id})
        
        dt:datetime.datetime = transactiondb["datetime"]
        embed = nextcord.Embed(title="Transaction Details",  color=Colour.blurple(), timestamp=timestamp,)
        embed.add_field(name="DateTime:", value=f"<t:{calendar.timegm(dt.timetuple())}:f>", inline=False)
        embed.add_field(name="TransactionID:", value=f"`{transactiondb['_id']}`", inline=False)
        embed.add_field(name="Type:", value=f"{transactiondb['type']}", inline=False)
        embed.add_field(name="SlotID:", value=f"```fix\n{transactiondb['slot_id']}\n```", inline=False)
        if transactiondb["type"] == "add" and transactiondb["sellerid"] ==  memebr.id:
            embed.add_field(name="Added Amount:", value=f"```js\n{transactiondb['gifted-amount']}\n```", inline=False)
            embed.add_field(name="Old Balance:", value=f"```fix\n{transactiondb['u_old-amount']}\n```", inline=True)
            embed.add_field(name="New Balance:", value=f"```fix\n{transactiondb['u_new-amount']}\n```", inline=True)
            customer = self.bot.get_user(transactiondb['customerid'])
            embed.add_field(name="Added to:", value=f"{customer.mention} - `{customer.id}`", inline=False)
            if "note" in transactiondb:
                embed.add_field(name="Note:", value=f"{transactiondb['note']}", inline=False)
            if "refund" in transactiondb and transactiondb["refund"]:
                embed.add_field(name="Refunded:", value="Yes", inline=False)
            else:
                if await is_slot_admin(memebr,transactiondb['slot_id']):
                    selectOption.append(nextcord.SelectOption(label="Refund",value="refund-add", emoji="💸"))
        elif transactiondb["type"] == "gift" and transactiondb["gifterid"] ==  memebr.id:
            embed.add_field(name="Gift Amount:", value=f"```js\n{transactiondb['gifted-amount']}\n```", inline=False)
            customer = self.bot.get_user(transactiondb['customerid'])
            embed.add_field(name="Customer:", value=f"{customer.mention} - `{customer.id}`", inline=False)
            embed.add_field(name="Old Customer Balance:", value=f"```css\n{transactiondb['u_old-amount']}\n```", inline=True)
            embed.add_field(name="New Customer Balance:", value=f"```fix\n{transactiondb['u_new-amount']}\n```", inline=False)
            embed.add_field(name="Old Gifter Balance:", value=f"```css\n{transactiondb['g_old-amount']}\n```", inline=True)
            embed.add_field(name="New Gifter Balance:", value=f"```fix\n{transactiondb['g_new-amount']}\n```", inline=True)
            embed.add_field(name="Fees:", value=f"```css\n{transactiondb['fees']}\n```", inline=False)
            if "refund" in transactiondb and transactiondb["refund"]:
                embed.add_field(name="Refunded:", value="Yes", inline=False)
            else:
                if await is_reseller(memebr):
                    selectOption.append(nextcord.SelectOption(label="Refund",value="refund-gift", emoji="💸"))
            
        selectOption.append(nextcord.SelectOption(label="Go Back",value="back", emoji="🔙"))
        await interaction.message.edit(embed=embed,view=sview(self.bot,properties_menu,memebr,180,selectOption,self.allist,self.filter,self.page,tr_id))
            
            
class properties_menu(nextcord.ui.Select):
    def __init__(self,bot:Bot,selectOption,allist,gfilter,page,tr_id):
        self.bot = bot
        self.allist = allist
        self.gfilter = gfilter
        self.page = page
        self.tr_id =tr_id
        
        super().__init__(placeholder="Select", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        page = self.page
        allist = self.allist
        gfilter = self.gfilter
        memebr = interaction.user    
        tr_id = self.tr_id  
        value = self.values[0]    
        
        if value == "back":
            await logs.transaction(self,interaction,memebr,page,allist,gfilter)
        elif value == "refund-add":
            
            
            embed = nextcord.Embed(title="Select Witch type of refund do you want", description="", color=Colour.red(), timestamp=timestamp,)
            await interaction.send(embed=embed,view=Refund_buttons(self.bot,tr_id))
        elif value == "refund-gift":
            embed = nextcord.Embed(title="Select Witch type of refund do you want", description="", color=Colour.red(), timestamp=timestamp,)
            await interaction.send(embed=embed,view=Refund_buttons(self.bot,tr_id))
            
            
class Refund_buttons(nextcord.ui.View):
    def __init__(self,bot:Bot,tr_id):
        super().__init__()
        self.value = None
        self.bot = bot 
        self.tr_id = tr_id
  
    @nextcord.ui.button(label="Refund", style=nextcord.ButtonStyle.red)
    async def Refund(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        datetime_utc = datetime.datetime.now(tz=tz)
        transactiondb = await db.sellsds.find_one({"_id":self.tr_id})
        baldb = await db.balancesdb.find_one({"userid":transactiondb["customerid"],"slot_id":transactiondb["slot_id"]})
        
        if baldb:
            
                
            customer = self.bot.get_user(transactiondb["customerid"])
            gifted_bal: int = transactiondb["gifted-amount"]
            current_bal: int = baldb["amount"]
            slot_id :int = transactiondb["slot_id"]
            new_bal = current_bal - gifted_bal
            
            await db.balancesdb.update_one({"userid":transactiondb["customerid"],"slot_id":transactiondb["slot_id"]}, {'$inc': {'amount': -gifted_bal}})
            removed = gifted_bal + new_bal
            predef = {
                "datetime":datetime_utc,
                "removerid" :interaction.user.id,
                "customerid":customer.id,
                "slot_id":slot_id,
                "note":f"refund TRID: {str(self.tr_id)}",
                "remove-amount":gifted_bal,
                "u_old-amount":current_bal,
                "u_new-amount":new_bal,
                "type":"remove",
                "addtype": transactiondb["type"]
            }
            log = nextcord.Embed(title="Transaction Refunded",  color=Colour.brand_red(), timestamp=timestamp,)
            log.add_field(name="Refunded TransactionID", value=f"```id\n{transactiondb['_id']}\n```", inline=True)
            log.add_field(name="SlotID:", value=f"```fix\n{transactiondb['slot_id']}\n```", inline=True)
            log.add_field(name="Amount refunded:", value=f"```css\n{removed}\n```", inline=False)
            
            
            if not new_bal >= 0:
                predef["missing"] = -new_bal
                log.add_field(name="Missing:", value=f"```fix\n{new_bal}\n```", inline=True)
                embed = embed_error("Error while Refund",f"Removed {prettify(removed)} of {prettify(gifted_bal)} commends, but {-new_bal} commends user dont have so now have negative balance\nNote: If u want report user for scam or other, just use /report")
            else:
                embed = embed_success("Successfully Refunded",f"Removed {prettify(gifted_bal)} commends from user: {customer.mention} - `{customer.id}`")
            log.add_field(name="Customer old balance:", value=f"```css\n{current_bal}\n```", inline=True)
            log.add_field(name="Customer new balance:", value=f"```fix\n{new_bal}\n```", inline=True)
            
            if "gift" == transactiondb["type"]:
                
                giftdb = await db.balancesdb.find_one({"userid":transactiondb["gifterid"],"slot_id":transactiondb["slot_id"]})
                if giftdb:
                    newgdb = await db.balancesdb.find_one_and_update({"userid":transactiondb["gifterid"],"slot_id":transactiondb["slot_id"]}, {'$inc': {'amount': +removed}},return_document=pymongo.ReturnDocument.AFTER)
                else:
                    newgdb = await create_bal(customer,interaction.user,slot_id,interaction.guild.id,removed) # mb problem when u insert to db u cant read values
                    
                predef["g_old-amount"] = giftdb["amount"]
                predef["g_new-amount"] = newgdb["amount"]
                log.add_field(name="Gifter old balance:", value=f"```css\n{giftdb['amount']}\n```", inline=False)
                log.add_field(name="Gifter new balance:", value=f"```fix\n{newgdb['amount']}\n```", inline=True)
            
                
            refdb = await db.sellsds.insert_one(predef)  
            log.add_field(name="TransactionID:", value=f"```id\n{refdb.inserted_id}\n```", inline=False)
            await db.sellsds.update_one({"_id":self.tr_id}, {'$set': {'refund': True,"refund_id":ObjectId(refdb.inserted_id)}})

            await interaction.send(embed=embed)
            await helpers.logembed(self,log,interaction.guild,slot_id)
            if await can_dm_user(customer):
                await customer.send(embed=log)
            if await can_dm_user(interaction.user):
                await interaction.user.send(embed=log)    
            
            
            
        else:
            await interaction.send(embed=embed_error("Unkown User","We cannot find user database"))
            
                
            


    @nextcord.ui.button(label="Refund&Report", style=nextcord.ButtonStyle.red)
    async def Refund_Report(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        datetime_utc = datetime.datetime.now(tz=tz)
        transactiondb = await db.sellsds.find_one({"_id":self.tr_id})
        baldb = await db.balancesdb.find_one({"userid":transactiondb["customerid"],"slot_id":transactiondb["slot_id"]})
        
        if baldb:
            
                
            customer = self.bot.get_user(transactiondb["customerid"])
            gifted_bal: int = transactiondb["gifted-amount"]
            current_bal: int = baldb["amount"]
            slot_id :int = transactiondb["slot_id"]
            new_bal = current_bal - gifted_bal
            
            await db.balancesdb.update_one({"userid":transactiondb["customerid"],"slot_id":transactiondb["slot_id"]}, {'$inc': {'amount': -gifted_bal}})
            removed = gifted_bal + new_bal
            predef = {
                "datetime":datetime_utc,
                "removerid" :interaction.user.id,
                "customerid":customer.id,
                "slot_id":slot_id,
                "note":f"refund TRID: {str(self.tr_id)}",
                "remove-amount":gifted_bal,
                "u_old-amount":current_bal,
                "u_new-amount":new_bal,
                "type":"remove",
                "addtype": transactiondb["type"]
            }
            log = nextcord.Embed(title="Transaction Refunded",  color=Colour.brand_red(), timestamp=timestamp,)
            log.add_field(name="Refunded TransactionID", value=f"```id\n{transactiondb['_id']}\n```", inline=True)
            log.add_field(name="SlotID:", value=f"```fix\n{transactiondb['slot_id']}\n```", inline=True)
            log.add_field(name="Refunded by:", value=f"{interaction.user.mention} - `{interaction.user.id}`", inline=False)
            log.add_field(name="Amount refunded:", value=f"```css\n{removed}\n```", inline=False)
            
            
            if not new_bal >= 0:
                predef["missing"] = -new_bal
                log.add_field(name="Missing:", value=f"```fix\n{new_bal}\n```", inline=True)
                embed = embed_error("Error while Refund",f"Removed {prettify(removed)} of {prettify(gifted_bal)} commends, but {-new_bal} commends user dont have so now have negative balance\nNote: If u want report user for scam or other, just use /report")
            else:
                embed = embed_success("Successfully Refunded",f"Removed {prettify(gifted_bal)} commends from user: {customer.mention} - `{customer.id}`")
            log.add_field(name="Customer old balance:", value=f"```css\n{current_bal}\n```", inline=True)
            log.add_field(name="Customer new balance:", value=f"```fix\n{new_bal}\n```", inline=True)
            
            if "gift" == transactiondb["type"]:
                
                giftdb = await db.balancesdb.find_one({"userid":transactiondb["gifterid"],"slot_id":transactiondb["slot_id"]})
                if giftdb:
                    newgdb = await db.balancesdb.find_one_and_update({"userid":transactiondb["gifterid"],"slot_id":transactiondb["slot_id"]}, {'$inc': {'amount': +removed}},return_document=pymongo.ReturnDocument.AFTER)
                else:
                    newgdb = await create_bal(customer,interaction.user,slot_id,interaction.guild.id,removed) # mb problem when u insert to db u cant read values
                    
                predef["g_old-amount"] = giftdb["amount"]
                predef["g_new-amount"] = newgdb["amount"]
                log.add_field(name="Gifter old balance:", value=f"```css\n{giftdb['amount']}\n```", inline=False)
                log.add_field(name="Gifter new balance:", value=f"```fix\n{newgdb['amount']}\n```", inline=True)
            
                
            refdb = await db.sellsds.insert_one(predef)  
            log.add_field(name="TransactionID:", value=f"```id\n{refdb.inserted_id}\n```", inline=False)
            await db.sellsds.update_one({"_id":self.tr_id}, {'$set': {'refund': True,"refund_id":ObjectId(refdb.inserted_id)}})

            await interaction.send(embed=embed)
            await helpers.logembed(self,log,interaction.guild,slot_id)
            if await can_dm_user(customer):
                await customer.send(embed=log)
            if await can_dm_user(interaction.user):
                await interaction.user.send(embed=log)    
            
            
            
        else:
            await interaction.send(embed=embed_error("Unkown User","We cannot find user database"))
    
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.stop()
    
            

class transactions_view(nextcord.ui.View):
        def __init__(self,bot:Bot,user,selectOption,page,allist,filter):
            super().__init__(timeout=180)
            self._user = user
            self.bot = bot 
            
            if selectOption and len(selectOption) !=0:
                self.add_item(properties(bot, selectOption,allist,filter,page))
            self.add_item(transactionfilter(bot, allist))
            
            self.add_item(left_tpage(bot, page,allist,filter))
            
            
            self.add_item(right_tpage(bot, page,allist,filter))
           
        async def on_timeout(self):
            print("transactions_view cccccccccccccccc")
            self.clear_items()
        async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
            if self._user is not None:
                variable = interaction.user == self._user
                if not variable:
                    embed=nextcord.Embed(title="error", description=f"**This `Selection` only can use {self._user.mention}**", color=nextcord.Colour.orange())
                    await interaction.send(embed=embed, ephemeral=True)
        
                return variable
            return True

class right_tpage(nextcord.ui.Button):
    def __init__(self, bot:Bot,page:int,allist,filter):
        self.bot = bot
        self.page = page
        self.allist = allist
        self.filter =filter

        super().__init__(
            emoji="➡️", style=nextcord.ButtonStyle.green
            
        )
        
    
    async def callback(self, interaction: nextcord.Interaction):    
        await logs.transaction(self,interaction,interaction.user,(self.page+1),self.allist,self.filter)
    
class left_tpage(nextcord.ui.Button):
    def __init__(self, bot:Bot,page:int,allist,filter):
        self.bot = bot
        self.page = page
        self.allist = allist
        self.filter =filter

        super().__init__(
            emoji="⬅️", style=nextcord.ButtonStyle.green
            
        )
        
    
    async def callback(self, interaction: nextcord.Interaction):    
        if not (self.page-1) < 0:
            
            await logs.transaction(self,interaction,interaction.user,(self.page-1),self.allist,self.filter)
        else:
            await logs.transaction(self,interaction,interaction.user,(self.page),self.allist,self.filter)





        
    
    

class transactionfilter(nextcord.ui.Select):
    def __init__(self,bot:Bot,glist):
        self.bot = bot
        self.glist = glist
        selectOption = [
            nextcord.SelectOption(label="Show All",value="all", emoji="📊"),
            nextcord.SelectOption(label="Show All Income",value="in", emoji="📈"),
            nextcord.SelectOption(label="Show All outgo",value="out", emoji="📉"),
            nextcord.SelectOption(label="Show Commend logs",value="commend", emoji="🟢"),
            nextcord.SelectOption(label="Show removed",value="remove", emoji="🔴"),
            nextcord.SelectOption(label="Show get commends via gift",value="gift1", emoji="🟣"),
            nextcord.SelectOption(label="Show gifts",value="gift2", emoji="🟠"),
            nextcord.SelectOption(label="Show get commends via add",value="add1", emoji="🔵"),
            nextcord.SelectOption(label="Show Added Balance",value="add2", emoji="🟡"),
            nextcord.SelectOption(label="Show Redeemed Balance",value="redeem1", emoji="🟤"),
            nextcord.SelectOption(label="Show Redeemed codes",value="redeem2", emoji="⚫"),
            nextcord.SelectOption(label="Filter User",value="userid", ),
  

        ]
        
        super().__init__(placeholder="Filter", min_values=1, max_values=len(selectOption), options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        filter = []
        if "in" not in self.values or "out" not in self.values:
                
            for value in self.values:
                if "all" == value:
                    filter = None
                    print("break")
                    break
                
                elif "in" == value:
                    filter.extend(["gift1","add1","redeem1","redeem2"])
                elif "out" == value:
                    filter.extend(["gift2","add2","remove","commend"])
                elif "userid" == value:
                    embed = nextcord.Embed(title="Please ping user/send user id in to chat", description="Please type in to chat", color=Colour.orange(), timestamp=timestamp,)
                    await interaction.send(embed=embed)
                    user,msg= await helpers.waitforrespon(self,interaction.channel,interaction.user,"user",60)
                    if user:
                        filter.append(f"userid-{user.id}")
                    
                    
                else:
                    filter.append(value)
        else:
            print("in/out")
            filter = None
        print(self.values)
        print(filter)
        await logs.transaction(self,interaction,interaction.user,(0),self.glist,filter)


class logs(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
        
    async def transaction(self,interaction:Interaction,member:User,page:int,allist:list, gfilter:list[str]=None):
        
        limit = 10 
        SelectOption = []
        
        print("in code")
        counting = 0
        if gfilter:
            userid = list(filter(lambda type: type.startswith("userid-"), gfilter))
            results = len(gfilter) - len(userid)
        else:
            results = 0  
            userid = []
            
        
        glist = []
        if  results != 0:
            
            
            if userid:
                userid = int(userid[0].split("-")[1])
                async for g in allist:
                    multi = []
                    
                    if g["customerid"] == userid or "sellerid" in g and g["sellerid"] == userid or "gifterid" in g and g["gifterid"] == userid:
                        print(userid)
                        if "type" in g:
                            if g["type"] == "add":
                                if g["customerid"] == member.id:
                                    multi.append("add1")
                                if g["sellerid"] == member.id:
                                    multi.append("add2")
                            elif g["type"] == "commend":
                                multi.append("commend")
                            elif g["type"] == "gift":
                                if g["customerid"] == member.id:
                                    multi.append("gift1")
                                if g["gifterid"] == member.id:
                                    multi.append("gift2")
                            elif g["type"] == "remove":
                                multi.append("remove")
                            elif g["type"] == "redeem":
                                if g["customerid"] == member.id:
                                    multi.append("redeem1")
                                if g["sellerid"] == member.id:
                                    multi.append("redeem2")
                        for name in multi:
                            if name in gfilter:
                                    
                                    glist.append(g)
            else:
                async for g in allist:
                    
                    multi = []
                    if "type" in g:
                        if g["type"] == "add":
                            if g["customerid"] == member.id:
                                multi.append("add1")
                            if g["sellerid"] == member.id:
                                multi.append("add2")
                        elif g["type"] == "commend":
                            multi.append("commend")
                        elif g["type"] == "gift":
                            if g["customerid"] == member.id:
                                multi.append("gift1")
                            if g["gifterid"] == member.id:
                                multi.append("gift2")
                        elif g["type"] == "remove":
                            multi.append("remove")
                        elif g["type"] == "redeem":
                            if g["customerid"] == member.id:
                                multi.append("redeem1")
                            if g["sellerid"] == member.id:
                                multi.append("redeem2")
                    for name in multi:
                        if name in gfilter:
                                
                                glist.append(g)
                    
                          
                  
                
        else:
            
            if userid:
                userid = int(userid[0].split("-")[1])
                async for g in allist:
                    if g["customerid"] == userid or "sellerid" in g and g["sellerid"] == userid or "gifterid" in g and g["gifterid"] == userid:
                        glist.append(g)
            else:
                glist = allist
                
            
        maxpages = int(len(glist) / limit)
        if maxpages < page:
            page -=1
        skip = limit * page    
        
        if skip != 0:
            glist = glist[skip:]
        
        glist = glist[:limit]
        
        
        
        desc = ""
        
        if len(glist) != 0:
            embed = nextcord.Embed(title="test transactions",description=desc)
            embed.set_footer(text=f"page: {page + 1}/{int(maxpages+1)}") 
            
            for transaction in glist:
                if "datetime" in transaction:
                    dt : datetime.datetime= transaction["datetime"].replace(tzinfo=datetime.timezone.utc)
                else:
                    dt : datetime.datetime= transaction["end-datetime"].replace(tzinfo=datetime.timezone.utc)
                    
                
                
                counting +=1
                
                if "type" in transaction:
                    if transaction["type"] == "add":
                        if  gfilter and  "add1" in  gfilter and "add2" not in gfilter or gfilter and  "add2" in  gfilter and "add1" not in gfilter:
                            if "add1" in gfilter:
                                customer = self.bot.get_user(transaction["sellerid"])
                                emoji = "🔵"
                                if "refund" in transaction or "refund" in transaction and transaction["refund"]:
                                    title = f"{emoji}・{counting}.  ❌Refunded - Get {transaction['gifted-amount']} from  {customer} "
                                else:
                                    title = f"{emoji}・{counting}. Get {transaction['gifted-amount']} from {customer}"
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{int(calendar.timegm(dt.timetuple()))}:f>", inline=False)
                                    
                                    
                            if "add2" in gfilter :
                                
                                customer = self.bot.get_user(transaction["customerid"])
                                emoji = "🟡"
                                if "refund" in transaction or "refund" in transaction and transaction["refund"]:
                                    title = f"{emoji}・{counting}. ❌Refunded - Add {transaction['gifted-amount']} to {customer}"
                                else:
                                    title = f"{emoji}・{counting}. Add {transaction['gifted-amount']} to {customer}"
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{int(calendar.timegm(dt.timetuple()))}:f>", inline=False)
                            
                        else:
                            if transaction["customerid"] == member.id :
                                customer = self.bot.get_user(transaction["sellerid"])
                                emoji = "🔵"
                                if "refund" in transaction or "refund" in transaction and transaction["refund"]:
                                    title = f"{emoji}・{counting}.  ❌Refunded - Get {transaction['gifted-amount']} from  {customer} "
                                else:
                                    title = f"{emoji}・{counting}. Get {transaction['gifted-amount']} from {customer}"
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{int(calendar.timegm(dt.timetuple()))}:f>", inline=False)
                                    
                                    
                            else:
                                
                                customer = self.bot.get_user(transaction["customerid"])
                                emoji = "🟡"
                                if "refund" in transaction or "refund" in transaction and transaction["refund"]:
                                    title = f"{emoji}・{counting}. ❌Refunded - Add {transaction['gifted-amount']} to {customer}"
                                else:
                                    title = f"{emoji}・{counting}. Add {transaction['gifted-amount']} to {customer}"
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{int(calendar.timegm(dt.timetuple()))}:f>", inline=False)
                                
                                
                    
                        
                        
                    elif transaction["type"] == "commend":
                        
                            if "steamID64" in transaction:
                                steamID64 = transaction["steamID64"]
                            else:
                                steamID64 = None 
                            emoji = "🟢"
                            title = f"{emoji}・{counting}. Commended {steamID64} with {transaction['commend-amount']} Commends"
                            embed.add_field(name=title, value=f"> CommendID: `{transaction['_id']}`\n> DateTime: <t:{calendar.timegm(dt.timetuple())}:f>", inline=False)

                    elif transaction["type"] == "gift":
                        if transaction["customerid"] == member.id :
                            
                                emoji = "🟣"
                                customer = self.bot.get_user(transaction["gifterid"])
                                if "refund" in transaction or "refund" in transaction and transaction["refund"]:
                                    title = f"{emoji}・{counting}. ❌Refunded - Get {transaction['gifted-amount']} from {customer} "
                                else:
                                    title = f"{emoji}・{counting}. Get {transaction['gifted-amount']} from {customer} "
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{calendar.timegm(dt.timetuple())}:f>", inline=False)
                                
                        else:
                                emoji = "🟠"
                                customer = self.bot.get_user(transaction["customerid"])
                                if "refund" in transaction or "refund" in transaction and transaction["refund"]:
                                    title = f"{emoji}・{counting}. ❌Refunded - Gifted {transaction['gifted-amount']} to {customer}"
                                else:
                                    title = f"{emoji}・{counting}. Gifted {transaction['gifted-amount']} to {customer}"
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{calendar.timegm(dt.timetuple())}:f>", inline=False)
                                
                    elif transaction["type"] == "remove":
                            emoji = "🔴"
                            title = f"{emoji}・{counting}. Removed {transaction['remove-amount']} Commends "
                            embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{calendar.timegm(dt.timetuple())}:f>", inline=False)
                    elif transaction["type"] == "redeem":
                        if  gfilter and  "redeem1" in  gfilter and "redeem2" not in gfilter or gfilter and  "redeem2" in  gfilter and "redeem1" not in gfilter:
                            if "redeem1" in gfilter:
                                emoji = "🟤"
                                seller = self.bot.get_user(transaction["sellerid"])
                                title = f"{emoji}・{counting}. Redeemed {transaction['gifted-amount']} from {seller}"
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{calendar.timegm(dt.timetuple())}:f>\n> Key: {transaction['code']}", inline=False)
                                
                            if "redeem2" in gfilter:
                                emoji = "⚫"
                                customer = self.bot.get_user(transaction["customerid"])
                                title = f"{emoji}・{counting}. {customer} Redeemed {transaction['gifted-amount']} "
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{calendar.timegm(dt.timetuple())}:f>\n> Key: {transaction['code']}", inline=False)
                            
                        else:
                            
                            if transaction["customerid"] == member.id :
                                emoji = "🟤"
                                seller = self.bot.get_user(transaction["sellerid"])
                                title = f"{emoji}・{counting}. Redeemed {transaction['gifted-amount']} from {seller}"
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{calendar.timegm(dt.timetuple())}:f>\n> Key: {transaction['code']}", inline=False)
                            else:
                                emoji = "⚫"
                                customer = self.bot.get_user(transaction["customerid"])
                                title = f"{emoji}・{counting}. {customer} Redeemed {transaction['gifted-amount']} "
                                embed.add_field(name=title, value=f"> TransactionID: `{transaction['_id']}`\n> DateTime: <t:{calendar.timegm(dt.timetuple())}:f>\n> Key: {transaction['code']}", inline=False)
                        
                    SelectOption.append(nextcord.SelectOption(label=f"{counting}. {transaction['_id']}",emoji=emoji,value=str(transaction['_id'])))
                            
            
        else:
            embed = nextcord.Embed(title="Transaction Logs", description="You dont have any transaction logs yet", color=Colour.orange(), timestamp=timestamp,) 
        
        
        print("enbd")   
        await interaction.message.edit(files=[],embed=embed,view=transactions_view(self.bot,interaction.user, SelectOption ,page,allist ,gfilter))        



def setup(bot: Bot) -> None:
    bot.add_cog(logs(bot))