#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import asyncio
import random
from datetime import datetime
from contextlib import suppress
from typing import override
from network import NetworkManager, Response
from event import BaseConfig, BaseEventManager, BaseEvent
from storage import Database, DiscordID

class SexualDatingManager(BaseEventManager):
    _logger = logging.getLogger('Clicker 2 Event Manager')

    def __init__(self):
        super().__init__('SexualDatingSetting.zip')
        self.event_id = None
        self.end_time = None
        self._logger.setLevel(logging.INFO)

    @override
    async def build_event_config(self):
        """
        Download latest event setting configs from the server CDN, and build the required list for script automation.
        """
        config = await BaseConfig(self.config).get_dict()
        now_ts = int(datetime.now().timestamp())
        # Retrieve event_id
        for event in config['sexual_dating_settings']:
            if event['timeslot_detail'][0]['end_time'] > now_ts > event['timeslot_detail'][0]['start_time']:
                # update event_id if Multiverse Dating event is currently online
                self.event_id = event['event_id']
                self.end_time = event['timeslot_detail'][0]['end_time']

        if self.event_id:
            # Build avg answer dict
            self.avg_dict = dict()
            for chapter in config['message_detail_settings']:
                ans_list = list()
                chapter_id = chapter['chapter']
                max_message_id = len(chapter['message_data']) + 1
                for message in chapter['message_data']:
                    if message['selection_list']:
                        for selection in message['selection_list']:
                            if selection['correct'] == 1:
                                content = { 'message_id': message['id'], 'selection': selection['selection_id'], 'energy_cost': selection['energy_cost'] }
                                ans_list.append(content)

                self.avg_dict.update({ chapter_id: ans_list })

            # Build machine dict for collect machine
            self.upgrade_dict = dict()
            for upgrade in config['explore_item_settings']:
                if upgrade['event_id'] == self.event_id:
                    cost = list()
                    if upgrade['cost_list']:
                        cost = upgrade['cost_list']
                        del cost[0]['config']
                    machine_info = { 'cost': json.dumps(cost), 'max_duration': upgrade['max_explore_limit'] }
                    self.upgrade_dict.update({ upgrade['tier']: machine_info })

            # Build exp dict for auto clickers
            self.exp_dict = dict()
            for scene in config['h_sence_settings']:
                if scene['event_id'] == self.event_id:
                    # extract minimum info from each chapter
                    chapter_id = scene['chapter_id']
                    max_exp = scene['max_exp']
                    active = scene['active']
                    option_dict = dict()
                    # build option dict
                    for op_id, option in enumerate(scene['option_detail'], 1):
                        cost = list()
                        if option['item_cost']:
                            cost = option['item_cost']
                            del cost[0]['config']
                        detail = { 'exp': option['exp'], 'upgrade': option['exp_require'], 'cost': json.dumps(cost) } 
                        option_dict.update({ op_id: detail })
                    scene_record = { 'max_exp': max_exp, 'active': active, 'options': option_dict }
                    self.exp_dict.update({ chapter_id: scene_record })


    @override
    def create_user_instance(self, discord_id: DiscordID):
        return SexualDating(discord_id, self.event_id, self.end_time, self.avg_dict, self.upgrade_dict, self.exp_dict)


class SexualDating(BaseEvent):
    _logger = logging.getLogger('Clicker 2')

    def __init__(self, discord_user_id: DiscordID, event_id: int, end_time: int, avg_dict: dict, upgrade_dict: dict, exp_dict: dict):
        super().__init__()
        self._logger.setLevel(logging.INFO)
        self.discord_user_id = discord_user_id
        self.event_id = event_id
        self.end_time = end_time
        self.avg_dict = avg_dict
        self.upgrade_dict = upgrade_dict
        self.exp_dict = exp_dict
        self.event_record = None
        self.energy = None
        self.machine_record = None
        self.clicker_profile = None
        self.is_sync = False

    @override
    async def on_start(self) -> None:
        await super().register(self.discord_user_id)
        self.is_sync = await self.fetch_records()

    @override
    async def run_loop(self) -> None:
        if self.is_sync:
            while self.end_time > int(datetime.now().timestamp()):
                try:
                    await super().register(self.discord_user_id)
                    await self.claim_energy()
                    if await self.is_premium():
                            return
                except Exception as e:
                    self._logger.exception(f"(User: {self.discord_user_id}) encountered process exception: {e}")
                await self.wait_until_next_update()

    """ Claim energy from collect machine """
    async def claim_energy(self) -> None:
        payload = { 'event_id': self.event_id }
        resp = await self._post(self.api.sexual_dating.claimItemExplore, payload)
        if resp.success():
            # update user records
            self.event_record = resp.user_record()
            self.energy = resp.user_energy()
            self.machine_record = resp.user_explore_item_record()
            amount = resp.updated_item_list()[0]['amount']
            self._logger.debug(f"(User: {self.discord_user_id}) collected {amount} energy. energy total: {self.energy}")
        else:
            self._logger.error(f"(User: {self.discord_user_id}) failed to collect energy, reason: {resp.error_message()}")

    """ Get the latest event records, return bool. """
    async def fetch_records(self) -> bool:
        resp = await self._get(self.api.sexual_dating.records)
        if resp.success():
            self.event_record = resp.user_record()
            self.energy = resp.user_energy()
            self.machine_record = resp.user_explore_item_record()

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

    def _update_duration(self) -> None:
        try:
            tier = self.dating_record['item_tier']
            for machine in self.machine_list:
                if machine['tier'] == tier:
                    self.duration = machine['max_duration']
                    self._logger.debug(f"(User: {self.discord_user_id}) updated duration to {self.duration} seconds.")
                    return None
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

    def user_record(self, event_id: int) -> dict | None:
        try:
            record = self.response()['user_record']
            if record['event_id'] == event_id:
                return record
            return None
        except:
            return None

    def user_energy(self) -> int | None:
        try:
            return self.response()['user_energy']['energy']
        except:
            return None

    def user_explore_item_record(event_id: int) -> dict | None:
        try:
            record = self.response()['user_explore_item_record']
            if record['event_id'] == event_id:
                return record
            return None
        except:
            return None



async def main():
    manager = SexualDatingManager()
    await manager.build_event_config()
    #await manager.run()

if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
