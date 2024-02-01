# discord libs
from datetime import datetime
import discord
from discord.ext import commands
import valo_api as valo
import math
import sys
import configparser
from statistics import mean
import re
import asyncio
import Paginator

from valorant import valo_commands
from openai_util import openai_util
from genshin import genshin_util
from hsr import hsr_util

from util import config
from util.utils import create_embed
from util.valo_utils import nametag_resolver
valo_thumbnail = 'https://www.techspot.com/images2/downloads/topdownload/2020/06/2020-06-09-ts3_thumbs-7fd-p_256.webp'
configuration = config.Config()
auth_token = configuration.discord_auth_token
command_prefix = configuration.discord_command_prefix
api_key = configuration.valo_api_key
local = configuration.local

valo.set_api_key(api_key=api_key)

# acc = valo.get_account_kd_by_name('v1', 'Prudence', 4424)
class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')

intents = discord.Intents.default()
intents.message_content = True

# Helper function to deal with match size error handling
async def match_size_handler(ctx, size: int, exclude: int, ctr: int):
    if size == 1:
        if exclude > ctr:
            await ctx.send(f'```Error: {exclude}/{size} Matches Excluded, Try a Different Size Parameter```')
            return
        else:
            description=f'Based on Latest Match (Descending)'
            return description
    elif size != 1 and exclude > 0:
        if exclude > ctr and ctr == 0:
            await ctx.send(f'```Error: {exclude}/{size} Matches Excluded, Try a Different Size Parameter```')
            return 
        else:
            description=f'Based on Latest {ctr} Matches (Excluding {exclude} Matches)'
            return description
    else:
        description=f'Based on Latest {ctr} Matches (Descending)'
        return description

bot = commands.Bot(command_prefix=command_prefix, intents=intents)

@bot.command()
async def valoaddacc(ctx, *arg):
    user = ctx.author
    usr=[user.id, user.name, user.display_name, user.avatar.url]

    if len(arg) == 0:
        await ctx.send('empty command')
        return

    ans = valo_commands.add_account(arg,usr)
    if ans is True:
        await ctx.send(f'```Account Added to User: {ctx.author.name}```')
    else:
        await ctx.send(f'```"{ans}"```')
        # await ctx.send('```Error: Account already belongs to a user OR has no recent matches```')
        return

@bot.command()
async def valoremoveacc(ctx, *arg):
    user = ctx.author
    usr=[user.id, user.name, user.display_name, user.avatar.url]
    if len(arg) == 0:
        await ctx.send('empty command')
        return
    ans = valo_commands.remove_account(arg, usr)
    # turn the 0 to 4 into constants variables
    if ans == 0:
        await ctx.send(f'```Successfully Removed Account from User!```')
    elif ans == 1:
        await ctx.send('```Error: User Does Not Exist in DB!```')
        return
    elif ans == 2:
        await ctx.send(f'```Error: Account Does Not Exist in DB!```')
        return
    elif ans == 3:
        await ctx.send(f'```Error: Account Does Not Belong to You!```')
        return
    elif ans == 4:
        await ctx.send(f'```Error: Account Does Not Exist!```')
        return

@bot.command()
async def valostats(ctx, *arg):
    try:
        res = nametag_resolver(arg)
        if type(res) is str:
            await ctx.send(res)
            return
        elif type(res) is list and type(res[0]) is int:
            size = res[0]
            result = res[1]
            title = res[2]
            try:
                hs = valo_commands.account_hs(result, size)
                kd = valo_commands.account_kd(result, size)
                if size == 1:
                    if kd[6] > kd[7]:
                        await ctx.send(f'```Error: {kd[6]}/{size} Matches Excluded, Try a Different Size Parameter```')
                        return
                    else:
                        description=f'Based on Latest Match (Descending)'
                elif size != 1 and kd[6] > 0:
                    if kd[6] > kd[7] and kd[7] == 0:
                        await ctx.send(f'```Error: {kd[6]}/{size} Matches Excluded, Try a Different Size Parameter```')
                        return 
                    else:
                        description=f'Based on Latest {kd[7]} Matches (Excluding {kd[6]} Matches)'
                else:
                    description=f'Based on Latest {kd[7]} Matches'
            except Exception as e:
                await ctx.send(f"```Error: {str(e)}\nTry a different size!```")
                return
        elif type(res) is list and type(res[0]) is str:
            result = res[0]
            title = res[1]
            hs = valo_commands.account_hs(result)
            kd = valo_commands.account_kd(result)
            description=f'Based on Latest {kd[7]} Matches'
        else:
            await ctx.send("something went wrong...")

        title=title
        color=discord.Color.green()
        msg = [
            {'name': 'Average Kills',
             'value': kd[3]},
            {'name': 'Average Deaths',
             'value': kd[4]},
            {'name': 'Average KDR',
             'value': kd[5]},
            {'name': '',
             'value': ''},
            {'name': '',
             'value': ''},
            {'name': '',
             'value': ''},
            {'name': 'Average Headshots',
             'value': hs[4]},
            {'name': 'Average Bodyshots',
             'value': hs[5]},
            {'name': 'Average HS Ratio',
             'value': hs[7]}
        ]
        embed = create_embed(title=title, desc=description, color=color, msg=msg)
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(e)
        await ctx.send(f"```{str(e)}```")

