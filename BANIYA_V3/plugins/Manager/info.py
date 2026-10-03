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
        "online": "🟢 Online",
        "offline": "🔴 Offline",
        "recently": "⏱️ Recently",
        "last_week": "📅 Last week",
        "last_month": "📆 Last month",
        "long_ago": "😴 Long ago"
    }.get(status, "❓ Unknown")


@app.on_message(filters.command(["info", "userinfo", "whois"]))
async def whois_handler(_, message: Message):
    try:
        if message.reply_to_message:
            user = message.reply_to_message.from_user
        elif len(message.command) > 1:
            user = await app.get_users(message.command[1])
        else:
            user = message.from_user

        loading = await message.reply("🔍 <b>Fetching user info...</b>")
        await asyncio.sleep(0.5)

        chat_user = await app.get_chat(user.id)

        name = get_full_name(user)
        username = f"@{user.username}" if user.username else "N/A"
        bio = chat_user.bio or "N/A"
        dc_id = getattr(user, "dc_id", "N/A")
        last_seen = get_last_seen(user.status)
        lang = getattr(user, "language_code", "N/A")

        text = (
            f"👤 <b>User Info</b>\n"
            f"────────────────\n"
            f"➣ <b>User ID:</b> <code>{user.id}</code>\n"
            f"➣ <b>Name:</b> {name}\n"
            f"➣ <b>Username:</b> {username}\n"
            f"➣ <b>Last seen:</b> {last_seen}\n"
            f"➣ <b>DataCenter ID:</b> {dc_id}\n"
            f"➣ <b>Language:</b> {lang}\n"
            f"────────────────\n"
            f"➣ <b>Verified:</b> {'Yes ✅' if user.is_verified else 'No ❌'}\n"
            f"➣ <b>Premium:</b> {'Yes 💎' if user.is_premium else 'No ❌'}\n"
            f"➣ <b>Bot:</b> {'Yes 🤖' if user.is_bot else 'No 👤'}\n"
            f"➣ <b>Scam:</b> {'Yes ⚠️' if getattr(user, 'is_scam', False) else 'No ✅'}\n"
            f"➣ <b>Fake:</b> {'Yes 🎭' if getattr(user, 'is_fake', False) else 'No ✅'}\n"
            f"➣ <b>Profile Photo:</b> {'Yes 🌸' if user.photo else 'No ❌'}\n"
            f"────────────────\n"
            f"➣ <b>Bio:</b> <code>{bio}</code>"
        )

        profile_url = (
            f"https://t.me/{user.username}"
            if user.username
            else f"tg://user?id={user.id}"
        )
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("👤 View Profile", url=profile_url),
            InlineKeyboardButton("📞 Share", url="tg://settings")
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
