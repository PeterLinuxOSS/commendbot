import datetime
import io

import nextcord
from matplotlib import pyplot as plt
from matplotlib import ticker as tck
from nextcord import Colour, Interaction
from nextcord.ext import commands
from nextcord.ext.commands import Bot

from cogs.helpers import *
from utils import *


class slot_select(nextcord.ui.Select):
    def __init__(self,bot:Bot, selectOption):
        self.bot =bot
        
        
        super().__init__(placeholder="Select slot", min_values=1, max_values=1, options=selectOption)

    async def callback(self, interaction: nextcord.Interaction):
        
        slotdb = await db.slotsdb.find_one({"_id":int(self.values[0])})
        await slots_stats.stats(self,interaction,slotdb)    


def y_fmt(x, y):
    return '{}:00'.format(int(x))

class slots_stats(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot 

    async def pre_stats(self,interaction:Interaction):
        
        customer = interaction.user
        selectOption,dbs = await find_slots(customer,self.bot)
        if len(selectOption) == 1:
            slotdb = dbs[0]
            await slots_stats.stats(self,interaction,slotdb)
        elif len(selectOption) != 0:
            embed = nextcord.Embed(title="Slot Manager", description="Select slot witch do you wanna use.", color=Colour.blue(), timestamp=timestamp,)
            await interaction.message.edit(embed=embed,view=sview(self.bot,slot_select,interaction.user,180))
        
    async def stats(self,interaction:Interaction,slotdb:dict,fetch= "h",definition=None):
        slot_id = slotdb["_id"]
        data_stream = io.BytesIO()
    
        colors =["#08F7FE","#C27C0E",'#00FFFF','#0000FF','#DC143C' , '#A52A2A','#7FFF00','#8A2BE2','#000000','#D2691E']
        
        
        plt.style.use("dark_background")
       
        
        
        if "h":
            
            info = dict()
            for i  in range(0,24):
                info[i] = list()
            statsdb =  db.learn.find({"slot_id":slot_id})
            async for stat in statsdb:
                steamids:list = stat["steamids"]
                if len(steamids) != 0:
                    dt:datetime.datetime = stat["datetime"]
                    info[dt.hour].extend(steamids)
                    
            
            hours,keys = list(),list()    
            
            
            for id,key  in info.items():
                ks = list(set(key))
                
                
                hours.append(int(id))
                keys.append(len(ks))
              
            
            plt.plot(hours,keys,"o-", linewidth=2,
                        
                        
                        color=colors[0])
            plt.gca().xaxis.set_major_formatter(tck.FuncFormatter(y_fmt))
    
            
        
            
            
            
                
                
            
           
        plt.grid(color='#2A3459')
        
        plt.xlabel("Dates")
        plt.ylabel("Balance")
    
        
        plt.tight_layout()
    
        plt.savefig(data_stream, format='png', bbox_inches="tight", dpi = 80)
        
        data_stream.seek(0)
        plt.clf()
        chart = nextcord.File(data_stream,filename="graph.png")
        embed = nextcord.Embed(title="x", description="x", color=Colour.blue(), timestamp=timestamp,)
        embed.set_image(url="attachment://graph.png")
        await interaction.message.edit(file=chart ,embed=embed)
        
        
        
    


def setup(bot: commands.Bot) -> None:
    bot.add_cog(slots_stats(bot))