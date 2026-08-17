from nextcord.ext import commands
from nextcord.ext.commands import Bot

from cogs.helpers import *
from utils import *


class news(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
   
        
    @commands.Cog.listener()
    async def on_ready(self):
        pass
        
             



def setup(bot: Bot) -> None:
    bot.add_cog(news(bot))