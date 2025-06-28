"""Clock module implemeted using asyncio. Bad jitter --> not suitable
for precise timer.

"""
from typing import List

import logging
import asyncio

from .constants import TOPICS
from .messages import message_create
from .publish_subsrcibe import Hub

logger = logging.getLogger(__name__)


async def clock_coro(name: str, hub: Hub, tick: float,  topics: List[str], ):
    """
    Timer coro sendint CLOCK_TICK -messages to 'topics'.

    Details
    ----
    Sends periodically clock message to topcs

    Parameters
    ----

    :tick: delay between ticks 

    :topcs: list of topics to infor on tick

    :hub: publish-subscibe patter message controller

    Return
    -----

    """

    logger.info("Clock_coro %s starting  now!", name)

    while True:
        await asyncio.sleep(delay=tick)
        tick_message = message_create(
            message_type=TOPICS.COMMON_MESSAGES.CLOCK_TICK)

        for topic in topics:
            logger.debug("publish message %s on topic: %s",
                         tick_message, topic)
            hub.publish(topic=topic, message=tick_message)
