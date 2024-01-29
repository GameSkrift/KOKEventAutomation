# -*- coding: utf-8 -*-
import json
import logging
import os
import io
import msgpack
import asyncio
import aiohttp
from zipfile import ZipFile
from datetime import datetime
from abc import abstractmethod
from typing import Coroutine
from network import NetworkManager, CONFIG_DIR
from storage import Database, UserDocument, DiscordID, LOCAL_STORAGE

__all__ = ('BaseConfig', 'BaseEvent', 'BaseEventManager')

class BaseConfig:
    _logger = logging.getLogger(__name__)
    asset_uri = 'https://ntk-zone-api.kokmm.net/api/system/assets?asset_v=0&device_type=web'

    def __init__(self, config: str):
        self._config = config

    async def _get_asset_list(self) -> list:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.asset_uri) as resp:
                    body = await resp.json()
                    self.download_url = body['response']['download_url']
                    return body['response']['assets']['asset_patchs']
            except Exception as e:
                self._logger.exception(f"Failed to download asset list from {self.asset_uri}, exception: {e}")

    async def get_dict(self) -> dict | None:
        netpath = None
        asset_list = await self._get_asset_list()
        for metadata in asset_list:
            if metadata[0] == self._config:
                netpath = metadata[1]
                asset_url = f"{self.download_url}{netpath}"
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(asset_url) as resp:
                            assert resp.status == 200
                            content = await resp.read()
                            bytestream = io.BytesIO(content)
                            filename = self._config.replace('.zip', '.byte')
                            full_path = os.path.join(CONFIG_DIR, filename)
                            with ZipFile(bytestream, 'r') as zipref:
                                zipref.extractall(CONFIG_DIR)
                                with open(full_path, 'br') as f:
                                    setting_dict = msgpack.unpackb(f.read(), raw=False, strict_map_key=False)
                                    return setting_dict
                    except Exception as e:
                        self._logger.exception(f"Failed to download (Filename: {self._config}) from {asset_url}, exception: {e}")
        self._logger.error(f"Could not find config file with the name {self._config}")
        return None


class BaseEvent(NetworkManager):
    def __init__(self, *, filepath=LOCAL_STORAGE):
        super().__init__(filepath)

    @abstractmethod
    async def on_start(self) -> None:
        """
        This is where we initialise player event record from ``record?`` GET request after event [setup](optional)
        """
        raise NotImplementedError()

    @abstractmethod
    async def run_loop(self) -> None:
        """
        This is where you put automation servies after awaiting ``self.on_start()``
        """
        raise NotImplementedError()


class BaseEventManager(Database):
    _running_users: set[UserDocument] = set()
    _coroutines: dict[DiscordID, Coroutine] = dict()
    
    def __init__(self, config: str, filepath=LOCAL_STORAGE, interval=60):
        super().__init__(filepath)
        self.config = config
        self._interval = interval
    
    @abstractmethod
    async def build_event_config(self):
        """
        Build a minimal infotainment for customised event automation
        """
        raise NotImplementedError()

    @abstractmethod
    def create_user_instance(self, user: UserDocument) -> BaseEvent:
        """
        This is where you initialise customised event class with event [setup](optional)

        NOTE: It must return initialised custom event class to proceed with ``user_instance.on_start()``
        """
        raise NotImplementedError()

    async def run(self, semaphore=asyncio.Semaphore(10)):
        """
        Main entry for all customised EventManager coroutines
        """
        while self.end_time > int(datetime.now().timestamp()):
            (new_users, delete_users) = await self._maintain_users()
            await self._start_new_instances(new_users, semaphore)
            self._delete_running_instances(delete_users)
            # sleep for (default=60) seconds
            await asyncio.sleep(self._interval)

    """ Create and start running user coroutines by ``asyncio.create_task`` """
    async def _start_new_instances(self, new_users: list[DiscordID], semaphore) -> None:
        for user in new_users:
            async with semaphore:
                new_event = self.create_user_instance(user)
                #TODO: try to at least ensure on_start()
                await new_event.on_start()
                new_instance = asyncio.create_task(new_event.run_loop())
                discord_id = user.doc_id
                # append corountine with matched DiscordID
                if discord_id not in self._coroutines.keys():
                    new_record = { discord_id: new_instance }
                    self._coroutines.update(new_record)
                    self._running_users.add(user)

    """ Cancel running coroutines matched by DiscordID, then delete entry from ``self._running_users`` """
    def _delete_running_instances(self, delete_users: list[DiscordID]) -> None:
        for user in delete_users:
            delete_discord_id = user.doc_id
            if delete_discord_id in self._coroutines.keys():
                on_cancel_event = self._coroutines.pop(delete_discord_id)
                on_cancel_event.cancel()
                self._running_users.discard(user)
                    
    """ Maintain local hash set of running instances by comparing to table users, returns a tuple of new and deleted user sets"""
    async def _maintain_users(self) -> (set[UserDocument], set[UserDocument]):
        new_users = delete_users = set()
        from_table = await self.user.get_all_users()
        if self._running_users:
            new_users = set(from_table).difference(self._running_users)
            delete_users = self._running_users.difference(set(from_table))
            # sync local _running_users hash set with user table storage
            self._running_users.update(new_users)
            self._running_users.symmetric_difference_update(delete_users)
        else:
            new_users = set(from_table)
            self._running_users = new_users

        return (new_users, delete_users)
