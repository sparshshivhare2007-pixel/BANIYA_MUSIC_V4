# Authored By Certified Coders © 2025
"""
-------------------------------------------------------------------------
Single-user moderation commands with complete edge-case handling.
-------------------------------------------------------------------------
"""

import asyncio
import datetime as dt
from typing import Optional

from pyrogram import filters, enums
from pyrogram.errors import (ChatAdminRequired, UserAdminInvalid,
                             UserNotParticipant, RPCError)
from pyrogram.types import Message, ChatPermissions

from BANIYA_V3 import app, config


# ────────────────────────────────────────────────────────────
# admin_check decorator (agar aapke helpers me nahi hai toh ye use karein)
# ────────────────────────────────────────────────────────────
from functools import wraps


def admin_check(func):
    @wraps(func)
    async def wrapper(client, message: Message, *args, **kwargs):
        if message.chat.type == enums.ChatType.PRIVATE:
            return
        # Owner bypass
        if message.from_user.id in config.OWNER_ID:
            return await func(client, message, *args, **kwargs)
        # Sudo bypass
        if message.from_user.id in app.sudoers:
            return await func(client, message, *args, **kwargs)
        # Admin check
        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            if member.status in (enums.ChatMemberStatus.ADMINISTRATOR,
                                 enums.ChatMemberStatus.OWNER):
                return await func(client, message, *args, **kwargs)
        except Exception:
            pass
        await message.reply_text("You need to be an admin to use this command.")
    return wrapper


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

def mention(user_id: int, name: str) -> str:
    return f"[{name}](tg://user?id={user_id})"


def parse_time(time_arg: str) -> Optional[dt.timedelta]:
    """1s, 5m, 2h, 3d → timedelta"""
    if not time_arg:
        return None
    unit = time_arg[-1].lower()
    try:
        num = int(time_arg[:-1])
    except ValueError:
        return None
    if unit == "s":
        return dt.timedelta(seconds=num)
    elif unit == "m":
        return dt.timedelta(minutes=num)
    elif unit == "h":
        return dt.timedelta(hours=num)
    elif unit == "d":
        return dt.timedelta(days=num)
    return None


async def extract_user_and_reason(message: Message, client):
    user_id = None
    name = None
    reason = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.first_name
        if len(message.command) > 1:
            reason = message.text.split(None, 1)[1]
    elif len(message.command) >= 2:
        arg = message.command[1]
        if arg.startswith("@"):
            try:
                user = await client.get_users(arg)
                user_id = user.id
                name = user.first_name
            except Exception:
                await message.reply_text("User not found.")
                return None, None, None
        else:
            try:
                user_id = int(arg)
                user = await client.get_users(user_id)
                name = user.first_name
            except Exception:
                await message.reply_text("Invalid user ID.")
                return None, None, None
        if len(message.command) > 2:
            reason = message.text.split(None, 2)[2]
    else:
        await message.reply_text("Please reply to a user or provide a username/ID.")
        return None, None, None

    return user_id, name, reason


# ────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────
_DEF_MUTE_PERMS = ChatPermissions()

_USAGES = {
    "ban":    "/ban @user [reason] — or reply with /ban [reason]",
    "unban":  "/unban @user [reason] — or reply with /unban [reason]",
    "mute":   "/mute @user [reason] — or reply with /mute [reason]",
    "unmute": "/unmute @user [reason] — or reply with /unmute [reason]",
    "tmute":  "/tmute @user <time> [reason] — or reply with /tmute <time> [reason]",
    "kick":   "/kick @user [reason] — or reply with /kick [reason]",
    "dban":   "Reply to a user's message with /dban [reason]",
    "sban":   "/sban @user — or reply with /sban",
    "tban":   "/tban @user <time> [reason] — or reply with /tban <time> [reason]",
    "kickme": "/kickme — kick yourself from the group",
}


def _usage(cmd: str) -> str:
    return _USAGES.get(cmd, "Invalid usage.")


def _format_success(action: str, msg: Message, uid: int, name: str, reason: Optional[str]) -> str:
    chat = msg.chat.title
    user_m  = mention(uid, name)
    admin_m = mention(msg.from_user.id, msg.from_user.first_name)
    text = (
        f"» {action} ᴀ ᴜsᴇʀ ɪɴ {chat}\n"
        f" ᴜsᴇʀ  : {user_m}\n"
        f" ᴀᴅᴍɪɴ : {admin_m}"
    )
    if reason:
        text += f"\nReason: {reason}"
    return text


async def _get_member_safe(client, chat_id: int, user_id: int):
    try:
        return await client.get_chat_member(chat_id, user_id)
    except (UserNotParticipant, RPCError):
        return None


