import nextcord
import NextcordUtils
from nextcord import Member
from nextcord.ext import commands
from nextcord.ext.commands import Bot

import config

# (nothing needed from cogs.commend)
from cogs.helpers import helpers
from utils import db, get_datetime_utc, user_template


class Invites(commands.Cog):
    def __init__(self, bot:Bot):
        self.bot = bot
        self.tracker = NextcordUtils.InviteTracker(bot)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.tracker.cache_invites()

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await self.tracker.update_invite_cache(invite)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.tracker.add_guild_cache(guild)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await self.tracker.remove_invite_cache(invite)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.tracker.remove_guild_cache(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member:Member):
        guild = member.guild
        coorect_one = False
        new = False
        
        
        if guild.id in [config.SUPPORT_GUILD_ID,config.COMMUNITY_GUILD_ID]:
            inviter:Member = await self.tracker.fetch_inviter(member)
            if inviter:
                current_date = get_datetime_utc()

                # Calculate the difference between the current date and the member's account creation date
                account_age = current_date - member.created_at

                # Check if the account age is older than 7 days
                if account_age.days > 7:
                    

                    # Calculate the difference between the current date and the member's account creation date
                    account_age = current_date - inviter.created_at

                    # Check if the account age is older than 7 days
                    if account_age.days > 7:
                    
                        # inviter is the member who invited
                        data :dict= await db.usersdb.find_one({"userid":inviter.id})
                        if not data :
                            data = user_template(inviter,False,free=True)
                            await db.usersdb.insert_one(data)
                            
                            if member != inviter:
                                test = await db.usersdb.find_one({f"{guild.id}.usersInvited":{ "$in":[member.id] }}) 
                                if test is None:
                                
                                    if str(guild.id) in data:
                                        if member.id not in data["usersInvited"]:
                                            new =True
                                            await db.usersdb.update_one({"userid":inviter.id},{'$inc': {f'{guild.id}.count': 1,
                                                                                                        'count': +1},
                                                                                                '$push': {f'{guild.id}.usersInvited': member.id,
                                                                                                            'usersInvited': [member.id]} ,
                                                                                                })
                                        else:
                                            
                                            if member.id not in data.get(f"{guild.id}.usersInvited",[]):
                                                await db.usersdb.update_one({"userid":inviter.id},{'$inc': {f'{guild.id}.count': 1,
                                                                                                            },
                                                                                                '$push': {f'{guild.id}.usersInvited': member.id,
                                                                                                            }})
                                    else:
                                        new =True
                                        await db.usersdb.update_one({"userid":inviter.id},{'$set': {f'{guild.id}.count': 1,f'{guild.id}.usersInvited': [member.id]},'$push': {'usersInvited': member.id},'$inc': {'count': +1}})
                                    subdb = await db.subdb.find_one({'guildid': guild.id})
                                    if "members" not in subdb:
                                        coorect_one =True
                                        await db.subdb.update_one({'guildid': guild.id}, {'$set': {'members': [member.id]}})
                                    elif  member.id not in subdb["members"]:
                                        coorect_one =True
                                        await db.subdb.update_one({'guildid': guild.id}, {'$push': {'members': member.id}})
                                    embed = nextcord.Embed(
                                        title=f"Welcome {member.display_name}",
                                        description=f"Invited by: {inviter.mention}\nInvites: {data['count']+1}\nGuild: {guild}",
                                        timestamp=member.joined_at,
                                        
                                    )
                                    embed.set_footer(text=guild.name)
                                    channel = self.bot.get_channel(config.INVITE_CHANNEL_ID)
                                    await channel.send(embed=embed)
                                    
                                    if coorect_one and new:
                                        invited = await db.balancesdb.find_one({"userid":member.id})
                                        if invited is None:
                                            await helpers.addbal(self, 10, inviter, 3, self.bot.user, None, 0, f"invite rewards for {member}")
                        

   

def setup(bot:Bot):
    bot.add_cog(Invites(bot))