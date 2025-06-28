"""Keyboard utilities."""

import sys
import evdev
import logging
import asyncio
from typing import Tuple

logger = logging.getLogger(__name__)

BS = "<BACKSPACE>"


def _list_devices():
    # List all input devices
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    # print(f"{devices=}")
    return devices


def find_keyboard(keyboard_name) -> evdev.InputDevice:
    """Find your input device with 'keyboard_name'."""
    #
    devices = _list_devices()
    kb_dev = None
    for device in devices:
        logger.info("device.path='%s', device.name=%s, device.phys=%s, looking for '%s'",
                    device.path, device.name, device.phys, keyboard_name)
        if (device.name == keyboard_name or
                device.name.endswith(keyboard_name)
            ):
            kb_dev = device
            logger.info("found keyboard kb_dev='%s'", kb_dev)

    logger.info("Found: kb_dev='%s'", kb_dev)
    return kb_dev

# ------------------------------------------------------------------
# async generators


async def read_raw_keyboard_gen(keyboard: evdev.InputDevice):
    """Generator yielding key events for key presson on 'keyboard'."""
    async for event in keyboard.async_read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            key_event = evdev.categorize(event)
            # print(f"{type(key_event)=}, {key_event=}")
            # print(f"{key_event.scancode=}")
            # print(f"{key_event.keycode=}")
            # print(f"{key_event.key_up=}")
            # print(f"{key_event.key_down=}")
            # print(f"{key_event.key_hold=}")

            yield key_event


async def read_keyboard_gen(keyboard: evdev.InputDevice):
    """Generator yielding character presses on QWERTY 'keyboard'.

    Kudos: ChatGPT
    """

    shift_pressed = False  # Track shift state for capital letters and special characters

    # Define a mapping for special characters when shift is pressed
    shift_map = {
        "1": "!",
        "2": "@",
        "3": "#",
        "4": "$",
        "5": "%",
        "6": "^",
        "7": "&",
        "8": "*",
        "9": "(",
        "0": ")",
        "-": "_",
        "=": "+",
        "[": "{",
        "]": "}",
        "\\": "|",
        ";": ":",
        "'": "\"",
        ",": "<",
        ".": ">",
        "/": "?",
        "`": "~",
        "MINUS": "_",
        "EQUAL": "+",
    }

    async for key_event in read_raw_keyboard_gen(keyboard=keyboard):
        # key_event = evdev.KeyEvent(event)  # Categorize the event
        key_code = key_event.keycode.replace("KEY_", "")  # Get the key name
        # logger.debug("key_code='%s'", key_code)

        if key_event.keystate == evdev.KeyEvent.key_down:  # Key pressed
            if key_code in ["LEFTSHIFT", "RIGHTSHIFT"]:
                shift_pressed = True
            elif key_code.isalpha() and len(key_code) == 1:  # Alphabet keys
                if shift_pressed:
                    kb_character = key_code.upper()  # Uppercase letters
                else:
                    kb_character = key_code.lower()  # Lowercase letters
                yield kb_character
            elif key_code.isdigit() or key_code in shift_map.keys():  # Numbers and symbols
                if shift_pressed and key_code in shift_map:
                    # Shift-modified character
                    kb_character = shift_map[key_code]
                else:
                    kb_character = key_code
                yield kb_character
            else:
                # Handle other keys (like space, enter, etc.)
                if key_code == "SPACE":
                    kb_character = " "
                elif key_code == "ENTER":
                    kb_character = "\n"
                else:
                    kb_character = f"<{key_code}>"
                yield kb_character

        elif key_event.keystate == evdev.KeyEvent.key_up:  # Key released
            if key_code in ["LEFTSHIFT", "RIGHTSHIFT"]:
                shift_pressed = False  # Reset shift state when shift is released

# ------------------------------------------------------------------.
# Operations on keyboard buffer


def edit_buffer(buf: str, key: str, pos: int | None = None) -> Tuple[str, int]:
    """Add 'key' to buffer 'buf' in position 'pos'.

    :pos: cursor position where to add next character, default None =
    end of buffer

    Non characters (len(key) > ) are special keys. When 'key'
    - BS: buffer content in 'pos' (=remove element bus[pos])

    :return:

    """

    def adjust_pos(pos, buf):

        if pos is None:
            pos = len(buf)
        pos = pos if pos <= len(buf) else len(buf)
        pos = pos if pos >= 0 else 0
        return pos
    pos = adjust_pos(pos, buf)

    print(f"{pos=}, {buf=}")

    if key == BS:
        # remove char in pos
        buf = buf[0:pos-1] + buf[pos:]
        pos -= 1

    pos = adjust_pos(pos, buf)
    return buf, pos