@bot.command()
async def valokdstats(ctx, *arg):
    try:
        res = nametag_resolver(arg)
        if type(res) is str:
            await ctx.send(res)
            return
        elif type(res) is list and type(res[0]) is int:
            size = res[0]
            result = res[1]
            title = res[2]
            try:
                kd = valo_commands.account_kd(result, size)
                description = await match_size_handler(ctx=ctx, size=size, exclude=kd[6], ctr=kd[7])
            except Exception as e:
                await ctx.send(f"```Error: {str(e)}\nTry a different size!```")
                return
        elif type(res) is list and type(res[0]) is str:
            result = res[0]
            title = res[1]
            kd = valo_commands.account_kd(result)
            description=f'Based on Latest {kd[7]} Matches'
        else:
            await ctx.send("something went wrong...")

        length = len(kd[0])
        title=title
        color=discord.Color.green()
        msg = [
            {'name': "Kills",
             'value': '\n'.join([f'{kd[0][n]}' for n in range(length)])},
            {'name': "Deaths",
             'value': '\n'.join([f'{kd[1][n]}' for n in range(length)])},
            {'name': 'KDR',
             'value': '\n'.join([f'{kd[2][n]}' for n in range(length)])},
            {'name': 'Average Kills',
             'value': kd[3]},
            {'name': 'Average Deaths',
            'value': kd[4]},
            {'name': 'Average KDR',
            'value': kd[5]}
        ]
        embed = create_embed(title=title, desc=description, color=color, msg=msg)
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)
        await ctx.send(f"```{str(e)}```")

@bot.command()
async def valohitstats(ctx, *arg):
    try:
        res = nametag_resolver(arg)
        if type(res) is str:
            await ctx.send(res)
            return
        elif type(res) is list and type(res[0]) is int:
            size = res[0]
            result = res[1]
            title = res[2]
            try:
                hs = valo_commands.account_hs(result, size)
                description = await match_size_handler(ctx=ctx, size=size, exclude=hs[8], ctr=hs[9])
            except Exception as e:
                await ctx.send(f"```Error: {str(e)}\nTry a different size!```")
                return
        elif type(res) is list and type(res[0]) is str:
            result = res[0]
            title = res[1]
            hs = valo_commands.account_hs(result)
            description = f'Based on Latest {hs[9]} Matches (Descending)'
        else:
            await ctx.send("something went wrong...")

        length = len(hs[0])
        title=title
        color=discord.Color.green() # color subject to change
        msg = [
            {'name': "Head",
            'value': '\n'.join([f'{hs[0][n]}' for n in range(length)])},
            {'name': 'Body',
            'value': '\n'.join([f'{hs[1][n]}' for n in range(length)])},
            {'name': 'HS Ratio',
            'value': '\n'.join([f'{hs[3][n]}' for n in range(length)])},
            {'name': 'Average Headshots',
            'value': hs[4]},
            {'name': 'Average Bodyshots',
            'value': hs[5]},
            {'name': 'Average HS Ratio',
            'value': hs[7]},
        ]
        embed = create_embed(title=title, desc=description, color=color, msg=msg)
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)
        return

