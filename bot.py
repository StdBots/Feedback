# Copyright (c) 2021 HEIMAN PICTURES
# Clone System Added

import os
import asyncio
import traceback
import logging

from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
)

from configs import Config as C
from database.broadcast import broadcast
from database.verifier import handle_user_status
from database.database import Database
from clone_bot import run_clone_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
LOG_CHANNEL = C.LOG_CHANNEL
AUTH_USERS = C.AUTH_USERS
AUTH_USERS.add(C.OWNER_ID)   # Main owner always in AUTH_USERS
DB_URL = C.DB_URL
DB_NAME = C.DB_NAME

db = Database(DB_URL, DB_NAME)

# ─── Main Bot ─────────────────────────────────────────────────────────────────
bot = Client(
    "Feedback bot",
    api_id=C.API_ID,
    api_hash=C.API_HASH,
    bot_token=C.BOT_TOKEN,
)

donate_link = C.DONATE_LINK
owner_id = C.OWNER_ID

# Running clone bots  {bot_token: pyrogram Client}
running_clones: dict[str, Client] = {}

IF_TEXT = "<b>Message from:</b> {}\n<b>Name:</b> {}\n\n{}"
IF_CONTENT = "<b>Message from:</b> {}\n<b>Name:</b> {}"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def is_sudo(user_id: int) -> bool:
    return user_id == owner_id or user_id in AUTH_USERS


async def ensure_user(bot_client, message, chat_id=None):
    """Add user to DB if not exists and log in LOG_CHANNEL."""
    cid = chat_id or message.from_user.id
    if not await db.is_user_exist(cid):
        data = await bot_client.get_me()
        await db.add_user(cid)
        await bot_client.send_message(
            LOG_CHANNEL,
            f"#NEWUSER: \n\nNew User [{message.from_user.first_name}](tg://user?id={cid}) started @{data.username} !!",
        )


async def check_ban(message, chat_id=None):
    """Return True (and reply) if user is banned."""
    cid = chat_id or message.from_user.id
    ban_status = await db.get_ban_status(cid)
    if ban_status["is_banned"]:
        await message.reply_text(
            f"You are Banned 🚫 to use this bot for **{ban_status['ban_duration']}** day(s) "
            f"for the reason __{ban_status['ban_reason']}__ \n\n**Message from the admin 🤠**"
        )
        return True
    return False

# ─────────────────────────────────────────────────────────────────────────────
#  CALLBACK HANDLER
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_callback_query()
async def callback_handlers(client: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    if "closeMeh" in cb.data:
        await cb.message.delete(True)
    elif "notifon" in cb.data:
        notif = await db.get_notif(user_id)
        new_notif = not notif
        await db.set_notif(user_id, notif=new_notif)
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


# ─────────────────────────────────────────────────────────────────────────────
#  USER STATUS CHECK (group + private)
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message((filters.private | filters.group))
async def _(client, cmd):
    await handle_user_status(client, cmd)


# ─────────────────────────────────────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("start") & (filters.private | filters.group))
async def start(client: Client, message: Message):
    chat_id = message.from_user.id
    await ensure_user(client, message, chat_id)
    if await check_ban(message, chat_id):
        return
    await message.reply_text(
        text=f"**Hi {message.chat.first_name}!**\n{C.START}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠SUPPORT🛠", url=C.SUPPORT_GROUP),
             InlineKeyboardButton("📮UPDATES📮", url=C.UPDATE_CHANNEL)]
        ])
    )


# ─────────────────────────────────────────────────────────────────────────────
#  /help
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("help") & (filters.group | filters.private))
async def help_cmd(client: Client, message: Message):
    chat_id = message.from_user.id
    await ensure_user(client, message, chat_id)
    if await check_ban(message, chat_id):
        return
    await message.reply_text(
        text=C.HELP,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠SUPPORT🛠", url=C.SUPPORT_GROUP),
             InlineKeyboardButton("📮UPDATES📮", url=C.UPDATE_CHANNEL)]
        ])
    )


