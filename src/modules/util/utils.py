import discord
from pymongo import *
from collections import Counter
from mongodb import mongodb_util
from util import config
import valo_api as valo
import re

configuration = config.Config()
uri = configuration.mongodb_uri
api_key = configuration.valo_api_key

def most_freq(list):
    count = Counter(list)
    return count.most_common(1)[0][0]

# Finds the index value of a specific key:value pair in a List of Dicts
def find_dict_idx(list, key, value):
    for i, dict in enumerate(list):
        if dict[key] == value:
            return i
    return -1

# create an embed object given a dict of fields
def create_embed(title: str, desc, color, msg, **kwargs):
    if 'timestamp' in kwargs:
        embed = discord.Embed(
            title=title,
            description=desc,
            color=color,
            timestamp=kwargs['timestamp']
        )
    else:
        embed = discord.Embed(
            title=title,
            description=desc,
            color=color,
        )
    if 'url' in kwargs:
        embed.set_thumbnail(url=kwargs['url'])
    else: 
        embed.set_thumbnail(url=None)

    for i in range(len(msg)):
        if 'inline' in msg[i]:
            embed.add_field(
                name=msg[i]['name'],
                value=msg[i]['value'],
                inline=msg[i]['inline']
            )
        else:
            embed.add_field(
                name=msg[i]['name'],
                value=msg[i]['value'],
                inline=True
            )
    return embed

    