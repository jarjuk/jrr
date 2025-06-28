"""Coroutine implementation to read from sdtdin.
"""
from typing import Callable
import asyncio
import sys
import logging
from functools import partial

from .constants import TOPICS
from .publish_subsrcibe import Hub

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
def _default_action(msg: str, hub: Hub, name: str, topic: str, topic_ctr: str):
    """Default action in 'stdin_coro'
    """
    if msg == TOPICS.CONTROL_MESSAGES.REBOOT:
        # Close app
        logger.info("%s: msg: '%s' - publish on topic '%s'",
                    name, msg, topic_ctr)
        hub.publish(topic_ctr, msg)
        # Expect somebody to listed to SHUTDOWN message and cancel also me
        # break

    logger.info("%s: msg: '%s' - publish on topic '%s'",
                name, msg, topic)
    hub.publish(topic, msg)

    return True

# ------------------------------------------------------------------


async def stdin_coro(
        name: str,
        hub: Hub,
        topic: str,
        topic_ctr: str,
        action: Callable[(str, Hub), bool] | None = None,
):
    """Coro routine for stdin.

    Details
    ----
    Wait for input from 'stdin' and publish it to 'topic'.

    If 'action' not given publish 'stdin' to 'topic' (and SHUTDOWN
    -string passed also to 'topic_ctr')

    If 'action' given call/await 'action' with message. Exit if
    'action' returns False.


    Parameters
    ----
    :name: string to show in log messages etc

    :hub: publish/subscribe data manager

    :topic: where to publish input read from stdin.

    :topic_ctr: where to publish SHUTDOWN message

    :action: Optional function call/await function with message. Exit if
    'action' returns False.

    Return
    -----
    String for exit reason

    """

    stream_reader = asyncio.StreamReader()
    stdin_pipe = sys.stdin
    event_loop = asyncio.get_event_loop()

    if action is None:
        # Default action: publish on topic, SHUTDOWN also to topic_ctr
        action = partial(
            _default_action, name=name, topic=topic, topic_ctr=topic_ctr)

    await event_loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(stream_reader),
        stdin_pipe)

    async for line in stream_reader:
        stdin_str = line.decode("utf-8").rstrip()

        # Opitionally invoke action
        logger.debug("%s stdin_str: '%s'", name, stdin_str)

        # distinguish between co-routine/normal function
        if asyncio.iscoroutinefunction(action):
            goon = await action(stdin_str, hub=hub)
        else:
            goon = action(stdin_str, hub=hub)
            logger.debug("name: %s - go-on %s", name, goon)

        # Exit on 'action' lambda
        if not goon:
            logger.warning(
                "name: %s - exiting on actions returning False", name)
            break

    # allow messages to pass - before exiting
    await asyncio.sleep(0.1)
    exit_msg = f"{name}: exiting"
    logger.info("%s: exit_msg: '%s'", name, exit_msg)
    return exit_msg
