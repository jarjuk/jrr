"""Manage messages
"""

from typing import (Dict, List, cast, Optional, Iterable)
from dataclasses import (dataclass, field, fields, asdict)
import logging

from .constants import TOPICS, COROS, APP_CONTEXT, DSCREEN

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Messages


@dataclass
class MsgRoot:
    """All message MUST have 'message_type'."""
    message_type: str             # All messages have a type


@dataclass
class MsgKeyVal:
    """List element for key,val"""
    key: str
    val: str | None

    @property
    def name(self):
        return self.key

    @property
    def value(self):
        return self.val

    @property
    def strValue(self):
        return "" if self.val is None else self.val


@dataclass
class MsgButton(MsgRoot):
    """"""
    button: int                   # GPIO number
    long_press: bool              # long/short press

    @property
    def short_press(self):
        return not self.long_press


@dataclass
class MsgKey(MsgRoot):
    """"""
    key: str                      # GPIO number

    @property
    def is_nl(self):
        return key == "\n"


@dataclass
class MsgDelay(MsgRoot):
    """"""
    ms: int                       # milli secs to delay


@dataclass
class MsgKeyboardStart(MsgRoot):
    pass


@dataclass
class MsgKeyboardStop(MsgRoot):
    pass


@dataclass
class MsgKeyboardStatus(MsgRoot):
    status: bool


@dataclass
class MsgKeyboardKey(MsgRoot):
    key: str


@dataclass
class MsgStreamer(MsgRoot):
    """Parent class for messages sent to strearem"""
    pass


@dataclass
class MsgStreamerStart(MsgStreamer):
    """Start streaming"""
    url: str                      # Url to start streaming from


@dataclass
class MsgStreamerStop(MsgStreamer):
    """Stop streaming"""
    pass


@dataclass
class MsgStreamerStatusReply(MsgRoot):
    """Reply to status streamer query"""
    status_str: str                   # String status
    running: bool                     # Running/not


@dataclass
class MsgScreen(MsgRoot):
    """Parent class for messages sent to screen."""


@dataclass
class MsgDScreen(MsgScreen):
    """Message with generic (key-val) DScreen content."""
    screen_name: str
    fields: list[MsgKeyVal] = field(default_factory=list)

    @property
    def fieldCount(self):
        return len(self.fields)

    def fieldStrValue(self, name: str) -> str | None:
        """Return string value for 'name' -field. None if no 'name'
        -field not found.
        """
        for i in range(self.fieldCount):
            key_val = self.fields[i]
            if key_val.name == name:
                return key_val.strValue
        return None


@dataclass
class MsgNetwork(MsgRoot):
    """Parent class for network messages."""
    status: bool


@dataclass
class MsgHalt_HaltAck(MsgRoot):
    """Halt message, distinguish source (knob on GPIO input/SIGTEM)

    """
    source: TOPICS.HALT_SOURCE


@dataclass
class MsgExit(MsgRoot):
    """Exit message signals coro to cleanup and exit.

    Distinguishes source (knob on GPIO input/SIGTEM/Message) for
    exiting.

    """
    source: TOPICS.HALT_SOURCE


@dataclass
class MsgScreenUpdate(MsgRoot):
    """Screen full/fast/partial."""

    MODE_FULL = APP_CONTEXT.SCREEN.MODE_FULL          # "full"
    MODE_FAST = APP_CONTEXT.SCREEN.MODE_FAST          # "fast"
    MODE_PARTIAL = APP_CONTEXT.SCREEN.MODE_PARTIAL    # "partial"
    MODE_NONE = APP_CONTEXT.SCREEN.MODE_NONE          # "NOupdate"

    # 'full','fast', 'partial' -mode (or no update)
    mode: str
    name: str | None = None                   # screen element to update partially


@dataclass
class MsgClockUpdate(MsgScreen):
    """Update clock with status spites."""
    network_status: bool
    streaming_status: bool
    keyboard_status: bool
    jrr_version: str


@dataclass
@dataclass
class MsgScreenIcon(MsgScreen):
    """Put icon to screen ."""
    icon: str


@dataclass
class MsgScreenText(MsgScreen):
    """Put 'text' to screen into screen position 'name' (generic)."""
    name: str
    text: str