# ─────────────────────────────────────────────────────────────────────────────
#  /donate
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("donate") & (filters.group | filters.private))
async def donate(client: Client, message: Message):
    chat_id = message.from_user.id
    await ensure_user(client, message, chat_id)
    if await check_ban(message, chat_id):
        return
    await message.reply_text(
        text=C.DONATE + "\nIf you liked this bot, you can donate via BTC `3AKE4bNwb9TsgaofLQxHAGCR9w2ftwFs2R`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("DONATE", url=donate_link)]
        ])
    )


# ─────────────────────────────────────────────────────────────────────────────
#  /settings
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.command("settings") & filters.private)
async def opensettings(client: Client, cmd: Message):
    user_id = cmd.from_user.id
    await ensure_user(client, cmd, user_id)
    notif = await db.get_notif(user_id)
    await cmd.reply_text(
        text=f"⚙ `Here You Can Set Your Settings:` ⚙\n\nNotifications: **{notif}**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"NOTIFICATION  {'🔔' if notif else '🔕'}",
                callback_data="notifon"
            )],
            [InlineKeyboardButton("CLOSE", callback_data="closeMeh")],
        ])
    )


# ─────────────────────────────────────────────────────────────────────────────
#  /broadcast  (AUTH_USERS only)
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.private & filters.command("broadcast"))
async def broadcast_handler_open(client: Client, m: Message):
    if not is_sudo(m.from_user.id):
        await m.delete()
        return
    if m.reply_to_message is None:
        await m.delete()
        return
    await broadcast(m, db)


# ─────────────────────────────────────────────────────────────────────────────
#  /stats  (AUTH_USERS only)
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message((filters.group | filters.private) & filters.command("stats"))
async def sts(client: Client, m: Message):
    if not is_sudo(m.from_user.id):
        await m.delete()
        return
    total_clones = await db.total_clones_count()
    await m.reply_text(
        text=(
            f"**Total Users in Database 📂:** `{await db.total_users_count()}`\n\n"
            f"**Total Users with Notification Enabled 🔔:** `{await db.total_notif_users_count()}`\n\n"
            f"**Total Clone Bots Running 🤖:** `{total_clones}`"
        ),
        quote=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  /ban_user  (AUTH_USERS only)
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.private & filters.command("ban_user"))
async def ban(client: Client, m: Message):
    if not is_sudo(m.from_user.id):
        await m.delete()
        return
    if len(m.command) == 1:
        await m.reply_text(
            "Usage:\n\n`/ban_user user_id ban_duration ban_reason`\n\n"
            "Eg: `/ban_user 1234567 28 You misused me.`",
            quote=True,
        )
        return
    try:
        user_id = int(m.command[1])
        ban_duration = int(m.command[2])
        ban_reason = " ".join(m.command[3:])
        if user_id == owner_id:
            await m.reply_text("**You can't ban the Owner!**")
            return
        try:
            await client.send_message(
                user_id,
                f"You are Banned 🚫 for **{ban_duration}** day(s). Reason: __{ban_reason}__"
            )
        except Exception:
            pass
        await db.ban_user(user_id, ban_duration, ban_reason)
        await m.reply_text(f"✅ Banned `{user_id}` for {ban_duration} days.", quote=True)
    except Exception:
        await m.reply_text(f"Error:\n`{traceback.format_exc()}`", quote=True)


# ─────────────────────────────────────────────────────────────────────────────
#  /unban_user  (AUTH_USERS only)
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message((filters.group | filters.private) & filters.command("unban_user"))
async def unban(client: Client, m: Message):
    if not is_sudo(m.from_user.id):
        await m.delete()
        return
    if len(m.command) == 1:
        await m.reply_text("Usage: `/unban_user user_id`", quote=True)
        return
    try:
        user_id = int(m.command[1])
        await db.remove_ban(user_id)
        try:
            await client.send_message(user_id, "Your ban has been lifted! ✅")
        except Exception:
            pass
        await m.reply_text(f"✅ Unbanned `{user_id}`.", quote=True)
    except Exception:
        await m.reply_text(f"Error:\n`{traceback.format_exc()}`", quote=True)