def split_buffer(buf: str, line_limit: int = 20) -> str:
    """Split  'buf' to line chunks of lenght 'line_limit' ."""

    parts = [buf[i:i+line_limit] for i in range(0, len(buf), line_limit)]
    return "\n".join(parts)

# ------------------------------------------------------------------.
# async routines


# async def read_raw_keyboard(keyboard: evdev.InputDevice):
#     """Generator yielding key events for key presson on 'keyboard'."""
#     event = await keyboard.async_read()
#     if event.type == evdev.ecodes.EV_KEY:
#         key_event = evdev.categorize(event)
#         # print(f"{type(key_event)=}, {key_event=}")
#         # print(f"{key_event.scancode=}")
#         # print(f"{key_event.keycode=}")
#         # print(f"{key_event.key_up=}")
#         # print(f"{key_event.key_down=}")
#         # print(f"{key_event.key_hold=}")

#         return key_event


# async def read_keyboard(keyboard: evdev.InputDevice):
#     """Generator yielding character presses on QWERTY 'keyboard'.

#     Kudos: ChatGPT
#     """

#     shift_pressed = False  # Track shift state for capital letters and special characters

#     # Define a mapping for special characters when shift is pressed
#     shift_map = {
#         "1": "!",
#         "2": "@",
#         "3": "#",
#         "4": "$",
#         "5": "%",
#         "6": "^",
#         "7": "&",
#         "8": "*",
#         "9": "(",
#         "0": ")",
#         "-": "_",
#         "=": "+",
#         "[": "{",
#         "]": "}",
#         "\\": "|",
#         ";": ":",
#         "'": "\"",
#         ",": "<",
#         ".": ">",
#         "/": "?",
#         "`": "~",
#         "MINUS": "_",
#         "EQUAL": "+",
#     }

#     while True:
#         key_event = await read_raw_keyboard(keyboard=keyboard)
#         # key_event = evdev.KeyEvent(event)  # Categorize the event
#         key_code = key_event.keycode.replace("KEY_", "")  # Get the key name
#         # logger.debug("key_code='%s'", key_code)

#         if key_event.keystate == evdev.KeyEvent.key_down:  # Key pressed
#             if key_code in ["LEFTSHIFT", "RIGHTSHIFT"]:
#                 shift_pressed = True
#             elif key_code.isalpha() and len(key_code) == 1:  # Alphabet keys
#                 if shift_pressed:
#                     kb_character = key_code.upper()  # Uppercase letters
#                 else:
#                     kb_character = key_code.lower()  # Lowercase letters
#                 return kb_character
#             elif key_code.isdigit() or key_code in shift_map.keys():  # Numbers and symbols
#                 if shift_pressed and key_code in shift_map:
#                     # Shift-modified character
#                     kb_character = shift_map[key_code]
#                 else:
#                     kb_character = key_code
#                 return kb_character
#             else:
#                 # Handle other keys (like space, enter, etc.)
#                 if key_code == "SPACE":
#                     kb_character = " "
#                 elif key_code == "ENTER":
#                     kb_character = "\n"
#                 else:
#                     kb_character = f"<{key_code}>"
#                 return kb_character

#         elif key_event.keystate == evdev.KeyEvent.key_up:  # Key released
#             if key_code in ["LEFTSHIFT", "RIGHTSHIFT"]:
#                 shift_pressed = False  # Reset shift state when shift is released


# ------------------------------------------------------------------
# Test locally


async def _kb_coro(keyboard: evdev.InputDevice):
    """Parse command line and dispatch commands."""

    async for k in read_keyboard(keyboard=keyboard):
        print(f"{k=}")


def _main(args):
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        # level=levels[min(parsed.verbose, len(levels)-1)],
        level=logging.DEBUG,
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
    )
    logger.info("logging.level: %s", logger.level)
    keyboard = find_keyboard(keyboard_name="USB Keyboard")

    asyncio.run(_kb_coro(keyboard=keyboard))


if __name__ == "__main__":
    args = sys.argv[1:]
    _main(args)
