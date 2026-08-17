from nextcord.ext import commands
from nextcord.ext.commands import Bot

# (nothing needed from cogs.commend)
# (nothing needed from cogs.helpers)
# (nothing needed from utils)


class UI(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
        
     



def setup(bot: Bot) -> None:
    bot.add_cog(UI(bot))