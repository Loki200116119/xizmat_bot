"""
🛡️  Throttling middleware — flood himoya
"""

import time
from typing import Callable, Any
from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 1.5):
        self.rate_limit = rate_limit
        self._user_last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable,
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()
        last = self._user_last_call.get(user_id, 0)

        if now - last < self.rate_limit:
            await event.answer("⏳ Iltimos, biroz sekinroq yozing...")
            return

        self._user_last_call[user_id] = now
        return await handler(event, data)