# ─────────────────────────────────────────────────────────────────────────────
#  /banned_users  (AUTH_USERS only)
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message((filters.group | filters.private) & filters.command("banned_users"))
async def _banned_usrs(client: Client, m: Message):
    if not is_sudo(m.from_user.id):
        await m.delete()
        return
    all_banned_users = await db.get_all_banned_users()
    banned_usr_count = 0
    text = ""
    async for banned_user in all_banned_users:
        user_id = banned_user["id"]
        ban_duration = banned_user["ban_status"]["ban_duration"]
        banned_on = banned_user["ban_status"]["banned_on"]
        ban_reason = banned_user["ban_status"]["ban_reason"]
        banned_usr_count += 1
        text += f"> **User_id**: `{user_id}`, **Ban Duration**: `{ban_duration}`, **Banned on**: `{banned_on}`, **Reason**: `{ban_reason}`\n\n"
    reply_text = f"Total banned user(s) 🤭: `{banned_usr_count}`\n\n{text}"
    if len(reply_text) > 4096:
        with open("banned-users.txt", "w") as f:
            f.write(reply_text)
        await m.reply_document("banned-users.txt", True)
        os.remove("banned-users.txt")
        return
    await m.reply_text(reply_text, True)


# ═════════════════════════════════════════════════════════════════════════════
#  🤖  CLONE SYSTEM
# ═════════════════════════════════════════════════════════════════════════════

@bot.on_message(filters.command("clone") & filters.private)
async def clone_cmd(client: Client, message: Message):
    """
    Step 1: User sends /clone
    Step 2: Bot asks for BotFather token
    Step 3: User sends token
    Step 4: Bot starts clone and registers it
    """
    user_id = message.from_user.id

    # Check if user already has a clone
    existing = await db.get_clone_by_owner(user_id)
    if existing:
        await message.reply_text(
            f"⚠️ You already have a clone bot: **@{existing['bot_username']}**\n\n"
            f"Use /myclone to see details or /removeclone to remove it first."
        )
        return

    await message.reply_text(
        "🤖 **Clone Bot Setup**\n\n"
        "Please send me your **BotFather token** for the bot you want to clone.\n\n"
        "Steps:\n"
        "1. Go to @BotFather\n"
        "2. Create a new bot or use existing\n"
        "3. Copy the token\n"
        "4. Send it here\n\n"
        "⏳ Waiting for your token... (60 seconds)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("@BotFather", url="https://t.me/BotFather")]
        ])
    )

    # Wait for next message from this user (token)
    try:
        token_msg: Message = await client.listen(
            chat_id=user_id,
            filters=filters.text,
            timeout=60
        )
    except asyncio.TimeoutError:
        await message.reply_text("⌛ Timeout! Please run /clone again.")
        return

    bot_token = token_msg.text.strip()

    # Basic token format check
    if ":" not in bot_token or len(bot_token) < 30:
        await token_msg.reply_text("❌ Invalid token format! Please try /clone again.")
        return

    # Check if token already in use
    existing_token = await db.get_clone_by_token(bot_token)
    if existing_token:
        await token_msg.reply_text(
            "❌ This token is already being used by another clone! Use a different bot token."
        )
        return

    status_msg = await token_msg.reply_text("⏳ Starting your clone bot... Please wait.")

    try:
        # Start the clone bot
        clone_client = await run_clone_bot(bot_token, user_id, db)
        me = await clone_client.get_me()
        bot_username = me.username

        # Save to DB
        await db.add_clone(user_id, bot_token, bot_username)

        # Store in running_clones dict
        running_clones[bot_token] = clone_client

        await status_msg.edit(
            f"✅ **Clone Bot Started Successfully!**\n\n"
            f"🤖 Bot: @{bot_username}\n"
            f"👤 Owner: You (ID: `{user_id}`)\n"
            f"🔑 Main Sudo: `{owner_id}` also has access\n\n"
            f"Your clone bot is now live and works exactly like this bot!\n\n"
            f"**Available commands for your clone:**\n"
            f"/stats - See user stats\n"
            f"/ban_user - Ban a user\n"
            f"/unban_user - Unban a user\n"
            f"/broadcast - Broadcast a message\n"
            f"/settings - User settings\n\n"
            f"Use /myclone to manage it anytime."
        )

        # Notify main owner
        if user_id != owner_id:
            try:
                await client.send_message(
                    owner_id,
                    f"#NEWCLONE\n\nUser [{message.from_user.first_name}](tg://user?id={user_id}) "
                    f"created a clone bot @{bot_username}!"
                )
            except Exception:
                pass

    except Exception as e:
        await status_msg.edit(
            f"❌ **Failed to start clone bot!**\n\n"
            f"Error: `{str(e)}`\n\n"
            f"Please make sure:\n"
            f"• The token is correct\n"
            f"• The bot is not already running somewhere else\n"
            f"• The bot was created by @BotFather"
        )


