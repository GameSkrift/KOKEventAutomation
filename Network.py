import requests
import logging
import json
import msgpack
import io
import os
from zipfile import ZipFile

APIs = {
    'nutaku': {
        'auth': 'https://ntk-login-api.kokmm.net',
        'data': 'https://ntk-zone-api.kokmm.net',
        'battle': 'https://ntk-zone-battle.kokmm.net'
    },
    'steam':{
        'auth': '',
        'data': '',
        'battle': ''
    },
    'taiwan': {
        'auth': '',
        'data': '',
        'battle': ''
    },
    'japan': {
        'auth': '',
        'data': '',
        'battle': ''
    }
}

class Network:

    def __init__(self, platform, nutaku_id, user_id):
        self.name = "Network"
        self.nid = nutaku_id
        self.uid = user_id
        self.prefix = int(str(user_id)[:3])
        self.platform = platform
        self.session = None
        self.socket_token = None
        self.API_BASE = APIs[platform]

    """
        Logs into the kok server 
        This function should not be called outside of the
    """
    def __login(self) -> bool:
        try:
            # initial login request
            url = '{}/api/auth/login/game_account'.format(self.API_BASE['auth'])
            payload = { "login_id": self.nid, "login_type": 0, "access_token": "", "pw": self.nid }
            r = requests.post(url, payload)

            # collect session
            login_info = r.json()['response']
            self.session = str(login_info['session_id'])
            self.account_id = login_info['account_id']
            print(r.url)

            # final request
            url = "{}/api/auth/login/user?nutaku_id={}".format(self.API_BASE['auth'], self.nid)
            payload = { "server_prefix": self.prefix, "account_id": self.account_id, "session_id": self.session }
            r = requests.post(url, payload)

            #get ingame chat socket token
            self.socket_token = r.json()['response']['socket_token']


            print(f"Login success - platform: {self.platform}, nid: {self.nid}, uid: {self.uid}, prefix: {self.prefix}, session: {self.session}, socket_token: {self.socket_token}")
            return True

        except Exception as e:
            print(f"Login attempt failed: {e}")
            return False


    """
        Generic get request with failure retry
    """
    def get(self, url, retry=False):
        original = url
        url = url.replace("user_id=", "user_id={}".format(self.uid))
        url = url.replace("server_prefix=", "server_prefix={}".format(self.prefix))
        url = url.replace("session_id=", "session_id={}".format(self.session))

        try:         
            response = requests.get(url)
            r = response.json()

            if not r["success"]:
                error = r["error_message"]
                print(f"ERROR_NETWORK_GET: {error}.")

                if not retry and error == "BAD_REQUEST" or error == "SESSION_TIME_EXPIRED":
                    print(f"Relogging to fix the issue...")
                    self.__login()
                    return self.get(original, True)
                
                #print(f"ERROR_NETWORK_GET: {r}")
                
            return r

        except:
            print(f"ERROR_NETWORK_GET_UKNOWN: Something went wrong URL - {url}")
            raise

    """
        Generic post request with failure retry
    """
    def post(self, url, payload, retry=False):
        original = url
        url = url.replace("user_id=", "user_id={}".format(self.uid))
        url = url.replace("server_prefix=", "server_prefix={}".format(self.prefix))
        url = url.replace("session_id=", "session_id={}".format(self.session))

        try:         
            response = requests.post(url, payload)
            r = response.json()

            if not r["success"]:
                error = r["error_message"]

                if not retry and error == "BAD_REQUEST" or error == "SESSION_TIME_EXPIRED":
                    print(f"ERROR_NETWORK_POST: {error}. Relogging to fix the issue...")
                    self.__login()
                    return self.post(original, payload, True)
                
                #print(f"ERROR_NETWORK_POST: {r}")
                
            return r

        except:
            print(f"ERROR_NETWORK_POST_UKNOWN: Something went wrong URL - {url}")
            raise


    """
        the list of game asset files
    """
    def assets(self):
        url = self.API_BASE['data'] + "/api/system/assets?asset_v=0&device_type=android"
        return self.get(url)

    """
        the list of secret asset files
    """
    def secrets(self):
        url = self.API_BASE['data'] + "/api/system/assets?asset_v=0&device_type=androidsecret"
        return self.get(url)

    """
        downloads a game file
    """
    def gameFile(self, filename):
        assets = self.assets()

        filePath = None
        for fileData in assets['response']['assets']['asset_patchs']:
            if fileData[0] == filename:
                filePath = fileData[1]

        if filePath == None:
            print(f"Could not find asset file with the name {filename}")
            return
        
        url = assets['response']['download_url'] + filePath
        response = requests.get(url)

        return response
    

    def byteGameFile(self, zipFileName, filename):
        directory = './config/'
        if not os.path.exists(directory):
            os.mkdir(directory)
        
        data = self.gameFile(zipFileName).content
        zip_stream = io.BytesIO(data)

        with ZipFile(zip_stream, 'r') as zip_ref:
            zip_ref.extractall(directory)
            with open(directory+filename, 'br') as f:
                return msgpack.unpackb(f.read(), raw=False, strict_map_key=False)


    """
        get the users account info
    """
    def user(self):
        url = self.API_BASE['data']+"/api/mall/getUserGlobalEventRecord?user_id=&session_id=&server_prefix="
        return self.get(url)['me']


    """
        return a list of pets
    """
    def pets(self):
        url = self.API_BASE['data']+"/api/user/pet/info?user_id=&session_id=&server_prefix="
        return self.get(url)


    """
        return a list of goddesses 
    """
    def goddesses(self):
        url = self.API_BASE['data']+"/api/user/god/info?user_id=&session_id=&server_prefix="
        return self.get(url)

    """
        return a list of teams
    """
    def teams(self):
        url = self.API_BASE['data']+"/api/user/pet-team/info?user_id=&session_id=&server_prefix="
        return self.get(url)

    """
        returns all items in the players backpack
    """
    def inventory(self):
        url = self.API_BASE['data']+"/api/user/backpack?user_id=&session_id=&server_prefix="
        return self.get(url)

    
    """
        returns all equipment and all equipped
        result['response']['user_equipments']  
        result['response']['equipment_usage']
    """
    def equipment(self):
        url = self.API_BASE['data']+"/api/user/equipment/info?user_id=&session_id=&server_prefix="
        return self.get(url)

    """
        returns a list of all owned flags
    """
    def flags(self):
        url = self.API_BASE['data']+"/api/slg/flag/records?user_id=&session_id=&server_prefix="
        return self.get(url)
    
    """
        Equips a piece of gear or an artifact onto a pet
        petSerial - the unique serial id of the target pet
        equipmentSerial - the unique serial id of the piece of equipment
    """
    def equip(self, petSerial, equipmentSerial):
        url = self.API_BASE['data']+"/api/user/equipment/equip?user_id=&session_id=&server_prefix="
        payload = {
            'pet_serial_id': petSerial,
            'eq_serial_id': equipmentSerial
        }

        return self.post(url, payload)
    

    def flag_equip(self, petSerial, flagSerial):
            url = self.API_BASE['data']+"/api/slg/flag/equip?user_id=&session_id=&server_prefix="
            payload = {
                'pet_serial_id': petSerial,
                'flag_serial_id': flagSerial
            }

            return self.post(url, payload)


    def unequip(self, petSerial, equipmentSerial):
            url = self.API_BASE['data']+"/api/user/equipment/unequip?user_id=&session_id=&server_prefix="
            payload = {
                'pet_serial_id': petSerial,
                'eq_serial_id': equipmentSerial
            }

            return self.post(url, payload)


    def flag_unequip(self, petSerial, flagSerial):
            url = self.API_BASE['data']+"/api/slg/flag/unequip?user_id=&session_id=&server_prefix="
            payload = {
                'pet_serial_id': petSerial,
                'flag_serial_id': flagSerial
            }

            return self.post(url, payload)
    
    """
        get the current state of the sexual dating event
    """
    def event_sd_record(self, eventId):
        url = self.API_BASE['data'] + "/api/sexual_dating/records?user_id=&session_id=&server_prefix=&event_id=" + str(eventId)
        return self.get(url)
    
    """
        claims the wine siting in the machine
    """
    def event_sd_collect(self, eventId):
        url = self.API_BASE['data'] + "/api/sexual_dating/claimItemExplore?user_id=&session_id=&server_prefix="
        data = { 'event_id': eventId }

        return self.post(url, data)
    
    """
        get the current state of the multiverse event
    """
    def event_mv_record(self):
        url = self.API_BASE['data'] + "/api/multiverse_dating/records?user_id=&session_id=&server_prefix="
        return self.get(url)

    """
        claims the wine siting in the machine
    """
    def event_mv_collect(self, eventId):
        url = self.API_BASE['data'] + "/api/multiverse_dating/explore/claim?user_id=&session_id=&server_prefix="
        data = { 'event_id': eventId }

        return self.post(url, data)
    
    def event_sd_click(self, eventId, wineId, chapterId, optionIndex, optionCost, clicks):        
        url = self.API_BASE['data'] + '/api/sexual_dating/option/click?user_id=&session_id=&server_prefix='
        data = {
            'event_id': eventId, 
            'chapter_id': chapterId, 
            'option_index': optionIndex, 
            'amount': clicks, 
            'cost': json.dumps([{"asset_type":6,"asset_id":wineId,"amount":optionCost}])
            }
        return self.post(url, data)
    
    def event_sd_claim_chapter_rewards(self, eventId, chapter):
        url = self.API_BASE['data'] + '/api/sexual_dating/claim?user_id=&session_id=&server_prefix='
        data = { 'event_id': eventId, 'chapter_id': chapter }
        
        return self.post(url, data)
    
    def event_sd_purchase_machine(self, eventId, targetTier, package):
        url = self.API_BASE['data'] + '/api/sexual_dating/upgradeExploreItemTier?user_id=&session_id=&server_prefix='
        data = {
            'event_id': eventId,
            'tier': targetTier,
            'cost': json.dumps([{"asset_type":6,"asset_id":package[0]['asset_id'],"amount":package[0]['amount']}])
        }
        
        return self.post(url, data)
    
    def event_sd_message_save_point(self, eventId, chapterId, messageId):
        url = self.API_BASE['data'] + '/api/sexual_dating/saveMessage?user_id=&session_id=&server_prefix='
        data = {
            'event_id': eventId,
            'chapter_id': chapterId,
            'message_id': messageId
        }

        return self.post(url, data)
    
    def event_sd_choose_message(self, eventId, chapterId, messageId, selectionId):
        url = self.API_BASE['data'] + '/api/sexual_dating/saveMessage?user_id=&session_id=&server_prefix='
        data = {
            'event_id': eventId,
            'chapter_id': chapterId,
            'message_id': messageId,
            'selection': selectionId
        }

        return self.post(url, data)
