# BANIYA_V3/plugins/Manager/_utils.py

import datetime as dt
from typing import Optional
from functools import wraps
from pyrogram import filters, enums
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, CallbackQuery
from BANIYA_V3 import app, config


def mention(user_id: int, name: str) -> str:
    return f"[{name}](tg://user?id={user_id})"


def parse_time(time_arg: str) -> Optional[dt.timedelta]:
    if not time_arg:
        return None
    unit = time_arg[-1].lower()
    try:
        num = int(time_arg[:-1])
    except ValueError:
        return None
    return {
        "s": dt.timedelta(seconds=num),
        "m": dt.timedelta(minutes=num),
        "h": dt.timedelta(hours=num),
        "d": dt.timedelta(days=num),
    }.get(unit)


async def _admin_filter_func(_, __, message: Message) -> bool:
    try:
        member = await message._client.get_chat_member(
            message.chat.id, message.from_user.id
        )
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


admin_filter = filters.create(_admin_filter_func)


def admin_required(*perms):
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message, *args, **kwargs):
            if message.chat.type == enums.ChatType.PRIVATE:
                return
            try:
                member = await client.get_chat_member(
                    message.chat.id, message.from_user.id
                )
                if member.status == ChatMemberStatus.OWNER:
                    return await func(client, message, *args, **kwargs)
                if message.from_user.id in config.OWNER_ID or message.from_user.id in app.sudoers:
                    return await func(client, message, *args, **kwargs)
                if member.status == ChatMemberStatus.ADMINISTRATOR:
                    priv = getattr(member, "privileges", None)
                    if perms and priv:
                        if all(getattr(priv, p, False) for p in perms):
                            return await func(client, message, *args, **kwargs)
                        return await message.reply_text(
                            f"You need: {', '.join(perms)}"
                        )
                    return await func(client, message, *args, **kwargs)
            except Exception:
                pass
            await message.reply_text("You need to be an admin.")
        return wrapper
    return decorator


async def is_admin(message_or_cq) -> bool:
    try:
        if isinstance(message_or_cq, CallbackQuery):
            chat_id = message_or_cq.message.chat.id
            user_id = message_or_cq.from_user.id
        else:
            chat_id = message_or_cq.chat.id
            user_id = message_or_cq.from_user.id

        if user_id in config.OWNER_ID or user_id in app.sudoers:
            return True

        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False
        