@bot.on_message(filters.command("myclone") & filters.private)
async def my_clone_cmd(client: Client, message: Message):
    """Show user's clone bot details."""
    user_id = message.from_user.id
    clone = await db.get_clone_by_owner(user_id)

    if not clone:
        await message.reply_text(
            "You don't have a clone bot yet.\n\nUse /clone to create one!"
        )
        return

    bot_username = clone["bot_username"]
    is_running = clone["bot_token"] in running_clones
    user_count = await db.total_clone_users_count(bot_username)

    await message.reply_text(
        f"🤖 **Your Clone Bot**\n\n"
        f"Username: @{bot_username}\n"
        f"Status: {'🟢 Running' if is_running else '🔴 Stopped'}\n"
        f"Total Users: `{user_count}`\n"
        f"Created: `{clone.get('created_at', 'Unknown')}`\n\n"
        f"Use /removeclone to delete this clone.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Open @{bot_username}", url=f"https://t.me/{bot_username}")]
        ])
    )


@bot.on_message(filters.command("removeclone") & filters.private)
async def remove_clone_cmd(client: Client, message: Message):
    """Remove (stop and delete) user's clone bot."""
    user_id = message.from_user.id
    clone = await db.get_clone_by_owner(user_id)

    if not clone:
        await message.reply_text("You don't have a clone bot to remove.")
        return

    bot_token = clone["bot_token"]
    bot_username = clone["bot_username"]

    # Stop the running clone if it's active
    if bot_token in running_clones:
        try:
            await running_clones[bot_token].stop()
        except Exception:
            pass
        del running_clones[bot_token]

    # Remove from DB
    await db.remove_clone(bot_token)

    await message.reply_text(
        f"✅ Clone bot @{bot_username} has been stopped and removed.\n\n"
        f"Use /clone to create a new one anytime."
    )


@bot.on_message(filters.command("clonelist") & filters.private)
async def clone_list_cmd(client: Client, message: Message):
    """Main sudo only - list all clone bots."""
    if not is_sudo(message.from_user.id):
        await message.delete()
        return

    all_clones = await db.get_all_clones()
    text = "🤖 **All Active Clone Bots**\n\n"
    count = 0

    async for clone in all_clones:
        count += 1
        is_running = clone["bot_token"] in running_clones
        text += (
            f"{count}. @{clone['bot_username']}\n"
            f"   Owner: `{clone['owner_id']}`\n"
            f"   Status: {'🟢 Running' if is_running else '🔴 Stopped'}\n"
            f"   Created: {clone.get('created_at', 'Unknown')[:10]}\n\n"
        )

    if count == 0:
        text = "No clone bots found."

    await message.reply_text(text)


