

import datetime
import math
import re
import secrets
import string
from decimal import Decimal
from itertools import cycle
from typing import Tuple, Union

import asyncstdlib as a
import nextcord
import pytz
from nextcord import Colour, Embed, Member, User
from nextcord.ext.commands import Bot
from pymongo import results
from steam import steamid
from termcolor import cprint

import config
import utils.translates as translates
from utils.mongodb import *

alphabet = string.ascii_letters + string.digits
OWNERID = config.OWNER_ID
Any = object()
GuildChannel = Union[nextcord.VoiceChannel, nextcord.StageChannel, nextcord.TextChannel, nextcord.CategoryChannel, nextcord.ForumChannel]
input_data = {0: 0, 0.35: 50, 0.55: 100, 1.2: 250, 1.75: 500, 3.5: 1000, 5.8: 2000, 9: 5000}
class _MissingSentinel:
    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    def __bool__(self):
        return False

    def __repr__(self):
        return "..."


checklist = []


MISSING = _MissingSentinel()
cet = pytz.timezone("Europe/Bratislava")
TESTING_GUILD_ID = config.TESTING_GUILD_IDS
# Staff shown at the top of the commend queue, keyed by Discord user id.
queue_vip = {admin_id: {"role": "Staff"} for admin_id in config.ADMIN_IDS}
queue_vip[config.OWNER_ID] = {"role": "Owner/Dev"}

servers = best_server = f'"`{config.GAME_SERVER_CONNECT}`"'

vps_value = {
    "vps_ip": config.VPS_HOST,
    "vps_user": config.VPS_USER,
    "vps_pass": config.VPS_PASS,
}


def feescalc(amount) ->int:
    fees = math.ceil(1 if amount <=25 else  amount /100*2)
    return fees

local_tz = pytz.timezone('Europe/Paris')
def utc_to_local(utc_dt:datetime.datetime):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(cet)
    return cet.normalize(local_dt)

mail_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

def remove_exponent(d):
    """Remove exponent."""
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()





def convert_value(value):
  """Converts a value based on the provided input data scheme.

  Args:
    value: The input value to be converted.

  Returns:
    The converted output value based on the input data scheme.
    If the value is not found in the scheme, a linear interpolation
    between the closest values is performed. For values higher than
    the highest key in the scheme, the maximum output value is used.
  """

  if value in input_data:
    return input_data[value]
  elif value > max(input_data.keys()):
    max_price = max(input_data.keys())
    max_amount = input_data[max_price]
    return int((max_amount/max_price)*value)
   
    
  else:
    # Find the two closest keys in the input data
    sorted_keys = sorted(input_data.keys())
    lower_key = max(key for key in sorted_keys if key <= value)
    upper_key = min(key for key in sorted_keys if key >= value)

    # Perform linear interpolation
    lower_value = input_data[lower_key]
    upper_value = input_data[upper_key]
    slope = (upper_value - lower_value) / (upper_key - lower_key)
    return int(lower_value + slope * (value - lower_key))


def extract_information(message:str):
    message = message.replace('\\', '')
    pattern = r"(\d+)\.\s+@([^ :]+)\s*:\s*(\d+)\s*\((.+?)\)"
    match = re.match(pattern, message)

    if match:
        count = int(match.group(1))
        username = match.group(2)
        user_id_str = match.group(3)
        reason = match.group(4)
        
        # Extract numeric user ID
        user_id_match = re.search(r'\d+', user_id_str)
        user_id = int(user_id_match.group()) if user_id_match else None

        return count, username, user_id, reason
    else:
        return None,None,None,None

def millify(n, precision=1, drop_nulls=True, prefixes=[]):
    """Humanize number."""
    millnames = ['', 'k', 'M', 'B', 'T', 'P', 'E', 'Z', 'Y']
    if prefixes:
        millnames = ['']
        millnames.extend(prefixes)
    n = float(n)
    millidx = max(0, min(len(millnames) - 1,
                         int(math.floor(0 if n == 0 else math.log10(abs(n)) / 3))))
    result = '{:.{precision}f}'.format(n / 10**(3 * millidx), precision=precision)
    if drop_nulls:
        result = remove_exponent(Decimal(result))
    return '{0}{dx}'.format(result, dx=millnames[millidx])

