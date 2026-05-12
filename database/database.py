import datetime
import motor.motor_asyncio


class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.clones_col = self.db.clone_bots  # Collection for storing clone bots

    # ─────────────────────────────────────────────
    #  USER METHODS
    # ─────────────────────────────────────────────

    def new_user(self, id):
        return dict(
            id=id,
            join_date=datetime.date.today().isoformat(),
            notif=True,
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=datetime.date.max.isoformat(),
                ban_reason="",
            ),
        )

    async def add_user(self, id):
        user = self.new_user(id)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({"id": int(id)})
        return True if user else False

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"id": int(user_id)})

    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_duration=0,
            banned_on=datetime.date.max.isoformat(),
            ban_reason="",
        )
        await self.col.update_one({"id": id}, {"$set": {"ban_status": ban_status}})

    async def ban_user(self, user_id, ban_duration, ban_reason):
        ban_status = dict(
            is_banned=True,
            ban_duration=ban_duration,
            banned_on=datetime.date.today().isoformat(),
            ban_reason=ban_reason,
        )
        await self.col.update_one({"id": user_id}, {"$set": {"ban_status": ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_duration=0,
            banned_on=datetime.date.max.isoformat(),
            ban_reason="",
        )
        user = await self.col.find_one({"id": int(id)})
        if not user:
            return default
        return user.get("ban_status", default)

    async def get_all_banned_users(self):
        return self.col.find({"ban_status.is_banned": True})

    async def set_notif(self, id, notif):
        await self.col.update_one({"id": id}, {"$set": {"notif": notif}})

    async def get_notif(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("notif", False) if user else False

    async def get_all_notif_user(self):
        return self.col.find({"notif": True})

    async def total_notif_users_count(self):
        return await self.col.count_documents({"notif": True})

    # ─────────────────────────────────────────────
    #  CLONE BOT METHODS
    # ─────────────────────────────────────────────

    async def add_clone(self, owner_id: int, bot_token: str, bot_username: str):
        """Register a new clone bot in the database."""
        existing = await self.clones_col.find_one({"bot_token": bot_token})
        if existing:
            return False  # Already cloned with this token
        doc = dict(
            owner_id=owner_id,
            bot_token=bot_token,
            bot_username=bot_username,
            created_at=datetime.datetime.utcnow().isoformat(),
            is_active=True,
        )
        await self.clones_col.insert_one(doc)
        return True

    async def remove_clone(self, bot_token: str):
        """Delete a clone bot record."""
        await self.clones_col.delete_one({"bot_token": bot_token})

    async def get_all_clones(self):
        """Return cursor of all active clone bots."""
        return self.clones_col.find({"is_active": True})

    async def get_clone_by_owner(self, owner_id: int):
        """Get clone bot info for a specific owner."""
        return await self.clones_col.find_one({"owner_id": owner_id})

    async def get_clone_by_token(self, bot_token: str):
        """Get clone bot info by token."""
        return await self.clones_col.find_one({"bot_token": bot_token})

    async def total_clones_count(self):
        return await self.clones_col.count_documents({"is_active": True})

    # Per-clone user collections (each clone has its own users)
    def get_clone_users_col(self, bot_username: str):
        """Return a per-clone users collection."""
        safe_name = bot_username.replace("@", "").lower()
        return self.db[f"clone_{safe_name}_users"]

    async def add_clone_user(self, bot_username: str, user_id: int):
        col = self.get_clone_users_col(bot_username)
        if not await col.find_one({"id": user_id}):
            await col.insert_one(dict(
                id=user_id,
                join_date=datetime.date.today().isoformat(),
                notif=True,
                ban_status=dict(
                    is_banned=False,
                    ban_duration=0,
                    banned_on=datetime.date.max.isoformat(),
                    ban_reason="",
                ),
            ))

    async def is_clone_user_exist(self, bot_username: str, user_id: int):
        col = self.get_clone_users_col(bot_username)
        return bool(await col.find_one({"id": user_id}))

    async def get_clone_ban_status(self, bot_username: str, user_id: int):
        col = self.get_clone_users_col(bot_username)
        default = dict(is_banned=False, ban_duration=0,
                       banned_on=datetime.date.max.isoformat(), ban_reason="")
        user = await col.find_one({"id": user_id})
        return user.get("ban_status", default) if user else default

    async def ban_clone_user(self, bot_username: str, user_id: int, ban_duration: int, ban_reason: str):
        col = self.get_clone_users_col(bot_username)
        ban_status = dict(is_banned=True, ban_duration=ban_duration,
                          banned_on=datetime.date.today().isoformat(), ban_reason=ban_reason)
        await col.update_one({"id": user_id}, {"$set": {"ban_status": ban_status}})

    async def unban_clone_user(self, bot_username: str, user_id: int):
        col = self.get_clone_users_col(bot_username)
        ban_status = dict(is_banned=False, ban_duration=0,
                          banned_on=datetime.date.max.isoformat(), ban_reason="")
        await col.update_one({"id": user_id}, {"$set": {"ban_status": ban_status}})

    async def get_all_clone_users(self, bot_username: str):
        return self.get_clone_users_col(bot_username).find({})

    async def get_clone_notif_users(self, bot_username: str):
        return self.get_clone_users_col(bot_username).find({"notif": True})

    async def set_clone_notif(self, bot_username: str, user_id: int, notif: bool):
        col = self.get_clone_users_col(bot_username)
        await col.update_one({"id": user_id}, {"$set": {"notif": notif}})

    async def get_clone_notif(self, bot_username: str, user_id: int):
        col = self.get_clone_users_col(bot_username)
        user = await col.find_one({"id": user_id})
        return user.get("notif", True) if user else True

    async def total_clone_users_count(self, bot_username: str):
        col = self.get_clone_users_col(bot_username)
        return await col.count_documents({})

    async def delete_clone_user(self, bot_username: str, user_id: int):
        col = self.get_clone_users_col(bot_username)
        await col.delete_many({"id": user_id})