# reaction testing command
# constant interaction seems to refresh the timeout timer in wait_for()
# standard convention: edit (original) message upon certain reaction
@bot.command()
async def react(ctx, *arg):
    if local:
        left_arrow =  '\U00002B05'
        right_arrow = '\U000027A1'

        msg = await ctx.send(f'React with {left_arrow} to go left and {right_arrow} to go right!')
        await msg.add_reaction(left_arrow)
        await msg.add_reaction(right_arrow)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [left_arrow, right_arrow]

        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=10.0, check=check)

                if str(reaction.emoji) == left_arrow:
                    # print statements that are meant for debugging should be turned into logs
                    print("User has selected Left Arrow")
                    await msg.edit(content=f'You have selected {left_arrow}')

                elif str(reaction.emoji) == right_arrow:
                    print("User has selected Right Arrow")
                    await msg.edit(content=f"You have selected {right_arrow}")

            except Exception as e:
                print(e)
                return
        
# user can check their profile to see what accounts are listed 
@bot.command()
async def valoprofile(ctx, *arg):
    print("Profile Hit")
    usr_id = ctx.author.id
    usr_name = ctx.author.name
    usr_pic = ctx.author.avatar.url
    ans = valo_commands.profile(usr_id)
    length = len(ans[0])
    title=f"{usr_name}'s Profile"
    description='Associated Account(s)\n' + '\n'.join([f'> **{ans[0][n]["acc_name"]}#{ans[0][n]["acc_tag"]}** | `{ans[0][n]["rank_name"]}`' for n in range(0, length)])
    color=discord.Color.green() # color subject to change
    timestamp=datetime.now()
    msg = [
        {'name': 'K/D Ratio',
        'value': ans[1],
        'inline': True},
        {'name': 'HS Ratio',
        'value': ans[2],
        'inline': True},
        {'name':'Current Highest Rank',
        'value': ans[0][0]['rank_name'],
        'inline': True}
    ]
    embed = create_embed(title=title, desc=description, color=color, msg=msg, timestamp=timestamp, url=usr_pic)
    await ctx.send(embed=embed)
    print("Profile Message Sent")