def prettify(amount, separator=','):
    """Separate with predefined separator."""
    orig = str(amount)
    new = re.sub("^(-?\d+)(\d{3})", "\g<1>{0}\g<2>".format(separator), str(amount))
    if orig == new:
        return new
    else:
        return prettify(new)

def sub_types(num:int) -> str:
    dl = {0:"Local",1:"Premium",2:"Standard - Server",3:"Standard - Personal",4:"Free",None:None}
    return dl[num]
    

async def find_wallets(user:User,amount:int,description:str) -> Tuple[list[nextcord.SelectOption],str,int] :
    gifterbalances =  db.balancesdb.find({"userid":user.id})
    slotlist = await db.slotsdb.find({}).to_list(length=None)
    selectOption = []
    
    count = 0
    async for count,balanced in a.enumerate(gifterbalances,1):
        
        slotdb = list(filter(lambda i: i['_id'] == balanced["slot_id"], slotlist))[0]
        
        slot_id  =slotdb["_id"]
        newamountg = balanced["amount"] -amount
        
        if not newamountg  < 0:
            
            if slotdb["enable"]:
                description +=  f"{config.EMOJI_YES} {count}. **{str(slotdb['name'])}** slot — **{balanced['amount']}** commends\n" 
                selectOption.append(nextcord.SelectOption(label=f"{count}. {slotdb['name']}" ,value=slot_id ))
            else:
                description +=  f"⛔ {count}. ~~**{str(slotdb['name'])}** slot — **{balanced['amount']}** commends~~ — __**Slot is Disabled!**__\n" 
                selectOption.append(nextcord.SelectOption(label=f"{count}. {slotdb['name']}" ,value=slot_id ,))
        else:
            description +=  f"{config.EMOJI_NO} {count}. ~~**{str(slotdb['name'])}** slot — **{balanced['amount']}** commends~~ — __**Not enough balance!**__\n" 
        
    return selectOption, description, count


async def find_slots(user:User,bot:Bot) -> Tuple[list[nextcord.SelectOption],list[dict]] : 
    if user.id == bot.owner_id:
        slotsdb = db.slotsdb.find({})
    else:
        slotsdb = db.slotsdb.find({"admins":[user.id]})

    id = 0
    selectOption = []    
    async for slotdb in slotsdb:
         
        slot_id  =slotdb["_id"]
        selectOption.append(nextcord.SelectOption(label=f"{id+1}. {slotdb['name']}" ,value=slot_id ))
        id+=1
    return selectOption,slotsdb

emojilist = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "🟤", "⚫", "⚪"]
    

def get_rules() -> Embed:
    rules = (
        "1. Abusing bot bugs to gain an unfair advantage is strictly prohibited. \n"
        "2. Reselling our product without a resell subscription (`/mysubscriptions`) is not allowed.\n"
        "3. Copying our bot and bot patents is strictly prohibited.\n"
        "4. Abusing bot errors to disrupt the server is not allowed.\n"
        "5. Spamming commands is not allowed as it may affect the bot's performance.\n"
        "6. The bot is intended to serve all members and their needs. \n"
        "7. Disrespecting server staff, insulting server moderators, or becoming belligerent after being warned or blacklisted is not allowed. \n"
        "8. Engaging in illegal activities or discussions is not allowed.\n"
        "9. Undermining the server's reputation or credibility is prohibited.\n"
        "10. Commending your own/bought accounts to resell them later is strictly prohibited.\n"
        "11. Reselling or giving commends to friends without permission is not allowed. \n > If you would like to give commends to your friends, please invite them to our server and use the `/giftbalance` command to transfer balance to their Discord account.\n"
        f"12. {config.BRAND_NAME} admins are allowed to change the rules based on the situation's severity. \n"
        "13. To unlock DMs for our CommendBot. \n > Please note that we cannot process commands and commend process if you have Discord DMs locked. \n > Kindly ensure that your Discord DMs are accessible for the CommendBot to function correctly.\n"
            
    )
    embedg=Embed(title="CommendBot Rules", description=rules, color=0xf27107)
    embedg.add_field(name="If you are caught abusing any of these or casual ones you will face the consequences of being blacklisted and u ll lose your current balance!", value="using this bot you **accepting** with rules", inline=False)
    embedg.set_footer(text=f'{config.BRAND_FOOTER} - Updated on 22.7.2023.',icon_url=config.BRAND_LOGO_URL)
    return embedg

