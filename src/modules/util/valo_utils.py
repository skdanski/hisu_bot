from pymongo import *
from mongodb import mongodb_util
from util import config
from valorant import valo_commands
from collections import Counter
import valo_api as valo
import re

configuration = config.Config()
uri = configuration.mongodb_uri
api_key = configuration.valo_api_key

# util for updating puuid into db
# shouldn't need to manually do this in the future.
def puuid_update():
    client = mongodb_util.createClient(uri, '1')
    mongodb_util.client_ping(client=client)

    db = client.valorant
    users = db.users
    stats = db.lifetime_stats
    mmr = db.mmr
    data = users.find()

    for user in data:
        if len(user['accounts']) > 0:
            for i in range(0,len(user['accounts'])):
                stat_col = mongodb_util.update_document(
                    collection=stats, 
                    filter={'puuid':user['accounts'][i]['puuid']}, 
                    update_data={'$set': {'puuid':user['accounts'][i]['puuid']}}, 
                    get_updated_doc=True, 
                    upsert=True
                    )
                mmr_col = mongodb_util.update_document(
                    collection=mmr, 
                    filter={'puuid':user['accounts'][i]['puuid']}, 
                    update_data={'$set': {'puuid':user['accounts'][i]['puuid']}}, 
                    get_updated_doc=True, 
                    upsert=True
                    )
                print(stat_col)
                print(mmr_col)

# try get_account_details_by_name_v1 and get_lifetime_matches_by_name_v1 to make sure account actually has info
# returns puuid or error
def try_two_endpoints_puuid(name, tag):
    # try block to use a backup endpoint if first endpoint fails
    try:
        acc = valo.get_account_details_by_name_v1(version='v1', name=name, tag=tag)
        puuid = acc.puuid
        return puuid
    except:
        try:
            acc = valo.get_lifetime_matches_by_name_v1(version='v1', region='na', name=name, tag=tag, size=1)
            puuid = acc[0].stats.puuid
            return puuid
        except Exception as e:
            return str(e)

# helper function for valorant nametag resolution (whitespaced and nonwhitespaced) 
def nametag_resolver(arg):
    result_lst = []
    if len(arg) < 1:
        message = '```Error: Too few arguments```'
        return message
    # one arg probably means a "name#tag" arg
    elif len(arg) == 1:
        try:
            nametag=str(arg[0]).split('#')
            result = try_two_endpoints_puuid(name=nametag[0], tag=nametag[1])
            title=f"{arg[0]}'s Stats"
        except Exception as e:
            return str(e) 

    elif len(arg) == 2:
        # check to see if arg[1] contains invalid characters (symbols)
        hit = re.search(r"(\w#\w+\W)|(\w#\W)|(\W\w+#)|(\w\W+#)", arg[1])
        if hit is None:
            pass
        elif hit.group(1) or hit.group(2) or hit.group(3) or hit.group(4):
            message = "```Invalid Arguments: Check to see if you have any special characters(symbols) in your input!```"
            return message

        # if arg[1] is a valid int, then arg[0] must be a nametag
        try:
            size = int(arg[1])
            nametag=str(arg[0]).split('#')
            result = try_two_endpoints_puuid(name=nametag[0], tag=nametag[1])
            title=f"{arg[0]}'s Stats"
            result_lst.append(size)
        # if not then arg[0] must be part of the nametag (ex: pizza cat#6874)
        except:
            nametag=arg[0]+' '+arg[1]
            nametag_split = re.split(r"#", nametag)
            result = try_two_endpoints_puuid(name=nametag_split[0], tag=nametag_split[1])
            title=f"{nametag}'s Stats"
    elif len(arg) == 3:
        # check to see if arg[1] contains invalid characters (symbols)
        hit = re.search(r"(\w#\w+\W)|(\w#\W)|(\W\w+#)|(\w\W+#)", arg[1])
        if hit is None:
            pass
        elif hit.group(1) or hit.group(2) or hit.group(3) or hit.group(4):
            message = "```Invalid Arguments: Check to see if you have any symbols other than '#' in your input!```"
            return message
        # check to see if arg[2] is an int
        try:
            size = int(arg[2])
            nametag=arg[0]+' '+arg[1]
            nametag_split = re.split(r"#", nametag)
            result = try_two_endpoints_puuid(name=nametag_split[0], tag=nametag_split[1])
            title=f"{nametag}'s Stats"
            result_lst.append(size)
        # if arg[2] is not a valid int, throw exception
        except Exception as e:
            message = '```Invalid arguments: Size should be a number!```'
            return message
    elif len(arg) > 3:
        message = '```Too many arguments!```'
        return message
    result_lst.append(result)
    result_lst.append(title)
    return result_lst

