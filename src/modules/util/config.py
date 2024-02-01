import configparser
import os

class Config:
    discord_auth_token = ''
    discord_command_prefix = ''
    valo_api_key = ''
    mongodb_api_version = '' 
    mongodb_uri = ''
    log_location = ''
    time_zone = ''
    openai_api_key = ''
    language = ''

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), '../../../config/', 'config.ini'))

        #config.read('../../../config/config.ini')
        use_local_config = config['GENERAL'].getboolean('LOCAL')
        if use_local_config:
            config.read(os.path.join(os.path.dirname(__file__), '../../../config/', 'config_local.ini'))

            #config.read('../../../config/config_local.ini')
            
        Config.discord_auth_token = config['DISCORD']['AUTH_TOKEN']
        Config.discord_command_prefix = config['DISCORD']['COMMAND_PREFIX']
        Config.valo_api_key = config['VALORANT']['API_KEY']
        Config.mongodb_api_version = config['DB']['API_VERSION']
        Config.mongodb_uri = config['DB']['URI']
        Config.log_location = os.path.join(os.path.dirname(__file__), config['GENERAL']['LOG_LOCATION'])
        Config.time_zone = config['GENERAL']['TIME_ZONE']
        Config.language = config['GENERAL']['LANGUAGE']
        Config.openai_api_key = config['OPENAI']['API_KEY']
        Config.local = use_local_config
