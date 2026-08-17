import asyncio
import datetime
import os
import platform

import nextcord
import paramiko
import pymongo
from nextcord import Colour, Member, TextChannel, User
from nextcord.ext import commands
from nextcord.ext.commands import Bot

import config

# (nothing needed from cogs.helpers)
from utils import convert_lang, db, favoriteguildsdb, vps_value

# Removed on publication: a pair of unused helpers that validated Discord user
# tokens by shelling out to a Node script outside this repo, with a real token
# pasted into the command line. Nothing called them.


class resellers(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot 
        
    async def leaderboard(self,guildstts):
        channelg = self.bot.get_channel(config.RESELLER_BOARD_CHANNEL_ID)
        counter =0
        
        subdbs:list = await (db.subdb.find({"guildid":{"$exists":True},"disabled":False}).sort("_id",pymongo.ASCENDING)).to_list(None)
        
        
        subdbs.sort(key=favoriteguildsdb)
        sublist = sorted(subdbs, key=lambda sub: sub['subtype']) 
        description="You can create private channels in these following servers.\n\n**Our Sellers:**\n\n"
        
        
        
        
        

        listofused = []
        for subdb in sublist:
            guild = self.bot.get_guild(subdb["guildid"])
            if guild:
                guildbs = list(filter(lambda i: i['guildid'] == guild.id and i["setupbot"], guildstts))
                
                if len(guildbs) != 0:
                    guildb = guildbs[0]
                    if guildb["public"]:
                        try:
                            invite = await self.bot.fetch_invite(guildb["link"])
                        except Exception:
                            if "startupid" in guildb:
                                channel = self.bot.get_channel(guildb['startupid'])
                                if channel:
                                    invite = await channel.create_invite(reason="invite is required",max_age=0,max_uses=0,temporary=False)
                                    await db.guildsetting.update_one({"guildid":guildb["guildid"]}, {"$set": {"link": invite.url}})
                                else:
                                    invite = None  
                            else:
                                invite = None  
                        else:
                            channel = self.bot.get_channel(guildb['startupid'])
                            if not channel:
                                await asyncio.sleep(5)
                                channel = self.bot.get_channel(guildb['startupid'])
                                if not channel:
                                    invite = None
                                    
                                    await db.guildsetting.update_one({"guildid":guildb["guildid"]}, {"$set": {"setupbot": False}})
                            
                        if invite is not None:
                            
                            counter+=1
                            if subdb["subtype"] not in listofused and subdb["subtype"] == 1:
                                description += "\n\n**Premium Resellers:**\n\n"
                                listofused.append(subdb["subtype"])
                            elif subdb["subtype"] not in listofused and subdb["subtype"] == 2:
                                description += "\n\n**Standard-Server Resellers:**\n\n"
                                listofused.append(subdb["subtype"])
                            
                            if "default_lang" in guildb:
                                loc = guildb["default_lang"]
                                translation = convert_lang(loc)
                                description += f"{counter}. [{guild.name}]({invite.url}) — Language: {translation['lang']} ||{channel.mention}||\n"
                            else:
                                description += f"{counter}. [{guild.name}]({invite.url}) — Language: English ||{channel.mention}||\n"
                            overwrite = channel.overwrites_for(channel.guild.default_role)
                            if  not overwrite.read_message_history or not overwrite.read_messages or not overwrite.view_channel :
                            
                                await channel.set_permissions(channel.guild.default_role, read_message_history=True,read_messages=True,view_channel=True,send_messages=False,reason="This guild is in public mode(use /setup -> setup-settings -> server-settings to change)")
     
                    
                
                else:
                    print(guild.name)
                    
        embed = nextcord.Embed(title="Current resellers", description=description, color=Colour.gold(), timestamp=datetime.datetime.now(),)
        msg = await channelg.fetch_message(config.RESELLER_BOARD_MESSAGE_ID)
        try:
            await msg.edit(embed=embed)
        except nextcord.errors.Forbidden:
            try:
                
                await channelg.last_message.edit(embed=embed)
            except Exception:
                msg = await channelg.send(embed=embed) 
           
        
            
    async def addpremiumr(self,channel: TextChannel,customer:Member or User, selfbot: User or Member,token):
        guildg = self.bot.get_guild(config.SLOT_GUILD_ID)
        print(guildg.name)
        print(guildg.categories)
        category = nextcord.utils.get(guildg.categories, id=config.SLOT_CATEGORY_ID)
        if guildg in selfbot.mutual_guilds:
            print(guildg.name)
            nuumber = await db.slotsdb.count_documents({})
            
            slotid = nuumber + 1
            main1 = await category.create_text_channel(f"slot{slotid}")
            await main1.create_webhook(name=f"slot{slotid}")
            await db.slotsdb.insert_one({"_id":int(slotid),"name":f"slot{slotid}","enable":True,"currency":2500,"update_currency":2500,"userid":selfbot.id,"max_daily_commends":500,"max_commends":250,"min_commends":10,"admins":[customer.id],"commend_channelid":main1.id,"ready":True,"price":0,"price-count":0})
            if "Linux" in platform.platform():
                os.popen("pm2 restart slot").read(1500)
            else:
                
                transport = paramiko.SSHClient()  # idk if it need to have ip in int
                transport.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                transport.connect(hostname=vps_value["vps_ip"],username = vps_value["vps_user"], password = vps_value["vps_pass"])
                stdin, stdout, stderr = transport.exec_command("pm2 restart slot")
                lines = stdout.readlines()
                print(lines)


                transport.close()
                    
                    
            await channel.send("we add new slot to db")


def setup(bot: Bot) -> None:
    bot.add_cog(resellers(bot))