@dataclass
class MsgScreenError(MsgScreen):
    """Show 'error' and """
    error: str         # short name/classification
    instructions: str  # multiline text


@dataclass
class MsgScreenQuestion(MsgScreen):
    """Show 'error' and """
    title: str         # short name/classification
    question: str      # possibly multiline text
    icon: str          # imagepath to icon to show on screen


@dataclass
class MsgScreenFirmware(MsgScreen):
    """Firmaware version and release notes"""
    header: str        # short name/classification
    version_tag: str   # version tag jrr-0.1.1
    notes: str         # relases notes (multiline)


@dataclass
class MsgScreenNetworkInfo(MsgScreen):
    """Show 'error' and """
    title: str
    sub_title: str
    ssid: str          # SSID of current network connection
    ip: str            # IP adddress on current network co


@dataclass
class MsgScreenConfigHeader(MsgScreen):
    """Configuration message to screen.

    Notice: None values are not updated on screen.

    """
    header: str = None
    sub_header: str = None
    icon: str | None = None


@dataclass
class MsgScreenButtons(MsgScreen):
    """Button labels 1,2,3,4 """
    label1: str
    label2: str
    label3: str
    label4: str


@dataclass
class MsgScreenStatusIcons(MsgScreen):
    """Streaming and network status"""
    network: bool
    streaming: bool
    keyboard: bool


# ------------------------------------------------------------------
# Dispatch message costructor
# Map 'message_type' to dataclasses with message fields
message_constructors = {
    # Control and common messages
    TOPICS.CONTROL_MESSAGES.REBOOT: MsgRoot,
    TOPICS.CONTROL_MESSAGES.HALT_ACK: MsgHalt_HaltAck,
    TOPICS.CONTROL_MESSAGES.HALT: MsgHalt_HaltAck,
    TOPICS.COMMON_MESSAGES.EXIT: MsgExit,
    TOPICS.COMMON_MESSAGES.DELAY: MsgDelay,
    TOPICS.COMMON_MESSAGES.CLOCK_TICK: str,
    TOPICS.COMMON_MESSAGES.PING: str,

    # GPIO messages
    TOPICS.GPIO_MESSAGES.GPIO: MsgButton,

    # NETWORK messages
    TOPICS.NETWORK_MESSAGES.STATUS: MsgNetwork,

    # KEYBOARD messages
    TOPICS.KEYBOARD_MESSAGES.START: MsgKeyboardStart,
    TOPICS.KEYBOARD_MESSAGES.STOP: MsgKeyboardStop,
    TOPICS.KEYBOARD_MESSAGES.STATUS: MsgKeyboardStatus,
    TOPICS.KEYBOARD_MESSAGES.KEY: MsgKeyboardKey,

    # Streamer messages
    TOPICS.STREAMER_MESSAGES.STOP: MsgStreamerStop,
    TOPICS.STREAMER_MESSAGES.START: MsgStreamerStart,
    TOPICS.STREAMER_MESSAGES.STATUS_QUERY: str,
    TOPICS.CONTROL_MESSAGES.STREAMER_STATUS_REPLY: MsgStreamerStatusReply,

    # Screen messages
    TOPICS.SCREEN_MESSAGES.INIT: str,
    TOPICS.SCREEN_MESSAGES.TEST: str,                          # TODO comment out?
    TOPICS.SCREEN_MESSAGES.UPDATE: MsgScreenUpdate,            # full,fast,partial
    TOPICS.SCREEN_MESSAGES.STREAM_ICON: MsgScreenIcon,
    TOPICS.SCREEN_MESSAGES.BUTTON_TXT: MsgScreenButtons,       # label1,2,3,4
    TOPICS.SCREEN_MESSAGES.CLEAR: str,
    TOPICS.SCREEN_MESSAGES.CLOSE: str,
    TOPICS.SCREEN_MESSAGES.CLOCK: MsgClockUpdate,              # update time on clock
    TOPICS.SCREEN_MESSAGES.SLEEP: str,
    TOPICS.SCREEN_MESSAGES.WAKEUP: str,
    TOPICS.SCREEN_MESSAGES.MSG_INFO: MsgScreenText,             # user message
    TOPICS.SCREEN_MESSAGES.SPRITE: MsgScreenStatusIcons,        # status on icon sprite
    # TOPICS.SCREEN_MESSAGES.CONFIG_MENU: MsgScreenText         # pass label in text
    TOPICS.SCREEN_MESSAGES.CONFIG_TITLE: MsgScreenConfigHeader,  # header and selection
    # Dscreen (key-val) content
    TOPICS.SCREEN_MESSAGES.DSCREEN: MsgDScreen,
    TOPICS.SCREEN_MESSAGES.ERROR: MsgScreenError,               # Some sort of an error
    TOPICS.SCREEN_MESSAGES.QUESTION: MsgScreenQuestion,         # Confirmation question
    # Firmware w. release notes
    TOPICS.SCREEN_MESSAGES.FIRMAWRE: MsgScreenFirmware,
    TOPICS.SCREEN_MESSAGES.NETWORK_INFO: MsgScreenNetworkInfo,  # Wifi info
}


