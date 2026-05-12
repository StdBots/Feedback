import os

class Config(object):

    API_ID = int(os.environ.get("API_ID", 12345))

    API_HASH = str(os.environ.get("API_HASH", ""))

    BOT_TOKEN = str(os.environ.get("BOT_TOKEN", ""))

    # Main Owner - SUDO of everything (original bot ka owner)
    OWNER_ID = int(os.environ.get("OWNER_ID", 1428968542))

    # AUTH_USERS includes OWNER_ID automatically
    AUTH_USERS = set(int(x) for x in os.environ.get("AUTH_USERS", "").split())

    START = str(os.environ.get("START_TEXT", "I am a Feedback Bot! Send me a message and the owner will reply."))

    HELP = str(os.environ.get("HELP_TEXT", "Send any message and the owner will receive it directly."))

    DONATE = str(os.environ.get("DONATE_TEXT", ""))

    DONATE_LINK = str(os.environ.get("DONATE_LINK", ""))

    UPDATE_CHANNEL = str(os.environ.get("UPDATE_CHANNEL", "https://t.me/HeimanSupports"))

    SUPPORT_GROUP = str(os.environ.get("SUPPORT_GROUP", "https://t.me/HeimanSupport"))

    DB_URL = str(os.environ.get("DB_URL", ""))

    DB_NAME = str(os.environ.get("DB_NAME", "feedback_bot"))

    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0))

    BROADCAST_AS_COPY = bool(os.environ.get("BROADCAST_AS_COPY", False))
