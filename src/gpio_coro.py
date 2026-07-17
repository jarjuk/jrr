"""Co-routines for GPIO management
"""

import logging

import datetime
import asyncio
from typing import List
from functools import partial

from .publish_subsrcibe import Hub
from .constants import RPI, TOPICS, APP_CONTEXT
from .messages import message_button, message_halt
from .utils import send_dmesg

if APP_CONTEXT.USE_LGPIO:
    from gpiozero import Device, Button
    from gpiozero.pins.lgpio import LGPIOFactory
    Device.pin_factory = LGPIOFactory()
else:
    try:
        from RPi import GPIO
    except ModuleNotFoundError:
        pass


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
    start_now = None

    # LGPIO/GPIO
    if APP_CONTEXT.USE_LGPIO:
        logging.debug("callback: USE_LGPIO button: %s, pressed: %s, now: %s",
                      button, button.is_pressed, now, )
        button_pin = button.pin.number
        if button.is_pressed:
            start_now = now
    else:
        button_pin = button
        if GPIO.input(button):
            # button pressed - start timer
            start_now = now

    # Button pushed+timer started OR released
    if start_now is not None:
        button_long_short[button] = start_now
    else:
        # button relaesed --> create msg
        diff = now - button_long_short[button]
        long_press = diff.total_seconds() > RPI.LONG_PRESS_S
        msg = message_button(
            button_pin,
            long_press=long_press
        )

        logging.debug(
            "callback: button: %s, now: %s, prev: %s diff: %s, long: %s",
            button, now, button_long_short[button], diff, long_press)

    # Something to publish?
    if msg is not None:
        hub.publish(topic, msg)
    # asyncio.run_coroutine_threadsafe(
    #     hub.publish(topic=topic, message=msg), loop)


def _shutdown_input_handler(button, hub: Hub, topic, loop):
    """Shutdown button (=volume knob off).

    Log message to kerner and send shutdown message to 'topic'.
    """

    button_state = None
    if APP_CONTEXT.USE_LGPIO:
        button_state = button.is_pressed
    else:
        button_state = GPIO.input(button)

    logger.warning("_shutdown_input_handler: button='%s', button_state: %s",
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
    if not APP_CONTEXT.USE_LGPIO:
        # Deprecated: using GPIO
        logger.info("gpio_init: setmode GPIO.BCM")
        GPIO.setmode(GPIO.BCM)


def _init_GPIO_old(buttons: List,
                   hub: Hub, topic: str, loop):
    """Depaced version on old os"""
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


def _init_GPIO_new(buttons: List,
                   hub: Hub, topic: str, loop):
    """New version using gpiozero and LGPIOFactory os"""
    button_callback = partial(
        _button_callback_hub_topic, hub=hub, topic=topic, loop=loop)

    for button in buttons:
        logger.info("init_GPIO_buttons: button='%s'", button)
        # GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        btn = Button(
            button,
            pull_up=True,
            bounce_time=0.05
        )

        # init slot for detecting long/short press for button
        button_long_short[button] = 0

        # GPIO.add_event_detect(button, GPIO.BOTH,
        #                       callback=button_callback, bouncetime=50)
        btn.when_pressed = lambda b=btn: \
            button_callback(b)

        btn.when_released = lambda b=btn: \
            button_callback(b)


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
    if APP_CONTEXT.USE_LGPIO:
        _init_GPIO_new(buttons, hub, topic, loop)
    else:
        _init_GPIO_old(buttons, hub, topic, loop)


def _init_GPIO_shutdown_old(button: int, hub: Hub, topic: str, loop):
    GPIO.setup(button, GPIO.IN)
    button_state = GPIO.input(button)
    if button_state:
        logger.warning(
            "init_GPIO_shutdown: button='%s' - expect volume knob opened && GPIO False, got %s ",
            button, button_state)
        return False

    button_callback = partial(
        _shutdown_input_handler, hub=hub, topic=topic, loop=loop)

    GPIO.add_event_detect(
        button, GPIO.RISING,
        callback=button_callback, bouncetime=500)
    return True


# Global init only once
_shutdown_button: Button = None


def _init_GPIO_shutdown_new(button: int, hub: Hub, topic: str, loop):

    global _shutdown_button

    if _shutdown_button is None:
        # Init only once
        _shutdown_button = Button(
            button,
            pull_up=None,
            active_state=False,
            bounce_time=0.05
        )
        logger.info("_init_GPIO_shutdown_new: _shutdown_button='%s' initialized",
                    _shutdown_button)

        button_callback = partial(
            _shutdown_input_handler, hub=hub, topic=topic, loop=loop)

        _shutdown_button.when_released = lambda: button_callback(
            _shutdown_button)

    btn_state = _shutdown_button.is_pressed

    logger.info("_init_GPIO_shutdown_new: btn_state='%s', _shutdown_button:%s",
                btn_state, _shutdown_button)
    return btn_state


def init_GPIO_shutdown(button: int, hub: Hub, topic: str, loop):
    """Init shutdown action shutdown 'button' (=volume knob).

    :return: true if  succesfull
    """
    logger.info("init_GPIO_shutdown: button='%s'", button)
    if APP_CONTEXT.USE_LGPIO:
        return _init_GPIO_shutdown_new(button, hub, topic, loop)
    else:
        return _init_GPIO_shutdown_old(button, hub, topic, loop)


def gpio_close():
    logger.info("Close GPIO_buttons")
    if not APP_CONTEXT.USE_LGPIO:
        # Depcreated using GPIO
        GPIO.cleanup()


async def GPIO_button_coro(name: str, hub: Hub, topic: str):
    logger.info("name: %s - starting", name)
    while True:
        await asyncio.sleep(1)
    logger.info("name: %s - exitig", name)
    return f"{name} - exiting"
