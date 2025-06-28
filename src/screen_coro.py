"""Coroutine mananing e-paper display"""

from typing import (cast, Any, Dict, Callable)
from dataclasses import asdict, fields
import os
import time
import logging
import asyncio
# from PIL import Image, ImageFont, ImageDraw


from .publish_subsrcibe import Hub
from .reader_coro import reader_coro
from .config import app_config
from .constants import RPI
from .utils import delegates


from .constants import (TOPICS, COROS, APP_CONTEXT, DSCREEN)
from .messages import (is_message_type, message_props, MsgScreenUpdate,
                       MsgScreenIcon, MsgScreenText, MsgClockUpdate, MsgRoot,
                       MsgDelay, MsgScreenButtons, MsgDScreen, MsgExit,
                       message_create, message_halt_ack, message_panik,
                       )

from .screen import Screen, overlay_names


# ------------------------------------------------------------------
# Resolve display used
from .tft_ili9486 import TFT_DRIVER

# ------------------------------------------------------------------
# Add driver to Screen


@delegates([""], to="screen")
class ScreenDriver():
    """Use 'driver' to output 'screen.img' to physical display.

    :awake: maintains display state (awake not awake)
    """

    def __init__(self, screen: Screen, driver: TFT_DRIVER):
        """Set screen and set driver -delegages."""
        self.screen = screen
        self.driver = driver
        self.awake = False         # display blank/not started
        self._nro = 0

    # # screen + driver delegates
    # def remove_entry(self, name: str):
    #     self.screen.remove_entry(name=name)

    def xor_alternatives(self, name: str):
        """Enable 'name' in overlays, disable otherhers."""

        # Only on these active
        # only_one = [COROS.Screen.ENTRY_STREAM_ICON,
        #             COROS.Screen.ENTRY_CONFIG_MENU,
        #             COROS.Screen.ENTRY_CONFIG,
        #             ]
        only_one = overlay_names()
        # Thes should be removed from screen
        disables = [n for n in only_one if n != name]

        logger.debug("xor_alternatives: activete name='%s'", name)
        self.screen.activate_entry(
            name=name,
            active=True)

        for other in disables:
            logger.debug("xor_alternatives: disable other='%s'", other)
            self.screen.activate_entry(
                name=other,
                active=False)

    async def add_or_update(
            self,
            name: str,
            entry_props: Dict,
            mode: str,
    ):
        """Add 'entry_props' on screen_entry 'name' to 'self.screen'."""
        logger.debug("ScreenDriver.add_or_update_entry: name: '%s', entry_props='%s'",
                     name, entry_props)
        updated = self.screen.add_or_update_entry(
            name=name, entry_props=entry_props
        )
        logger.debug("ScreenDriver.add_or_update_entry: updated='%s'", updated)
        if (mode == APP_CONTEXT.SCREEN.MODE_FULL or updated) and self.awake:
            logger.info(
                "ScreenDriver.add_or_update: name='%s', mode='%s' - updated=%s",
                name, mode, updated)

            await self.update(mode=mode, name=name)
        return updated

    # driver delegates - operations

    async def init(self) -> bool:
        """Init display (called before add epd.actions).

        Opposite 'full_close'

        Return: True if init actually done.
        """
        logger.debug("ScreenDriver.init")
        await self.driver.init()
        self.awake = True
        return True

    async def clear(self, keep_content: bool = True):
        """Clear display, maybe 'keep_content'."""
        logger.debug("ScreenDriver.clear: keep_content='%s'", keep_content)
        if not keep_content:
            self.screen.clear()
        await self.driver.Clear()

    async def sleep(self):
        """Put display to screen, wake_up opposite action .."""
        logger.info("ScreenDriver.sleep: self.awake='%s'", self.awake)
        await self.driver.Clear()
        # await self.driver.sleep()
        self.awake = False

    async def wake_up(self):
        """Put display to screen. (Init required to awaken to display)."""
        logger.info("ScreenDriver.wake_up: self.awake='%s'", self.awake)
        await self.driver.wake_up()
        self.awake = True

    async def update(self, mode: str, name: str | None = None):
        """Update 'screen.img' on display in 'mode'

        :mode: full/fast/partial/none, where full construct image
        buffer fully, 'partial' updates only named entry on image
        buffer.

        :name: screen entry to update in image buffer (in parial
        -mode.)

        """
        logger.debug(
            "ScreenDriver.update: self.awake='%s', mode=%s, name='%s'",
            self.awake, mode, name)

        # Awake if not in sleep (=not awake)
        if not self.awake:
            await self.wake_up()
        if mode == MsgScreenUpdate.MODE_FULL:
            self.screen.update_full()
            img = self.screen.img
            await self.driver.display(img, x0=0, y0=0)
        elif mode == MsgScreenUpdate.MODE_PARTIAL:
            self.screen.update_partial(name=name)
            img = self.screen.img
            await self.driver.display(img, x0=0, y0=0)
        elif mode == MsgScreenUpdate.MODE_NONE:
            pass
        else:
            raise NotADirectoryError(f"update mode %s - not implemented")

    async def full_close(self):
        """Clear display and content, goto sleep -mode."""
        logger.debug("ScreenDriver.full_close: self.awake='%s'", self.awake)
        await self.driver.close()
        self.awake = False


