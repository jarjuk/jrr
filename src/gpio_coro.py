"""Co-routines for GPIO management
"""
try:
    from RPi import GPIO
except ModuleNotFoundError:
    pass


import logging

import datetime
import asyncio
from typing import List
from functools import partial

from .publish_subsrcibe import Hub
from .constants import RPI, TOPICS
from .messages import message_button, message_halt
from .utils import send_dmesg

# semafore = asyncio.Semaphore(0)
# semafore_msg = bytearray(200)

# ------------------------------------------------------------------
# Globals

# slot for detecting long/short press for button
button_long_short = {}
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------

# async def publish_message(hub: Hub, topic: str, msg: str):
#     """A co-routine for publishing 'msg' on 'topic' on message
#     controller 'hub'."""
#     print(f"publish_message: {topic=}, {msg=}")

#     hub.publish(topic, msg)
#     await asyncio.sleep(0.1)


# async def publish_message(hub: Hub, topic: str, msg: str):
#     """A co-routine for publishing 'msg' on 'topic' on message
#     controller 'hub'."""
#     global semafore_msg
#     semafore_msg = msg
#     semafore.release()


def _button_callback_hub_topic(button, hub: Hub, topic, loop):
    """Send message on 'topic' on data controller 'hub'."""
    msg = None
    now = datetime.datetime.now()
    if not GPIO.input(button):
        # button pressed - start timer
        button_long_short[button] = now
    else:
        # button relaesed --> create msg
        diff = now - button_long_short[button]
        msg = message_button(
            button,
            long_press=diff.total_seconds() > RPI.LONG_PRESS_S
        )

        logging.debug("callback: button: %s, now: %s, prev: %s diff: %s",
                      button, now, button_long_short[button], diff)

    # Something to publish?
    if msg is not None:
        hub.publish(topic, msg)
    # asyncio.run_coroutine_threadsafe(
    #     hub.publish(topic=topic, message=msg), loop)


def _shutdown_input_handler(button, hub: Hub, topic, loop):
    """Shutdown button (=volume knob off).

    Log message to kerner and send shutdown message to 'topic'.
    """

    button_state = GPIO.input(button)

    logger.warning("_button_shutdown: button='%s', button_state: %s",
                   button, button_state)
    send_dmesg(f"{__file__}: Shudown starting")
    hub.publish(
        topic=topic,
        message=message_halt(source=TOPICS.HALT_SOURCE.GPIO)
    )


# ------------------------------------------------------------------
# Init


def gpio_init():
    """Common init for all GPIO stuff."""
    logger.info("gpio_init: setmode GPIO.BCM")
    GPIO.setmode(GPIO.BCM)


def init_GPIO_buttons(buttons: List, hub: Hub, topic: str, loop
                      ):
    """Initialize GPIO buttons.

    Details
    ----
    Buttons using pull up i.e. they when pushed input pin is grounded. 

    Parameters
    ----

    :buttons: List of input pins (BCM numbering) for push buttons.

    :topic: where message is send

    :hub: publish subscriber data controller

    :loop: asyncio controller loopu

    Return
    -----

    """

    # GPIO.setmode(GPIO.BCM)
    button_callback = partial(
        _button_callback_hub_topic, hub=hub, topic=topic, loop=loop)
    for button in buttons:
        logger.info("init_GPIO_buttons: button='%s'", button)
        GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # init slot for detecting long/short press for button
        button_long_short[button] = 0
        GPIO.add_event_detect(button, GPIO.BOTH,
                              callback=button_callback, bouncetime=50)


def init_GPIO_shutdown(button: int, hub: Hub, topic: str, loop):
    """Init shutdown action shutdown 'button' (=volume knob)."""
    button_callback = partial(
        _shutdown_input_handler, hub=hub, topic=topic, loop=loop)

    logger.info("init_GPIO_shutdown: button='%s'", button)
    GPIO.setup(button, GPIO.IN)
    GPIO.add_event_detect(
        button, GPIO.BOTH,
        callback=button_callback, bouncetime=50)


def gpio_close():
    logger.info("Close GPIO_buttons")
    GPIO.cleanup()


async def GPIO_button_coro(name: str, hub: Hub, topic: str):
    logger.info("name: %s - starting", name)
    while True:
        await asyncio.sleep(1)
    logger.info("name: %s - exitig", name)
    return f"{name} - exiting"