# updates agent list
# size = number of matches  
def all_agent_update(details, size, logger):
    agent_dic_lst = []
    agent_lst = []
    agent_info = {
        'name': '',
        'agent_id':'',
        'kills':0,
        'deaths':0,
        'avg_kills':0.0,
        'avg_deaths':0.0,
        'total_matches':0
    }

    for i in range(0, size):
        agent_name = details[i].stats.character.name
        agent_id = details[i].stats.character.id
        kills = details[i].stats.kills
        deaths = details[i].stats.deaths
        logger.debug('all_agent_update', f'agent_name: {agent_name}, agent_id: {agent_id}, kills: {kills}, deaths: {deaths}') 
        # check to see if the agent exists in the list of agent names 
        if agent_name in agent_lst:
            # search where the agent name is in the list (find the index)
            # then append the data to the appropriate index of the list of dicts
            idx = agent_lst.index(agent_name)
            agent_dic_lst[idx]['kills'] += kills
            agent_dic_lst[idx]['deaths'] += deaths
            agent_dic_lst[idx]['total_matches'] += 1
            agent_dic_lst[idx]['avg_kills'] = agent_dic_lst[idx]['kills']/agent_dic_lst[idx]['total_matches'] 
            agent_dic_lst[idx]['avg_deaths'] = agent_dic_lst[idx]['deaths']/agent_dic_lst[idx]['total_matches']

        # agent doesn't exist in preexisting list -> add it and then add the information
        else:
            agent_lst.append(agent_name)
            agent_info['name'] = agent_lst[-1]
            agent_info['agent_id'] = agent_id
            agent_dic_lst.append(agent_info.copy())
            idx = agent_lst.index(agent_name)
            agent_dic_lst[idx]['kills'] += kills
            agent_dic_lst[idx]['deaths'] += deaths
            agent_dic_lst[idx]['total_matches'] += 1
            agent_dic_lst[idx]['avg_kills'] = agent_dic_lst[idx]['kills']/agent_dic_lst[idx]['total_matches'] 
            agent_dic_lst[idx]['avg_deaths'] = agent_dic_lst[idx]['deaths']/agent_dic_lst[idx]['total_matches']       
        logger.debug('all_agent_update', f'Iteration {i}: {agent_dic_lst}')
    
    logger.info('all_agent_update', 'all_agent_update DONE')
    return agent_dic_lst

