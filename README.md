# 🤖 Feedback Bot with Clone System

Original bot jaise hi kaam karta hai + **Clone System** added!

## 🌟 Clone System kya hai?

Livegram bot ki tarah — koi bhi user apna **BotFather token** de ke ek clone feedback bot bana sakta hai.

- Clone ka **Owner** = jisne `/clone` kiya (uska apna inbox)
- **Main Sudo** (OWNER_ID) = sabhi clone bots ka bhi sudo access
- Clone bot exactly original jaise kaam karta hai

---

## 📋 Commands

### All Users:
| Command | Description |
|---------|-------------|
| `/start` | Bot start karo |
| `/help` | Help message |
| `/settings` | Notification settings |
| `/clone` | Apna clone bot banao |
| `/myclone` | Apne clone ki details dekho |
| `/removeclone` | Clone bot remove karo |

### Sudo (Owner + AUTH_USERS):
| Command | Description |
|---------|-------------|
| `/stats` | Total users + clone count |
| `/broadcast` | Broadcast message |
| `/ban_user` | User ban karo |
| `/unban_user` | User unban karo |
| `/banned_users` | All banned users |

### Main Owner Only:
| Command | Description |
|---------|-------------|
| `/clonelist` | Sabhi clone bots ki list |
| `/stopclone @username` | Kisi bhi clone ko force stop karo |

---

## 🚀 Clone System Flow

```
User: /clone
Bot: "Send BotFather token"
User: 123456:ABCDEF...
Bot: ✅ Clone @YourBot started!
```

Clone bot automatically:
- Same feedback forwarding system
- Clone owner ko messages forward hote hain
- Main SUDO bhi clone bots mein reply kar sakta hai
- Ban/unban/broadcast sab work karta hai
- Bot restart pe automatically restore hota hai

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | ✅ | my.telegram.org se |
| `API_HASH` | ✅ | my.telegram.org se |
| `BOT_TOKEN` | ✅ | @BotFather se main bot token |
| `OWNER_ID` | ✅ | Tera Telegram User ID (SUDO of all) |
| `DB_URL` | ✅ | MongoDB connection URL |
| `DB_NAME` | ❌ | Default: `feedback_bot` |
| `LOG_CHANNEL` | ✅ | Log channel/group ID |
| `AUTH_USERS` | ❌ | Extra sudo users (space separated) |
| `START_TEXT` | ❌ | Custom start message |
| `HELP_TEXT` | ❌ | Custom help message |

---

## 🗄️ Database Structure

MongoDB mein teen tarah ke collections:
- `users` — main bot ke users
- `clone_bots` — registered clone bots
- `clone_{username}_users` — har clone ka apna user collection

---

## 📦 Deploy on Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

1. Heroku pe deploy karo
2. Env vars set karo
3. Worker dyno start karo
4. `/clone` command se clone bots banao!
