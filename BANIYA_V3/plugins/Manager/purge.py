# Authored By Certified Coders © 2025
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import MessageDeleteForbidden, RPCError, FloodWait
from pyrogram.types import Message

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


def divide_chunks(l: list, n: int = 100):
    for i in range(0, len(l), n):
        yield l[i: i + n]


# ────────────────────────────────────────────────────────────
# /purge
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("purge") & filters.group & admin_filter)
async def purge(client, msg: Message):
    if msg.chat.type != ChatType.SUPERGROUP:
        return await msg.reply(
            "**❌ This command only works in supergroups. Please convert your group to a supergroup first.**"
        )

    if not msg.reply_to_message:
        return await msg.reply(
            "**❌ Reply to a message to start purging!**"
        )

    message_ids = list(range(msg.reply_to_message.id, msg.id))
    m_list = list(divide_chunks(message_ids))

    try:
        for plist in m_list:
            try:
                await app.delete_messages(chat_id=msg.chat.id, message_ids=plist, revoke=True)
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
        await msg.delete()
        count = len(message_ids)
        confirm = await msg.reply(f"✅ | **Deleted `{count}` messages.**")
        await asyncio.sleep(3)
        try:
            await confirm.delete()
        except Exception:
            pass
    except MessageDeleteForbidden:
        await msg.reply(
            "**❌ I can't delete messages. Maybe I'm not admin or don't have delete permission.**"
        )
    except RPCError as e:
        await msg.reply(f"**Error occurred:**\n<code>{e}</code>")


# ────────────────────────────────────────────────────────────
# /spurge (silent purge)
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("spurge") & filters.group & admin_filter)
async def spurge(client, msg: Message):
    if msg.chat.type != ChatType.SUPERGROUP:
        return await msg.reply(
            "**❌ This command only works in supergroups.**"
        )

    if not msg.reply_to_message:
        return await msg.reply(
            "**❌ Reply to a message to start purging!**"
        )

    message_ids = list(range(msg.reply_to_message.id, msg.id))
    m_list = list(divide_chunks(message_ids))

    try:
        for plist in m_list:
            try:
                await app.delete_messages(chat_id=msg.chat.id, message_ids=plist, revoke=True)
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
        await msg.delete()
    except MessageDeleteForbidden:
        await msg.reply("**❌ I can't delete messages. Check my permissions.**")
    except RPCError as e:
        await msg.reply(f"**Error occurred:**\n<code>{e}</code>")


# ────────────────────────────────────────────────────────────
# /del
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command("del") & filters.group & admin_filter)
async def del_msg(client, msg: Message):
    if msg.chat.type != ChatType.SUPERGROUP:
        return await msg.reply("**❌ This command only works in supergroups.**")

    if not msg.reply_to_message:
        return await msg.reply("**❓ What do you want to delete?**")

    try:
        await msg.delete()
        await app.delete_messages(chat_id=msg.chat.id, message_ids=msg.reply_to_message.id)
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        await msg.reply(f"**Failed to delete message:**\n<code>{e}</code>")
