#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import msgpack
import requests
import logging
import io
import os
import asyncio
from dotenv import load_dotenv
from zipfile import ZipFile
from api import GameApi
from storage import Storage
from enum import Enum

load_dotenv()
CONFIG_DIR = os.environ["CONFIG_DIR"]
PASSWORD = os.environ["PASSWORD"]

class NetworkManager:
    def __init__(self):
        self.api = GameApi()
        self.db = Storage()
        self.logger = logging.getLogger('NetworkManager')
        self.logger.setLevel(logging.DEBUG)
        if not os.path.exists(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)

    """ Log into the game by user's nutaku ID and update user database session. If session ID is given, bypass the login request."""
    async def register(self, discord_user_id, session_id=None) -> None:
        record = await self.db.user.get_user_record(discord_user_id)
        if session_id:
            me = self.get(self.api.user.info, record['user_id'], session_id, record['user_id'][:3]).me()
            if record['display_name']:
                await self.db.user.update_session_id(discord_user_id, session_id)
            else:
                await self.db.user.update_session(discord_user_id, me['user_id'], me['display_name'], session_id, socket_token, me['last_login_time'])
            self.logger.info(f"(User: {discord_user_id}) has updated new session_id ({session_id})")
        else:
            info = self.login(discord_user_id, record['nutaku_id'], record['user_id'][:3])
            if info:
                await self.db.user.update_session(discord_user_id, info['user_id'], info['name'], info['session_id'], info['socket_token'], info['last_login_time'])
                self.logger.info(f"(User: {discord_user_id}) has updated new session_id ({info['session_id']})")
        # ensure that the new session has flushed into disk
        await asyncio.sleep(1)

    """ POST login request and return player credentials on success. """
    def login(self, discord_user_id, nutaku_id, prefix) -> dict | None:
        acc = requests.post(self.api.auth.login.game_account, { "login_id": nutaku_id, "login_type": 0, "access_token": "", "pw": nutaku_id }).json()
        if acc['success']:
            login_info = acc['response']
            session_id = login_info['session_id']
            account_id = login_info['account_id']
            uri = f"{self.api.auth.login.user}nutaku_id={nutaku_id}"
            user = requests.post(uri, { "server_prefix": prefix, "account_id": account_id, "session_id": session_id }).json()
            if user['success']:
                me = user['me']
                return { 'user_id': me['user_id'], 'name': me['display_name'], 'session_id': session_id, 'socket_token': user['response']['socket_token'], 'last_login_time': me['last_login_time'] }
            else:
                self.logger.error(f"(User: {discord_user_id}) failed logging into the game, reason: {user['error_message']}")
        else:
            self.logger.error(f"(User: {discord_user_id}) failed logging into the game, reason: {acc['error_message']}")

    """ Fetch the asset list from server and download config file by filename. """
    def install_config(self, filename) -> dict | None:
        fpath = None
        (prefix, asset_list) = self._get_asset_list()
        for metadata in asset_list:
            if metadata[0] == filename:
                fpath = metadata[1]
                url = f"{prefix}{fpath}"
                content = requests.get(url).content
                bytestream = io.BytesIO(content)
                filename = filename.replace('.zip', '.byte')
                full_path = os.path.join(CONFIG_DIR, filename)
                with ZipFile(bytestream, 'r') as zip_ref:
                    zip_ref.extractall(CONFIG_DIR)
                    with open(full_path, 'br') as f:
                        return msgpack.unpackb(f.read(), raw=False, strict_map_key=False)
        else:
            self.logger.error(f"Could not find config file with the name {filename}")
            return None

    """ Download Localization.csv file and return the content. """
    def get_localization(self) -> str | None:
        (prefix, asset_list) = self._get_asset_list()
        for metadata in asset_list:
            if metadata[0] == 'Localization.csv':
                url = f"{prefix}{metadata[1]}"
                csv = requests.get(url).text
                return csv.split('\n')
        return None

    """ Download encrypted unity3d assets at destinated file location. """
    def download_assets(self, keyword, download_dir):
        resp = self._get_asset_list()
        (url, asset_list) = self._get_asset_list()
        if not os.path.exists(download_dir):
            os.mkdir(download_dir)
        for metadata in asset_list:
            if keyword in metadata[0]:
                uri = f"{url}{metadata[1]}"
                self.logger.debug(f"Downloading content from {uri}")
                content = requests.get(uri).content
                bytestream = io.BytesIO(content)
                download_path = download_dir.joinpath(metadata[0])
                self.logger.debug(f"(File: {metadata[0]}) has been downloaded at {download_path}, extracting files ...")
                if metadata[0].endswith('.zip'):
                    with ZipFile(bytestream, 'r') as zip_ref:
                        zip_ref.extractall(download_dir, pwd=PASSWORD.encode('utf-8'))
                else:
                    with open(download_path, "wb") as outfile:
                        # Copy the BytesIO stream to the output file
                        outfile.write(bytestream.getbuffer())

    """ Download entire game assets at destinated file location. """
    def download_assets_all(self, download_dir):
        resp = self._get_asset_list()
        (url, asset_list) = self._get_asset_list()
        if not os.path.exists(download_dir):
            os.mkdir(download_dir)
        for metadata in asset_list:
            uri = f"{url}{metadata[1]}"
            self.logger.debug(f"Downloading content from {uri}")
            content = requests.get(uri).content
            bytestream = io.BytesIO(content)
            download_path = download_dir.joinpath(metadata[0])
            self.logger.debug(f"(File: {metadata[0]}) has been downloaded at {download_path}, extracting files ...")
            if metadata[0].endswith('.zip'):
                with ZipFile(bytestream, 'r') as zip_ref:
                    zip_ref.extractall(download_dir, pwd=PASSWORD.encode('utf-8'))
            else:
                with open(download_path, "wb") as outfile:
                    # Copy the BytesIO stream to the output file
                    outfile.write(bytestream.getbuffer())

    """ Async GET request builder with game server APIs for users. """
    async def get_async(self, api_name, discord_user_id, q=None, event_id=None, battle_id=None) -> dict | None:
        uri = await self._fetch_uri(discord_user_id)
        user_id = uri['user_id']
        session_id = uri['session_id']
        return self.get(api_name, user_id, session_id, q, event_id, battle_id)

    """ Async POST request builder with game server APIs for users. """
    async def post_async(self, api_name, discord_user_id, payload, nutaku_id=None, require_login=True) -> dict | None:
        uri = await self._fetch_uri(discord_user_id, require_login)
        user_id = uri['user_id']
        session_id = uri['session_id']
        return self.post(api_name, user_id, session_id, payload, nutaku_id, require_login)

    """ GET request builder with game server APIs for manual users. """
    def get(self, api_name, user_id, session_id, q=None, event_id=None, battle_id=None) -> dict | None:
        assert len(user_id) == 13
        prefix = user_id[:3]
        try:
            if q and api_name == self.api.user.friend.search:
                uri = "{}q={}&user_id={}&session_id={}&server_prefix={}".format(api_name, q, user_id, session_id, prefix)
            elif event_id:
                uri = "{}event_id={}&user_id={}&session_id={}&server_prefix={}".format(api_name, event_id, user_id, session_id, prefix)
            elif battle_id:
                uri = "{}user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}".format(api_name, user_id, session_id, prefix, battle_id, prefix)
            else:
                uri = "{}user_id={}&session_id={}&server_prefix={}".format(api_name, user_id, session_id, prefix)
            return Response(requests.get(uri).json())
        except Exception as e:
            self.logger.exception(f"GET request error: {e}")
            return None

    """ POST request builder with game server APIs for manual users. """
    def post(self, api_name, user_id, session_id, payload, nutaku_id=None, require_login=True) -> dict | None:
        assert len(user_id) == 13
        prefix = user_id[:3]
        try:
            if require_login:
                uri = "{}user_id={}&session_id={}&server_prefix={}".format(api_name, user_id, session_id, prefix)
                return Response(requests.post(uri, payload).json())
            else:
                match api_name:
                    case self.api.auth.login.game_account:
                        uri = f"{api_name}"
                        return Response(requests.post(uri, payload).json())
                    case self.api.auth.login.user:
                        uri = "{}nutaku_id={}".format(api_name, nutaku_id)
                        return Response(requests.post(uri, payload).json())
        except Exception as e:
            self.logger.exception(f"POST request error: {e}")
            return None

    async def _fetch_uri(self, discord_user_id, require_login=True) -> dict:
        record = await self.db.user.get_user_record(discord_user_id)
        if require_login:
            if record['session_id']:
                uri = { 'user_id': record['user_id'], 'prefix': record['user_id'][:3], 'session_id': record['session_id'], 'guild_id': record['guild_id'] }
                return uri
            else:
                reason = f"(User: {discord_user_id}) has not logged into server yet!"
                raise Exception(reason)
        else:
            uri = { 'nutaku_id': record['nutaku_id'] ,'user_id': record['user_id'], 'prefix': record['user_id'][:3] }
            return uri

    def _get_asset_list(self) -> (str, list):
        url = "{}/api/system/assets?asset_v=0&device_type=web".format(self.api.data_url)
        r = requests.get(url).json()
        return (r['response']['download_url'], r['response']['assets']['asset_patchs'])

    def get_asset_list_by_version(self, version: int) -> list:
        url = "{}/api/system/assets?asset_v={}&device_type=web".format(self.api.data_url, version)
        r = requests.get(url).json()
        return r['response']['assets']['asset_patchs']

    def get_secret_asset_list_by_version(self, version: int) -> list:
        url = "{}/api/system/assets?asset_v={}&device_type=websecret".format(self.api.data_url, version)
        r = requests.get(url).json()
        return r['response']['assets']['asset_patchs']

    def get_odd_list_by_version(self, version: int) -> list:
        url = "{}/api/system/assets?asset_v={}&device_type=webodd".format(self.api.data_url, version)
        r = requests.get(url).json()
        return r['response']['assets']['asset_patchs']


class Response(dict):
    def __init__(self, body):
        self.body = body

    def success(self) -> bool:
        return self.body['success']
    
    def error(self) -> bool:
        return not self.success()

    def error_code(self) -> int | None:
        return self.body['error_code'] if self.error() else None

    def error_message(self) -> str | None:
        return self.body['error_message'] if self.error() else None
    
    def me(self) -> dict | None:
        try:
            return self.body['me']
        except:
            return None
    
    def response(self) -> dict | None:
        try:
            return self.body['response']
        except:
            return None

    def __str__(self) -> str:
        fmt = json.dumps(self.body, indent=2, ensure_ascii=False)
        return f"{fmt}"