# driver for updating the lifetime_stats collection
def lifetime_stats_updater(stats, logger, puuid: str | None = None):
    print("Lifetime Stats Updating...")
    # if a puuid is provided, only perform update on one account(puuid)
    if puuid is not None:
        data = stats.find({'puuid': puuid})
    else:
        data = stats.find()
    try:
        for user in data:
            puuid = user['puuid']
            
            # updates total_matches, avg_kills, avg_deaths
            kd_stats = valo_commands.account_kd(puuid)
            logger.debug('lifetime_stats_updater', 'Number of matches: ' + str(kd_stats[7]))
            kd_update = mongodb_util.update_document(
                collection=stats,
                filter={'puuid': puuid},
                update_data={'$set': {'total_matches': kd_stats[7], 'avg_kills': kd_stats[3], 'avg_deaths': kd_stats[4], 'avg_kdr': kd_stats[5]}},
                get_updated_doc=True,
                upsert=True
            )
            logger.info('lifetime_stats_updater', f'kd_update DONE')
            logger.debug('lifetime_stats_updater', f'kd_update Results: {kd_update}')

            # updates avg_headshot
            hit_stats = valo_commands.account_hs(puuid)
            hit_update = mongodb_util.update_document(
                collection=stats,
                filter={'puuid': puuid},
                update_data={'$set': {'avg_headshot': hit_stats[7]}},
                get_updated_doc=True,
                upsert=True
            )
            logger.info('lifetime_stats_updater', f'hit_update DONE')
            logger.debug('lifetime_stats_updater', f'hit_update Results: {hit_update}')

            # updates last_match_id and last_played_timestamp
            last_match = valo.get_match_history_by_puuid_v3(version='v3', region='na', puuid=puuid, size=1)
            if len(last_match) < 1:
                # print("No Recent Match History")
                logger.warning('lifetime_stats_updater', f'last_match_update for {puuid} FAILED')
            else:
                last_match_update = mongodb_util.update_document(
                    collection=stats,
                    filter={'puuid': puuid},
                    update_data={'$set': {'last_match_id': last_match[0].metadata.matchid, 'last_played_timestamp': last_match[0].metadata.game_start_patched}},
                    get_updated_doc=True,
                    upsert=True
                )
                logger.info('lifetime_stats_updater', f'last_match_update SUCCESS')
                logger.debug('lifetime_stats_updater', f'last_match_update Results: {last_match_update}')

            agent_lst = []
            agent_query = valo.get_lifetime_matches_by_puuid_v1(version='v1', region='na', puuid=puuid)
            for i in range(0, kd_stats[7]):
                agent_lst.append(agent_query[i].stats.character.name)

            occurence_ctr = Counter(agent_lst)
            max_name = occurence_ctr.most_common(1)[0][0]
           
            # updates most_played_agent
            most_agent_update = mongodb_util.update_document(
                collection=stats,
                filter={'puuid': puuid},
                update_data={'$set': {'most_played_agent': max_name}},
                get_updated_doc=True,
                upsert=True
            )
            logger.info('lifetime_stats_updater', f'most_agent_update DONE')
            logger.debug('lifetime_stats_updater', f'most_agent_update Results: {most_agent_update}')

            # updates agent_list 
            agent_dic = all_agent_update(agent_query, kd_stats[7], logger)
            agent_dic_update = mongodb_util.update_document(
                collection=stats,
                filter={'puuid': puuid},
                update_data={'$set': {'agent_list': agent_dic}},
                get_updated_doc=True,
                upsert=True
            )
            logger.info('lifetime_stats_updater', f'agent_dic_update DONE')
            logger.debug('lifetime_stats_updater', f'agent_dic_update Results: {agent_dic_update}')

    except Exception as e:
        print("Error in Updating lifetime_stats!")
        logger.error('lifetime_stats_updater', str(e))

# driver for updating mmr details
# [optional] puuid arg for change_streams
def mmr_updater(mmr, logger, puuid: str | None = None):
    print("MMR Updating...")
    if puuid is not None:
        data = mmr.find({'puuid': puuid})
    else:
        data = mmr.find()
    try:
        for user in data:
            puuid = user['puuid']
            rank_details = valo.get_mmr_details_by_puuid_v2(version="v2", region='na', puuid=puuid)
            mmr_col = mongodb_util.update_document(
                collection=mmr, 
                filter={'puuid':puuid}, 
                update_data={'$set': {'rank_name':rank_details.current_data.currenttierpatched, 'tier_num': rank_details.current_data.currenttier}}, 
                get_updated_doc=True, 
                upsert=True
                )
        logger.info('mmr_updater', f'mmr_update DONE')
        logger.debug('mmr_updater', f'mmr_update Results: {mmr_col}')

    except Exception as e:
        print("Error in Updating mmr!")
        logger.error('mmr_updater', str(e))

# driver for updating nametag information
def nametag_updater(users, logger):
    print("Nametag Updating...")
    data = users.find()
    try:
        for user in data:
            for i in range(0, len(user['accounts'])):
                puuid = user['accounts'][i]['puuid']
                nametag = valo.get_account_details_by_puuid_v1(version='v1', puuid=puuid)
                logger.debug('nametag_updater', f'puuid of account {user["accounts"][i]["name"]}: ' + str(puuid))
                logger.debug('nametag_updater', f'Name in Riot DB: {nametag.name}')
                logger.debug('nametag_updater', f'Tag in Riot DB: {nametag.tag}')
                nametag_update = mongodb_util.update_document(
                    collection=users,
                    filter={'accounts': {'$elemMatch': {'puuid': str(puuid)}}},
                    update_data={'$set': {'accounts.$.name': nametag.name, 'accounts.$.tag': nametag.tag}},
                    get_updated_doc=True,
                    upsert=False
                )
                logger.debug('nametag_updater', f'Updated Name: {nametag_update["accounts"][i]["name"]}')
                logger.debug('nametag_updater', f'Updated Tag: {nametag_update["accounts"][i]["tag"]}')
    
    except Exception as e:
        print("Error in Updating nametag!")
        logger.error('nametag_updater', str(e))