async def _get_bot_member(client, chat_id: int):
    me = await client.get_me()
    return await _get_member_safe(client, chat_id, me.id)


def _is_admin_status(status: enums.ChatMemberStatus) -> bool:
    return status in (enums.ChatMemberStatus.ADMINISTRATOR,
                      enums.ChatMemberStatus.OWNER)


# ────────────────────────────────────────────────────────────
# /ban
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("ban") & filters.group)
@admin_check
async def ban_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text(_usage("ban"))

    uid, name, reason = await extract_user_and_reason(message, client)
    if not uid:
        return

    target = await _get_member_safe(client, message.chat.id, uid)
    if target and _is_admin_status(target.status):
        return await message.reply_text("I cannot ban an admin or the group owner.")

    if target and target.status == enums.ChatMemberStatus.BANNED:
        return await message.reply_text("User is already banned.")

    try:
        await client.ban_chat_member(message.chat.id, uid)
        await message.reply_text(_format_success("Ban", message, uid, name, reason))
    except ChatAdminRequired:
        await message.reply_text("I need ban permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot ban an admin.")


# ────────────────────────────────────────────────────────────
# /unban
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("unban") & filters.group)
@admin_check
async def unban_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text(_usage("unban"))

    uid, name, reason = await extract_user_and_reason(message, client)
    if not uid:
        return
    mem = await _get_member_safe(client, message.chat.id, uid)
    if not mem or mem.status != enums.ChatMemberStatus.BANNED:
        return await message.reply_text("User is not banned.")

    try:
        await client.unban_chat_member(message.chat.id, uid)
        await message.reply_text(_format_success("Unban", message, uid, name, reason))
    except ChatAdminRequired:
        await message.reply_text("I need unban permissions.")


# ────────────────────────────────────────────────────────────
# /mute
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("mute") & filters.group)
@admin_check
async def mute_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text(_usage("mute"))

    uid, name, reason = await extract_user_and_reason(message, client)
    if not uid:
        return

    target = await _get_member_safe(client, message.chat.id, uid)
    if target and _is_admin_status(target.status):
        return await message.reply_text("I cannot mute an admin or the group owner.")

    if target and target.status == enums.ChatMemberStatus.RESTRICTED and target.permissions == _DEF_MUTE_PERMS:
        return await message.reply_text("User is already muted.")

    try:
        await client.restrict_chat_member(message.chat.id, uid, _DEF_MUTE_PERMS)
        await message.reply_text(_format_success("Mute", message, uid, name, reason))
    except ChatAdminRequired:
        await message.reply_text("I need mute permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot mute an admin.")


# ────────────────────────────────────────────────────────────
# /unmute
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("unmute") & filters.group)
@admin_check
async def unmute_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text(_usage("unmute"))

    uid, name, reason = await extract_user_and_reason(message, client)
    if not uid:
        return
    mem = await _get_member_safe(client, message.chat.id, uid)
    if not mem or mem.status != enums.ChatMemberStatus.RESTRICTED:
        return await message.reply_text("User is not muted.")

    perms = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_invite_users=True,
    )
    try:
        await client.restrict_chat_member(message.chat.id, uid, perms)
        await message.reply_text(_format_success("Unmute", message, uid, name, reason))
    except ChatAdminRequired:
        await message.reply_text("I need unmute permissions.")


# ────────────────────────────────────────────────────────────
# /tmute
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("tmute") & filters.group)
@admin_check
async def tmute_cmd(client, message: Message):
    if ((not message.reply_to_message and len(message.command) < 3) or
        (message.reply_to_message and len(message.command) < 2)):
        return await message.reply_text(_usage("tmute"))

    if message.reply_to_message:
        user    = message.reply_to_message.from_user
        time_arg= message.command[1]
        reason  = message.text.partition(time_arg)[2].strip()
    else:
        user = await client.get_users(message.command[1])
        if not user:
            return await message.reply_text("I can't find that user.")
        time_arg= message.command[2]
        reason  = message.text.partition(time_arg)[2].strip()

    target = await _get_member_safe(client, message.chat.id, user.id)
    if target and _is_admin_status(target.status):
        return await message.reply_text("I cannot mute an admin or the group owner.")

    delta = parse_time(time_arg)
    if not delta:
        return await message.reply_text("Invalid time format. Use s/m/h/d suffix.")

    until = dt.datetime.now(dt.timezone.utc) + delta
    try:
        await client.restrict_chat_member(message.chat.id, user.id, _DEF_MUTE_PERMS, until_date=until)
        await message.reply_text(_format_success(f"Mute for {time_arg}", message, user.id, user.first_name, reason))
    except ChatAdminRequired:
        await message.reply_text("I need mute permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot mute an admin.")


