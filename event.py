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
from network import CONFIG_DIR
from storage import Database, UserDocument, DiscordID, LOCAL_STORAGE

__all__ = ('BaseConfig', 'BaseEventManager')

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


class BaseEventManager(Database):
    _running_users: set[UserDocument] = set()
    _coroutines: dict[DiscordID, Coroutine] = dict()
    
    def __init__(self, config: str, filepath=LOCAL_STORAGE, sync_secs=60):
        super().__init__(filepath)
        self.config = config
        self._sync_secs = sync_secs
    
    @abstractmethod
    async def build_event_config(self):
        """
        Build a minimal infotainment for customised event automation
        """
        raise NotImplementedError()

    @abstractmethod
    async def create_user_instance(self, user: UserDocument):
        """
        This is where you initialise customised event class with setup function (if any)
        """
        raise NotImplementedError()

    """ Main entry for all customised EventManager coroutines """
    async def run(self):
        while self.end_time > int(datetime.now().timestamp()):
            async with asyncio.TaskGroup() as tg:
                (new_users, delete_users) = await self._maintain_users()
                for user in new_users:
                    new_instance = await self.create_user_instance(user)
                    event = new_instance.run_loop()
                    # append corountine with matched discord User ID
                    if user.doc_id not in self._coroutines.keys(): 
                        kv = { user.doc_id: event }
                        self._coroutines.update(kv)
                        tg.create_task(event)
                for user in delete_users:
                    if user.doc_id in self._coroutines.keys():
                        self._coroutines[user.doc_id].close()

            await asyncio.sleep(self._sync_secs)
                    
    """ Maintain local hash set of running instances by comparing to table users, returns a tuple of new and deleted user sets"""
    async def _maintain_users(self) -> (set[UserDocument], set[UserDocument]):
        new_users = delete_users = set()
        from_table = await self.user.get_all_users()
        if self._running_users:
            new_users = set(from_table).difference(self._user_list)
            delete_users = self._running_users.difference(set(from_table))
            # sync local _running_users to user table storage
            self._running_users.update(new_users).symmetric_difference_update(delete_users)   
        else:
            new_users = set(from_table)
            self._running_users = new_users
        return (new_users, delete_users)