def howitworksemb(lang : dict,getserver: list,steamid: int) -> Embed:
    if getserver is None:
        cprint("COMMEND SERVER IS NONE!!!!!!!!!!!!!!!!!!!","red")
        return None
    embed=nextcord.Embed(color=0xff0000)
    
    embed.set_thumbnail(url=config.BRAND_LOGO_URL)
    embed.add_field(name=lang["howitworkis-field1-title"], value=lang["howitworkis-field1-description"], inline=False)
    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL)
    return embed


def get_panel_login(name) -> Tuple[str,str]:
    login = "".join(char for char in str(name) if char.isalnum())
    password = ''.join(secrets.choice(alphabet) for i in range(8))
    
    return login, password


class pview(nextcord.ui.View):
        def __init__(self,bot:Bot,item: nextcord.ui.Select,item2: nextcord.ui.Select,item3: nextcord.ui.Select,item4: nextcord.ui.Select,user:nextcord.User | nextcord.Member,timeout = None, *args):
            super().__init__(timeout=timeout)
            self._user = user
            self.bot = bot 
            
            
             
            
        
            print(len(args))
            
            args1 = []
            args2 = []
            listargs = cycle([1,2])
            for arg in args:
                number = next(listargs)
                if int(number) == 1:
                    args1.append(arg)
                else:
                    args2.append(arg)
                    
                
                
            self.add_item(item(bot))
            self.add_item(item4(bot,translates.eng,"commend"))
            self.add_item(item2(bot, *args2))
            self.add_item(item3(bot,))
            
        async def on_timeout(self):
            
            
            print("pview ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
            self.clear_items()
        async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
            if self._user is not None:
                variable = interaction.user == self._user
                if not variable:
                    embed=nextcord.Embed(title="error", description=f"**This `Selection` only can use {self._user.mention}**", color=nextcord.Colour.orange())
                    await interaction.send(embed=embed, ephemeral=True)
        
                return variable
            return True


class mview(nextcord.ui.View):
        def __init__(self,bot:Bot,item: nextcord.ui.Select,item2: nextcord.ui.Select,user:nextcord.User | nextcord.Member,timeout = None, *args):
            super().__init__(timeout=timeout)
            self._user = user
            self.bot = bot 
            
            
             
            
        
            print(len(args))
            
            args1 = []
            args2 = []
            listargs = cycle([1,2])
            for arg in args:
                number = next(listargs)
                if int(number) == 1:
                    args1.append(arg)
                else:
                    args2.append(arg)
                    
                
                
            self.add_item(item(bot, *args1))
            self.add_item(item2(bot, *args2))
        async def on_timeout(self):
            
            
            print("mview ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
            self.clear_items()
        async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
            if self._user is not None:
                variable = interaction.user == self._user
                if not variable:
                    embed=nextcord.Embed(title="error", description=f"**This `Selection` only can use {self._user.mention}**", color=nextcord.Colour.orange())
                    await interaction.send(embed=embed, ephemeral=True)
        
                return variable
            return True

class sview(nextcord.ui.View):
        def __init__(self,bot:Bot,item: nextcord.ui.Select,user:nextcord.User | nextcord.Member,timeout:float | None = None, *args):
            super().__init__(timeout=timeout)
            self._user = user
            self.bot = bot 
            
             
            
        
            print(len(args))
            self.add_item(item(bot, *args))
        async def on_timeout(self):
            self.clear_items()
            
        async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
            if self._user is not None:
                variable = interaction.user == self._user
                if not variable:
                    embed=nextcord.Embed(title="error", description=f"**This `Selection` only can use {self._user.mention}**", color=nextcord.Colour.orange())
                    await interaction.send(embed=embed, ephemeral=True)
        
                return variable
            return True
        
        



class wview(nextcord.ui.View):
        def __init__(self,item: nextcord.ui.Select,user:nextcord.User | nextcord.Member, timeout:float | None = 120,*args):
            super().__init__(timeout=timeout)
            self._user = user
            
            
             
            
        
            
            self.add_item(item( *args))
        async def on_timeout(self):
            print("wview ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc")
            self.clear_items()
        async def interaction_check(self, interaction: nextcord.Interaction) -> bool:
            if self._user is not None:
                variable = interaction.user == self._user
                if not variable:
                    embed=nextcord.Embed(title="error", description=f"**This `Selection` only can use {self._user.mention}**", color=nextcord.Colour.orange())
                    await interaction.send(embed=embed, ephemeral=True)
        
                return variable
            return True
 

async def delete_autodelete(channel:Union[nextcord.TextChannel,int] ):
    """if isinstance(user,int):
        user_id = user
    else:
        user_id = user.id"""
    if isinstance(channel,int):
        channel_id = channel
    else:
        channel_id = channel.id
    await db.timedb.delete_one({"channelid":channel_id})
    
    
 
       
def emebd_remove(customer: User | Member , admin : User | Member ,amount,oldamount,newamount,onhold) -> Embed:        
    embed=nextcord.Embed(title="Balance was add to on_hold!", description="Balance has been removed to the user.", color=Colour.orange(), timestamp=datetime.datetime.now())
    embed.add_field(name="Balance removed to:", value=customer.mention, inline=False)
    embed.add_field(name="Balance removed by:", value=admin.mention , inline=False)
    embed.add_field(name="Amount add to onhold:", value=f"{amount} commends", inline=False)
    embed.add_field(name="Onhold balance", value=f"{onhold} commends", inline=False)
    embed.add_field(name="User's old balance:", value=f"{oldamount} commends", inline=False)
    embed.add_field(name="User's new balance:", value=f"{newamount} commends", inline=False)
    embed.set_footer(text=config.BRAND_FOOTER,icon_url=config.BRAND_LOGO_URL) 
    return embed
        
async def can_dm_user(user: nextcord.User) -> bool:
    """Probe whether the bot may DM ``user`` without actually sending anything.

    ``send()`` with no payload always fails: Forbidden when DMs are closed,
    HTTPException (empty message) when they are open. That distinction is the
    whole check.
    """
    return_value = None
    if user.id in config.NO_DM_USER_IDS:
        # Known service accounts - skip the probe entirely.
        return None

    ch = user.dm_channel
    if ch is None:
        try:
            ch = await user.create_dm()
        except nextcord.Forbidden:
            return True
        except Exception:
            
            return  False
        
    
    try:
        await ch.send()
    except nextcord.Forbidden:
        return_value = False
    except nextcord.HTTPException:
        return_value = True 

       
    
    return return_value    
        
    
    

# Guild sort order for the "where can I buy" listing: the support guild first,
# then the slot guild, then the guilds with a custom storefront, then the rest.
# The original spelled this out as an if/elif chain that listed the slot guild
# twice, so one branch was unreachable.
GUILD_PRIORITY = [
    config.SUPPORT_GUILD_ID,
    config.SLOT_GUILD_ID,
    *config.CUSTOM_WELCOME_GUILD_IDS,
]
_UNRANKED = len(GUILD_PRIORITY)


def _guild_rank(guild_id: int) -> int:
    try:
        return GUILD_PRIORITY.index(guild_id)
    except ValueError:
        return _UNRANKED


def favoriteguilds(guild: nextcord.Guild) -> int:
    return _guild_rank(guild.id)


def favoriteguildsdb(db) -> int:
    return _guild_rank(db["guildid"])


def get_steamID64(steamlink:str) -> int:
    if len(str(steamlink)) == 17:
        try:
            steamID64 = int(steamlink)
        except Exception:
            return None
        else:
            return steamID64

    elif "/id/" in steamlink or "/profiles/"  in steamlink:
                                                
        try:    
            urls = steamid.steam64_from_url(steamlink, http_timeout=80)
        except Exception:
            return None
        else:
            return urls
    else:
        return None

timestamp = datetime.datetime.now()
def get_datetime_utc():
    return datetime.datetime.now(datetime.timezone.utc)

def find_command(bot:Bot,command_name:str):
    

    if   value:=bot.global_commands.get(command_name):
        return f"</{command_name}:{value}>"
    else:
        return f"/{command_name}"


bluepr = 0x0a8f82
tz = datetime.timezone(datetime.timedelta(hours=0))
tzsk = datetime.timezone(datetime.timedelta(hours=2))
as_variable_td = datetime.datetime.now(tz=tz)  

def user_template(member:User | int,rules:bool=False,points:int=0,reseller:bool=False,language="eng",free:bool=False) -> dict: 
    if isinstance(member,int):
        login,pwd = get_panel_login(member)
        return {"userid":member.id, "rules":rules, "created":datetime.datetime.now(tz=tz),"points":points,"won":0,"drop":0,"daily":0,"reseller":reseller,"login":login,"password":pwd,"expire":datetime.datetime(1,1,1,1,1,1,1,tzinfo=tz),"u_rules":rules,"tr212_promo":0,"language":language,"count":0,"usersInvited":[],"free":free}
        
    else:    
        login,pwd = get_panel_login(member.name)
        return {"userid":member.id, "rules":rules, "created":datetime.datetime.now(tz=tz),"points":points,"won":0,"drop":0,"daily":0,"reseller":reseller,"login":login,"password":pwd,"expire":datetime.datetime(1,1,1,1,1,1,1,tzinfo=tz),"u_rules":rules,"tr212_promo":0,"language":language,"count":0,"usersInvited":[],"free":free}


logo = config.BRAND_LOGO_URL
server_name = config.BRAND_NAME
async def create_bal(customer:User,gifter:User,slot_id:int,guild_id:int=None,balance:float=0.0,) -> results.InsertOneResult:
    datetime_utc = datetime.datetime.now(tz=tz)
    baldb = await db.balancesdb.insert_one({"userid":customer.id,"guildid":guild_id, "lastid":gifter.id, "amount":balance, "slot_id":slot_id,"today_used":0,"onhold":0,"datetime":datetime_utc,"active":True})
    userdb = await db.usersdb.find_one({"userid":customer.id})
    if not userdb:
        await db.usersdb.insert_one(user_template(customer,True))
    return baldb

async def is_reseller(user:User,pay:bool = True) -> bool:
    sub =await db.subdb.find_one({"ownerid":user.id,"disabled":False,"pay":pay})
    if sub:
        return True
    else:
        return False
   
   

subdecoder = {4:"Free",3:"Standard-Personal",2:"Standard-Server",1:"Premium",0:"Local"}
    
async def is_slot_admin(user:User,slot_id:int) -> bool:
    is_admin = False
    if user.id != OWNERID:
        slot = await db.slotsdb.find_one({"_id":slot_id,"admins":{ "$in":[user.id] }})
        if slot:
            is_admin = True
    else:
        is_admin = True
    return is_admin
    

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        
        return False
 
def get_user_avatar(user: Member | User ):
    if    user.avatar:
            return user.avatar.url
    else:
            return user.default_avatar.url   
    
def convert_lang(lang):
    if lang =="eng":
        return translates.eng
    elif lang =="sk":
        return translates.sk
    elif lang =="hu":
        return translates.hu
    elif lang =="ger":
        return translates.ger
    elif lang == "pt":
        return translates.pt
    elif lang == "pl":
        return translates.pl
    else:
        return translates.eng
    

async def get_lang(langdb=None,guild: nextcord.Guild =None ):
    if langdb is None:
        if guild is None:
            return translates.eng
        else:
            guildssetup = await db.guildsetting.find_one({"default_lang":{"$exists":True},"guildid":guild.id})
            if guildssetup:
                lang = guildssetup["default_lang"]
                if lang =="eng":
                    return translates.eng
                elif lang =="sk":
                    return translates.sk
                elif lang =="hu":
                    return translates.hu
                elif lang =="ger":
                    return translates.ger
                elif lang == "pt":
                    return translates.pt
                elif lang == "pl":
                    return translates.pl
                else:
                    print(f"Incorrect langauge(guild: {guild}) {lang}")
                    return translates.eng
            else:
                return translates.eng

    else:
        lang = langdb["language"]
        if lang is not None:

            if lang =="eng":
                return translates.eng
            elif lang =="sk":
                return translates.sk
            elif lang =="hu":
                return translates.hu
            elif lang =="ger":
                return translates.ger
            elif lang == "pt":
                return translates.pt
            elif lang == "pl":
                    return translates.pl
            else:
                print(f"Incorrect langauge {lang}")
                return translates.eng
        else:
            return translates.eng