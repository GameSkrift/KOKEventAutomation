#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from zipfile import ZipFile
from api import GameAPI
from storage import Database, DiscordID

load_dotenv()
CONFIG_DIR = os.environ["CONFIG_DIR"]
PASSWORD = os.environ["PASSWORD"]

def handler():
    handler = logging.StreamHandler()
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(formatter)
    return handler


class NetworkManager:
    _logger = logging.getLogger('NetworkManager')

    def __init__(self):
        self.api = GameAPI()
        self.db = Database()
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            self._logger.addHandler(handler())
        if not os.path.exists(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)

    """ Log into the game by user's nutaku ID and update user database session. If session ID is given, bypass the login request."""
    async def register(self, discord_user_id: DiscordID, session_id=None) -> None:
        user = await self.db.user.get_user(discord_user_id)
        user_id = user.get_user_id()
        prefix = user.get_prefix()
        if session_id:
            me = await self._get_async(self.api.user.info, user_id, session_id, prefix).me()
            if user.get_name():
                await self.db.user.update_session_id(discord_user_id, session_id)
            else:
                await self.db.user.update_user(discord_user_id, int(me['user_id']), me['display_name'], session_id, socket_token, int(me['last_login_time']))
            self._logger.info(f"(User: {discord_user_id}) has updated new session_id ({session_id})")
        else:
            nutaku_id = user.get_nutaku_id()
            info = await self.login(discord_user_id, nutaku_id, prefix)
            if info:
                await self.db.user.update_user(discord_user_id, int(info['user_id']), info['name'], info['session_id'], info['socket_token'], int(info['last_login_time']))
                self._logger.info(f"(User: {discord_user_id}) has updated new session_id ({info['session_id']})")
        # ensure that the new session has flushed into disk
        await asyncio.sleep(1)

    """ Send asynchronous POST login request and return player credentials on success. """
    async def login(self, discord_user_id: DiscordID, nutaku_id: int, prefix: int) -> dict | None:
        acc = await self._post_async(self.api.auth.login.game_account, { "login_id": nutaku_id, "login_type": 0, "access_token": "", "pw": nutaku_id }, require_login=False)
        if acc.success():
            session_id = acc.response()['session_id']
            account_id = acc.response()['account_id']
            user = await self._post_async(self.api.auth.login.user, { "server_prefix": prefix, "account_id": account_id, "session_id": session_id }, nutaku_id=nutaku_id, require_login=False)
            if user.success():
                me = user.me()
                return { 'user_id': me['user_id'], 'name': me['display_name'], 'session_id': session_id, 'socket_token': user.response()['socket_token'], 'last_login_time': me['last_login_time'] }
            else:
                self._logger.error(f"(User: {discord_user_id}) failed logging into the game, reason: {user.error_message()}")
        else:
            self._logger.error(f"(User: {discord_user_id}) failed logging into the game, reason: {acc.error_message()}")
        return None

    """ Send asynchronous GET request by providing the API name and discord user ID. """
    async def get(self, api_name: GameAPI, discord_user_id: DiscordID, q=None, event_id=None, battle_id=None) -> dict | None:
        uri = await self._fetch_uri(discord_user_id)
        user_id = uri['user_id']
        session_id = uri['session_id']
        prefix = uri['prefix']
        return await self._get_async(api_name, user_id, session_id, prefix, q, event_id, battle_id)

    """ Send asynchronous POST request by providing the API name and discord user ID. """
    async def post(self, api_name: GameAPI, payload: dict, discord_user_id: DiscordID, nutaku_id=None, require_login=True) -> dict | None:
        uri = await self._fetch_uri(discord_user_id, require_login)
        user_id = uri['user_id']
        session_id = uri['session_id']
        prefix = uri['prefix']
        return await self._post_async(api_name, payload, user_id, prefix, session_id, nutaku_id, require_login)

    """ Async GET request builder. """
    async def _get_async(self, api_name, user_id, session_id, prefix, q=None, event_id=None, battle_id=None) -> dict | None:
        if q and api_name == self.api.user.friend.search:
            uri = "{}q={}&user_id={}&session_id={}&server_prefix={}".format(api_name, q, user_id, session_id, prefix)
        elif event_id:
            uri = "{}event_id={}&user_id={}&session_id={}&server_prefix={}".format(api_name, event_id, user_id, session_id, prefix)
        elif battle_id:
            uri = "{}user_id={}&session_id={}&server_prefix={}&battleId={}&serverPrefix={}".format(api_name, user_id, session_id, prefix, battle_id, prefix)
        else:
            uri = "{}user_id={}&session_id={}&server_prefix={}".format(api_name, user_id, session_id, prefix)
        async with aiohttp.ClientSession() as session:
            self._logger.debug(f"(User: {self.discord_user_id}) is sending GET request to {uri}")
            try:
                async with session.get(uri) as resp:
                    body = await resp.json()
                    return Response(body)
            except Exception as e:
                self._logger.exception(f"GET request error: {e}")
                return None

    """ Async POST request builder. """
    async def _post_async(self, api_name, payload, user_id=None, prefix=None, session_id=None, nutaku_id=None, require_login=True) -> dict | None:
        if require_login:
            async with aiohttp.ClientSession() as session:
                uri = "{}user_id={}&session_id={}&server_prefix={}".format(api_name, user_id, session_id, prefix)
                self._logger.debug(f"(User: {self.discord_user_id}) is sending POST request to {uri} with payload {payload}")
                try:
                    async with session.post(uri, data=payload) as resp:
                        body = await resp.json()
                        return Response(body)
                except Exception as e:
                    self._logger.exception(f"POST request error: {e}")
                    return None
        else:
            match api_name:
                case self.api.auth.login.game_account:
                    uri = api_name
                case self.api.auth.login.user:
                    uri = "{}nutaku_id={}".format(api_name, nutaku_id)
                case _:
                    self._logger.error(f"(API): {api_name}) requires user session.")
                    return None
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(uri, data=payload) as resp:
                        body = await resp.json()
                        return Response(body)
                except Exception as e:
                    self._logger.exception(f"POST request error: {e}")
                    return None

    async def _fetch_uri(self, discord_user_id: DiscordID, require_login=True) -> dict:
        user = await self.db.user.get_user(discord_user_id)
        user_id = user.get_user_id()
        prefix = user.get_prefix()
        if require_login:
            session_id = user.get_session_id()
            if session_id:
                guild_id = user.get_guild_id()
                #TODO: URI Class
                uri = { 'user_id': user_id, 'prefix': prefix, 'session_id': session_id, 'guild_id': guild_id }
                return uri
            else:
                reason = f"(User: {discord_user_id}) has not logged into server yet!"
                raise Exception(reason)
        else:
            nutaku_id = user.get_nutaku_id()
            uri = { 'nutaku_id': nutaku_id, 'user_id': user_id, 'prefix': prefix }
            return uri


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
