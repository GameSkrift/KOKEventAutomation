import json
import os
from dotenv import load_dotenv
from datetime import datetime
from asynctinydb import TinyDB, Query
from asynctinydb.table import Table

load_dotenv()
LOCAL_STORAGE = os.environ["LOCAL_STORAGE"]
RECORD = Query()

""" Asynchronous TinyDB with CRUD implementation """
class Storage:
    def __init__(self):
        db = TinyDB(LOCAL_STORAGE, no_dbcache=True)
        db.isolevel = 2
        self.user = self.UserTable(db.table("subscription"))

    class UserTable:
        def __init__(self, table):
            self.table = table

        async def add_new_record(self, discord_user_id, user_id, nutaku_id=None, premium=False, bot=False):
            new_ts = self._get_current_timestamp()
            if not await self.table.contains(RECORD.discord_user_id == str(discord_user_id)):
                new_record = { 'discord_user_id': str(discord_user_id), 'nutaku_id': str(nutaku_id), 'user_id': str(user_id), 'guild_id': '', 'name': '', 'premium': premium, 'bot': bot, 'session_id': '', 'socket_token': '', 'create_time': new_ts, 'last_update': new_ts, 'last_session_update': 0, 'next_update': 0 }
                await self.table.insert(new_record)
            else:
                raise Exception("User table record already exists!") 
    
        async def get_user_record(self, discord_user_id) -> dict:
            return await self.table.get(RECORD.discord_user_id == str(discord_user_id))

        async def get_all_records(self) -> list:
            return await self.table.all()

        async def get_next_update_timestamp(self, discord_user_id) -> int:
            record = await self.get_user_record(discord_user_id)
            return record['next_update']

        async def get_next_update_records(self) -> list:
            new_ts = self._get_current_timestamp()
            return await self.table.search(RECORD.next_update <= new_ts)

        async def update_nutaku_id(self, discord_user_id, nutaku_id):
            new_ts = self._get_current_timestamp()
            await self.table.update({ 'nutaku_id': str(nutaku_id), 'last_update': new_ts }, RECORD.discord_user_id == discord_user_id)

        async def update_user_id(self, discord_user_id, user_id):
            new_ts = self._get_current_timestamp()
            await self.table.update({ 'user_id': str(user_id), 'last_update': new_ts }, RECORD.discord_user_id == discord_user_id)

        async def update_guild_id(self, discord_user_id, guild_id):
            new_ts = self._get_current_timestamp()
            await self.table.update({ 'guild_id': str(guild_id), 'last_update': new_ts }, RECORD.discord_user_id == discord_user_id)

        async def update_session_id(self, discord_user_id, session_id):
            new_ts = self._get_current_timestamp()
            await self.table.update({ 'session_id': session_id, 'last_update': new_ts, 'last_session_update': new_ts }, RECORD.discord_user_id == discord_user_id)

        async def update_session(self, discord_user_id, user_id, name, session_id, socket_token, server_time: int):
            new_ts = self._get_current_timestamp()
            await self.table.update({ 'user_id': str(user_id), 'name': name, 'session_id': session_id, 'socket_token': socket_token, 'last_update': new_ts, 'last_session_update': server_time }, RECORD.discord_user_id == discord_user_id)

        async def set_next_update_timestamp(self, discord_user_id, next_ts: int):
            new_ts = self._get_current_timestamp()
            await self.table.update({ 'last_update': new_ts, 'next_update': next_ts }, RECORD.discord_user_id == discord_user_id)

        async def verify_socket_token(self, discord_user_id, since_sec=21600) -> bool:
            user_info = await self.get_user_record(discord_user_id)
            new_ts = self._get_current_timestamp()
            return True if new_ts - user_info['last_session_update'] < since_sec else False

        async def remove_record(self, discord_user_id):
            await self.table.remove(RECORD.discord_user_id == discord_user_id)

        async def remove_record_by_user_id(self, user_id):
            await self.table.remove(RECORD.user_id == user_id)

        def _get_current_timestamp(self) -> int:
            return int(datetime.now().timestamp())