@bot.on_message(filters.command("stopclone") & filters.private)
async def stop_clone_admin_cmd(client: Client, message: Message):
    """Main sudo only - forcefully stop any clone bot."""
    if message.from_user.id != owner_id:
        await message.delete()
        return

    if len(message.command) < 2:
        await message.reply_text("Usage: `/stopclone @username_or_owner_id`")
        return

    query = message.command[1].replace("@", "")

    # Try to find by username or owner_id
    all_clones = await db.get_all_clones()
    found = None
    async for clone in all_clones:
        if clone["bot_username"].lower() == query.lower():
            found = clone
            break
        try:
            if clone["owner_id"] == int(query):
                found = clone
                break
        except ValueError:
            pass

    if not found:
        await message.reply_text(f"❌ No clone found for `{query}`")
        return

    bot_token = found["bot_token"]
    bot_username = found["bot_username"]

    if bot_token in running_clones:
        try:
            await running_clones[bot_token].stop()
        except Exception:
            pass
        del running_clones[bot_token]

    await db.remove_clone(bot_token)
    await message.reply_text(f"✅ Clone @{bot_username} stopped and removed by SUDO.")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN BOT: PM text handler
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message((filters.group | filters.private) & filters.text)
async def pm_text(client: Client, message: Message):
    chat_id = message.from_user.id
    await ensure_user(client, message, chat_id)
    if await check_ban(message, chat_id):
        return
    if message.from_user.id == owner_id:
        await reply_text(client, message)
        return
    info = await client.get_users(user_ids=message.from_user.id)
    await client.send_message(
        chat_id=owner_id,
        text=IF_TEXT.format(chat_id, info.first_name, message.text),
    )


@bot.on_message((filters.group | filters.private) & filters.media_group)
async def pm_media_group(client: Client, message: Message):
    chat_id = message.from_user.id
    await ensure_user(client, message, chat_id)
    if await check_ban(message, chat_id):
        return
    if message.from_user.id == owner_id:
        await replay_media(client, message)
        return
    await client.copy_media_group(
        chat_id=owner_id,
        from_chat_id=chat_id,
        message_id=message.message_id
    )


@bot.on_message((filters.group | filters.private) & filters.media)
async def pm_media(client: Client, message: Message):
    chat_id = message.from_user.id
    await ensure_user(client, message, chat_id)
    if await check_ban(message, chat_id):
        return
    if message.from_user.id == owner_id:
        await replay_media(client, message)
        return
    info = await client.get_users(user_ids=message.from_user.id)
    if message.media_group_id is not None:
        return
    await client.copy_message(
        chat_id=owner_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        caption=IF_CONTENT.format(chat_id, info.first_name),
    )


# ─────────────────────────────────────────────────────────────────────────────
#  OWNER REPLY handlers
# ─────────────────────────────────────────────────────────────────────────────

@bot.on_message(filters.user(owner_id) & filters.text)
async def reply_text(client: Client, message: Message):
    await ensure_user(client, message)
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
            await client.send_message(chat_id=reference_id, text=message.text)


@bot.on_message(filters.user(owner_id) & filters.media)
async def replay_media(client: Client, message: Message):
    await ensure_user(client, message)
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
            await client.copy_message(
                chat_id=reference_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                caption=message.caption,
            )


# ═════════════════════════════════════════════════════════════════════════════
#  STARTUP: restore all saved clone bots from DB
# ═════════════════════════════════════════════════════════════════════════════

async def restore_clones():
    """On bot startup, restart all saved clone bots."""
    logger.info("🔄 Restoring clone bots from database...")
    all_clones = await db.get_all_clones()
    count = 0
    async for clone in all_clones:
        bot_token = clone["bot_token"]
        clone_owner_id = clone["owner_id"]
        try:
            clone_client = await run_clone_bot(bot_token, clone_owner_id, db)
            running_clones[bot_token] = clone_client
            count += 1
            logger.info(f"✅ Restored clone @{clone['bot_username']}")
        except Exception as e:
            logger.error(f"❌ Could not restore clone @{clone.get('bot_username')}: {e}")
    logger.info(f"🤖 {count} clone bot(s) restored.")


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    await bot.start()
    logger.info("---------- ** Main Bot Started ** ----------")
    await restore_clones()
    await bot.idle()


if __name__ == "__main__":
    asyncio.run(main())
