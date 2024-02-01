from mihomo import Language, MihomoAPI
from mihomo.models import StarrailInfoParsed
from mihomo.models.v1 import StarrailInfoParsedV1
import mihomo
from pymongo.mongo_client import MongoClient
from mongodb import mongodb_util
from util import config
import discord
from datetime import datetime

hsr_client = MihomoAPI(language=Language.EN)
configuration = config.Config()
uri = configuration.mongodb_uri
api_version = configuration.mongodb_api_version
client = mongodb_util.createClient(uri, api_version)

async def verify_uid(uid, discord_id) -> bool:
    try:
        if uid is None:
            return False
        data = await hsr_client.fetch_user_v1(uid)
        return data is not None and data.player is not None and data.player.signature is not None and data.player.signature.__contains__(str(discord_id))
    except mihomo.errors.InvalidParams:
        return False

async def get_user(uid):
    if uid is None:
        return None
    data = await hsr_client.fetch_user_v1(uid)
    return data.player

def insert_profile(uid, discord_id):
    client = mongodb_util.createClient(uri, api_version)
    hsr = client.hsr
    player_collection = hsr.players
    return mongodb_util.update_document(player_collection, {"discord_id": discord_id},  {"$set": {"discord_id": discord_id, "uid": uid}}, True, True)


def delete_profile(discord_id):
    client = mongodb_util.createClient(uri, api_version)
    hsr = client.hsr
    player_collection = hsr.players
    doc = mongodb_util.delete_document(player_collection, {"discord_id": discord_id})
    return doc

def add_discord_id_to_server(server_id, usr_id):
    client = mongodb_util.createClient(uri, api_version)
    hsr = client.hsr
    server_collection = hsr.discord_servers

    server_count = mongodb_util.get_document_count(server_collection, {"server_id": server_id})
    if server_count == 0:
        mongodb_util.update_document(server_collection, {"server_id": server_id}, {"$set":{"server_id": server_id, "ids": []}}, True, True)
    
    server_count = mongodb_util.get_document_count(server_collection, {"server_id": server_id, "ids": usr_id})
    if server_count == 0:
        mongodb_util.update_document(server_collection, {"server_id": server_id}, {"$push":{"ids": usr_id}}, True, True)

def delete_discord_id_to_server(server_id, usr_id):
    client = mongodb_util.createClient(uri, api_version)
    hsr = client.hsr
    server_collection = hsr.discord_servers

    server_count = mongodb_util.get_document_count(server_collection, {"server_id": server_id})
    if server_count == 0:
        return
    server_count = mongodb_util.get_document_count(server_collection, {"server_id": server_id, "ids": usr_id})
    if server_count > 0:
        mongodb_util.update_document(server_collection, {"server_id": server_id}, {"$pull":{"ids": usr_id}}, True, True)
    
async def get_server_uids_list(server_id, bot):
    client = mongodb_util.createClient(uri, api_version)
    hsr = client.hsr
    server_collection = hsr.discord_servers
    player_collection = hsr.players
    embeds = []
    count = 0
    server_list = mongodb_util.get_documents(server_collection, {"server_id": server_id})
    if server_list is None or len(server_list) == 0:
        return embeds
    
    for discord_id in server_list[0]['ids']:
        if count % 5 == 0:
            embed = discord.Embed(title="Honkai: Star Rail UIDs", description="List of players' UIDs in this server", color=0xf3ec1b, timestamp=datetime.now())
            embed.set_thumbnail(url='https://upload-os-bbs.hoyolab.com/upload/2023/07/11/76d0fafe7d0e15dd7c63fb87573f6468_8555660723501698853.png?x-oss-process=image%2Fresize%2Cs_1000%2Fauto-orient%2C0%2Finterlace%2C1%2Fformat%2Cwebp%2Fquality%2Cq_80')
            embeds.append(embed)

        discord_name = ''
        hsr_name = ''
        hsr_uid = ''
        
        uid_doc_list = mongodb_util.get_documents(player_collection, {"discord_id": discord_id})
        if uid_doc_list is None or len(uid_doc_list) == 0:
            count = count + 1
            continue

        discord_data = await bot.fetch_user(discord_id)
        if discord_data is not None:
            discord_name = discord_data.name
        hsr_uid = uid_doc_list[0]["uid"]
        player_data = await get_user(hsr_uid)
        if player_data is not None:
            hsr_name = player_data.name
        
        embed.add_field(name='', value='', inline=False)
        embed.add_field(name='Discord Username', value=discord_name, inline=True)
        embed.add_field(name="HSR Nickname", value=hsr_name, inline=True)
        embed.add_field(name="HSR UID", value=hsr_uid, inline=True)
        count = count + 1
    return embeds
