"""Publish subscribe 'spy' aka 'reader'
"""
import asyncio
import logging
import random
import evdev

from .publish_subsrcibe import Hub, Subscription
from .constants import TOPICS, RPI
from .kb import read_keyboard_gen, find_keyboard
from .helpers import cancel_and_wait
from .messages import (
    is_message_type, message_key,
)

# ------------------------------------------------------------------
# Module state

logger = logging.getLogger(__name__)

# Keyboard task reading keyboar
keyboard_task: asyncio.Task | None = None

# Access to keyboard device
keyboard: evdev.InputDevice | None = None


def _kb_action(key: str, hub: Hub, topic_out: str) -> bool:
    """Publish MsgKey(key) on 'topic_out'. """

    logger.debug("_kb_action: key='%s'", key)

    hub.publish(topic=topic_out, message=message_key(key=key))

    return True


async def _kb_reader_coro(name: str,
                          hub: Hub,
                          topic_out: str,
                          ) -> str:
    """Wait for key presses and send keys to 'topic_out'

    Parameters
    ----

    :hub: publish/subscribe patter data manager

    :name: just a string to identify coro

    :action: function/async function to call when message
    received. Exit if 'action' returns False.

    Return
    -----
    Shutdown message

    """

    global keyboard
    keyboard = None

    goon = True
    while goon:

        if keyboard is None:
            keyboard = find_keyboard(keyboard_name=RPI.KEYBOARD_NAME)
            if keyboard is None:
                logger.info("No keyboard: keyboard='%s'", keyboard)
                await asyncio.sleep(random.random() * 5)
        else:
            logger.debug("start reading keyboard: keyboard='%s'", keyboard)
            async for key in read_keyboard_gen(keyboard=keyboard):
                logger.debug("reiviced key: key='%s'", key)
                goon = _kb_action(key=key, hub=hub, topic_out=topic_out)
                if not goon:
                    logger.debug("break output from loop : key='%s'", key)
                    break

    exit_msg = f"kb_coro '{name}' is shutting down on '{key=}'"
    logger.info("%s msg: %s", name, exit_msg)
    return exit_msg

# ------------------------------------------------------------------
# Manage keyboard_task


async def _keyboard_stop(name: str):
    """Stops keyboard task

    :name: name to coro where called from 
    """
    logger.info("_keyboard_stop starting: name: '%s'", name)

    global keyboard_task
    try:
        if keyboard_task is not None:
            logger.info(
                "%s: cancellling keyboard_task: %s", name, keyboard_task)
            await cancel_and_wait(
                keyboard_task, msg=f"cancel_and_wait 'keyboard_task' in kb_coro {name}")
            logger.debug("Return from cancel_and_wait")
        else:
            logger.warning(
                "No task to cancel - nothing done")
    except UnboundLocalError as e:
        logger.warning(f"Excpetion '{e}' when accessing 'keyboard_task'")
    finally:
        keyboard_task = None


def is_keyboard_connected() -> bool:
    """Return keyboard connection state.


    """
    ret = keyboard_task is not None and not keyboard_task.done() and keyboard is not None
    logger.debug("is_keyboard_connected: '%s', keyboard_task='%s', keyboard='%s'",
                 ret, keyboard_task, keyboard)
    return ret


async def kb_coro(
        name: str,
        hub: Hub,
        topic: str,
        topic_out: str,
) -> str:
    """Accept control messages from topic and manage _kb_reader_coro.

    Messages processed:
    - EXIT
    - START

    :topic: receive control messages

    :topic_out: topic where to send keyboard message

    """

    # await asyncio.sleep(random.random() * 5)
    logger.info("kb_coro: '%s' has decided to subscribe now!", name)

    global keyboard_task

    with Subscription(hub=hub, topic=topic) as queue:
        goon = True
        while goon:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=5)
                logger.debug("kb_coro: msg='%s'", msg)

                if is_message_type(msg, TOPICS.COMMON_MESSAGES.EXIT):
                    await _keyboard_stop(name=name)
                    goon = False

                elif is_message_type(msg, TOPICS.KEYBOARD_MESSAGES.START):
                    # msg_start = cast(MsgKeyboardStart, msg)
                    if keyboard_task is None:
                        keyboard_task = asyncio.create_task(
                            _kb_reader_coro(name=name, hub=hub, topic_out=topic_out))

                elif is_message_type(msg, TOPICS.KEYBOARD_MESSAGES.STOP):
                    # msg_stop = cast(MsgKeyboardStop, msg)
                    await _keyboard_stop(name=name)

            except asyncio.TimeoutError:
                # logger.debug("kb_coro: timeout'")
                if keyboard_task is not None and keyboard_task.done():
                    # Should be running and finished - relaunc
                    logger.info(": keyboard_task='%s', done='%s' --> relaunch",
                                keyboard_task,  keyboard_task.done())
                    keyboard_task = asyncio.create_task(
                        _kb_reader_coro(name=name, hub=hub, topic_out=topic_out))


    exit_msg = f"kb_coro '{name}' is shutting down"
    logger.info("%s msg: %s", name, exit_msg)
    return exit_msg