# ------------------------------------------------------------------
# Module state
logger = logging.getLogger(__name__)
screen_driver: ScreenDriver | None = None

# ------------------------------------------------------------------
# Actions -method for receiving message from topic

# pylint: disable=too-many-branches
# pylint: disable=too-many-statements


async def _screen_action(msg: Any, hub: Hub):
    """Async actions to work on receiving 'msg' from 'topic'."""
    logger.debug("_screen_action: start-msg: %s", msg)

    global screen_driver
    if screen_driver is None:
        size = (APP_CONTEXT.SCREEN.WIDTH,
                APP_CONTEXT.SCREEN.HEIGHT)
        logger.info("_screen_action: init screen: size='%s'", size)
        display_driver = TFT_DRIVER(
            dc=RPI.ILI9486.DC_PIN,
            spi_bus=RPI.ILI9486.SPI_BUS,
            spi_device=RPI.ILI9486.SPI_DEVICE,
            rst=RPI.ILI9486.RST_PIN, )
        screen_driver = ScreenDriver(
            screen=Screen(size=size),
            driver=display_driver
        )

    def _msg_to_overlay_props(
            msg: MsgRoot,
            keymapper: Callable[[str], str] = lambda k: f"{k}.text") -> Dict[str, str]:
        """Map message fields (excluding message_type) to dict.

        :keymapper: callable to map message key to dict keys.

        """

        overlay_props = {
            keymapper(k): v
            for k, v in asdict(msg).items() if k not in ["message_type"]
        }
        return overlay_props

    goon = True
    if is_message_type(msg, TOPICS.SCREEN_MESSAGES.INIT):
        await screen_driver.init()

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.CLEAR):
        # clear 'screen' and data
        await screen_driver.clear(keep_content=False)

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.SLEEP):
        logger.info("%s: sleep-msg='%s'", TOPICS.SCREEN_MESSAGES.SLEEP, msg)
        # await screen_driver.clear(keep_content=True)
        # await screen_driver.update(mode=MsgScreenUpdate.MODE_FULL)
        # await asyncio.sleep(0.1)
        await screen_driver.sleep()

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.WAKEUP):
        # Refresh screen = awake
        logger.info("%s: awake-msg='%s'", TOPICS.SCREEN_MESSAGES.WAKEUP, msg)
        await screen_driver.wake_up()
        await screen_driver.update(mode=MsgScreenUpdate.MODE_FULL)

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.CLOSE):
        # full-clear && sleep
        raise NotImplementedError
        # await screen_driver.clear(keep_content=True)
        # await asyncio.sleep(0.1)
        # TODO: sleep needed or NOT
        # await screen_driver.sleep()
        # for _ in range(2):
        #     # must clear twice to actually clear the display
        #     await screen_driver.clear(keep_content=True)
        #     await screen_driver.sleep()

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.UPDATE):
        # msg.mode --> update display fully/partially
        msg_show = cast(MsgScreenUpdate, msg)
        logger.debug("%s: msg_show: %s, partial=%s",
                     TOPICS.SCREEN_MESSAGES.UPDATE,
                     msg_show,
                     msg_show.mode
                     )
        await screen_driver.update(mode=msg_show.mode, name=msg_show.name)

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.BUTTON_TXT):

        msg_button = cast(MsgScreenButtons, msg)
        logger.debug("%s-msg , msg='%s'",
                     TOPICS.SCREEN_MESSAGES.BUTTON_TXT,
                     msg_button,
                     )
        # add button labels (no update)
        updated = False
        updated |= await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_B1,
            entry_props={"text": msg_button.label1},
            mode=MsgScreenUpdate.MODE_NONE,
        )
        updated |= await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_B2,
            entry_props={"text": msg_button.label2},
            mode=MsgScreenUpdate.MODE_NONE,
        )
        logger.info("update-2: updated='%s'", updated)
        updated |= await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_B3,
            entry_props={"text": msg_button.label3},
            mode=MsgScreenUpdate.MODE_NONE,
        )
        updated |= await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_B4,
            entry_props={"text": msg_button.label4},
            mode=MsgScreenUpdate.MODE_NONE,
        )
        # Icons infron of key labels
        updated |= await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_ICON_KEY1,
            entry_props={"imagepath": APP_CONTEXT.ICON_SPRITE_FILE_PATH},
            mode=MsgScreenUpdate.MODE_NONE,
        )
        updated |= await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_ICON_KEY2,
            entry_props={"imagepath": APP_CONTEXT.ICON_SPRITE_FILE_PATH},
            mode=MsgScreenUpdate.MODE_NONE,
        )
        # after all buttons do full update
        if updated:
            logger.info("_screen_action: msg_button='%s' - updated",
                        msg_button)
            await screen_driver.update(mode=MsgScreenUpdate.MODE_FULL)

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.SPRITE):

        # find image sprite in a fixed path, take sprite status from
        # message
        props = {
            "imagepath": APP_CONTEXT.ICON_SPRITE_FILE_PATH
        } | message_props(msg)
        updated = await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_SPRITE_ICONS,
            entry_props=props,
            mode=MsgScreenUpdate.MODE_PARTIAL,
        )
        if updated:
            logger.info("%s: msg='%s'", COROS.Screen.ENTRY_SPRITE_ICONS, msg)

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.MSG_INFO):

        msg_text = cast(MsgScreenText, msg)
        logger.debug("%s-msg   name=%s, text='%s'",
                     TOPICS.SCREEN_MESSAGES.MSG_INFO,
                     msg_text.name,
                     msg_text.text,
                     )
        # Put on screen && partial update
        updated = await screen_driver.add_or_update(
            name=msg_text.name,
            entry_props={"text": msg_text.text},
            mode=MsgScreenUpdate.MODE_PARTIAL,
        )

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.CLOCK):
        # Add/update current time on screen entry 'ENTRY_CLOCK'
        msg_clock: MsgClockUpdate = cast(MsgClockUpdate, msg)
        hh_mi = time.strftime("%H:%M:%S")
        logger.debug("clock: hh_mi= %s", hh_mi)

        # Allow clock message - but update only screen state if not awake
        update_mode = MsgScreenUpdate.MODE_PARTIAL if screen_driver.awake else MsgScreenUpdate.MODE_NONE

        # Time updated
        updated = False
        updated = await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_CLOCK,
            entry_props={"text": hh_mi},
            mode=update_mode,
        )

        # Sprite icongs
        props = {
            "imagepath": APP_CONTEXT.ICON_SPRITE_FILE_PATH,
            "network": msg_clock.network_status,
            "streaming": msg_clock.streaming_status,
            "keyboard": msg_clock.keyboard_status,
        }
        updated = await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_SPRITE_ICONS,
            entry_props=props,
            mode=update_mode,
        )

        # MSG_L1 = ""
        updated |= await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_MSG_L1,
            entry_props={
                "text": ""
            },
            mode=update_mode,
        )

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.ERROR):
        logger.debug("ERROR: msg='%s'", msg)

        # Only one active from alternatives
        screen_driver.xor_alternatives(
            name=COROS.Screen.ENTRY_ERROR_OVL)

        # _overlay_props = {
        #     f"{k}.text": v
        #     for k, v in asdict(msg).items() if k not in ["message_type"]
        # }
        _overlay_props = _msg_to_overlay_props(msg)

        await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_ERROR_OVL,
            entry_props=_overlay_props,
            mode=MsgScreenUpdate.MODE_FULL,
        )

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.QUESTION):
        logger.debug("QUESTION: msg='%s'", msg)

        # Only one active from alternatives
        screen_driver.xor_alternatives(
            name=COROS.Screen.ENTRY_QUESTION_OVL)

        def _key2prop(k) -> str:
            """Icon field tells point to icon file to show."""
            if k == TOPICS.QUESTION_MESSAGE.ICON:
                return f"{k}.imagepath"
            return f"{k}.text"

        _overlay_props = _msg_to_overlay_props(msg, keymapper=_key2prop)

        await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_QUESTION_OVL,
            entry_props=_overlay_props,
            mode=MsgScreenUpdate.MODE_FULL,
        )

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.NETWORK_INFO):
        logger.debug("NETWORK_INFO: msg='%s'", msg)

        # Only one active from alternatives
        screen_name = COROS.Screen.ENTRY_NETWORK_INFO_OVL
        screen_driver.xor_alternatives(
            name=screen_name)

        _overlay_props = _msg_to_overlay_props(msg)

        await screen_driver.add_or_update(
            name=screen_name,
            entry_props=_overlay_props,
            mode=MsgScreenUpdate.MODE_FULL,
        )

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.CONFIG_TITLE):
        # Show 'msg.text' on screen entry 'msg.name'
        logger.debug("CONFIG_MENU: msg='%s'", msg)

        # Only one active from alternatives
        screen_driver.xor_alternatives(
            name=COROS.Screen.ENTRY_CONFIG_TITLE)

        def _key2prop(k) -> str:
            """Icon field tells point to icon file to show."""
            if k == TOPICS.CONFIG_TITLE_MESSAGE.ICON:
                return f"{k}.imagepath"
            return f"{k}.text"

        # 'msg_field'.text
        _overlay_props = _msg_to_overlay_props(msg, keymapper=_key2prop)
        logger.debug("CONFIG_TITLE: _overlay_props='%s'", _overlay_props)

        await screen_driver.add_or_update(
            name=COROS.Screen.ENTRY_CONFIG_TITLE,
            entry_props=_overlay_props,
            mode=MsgScreenUpdate.MODE_FULL,
        )

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.DSCREEN):
        # Show 'msg.text' on screen entry 'msg.name'
        logger.debug("SCREEN_MESSAGES.DSCREEN: msg='%s'", msg)
        msg_dscreen = cast(MsgDScreen, msg)

        # Notice: not all message fields
        _overlay_props = {
            f"{kv.key}.text": kv.val
            for kv in msg_dscreen.fields
        }

        # Only one active from alternatives
        screen_driver.xor_alternatives(
            name=msg_dscreen.screen_name)

        await screen_driver.add_or_update(
            name=msg_dscreen.screen_name,
            entry_props=_overlay_props,
            mode=MsgScreenUpdate.MODE_FULL,
        )

    elif is_message_type(msg, TOPICS.SCREEN_MESSAGES.STREAM_ICON):
        # Put stream icon to screen
        msg_icon = cast(MsgScreenIcon, msg)
        if len(msg_icon.icon) == 0:
            # TODO: disable screen here (may not needed?)
            screen_driver.screen.activate_entry(
                name=COROS.Screen.ENTRY_STREAM_ICON, active=False)

            # screen_driver.remove_entry(
            #     name=COROS.Screen.ENTRY_STREAM_ICON,
            # )
            # await screen_driver.update(mode=MsgScreenUpdate.MODE_FULL)

        else:
            # add or update screen
            screen_driver.xor_alternatives(
                name=COROS.Screen.ENTRY_STREAM_ICON)

            imagepath = os.path.join(app_config.icon_directory, msg_icon.icon)
            logger.debug("%s:  icon: %s, imagepath=%s",
                         TOPICS.SCREEN_MESSAGES.STREAM_ICON,
                         msg_icon.icon,
                         imagepath,
                         )

            # Adds: ScreenEntryImage, default
            await screen_driver.add_or_update(
                name=COROS.Screen.ENTRY_STREAM_ICON,
                entry_props={"imagepath": imagepath},
                mode=MsgScreenUpdate.MODE_PARTIAL,
            )

    elif is_message_type(msg, TOPICS.COMMON_MESSAGES.CLOCK_TICK):
        raise NotImplementedError(
            f"message {TOPICS.COMMON_MESSAGES.CLOCK_TICK}", )

    elif is_message_type(msg, TOPICS.COMMON_MESSAGES.EXIT):
        msg_exit = cast(MsgExit, msg)
        await screen_driver.full_close()
        # Allow all other coros to EXIT
        await asyncio.sleep(0.5)
        hub.publish(TOPICS.CONTROL,
                    message_halt_ack(source=msg_exit.source))
        # exit
        goon = False

    elif is_message_type(msg, TOPICS.COMMON_MESSAGES.PING):
        # # Application init - reply PING to CONTROL topic
        # await screen.update(mode=MsgScreenUpdate.MODE_FULL)

        # Application init - reply PING to CONTROL topic (assume that
        # screen content all there)
        hub.publish(
            topic=TOPICS.CONTROL,
            message=message_create(message_type=TOPICS.COMMON_MESSAGES.PING)
        )

    else:
        logging.warning("_screen_action: unknown msg: %s", msg)

    return goon

# ------------------------------------------------------------------
# Plumb _screen_action with framework


async def screen_coro(
        name: str,
        hub: Hub,
        topic: str,
):
    """Co-routine for managing  epaper display."""
    logger.info(
        "screen_coro: start name='%s', listen to topic '%s'", name, topic)
    try:
        await reader_coro(name=name, hub=hub, topic=topic, action=_screen_action)
    except Exception as ex:
        logger.error(f"{ex}")
        logger.exception(f"screen_coro got exception {ex}")
        hub.publish(TOPICS.CONTROL, message_panik())
        raise
    exit_msg = f"{name} - exiting"
    logger.info("exit_msg: %s", exit_msg)
    return exit_msg


def screen_close():
    """Hardware close on display."""