# ────────────────────────────────────────────────────────────
# /kick
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("kick") & filters.group)
@admin_check
async def kick_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text(_usage("kick"))

    uid, name, reason = await extract_user_and_reason(message, client)
    if not uid:
        return

    target = await _get_member_safe(client, message.chat.id, uid)
    if target and _is_admin_status(target.status):
        return await message.reply_text("I cannot kick an admin or the group owner.")

    try:
        await client.ban_chat_member(message.chat.id, uid)
        await asyncio.sleep(2)
        await client.unban_chat_member(message.chat.id, uid)
        await message.reply_text(_format_success("Kick", message, uid, name, reason))
    except ChatAdminRequired:
        await message.reply_text("I need ban permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot kick an admin.")


# ────────────────────────────────────────────────────────────
# /dban
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("dban") & filters.group)
@admin_check
async def dban_cmd(client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(_usage("dban"))

    user   = message.reply_to_message.from_user
    reason = message.text.split(None, 1)[1] if len(message.command) > 1 else None

    target = await _get_member_safe(client, message.chat.id, user.id)
    if target and _is_admin_status(target.status):
        return await message.reply_text("I cannot ban an admin or the group owner.")

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await message.reply_to_message.delete()
        await message.reply_text(_format_success("Ban", message, user.id, user.first_name, reason))
    except ChatAdminRequired:
        await message.reply_text("I need ban & delete permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot ban an admin.")


# ────────────────────────────────────────────────────────────
# /sban
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("sban") & filters.group)
@admin_check
async def sban_cmd(client, message: Message):
    if len(message.command) == 1 and not message.reply_to_message:
        return await message.reply_text(_usage("sban"))

    uid, _, _ = await extract_user_and_reason(message, client)
    if not uid:
        return

    target = await _get_member_safe(client, message.chat.id, uid)
    if target and _is_admin_status(target.status):
        return await message.reply_text("I cannot ban an admin or the group owner.")

    try:
        await client.ban_chat_member(message.chat.id, uid)
        await message.delete()
    except ChatAdminRequired:
        await message.reply_text("I need ban permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot ban an admin.")


# ────────────────────────────────────────────────────────────
# /kickme
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("kickme") & filters.group)
async def kickme_cmd(client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return

    target = await _get_member_safe(client, message.chat.id, message.from_user.id)
    if target and _is_admin_status(target.status):
        return await message.reply_text("Nice try, boss 😅 I can't kick admins or the owner.")

    bot_mem = await _get_bot_member(client, message.chat.id)
    if not bot_mem or not getattr(bot_mem, "can_restrict_members", False):
        return await message.reply_text("I need ban permissions to kick you. Ask an admin to enable it.")

    try:
        await client.ban_chat_member(message.chat.id, message.from_user.id)
        await asyncio.sleep(3)
        await client.unban_chat_member(message.chat.id, message.from_user.id)
        await message.reply_text("Kicked so hard, your ancestors felt it. 👟💥")
    except ChatAdminRequired:
        await message.reply_text("I need ban permissions.")
    except UserAdminInvalid:
        await message.reply_text("I can't kick admins or the owner.")


# ────────────────────────────────────────────────────────────
# /tban
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("tban") & filters.group)
@admin_check
async def tban_cmd(client, message: Message):
    if ((not message.reply_to_message and len(message.command) < 3) or
        (message.reply_to_message and len(message.command) < 2)):
        return await message.reply_text(_usage("tban"))

    if message.reply_to_message:
        user    = message.reply_to_message.from_user
        time_arg= message.command[1]
        reason  = message.text.partition(time_arg)[2].strip()
    else:
        user = await client.get_users(message.command[1])
        if not user:
            return await message.reply_text("I can't find that user.")
        time_arg= message.command[2]
        reason  = message.text.partition(time_arg)[2].strip()

    target = await _get_member_safe(client, message.chat.id, user.id)
    if target and _is_admin_status(target.status):
        return await message.reply_text("I cannot ban an admin or the group owner.")

    delta = parse_time(time_arg)
    if not delta:
        return await message.reply_text("Invalid time format. Use s/m/h/d suffix.")

    until = dt.datetime.now(dt.timezone.utc) + delta
    try:
        await client.ban_chat_member(message.chat.id, user.id, until_date=until)
        await message.reply_text(_format_success(f"Ban for {time_arg}", message, user.id, user.first_name, reason))
    except ChatAdminRequired:
        await message.reply_text("I need ban permissions.")
    except UserAdminInvalid:
        await message.reply_text("I cannot ban an admin.")
