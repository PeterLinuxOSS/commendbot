from nextcord.ext import commands
from nextcord.ext.commands import Bot

from cogs.commend import *
from cogs.helpers import *
from utils import *


class UI(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
        
     



def setup(bot: Bot) -> None:
    bot.add_cog(UI(bot))