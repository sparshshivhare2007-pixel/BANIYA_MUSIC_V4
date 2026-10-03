# Authored By Certified Coders © 2025
from pyrogram import filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from BANIYA_V3 import app


# ────────────────────────────────────────────────────────────
# admin_filter (khud define)
# ────────────────────────────────────────────────────────────
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


# ────────────────────────────────────────────────────────────
# Utility Functions
# ────────────────────────────────────────────────────────────
def is_group(message: Message) -> bool:
    return message.chat.type not in (ChatType.PRIVATE, ChatType.BOT)


async def has_permission(user_id: int, chat_id: int, permission: str) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        priv = getattr(member, "privileges", None)
        if priv and getattr(priv, permission, False):
            return True
        return getattr(member, "status", "") == ChatMemberStatus.OWNER
    except Exception:
        return False


def _view_btn(msg: Message):
    try:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("📝 View Message", url=msg.link)
        ]])
    except Exception:
        return None


# ────────────────────────────────────────────────────────────
# /pin
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("pin") & filters.group & admin_filter)
async def pin(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**This command only works in groups!**")

    if not message.reply_to_message:
        return await message.reply_text("**Reply to a message to pin it!**")

    if not await has_permission(message.from_user.id, message.chat.id, "can_pin_messages"):
        return await message.reply_text("**You don't have permission to pin messages.**")

    try:
        await message.reply_to_message.pin()
        await message.reply_text(
            f"**Successfully pinned message!**\n\n"
            f"**Chat:** {message.chat.title}\n"
            f"**Admin:** {message.from_user.mention}",
            reply_markup=_view_btn(message.reply_to_message)
        )
    except Exception as e:
        await message.reply_text(f"**Failed to pin message:**\n`{e}`")


# ────────────────────────────────────────────────────────────
# /unpin
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("unpin") & filters.group & admin_filter)
async def unpin(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**This command only works in groups!**")

    if not message.reply_to_message:
        return await message.reply_text("**Reply to a message to unpin it!**")

    if not await has_permission(message.from_user.id, message.chat.id, "can_pin_messages"):
        return await message.reply_text("**You don't have permission to unpin messages.**")

    try:
        await message.reply_to_message.unpin()
        await message.reply_text(
            f"**Successfully unpinned message!**\n\n"
            f"**Chat:** {message.chat.title}\n"
            f"**Admin:** {message.from_user.mention}",
            reply_markup=_view_btn(message.reply_to_message)
        )
    except Exception as e:
        await message.reply_text(f"**Failed to unpin message:**\n`{e}`")


# ────────────────────────────────────────────────────────────
# /setphoto
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("setphoto") & filters.group & admin_filter)
async def set_photo(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**This command only works in groups!**")
    if not message.reply_to_message:
        return await message.reply_text("**Reply to a photo or image document.**")
    if not await has_permission(message.from_user.id, message.chat.id, "can_change_info"):
        return await message.reply_text("**You don't have permission to change group info.**")

    target = message.reply_to_message
    file_id = None

    if getattr(target, "photo", None):
        file_id = target.photo.file_id
    elif getattr(target, "document", None) and getattr(target.document, "mime_type", ""):
        if target.document.mime_type.startswith("image/"):
            file_id = target.document.file_id

    if not file_id:
        return await message.reply_text("**Please reply to an image (photo or image document).**")

    try:
        await app.set_chat_photo(chat_id=message.chat.id, photo=file_id)
        await message.reply_text(
            f"**Group photo updated successfully!**\nBy {message.from_user.mention}"
        )
    except Exception as e:
        await message.reply_text(f"**Failed to set photo:**\n`{e}`")


# ────────────────────────────────────────────────────────────
# /removephoto
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("removephoto") & filters.group & admin_filter)
async def remove_photo(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**This command only works in groups!**")
    if not await has_permission(message.from_user.id, message.chat.id, "can_change_info"):
        return await message.reply_text("**You don't have permission to change group info.**")
    try:
        await app.delete_chat_photo(message.chat.id)
        await message.reply_text(
            f"**Group photo removed!**\nBy {message.from_user.mention}"
        )
    except Exception as e:
        await message.reply_text(f"**Failed to remove photo:**\n`{e}`")


# ────────────────────────────────────────────────────────────
# /settitle
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("settitle") & filters.group & admin_filter)
async def set_title(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**This command only works in groups!**")
    if not await has_permission(message.from_user.id, message.chat.id, "can_change_info"):
        return await message.reply_text("**You don't have permission to change group info.**")

    title = None
    if len(message.command) > 1:
        title = message.text.split(None, 1)[1].strip()
    elif message.reply_to_message and getattr(message.reply_to_message, "text", None):
        title = message.reply_to_message.text.strip()

    if not title:
        return await message.reply_text("**Please provide a new title.**")

    try:
        await message.chat.set_title(title)
        await message.reply_text(
            f"**Group title changed to:** {title}\nBy {message.from_user.mention}"
        )
    except Exception as e:
        await message.reply_text(f"**Failed to set title:**\n`{e}`")


# ────────────────────────────────────────────────────────────
# /setdiscription (ya /setdescription)
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command(["setdiscription", "setdescription"]) & filters.group & admin_filter)
async def set_description(_, message: Message):
    if not is_group(message):
        return await message.reply_text("**This command only works in groups!**")
    if not await has_permission(message.from_user.id, message.chat.id, "can_change_info"):
        return await message.reply_text("**You don't have permission to change group info.**")

    desc = None
    if len(message.command) > 1:
        desc = message.text.split(None, 1)[1].strip()
    elif message.reply_to_message and getattr(message.reply_to_message, "text", None):
        desc = message.reply_to_message.text.strip()

    if not desc:
        return await message.reply_text("**Please provide a new description.**")

    try:
        await message.chat.set_description(desc)
        await message.reply_text(
            f"**Group description updated!**\nBy {message.from_user.mention}"
        )
    except Exception as e:
        await message.reply_text(f"**Failed to set description:**\n`{e}`")