def message_create(
        d: Dict | None = None,
        message_type: str | None = None
) -> MsgRoot:
    """Construct message of type 'message_type' with properties 'd'.

    Details
    ----

    Expect message_type either in 'd' or as 'message_type' paramater.

    Dispatches contructor using 'message_constructors' -dictionary.

    Parameters
    ----
    :d: dict mapping **kwvalue for message constructor


    Return
    -----

    Object from MsgRoot hierarchy (or from string). Possibly 'str' for
    simple messages.

    """
    if d is None:
        d = {}

    # query type of message
    class_query = message_type if message_type is not None else d["message_type"]
    msg_class = message_constructors[class_query]

    # instantiate 'message' for 'msg_class'
    if msg_class.__name__ == str.__name__:
        # very simple message - just string property - no dict values
        # needed
        message = msg_class(class_query)
    else:
        # call constructor 'msg_class' with 'd' -**kwargs.
        try:
            d["message_type"] = class_query
            message = msg_class(**d)
        except TypeError as e:
            e.add_note(
                f"Error in {message_type=}," +
                f"fields {[f for f in dir(msg_class) if not f.startswith('_')]}")
            raise

    # print(f"message_create: {message=}, {msg_class=}, {class_query=}")

    return message

# ------------------------------------------------------------------
# Message reflaction and interpretation


def is_message_type(msg: str | MsgRoot, message_type: str | List[str]) -> bool:
    """True if 'msg' is of 'message_type' -type."""
    if isinstance(message_type, str):
        message_type = [message_type]
    if isinstance(msg, str):
        return msg in message_type
    else:
        root_message = cast(MsgRoot, msg)
        return root_message.message_type in message_type


def message_types() -> List[str]:
    """List of messagetypes."""
    msg_types = [t for t in message_constructors.keys()]
    return msg_types


def message_keys(message_type: str) -> List[str]:
    """List of fields in 'message_type' -message."""
    msg_class = message_constructors[message_type]
    keys = [f.name for f in fields(msg_class)]
    return keys


def message_props(msg) -> Dict:
    """Return key-value dictionary for 'msg' excluding 'message_type'."""
    message_props = asdict(msg)
    del message_props["message_type"]
    return message_props


# ------------------------------------------------------------------
# Some fixed message


def message_screen_update(mode=MsgScreenUpdate.MODE_FULL) -> MsgRoot | str:
    """Update screen in 'mode'."""
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.UPDATE,
        d={
            "mode": mode
        })
    return msg


def message_info(line1: str) -> MsgScreenText:
    """Construct two info line message."""
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.MSG_INFO,
        d={
            "name": COROS.Screen.ENTRY_MSG_L1,
            "text": line1,
        })
    msg_text = cast(MsgScreenText, msg)
    logger.debug("message_info: msg_text: %s", msg_text)
    return msg_text


def message_screen_sleep() -> MsgRoot | str:
    """Put screen into sleep."""
    msg = message_create(message_type=TOPICS.SCREEN_MESSAGES.SLEEP,)
    return msg


