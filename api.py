# -*- coding: utf-8 -*-
import json
import requests

class GameApi:
    """ only support NTK version for now """
    auth_url = 'https://ntk-login-api.kokmm.net'
    data_url = 'https://ntk-zone-api.kokmm.net'
    battle_url = 'https://ntk-zone-battle.kokmm.net'
    
    def __init__(self):
        """ A class level of King of Kinks RESTful client implementation with a collection of its APIs.
        """
        # sync to database for web URIs
        self.auth = self.Auth(self.auth_url)
        self.user = self.User(self.data_url)
        self.accumulate_top_up = self.AccumulateTopUp(self.data_url)
        self.slg = self.Slg(self.data_url)
        self.crystal = self.Crystal(self.data_url)
        self.guild = self.Guild(self.data_url)
        self.guild_boss = self.GuildBoss(self.data_url, self.battle_url)
        self.world_boss = self.WorldBoss(self.data_url, self.battle_url)
        self.cycle_boss = self.CycleBoss(self.data_url, self.battle_url)
        self.event_boss = self.EventBoss(self.data_url, self.battle_url)
        self.sexual_dating = self.SexualDating(self.data_url)
        self.multiverse_dating = self.MultiverseDating(self.data_url)
        self.mega_pet_event = self.MegaEvent(self.data_url)
        self.pvp = self.Pvp(self.data_url, self.battle_url)
        self.pvp_3v3 = self.Pvp3v3(self.data_url, self.battle_url)

    class Auth:
        """ An inner class level of `/auth/login` API corresponding to `GameApi.auth_url`

        FROM `GameApi.auth_url`
        **POST** /api/auth/login/game_account
            - **PAYLOAD** { "login_id": [NUTAKU_ID], "login_type": 0, "access_token": "", "pw": [NUTAKU_ID] }
            - [NUTAKU_ID]: [1-9][0-9]*
        **POST** /api/auth/login/user?nutaku_id={}
            - **PAYLOAD** { "server_prefix": [SERVER_PREFIX], "account_id": [ACCOUNT_ID], "session_id": [SESSION_ID] }
            - [SERVER_PREFIX]: [1-9][0-9]{2}
            - [ACCOUNT_ID]: [0-9]{5}
            - [SESSION_ID]: [a-z0-9]{40}
        """
        def __init__(self, url):
            self.login = self._Login(url)
        class _Login:
            def __init__(self, url):
                # POST
                self.game_account = f"{url}/api/auth/login/game_account"
                self.user = f"{url}/api/auth/login/user?"

    class User:
        """ An inner class level of `/user` API corresponding to `GameApi.data_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: q={}&user_id={}&session_id={}&server_prefix={}
        
        FROM `GameApi.data_url`
        **GET** /api/user/info?[URI]
        **GET** /api/user/pet/info?[URI]
        **GET** /api/user/pet-team/info?[URI]
        **GET** /api/user/god/info?[URI]
        **GET** /api/user/equipment/info?[URI]
        **GET** /api/user/mail/get?[URI]
        **GET** /api/user/bundle_package/free?[URI]
        **GET** /api/user/daily_gold_package/record?[URI]
        **GET** /api/user/friend/search?[URI2]
        **GET** /api/user/friend/list?[URI]
        **GET** /api/user/friend/collect-and-send-fp-all?[URI]
        **GET** /api/user/friend/requesting-list?[URI]
        **GET** /api/user/friend/suggest-list?[URI]

        **POST** /api/user/equipment/equip?[URI]
            - **PAYLOAD** { "pet_serial_id": [PET_SERIAL_ID], "eq_serial_id": [EQ_SERIAL_ID] }
            - [PET_SERIAL_ID]: [a-z0-9]{40}
            - [EQ_SERIAL_ID]: [a-z0-9]{40}
        **POST** /api/user/equipment/unequip?[URI]
            - **PAYLOAD** { "pet_serial_id": [PET_SERIAL_ID], "eq_serial_id": [EQ_SERIAL_ID] }
            - [PET_SERIAL_ID]: [a-z0-9]{40}
            - [EQ_SERIAL_ID]: [a-z0-9]{40}
        **POST** /api/user/mail/claim-all?[URI]
            - **PAYLOAD** { "user_build_version": [VERSION] }
            - [VERSION]: [1-9][0-9]*
        **POST** /api/user/offline-reward/claim?
            - **PAYLOAD** { "user_id": [USER_ID], "server_prefix": [SERVER_PREFIX], "session_id": [SESSION_ID] }
            - [USER_ID]: [1-9][0-9]{12}
            - [SERVER_PREFIX]: [1-9][0-9]{2}
            - [SESSION_ID]: [a-z0-9]{40}
        **POST** /api/user/offline-reward/quick-claim?[URI]
            - **PAYLOAD** { "time_count": 7200, "cost_list": [ [COST_LIST] ] }
            - [COST_LIST]: {"asset_type":0,"asset_id":"0","amount":50|80|100|100|200}?
        **POST** /api/user/daily_gold_package/purchase?[URI]
            - **PAYLOAD** { "package_id": [PACKAGE_ID], "cost": [ [COST] ] }
            - [PACKAGE_ID]: [1-3]
            - [COST]: {"asset_type":0,"asset_id":"0","amount":30|60}?
        **POST** /api/mall/festival/daily-claim?[URI]
            - **PAYLOAD** { "event_id": 36 }
        **POST** /api/privilege/claim_daily_free_privilege_reward?[URI]
            - **PAYLOAD** { "now": [NOW] }
            - [NOW]: [1-9][0-9]{9}
        **POST** /api/mall/purchase?[URI]
            - **PAYLOAD** { "id": [ID], "amount": [AMOUNT] }
            - [ID]: 1001|1006|1013|[1-9][0-9]*
            - [AMOUNT]: [1-9][0-9]*
        **POST** /api/user/count_down_bonus/claim?[URI]
            - **PAYLOAD** { "event_id": 1, "step_id": [STEP_ID] }
            - [STEP_ID]: [1-5]
        **POST** /api/user/friend/send-request?[URI]
            - **PAYLOAD** { "user_id": [USER_ID] }
            - [USER_ID]: [1-9][0-9]{12}
        **POST** /api/user/friend/remove-fd?[URI]
            - **PAYLOAD** { "user_id": [USER_ID] }
            - [USER_ID]: [1-9][0-9]{12}
        **POST** /api/user/get-blacklist?[URI]
            - **PAYLOAD** { "target_user_id": [TARGET_USER_ID] }
            - [TARGET_USER_ID]: [1-9][0-9]{12}
        **POST** /api/user/remove-blacklist?[URI]
            - **PAYLOAD** { "target_user_id": [TARGET_USER_ID] }
            - [TARGET_USER_ID]: [1-9][0-9]{12}
        """
        def __init__(self, url):
            self.info = f"{url}/api/user/info?"
            self.pet = self._Pet(url)
            self.pet_team = self._PetTeam(url)
            self.god = self._God(url)
            self.equipment = self._Equipment(url)
            self.mail = self._Mail(url)
            self.bundle_package = self._BundlePackage(url)
            self.privilege = self._Privilege(url)
            self.offline_reward = self._OfflineReward(url)
            self.daily_gold_package = self._DailyGoldPackage(url)
            self.mall = self._Mall(url)
            self.friend = self._Friend(url)
            self.get_blacklist = f"{url}/api/user/get-blacklist?"
            self.remove_blacklist = f"{url}/api/user/remove-blacklist?"
        class _Pet:
            def __init__(self, url):
                self.info = f"{url}/api/user/pet/info?"
        class _PetTeam:
            def __init__(self, url):
                self.info = f"{url}/api/user/pet-team/info?"
        class _God:
            def __init__(self, url):
                self.info = f"{url}/api/user/god/info?"
        class _Equipment:
            def __init__(self, url):
                self.info = f"{url}/api/user/equipment/info?"
                self.equip = f"{url}/api/user/equipment/equip?"
                self.unequip = f"{url}/api/user/equipment/unequip?"
        class _Mail:
            def __init__(self, url):
                self.get = f"{url}/api/user/mail/get?"
        class _BundlePackage:
            def __init__(self, url):
                self.free = f"{url}/api/user/bundle_package/free?"
        class _Privilege:
            def __init__(self, url):
                self.claim_daily_free_privilege_reward = f"{url}/api/privilege/claim_daily_free_privilege_reward?"
        class _OfflineReward:
            def __init__(self, url):
                self.claim = f"{url}/api/user/offline-reward/claim?"
                self.quick_claim = f"{url}/api/user/offline-reward/quick-claim?"
        class _DailyGoldPackage:
            def __init__(self, url):
                self.record = f"{url}/api/user/daily_gold_package/record?"
                self.purchase = f"{url}/api/user/daily_gold_package/purchase?"
        class _Mall:
            def __init__(self, url):
                self.festival = self._Festival(url)
                self.purchase = f"{url}/api/user/mall/purchase?"
            class _Festival:
                def __init__(self, url):
                    self.daily_claim = f"{url}/api/mall/festival/daily-claim?"
        class _Friend:
            def __init__(self, url):
                self.search = f"{url}/api/user/friend/search?"
                self.list = f"{url}/api/user/friend/list?"
                self.collect_and_send_fp_all = f"{url}/api/user/friend/collect-and-send-fp-all?"
                self.requesting_list = f'{url}/api/user/friend/requesting-list?'
                self.suggest_list = f"{url}/api/user/friend/suggest-list?"
                self.remove_fd = f"{url}/api/user/friend/remove-fd?"
        class _PetTeam:
            def __init__(self, url):
                self.info = f"{url}/api/user/pet-team/info?"
        class _Mail:
            def __init__(self, url):
                self.get = f"{url}/api/user/mail/get?"

    class AccumulateTopUp:
        """ An inner class level of `/accumulate_top_up` API corresponding to `GameApi.data_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        
        FROM `GameApi.data_url`
        **GET** /api/accumulate_top_up/daily/records?[URI]
        """
        def __init__(self, url):
            self.daily = self._Daily(url)
        class _Daily:
            def __init__(self, url):
                self.records = f"{url}/api/accumulate_top_up/daily/records?"

    class Slg:
        """ An inner class level of `/slg` API corresponding to `GameApi.data_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        
        FROM `GameApi.data_url`
        **GET** /api/slg/flag/records?[URI]

        **POST** /api/slg/flag/equip?[URI] 
            - **PAYLOAD** { "flag_serial_id": [FLAG_SERIAL_ID], "pet_serial_id": [PET_SERIAL_ID] }
            - [FLAG_SERIAL_ID]: [a-z0-9]{40}
            - [PET_SERIAL_ID]: [a-z0-9]{40}
        **POST** /api/slg/flag/unequip?[URI] 
            - **PAYLOAD** { "flag_serial_id": [FLAG_SERIAL_ID], "pet_serial_id": [PET_SERIAL_ID] }
            - [FLAG_SERIAL_ID]: [a-z0-9]{40}
            - [PET_SERIAL_ID]: [a-z0-9]{40}
        """
        def __init__(self, url):
            self.records = f"{url}/api/slg/records?"
            self.equip = f"{url}/api/slg/flag/equip?"
            self.unequip = f"{url}/api/slg/flag/unequip?"

    class Crystal:
        """ An inner class level of `/crystal` API corresponding to `GameApi.data_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        
        FROM `GameApi.data_url`
        **GET** /api/crystal/record?[URI]
        
        **POST** /api/crystal/place?[URI]
            - **PAYLOAD**
        **POST** /api/crystal/remove?[URI]
            - **PAYLOAD**
        """
        def __init__(self, url):
            self.record = f"{url}/api/crystal/record?"
            self.place = f"{url}/api/crystal/place?"
            self.remove = f"{url}/api/crystal/remove?"

    class Guild:
        """ An inner class level of `/user` API corresponding to `GameApi.data_url`
        [URI]: user_id={}&session_id={}&server_prefix={}

        FROM `GameApi.data_url`
        **GET** /api/guild/get_guild_user_data?[URI]
        **GET** /api/guild/exp_reward_record?[URI]
        **GET** /api/guild/get_guild_all_data?[URI2]
        **GET** /api/guild/get_guild_all_user?[URI2]

        **POST** /api/guild/join_guild?[URI]
            - **PAYLOAD** { "guild_id": [GUILD_ID] }
            - [GUILD_ID]: [0-9]|[1-9][0-9]*
        **POST** /api/guild/accpet_join?[URI]
            - **PAYLOAD** { "member_id": [MEMBER_ID] }
            - [MEMBER_ID]: [1-9][0-9]{4}
        **POST** /api/guild/reject_join?[URI]
            - **PAYLOAD** { "member_id": [MEMBER_ID] }
            - [MEMBER_ID]: [1-9][0-9]{4}
        **POST** /api/guild/del_member?[URI]
            - **PAYLOAD** { "member_id": [MEMBER_ID] }
            - [MEMBER_ID]: [1-9][0-9]{4}
        **POST** /api/guild/trigger_vice?[URI]
            - **PAYLOAD** { "guild_id": [GUILD_ID], "member_id": [MEMBER_ID] }
            - [GUILD_ID]: [0-9]|[1-9][0-9]*
            - [MEMBER_ID]: [1-9][0-9]{4}
        **POST** /api/guild/change_president?[URI]
            - **PAYLOAD** { "guild_id": [GUILD_ID], "member_id": [MEMBER_ID] }
            - [GUILD_ID]: [0-9]|[1-9][0-9]*
            - [MEMBER_ID]: [1-9][0-9]{4}
        **POST** /api/guild/donation?
            - **PAYLOAD** { "donate_id": [DONATE_ID], "guild_id": int, "cost": [{ "asset_type": 0, "asset_id": "0", "amount": [AMOUNT] }], 'get_coin': [GET_COIN], 'get_exp': [GET_EXP] }
            - [DONATE_ID]: [1-3]
            - [AMOUNT]: 60000|20|60
            - [GET_COIN]: 30|100|330
            - [GET_EXP]: 50|100|200
        **POST** /api/guild/take_exp_reward?[URI]
            - **PAYLOAD** { TODO }
        **POST** /api/guild/update_info?[URI]
            - **PAYLOAD** { "icon": [ICON], "desciption": [DESCRIPTION] }
            - [ICON]: [0-9]|1[0-9]|2[0-5]
            - [DESCRIPTION]: \\w*
        """
        def __init__(self, url):
            # GET
            self.get_guild_user_data = f"{url}/api/guild/get_guild_user_data?"
            self.exp_reward_record = f"{url}/api/guild/exp_reward_record?"
            self.get_guild_all_data = f"{url}/api/guild/get_guild_all_data?"
            self.get_guild_all_user = f"{url}/api/guild/get_guild_all_user?"

            #POST
            self.join_guild = f"{url}/api/guild/join_guild?"
            # 'accpet' is not a typo
            self.accept_join = f"{url}/api/guild/accpet_join?"
            self.reject_join = f"{url}/api/guild/reject_join?"
            self.del_member = f"{url}/api/guild/del_member?"
            self.trigger_vice = f"{url}/api/guild/trigger_vice?"
            self.change_president = f"{url}/api/guild/change_president?"
            self.donation = f"{url}/api/guild/donation?"
            self.take_exp_reward = f"{url}/api/guild/take_exp_reward?"

    class GuildBoss:
        """ An inner class level of `/guild-boss` API corresponding to `GameApi.data_url` and `GameApi.battle_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}

        FROM `GameApi.data_url`
        **GET** /api/guild-boss/records?[URI]
        **GET** /api/guild-boss/guild-all-record?[URI]
        
        **POST** /api/guild-boss/battle/start?[URI]
            - **PAYLOAD** { "id": [ID], "team_list": { "pet": [ [PET] ], "pet_god": [ [PET_GOD] ] } }
            - [ID]: [1-9][0-9]*
            - [PET]: { "team_position": [0-5], "pet_serial_id": [a-z0-9]{40} }+
            - [PET_GOD]: { "god_serial_id": [a-z0-9]{40} }{1,2}
        **POST** /api/guild-boss/battle/end?[URI]
            - **PAYLOAD** { "id": [ID], "battle_serial_id": [BATTLE_SERIAL_ID] }
            - [ID]: [1-9][0-9]*
            - [BATTLE_SERIAL_ID]: [a-z0-9]{40}

        FROM `GameApi.battle_url`
        **GET** /startGuildBossBattle?[URI2]
        """
        def __init__(self, url, url2):
            self.records = f"{url}/api/guild-boss/records?"
            self.guild_all_record = f"{url}/api/guild-boss/guild-all-record?"
            self.battle = self._Battle(url, url2)

        class _Battle:
            def __init__(self, url, url2):
                self.start = f"{url}/api/guild-boss/battle/start?"
                self.log = f"{url2}/startGuildBossBattle?"
                self.end = f"{url}/api/guild-boss/battle/end?"

    class WorldBoss:
        """ An inner class level of `/world-boss` API corresponding to `GameApi.data_url` and `GameApi.battle_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}

        FROM `GameApi.data_url`
        **GET** /api/world-boss/records?[URI]

        **POST** /api/world-boss/purchase/challenge-times?[URI]
            - **PAYLOAD** { "cost": [{ "asset_type": 0, "asset_id": [ASSET_ID], "amount": 40 }] }
            - [ASSET_ID]: [1-9][0-9]{6}
        **POST** /api/world-boss/battle/start?[URI]
            - **PAYLOAD** { "id": [ID], "team_list": { "pet": [ [PET] ], "pet_god": [ [PET_GOD] ] } }
            - [ID]: [1-9]|[1-9][0-9]*
            - [PET]: { "team_position": [0-5], "pet_serial_id": [a-z0-9]{40} }+
            - [PET_GOD]: { "god_serial_id": [a-z0-9]{40} }{1,2}
        **POST** /api/world-boss/battle/end?[URI]
            - **PAYLOAD** { "id": [ID], "battle_serial_id": [BATTLE_SERIAL_ID] }
            - [ID]: [1-9]|[1-9][0-9]*
            - [BATTLE_SERIAL_ID]: [a-z0-9]{40}

        FROM `GameApi.battle_url`
        **GET** /startWorldBossBattle?[URI2]
        """
        def __init__(self, url, url2):
            self.records = f"{url}/api/world-boss/records?"
            self.purchase = self._Purchase(url)
            self.battle = self._Battle(url, url2)
        class _Purchase:
            def __init__(self, url):
                self.challenge_times = f"{url}/api/world-boss/purchase/challenge-times?"
        class _Battle:
            def __init__(self, url, url2):
                self.start = f"{url}/api/world-boss/battle/start?"
                self.log = f"{url2}/startWorldBossBattle?"
                self.end = f"{url}/api/world-boss/battle/end?"

    class CycleBoss:
        """ An inner class level of `/cycle-boss` API corresponding to `GameApi.data_url` and `GameApi.battle_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}

        FROM `GameApi.data_url`
        **GET** /api/cycle-boss/records?[URI]

        **POST** /api/cycle-boss/battle/start?[URI]
            - **PAYLOAD** { "id": [ID], "difficulty": [DIFFICULTY], "team_list": { "pet": [ [PET] ], "pet_god": [ [PET_GOD] ] } }
            - [ID]: [1-9]|[1-9][0-9]*
            - [DIFFICULTY]: [1-9]
            - [PET]: { "team_position": [0-5], "pet_serial_id": [a-z0-9]{40} }+
            - [PET_GOD]: { "god_serial_id": [a-z0-9]{40} }{1,2}
        **POST** /api/cycle-boss/battle/end?[URI]
            - **PAYLOAD** { "id": [ID], "battle_serial_id": [BATTLE_SERIAL_ID] }
            - [ID]: [1-9]|[1-9][0-9]*
            - [BATTLE_SERIAL_ID]: [a-z0-9]{40}

        FROM `GameApi.battle_url`
        **GET** /startCycleBossBattle?[URI2]
        """
        def __init__(self, url, url2):
            self.records = f"{url}/api/cycle-boss/records?"
            self.battle = self._Battle(url, url2)
        class _Battle:
            def __init__(self, url, url2):
                self.start = f"{url}/api/cycle-boss/battle/start?"
                self.log = f"{url2}/startCycleBossBattle?"
                self.end = f"{url}/api/cycle-boss/battle/end?"
    
    class EventBoss:
        """ An inner class level of `/event-boss` API corresponding to `GameApi.data_url` and `GameApi.battle_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}

        FROM `GameApi.data_url`
        **GET** /api/event-boss/records?[URI]

        **POST** /api/event-boss/battle/start?[URI]
            - **PAYLOAD** { "season": [SEASON], "team_list": { "pet": [ [PET] ], "pet_god": [ [PET_GOD] ] } }
            - [SEASON]: [1-9]|[1-9][0-9]*
            - [PET]: { "team_position": [0-5], "pet_serial_id": [a-z0-9]{40} }+
            - [PET_GOD]: { "god_serial_id": [a-z0-9]{40} }{1,2}
        **POST** /api/event-boss/battle/end?[URI]
            - **PAYLOAD** { "season": [SEASON], "battle_serial_id": [BATTLE_SERIAL_ID] }
            - [SEASON]: [1-9]|[1-9][0-9]*
            - [BATTLE_SERIAL_ID]: [a-z0-9]{40}
        **POST** /api/event-boss/battle/claim?[URI]
            - **PAYLOAD** { "battle_serial_id": [BATTLE_SERIAL_ID] }
            - [BATTLE_SERIAL_ID]: [a-z0-9]{40}

        FROM `GameApi.battle_url`
        **GET** /startEventBossBattle?[URI2]
        """
        def __init__(self, url, url2):
            self.records = f"{url}/api/event-boss/records?"
            self.battle = self._Battle(url, url2)
        class _Battle:
            def __init__(self, url, url2):
                self.start = f"{url}/api/event-boss/battle/start?"
                self.log = f"{url2}/startEventBossBattle?"
                self.end = f"{url}/api/event-boss/battle/end?"
                self.claim = f"{url}/api/event-boss/battle/claim?"

    class SexualDating:
        """ An inner class level of `/sexual-dating` API corresponding to `GameApi.data_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: event_id={}&user_id={}&session_id={}&server_prefix={}
        
        **GET** /api/sexual_dating/claimItemExplore?[URI]
        **GET** /api/sexual_dating/records?[URI2]
        **GET** /api/sexual_dating/claim?[URI]

        **POST** /api/sexual_dating/option/click?[URI]
        **POST** /api/sexual_dating/choose?[URI]
        """
        def __init__(self, url):
            self.claimItemExplore = f"{url}/api/sexual_dating/claimItemExplore?"
            self.records = f"{url}/api/sexual_dating/records?"
            self.claim = f"{url}/api/sexual_dating/claim?"
            self.option = self._Option(url)
            self.choose = f"{url}/api/sexual_dating/choose?"
        class _Option:
            def __init__(self, url):
                self.click = f"{url}/api/sexual_dating/option/click?"

    class MultiverseDating:
        """ An inner class level of `/multiverse_dating` API corresponding to `GameApi.data_url`
        [URI]: user_id={}&session_id={}&server_prefix={}

        **GET** /api/multiverse_dating/records?[URI]

        **POST** /api/multiverse_dating/view/avg?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
        **POST** /api/multiverse_dating/explore/claim?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
        **POST** /api/multiverse_dating/explore/upgrade?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "tier": [TIER], "cost": [ [COST] ] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
            - [TIER]: [2-4]
            - [COST]: { "asset_type": 6,"asset_id": "[1-9][0-9]{6}","amount": 500|1500|4000 }
        **POST** /api/multiverse_dating/meet?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
        **POST** /api/multiverse_dating/gift?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "item_id": [ITEM_ID] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
            - [ITEM_ID]: [1-9][0-9]{6}
        **POST** /api/multiverse_dating/level/claim?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "level": [LEVEL] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
            - [LEVEL]: [1-7]
        **POST** /api/multiverse_dating/select?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "select_id": 0, "cost": [ [COST] ] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
            - [COST]: { "asset_type": 6,"asset_id": "[0-9]{7}","amount": 25|30|35|40|50|75|100|125|150|160|170|180|190|200 }
        """
        def __init__(self, url):
            self.records = f"{url}/api/multiverse_dating/records?"
            self.view = self._View(url)
            self.explore = self._Explore(url)
            self.meet = f"{url}/api/multiverse_dating/meet?"
            self.gift = f"{url}/api/multiverse_dating/gift?"
            self.level = self._Level(url)
            self.select = f"{url}/api/multiverse_dating/select?"
        class _View:
            def __init__(self, url):
                self.avg = f"{url}/api/multiverse_dating/view/avg?"
        class _Explore:
            def __init__(self, url):
                self.claim = f"{url}/api/multiverse_dating/explore/claim?"
                self.upgrade = f"{url}/api/multiverse_dating/explore/upgrade?"
        class _Level:
            def __init__(self, url):
                self.claim = f"{url}/api/multiverse_dating/level/claim?"

    class MegaEvent:
        """ An inner class level of `/mega-pet-event` API corresponding to `GameApi.data_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: event_id={}&user_id={}&session_id={}&server_prefix={}

        FROM `GameApi.data_url`
        **GET** /api/mega-pet-event/records?[URI2]

        **POST** /api/mega-pet-event/main/avg/finish?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
        **POST** /api/mega-pet-event/daily-login/claim?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "day": [DAY] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
            - [DAY]: [1-9]|1[0-9]|2[0-4]
        **POST** /api/mega-pet-event/explore/claim?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
        **POST** /api/mega-pet-event/game-1/avg/finish?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
        **POST** /api/mega-pet-event/game-1/purchase/challenge-limit?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "cost": [{ "asset_type": 0, "asset_id": "0", "amount": [AMOUNT] }] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
            - [AMOUNT]: 200|350|500|650|800|1000  
        **POST** /api/mega-pet-event/game-1/action/finish?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "score": 150 }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
        **POST** /api/mega-pet-event/puzzle/draw?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "cost": [{ "asset_type": 6, "asset_id": ASSET_ID, "amount": 170 }]}
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
            - [ASSET_ID]: [0-9]{7}
        **POST** /api/mega-pet-event/puzzle/line/claim?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "line_index": [LINE_INDEX] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
            - [LINE_INDEX]: [0-9]
        **POST** /api/mega-pet-event/game-3/avg/finish?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID] }
            - [EVENT_ID]: [1-9]|[1-9][0-9]*
        **POST** /api/mega-pet-event/game-3/action/finish?[URI]
            - **PAYLOAD** { "event_id": [EVENT_ID], "score": 100000, "cost": [{ "asset_type": 6, "asset_id": str, "amount": [AMOUNT] }], "cost_type": [COST_TYPE] }
            - [EVENT_ID]: [1-9][0-9]*
            - [AMOUNT]: 200|2000
            - [COST_TYPE]: 0|1
        """
        def __init__(self, url):
            # GET
            self.records = f"{url}/api/mega-pet-event/records?"
            # POST
            self.main = self._Main(url)
            self.daily_login = self._DailyLogin(url)
            self.explore = self._Explore(url)
            self.game_1 = self._GameOne(url)
            self.puzzle = self._Puzzle(url)
            self.game_3 = self._GameThree(url)
        class _Main:
            def __init__(self, url):
                self.avg = self._Avg(url)
            class _Avg:
                def __init__(self, url):
                    self.finish = f"{url}/api/mega-pet-event/main/avg/finish?"
        class _DailyLogin:
            def __init__(self, url):
                self.claim = f"{url}/api/mega-pet-event/daily-login/claim?"
        class _Explore:
            def __init__(self, url):
                    self.claim = f"{url}/api/mega-pet-event/explore/claim?"
        class _GameOne:
            def __init__(self, url):
                self.avg = self._Avg(url)
                self.purchase = self._ChallengeLimit(url)
                self.action = self._Action(url)
            class _Avg:
                def __init__(self, url):
                    self.finish = f"{url}/api/mega-pet-event/game-1/avg/finish?"
            class _ChallengeLimit:
                def __init__(self, url):
                    self.challenge_limit = f"{url}/api/mega-pet-event/game-1/purchase/challenge-limit?"
            class _Action:
                def __init__(self, url):
                    self.finish = f"{url}/api/mega-pet-event/game-1/action/finish?"
        class _Puzzle:
            def __init__(self, url):
                self.draw = f"{url}/api/mega-pet-event/puzzle/draw?"
                self.line = self._Line(url)
            class _Line:
                def __init__(self, url):
                    self.claim = f"{url}/api/mega-pet-event/puzzle/line/claim?"
        class _GameThree:
            def __init__(self, url):
                self.avg = self._Avg(url)
                self.action = self._Action(url)
            class _Avg:
                def __init__(self, url):
                    self.finish = f"{url}/api/mega-pet-event/game-3/avg/finish?"
            class _Action:
                def __init__(self, url):
                    self.finish = f"{url}/api/mega-pet-event/game-3/action/finish?"

    class Pvp:
        """ An inner class level of `/pvp` API corresponding to `GameApi.data_url` and `GameApi.battle_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}

        FROM `GameApi.data_url`
        **GET** /api/pvp/user/top_rank_player_list?[URI]
        **GET** /api/pvp/opponent/list?[URI]
        
        **POST** /api/pvp/purchaseBattleTicket?[URI]
            - **PAYLOAD** {}
        **POST** /api/pvp/battle_start?[URI]
            - **PAYLOAD** {}
        **POST** /api/pvp/battle_end?[URI]
            - **PAYLOAD** {}

        FROM `GameApi.battle_url`
        **GET** /startPVPBattle?[URI2]
        """
        def __init__(self, url, url2):
            self.user = self._User(url)
            self.opponent = self._Opponent(url)
            self.purchase_battle_ticket = f"{url}/api/pvp/purchaseBattleTicket?"
            self.battle_start = f"{url}/api/pvp/battle_start?"
            self.battle_log = f"{url2}/startPVPBattle?"
            self.battle_end = f"{url}/api/pvp/battle_end?"
        class _User:
            def __init__(self, url):
                self.top_rank_player_list = f"{url}/api/pvp/user/top_rank_player_list?"
        class _Opponent:
            def __init__(self, url):
                self.list = f"{url}/api/pvp/opponent/list?"

    class Pvp3v3:
        """ An inner class level of `/pvp_3v3` and `/pvp3` API corresponding to `GameApi.data_url` and `GameApi.battle_url`
        [URI]: user_id={}&session_id={}&server_prefix={}
        [URI2]: user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}

        FROM `GameApi.data_url`
        **GET** /api/pvp_3v3/user/grown_reward/record?[URI]
        **GET** /api/pvp_3v3/ranking/last_season/reward/record?[URI]
        **GET** /api/pvp_3v3/ranking?[URI]
        **GET** /api/pvp_3v3/opponent/list?[URI]
        
        **POST** /api/pvp3/battle_ticket/purchase?[URI]
            - **PAYLOAD** {}
        **POST** /api/pvp_3v3/battle_start?[URI]
            - **PAYLOAD** {}
        **POST** /api/pvp_3v3/battle_end?[URI]
            - **PAYLOAD** {}

        FROM `GameApi.battle_url`
        **GET** /startPVP3Battle?[URI2]
        """
        def __init__(self, url, url2):
            self.user = self._User(url)
            self.ranking = self._Ranking(url)
            self.opponent = self._Opponent(url)
            self.battle_ticket = self._BattleTicket(url)
            self.battle_start = f"{url}/api/pvp_3v3/battle_start?"
            self.battle_log = f"{url2}/startPVP3Battle?"
            self.battle_end = f"{url}/api/pvp_3v3/battle_end?"
        class _User:
            def __init__(self, url):
                self.grown_reward = self._GrownReward(url)
            class _GrownReward:
                def __init__(self, url):
                    self.record = f"{url}/api/pvp_3v3/user/grown_reward/record?"
        class _Ranking:
            def __init__(self, url):
                self._url = url
                self.last_season = self._LastSeason(url)
            def __str__(self) -> str:
                return f"{self._url}/api/pvp_3v3/ranking?"
            class _LastSeason:
                def __init__(self, url):
                    self.reward = self._Reward(url)
                class _Reward:
                    def __init__(self, url):
                        self.record = f"{url}/api/pvp_3v3/ranking/last_season/reward/record?"
        class _Opponent:
            def __init__(self, url):
                self.list = f"{url}/api/pvp_3v3/opponent/list?"
        class _BattleTicket:
            def __init__(self, url):
                self.purchase = f"{url}/api/pvp3/battle_ticket/purchase?"

