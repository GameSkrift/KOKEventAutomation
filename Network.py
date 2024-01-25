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
    async def login(self, discord_user_id, session_id=None) -> None:
        record = await self.db.user.get_user_record(discord_user_id)
        if session_id:
            await self.db.user.update_session_id(discord_user_id, session_id)
            self.logger.info(f"(User: {discord_user_id}) has updated new session_id ({session_id})")
        else:
            acc = await self.post(discord_user_id, self.api.auth.login.game_account, { "login_id": record['nutaku_id'], "login_type": 0, "access_token": "", "pw": record['nutaku_id'] }, require_login=False)
            if acc.success():
                login_info = acc.response()
                session_id = login_info['session_id']
                account_id = login_info['account_id']
                user = await self.post(discord_user_id, self.api.auth.login.user, { "server_prefix": record['user_id'][:3], "account_id": account_id, "session_id": session_id }, require_login=False)
                if user.success():
                    me = user.me()
                    await self.db.user.update_session(discord_user_id, me['user_id'], me['display_name'], session_id, user.response()['socket_token'], me['last_login_time'])
                    self.logger.info(f"(User: {discord_user_id}) has updated new session_id ({session_id})")
                    await asyncio.sleep(1)
            else:
                self.logger.error(f"(User: {discord_user_id}) failed logging into the game, reason: {acc.error_message()}")


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

    """ Universal GET request builder for game client by API name. """
    async def get(self, discord_user_id, api_name, q=None, event_id=None, battle_id=None) -> dict | None:
        uri = await self._fetch_uri(discord_user_id)
        try:
            if q and api_name == self.api.user.friend.search:
                uri = "{}q={}&user_id={}&session_id={}&server_prefix={}".format(api_name, q, uri['user_id'], uri['session_id'], uri['prefix'])
            elif event_id:
                uri = "{}event_id={}&user_id={}&session_id={}&server_prefix={}".format(api_name, event_id, uri['user_id'], uri['session_id'], uri['prefix'])
            elif battle_id:
                uri = "{}user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}".format(api_name, uri['user_id'], uri['session_id'], uri['prefix'], battle_id, uri['prefix'])
            else:
                uri = "{}user_id={}&session_id={}&server_prefix={}".format(api_name, uri['user_id'], uri['session_id'], uri['prefix'])
            return Response(requests.get(uri).json())
        except Exception as e:
            self.logger.exception(f"GET request error: {e}")
            return None


    """ Universal POST request builder for game client by API name. """
    async def post(self, discord_user_id, api_name, payload, require_login=True):
        uri = await self._fetch_uri(discord_user_id, require_login)
        api = self.api
        try:
            match api_name:
                case api.auth.login.game_account:
                    uri = f"{api_name}"
                    return Response(requests.post(uri, payload).json())
                case api.auth.login.user:
                    uri = "{}nutaku_id={}".format(api_name, uri['nutaku_id'])
                    return Response(requests.post(uri, payload).json())
                case _:
                    uri = "{}user_id={}&session_id={}&server_prefix={}".format(api_name, uri['user_id'], uri['session_id'], uri['prefix'])
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



