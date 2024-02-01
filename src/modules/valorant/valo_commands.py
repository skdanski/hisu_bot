import discord
import valo_api as valo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from statistics import mean
import pymongo
import pprint
from util import config, logger
import re
import sys
from mongodb import mongodb_util 
from util.valo_utils import mmr_updater, lifetime_stats_updater

configuration = config.Config()
uri = configuration.mongodb_uri

logging = logger.Logger('valo_commands', 'valo_commands_logger')


# usr_id is a list --> [id, name, dname, avatar]
def add_account(arg_lst, usr) -> bool:

    account_documents_list = []
    usr_info={
        'id': usr[0],
        'name': usr[1],
        'display_name': usr[2],
        'avatar': usr[3],
        'accounts': []
    }
    if len(arg_lst) == 1:
        nametag = arg_lst[0]
        print(f"length of args = 1 / {nametag}")
    elif len(arg_lst) == 2:
        nametag = arg_lst[0]+' '+arg_lst[1]
        print(f"length of arg = 2 / {nametag}")
    try:
        nametag_split = re.split(r"#", nametag)
        print(nametag_split)
    except Exception as e:
        return

    try:
        print(nametag_split[0])
        print(nametag_split[1])
        acc = valo.get_account_details_by_name('v1', nametag_split[0], nametag_split[1])
        logging.debug('add_account', f"PUUID of Added Account: {acc.to_dict()['puuid']}")
        account_documents_list.append(
            {"name": acc.to_dict()['name'], 
            "tag": acc.to_dict()['tag'], 
            "puuid": acc.to_dict()['puuid'], 
            "region": acc.to_dict()['region']
            }
        )
        print(account_documents_list)
    # if first method (account_details) throws exception, try an alternative method (lifetime_matches)
    except Exception as e:
        logging.error('add_account', "get_account_details_by_name: "+str(e))
        try:
            acc = valo.get_lifetime_matches_by_name_v1(version='v1', region='na', name=nametag_split[0], tag=nametag_split[1], size=1)
            logging.debug('add_account', f"PUUID of Added Account: {acc[0].stats.puuid}")
            account_documents_list.append(
                {"name": nametag_split[0], 
                "tag": nametag_split[1], 
                "puuid": acc[0].stats.puuid, 
                "region": "na"
                }
            )
            print(account_documents_list)
        except Exception as e:
            logging.error('add_account', "get_lifetime_matches_by_name_v1: "+str(e))
            return e

    client = mongodb_util.createClient(uri, '1')
    mongodb_util.client_ping(client=client)
    #db
    db = client.valorant

    #collection
    users = db.users
    stats = db.lifetime_stats
    mmr = db.mmr

    try:
        user_exists = users.find_one({'id': usr[0]})
        if user_exists == None:
            logging.debug('add_account', f'User does not exist in DB\nAdding user with information:\n{usr_info}')
            new = users.insert_one(usr_info)
            usr_oid = new.inserted_id
        else:
            logging.debug('add_account', f"User {user_exists['name']} exists with Object ID: {user_exists['_id']}")
            usr_oid = user_exists['_id']

        for account in account_documents_list:
            acc_exists = users.find_one({'accounts.puuid': account['puuid']})
            # if account already exists in db, then exit out
            if acc_exists != None:
                e = f"Error: {account['name']}#{account['tag']} already belongs to a user!"
                logging.error('add_account', f"Error: account {account['name']}#{account['tag']} already exists in DB (belongs to user: {acc_exists['name']})")
                return e
            else:
                logging.info('add_account', f"Account: {account['name']}#{account['tag']} INSERT...")
                
                users.update_one({"_id": usr_oid}, {'$push': {"accounts": account}}) # account is a dict object
                # mongodb_util.update_document(collection=stats, filter={'puuid':account['puuid']}, update_data={'$set': {'puuid': account['puuid']}}, get_updated_doc=True, upsert=True)
                # mongodb_util.update_document(collection=mmr, filter={'puuid':account['puuid']}, update_data={'$set': {'puuid': account['puuid']}}, get_updated_doc=True, upsert=True)
                new_docs = [{'puuid': account['puuid']}]
                mongodb_util.insert_into_collection(collection=stats, documents= new_docs)
                mongodb_util.insert_into_collection(collection=mmr, documents= new_docs)
                lifetime_stats_updater(stats=stats, logger=logging, puuid=account['puuid'])
                mmr_updater(mmr=mmr, logger=logging, puuid=account['puuid'])
                logging.info('add_account', f"Account: {account['name']}#{account['tag']} SUCCESS!! ")
                logging.info('add_account', f"{usr[1]} successfully added {len(account_documents_list)} Account(s) to the DB")
                logging.info('add_account', f"DB Results: {users.find_one({'_id': usr_oid})}")

    except pymongo.errors.OperationFailure:
        logging.error('add_account', "An authentication error was received. Are you sure your database user is authorized to perform write operations?")
        sys.exit(1)
    return True

