#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import asyncio
import random
from datetime import datetime
from contextlib import suppress
from network import NetworkManager, Response
from event import BaseConfig, BaseEventManager
from storage import Database, UserDocument, DiscordID

def handler():
    handler = logging.StreamHandler()
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    return handler

class MultiverseDatingManager(BaseEventManager):
    _logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__('MultiverseEventSetting.zip')
        self.event_id = None
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            self._logger.addHandler(handler())

    """ Download latest event setting configs from the server CDN, and build the required list for script automation. """
    async def build_event_config(self):
        config = await BaseConfig(self.config).get_dict()
        now_ts = int(datetime.now().timestamp())
        # Retrieve event_id
        for event in config['multiverse_dating_settings']:
            if event['timeslot_detail'][0]['end_time'] > now_ts > event['timeslot_detail'][0]['start_time']:
                # update event_id if Multiverse Dating event is currently online
                self.event_id = event['event_id']
                self.end_time = event['timeslot_detail'][0]['end_time']

        if self.event_id:
            # Build reward list for each level completion
            self.reward_list = list()
            self.gift_list = list()
            for level in config['multiverse_dating_level_settings']:
                if level['event_id'] == self.event_id:
                    if level['level'] > 0:
                        rewards = list()
                        for reward in level['reward_list']:
                            del reward['config']
                            rewards.append(json.dumps(reward))
                        # hard coding the gift list 
                        if level['level'] == 1:
                            first_item = json.loads(rewards[1])['asset_id']
                            # Build gift list for each item ID
                            for i in range(4):
                                self.gift_list.append(int(first_item) + i)
                        reward_info = { 'level': level['level'], 'exp': level['exp'], 'rewards': rewards }
                        self.reward_list.append(reward_info)

            # Build machine list for collect machine
            self.machine_list = list()
            for upgrade in config['multiverse_dating_explore_item_settings']:
                if upgrade['event_id'] == self.event_id:
                    cost = dict()
                    if upgrade['tier_cost']:
                        cost = upgrade['tier_cost'][0]
                        del cost['config']
                    machine_info = { 'tier': upgrade['tier'], 'cost': json.dumps([cost]), 'max_duration': upgrade['max_duration'] }
                    self.machine_list.append(machine_info)

            # Build Q&A cost list from level 1 to 6
            self.avg_dict = dict()
            for qa in config['multiverse_dating_question_settings']:
                if qa['event_id'] == self.event_id and qa['level'] > 0:
                    payload_list = list()
                    for q_idx, q in enumerate(qa['question']):
                        for a_idx, a in enumerate(q['answer_list']):
                            if a['is_true'] == 1:
                                cost = a['cost'][0]
                                del cost['config']
                                payload = { 'question_id': q_idx, 'select_id': a_idx, 'cost': json.dumps([cost]) }
                                payload_list.append(payload)
                    self.avg_dict.update({ qa['level']: payload_list })
        else:
            self._logger.error(f"There's no multiverse event running right now.")

    async def create_user_instance(self, user: UserDocument):
        instance = MultiverseDating(user.doc_id, self.event_id, self.end_time, self.reward_list, self.gift_list, self.machine_list, self.avg_dict)
        await instance.on_start()
        return instance