# currently shows up to 20 players
# todo: let users choose between KD / Rank
@bot.command()
async def valoleaderboard(ctx, *arg):
    left_arrow =  '\U00002B05'
    right_arrow = '\U000027A1'
    # state conditions
    # 0 = 0~5 ; 1 = 5~10; 2 = 10~15, 3 = 15~20, 4 = 20~25, 5 = 25~30 
    n = pg_cnt = max_len = 0
    ctr = curr_pg = 1
    print("Fetching Stats...")
    ans = valo_commands.leaderboard()
    print("Fetching Complete!")

    embed = discord.Embed(title="Valo Leaderboard", description="*Based on K/D*", color=0xf3ec1b, timestamp=datetime.now())
    embed.set_thumbnail(url=valo_thumbnail)

    pg2 = discord.Embed(title="Valo Leaderboard", description="*Based on K/D*", color=0xf3ec1b, timestamp=datetime.now())
    pg2.set_thumbnail(url=valo_thumbnail)

    pg3 = discord.Embed(title="Valo Leaderboard", description="*Based on K/D*", color=0xf3ec1b, timestamp=datetime.now())
    pg3.set_thumbnail(url=valo_thumbnail)

    pg4 = discord.Embed(title="Valo Leaderboard", description="*Based on K/D*", color=0xf3ec1b, timestamp=datetime.now())
    pg4.set_thumbnail(url=valo_thumbnail)

    if len(ans) < 5:
        # print('hit len(ans) < 5')
        while n < len(ans):
            embed.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
            embed.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
            embed.add_field(name="Rank", value=ans[n]['rank'], inline=True)
            embed.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
        n += 1
        ctr += 1
    else:
        # print('hit len(ans) > 5')
        while n < 5:
            embed.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
            embed.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
            embed.add_field(name="Rank", value=ans[n]['rank'], inline=True)
            embed.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
            n += 1
            ctr += 1

    rem = len(ans) % 5
    # quotient == 2 -> 10's quotient = 4 -> 20's, quotient = 6 -> 30's etc...
    quotient = int(len(ans)/5)

    if rem == 0:
        print('hit rem == 0')
        pg_cnt = len(ans)/5
        max_len = len(ans)
        if max_len == 10:
            while n < 10:
                pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                n += 1
                ctr += 1
        elif max_len == 15:
            while n < 10:
                pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                n += 1
                ctr += 1
            while n < 15:
                pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                n += 1
                ctr += 1
        elif max_len == 20:
            while n < 10:
                pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                n += 1
                ctr += 1
            while n < 15:
                pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                n += 1
                ctr += 1
            while n < 20:
                pg4.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                pg4.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                pg4.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                pg4.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                n += 1
                ctr += 1
        
    else:
        # print('hit rem > 0')
        pg_cnt = math.ceil(len(ans)/5)
        if rem == 1 and len(ans) > 5:
            max_len = quotient * 5 + 1
            if quotient == 0:
                print('Error: Length of Array is 1')
                return
            elif quotient == 1 and max_len == 6:
                while n < 6:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
            elif quotient == 2 and max_len == 11:
                while n < 10:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
                while n < 11:
                    pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
            elif quotient == 2 and max_len == 16:
                while n < 10:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
                while n < 16:
                    pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
        elif rem == 2 and len(ans) > 5:
            max_len = quotient * 5 + 2
            if quotient == 0:
                print('Error: Length of Array is 1')
                return
            elif quotient == 1 and max_len == 7:
                while n < 7:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
            elif quotient == 2 and max_len == 12:
                while n < 10:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
                while n < 12:
                    pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
            elif quotient == 2 and max_len == 17:
                while n < 10:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
                while n < 17:
                    pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
        elif rem == 3 and len(ans) > 5:
            max_len = quotient * 5 + 3
            if quotient == 0:
                print('Error: Length of Array is 1')
                return
            elif quotient == 1 and max_len == 8:
                while n < 8:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
            elif quotient == 2 and max_len == 13:
                while n < 10:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
                while n < 13:
                    pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
            elif quotient == 2 and max_len == 18:
                while n < 10:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
                while n < 18:
                    pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
        elif rem == 4 and len(ans) > 5:
            max_len = quotient * 5 + 4
            if quotient == 0:
                print('Error: Length of Array is 1')
                return
            elif quotient == 1 and max_len == 9:
                while n < 9:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
            elif quotient == 2 and max_len == 14:
                while n < 10:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
                while n < 14:
                    pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
            elif quotient == 2 and max_len == 19:
                while n < 10:
                    pg2.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg2.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg2.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg2.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
                while n < 19:
                    pg3.add_field(name=f"__{ctr}. {ans[n]['acc_name']}#{ans[n]['acc_tag']}__", value="", inline=False)
                    pg3.add_field(name="K/D", value=ans[n]['kd_stat'], inline=True)
                    pg3.add_field(name="Rank", value=ans[n]['rank'], inline=True)
                    pg3.add_field(name="Discord User", value=ans[n]['disc_name'], inline=True)
                    n += 1
                    ctr += 1
        

    embed.set_footer(text="*Ranking Based on Competitive Matches*")

    msg = await ctx.send(embed=embed)
    await msg.add_reaction(left_arrow)
    await msg.add_reaction(right_arrow)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in [left_arrow, right_arrow]

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == left_arrow and curr_pg == 1:
                # print("User has selected Left Arrow")
                print("Error: Already on First Page!")
            elif str(reaction.emoji) == left_arrow and curr_pg > 1:
                if curr_pg == 2:
                    # print("User has selected Left Arrow")
                    await msg.edit(embed=embed)
                    curr_pg -= 1
                elif curr_pg == 3:
                    # print("User has selected Left Arrow")
                    await msg.edit(embed=pg2)
                    curr_pg -= 1
                elif curr_pg == 4:
                    # print("User has selected Left Arrow")
                    await msg.edit(embed=pg3)
                    curr_pg -= 1
            elif str(reaction.emoji) == right_arrow and curr_pg != pg_cnt and curr_pg == 1:
                # print("User has selected Right Arrow")
                await msg.edit(embed=pg2)
                curr_pg += 1
            elif str(reaction.emoji) == right_arrow and curr_pg != pg_cnt and curr_pg > 1:
                # print("User has selected Right Arrow")
                if curr_pg == 2:
                    # print("User has selected Right Arrow")
                    await msg.edit(embed=pg3)
                    curr_pg += 1
                elif curr_pg == 3:
                    # print("User has selected Right Arrow")
                    await msg.edit(embed=pg4)
                    curr_pg += 1
            elif str(reaction.emoji) == right_arrow and curr_pg == pg_cnt:
                # print("User has selected Right Arrow")
                print("Error: Already at End of Page!")

        except Exception as e:
            print(e)
            return
        
