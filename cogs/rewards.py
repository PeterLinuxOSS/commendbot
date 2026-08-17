import datetime

import asyncstdlib as a
import nextcord
import pymongo
from nextcord import Colour, Embed, Guild, Interaction, SelectOption, SlashOption
from nextcord.ext import commands
from nextcord.ext.commands import Bot

import config
from cogs.helpers import helpers
from utils import bluepr, db, get_lang, get_user_avatar, sview, timestamp

rewardslist = {1:{"name":"Steam RBot 1day", "description":"Steam ReportBot license for 1day","price":40,"stock":999},
               2:{"name":"1,5k Instagram Likes", "description":"1,5k Instagram Likes","price":85,"stock":999},
               3:{"name":"1 Week Report-Bot access", "description":"Steam ReportBot license for 1month","price":100,"stock":999},
               4:{"name":"25 csgo commends", "description":"CS:GO commends","price":150,"stock":5,"amount":50},
               5:{"name":"1 csgo Rankup", "description":"1 csgo mm rankup from any rank via VertigoBoosting","price":300,"stock":999},
               #6:{"name":"5 wm wins in csgo", "description":"5 prime wins wingman in csgo","price":200,"stock":999},
 
}

class rewards_menu(nextcord.ui.Select):
    def __init__(self, bot:Bot, options:list[SelectOption]):
        self.bot = bot
        super().__init__(
            placeholder="Choose what u want to buy...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: Interaction):
        user = interaction.user 
        guildf = list(filter(lambda i : i.id == config.SUPPORT_GUILD_ID, user.mutual_guilds))
       
        if len(guildf) == 1:
            guild :Guild = guildf[0]
            id = int(self.values[0])
            productdb = rewardslist[id]
            langdb  = await db.usersdb.find_one({"userid":user.id})
            lang = await get_lang(langdb,interaction.guild)
            msg =lang["commendbotbutton-msg"]
            await interaction.send(msg,ephemeral=True )
            other = nextcord.utils.get(guild.categories, id=config.REWARD_CATEGORY_ID)
            overwrites = {guildf[0].default_role: nextcord.PermissionOverwrite(read_messages=False)}
            channel  = await guild.create_text_channel(name=f'📂・r-{user.name}' ,category=other,overwrites=overwrites)
            await channel.edit(sync_permissions=True)
            await channel.set_permissions(user, send_messages=True, view_channel=True, read_messages=True,use_slash_commands=True,read_message_history=True)
            await interaction.edit_original_message(content=f'{user.mention} {lang["commendbotbutton-msg-edit"]} {channel.mention}')
            userdb = await db.usersdb.find_one({"userid":user.id})
            points = int(userdb["points"])
            if points >=productdb["price"]:
                embed = nextcord.Embed(title="Get your reward", color=bluepr, timestamp=datetime.datetime.now())
                embed.add_field(name="Product_ID", value=id, inline=True)
                embed.add_field(name="Product_Name", value=productdb["name"], inline=True)
                embed.add_field(name="Product_price", value=productdb["price"], inline=True)
                embed.add_field(name="Product_Stock", value=productdb["stock"], inline=True)
                embed.add_field(name="User old_balance", value=int(points), inline=True)
                
                await channel.send(content=user.mention,embed=embed)
                await db.usersdb.update_one({"userid":user.id}, {"$inc":{"points":-productdb["price"]}})
                if id == 1:
                    pass
                elif id == 2:
                    pass 
                elif id == 3:
                    pass 
                elif id == 4:
                    mydb = await db.balancesdb.find_one({"userid":config.OWNER_ID})
                    owner = self.bot.get_user(self.bot.owner_id)
                    await helpers.giftbal(self,True,mydb,productdb["amount"],channel,owner,user,guild)
                elif id == 5:
                    await channel.send(f"wait for <@{self.bot.owner_id}> 1 mm rankup")
                elif id == 6:
                    await channel.send(f"wait for <@{self.bot.owner_id}> 10 p mm wins")
            else:
                await channel.send(content=f"{user.mention}- you dont have enought points to buy product")
           
        
        else:
            await interaction.response.send_message(f"To get your reward, just [join]({config.BRAND_DISCORD_URL}) in to server {config.BRAND_DISCORD_URL} verify, make ticket and ping developer or managers!(02.07.2022 ll be it fully automatic!)",ephemeral=True)
   


    
class rewards(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
        
    @nextcord.slash_command(name="leaderboard",description="CommendBot score leaderboard")
    async def  leaderboard_command(self, interaction: Interaction,
        option: str=SlashOption("type",required=True,choices=["rewards","commends"])):
        if option == "rewards":
            
            users =  db.usersdb.find({"points":{"$gt":0}}).sort("points",pymongo.DESCENDING)
            leaderboard = ""
            count = 0 
            curpos = None
            async for user in users:
                if count < 10:
                    userg = self.bot.get_user(user["userid"])
                    if userg:
                        count+=1
                        number = "🥇" if count == 1 else "🥈" if count == 2 else "🥉" if count == 3 else f"`{count}`."
                        leaderboard += f"{number} **{str(userg)}** `{int(user['points'])}`**✰** \n"
                else:
                    count+=1
                    
                if user['userid'] == interaction.user.id:
                    curpos = count
                    curdb = user
            if curpos:
                embed = nextcord.Embed(title="Leaderboard", description=f"Your position is `{curpos}` with **{int(curdb['points'])}** points", color=Colour.gold(), timestamp=timestamp,)
            else:
                embed = nextcord.Embed(title="Leaderboard", description="Your position is `∞` with 0 points", color=Colour.gold(), timestamp=timestamp,)
            embed.add_field(name="Top 10 Leaderboard", value=leaderboard, inline=False)
            await interaction.send(embed=embed)
        
        elif option == "commends":
            leaderboard = ""
            users = db.balancesdb.find({}).sort("amount",pymongo.DESCENDING)
            curpos = None
            async for  id,user in a.enumerate(users,1):
                userg = self.bot.get_user(user["userid"])
                if id < 25:
                    number = "🥇" if id == 1 else "🥈" if id == 2 else "🥉" if id == 3 else f"`{id}`."
                    if userg:
                        
                        leaderboard += f"{number} **{str(userg)}** `{int(user['amount'])}`**✰** \n"
                    else:
                        leaderboard += f"{number} **{user['userid']}** `{int(user['amount'])}`**✰** \n"
                if user['userid'] == interaction.user.id:
                    curpos = id
                    curdb = user
                    if id < 25:
                        break
            if curpos:
                embed = nextcord.Embed(title="Leaderboard", description=f"Your position is `{curpos}` with **{int(curdb['amount'])}** commends", color=Colour.gold(), timestamp=timestamp,)
            else:
                embed = nextcord.Embed(title="Leaderboard", description="Your position is `∞` with 0 commends", color=Colour.gold(), timestamp=timestamp,)
            embed.add_field(name="Top 10 Leaderboard", value=leaderboard, inline=False)
            await interaction.send(embed=embed)
                
                
         
    @nextcord.slash_command(name="rewards")
    async def  rewards_command(self, interaction: Interaction):
        
        
        description = ""
        userdb = await db.usersdb.find_one({"userid":interaction.user.id})
        if userdb:
            points = int(userdb["points"])
        else:
            points = 0 
        options = [ ]
        
        for id,rewarddb in rewardslist.items():
            if points >= rewarddb["price"]:
                
                
                if rewarddb["stock"] > 0: 
                    description+= f'**{rewarddb["name"]}**({rewarddb["stock"]}) — [✰ {rewarddb["price"]}]({config.BRAND_URL}) **|** {config.EMOJI_YES}\n{rewarddb["description"]}\n\n'
                    options.append(nextcord.SelectOption(label=rewarddb["name"], value=id))
                    
                else:
                    description+= f'**{rewarddb["name"]}**({rewarddb["stock"]}) — [✰ {rewarddb["price"]}]({config.BRAND_URL}) **|** {config.EMOJI_NO}\n{rewarddb["description"]}\n\n'
            else:
                description+= f'**{rewarddb["name"]}**({rewarddb["stock"]}) — [✰ {rewarddb["price"]}]({config.BRAND_URL}) **|** {config.EMOJI_NO}\n{rewarddb["description"]}\n\n'
        embed=Embed(title="Rewads shop", description=description, color=nextcord.Colour.dark_gold())  
        embed.add_field(name="Donators 💸", value="\n".join(f"{i}. {name}" for i, name in enumerate(config.DONATORS, 1)), inline=True)  
        embed.set_footer(text=f"{interaction.user.name} | ❌ .. Unable to buy | ✅ ... Possible to buy", icon_url=get_user_avatar(interaction.user))

        if len(options) == 0:
            await interaction.send(embed=embed)
        else:
            await interaction.send(embed=embed,view=sview(self.bot, rewards_menu,interaction.user, 120,options))
        
         
        
        



def setup(bot: Bot) -> None:
    bot.add_cog(rewards(bot))