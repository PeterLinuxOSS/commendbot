import datetime
from typing import Union

import nextcord
from key_generator.key_generator import generate
from nextcord import Colour, Interaction, SlashOption, TextChannel, User
from nextcord.ext import commands
from nextcord.ext.commands import Bot
from pymongo import ReturnDocument

import config
from cogs.helpers import *
from utils import *


class select_type_gen_slot(nextcord.ui.Select):
    def __init__(self,bot:Bot,keys:int,amount:int,price:float):
        self.bot = bot
        self.keys,self.amount,self.price = keys,amount,price
        selectOption = [
            nextcord.SelectOption(label="Use Slot balance(slot admin perm)",value="slot", emoji="🟠"),
            nextcord.SelectOption(label="Use wallet balance(reseller perm)",value="wallet", emoji="🟢"),
                        ]
        
        super().__init__(placeholder="Select Option", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        type = self.values[0]
        if type == "slot":
            amount =self.amount
            keys = self.keys
            selectOption,dbs = await find_slots(interaction.user,self.bot)
            if len(selectOption) == 1:
                slot_id = int(selectOption[0].value)
                await keygen.generate_keys(self,keys,amount,interaction,interaction.user,self.price,slot_id,False)
                
                
            
            elif len(selectOption) == 0:
                embed=nextcord.Embed(title="error", description="Only the **admin**/**developer**/**reseller** can use this command.", color=0xff0000)
                await interaction.send(ephemeral=True,embed=embed)
            
            else:
                embed=nextcord.Embed(title="Select Slot", description="Please select a slot for what u want generate keys", color=nextcord.Color.orange())
                await interaction.send(ephemeral=True,embed=embed,view=sview(self.bot,selectgenslot,interaction.user,180,selectOption,keys,amount,self.price))
        elif type == "wallet":
            amount =self.amount
            keys = self.keys
            
            description = "Please select a slot you would like gift balance from:\n\n"
            selectOption2 , description,slots_num = await find_wallets(interaction.user,(amount*keys),description)
            if slots_num == 1 and len(selectOption2) == 1:
                
                slot_id = int(selectOption2[0].value)
                await keygen.generate_keys(self,keys,amount,interaction,interaction.user,0,slot_id,True)
                
                
            
            elif slots_num == 0:
                embed=nextcord.Embed(title="error", description="Only the **admin**/**developer**/**reseller** can use this command.", color=0xff0000)
                await interaction.send(ephemeral=True,embed=embed)
            
            else:
                embed=nextcord.Embed(title="Select Wallet", description=description, color=nextcord.Color.orange())
                if slots_num != 1:
                    
                    await interaction.send(embed=embed, view = sview(self.bot,selectgenwallet,interaction.user,180,selectOption2,keys,amount),ephemeral=True)
                else:
                    await interaction.send(embed=embed, ephemeral=True)
            

class selectgenslot(nextcord.ui.Select):
    def __init__(self,bot:Bot, selectOption,keys:int,amount:int,price:float):
        self.bot = bot
        self.keys,self.amount,self.price = keys,amount,price
       
        
        super().__init__(placeholder="Select Slot", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        slot_id = int(self.values[0])
        await keygen.generate_keys(self,self.keys,self.amount,interaction,interaction.user,self.price,slot_id)
        
        
class selectgenwallet(nextcord.ui.Select):
    def __init__(self,bot:Bot, selectOption,keys:int,amount:int,):
        self.bot = bot
        self.keys,self.amount = keys,amount
       
        
        super().__init__(placeholder="Select Wallet", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        slot_id = int(self.values[0])
        await keygen.generate_keys(self,self.keys,self.amount,interaction,interaction.user,0,slot_id,True)
        

class keygen(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
        
    @nextcord.slash_command(
        name="redeem",
        description="redeem key/id",
        
        
    )
    async def redeem_command(self, interaction: Interaction,
        key: str = SlashOption(name="key", description="Your activation code", required=True),
    ):
        key.strip()
        keydb = await db.keysdb.find_one({"key":key})
        if keydb and "active" in keydb and keydb["active"]:
            await interaction.response.defer(ephemeral=False)
            await db.keysdb.update_one({"_id":keydb["_id"]},{'$set': {'active': False,"activatedby":interaction.user.id}})
            await keygen.redeem_bal(self,interaction,keydb)
            
        else:    
            
            embed=nextcord.Embed(title="Failure", description="The license key you entered is invalid/deactivated.", color=0xe74c3c)
            await interaction.response.send_message(embed=embed,ephemeral=True)
            
            
       
    @nextcord.slash_command(
        name="generate",
        description="generate keys",
        
        
    )
    async def generate_command(self, interaction: Interaction,
        keys: int = SlashOption(name="amount_of_keys", description="amount of key/s to generate(max. 25)", required=True),
        amount: int = SlashOption(name="amount_of_commends", description="amount of commends per/1 key", required=True),
        price: float = SlashOption(name="price", description="eta price for key/s", required=True),
        
    ):        
        selectOption,dbs = await find_slots(interaction.user,self.bot)
                
        reseller = await db.subdb.find_one({"ownerid":interaction.user.id,"disabled":False,"pay":True})
        if reseller and len(selectOption) != 0:
            embed=nextcord.Embed(title="Select Slot", description="Please select what type of commends do you want you", color=nextcord.Color.orange())
            await interaction.send(embed=embed,view=sview(self.bot,select_type_gen_slot,interaction.user,180,keys,amount,price),ephemeral=True)
        elif reseller and len(selectOption) == 0:
            description = "Please select a slot you would like gift balance from:\n\n"
            selectOption2 , description,slots_num = await find_wallets(interaction.user,(amount*keys),description)
            if slots_num == 1 and  len(selectOption2) == 1:
                await interaction.send("Generating,Please Wait!")
                slot_id = int(selectOption2[0].value)
                
                await keygen.generate_keys(self,keys,amount,interaction,interaction.user,0,slot_id,True)
                
                
            
            elif slots_num == 0:
                embed=nextcord.Embed(title="error", description="Only the **admin**/**developer**/**reseller** can use this command.", color=0xff0000)
                await interaction.send(embed=embed, ephemeral=True)
            
            else:
                
                embed=nextcord.Embed(title="Select Wallet", description=description, color=nextcord.Color.orange())
                if slots_num != 1:
                    await interaction.send(embed=embed,view = sview(self.bot,selectgenwallet,interaction.user,180,selectOption2,keys,amount) ,ephemeral=True)
                else:
                    await interaction.send(embed=embed,ephemeral=True)
                
                    
                
            
        
            
            
        else:
            if len(selectOption) == 1:
                await interaction.send("Generating,Please Wait!")
                slot_id = int(selectOption[0].value)
                await keygen.generate_keys(self,keys,amount,interaction,interaction.user,price,slot_id,False)
                
                
            
            elif len(selectOption) == 0:
                embed=nextcord.Embed(title="error", description="Only the **admin**/**developer**/**reseller** can use this command.", color=0xff0000)
                await interaction.send(embed=embed, ephemeral=True)
            
            else:
                embed=nextcord.Embed(title="Select Slot", description="Please select a slot for what u want generate keys", color=nextcord.Color.orange())
                await interaction.send(embed=embed,view=sview(self.bot,selectgenslot,interaction.user,180,selectOption,keys,amount,price),ephemeral=True)
               
    
        
            
            


    async def generate_keys(self,keys:int,amount:int,interaction:Union[Interaction,TextChannel],gifter:User,price:float,slot_id:int,wallet:bool=False):
        sub = await db.subdb.find_one({"ownerid":gifter.id}, sort=[("subtype", 1)])
        keysdb = await db.keysdb.count_documents({"gifterid":gifter.id,"active":True})
        datetime_utc = get_datetime_utc()  
        if sub:
            if sub["subtype"] == 3:
                keyslíimit = 0 
            elif sub["subtype"] == 2:
                keyslíimit = 20 
            elif sub["subtype"] == 1:
                keyslíimit = 250
            else:
                keyslíimit = 9999
            if keysdb < keyslíimit:
                
            
                if  0<= price:
                    if keys > 0:
                        if keys < 26:
                            if amount >= 10:
                                pay = False
                                if wallet:
                                    total_amount = amount * keys
                                    checkdb = await db.balancesdb.find_one({"userid":gifter.id,"slot_id":slot_id})
                                    if (checkdb["amount"] - total_amount) >= 0:
                                        baldb = await db.balancesdb.find_one_and_update({"userid":gifter.id,"slot_id":slot_id}, {"$inc": {"amount":-total_amount}},return_document=ReturnDocument.AFTER)
                                        pay = True
                                        await db.sellsds.insert_one({
                                                        "datetime":datetime_utc,
                                                        "customerid":gifter.id,
                                                        "slot_id":slot_id,
                                                        "note":f"generate {keys} keys with {amount}",
                                                        "remove-amount":total_amount,
                                                        "u_old-amount":(baldb["amount"]+total_amount),
                                                        "u_new-amount":baldb["amount"],
                                                        "type":"remove"
                                                    })  
                                    else:
                                        embed = nextcord.Embed(title="Error", description="You dont have enought balance", color=Colour.red(), timestamp=timestamp,)
                                        await interaction.send(ephemeral=True,embed=embed)
                                else:
                                    pay = True
                                if pay:
                                    keyslist = ""
                                    kdb = await db.keysdb.find({}).to_list(None)
                                    for i in range(0,keys):
                                        key = generate(4, ['-'], 5, 5, type_of_value = 'hex', capital = 'all').get_key()
                                        
                                        if not any( "key" in d and d['key'] == key for d in kdb):
                                            keyslist+= f"{key}\n"
                                            await db.keysdb.insert_one({"key":key,"amount":amount,"price":price,"slot_id":slot_id,"gifterid":gifter.id,"wallet":wallet,"active":True})
                                        else:
                                            key = generate(4, ['-'], 5, 5, type_of_value = 'hex', capital = 'all').get_key()
                                            if not any("key" in d and d['key'] == key for d in kdb):
                                                keyslist+= f"{key}\n"
                                                await db.keysdb.insert_one({"key":key,"amount":amount,"price":price,"slot_id":slot_id,"gifterid":gifter.id,"wallet":wallet,"active":True})
                                            else:
                                                key = generate(4, ['-'], 5, 5, type_of_value = 'hex', capital = 'all').get_key()
                                                if not any("key" in d and d['key'] == key for d in kdb):
                                                    keyslist+= f"{key}\n"
                                                    await db.keysdb.insert_one({"key":key,"amount":amount,"price":price,"slot_id":slot_id,"gifterid":gifter.id,"wallet":wallet,"active":True})
                                                
                                            
                                        
                                    await interaction.send(f"```\nGenerated {keys} keys with value {amount} commends per 1 key:\n{keyslist}```",ephemeral=True,)
                                    if await can_dm_user(interaction.user):
                                        await interaction.user.send(f"```\nGenerated {keys} keys with value {amount} commends per 1 key:\n{keyslist}```")
                            else:
                                await interaction.send("u cant set lower than 10 commends!",ephemeral=True,)
                        else:
                            await interaction.send("U cant generate more than 25 keys!",ephemeral=True,)
                else:
                    await interaction.send("U cant generate lower than 1 key!",ephemeral=True)
            else:
                await interaction.send("You reach maximal limit of keys for your sub",ephemeral=True)
        else:
            await interaction.send("You don't have activitie resell subscription.")
    async def redeem_bal(self,interaction:Interaction, keydb:dict,invisible:bool = False):
        datetime_utc = get_datetime_utc()  
        member = interaction.user
        gifter = self.bot.get_user(keydb["gifterid"])
        slot_id = keydb["slot_id"]
        amount = keydb["amount"]
        price = keydb["price"] if "price" in keydb else 0
        usertest = await db.balancesdb.find_one({"userid":member.id,"slot_id":slot_id})
        if isinstance(member, nextcord.Member) and member.guild:
            guild_id = member.guild.id
        else:
            guild_id = None
        
        if usertest is None:
            userdb = await db.usersdb.find_one({"userid":member.id})
            if not userdb :
                try:
                    await member.send(embeds=await helpers.welcom_message(self,member))
                    print("after embed")
                except Exception:
                    await db.usersdb.insert_one(user_template(member,False))
                else:
                    await db.usersdb.insert_one(user_template(member,True))
            
            oldamount= 0
            newamount = oldamount + amount
            
            
            await db.balancesdb.insert_one({"userid":member.id,"guildid":guild_id, "lastid":keydb["gifterid"], "amount":amount, "slot_id":slot_id,"today_used":0,"onhold":0,"active":True})
        else:
            oldamount = int(usertest["amount"])
            await db.balancesdb.update_one({"userid":member.id,"slot_id":slot_id}, {"$inc": {"amount":amount}})
                
            newamount = oldamount + amount
        
        sell = {
            "datetime":datetime_utc,
            "guildid":guild_id,
            "customerid":member.id,
            "sellerid":keydb["gifterid"],
            "slot_id":slot_id,
            "price":price,
            "gifted-amount":amount,
            "u_old-amount":oldamount,
            "u_new-amount":newamount,    
            "type":"redeem",
            "wallet":keydb["wallet"],
            "code":keydb["key"]
        }
        selldb = await db.sellsds.insert_one(sell)
        
        
        embed=nextcord.Embed(title="Balance added via redeem!", description="User redeem the key/id", color=Colour.brand_green(), timestamp=datetime.datetime.now())
        embed.add_field(name="TransactionID", value=selldb.inserted_id, inline=False)
        embed.add_field(name="Balance added to:", value=member.mention, inline=False)
        embed.add_field(name="Balance added by:", value=(gifter.mention if gifter else keydb["gifterid"]) , inline=False)
        embed.add_field(name="Amount added:", value=f"{amount} commends", inline=False)
        embed.add_field(name="User's old balance:", value=f"{oldamount} commends", inline=False)
        embed.add_field(name="User's new balance:", value=f"{newamount} commends", inline=False)
        
        embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
        await interaction.send(embed=embed,ephemeral=invisible)
        embed.add_field(name="Code used:", value=keydb["key"], inline=False)
        
        
        if await can_dm_user(member):
            try:
                await member.send(embed=embed)
            except Exception:
                pass
        embed.add_field(name="Wallet Type", value=keydb["wallet"], inline=False)
        embed.add_field(name="Price:", value=f"{price}€", inline=False)
        await helpers.logembed(self,embed,interaction.guild,slot_id)
        
        
        await db.slotsdb.update_one({"_id":slot_id}, {"$inc": {"price": price,"price-count":1}})
        

def setup(bot: Bot) -> None:
    bot.add_cog(keygen(bot)) 