@bot.remove_command("help")
@bot.command()
async def help(ctx):
    title = "List of Commands"
    desc = ""
    color = 0xf3ec1b
    msg = [
        {'name': "*Valorant Account Linking Commands*",
         'value': "",
         'inline': True},
        {'name': command_prefix + "valoaddacc",
         'value': "> Link a Valorant Account to your Discord Account\n__Usage__: `" + command_prefix + "valoaddacc player1#tag1`",
         'inline': True},
        {'name': command_prefix + "valoremoveacc",
         'value': "> Unlink a Valorant Account from your Discord Account\n__Usage__: `" + command_prefix + "valoremoveacc player1#tag1`",
         'inline': True},
        {'name': "*Valorant Account Statistics Commands*",
         'value': '',
         'inline': True},
        {'name': command_prefix + "valokdstats",
         'value': "> Show the K/D Stats of a Valorant Account\n__Usage__: `" + command_prefix + "valokdstats player1#tag1`",
         'inline': True},
        {'name': command_prefix + "valohitstats",
         'value': "> Show the Hit (Head/Body/Leg) Stats of a Valorant Account\n__Usage__: `" + command_prefix + "valohitstats player1#tag1`",
         'inline': True},
        {'name': '',
         'value': '',
         'inline': True},
        {'name': command_prefix + "valostats",
         'value': "> Show Simplified Stats of a Valorant Account\n__Usage__: `" + command_prefix + "valostats player1#tag1`",
         'inline': True},
        {'name': '',
         'value': '',
         'inline': True},
        {'name': "*Valorant Account Misc Commands*",
         'value': '',
         'inline': True},
        {'name': command_prefix + "valoleaderboard",
         'value':"> Shows the Leaderboard for all Linked Valorant Accounts\n__Usage__: `" + command_prefix + "valoleaderboard`",
         'inline': True},
        {'name': command_prefix + "valoprofile",
         'value': "> Shows Information of all the Discord User's Linked Accounts\n__Usage__: `" + command_prefix + "valoprofile`",
         'inline': True},
         {'name': "*ChatGPT Commands*",
         'value': '',
         'inline': True},
        {'name': command_prefix + "chat",
         'value':"> Talk to Hisu Bot with any prompt\n__Usage__: `" + command_prefix + "chat <prompt>`",
         'inline': True},
        {'name': command_prefix + "translate",
         'value': "> Translate text from one language to another. Default langugae is english if orginal language is omitted\n__Usage__: `" + command_prefix + "translate <original language> <target langauge> <text>`",
         'inline': True},
        {'name': command_prefix + "genshinuidinsert",
         'value': "> Link or update your Genshin UID in this server. Your discord user id must be set in your profile signature in Genshin for verification.\n__Usage__: `" + command_prefix + "genshinuidinsert <uid>`",
         'inline': True},
        {'name': command_prefix + "genshinuiddelete",
         'value': "> Unlink your Genshin UID in this server.",
         'inline': True},
        {'name': command_prefix + "genshinuids",
         'value': "> See the UIDs of Genshin players in this server.",
         'inline': True},
        {'name': command_prefix + "hsruidinsert",
         'value': "> Same as " + command_prefix + "genshinuidinsert but with HSR UIDs.",
         'inline': True},
        {'name': command_prefix + "genshinuiddelete",
         'value': "> Unlink your HSR UID in this server.",
         'inline': True},
         {'name': command_prefix + "genshinuids",
         'value': "> See the UIDs of HSR players in this server.",
         'inline': True},
         
    ]
    embed = create_embed(msg=msg, title=title, desc=desc, color=color)
    await ctx.send(embed=embed)

