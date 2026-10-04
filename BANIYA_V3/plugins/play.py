# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

from pathlib import Path

from pyrogram import enums, filters, types

from BANIYA_V3 import anon, app, config, db, lang, queue, tg, yt
from BANIYA_V3.helpers import buttons, utils
from BANIYA_V3.helpers._play import checkUB
from BANIYA_V3.utils.rich_utils import _html_caption_to_blocks


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


async def _send_queued_rich(client, chat_id, message, text, file_id, lang_dict):
    """Send a queued-track notification as a rich message."""
    blocks = _html_caption_to_blocks(text)

    play_now_text = (lang_dict or {}).get("play_now", "▶ Play Now")
    skip_text     = (lang_dict or {}).get("skipped", "» Skip")
    end_text      = (lang_dict or {}).get("stopped", "🚫 End")

    blocks.append(
        types.InputRichBlockButtons(
            buttons=[
                types.RichMessageButton(
                    text=play_now_text,
                    style=enums.ButtonStyle.SUCCESS,
                    callback_data=f"controls force {chat_id} {file_id}",
                ),
            ]
        )
    )
    blocks.append(
        types.InputRichBlockButtons(
            buttons=[
                types.RichMessageButton(
                    text=skip_text,
                    style=enums.ButtonStyle.PRIMARY,
                    callback_data=f"controls skip {chat_id}",
                ),
                types.RichMessageButton(
                    text=end_text,
                    style=enums.ButtonStyle.DANGER,
                    callback_data=f"controls stop {chat_id}",
                ),
            ]
        )
    )

    rich = types.InputRichMessage(blocks=blocks)
    try:
        return await message.edit_text(rich_message=rich)
    except Exception:
        try:
            await message.delete()
        except Exception:
            pass
        try:
            return await client.send_rich_message(
                chat_id=chat_id,
                rich_message=rich,
            )
        except Exception:
            # Fallback: send raw string (may show tags if unsupported)
            return await client.send_message(chat_id=chat_id, text=text)


# ========== AUDIO PLAY COMMANDS ==========
@app.on_message(
    filters.command(["play", "playforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:
    sent = await m.reply_text(m.lang["play_searching"])
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif m3u8:
        file = await tg.process_m3u8(url, sent.id, video)

    elif url:
        if "playlist" in url:
            await sent.edit_text(m.lang["playlist_fetch"])
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video
            )

            if not tracks:
                return await sent.edit_text(m.lang["playlist_error"])

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=video)

        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id, video=video)
        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    if not file:
        return await sent.edit_text(m.lang["play_usage"])

    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration)

    file.user = mention
    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)

        if position != 0 or await db.get_call(m.chat.id):
            _queued_text = m.lang["play_queued"].format(
                position,
                file.url,
                file.title,
                file.duration,
                m.from_user.mention,
            )
            await _send_queued_rich(
                client=app,
                chat_id=m.chat.id,
                message=sent,
                text=_queued_text,
                file_id=file.id,
                lang_dict=m.lang,
            )
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                )
            return

    if not file.file_path:
        fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            file.file_path = fname
        else:
            await sent.edit_text(m.lang["play_downloading"])
            file.file_path = await yt.download(file.id, video=video)

    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    if not tracks:
        return
    added = playlist_to_queue(m.chat.id, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
    )


# ========== VIDEO PLAY COMMANDS ==========
@app.on_message(
    filters.command(["vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def vplay_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = True,
    url: str = None,
) -> None:
    """Handle video playback in voice chat — same style as /play"""

    if m.command[0].endswith("force"):
        force = True

    sent = await m.reply_text(m.lang["play_searching"])
    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif m3u8:
        file = await tg.process_m3u8(url, sent.id, video)

    elif url:
        if "playlist" in url:
            await sent.edit_text(m.lang["playlist_fetch"])
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video
            )

            if not tracks:
                return await sent.edit_text(m.lang["playlist_error"])

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=video)

        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id, video=video)
        if not file:
            return await sent.edit_text(
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )

    if not file:
        return await sent.edit_text(m.lang["play_usage"])

    if file.duration_sec > config.DURATION_LIMIT:
        return await sent.edit_text(
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )

    if await db.is_logger():
        await utils.play_log(m, sent.link, file.title, file.duration)

    file.user = mention
    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)

        if position != 0 or await db.get_call(m.chat.id):
            _queued_text = m.lang["play_queued"].format(
                position,
                file.url,
                file.title,
                file.duration,
                m.from_user.mention,
            )
            await _send_queued_rich(
                client=app,
                chat_id=m.chat.id,
                message=sent,
                text=_queued_text,
                file_id=file.id,
                lang_dict=m.lang,
            )
            if tracks:
                added = playlist_to_queue(m.chat.id, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                )
            return

    if not file.file_path:
        fname = f"downloads/{file.id}.mp4"
        if Path(fname).exists() and Path(fname).stat().st_size > 0:
            file.file_path = fname
        else:
            await sent.edit_text(m.lang["play_downloading"])
            file.file_path = await yt.download(file.id, video=True)

            if not file.file_path:
                return await sent.edit_text(
                    m.lang["error_no_file"].format(config.SUPPORT_CHAT)
                )

    await anon.play_media(chat_id=m.chat.id, message=sent, media=file)
    if not tracks:
        return
    added = playlist_to_queue(m.chat.id, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
    )
