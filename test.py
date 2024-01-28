#!/usr/bin/env python3
from api import GameApi
from NetworkManager import NetworkManager
import unittest
import json


class TestGameApi(unittest.TestCase):
    def test_network_request(self):
    def test_api_name_all(self):
        api = GameApi()
        auth_url = api.auth_url
        data_url = api.data_url
        battle_url = api.battle_url
        # Auth
        self.assertEqual(f"{api.auth.login.game_account}", auth_url + '/api/auth/login/game_account')
        self.assertEqual(f"{api.auth.login.user}", auth_url + '/api/auth/login/user?')
        # User
        self.assertEqual(f"{api.user.info}", data_url + '/api/user/info?')
        self.assertEqual(f"{api.user.get_blacklist}", data_url + '/api/user/get-blacklist?')
        self.assertEqual(f"{api.user.remove_blacklist}", data_url + '/api/user/remove-blacklist?')
        self.assertEqual(f"{api.user.pet.info}", data_url + '/api/user/pet/info?')
        self.assertEqual(f"{api.user.pet_team.info}", data_url + '/api/user/pet-team/info?')
        self.assertEqual(f"{api.user.god.info}", data_url + '/api/user/god/info?')
        self.assertEqual(f"{api.user.equipment.info}", data_url + '/api/user/equipment/info?')
        self.assertEqual(f"{api.user.mail.get}", data_url + '/api/user/mail/get?')
        self.assertEqual(f"{api.user.bundle_package.free}", data_url + '/api/user/bundle_package/free?')
        self.assertEqual(f"{api.user.privilege.claim_daily_free_privilege_reward}", data_url + '/api/privilege/claim_daily_free_privilege_reward?')
        self.assertEqual(f"{api.user.offline_reward.claim}", data_url + '/api/user/offline-reward/claim?')
        self.assertEqual(f"{api.user.mall.purchase}", data_url + '/api/user/mall/purchase?')
        self.assertEqual(f"{api.user.mall.festival.daily_claim}", data_url + '/api/mall/festival/daily-claim?')
        self.assertEqual(f"{api.user.friend.search}", data_url + '/api/user/friend/search?')
        self.assertEqual(f"{api.user.friend.list}", data_url + '/api/user/friend/list?')
        self.assertEqual(f"{api.user.friend.collect_and_send_fp_all}", data_url + '/api/user/friend/collect-and-send-fp-all?')
        self.assertEqual(f"{api.user.friend.requesting_list}", data_url + '/api/user/friend/requesting-list?')
        self.assertEqual(f"{api.user.friend.suggest_list}", data_url + '/api/user/friend/suggest-list?')
        self.assertEqual(f"{api.user.friend.remove_fd}", data_url + '/api/user/friend/remove-fd?')
        self.assertEqual(f"{api.user.pet_team.info}", data_url + '/api/user/pet-team/info?')
        self.assertEqual(f"{api.user.mail.get}", data_url + '/api/user/mail/get?')
        # AccumulateTopUp
        self.assertEqual(f"{api.accumulate_top_up.daily.records}", data_url + '/api/accumulate_top_up/daily/records?')
        # Crystal
        self.assertEqual(f"{api.crystal.record}", data_url + '/api/crystal/record?')
        self.assertEqual(f"{api.crystal.place}", data_url + '/api/crystal/place?')
        self.assertEqual(f"{api.crystal.remove}", data_url + '/api/crystal/remove?')
        # Guild
        self.assertEqual(f"{api.guild.get_guild_user_data}", data_url + '/api/guild/get_guild_user_data?')
        self.assertEqual(f"{api.guild.get_guild_all_data}", data_url + '/api/guild/get_guild_all_data?')
        self.assertEqual(f"{api.guild.get_guild_all_user}", data_url + '/api/guild/get_guild_all_user?')
        self.assertEqual(f"{api.guild.join_guild}", data_url + '/api/guild/join_guild?')
        self.assertEqual(f"{api.guild.accept_join}", data_url + '/api/guild/accpet_join?')
        self.assertEqual(f"{api.guild.reject_join}", data_url + '/api/guild/reject_join?')
        self.assertEqual(f"{api.guild.del_member}", data_url + '/api/guild/del_member?')
        self.assertEqual(f"{api.guild.trigger_vice}", data_url + '/api/guild/trigger_vice?')
        self.assertEqual(f"{api.guild.change_president}", data_url + '/api/guild/change_president?')
        self.assertEqual(f"{api.guild.donation}", data_url + '/api/guild/donation?')
        self.assertEqual(f"{api.guild.take_exp_reward}", data_url + '/api/guild/take_exp_reward?')
        # GuildBoss
        self.assertEqual(f"{api.guild_boss.records}", data_url + '/api/guild-boss/records?')
        self.assertEqual(f"{api.guild_boss.guild_all_record}", data_url + '/api/guild-boss/guild-all-record?')
        self.assertEqual(f"{api.guild_boss.battle.start}", data_url + '/api/guild-boss/battle/start?')
        self.assertEqual(f"{api.guild_boss.battle.log}", battle_url + '/startGuildBossBattle?')
        self.assertEqual(f"{api.guild_boss.battle.end}", data_url + '/api/guild-boss/battle/end?')



        # Pvp3v3
        self.assertEqual(f"{api.pvp_3v3.ranking}", data_url + '/api/pvp_3v3/ranking?')
        self.assertEqual(f"{api.pvp_3v3.battle_log}", battle_url + '/startPVP3Battle?')
        
