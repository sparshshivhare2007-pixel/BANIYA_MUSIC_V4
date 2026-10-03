# Authored By Certified Coders © 2025
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant, FloodWait
from pyrogram.types import Message

from BANIYA_V3 import app


# ────────────────────────────────────────────────────────────
# admin_filter (khud define kar rahe hain)
# ────────────────────────────────────────────────────────────
async def admin_filter(_, __, message: Message) -> bool:
    """Filter: user admin hai ya nahi"""
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


admin_filter = filters.create(admin_filter)


# ────────────────────────────────────────────────────────────
# /utag /all /mention
# ────────────────────────────────────────────────────────────
spam_chats = set()


@app.on_message(filters.command(["utag", "all", "mention"]) & filters.group & admin_filter)
async def tag_all_users(client, message: Message):
    replied = message.reply_to_message
    text = message.text.split(None, 1)[1] if len(message.command) > 1 else ""

    if not replied and not text:
        return await message.reply(
            "**❌ Please provide a message or reply to a message to tag all users.**"
        )

    spam_chats.add(message.chat.id)
    usernum, usertxt, total_tagged = 0, "", 0

    try:
        async for member in client.get_chat_members(message.chat.id):
            if message.chat.id not in spam_chats:
                break

            if not member.user or member.user.is_bot:
                continue

            usernum += 1
            total_tagged += 1
            usertxt += f"➤ [{member.user.first_name}](tg://user?id={member.user.id})\n"

            if usernum == 5:
                try:
                    if replied:
                        await replied.reply_text(
                            f"{text}\n{usertxt}\n📢 Tagged {total_tagged} users so far..."
                        )
                    else:
                        await message.reply_text(
                            f"{text}\n{usertxt}\n📢 Tagged {total_tagged} users so far..."
                        )
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    pass

                await asyncio.sleep(3)
                usernum, usertxt = 0, ""

        if usertxt:
            try:
                if replied:
                    await replied.reply_text(
                        f"{text}\n{usertxt}\n📢 Tagged {total_tagged} users..."
                    )
                else:
                    await message.reply_text(
                        f"{text}\n{usertxt}\n📢 Tagged {total_tagged} users..."
                    )
            except Exception:
                pass

        await message.reply(
            f"✅ **Tagging completed. Total tagged:** `{total_tagged}` **users.**"
        )

    finally:
        spam_chats.discard(message.chat.id)


# ────────────────────────────────────────────────────────────
# /cancel /ustop
# ────────────────────────────────────────────────────────────
@app.on_message(filters.command(["cancel", "ustop"]) & filters.group)
async def cancel_spam(client, message: Message):
    chat_id = message.chat.id

    if chat_id not in spam_chats:
        return await message.reply("**❌ No tagging process is running.**")

    try:
        member = await client.get_chat_member(chat_id, message.from_user.id)
        if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            return await message.reply("**❌ Only admins can cancel the tagging.**")
    except UserNotParticipant:
        return await message.reply("**❌ You are not a participant of this chat.**")
    except Exception:
        return await message.reply("**❌ An error occurred.**")

    spam_chats.discard(chat_id)
    return await message.reply("**🚫 Tagging process cancelled successfully.**")
