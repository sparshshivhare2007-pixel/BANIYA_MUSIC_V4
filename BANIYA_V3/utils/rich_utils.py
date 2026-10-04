# Copyright (c) 2025 BANIYA_V3mousX1025
# Licensed under the MIT License.
# Rich message helpers for now-playing UI

import math
import random
import re

from pyrogram import enums, errors, types

from BANIYA_V3 import lang as _lang_obj, logger


# ---------- Helpers ----------

def _time_to_seconds(t: str) -> int:
    """Convert '3:10' or '1:02:30' to total seconds."""
    if not t:
        return 0
    try:
        parts = [int(x) for x in str(t).split(":")]
    except (ValueError, AttributeError):
        return 0
    return sum(p * 60 ** i for i, p in enumerate(reversed(parts)))


def _parse_inline(segment):
    parts = []
    stack = []
    pos = 0

    for m in re.finditer(r"<(/?)(b|a)(?:\s+href=([^>]+))?>", segment, re.IGNORECASE):
        if m.start() > pos:
            parts.append(segment[pos:m.start()])
        pos = m.end()
        closing, tag, href = m.group(1), m.group(2).lower(), m.group(3)
        if not closing:
            stack.append((tag, href.strip("\"'") if href else None, len(parts)))
        elif stack and stack[-1][0] == tag:
            open_tag, url, start = stack.pop()
            inner = parts[start:]
            del parts[start:]
            inner = inner[0] if len(inner) == 1 else inner if inner else ""
            if open_tag == "b":
                parts.append(types.RichTextBold(text=inner))
            else:
                parts.append(types.RichTextUrl(text=inner, url=url))

    if pos < len(segment):
        parts.append(segment[pos:])

    if not parts:
        return ""
    return parts[0] if len(parts) == 1 else parts


def _balance_lines(caption_html):
    lines = []
    carry = False
    for line in caption_html.split("\n"):
        if not line:
            lines.append(line)
            continue
        if carry:
            line = "<b>" + line
        opened = len(re.findall(r"<b>", line, re.IGNORECASE))
        closed = len(re.findall(r"</b>", line, re.IGNORECASE))
        carry = opened > closed
        if carry:
            line += "</b>"
        lines.append(line)
    return lines


def _html_caption_to_blocks(caption_html):
    return [
        types.InputRichBlockParagraph(text=_parse_inline(line))
        for line in _balance_lines(caption_html)
    ]


def _progress_line(played, dur):
    played_sec = _time_to_seconds(played)
    duration_sec = _time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100 if duration_sec else 0
    umm = math.floor(percentage)
    if 0 < umm <= 10:
        bar = "◉—————————"
    elif 10 < umm < 20:
        bar = "—◉————————"
    elif 20 <= umm < 30:
        bar = "——◉———————"
    elif 30 <= umm < 40:
        bar = "———◉——————"
    elif 40 <= umm < 50:
        bar = "————◉—————"
    elif 50 <= umm < 60:
        bar = "—————◉————"
    elif 60 <= umm < 70:
        bar = "——————◉———"
    elif 70 <= umm < 80:
        bar = "———————◉——"
    elif 80 <= umm < 95:
        bar = "————————◉—"
    else:
        bar = "—————————◉"
    return f"{played}  {bar}  {dur}"


_BUTTON_STYLES = [
    enums.ButtonStyle.DEFAULT,
    enums.ButtonStyle.PRIMARY,
    enums.ButtonStyle.SUCCESS,
    enums.ButtonStyle.DANGER,
]


def _random_styles():
    styles = list(_BUTTON_STYLES)
    styles.append(random.choice(_BUTTON_STYLES))
    random.shuffle(styles)
    return styles


def _progress_row(played, dur, style):
    return types.InputRichBlockButtons(
        buttons=[
            types.RichMessageButton(
                text=_progress_line(played, dur),
                style=style,
                callback_data="GetTimer",
            )
        ]
    )


def _control_rows(lang_dict, chat_id, playing, styles):
    replay_style, toggle_style, skip_style, queue_style = styles

    replay_text = (lang_dict or {}).get("RICH_BTN_REPLAY", "🔁 ʀᴇᴘʟᴀʏ")
    pause_text  = (lang_dict or {}).get("RICH_BTN_PAUSE",  "⏸ ᴘᴀᴜsᴇ")
    resume_text = (lang_dict or {}).get("RICH_BTN_RESUME", "▶️ ʀᴇsᴜᴍᴇ")
    skip_text   = (lang_dict or {}).get("RICH_BTN_SKIP",   "⏭ sᴋɪᴘ")
    queue_text  = (lang_dict or {}).get("RICH_BTN_QUEUE",  "≡ ǫᴜᴇᴜᴇ")

    toggle = types.RichMessageButton(
        text=pause_text if playing else resume_text,
        style=toggle_style,
        callback_data=f"ADMIN {'Pause' if playing else 'Resume'}|{chat_id}",
    )
    return [
        types.InputRichBlockButtons(
            buttons=[
                types.RichMessageButton(
                    text=replay_text,
                    style=replay_style,
                    callback_data=f"ADMIN Replay|{chat_id}",
                ),
                toggle,
                types.RichMessageButton(
                    text=skip_text,
                    style=skip_style,
                    callback_data=f"ADMIN Skip|{chat_id}",
                ),
            ]
        ),
        types.InputRichBlockButtons(
            buttons=[
                types.RichMessageButton(
                    text=queue_text,
                    style=queue_style,
                    callback_data=f"nowplaying_queue {chat_id}",
                ),
            ]
        ),
    ]


def build_now_playing_blocks(photo, caption_html, chat_id, lang_dict=None,
                             played=None, dur=None, playing=True):
    blocks = [types.InputRichBlockPhoto(photo=types.InputMediaPhoto(photo))]
    blocks += _html_caption_to_blocks(caption_html)
    styles = _random_styles()
    if played and dur:
        blocks.append(_progress_row(played, dur, styles[4]))
    blocks += _control_rows(lang_dict, chat_id, playing, styles[:4])
    return blocks


async def send_now_playing_rich(client, chat_id, photo, caption_html, replace=None):
    lang_dict = await _lang_obj.get_lang(chat_id)
    blocks = build_now_playing_blocks(photo, caption_html, chat_id, lang_dict)
    rich = types.InputRichMessage(blocks=blocks)

    try:
        if replace is not None:
            return await replace.edit_text(rich_message=rich)
        return await client.send_rich_message(chat_id, rich_message=rich)
    except (errors.ChatSendPhotosForbidden, errors.ChatSendMediaForbidden):
        plain = [b for b in blocks if not isinstance(b, types.InputRichBlockPhoto)]
        rich = types.InputRichMessage(blocks=plain)
        if replace is not None:
            return await replace.edit_text(rich_message=rich)
        return await client.send_rich_message(chat_id, rich_message=rich)
    except Exception as e:
        logger.warning(f"[RICH] send_now_playing_rich failed: {e}")
        raise