def remove_account(arg_lst, usr): 
    err = 0
    # for acc in arg_list:
    #     match = re.match(r'(.+)#(.+)', acc)
    #     account.append((match.group(1), match.group(2)))
    
    if len(arg_lst) == 1:
        nametag = arg_lst[0]
        print(f"length of args = 1 / {nametag}")

    elif len(arg_lst) == 2:
        nametag = arg_lst[0]+' '+arg_lst[1]
        print(f"length of arg = 2 / {nametag}")
    try:
        nametag_split = re.split(r"#", nametag)
        print(nametag_split)
    except Exception as e:
        return

    # if non-existing account provided, return error code 4
    try:
        acc = valo.get_account_details_by_name('v1', nametag_split[0], nametag_split[1])
        puuid = acc.to_dict()['puuid']
    except Exception as e:
        logging.error("remove_account", "get_account_details_by_name: "+str(e))
        try:
            acc = valo.get_lifetime_matches_by_name_v1(version='v1', region='na', name=nametag_split[0], tag=nametag_split[1], size=1)
            puuid = acc[0].stats.puuid
        except Exception as e:
            logging.error("remove_account", "get_lifetime_matches_by_name_v1: "+str(e))
            err = 4
            return err
    

    client = mongodb_util.createClient(uri, '1')
    mongodb_util.client_ping(client=client)

    #db
    db = client.valorant

    #collection
    users = db.users
    stats = db.lifetime_stats
    mmr = db.mmr
    
    user_exists = users.find_one({'id': usr[0]})
    acc_exists = users.find_one({'accounts.puuid': puuid})
    user_acc_exists = users.find_one({'$and':[{'id': usr[0]}, {'accounts.puuid': puuid}]})

    try:
        # if user does not exist in the db
        if user_exists == None:
            logging.error('remove_account', f'Error: User Account {usr} Does Not Exist in DB!')
            err = 1
            return err 
        # if user exists but valo account doesn't exist
        elif user_exists != None and acc_exists == None:
            logging.error('remove_account', f'Error: Valorant Account {nametag} Does Not Exist in DB!')
            err = 2
            return err
        # if user exists but valo account is not in the user's document
        elif user_exists != None and user_acc_exists == None:
            print('========================================================================================')
            print(f'Error: Valorant Account {nametag} Belongs to a Different User!')
            print(f'Valorant Account {nametag} Belongs to {acc_exists["name"]}!')
            print('========================================================================================')
            err = 3
            return err
        # delete from account from associated user
        else:
            logging.info('remove_account', f"User: {user_exists['name']} exists with Object ID: {user_exists['_id']}")
            logging.info('remove_account', f"Account: {nametag} Exists in User: {user_exists['name']}'s Document!")
            usr_filter = {'id': usr[0]}
            misc_filter = {'puuid': puuid}
            update_data = {'$pull': {'accounts': {'puuid': puuid}}}
            try:
                result = mongodb_util.update_document(users, usr_filter, update_data, True, False)
                mongodb_util.delete_document(stats, misc_filter)
                mongodb_util.delete_document(mmr, misc_filter)
                if result != None:
                    logging.info('remove_account', f"{nametag} Successfully Deleted From {user_exists['name']}'s Document!")
            except Exception as e:
                print(e)
            return err 
        
    except pymongo.errors.OperationFailure as e:
        print(e)
        sys.exit(1)


