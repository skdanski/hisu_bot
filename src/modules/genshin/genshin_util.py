from enkanetwork import EnkaNetworkAPI
from pymongo.mongo_client import MongoClient
from mongodb import mongodb_util
from util import config
import discord
from datetime import datetime
import enkanetwork


configuration = config.Config()
enka_client = EnkaNetworkAPI()
uri = configuration.mongodb_uri
api_version = configuration.mongodb_api_version
client = mongodb_util.createClient(uri, api_version)

async def verify_uid(uid, discord_id) -> bool:
    try:
        if uid is None:
            return False
        async with enka_client:
            data = await enka_client.fetch_user_by_uid(uid)
            return data is not None and data.player is not None and data.player.signature is not None and data.player.signature.__contains__(str(discord_id))
    except enkanetwork.exception.VaildateUIDError:
        return False

async def get_user(uid):
    if uid is None:
        return None
    async with enka_client:
        data = await enka_client.fetch_user_by_uid(uid)
        return data.player

def insert_profile(uid, discord_id):
    client = mongodb_util.createClient(uri, api_version)
    genshin = client.genshin
    player_collection = genshin.players
    return mongodb_util.update_document(player_collection, {"discord_id": discord_id},  {"$set": {"discord_id": discord_id, "uid": uid}}, True, True)


def delete_profile(discord_id):
    client = mongodb_util.createClient(uri, api_version)
    genshin = client.genshin
    player_collection = genshin.players
    doc = mongodb_util.delete_document(player_collection, {"discord_id": discord_id})
    return doc

def add_discord_id_to_server(server_id, usr_id):
    client = mongodb_util.createClient(uri, api_version)
    genshin = client.genshin
    server_collection = genshin.discord_servers

    server_count = mongodb_util.get_document_count(server_collection, {"server_id": server_id})
    if server_count == 0:
        mongodb_util.update_document(server_collection, {"server_id": server_id}, {"$set":{"server_id": server_id, "ids": []}}, True, True)
    
    server_count = mongodb_util.get_document_count(server_collection, {"server_id": server_id, "ids": usr_id})
    if server_count == 0:
        mongodb_util.update_document(server_collection, {"server_id": server_id}, {"$push":{"ids": usr_id}}, True, True)

def delete_discord_id_to_server(server_id, usr_id):
    client = mongodb_util.createClient(uri, api_version)
    genshin = client.genshin
    server_collection = genshin.discord_servers

    server_count = mongodb_util.get_document_count(server_collection, {"server_id": server_id})
    if server_count == 0:
        return
    server_count = mongodb_util.get_document_count(server_collection, {"server_id": server_id, "ids": usr_id})
    if server_count > 0:
        mongodb_util.update_document(server_collection, {"server_id": server_id}, {"$pull":{"ids": usr_id}}, True, True)
    
async def get_server_uids_list(server_id, bot):
    client = mongodb_util.createClient(uri, api_version)
    genshin = client.genshin
    server_collection = genshin.discord_servers
    player_collection = genshin.players
    embeds = []
    count = 0

    server_list = mongodb_util.get_documents(server_collection, {"server_id": server_id})
    if server_list is None or len(server_list) == 0:
        return embeds
    
    for discord_id in server_list[0]['ids']:
        if count % 5 == 0:
            embed = discord.Embed(title="Genshin UIDs", description="List of players' UIDs in this server", color=0xf3ec1b, timestamp=datetime.now())
            embed.set_thumbnail(url='https://cdn.donmai.us/original/0c/37/0c37ed59cc1fdbd2d31c3c281eaca761.jpg')
            embeds.append(embed)
            
        discord_name = ''
        genshin_name = ''
        genshin_uid = ''
        
        uid_doc_list = mongodb_util.get_documents(player_collection, {"discord_id": discord_id})
        if uid_doc_list is None or len(uid_doc_list) == 0:
            count = count + 1
            continue

        discord_data = await bot.fetch_user(discord_id)
        if discord_data is not None:
            discord_name = discord_data.name
        genshin_uid = uid_doc_list[0]["uid"]
        player_data = await get_user(genshin_uid)
        if player_data is not None:
            genshin_name = player_data.nickname
        
        embed.add_field(name='', value='', inline=False)
        embed.add_field(name='Discord Username', value=discord_name, inline=True)
        embed.add_field(name="Genshin Nickname", value=genshin_name, inline=True)
        embed.add_field(name="Genshin UID", value=genshin_uid, inline=True)
        count = count + 1
    return embeds