class MultiverseDating(NetworkManager):
    _logger = logging.getLogger('Clicker 2.5')

    def __init__(self, discord_user_id: DiscordID, event_id: int, end_time: int, reward_list, gift_list, machine_list, avg_dict):
        super().__init__()
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            self._logger.addHandler(handler())
        self.discord_user_id = discord_user_id
        self.event_id = event_id
        self.end_time = end_time
        self.reward_list = reward_list
        self.gift_list = gift_list
        self.machine_list = machine_list
        self.avg_dict = avg_dict
        self.energy = 0
        self.duration = 0
        self.is_sync = False

    async def on_start(self) -> None:
        await super().register(self.discord_user_id)
        self.is_sync = await self.fetch_records()

    async def run_loop(self) -> None:
        if self.is_sync:
            while self.end_time > int(datetime.now().timestamp()):
                if await self.is_premium():
                    try:
                        await super().register(self.discord_user_id)
                        await self.claim_energy()
                        await self.auto_dialog()
                        await self.daily_meet()
                        await self.automate_level_rewards()
                        await self.wait_until_next_update()
                    except Exception as e:
                        self._logger.exception(f"(User: {self.discord_user_id}) encountered process exception: {e}")
                else:
                    await super().register(self.discord_user_id)
                    await self.claim_energy()

    """ Complete event dialogues if player energy sufficient. """
    async def auto_dialog(self):
        await self.fetch_records()
        while self.energy >= self._current_question_cost():
            if not await self.select_answer():
                 break

    """ Complete all daily meet attempts at once """
    async def daily_meet(self):
        meet_count = self.dating_record['meet_count']
        payload = { 'event_id': self.event_id }
        for i in range(10 - meet_count):
            resp = await self._post(self.api.multiverse_dating.meet, payload)
            # update user record
            self.dating_record = resp.response()['user_multiverse_dating_record']
            if i == 0:
                self._logger.info(f"(User: {self.discord_user_id}) has met 1 time.")
            else:
                self._logger.info(f"(User: {self.discord_user_id}) has met {i+1} times.")

    """ Claim energy from collect machine """
    async def claim_energy(self) -> None:
        payload = { 'event_id': self.event_id }
        resp = await self._post(self.api.multiverse_dating.explore.claim, payload)
        if resp.success():
            # update user record
            self.dating_record = resp.response()['user_multiverse_dating_record']
            self.energy = resp.updated_item_list()[0]['amount']
            amount = resp.response()['asset_return'][0]['amount']
            self._logger.info(f"(User: {self.discord_user_id}) collected {amount} energy. energy total: {self.energy}")
        else:
            self._logger.error(f"(User: {self.discord_user_id}) failed to collect energy, reason: {resp.error_message()}")
    
    """ Check if the user has enough EXP to receive level complete rewards. If eligible level rewards contain upgrade materials, proceed to upgrade collect machine automatically. """
    async def automate_level_rewards(self) -> None:
        await self.fetch_records()
        claimed_levels = self.dating_record['claim_reward_level']
        current_level = self.dating_record['level']
        for level_reward in self.reward_list:
            if level_reward['level'] > current_level:
                break
            else:
                if current_level not in claimed_levels:
                    payload = { 'event_id': self.event_id, 'level': current_level }
                    await self._post(self.api.multiverse_dating.level.claim, payload)
                    self._logger.info(f"(User: {self.discord_user_id}) claimed (Level: {level_reward['level']}) rewards.")
                    # only 2, 4, 5 level rewards contain upgrade materials
                    match current_level:
                        case 2:
                            if self.dating_record['item_tier'] == 1:
                                await self.upgrade(2, self.machine_list[1]['cost'])
                        case 4:
                            match self.dating_record['item_tier']:
                                case 1:
                                    await self.upgrade(2, self.machine_list[1]['cost'])
                                    await self.upgrade(3, self.machine_list[2]['cost'])
                                case 2:
                                    await self.upgrade(3, self.machine_list[2]['cost'])
                                case _:
                                    continue
                        case 5:
                            match self.dating_record['item_tier']:
                                case 1:
                                    await self.upgrade(2, self.machine_list[1]['cost'])
                                    await self.upgrade(3, self.machine_list[2]['cost'])
                                    await self.upgrade(4, self.machine_list[3]['cost'])
                                case 2:
                                    await self.upgrade(3, self.machine_list[2]['cost'])
                                    await self.upgrade(4, self.machine_list[3]['cost'])
                                case 3:
                                    await self.upgrade(4, self.machine_list[3]['cost'])
                                case _:
                                    continue
                        case _:
                            # we use spare levels to consume remaining gifts
                            for gift_id in self.gift_list:
                                remains = await self.send_gift(gift_id)
                                if remains:
                                    for _ in range(remains):
                                        await self.send_gift(gift_id)

    """ Send gift to event hero, return remaining amount of the gift item. """
    async def send_gift(self, item_id) -> int | None:
        payload = { 'event_id': self.event_id, 'item_id': item_id }
        resp = await self._post(self.api.multiverse_dating.gift, payload)
        if resp.success():
            cmp_record = self.dating_record()
            self.dating_record = self.response()['user_multiverse_dating_record']
            delta = self.dating_record['exp'] - cmp_record['exp']
            self._logger.info(f"(User: {self.discord_user_id}) gained {delta} EXP by sending the gift.")
            remains = resp.reduced_item_list()[0]['amount']
            return remains
        elif resp.error_code() == 11002:
            self._logger.warning(f"(User: {self.discord_user_id}) does not have any gift (ID: {item_id}).")
        else:
            self._logger.error(f"(User: {self.discord_user_id}) failed to send gift, reason: {resp.error_message()}")
    
    """ Get the latest event records, return bool. """
    async def fetch_records(self) -> bool:
        resp = await self._get(self.api.multiverse_dating.records)
        if resp.success():
            self.dating_record = resp.dating_record(self.event_id)
            self.dialog_records = resp.dialog_records(self.event_id)
            self._logger.info(f"(User: {self.discord_user_id}) updated dating record.")
            self._update_duration()
            return True
        else:
            self._logger.error(f"(User: {self.discord_user_id}) failed to fetch event records, reason: {resp.error_message()}")
            return False

    """ Upgrade collect machine """
    async def upgrade(self, tier: int, cost: str) -> None:
        payload = { 'event_id': self.event_id, 'tier': tier, 'cost': cost }
        resp = await self._post(self.api.multiverse_dating.explore.upgrade, payload)
        if resp.success():
            # update user record
            self.dating_record = resp.response()['user_multiverse_dating_record']
            self._update_duration()
            self._logger.info(f"(User: {self.discord_user_id}) upgraded machine to tier {self.dating_record['item_tier']}.")
        else:
            self._logger.error(f"(User: {self.discord.user_id}) failed to upgrade machine to tier {tier}, reason: {resp.error_message()}")

    """ Auto complete question by current question ID, return False if something is wrong """
    async def select_answer(self) -> bool:
        cmp_record = self.dating_record
        cheatsheet = self.avg_dict[cmp_record['level']]
        for qa in cheatsheet:
            if qa['question_id'] == cmp_record['current_question']:
                select_id = qa['select_id']
                cost = qa['cost']
                break

        payload = { 'event_id': self.event_id, 'select_id': select_id, 'cost': cost }
        resp = await self._post(self.api.multiverse_dating.select, payload)
        if resp.success():
            # update user record
            self.dating_record = resp.response()['user_multiverse_dating_record']
            self.energy = resp.reduced_item_list()[0]['amount']
            if self.dating_record['exp'] > cmp_record['exp']:
                self._logger.info(f"(User: {self.discord_user_id}) has answered the dialog successfully! total EXP: {self.dating_record['exp']}, next question ID: {self.dating_record['current_question']}")
                return True
            else:
                self._logger.warning(f"(User: {self.discord_user_id}) selected the wrong answer! please inform admin to resolve issues.")
                return False
        else:
            self._logger.error(f"(User: {self.discord_user_id}) failed to submit the answer, reason: {resp.error_message()}")
            return False

    """ Override get request from NetworkManager to return EventResponse """
    async def _get(self, api_name, **kwargs) -> dict:
        resp = await super().get(api_name, self.discord_user_id, **kwargs)
        return EventResponse(resp.body)
    
    """ Override post request from NetworkManager to return EventResponse """
    async def _post(self, api_name, payload, **kwargs) -> dict:
        resp = await super().post(api_name, payload, self.discord_user_id, **kwargs)
        return EventResponse(resp.body)
    
    """ Override database CRUD to fetch next_update timestamp from the user storage """
    async def get_next_update_timestamp(self) -> int:
        user = await self.db.user.get_user(self.discord_user_id)
        next_update_ts = user.get_next_update_timestamp()
        return next_update_ts

    """ Override database CRUD to fetch premium status from the user storage """
    async def is_premium(self) -> bool:
        user = await self.db.user.get_user(self.discord_user_id)
        return user.is_premium()

    """ Override database CRUD to set next_update timestamp at wait until the energy reaches at 80% machine capacity """
    async def wait_until_next_update(self) -> None:
        interval = int(self.duration * random.randint(80, 90) / 100)
        next_update_ts = int(datetime.now().timestamp()) + interval
        await self.db.user.set_next_update_timestamp(self.discord_user_id, next_update_ts)
        self._logger.info(f"(User: {self.discord_user_id}) coroutine starts sleeping for {interval} seconds.")
        await asyncio.sleep(interval)

    def _current_question_cost(self) -> int:
        level = self.dating_record['level']
        question_id = self.dating_record['current_question']
        for qa in self.avg_dict[level]:
            if qa['question_id'] == question_id:
                return json.loads(qa['cost'])[0]['amount']
    
    def _update_duration(self):
        try:
            tier = self.dating_record['item_tier']
            for machine in self.machine_list:
                if machine['tier'] == tier:
                    self.duration = machine['max_duration']
                    self._logger.info(f"(User: {self.discord_user_id}) updated duration to {self.duration} seconds.")
        except:
            self._logger.exception(f"(User: {self.discord_user_id}) has not initialised dating record yet!")


class EventResponse(Response):
    def __init__(self, body):
        super().__init__(body)

    def reduced_item_list(self) -> list | None:
        try:
            return self.body['reduced_item_list']
        except:
            return None

    def updated_item_list(self) -> list | None:
        try:
            return self.body['updated_item_list']
        except:
            return None

    def dating_record(self, event_id: int) -> dict | None:
        try:
            for record in self.response()['user_multiverse_dating_records']:
                if record['event_id'] == event_id:
                    return record

            return {}
        except:
            return None
    
    def dialog_records(self, event_id: int) -> list | None:
        try:
            results = list()
            for record in self.response()['user_multiverse_dating_dialog_records']:
                if record['event_id'] == event_id:
                    results.append(record)

            return results
        except:
            return None



async def main():
    manager = MultiverseDatingManager()
    await manager.build_event_config()
    await manager.run()

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
