# Simple in-memory welcome DB (MongoDB ke bina bhi kaam karega)
import time
from typing import Dict, Tuple

_welcome_state: Dict[int, bool] = {}       # chat_id -> on/off
_join_bumps: Dict[int, list] = {}          # chat_id -> [timestamps]
_cool_until: Dict[int, float] = {}         # chat_id -> cooldown end time


async def is_on(chat_id: int) -> bool:
    return _welcome_state.get(chat_id, False)


async def set_state(chat_id: int, state: str):
    _welcome_state[chat_id] = (state == "on")


async def bump(chat_id: int, window: int) -> int:
    """Kitne joins last `window` seconds me hue"""
    now = time.time()
    arr = _join_bumps.setdefault(chat_id, [])
    arr.append(now)
    # Purane timestamps hata do
    arr[:] = [t for t in arr if now - t <= window]
    return len(arr)


async def cool(chat_id: int, minutes: int):
    """Welcome ko X minutes ke liye band karo"""
    _cool_until[chat_id] = time.time() + minutes * 60


async def auto_on(chat_id: int) -> bool:
    """Cooldown khatam hone par auto-on"""
    now = time.time()
    if chat_id in _cool_until:
        if now >= _cool_until[chat_id]:
            del _cool_until[chat_id]
            _welcome_state[chat_id] = True
            return True
        return False
    return False
