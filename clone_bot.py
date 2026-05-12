"""
clone_bot.py
============
Har clone bot is file se run hota hai as a separate Pyrogram Client.
Clone ka owner = jisne /clone kiya
Main SUDO = OWNER_ID from Config (sabka sudo)
"""

import asyncio
import traceback
import logging

from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
)
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid

from config import Config
from database.database import Database

logger = logging.getLogger(__name__)

MAIN_SUDO = Config.OWNER_ID  # Main owner - har clone ka bhi sudo

IF_TEXT = "<b>Message from:</b> {}\n<b>Name:</b> {}\n\n{}"
IF_CONTENT = "<b>Message from:</b> {}\n<b>Name:</b> {}"


def create_clone_client(bot_token: str, api_id: int, api_hash: str, session_name: str) -> Client:
    """Create a new Pyrogram Client for the clone bot."""
    return Client(
        name=session_name,
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
        in_memory=True,  # No session file on disk
    )


async def run_clone_bot(bot_token: str, clone_owner_id: int, db: Database):
    """
    Start a clone bot. Clone ka owner = clone_owner_id.
    MAIN_SUDO bhi is bot ka sudo hai.
    """
    api_id = Config.API_ID
    api_hash = Config.API_HASH

    # Safe session name
    session_name = f"clone_{clone_owner_id}"

    app = create_clone_client(bot_token, api_id, api_hash, session_name)

    # ── Helper: check if user is sudo (clone owner ya main sudo) ──────────
    def is_sudo(user_id: int) -> bool:
        return user_id == clone_owner_id or user_id == MAIN_SUDO

    # ── Helper: get bot username ──────────────────────────────────────────
    async def get_bot_username():
        me = await app.get_me()
        return me.username

    # ──────────────────────────────────────────────────────────────────────
    #  CALLBACKS
    # ──────────────────────────────────────────────────────────────────────

    @app.on_callback_query()
    async def callback_handlers(client: Client, cb: CallbackQuery):
        user_id = cb.from_user.id
        bot_username = await get_bot_username()

        if "closeMeh" in cb.data:
            await cb.message.delete(True)

        elif "notifon" in cb.data:
            notif = await db.get_clone_notif(bot_username, user_id)
            new_notif = not notif
            await db.set_clone_notif(bot_username, user_id, new_notif)
            await cb.message.edit(
                f"`Here You Can Set Your Settings:`\n\nSuccessfully set notifications to **{new_notif}**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        f"NOTIFICATION  {'🔔' if new_notif else '🔕'}",
                        callback_data="notifon",
                    )],
                    [InlineKeyboardButton("CLOSE", callback_data="closeMeh")],
                ]),
            )
            await cb.answer(f"Notifications set to {new_notif}")

    # ──────────────────────────────────────────────────────────────────────
    #  /start
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("start") & filters.private)
    async def start(client: Client, message: Message):
        user_id = message.from_user.id
        bot_username = await get_bot_username()

        if not await db.is_clone_user_exist(bot_username, user_id):
            await db.add_clone_user(bot_username, user_id)

        ban_status = await db.get_clone_ban_status(bot_username, user_id)
        if ban_status["is_banned"]:
            await message.reply_text(
                f"You are Banned 🚫 to use this bot for **{ban_status['ban_duration']}** day(s) "
                f"for the reason __{ban_status['ban_reason']}__ \n\n**Message from the admin 🤠**"
            )
            return

        await message.reply_text(
            text=f"**Hi {message.from_user.first_name}!**\n\n{Config.START}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛠 SUPPORT 🛠", url=Config.SUPPORT_GROUP),
                 InlineKeyboardButton("📮 UPDATES 📮", url=Config.UPDATE_CHANNEL)]
            ])
        )

    # ──────────────────────────────────────────────────────────────────────
    #  /help
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("help") & filters.private)
    async def help_cmd(client: Client, message: Message):
        user_id = message.from_user.id
        bot_username = await get_bot_username()

        if not await db.is_clone_user_exist(bot_username, user_id):
            await db.add_clone_user(bot_username, user_id)

        ban_status = await db.get_clone_ban_status(bot_username, user_id)
        if ban_status["is_banned"]:
            await message.reply_text(
                f"You are Banned 🚫 to use this bot for **{ban_status['ban_duration']}** day(s) "
                f"for the reason __{ban_status['ban_reason']}__"
            )
            return

        await message.reply_text(
            text=Config.HELP,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛠 SUPPORT 🛠", url=Config.SUPPORT_GROUP),
                 InlineKeyboardButton("📮 UPDATES 📮", url=Config.UPDATE_CHANNEL)]
            ])
        )

    # ──────────────────────────────────────────────────────────────────────
    #  /settings
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("settings") & filters.private)
    async def settings_cmd(client: Client, message: Message):
        user_id = message.from_user.id
        bot_username = await get_bot_username()

        notif = await db.get_clone_notif(bot_username, user_id)
        await message.reply_text(
            text=f"⚙ `Here You Can Set Your Settings:` ⚙\n\nNotifications: **{notif}**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    f"NOTIFICATION  {'🔔' if notif else '🔕'}",
                    callback_data="notifon"
                )],
                [InlineKeyboardButton("CLOSE", callback_data="closeMeh")],
            ])
        )

    # ──────────────────────────────────────────────────────────────────────
    #  /stats  (sudo only)
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("stats") & filters.private)
    async def stats_cmd(client: Client, message: Message):
        if not is_sudo(message.from_user.id):
            await message.delete()
            return
        bot_username = await get_bot_username()
        total = await db.total_clone_users_count(bot_username)
        await message.reply_text(
            f"**📊 Stats for @{bot_username}**\n\n"
            f"**Total Users in Database 📂:** `{total}`"
        )

    # ──────────────────────────────────────────────────────────────────────
    #  /ban_user  (sudo only)
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("ban_user") & filters.private)
    async def ban_cmd(client: Client, message: Message):
        if not is_sudo(message.from_user.id):
            await message.delete()
            return
        if len(message.command) < 4:
            await message.reply_text(
                "Usage: `/ban_user user_id ban_duration ban_reason`\n"
                "Eg: `/ban_user 123456 7 Spam`"
            )
            return
        try:
            bot_username = await get_bot_username()
            target_id = int(message.command[1])
            ban_dur = int(message.command[2])
            ban_reason = " ".join(message.command[3:])
            await db.ban_clone_user(bot_username, target_id, ban_dur, ban_reason)
            try:
                await client.send_message(
                    target_id,
                    f"You are Banned 🚫 for **{ban_dur}** day(s). Reason: __{ban_reason}__"
                )
            except Exception:
                pass
            await message.reply_text(f"✅ Banned user `{target_id}` for {ban_dur} days.")
        except Exception:
            await message.reply_text(f"Error:\n`{traceback.format_exc()}`")

    # ──────────────────────────────────────────────────────────────────────
    #  /unban_user  (sudo only)
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("unban_user") & filters.private)
    async def unban_cmd(client: Client, message: Message):
        if not is_sudo(message.from_user.id):
            await message.delete()
            return
        if len(message.command) < 2:
            await message.reply_text("Usage: `/unban_user user_id`")
            return
        try:
            bot_username = await get_bot_username()
            target_id = int(message.command[1])
            await db.unban_clone_user(bot_username, target_id)
            try:
                await client.send_message(target_id, "Your ban has been lifted! ✅")
            except Exception:
                pass
            await message.reply_text(f"✅ Unbanned user `{target_id}`.")
        except Exception:
            await message.reply_text(f"Error:\n`{traceback.format_exc()}`")

    # ──────────────────────────────────────────────────────────────────────
    #  /broadcast  (sudo only)
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.command("broadcast") & filters.private)
    async def broadcast_cmd(client: Client, message: Message):
        if not is_sudo(message.from_user.id):
            await message.delete()
            return
        if message.reply_to_message is None:
            await message.reply_text("Reply to a message to broadcast it.")
            return

        bot_username = await get_bot_username()
        users_cursor = await db.get_clone_notif_users(bot_username)
        bcast_msg = message.reply_to_message
        total = 0
        success = 0
        failed = 0

        status_msg = await message.reply_text("📢 Broadcasting...")

        async for user in users_cursor:
            user_id = user["id"]
            try:
                if Config.BROADCAST_AS_COPY:
                    await bcast_msg.copy(chat_id=user_id)
                else:
                    await bcast_msg.forward(chat_id=user_id)
                success += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except (UserIsBlocked, InputUserDeactivated, PeerIdInvalid):
                await db.delete_clone_user(bot_username, user_id)
                failed += 1
            except Exception:
                failed += 1
            total += 1

        await status_msg.edit(
            f"✅ Broadcast done!\n\nTotal: `{total}` | Success: `{success}` | Failed: `{failed}`"
        )

    # ──────────────────────────────────────────────────────────────────────
    #  OWNER reply to user (text)  - sudo sends text replying to forwarded msg
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.user([clone_owner_id, MAIN_SUDO]) & filters.text & filters.private)
    async def owner_reply_text(client: Client, message: Message):
        bot_username = await get_bot_username()
        user_id = message.from_user.id

        if not await db.is_clone_user_exist(bot_username, user_id):
            await db.add_clone_user(bot_username, user_id)

        if message.reply_to_message is not None:
            file = message.reply_to_message
            reference_id = None
            try:
                reference_id = int(file.text.split()[2])
            except Exception:
                pass
            try:
                reference_id = int(file.caption.split()[2])
            except Exception:
                pass

            if reference_id:
                try:
                    await client.send_message(chat_id=reference_id, text=message.text)
                except Exception as e:
                    await message.reply_text(f"Could not send: {e}")

    # ──────────────────────────────────────────────────────────────────────
    #  OWNER reply to user (media)
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.user([clone_owner_id, MAIN_SUDO]) & filters.media & filters.private)
    async def owner_reply_media(client: Client, message: Message):
        bot_username = await get_bot_username()
        user_id = message.from_user.id

        if not await db.is_clone_user_exist(bot_username, user_id):
            await db.add_clone_user(bot_username, user_id)

        if message.reply_to_message is not None:
            file = message.reply_to_message
            reference_id = None
            try:
                reference_id = int(file.text.split()[2])
            except Exception:
                pass
            try:
                reference_id = int(file.caption.split()[2])
            except Exception:
                pass

            if reference_id:
                try:
                    await client.copy_message(
                        chat_id=reference_id,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id,
                        caption=message.caption,
                    )
                except Exception as e:
                    await message.reply_text(f"Could not send: {e}")

    # ──────────────────────────────────────────────────────────────────────
    #  USER sends TEXT  →  forward to clone owner (and main sudo if different)
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.private & filters.text)
    async def user_text(client: Client, message: Message):
        user_id = message.from_user.id

        # Skip if it's the clone owner or main sudo
        if is_sudo(user_id):
            return

        bot_username = await get_bot_username()

        if not await db.is_clone_user_exist(bot_username, user_id):
            await db.add_clone_user(bot_username, user_id)

        ban_status = await db.get_clone_ban_status(bot_username, user_id)
        if ban_status["is_banned"]:
            await message.reply_text(
                f"You are Banned 🚫 for **{ban_status['ban_duration']}** day(s). "
                f"Reason: __{ban_status['ban_reason']}__"
            )
            return

        info = await client.get_users(user_ids=user_id)
        forward_text = IF_TEXT.format(user_id, info.first_name, message.text)

        # Send to clone owner
        await client.send_message(chat_id=clone_owner_id, text=forward_text)

        # Also notify main sudo if different
        if MAIN_SUDO != clone_owner_id:
            try:
                await client.send_message(
                    chat_id=MAIN_SUDO,
                    text=f"[Clone @{bot_username}]\n" + forward_text
                )
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────────────────
    #  USER sends MEDIA
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.private & filters.media)
    async def user_media(client: Client, message: Message):
        user_id = message.from_user.id

        if is_sudo(user_id):
            return

        bot_username = await get_bot_username()

        if not await db.is_clone_user_exist(bot_username, user_id):
            await db.add_clone_user(bot_username, user_id)

        ban_status = await db.get_clone_ban_status(bot_username, user_id)
        if ban_status["is_banned"]:
            await message.reply_text(
                f"You are Banned 🚫 for **{ban_status['ban_duration']}** day(s). "
                f"Reason: __{ban_status['ban_reason']}__"
            )
            return

        if message.media_group_id:
            return

        info = await client.get_users(user_ids=user_id)
        caption = IF_CONTENT.format(user_id, info.first_name)

        await client.copy_message(
            chat_id=clone_owner_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            caption=caption,
        )

    # ──────────────────────────────────────────────────────────────────────
    #  USER sends MEDIA GROUP
    # ──────────────────────────────────────────────────────────────────────

    @app.on_message(filters.private & filters.media_group)
    async def user_media_group(client: Client, message: Message):
        user_id = message.from_user.id

        if is_sudo(user_id):
            return

        bot_username = await get_bot_username()

        ban_status = await db.get_clone_ban_status(bot_username, user_id)
        if ban_status["is_banned"]:
            return

        await client.copy_media_group(
            chat_id=clone_owner_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )

    # ──────────────────────────────────────────────────────────────────────
    #  START the clone bot
    # ──────────────────────────────────────────────────────────────────────
    try:
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ Clone bot @{me.username} started for owner {clone_owner_id}")
        return app
    except Exception as e:
        logger.error(f"❌ Failed to start clone bot for owner {clone_owner_id}: {e}")
        raise