def account_kd(puuid, size=None):
    version='v1'
    region='na'
    size=size
    kills, deaths, kdr = ([] for i in range(3))
    n = ctr = exclude = 0
    avg_k = avg_d = avg_kd = 0
    if size == None:
        details = valo.get_lifetime_matches_by_puuid_v1(version=version, region=region, puuid=puuid)
        size = len(details)

    else:
        details = valo.get_lifetime_matches_by_puuid_v1(version=version, region=region, puuid=puuid, size=size)
        size=size


    while n < size:
        if details[n].meta.mode == 'Competitive':
            kills.append(details[n].stats.kills)
            deaths.append(details[n].stats.deaths)
            kdr.append(round(kills[ctr]/deaths[ctr], 2))
            # print(f'Match {n+1}: Kills: {kills[ctr]} / Deaths: {deaths[ctr]} / KDR: {kdr[ctr]}')
            ctr += 1
        else: 
            # print(f'Excluding Match: {n+1} | Game mode: {details[n].meta.mode}')
            exclude += 1
        n += 1
        
    if ctr > exclude or ctr > 0:
        avg_k = round(mean(kills), 2)
        avg_d = round(mean(deaths), 2)
        avg_kd = round(mean(kdr), 2)
    else:
        pass

    return kills, deaths, kdr, avg_k, avg_d, avg_kd, exclude, ctr

def account_hs(puuid, size=None):
    version = 'v1'
    region = 'na'
    hs_ratio, head, body, leg = ([] for i in range(4))
    n = ctr = exclude = avg_h = avg_b = avg_l = avg_hs = 0
    if size == None:
        details = valo.get_lifetime_matches_by_puuid_v1(version=version, region=region, puuid=puuid)
        size = len(details)
    else:
        details = valo.get_lifetime_matches_by_puuid_v1(version=version, region=region, puuid=puuid, size=size)
        size=size
    # print(f'\n{id[0]}#{id[1]} Hit Stats Based on {size} Matches')

    while n < size:
        if details[n].meta.mode == 'Competitive':
            head.append(details[n].stats.shots.head)
            body.append(details[n].stats.shots.body)
            leg.append(details[n].stats.shots.leg)
            hs_ratio.append(round(head[ctr]/(body[ctr]+leg[ctr]), 2))
            # print(f'Match {n+1}: Head: {head[ctr]} / Body: {body[ctr]} / Leg: {leg[ctr]} / HS Ratio: {hs_ratio[ctr]}')
            ctr += 1
        else:
            # print(f'Excluding Match: {n+1} | Game mode: {details[n].meta.mode}')
            exclude += 1
        n += 1
    if ctr > exclude or ctr > 0:
        avg_h = round(mean(head), 2)
        avg_b = round(mean(body), 2)
        avg_l = round(mean(leg), 2)
        avg_hs = round(mean(hs_ratio), 2)
    else:
        pass

    return head, body, leg, hs_ratio, avg_h, avg_b, avg_l, avg_hs, exclude, ctr

