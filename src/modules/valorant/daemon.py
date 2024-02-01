from collections import Counter
import sched
import time
import valo_api as valo
from valorant import valo_commands

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from util import config, logger
from mongodb import mongodb_util 
from util.valo_utils import nametag_updater, mmr_updater, lifetime_stats_updater, all_agent_update 

logging = logger.Logger('daemon', 'daemon_logger')

configuration = config.Config()
api_key = configuration.valo_api_key
valo.set_api_key(api_key=api_key)
uri = configuration.mongodb_uri

client = mongodb_util.createClient(uri, '1')
mongodb_util.client_ping(client=client)
db = client.valorant
stats = db.lifetime_stats
users = db.users
mmr = db.mmr

ct = time.localtime()
time_str = time.strftime("%H:%M:%S", ct)

event_scheduler = sched.scheduler(time.time, time.sleep)

def handler():
    # ct = time.localtime()
    # time_str = time.strftime("%H:%M:%S", ct)
    print('Updating DB...')
    nametag_updater(users=users, logger=logging)
    mmr_updater(mmr=mmr, logger=logging)
    lifetime_stats_updater(stats=stats, logger=logging)
    logging.info('daemon', 'DB Update Routine Complete!')
    event_scheduler.enter(3600, 1, handler) # 1 hour interval
    event_scheduler.run()

handler()