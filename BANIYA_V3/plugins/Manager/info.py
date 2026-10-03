# Authored By Certified Coders © 2025
import asyncio
from pyrogram import filters, enums
from pyrogram.errors import PeerIdInvalid, RPCError, FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from BANIYA_V3 import app


def get_full_name(user):
    return f"{user.first_name} {user.last_name}" if user.last_name else user.first_name


def get_last_seen(status):
    if isinstance(status, str):
        status = status.replace("UserStatus.", "").lower()
    elif isinstance(status, enums.UserStatus):
        status = status.name.lower()

    return {
        "online": "<emoji id='6127296324107769784'>✅</emoji> Online",
        "offline": "<emoji id='6032606743500951856'>❌</emoji> Offline",
        "recently": "<emoji id='5426856766665154421'>🚬</emoji> Recently",
        "last_week": "<emoji id='5769547529993588669'>👑</emoji> Last week",
        "last_month": "<emoji id='6127296324107769784'>✅</emoji> Last month",
        "long_ago": "<emoji id='6127296324107769784'>✅</emoji> Long ago"
    }.get(status, "<emoji id='6127296324107769784'>✅</emoji> Unknown")


@app.on_message(filters.command(["info", "userinfo", "whois"]))
async def whois_handler(_, message: Message):
    try:
        if message.reply_to_message:
            user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            user = await app.get_users(message.command[1])
        else:
            user = message.from_user

        loading = await message.reply(
            "<emoji id='6127296324107769784'>✅</emoji> <b>Fetching user info...</b>"
        )
        await asyncio.sleep(0.5)

        chat_user = await app.get_chat(user.id)

        name = get_full_name(user)
        username = f"@{user.username}" if user.username else "N/A"
        bio = chat_user.bio or "N/A"
        dc_id = getattr(user, "dc_id", "N/A")
        last_seen = get_last_seen(user.status)
        lang = getattr(user, "language_code", "N/A")

        # Premium emoji
        EMOJI = "<emoji id='6127296324107769784'>✅</emoji>"
        PROFILE = "<emoji id='6127296324107769784'>✅</emoji>"

        text = (
            f"{EMOJI} <b>User Info</b>\n"
            f"────────────────\n"
            f"{EMOJI} <b>User ID:</b> <code>{user.id}</code>\n"
            f"{EMOJI} <b>Name:</b> {name}\n"
            f"{EMOJI} <b>Username:</b> {username}\n"
            f"{EMOJI} <b>Last seen:</b> {last_seen}\n"
            f"{EMOJI} <b>DataCenter ID:</b> {dc_id}\n"
            f"{EMOJI} <b>Language:</b> {lang}\n"
            f"────────────────\n"
            f"{EMOJI} <b>Verified:</b> {EMOJI if user.is_verified else EMOJI}\n"
            f"{EMOJI} <b>Premium:</b> {EMOJI if user.is_premium else EMOJI}\n"
            f"{EMOJI} <b>Bot:</b> {EMOJI if user.is_bot else EMOJI}\n"
            f"{EMOJI} <b>Scam:</b> {EMOJI if getattr(user, 'is_scam', False) else EMOJI}\n"
            f"{EMOJI} <b>Fake:</b> {EMOJI if getattr(user, 'is_fake', False) else EMOJI}\n"
            f"{EMOJI} <b>Profile Photo:</b> {EMOJI if user.photo else EMOJI}\n"
            f"────────────────\n"
            f"{EMOJI} <b>Bio:</b> <code>{bio}</code>"
        )

        profile_url = (
            f"https://t.me/{user.username}"
            if user.username
            else f"tg://user?id={user.id}"
        )

        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                f"{EMOJI} View Profile",
                url=profile_url,
            ),
            InlineKeyboardButton(
                f"{EMOJI} Share",
                url="tg://settings",
            )
        ]])

        await app.edit_message_text(
            chat_id=message.chat.id,
            message_id=loading.id,
            text=text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )

    except PeerIdInvalid:
        await message.reply("❌ I couldn't find that user.")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await whois_handler(_, message)
    except RPCError as e:
        await message.reply(f"⚠️ RPC error:\n<code>{e}</code>")
    except Exception as e:
        await message.reply(f"❌ Error:\n<code>{e}</code>")