# leaderboard function
def leaderboard():
    player_list = []
    player_info = {'disc_name':'',
            'acc_name': '',
            'acc_tag': '',
            'acc_puuid': '',
            'kd_stat': '',
            'rank': '',
            }
    
    client = mongodb_util.createClient(uri, '1')
    mongodb_util.client_ping(client=client)

    db = client.valorant
    users = db.users
    stats = db.lifetime_stats
    mmr = db.mmr
    data = users.find()

    # creates a list of dicts for all valorant accounts on the db
    for user in data:
        # if the discord user has at least one account associated 
        if len(user['accounts']) > 0:
            for i in range(0,len(user['accounts'])):
                player_info['disc_name'] = user['name']
                player_info['acc_name'] = user['accounts'][i]['name']
                player_info['acc_tag'] = user['accounts'][i]['tag']
                player_info['acc_puuid'] = user['accounts'][i]['puuid']
                stats_info = mongodb_util.get_documents(
                    collection=stats,
                    filter={'puuid': player_info['acc_puuid']}
                )
                player_info['kd_stat'] = stats_info[0]['avg_kdr']
                # kd = account_kd(puuid=f"{player_info['acc_puuid']}")
                # player_info['kd_stat'] = kd[5]
                # rank = valo.get_mmr_details_by_puuid_v2(version='v2', region='na', puuid=player_info['acc_puuid'])
                # player_info['rank'] = rank.current_data.currenttierpatched
                mmr_info = mongodb_util.get_documents(
                    collection=mmr,
                    filter={'puuid': player_info['acc_puuid']}
                )
                player_info['rank'] = mmr_info[0]['rank_name']
                player_list.append(player_info.copy())
        # no accounts associated with this discord user
        # else:
        #     player_info['disc_name'] = user['name']
        #     player_info['acc_name'] = None
        #     player_info['acc_tag'] = None
        #     player_info['kd_stat'] = None
        #     player_info['rank'] = None
        #     player_list.append(player_info.copy())

    sorted_list = sorted(player_list, key=lambda x: x['kd_stat'] or 0.0, reverse=True)
    return sorted_list

# profile of a valorant account
def profile(usr_id):
    state = 1 
    player_list = []
    kd_list = []
    hs_list = []
    player_info = {
        'acc_name': '',
        'acc_tag': '',
        'acc_puuid':'',
        'kd_stat': '',
        'hs_stat': '',
        'rank_name': '',
        'tier_num': ''
        }

    client = mongodb_util.createClient(uri, '1')
    mongodb_util.client_ping(client=client)

    db = client.valorant
    users = db.users
    stats = db.lifetime_stats
    mmr = db.mmr

    usr_info = users.find_one({'id': usr_id})
    if usr_info == None:
        print(f'User does not exist in DB!')
        state = 1
        return state
    else:
        if len(usr_info['accounts']) < 1:
            print('No Associated Valorant Accounts')
        # at least one valorant account associated
        elif len(usr_info['accounts']) > 1:
            for i in range(0,len(usr_info['accounts'])):
                player_info['acc_name'] = usr_info['accounts'][i]['name']
                player_info['acc_tag'] = usr_info['accounts'][i]['tag']
                player_info['acc_puuid'] = usr_info['accounts'][i]['puuid']

                # kd = account_kd(puuid=f"{player_info['acc_puuid']}")
                # player_info['kd_stat'] = kd[5]
                stats_info = mongodb_util.get_documents(
                    collection=stats,
                    filter={'puuid': player_info['acc_puuid']}
                )
                player_info['kd_stat'] = stats_info[0]['avg_kdr']
                player_info['hs_stat'] = stats_info[0]['avg_headshot']
                # rank = valo.get_mmr_details_by_puuid_v2(version='v2', region='na', puuid=player_info['acc_puuid'])
                # player_info['rank_name'] = rank.current_data.currenttierpatched
                # player_info['tier_num'] = rank.current_data.currenttier
                mmr_info = mongodb_util.get_documents(
                    collection=mmr,
                    filter={'puuid': player_info['acc_puuid']}
                )
                player_info['rank_name'] = mmr_info[0]['rank_name']
                player_info['tier_num'] = mmr_info[0]['tier_num']
                # hs = account_hs(puuid=f"{player_info['acc_puuid']}")
                # player_info['hs_stat'] = hs[7]
                player_list.append(player_info.copy())

    sorted_list = sorted(player_list, key=lambda x: x['tier_num'] or 0, reverse=True)
    for i in range(len(sorted_list)):
        hs_list.append(sorted_list[i]['hs_stat'])
        kd_list.append(sorted_list[i]['kd_stat'])
    avg_hs = round(mean(hs_list), 2)
    avg_kd = round(mean(kd_list), 2)

    return sorted_list, avg_hs, avg_kd
         