@bot.command('chat')
async def chat(ctx, *args):
    if len(args) == 0:
        await ctx.send('Empty command')
        return
    combined_text = ' '.join(args)
    bot_response = openai_util.chat(combined_text)

    if len(bot_response) == 0:
        await ctx.send('Donowalling you...')
        return
    await ctx.send(bot_response)
    return

@bot.command('translate')
async def chat(ctx, *args):
    src_language = None
    target_language = None
    text = None
    if len(args) == 0:
        await ctx.send('Empty command')
        return
    elif len(args) < 2:
        await ctx.send('Command must have target language to translate to and the text to translate afterwards!')
        return
    elif len(args) == 2:
        src_language = configuration.language
        target_language = args[0]
        text = ' '.join(args[1:])  
    elif len(args) == 3:
        src_language = args[0]
        target_language = args[1]
        text = ' '.join(args[2:])       

    translated_text = openai_util.translate_text(text, src_language, target_language)
    await ctx.send(translated_text)
    return

@bot.command('genshinuidinsert')
async def chat(ctx, *args):
    uid = None
    usr_id = ctx.author.id
    server_id = ctx.message.guild.id
    if len(args) == 0:
        await ctx.send('Empty command')
        return
    uid = args[0]

    verified = await genshin_util.verify_uid(uid, usr_id)
    if verified is False:
        await ctx.send('UID is not valid or your genshin account\'s signature is not set to be your discord id(' + str(usr_id) + ') .')
        return
    doc = genshin_util.insert_profile(uid, usr_id)
    if doc is not None:
        genshin_util.add_discord_id_to_server(server_id, usr_id)
        await ctx.send('UID is now linked to your discord account')
        return
    else:
        await ctx.send('Something went wrong with updating user account.')
        return


@bot.command('genshinuiddelete')
async def chat(ctx, *args):
    usr_id = ctx.author.id
    server_id = ctx.message.guild.id

    doc = genshin_util.delete_profile(usr_id)
    if doc is None or doc.get('deleted_count') == 0:
        await ctx.send('No Genshin account assoicated with discord account.')
        return
    genshin_util.delete_discord_id_to_server(server_id, usr_id)
    await ctx.send('Genshin account no longer linked to your discord account.')
    return

@bot.command('genshinuids')
async def chat(ctx, *args):
    server_id = ctx.message.guild.id
    embeds = await genshin_util.get_server_uids_list(server_id, bot)
    InitialPage = 0 # Page to start the paginator on.
    timeout = 42069 # Seconds to timeout. Default is 60

    await Paginator.Simple(
        InitialPage=InitialPage,
        timeout=timeout).start(ctx, pages=embeds)


@bot.command('hsruidinsert')
async def chat(ctx, *args):
    uid = None
    usr_id = ctx.author.id
    server_id = ctx.message.guild.id
    if len(args) == 0:
        await ctx.send('Empty command')
        return
    uid = args[0]

    verified = await hsr_util.verify_uid(uid, usr_id)
    if verified is False:
        await ctx.send('UID is not valid or your HSR account\'s signature is not set to be your discord id(' + str(usr_id) + ') .')
        return
    doc = hsr_util.insert_profile(uid, usr_id)
    if doc is not None:
        hsr_util.add_discord_id_to_server(server_id, usr_id)
        await ctx.send('UID is now linked to your discord account')
        return
    else:
        await ctx.send('Something went wrong with updating user account.')
        return


@bot.command('hsruiddelete')
async def chat(ctx, *args):
    usr_id = ctx.author.id
    server_id = ctx.message.guild.id

    doc = hsr_util.delete_profile(usr_id)
    if doc is None or doc.get('deleted_count') == 0:
        await ctx.send('No HSR account assoicated with discord account.')
        return
    hsr_util.delete_discord_id_to_server(server_id, usr_id)
    await ctx.send('HSR account no longer linked to your discord account.')
    return

@bot.command('hsruids')
async def chat(ctx, *args):
    server_id = ctx.message.guild.id
    embeds = await hsr_util.get_server_uids_list(server_id, bot)
    InitialPage = 0 # Page to start the paginator on.
    timeout = 42069 # Seconds to timeout. Default is 60

    await Paginator.Simple(
        InitialPage=InitialPage,
        timeout=timeout).start(ctx, pages=embeds)

bot.run(auth_token)