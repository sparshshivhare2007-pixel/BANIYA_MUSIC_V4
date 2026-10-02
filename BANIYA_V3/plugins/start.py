# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import logging

import requests
from pyrogram import enums, filters, types

from BANIYA_V3 import app, config, db, lang
from BANIYA_V3.helpers import buttons, utils

logger = logging.getLogger(__name__)


def _debug_url(url: str):
    """Check if a URL is reachable and return useful info for debugging."""
    info = {
        "url": url,
        "status_code": None,
        "content_type": None,
        "content_length": None,
        "final_url": None,
        "error": None,
    }
    try:
        resp = requests.head(url, timeout=10, allow_redirects=True)
        info["status_code"] = resp.status_code
        info["content_type"] = resp.headers.get("Content-Type")
        info["content_length"] = resp.headers.get("Content-Length")
        info["final_url"] = resp.url
        if resp.status_code != 200:
            info["error"] = f"Non-200 status: {resp.status_code}"
    except Exception as e:
        info["error"] = f"{type(e).__name__}: {e}"
    return info


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    await m.reply_text(
        text=m.lang["help_menu"],
        reply_markup=buttons.help_markup(m.lang),
    )


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE
    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, app.name)
        if private
        else message.lang["start_gp"].format(app.name)
    )

    key = buttons.start_key(message.lang, private)

    # DEBUG: log the image URL before sending
    logger.info("[START] chat_id=%s private=%s", message.chat.id, private)
    logger.info("[START] START_IMG value = %r", config.START_IMG)
    logger.info("[START] START_IMG type  = %s", type(config.START_IMG).__name__)

    # If it's an HTTP URL, check reachability and log details
    if isinstance(config.START_IMG, str) and config.START_IMG.startswith(("http://", "https://")):
        debug_info = _debug_url(config.START_IMG)
        logger.info(
            "[START] URL debug | status=%s | type=%s | length=%s | final=%s | error=%s",
            debug_info["status_code"],
            debug_info["content_type"],
            debug_info["content_length"],
            debug_info["final_url"],
            debug_info["error"],
        )

        # Warn if content-type isn't an image
        ct = debug_info["content_type"] or ""
        if not ct.startswith("image/"):
            logger.warning(
                "[START] URL does not return an image. Content-Type=%r. "
                "Telegram will likely reject this with WEBPAGE_CURL_FAILED.",
                ct,
            )
    else:
        logger.info("[START] START_IMG is not an HTTP URL, skipping reachability check.")

    try:
        await message.reply_photo(
            photo=config.START_IMG,
            caption=_text,
            reply_markup=key,
        )
        logger.info("[START] Photo sent successfully.")
    except Exception as e:
        logger.exception("[START] reply_photo failed: %s", e)
        # Fallback: send text without the photo so the user still gets a reply
        try:
            await message.reply_text(
                text=_text,
                reply_markup=key,
                disable_web_page_preview=True,
            )
            logger.info("[START] Fallback text message sent (photo failed).")
        except Exception as e2:
            logger.exception("[START] Fallback text also failed: %s", e2)

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        await db.add_user(message.from_user.id)
    else:
        if await db.is_chat(message.chat.id):
            return
        await utils.send_log(message, True)
        await db.add_chat(message.chat.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    admin_only = await db.get_play_mode(message.chat.id)
    cmd_delete = await db.get_cmd_delete(message.chat.id)
    _language = await db.get_lang(message.chat.id)
    await message.reply_text(
        text=message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, cmd_delete, _language, message.chat.id
        ),
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    await asyncio.sleep(3)
    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await utils.send_log(message, True)
            await db.add_chat(message.chat.id)
