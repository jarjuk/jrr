"""Publish subscribe 'spy' aka 'reader'
"""
import asyncio
import logging
from typing import Callable

from .publish_subsrcibe import Hub, Subscription
from .constants import TOPICS
from .messages import is_message_type


logger = logging.getLogger(__name__)


async def reader_coro(name: str,
                      hub: Hub,
                      topic: str,
                      action: Callable | None = None
                      ) -> str:
    """Publish subscribe 'spy' aka 'reader'.

    Details
    ----

    Listen to 'topic' - print to stdout. Exits on EXIT message on
    'topic' or if optional 'action' lambda returns False (=!goon).

    Parameters
    ----

    :hub: publish/subscribe patter data manager

    :name: just a string to identify coro

    :action: function/async function to call when message
    received. Exit if 'action' return False.

    Return
    -----
    Shutdown message

    """

    # await asyncio.sleep(random.random() * 5)
    logger.info("Reader '%s' has decided to subscribe now!", name)

    msg = ""
    with Subscription(hub=hub, topic=topic) as queue:
        # while msg not in [TOPICS.COMMON_MESSAGES.EXIT]:
        while not is_message_type(msg, TOPICS.COMMON_MESSAGES.EXIT):
            msg = await queue.get()
            # logger.debug("%s got msg: '%s'", name, msg)

            # Opitionally invoke action
            if action is not None:
                # logger.info("%s call action on msg: '%s'", name, msg)

                # distinguish between co-routine/normal function
                if asyncio.iscoroutinefunction(action):
                    logger.debug("async call: msg='%s'", msg)
                    goon = await action(msg, hub=hub)
                else:
                    logger.debug("sync call: msg='%s'", msg)
                    goon = action(msg, hub=hub)
                logger.info("name: %s - action on msg '%s' finished -> goon: %s",
                            name, msg, goon)

                # Exit on 'action' lambda
                if not goon:
                    logger.warning(
                        "name: %s - exiting on action returning False", name)
                    break

    exit_msg = f"Reader '{name}' is shutting down on '{msg=}'"
    logger.info("%s msg: %s", name, exit_msg)
    return exit_msg