def message_streamer_start(url: str) -> MsgStreamerStart:
    """Message to start streaming.

    :url: url to start streaming to

    """
    msg = message_create(
        message_type=TOPICS.STREAMER_MESSAGES.START,
        d={
            "url": url,
        }
    )
    msg_streamer = cast(MsgStreamerStart, msg)
    return msg_streamer


def message_streamer_stop() -> MsgStreamerStop:
    """Message to stop streaming.

    """
    msg = message_create(
        message_type=TOPICS.STREAMER_MESSAGES.STOP,
    )
    msg_streamer = cast(MsgStreamerStop, msg)
    return msg_streamer


def message_keyboard_start() -> MsgKeyboardStart:
    """Message to start reading keyboard

    TODO: fix implementation
    """
    msg = message_create(
        message_type=TOPICS.KEYBOARD_MESSAGES.START
    )
    msg_kb = cast(MsgKeyboardStart, msg)
    return msg_kb


def message_keyboard_stop() -> MsgKeyboardStop:
    """Message to stop reading keyboard
    """
    msg = message_create(
        message_type=TOPICS.KEYBOARD_MESSAGES.STOP
    )
    msg_kb = cast(MsgKeyboardStop, msg)
    return msg_kb


def message_screen_stream_icon(icon: str) -> MsgScreenIcon:
    """Message to set stream icon.

    :icon: name of stream icon file 

    """
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.STREAM_ICON,
        d={
            "icon": icon
        }
    )
    msg_icon = cast(MsgScreenIcon, msg)
    return msg_icon


def message_screen_close() -> MsgRoot | str:
    """Clear display content, (keep data), sleep.

    Do whatever it takes (may flash quite a lot)

    """
    msg = message_create(message_type=TOPICS.SCREEN_MESSAGES.CLOSE,)
    return msg


def message_screen_refresh() -> MsgRoot | str:
    """Refresh screen."""
    msg = message_create(message_type=TOPICS.SCREEN_MESSAGES.WAKEUP,)
    return msg


def message_network_status(status: bool) -> MsgNetwork:
    """Network status message."""
    msg = message_create(message_type=TOPICS.NETWORK_MESSAGES.STATUS,
                         d={
                             "status": status
                         })

    msg_status = cast(MsgNetwork, msg)
    return msg_status


def message_status_icons(network: bool,
                         streaming: bool,
                         keyboard: bool) -> MsgScreenStatusIcons:
    """Message for status sprite."""
    msg = message_create(message_type=TOPICS.SCREEN_MESSAGES.SPRITE, d={
        "network": network,
        "streaming": streaming,
        "keyboard": keyboard,
    })
    msg_icons = cast(MsgScreenStatusIcons, msg)
    return msg_icons


def message_clock_update(
        network_status: bool,
        streaming_status: bool,
        keyboard_status: bool,
        jrr_version: str,
) -> MsgClockUpdate:
    """Message to update clock on screen, and possibly
    'refresh_display'.

    :network_status: ok/nok

    :streaming_status: playing/not playing

    :keyboard_status: connected/not connected

    """
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.CLOCK,
        d={
            "network_status": network_status,
            "streaming_status": streaming_status,
            "keyboard_status": keyboard_status,
            "jrr_version": jrr_version,
        })
    msg_clock = cast(MsgClockUpdate, msg)
    return msg_clock


def message_button_labels(
        label1: str,
        label2: str,
        label3: str,
        label4: str) -> MsgScreenButtons:
    """Message to set button labels."""
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.BUTTON_TXT,
        d={
            "label1": label1,
            "label2": label2,
            "label3": label3,
            "label4": label4,
        })
    msg_buttons = cast(MsgScreenButtons, msg)
    return msg_buttons


def message_button(button: int, long_press: bool):
    """Create button message for 'button' pressed 'short_or_long'.

    :return: MsgButton
    """
    # return f"{button}={short_or_long}"
    msg = message_create(message_type=TOPICS.GPIO_MESSAGES.GPIO,
                         d={
                             "button": button,
                             "long_press": long_press,
                         })
    return msg


