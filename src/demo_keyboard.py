#!/usr/bin/env python3

"""Test keyboar
"""
import sys
import logging
import evdev

logger = logging.getLogger(__name__)


def list_devices():
    # List all input devices
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    print(f"{devices=}")
    return devices


def find_keyboard(keyboard_name) -> evdev.InputDevice:
    # Find your keyboard device
    devices = list_devices()
    kb_dev = None
    for device in devices:
        print(f"{device.path=}, {device.name=}, {device.phys=}")
        if device.name == keyboard_name:
            kb_dev = device
            print(f"{kb_dev=} chosen")

    return kb_dev


def read_raw_keyboard(keyboard: evdev.InputDevice):
    """Generator yielding key events for key presson on 'keyboard'."""
    for event in keyboard.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            key_event = evdev.categorize(event)
            # print(f"{type(key_event)=}, {key_event=}")
            # print(f"{key_event.scancode=}")
            # print(f"{key_event.keycode=}")
            # print(f"{key_event.key_up=}")
            # print(f"{key_event.key_down=}")
            # print(f"{key_event.key_hold=}")

            yield key_event


def read_keyboard(keyboard: evdev.InputDevice):
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
    }

    for key_event in read_raw_keyboard(keyboard=keyboard):
        # key_event = evdev.KeyEvent(event)  # Categorize the event
        key_code = key_event.keycode.replace("KEY_", "")  # Get the key name
        # print(f"{key_code=}")

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


def main(args):
    """Parse command line and dispatch commands."""

    # parsed = commandLineArgruments(args)
    # logging.basicConfig(level=logging.DEBUG)
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(
        # level=levels[min(parsed.verbose, len(levels)-1)],
        level=logging.DEBUG,
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
    )
    logger.info("logging.level: %s", logger.level)
    keyboard = find_keyboard(keyboard_name="USB Keyboard")
    for k in read_keyboard(keyboard=keyboard):
        print(f"{k=}")

    # Dispatch actions
    # if parsed.command == CLI.CMD_RADIO:
    #     radio_main(parsed)
    # elif parsed.command == CLI.CMD_ICON_CONVERT:
    #     converter_main(parsed)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
