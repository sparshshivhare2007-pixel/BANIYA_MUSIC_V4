# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import filters, types

from BANIYA_V3 import app, config, db, lang, queue
from BANIYA_V3.helpers import Track, buttons, thumb
from BANIYA_V3.utils.rich_utils import (
    _html_caption_to_blocks,
    _progress_row,
    _random_styles,
)


@app.on_message(filters.command(["queue", "playing"]) & filters.group & ~app.bl_users)
@lang.language()
async def _queue_func(_, m: types.Message):
    if not await db.get_call(m.chat.id):
        return await m.reply_text(m.lang["not_playing"])

    _reply = await m.reply_text(m.lang["queue_fetching"])
    _queue = queue.get_queue(m.chat.id)
    _media = _queue[0]

    # Generate thumbnail
    _thumb = (
        await thumb.generate(_media)
        if isinstance(_media, Track)
        else config.DEFAULT_THUMB
    ) if config.THUMB_GEN else None

    # Build the caption HTML (with premium emoji tags intact)
    _text = m.lang["queue_curr"].format(
        _media.url,
        _media.title[:50],
        _media.duration,
        _media.user,
    )
    _queue.pop(0)

    if _queue:
        _text += "<blockquote expandable>"
        for i, media in enumerate(_queue, start=1):
            if i == 15:
                break
            _text += m.lang["queue_item"].format(
                i + 1, media.title, media.duration
            )
        _text += "</blockquote>"

    # ---------- Build rich message blocks ----------
    blocks = []
    if _thumb:
        blocks.append(types.InputRichBlockPhoto(photo=types.InputMediaPhoto(_thumb)))
    blocks += _html_caption_to_blocks(_text)

    # Add the pause/resume toggle button as a rich button
    _playing = await db.playing(m.chat.id)
    toggle_text = m.lang["playing"] if _playing else m.lang["paused"]
    blocks.append(
        types.InputRichBlockButtons(
            buttons=[
                types.RichMessageButton(
                    text=toggle_text,
                    style=(
                        types.ButtonStyle.SUCCESS
                        if _playing
                        else types.ButtonStyle.PRIMARY
                    ),
                    callback_data=(
                        f"controls pause {m.chat.id}"
                        if _playing
                        else f"controls resume {m.chat.id}"
                    ),
                ),
            ]
        )
    )

    # ---------- Send as rich message ----------
    rich = types.InputRichMessage(blocks=blocks)
    try:
        await _reply.edit_text(rich_message=rich)
    except Exception:
        # If editing fails, send fresh rich message
        try:
            await _reply.delete()
        except Exception:
            pass
        try:
            await app.send_rich_message(
                chat_id=m.chat.id,
                rich_message=rich,
            )
        except Exception:
            # Final fallback — plain text without emoji tags
            plain = _text.replace("<u>", "").replace("</u>", "")
            import re as _re
            plain = _re.sub(r"<emoji[^>]*>(.*?)</emoji>", r"\1", plain)
            await m.reply_text(plain)