def message_config_title(
        title: str,
        sub_title: str | None = None,
        imagepath: str | None = "",
) -> MsgScreenConfigHeader:
    """Create message to set config menu title.

    :icon: optional image to show on screen

    :return: MsgScreenConfigHeader
    """
    if sub_title is None:
        sub_title = ""
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.CONFIG_TITLE,
        d={
            DSCREEN.CONFIG_TITLE_OVERLAY.HEADER: title.rstrip(),
            DSCREEN.CONFIG_TITLE_OVERLAY.SUB_HEADER: sub_title.rstrip(),
            DSCREEN.CONFIG_TITLE_OVERLAY.ICON: imagepath,
        })

    msg_title = cast(MsgScreenConfigHeader, msg)
    return msg_title


def message_key(key: str) -> MsgKey:
    """Key pressed'.

    :return: MsgKey
    """
    # return f"{button}={short_or_long}"
    msg = message_create(message_type=TOPICS.KEYBOARD_MESSAGES.KEY,
                         d={
                             "key": key,
                         })
    msg_key = cast(MsgKey, msg)
    return msg_key


def message_dscreen(screen_name: str, key_values: Iterable) -> MsgDScreen:
    """Message to pass Dscreen fieldValues to screen-coro'.

    :return: MsgDScreen
    """

    msg = message_create(message_type=TOPICS.SCREEN_MESSAGES.DSCREEN,
                         d={
                             "screen_name": screen_name
                         }
                         )
    msg_dscreen = cast(MsgDScreen, msg)
    for k, v in key_values:
        msg_dscreen.fields.append(MsgKeyVal(key=k, val=v))

    return msg_dscreen


def message_halt(source: TOPICS.HALT_SOURCE) -> MsgHalt_HaltAck:
    msg = message_create(message_type=TOPICS.CONTROL_MESSAGES.HALT,
                         d={
                             "source": source
                         }
                         )
    msg_halt = cast(MsgHalt_HaltAck, msg)

    return msg_halt


def message_halt_ack(source: TOPICS.HALT_SOURCE) -> MsgHalt_HaltAck:
    msg = message_create(message_type=TOPICS.CONTROL_MESSAGES.HALT_ACK,
                         d={
                             "source": source
                         }
                         )
    msg_halt_ack = cast(MsgHalt_HaltAck, msg)

    return msg_halt_ack


def message_exit(source: TOPICS.HALT_SOURCE) -> MsgExit:
    msg = message_create(
        message_type=TOPICS.COMMON_MESSAGES.EXIT,
        d={
            "source": source
        }
    )
    msg_exit = cast(MsgExit, msg)

    return msg_exit


def message_panik():
    msg = message_create(
        message_type=TOPICS.CONTROL_MESSAGES.REBOOT,
    )

    return msg


def message_error(error: str, instructions: str | None) -> MsgScreenError:
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.ERROR,
        d={
            "error": error,
            "instructions": instructions,
        }
    )
    msg_error = cast(MsgScreenError, msg)
    return msg_error


def message_question(title: str, question: str, imagepath: str | None = None) -> MsgScreenQuestion:
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.QUESTION,
        d={
            "title": title,
            "question": question,
            TOPICS.QUESTION_MESSAGE.ICON: imagepath,
        }
    )
    msg_question = cast(MsgScreenQuestion, msg)
    return msg_question


def message_firmware(title: str, version_tag: str, notes: str) -> MsgScreenFirmware:
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.FIRMAWRE,
        d={
            "header": title,
            "version_tag": version_tag,
            "notes": notes
        }
    )
    msg_firmware = cast(MsgScreenFirmware, msg)
    return msg_firmware


def message_network_info(
        title: str,
        sub_title: str,
        ssid: str,
        ip: str,
) -> MsgScreenNetworkInfo:
    msg = message_create(
        message_type=TOPICS.SCREEN_MESSAGES.NETWORK_INFO,
        d={
            DSCREEN.NETWORK_INFO_OVERLAY.TITLE: title,
            DSCREEN.NETWORK_INFO_OVERLAY.SUB_TITLE: sub_title,
            DSCREEN.NETWORK_INFO_OVERLAY.SSID: ssid,
            DSCREEN.NETWORK_INFO_OVERLAY.IP: ip,
        }
    )
    msg_network_info = cast(MsgScreenNetworkInfo, msg)
    return msg_network_info
