"""
Constants module
"""
from pathlib import Path
from enum import Enum
import os


class CLI:
    """Configure command line"""

    # Commands
    CMD_RADIO = "radio"
    CMD_ICON_CONVERT = "convert"

    # CLI options (for radio streamer)
    # OPT_SYSTEM_HALT = "--system-halt"
    OPT_CONSOLE_ALL_LINES = "--all-lines"

    # CLI options (for icon converter)
    OPT_ICON_SOURCE = "--icons-from"
    OPT_ICON_TARGET = "--icons-to"
    OPT_STREAMING_ICON_WIDTH = "--width"
    OPT_STREAMING_ICON_HEIGHT = "--height"

    # DEFAULT_STREAMING_ICON_WIDTH = 96             # streamer icon width
    DEFAULT_STREAMING_ICON_WIDTH = 200             # streamer icon width
    DEFAULT_STREAMING_ICON_HEIGHT = DEFAULT_STREAMING_ICON_WIDTH
    # icon size (w,h) in sprite (divisible by 8)
    DEFAULT_SPRITE_ICON_SIZE = 24

    # Directories and files
    DEFAULT_ICON_SOURCE_DIR = Path.home() / ".icons"        # input for icon conversion
    DEFAULT_ICON_DIR = os.path.join(
        os.path.dirname(__file__), "../cnf", "icons")
    DEFAULT_STREAM_YAML = os.path.join(
        os.path.dirname(__file__), "../cnf", "jrr_streams.yaml")

    FACTORY_ICON_DIR = os.path.join(
        os.path.dirname(__file__), "cnf", "icons")
    FACTORY_STREAM_YAML = os.path.join(
        os.path.dirname(__file__), "cnf", "jrr_streams.yaml")

    # Time and time out managenemtn
    DEFAULT_CLOCK_TICK = 10                        # secs betweeen CLOCK_TICK messages
    # TODO: display put to sleep after timeout
    DEFAULT_INACTIVITY_TIMEOUT = 30

    # Screeen configuration
    DEFAULT_FULL_UPDATE_LIMIT = 10                 # full update after this limit


class TOPICS:
    """Publish/subscrice topics and messages"""

    # Unique topic names in publish/subscribe pattern
    CONTROL = "ctrl"                               # control channel
    DEFAULT = "default"                            # default channel TODO remove
    SCREEN = "screen"                              # e-paper display
    STREAMER = "streamer"                          # audio streamer
    NETWORK_MONITOR = "network"                    # network monitor coro control
    KEYBOARD = "kb"

    # Unique message names (grouped within *_MESSAGES just for
    # documentation purposes)
    class COMMON_MESSAGES:
        """Common messages in any -topic"""

        EXIT = "exit"                              # close coro on EXIT message
        DELAY = "delay"                            # async sleep
        CLOCK_TICK = "tick"                        # clock ticks
        PING = "ping"                              # are you there

    class GPIO_MESSAGES:
        """Messages in GPIO."""
        GPIO = "gpio"                              # button pressed

    class KEYBOARD_MESSAGES:
        """Messages in GPIO."""
        KEY = "key"                                # key pressed
        START = "start-kb"                         # start reading keyboard
        STOP = "stop-kb"                           # stop reading keyboard
        STATUS = "kb-status"                       # report keyboard status

    class CONTROL_MESSAGES:
        """Messages in CONTROL -topic."""
        REBOOT = "REBOOT"                          # close app (and hope it gets restarted)
        HALT = "HALT"                              # halt machine
        HALT_ACK = "HALT-ACK"                      # halt acknowneded
        # streame (runner) status reply
        STREAMER_STATUS_REPLY = "status_reply"

    class NETWORK_MESSAGES:
        STATUS = "nw-status"

    class STREAMER_MESSAGES:
        """Messages in STREAMER -topic"""
        START = "start_stream"                     # start streaming
        STOP = "stop_stream"                       # stop streaming
        # query stream (runner) status
        STATUS_QUERY = "status_stream"

    class SCREEN_MESSAGES:
        """Messages in SCREEN -topic"""
        INIT = "init"                              # init (should be called first)
        SLEEP = "sleep"                            # sleep mode
        WAKEUP = "wakeup"                          # wakeup after sleep
        CLEAR = "clear"                            # clear 'screen' and 'display'
        CLOSE = "close"                            # power off
        UPDATE = "update"                          # full/fast/partial screen update
        TEST = "test"                              # test something
        CLOCK = "clock"                            # Update display time
        SPRITE = "sprite"                          # Status icons on sprite
        BUTTON_TXT = "button"                      # button text
        MSG_INFO = "info"                          # info message to user
        # Alternatives
        STREAM_ICON = "msg-stream-icon"            # stream icon image to screen
        CONFIG_TITLE = "title-subtitle"            # bold title, sub-title
        ERROR = "error"                            # error message ()
        QUESTION = "question"                      # confirm/other question
        DSCREEN = "dscreen"                        # generic dscreen message
        NETWORK_INFO = "network"                   # ssid and IP address

    class QUESTION_MESSAGE:
        """Fields in Question message"""
        ICON = "icon"                              # image path for icon

    class CONFIG_TITLE_MESSAGE:
        """Fields in Title message"""
        ICON = "icon"                              # image path for icon

    class HALT_SOURCE(Enum):
        """Distinguish source for halt message."""
        GPIO = 1                                   # knob on GPIO input
        SIGNAL = 2                                 # sigterm
        MESSAGE = 3                                # shutdown message received


class COROS:
    """Names for co-routines"""
    CLOCK = "clock"                                # clock publishing 'CLOCK_TICK'
    STDIN_READER = "stdin"                         # stdin->topic (debugger)
    # ubs keyboard -> ctrl (config)
    KB_READER = "kb"
    NETWORK_MONITOR = "network-mon"                # network status
    SPY_DEFAULT = "spy-default"                    # DEFAULT->log
    SPY_CONTROL = "spy-ctrl"                       # CONTROL->log
    GPIO_PB = "buttons"                            # GPIO->topic
    MASTER = "master"                              # shutdown, screen + streamer state
    SCREEN = "screen"                              # topic->eInk
    STREAMER = "streamer"                          # manage streamer (ffmpeg)

    class Screen:
        """Named screen locations"""
        ENTRY_CLOCK = "clock"
        ENTRY_STREAM_ICON = "stream-ovlay"
        ENTRY_CONFIG = "config-ovlay"
        ENTRY_CONFIG_TITLE = "conf-menu-ovlay"
        ENTRY_WIFI_OVL = "wifi-ovlay"
        ENTRY_URL_LOAD_OVL = "url-load-ovlay"
        ENTRY_ERROR_OVL = "error-ovlay"
        ENTRY_QUESTION_OVL = "question-ovlay"
        ENTRY_NETWORK_INFO_OVL = "network-ovlay"
        ENTRY_SPRITE_ICONS = "sprite"
        ENTRY_ICON_KEY1 = "key1-icon"
        ENTRY_ICON_KEY2 = "key2-icon"
        ENTRY_B1 = "b1"
        ENTRY_B2 = "b2"
        ENTRY_B3 = "b3"
        ENTRY_B4 = "b4"
        ENTRY_MSG_L1 = "msg1"
        ENTRY_MSG_L2 = "msg2"


class RPI:
    """Raspberry PI configruation"""

    BUTTON1_GPIO = 19     # Upper button, internal pull up
    BUTTON2_GPIO = 20     # Lower button, internal pull up
    BUTTON_SHUTDOWN = 26  # external pull, N-ch mosfet pulls down on shutdown

    class ILI9486:
        """3.5 inch TFT display size 480x320 pixels"""
        # Pin definition
        RST_PIN = 25
        DC_PIN = 24
        # SPI definition
        SPI_BUS = 0
        SPI_DEVICE = 0
        WIDTH = 480
        HEIGHT = 320

    BUTTON_GPIOS = [
        BUTTON1_GPIO,
        BUTTON2_GPIO
    ]                                              # buttons used and initiazlide

    LONG_PRESS_S = 700/1000                        # millis -> fraction of sec

    # ICON_DIR = Path.home() / ".icons/v2" # directory for thumb size images
    ICON_DIR = CLI.DEFAULT_ICON_DIR        # directory for thumb size images

    # String identifying USB keyboard
    KEYBOARD_NAME = "USB Keyboard"


class APP_CONTEXT:
    STREAMER_SCRIPT = Path.home() / "src/jrr_streamer.sh"
    # Symbolic link name
    FIRMWARE_CURRENT_LINK = "src"
    FIRMWARE_PENDING_LINK = "src.pending"
    DEFAULT_FIRMWARE_LOCAL_ROOT = os.path.join(
        Path.home(), FIRMWARE_CURRENT_LINK)
    DEFAULT_FIRMWARE_REPO_URL = f"file://{Path.home()}/jrr"
    FIRMWARE_TAG_PATTERN = r'jrr-(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\w+)'
    DEBUG_DIR = Path.home() / "src/debug/"
    DEBUG_SUFFIX = "dbg"
    APP_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")
    # ICON_SPRITE_FILE_PATH = Path.home() / "src/resources" / "icon-sprite.png"
    ICON_SPRITE_FILE_PATH = os.path.join(APP_RESOURCES, "icon-sprite.png")
    APP_STATE_FILE = "jrr.yaml"
    CHANNEL_ICONS = CLI.DEFAULT_ICON_DIR

    class STREAMER_COMMANDS:
        WIFI_SETUP = "wifi-setup"              # wifi SSID PASSI

    class SCREEN:
        MODE_FULL = "full"                 # screen update full
        MODE_FAST = "fast"                 # only for ePaper
        MODE_PARTIAL = "partial"           # update screen entry
        MODE_NONE = "NOupdate"             # no update

        WIDTH = RPI.ILI9486.WIDTH
        HEIGHT = RPI.ILI9486.HEIGHT

        VALUE_FIELD_WIDTH = 40             # longer lines split into multiple lines

    class EXTENSION_HOOK:
        """Extension configuration"""

        ICON_DIR = "icons"                 # icons relative to channel YAML url

    class MENU:

        """Menu labels"""

        # Common
        NEXT = "Seuraava"
        PREV = "Edellinen"
        RADIO = "Radio"
        NO_ACTION = ""                      # No menu action
        UN_USED = ""                        # Not in use
        CHOOSE = "Valitse"
        ACTIVATE = "Aktivoi"
        MAY_SETUP = "Asetetaanko"
        DO_LOAD = "Lataa"
        DELETE = "Poista"
        DELETE_CONFIRM = "Poistetaan"
        ACTIVATE_CONFIRM = "Aktivoidaan"
        MAY_DELETE = "Poistaanko"
        MAY_ACTIVATE = "Aktivoidaanko"
        MAY_REBOOT_TITLE = "Käynnistetäänkö"
        MAY_REBOOT_SUBTITLE = "uudelleen?"
        RESUME = "Takaisin"
        RESTART = "Reset"
        LOAD_CHANNELS = "Kanavat"           # Load more channels
        MENU_SUCCESS = "Onnistui"           # Operation success
        MENU_FAILURE = "Virhe"              # Operation Failure

        KB_NOK = "Näppäimistövirhe"
        KB_ACT = """
        Kytke USB näppäimistö ja
        paina jotain näppäintä!"
        """

        WIFI_SETUP = "Wifi valinta"

        # Radio Streamer
        RADIO_NEXT_CHANNEL = NEXT           # Stream next channel
        RADIO_PREV_CHANNEL = PREV           # Stream prev channel
        CONFIG_ENTER = "Asetukset"          # Stream prev channel
        # Config
        CONFIG_RETURN = "Palaa"            # Back to prev. level
        CONFIG_OK = "OK"                   # Back to prev. level
        CONFIG_RADIO = RADIO               # Stream prev channel
        CONFIG_NEXT = NEXT
        CONFIG_PREV = PREV

        MENU_CONFIG_WIFI = "Wifi"
        MENU_MAYBE_CONFIG_WIFI = "Valintaanko Wifi?"
        MENU_DO_CONFIG_WIFI = "Wifin aktivointi"
        MENU_CONFIG_SETUP = "Asetukset"
        MENU_CONFIG_KEYBOARD = "Näppis"
        MENU_CHANNELS_SETUP = "Kanavat"
        MENU_REBOOT = "Reboot"
        MENU_CHANNELS_ORIGIN = "Hakemisto"
        MENU_CHANNELS_BROWSE = "Selaa"
        MENU_IP = "Verkkoyhteys"
        MENU_CHANNELS_ADD = "Lisää"
        MENU_ACTIVATE_CHANNELS = "Aktivoi kanavia"
        MENU_CHANNELS_DEL_ALL = "Poista"
        # MENU_CHANNELS_RESET = "Oletusarvot"

        CONFIG_MENU_ADD_CHANNEL = "Lisää"

        class LOAD_CHANNELS_DEFAULTS:
            PROMP = "Gimme URL"
            # DEFAULT_URL = "file:///home/pi/resources/channels"
            # DEFAULT_URL = "https://github.com/jarjuk/jrr/blob/main/resources/channels"
            DEFAULT_URL = "https://raw.githubusercontent.com/jarjuk/jrr/refs/heads/main/resources/channels"
            YAML = "rondo.yaml"

        class WIFI_SETUP_SCREEN:
            SSID_PROMPT = "SSID:"
            PASSWORD_PROMPT = "Salasana:"

        class ACTS:
            """Key-names in dict for menu configuration"""

            BTN_LABELS = "btn-labels"
            APP_SCREEN = "app-screen"
            ENTRY_ACTION = "entry-action"     # lamda(hub, menu_step)

            """Message actions to act upon"""
            BTN1_SHORT = "btn1_short"  # next if not given
            BTN2_SHORT = "btn2_short"
            BTN1_LONG = "btn1_long"
            BTN2_LONG = "btn2_long"
            KEYBOARD = "keyboard"

    class SCREEN_LAYOUTS:
        """Alternative screen overlays"""
        STREAMING = "stream"
        CONFIGURATION_CONTAINER = "config"
        # CONFIGURATION_MENU = "config-menu"


class KEYBOARD:
    """Configure keys"""

    BACKSPACE = "<BACKSPACE>"
    DEL = "DEL"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    TAB = "	"      # 'normal' tab
    STAB = "STAB"        # shift tab


class DSCREEN:
    """Screen data content manager used in controller."""

    class FIELD_STATUS(Enum):
        """Status enum for FieldValue."""
        OK = 0
        ERR = -1

    class VALIDATION_ERRORS:
        """Messages for return validation errors"""
        INPUT_TYPE_MISMATCH = "Invalid type for input '{dataIn}' - expecting {expect}"
        INPUT_MAX_LEN = "Maximun length exceeded {value}{dataIn} - expecting {expect}"
        UNKNOWN_INPUT = "Could not process input '{dataIn}' - expecting {expect}"

    class MISC_ERRORS:
        UNKNOWN_SCREEN = "No such screen '{current}' - valid screens {screens}"
        NO_SCREEN_ACTIVE = "No screen  active - valid screens {screens}"

    class SCREEN_OVERLAYS:
        """Overlays for configuration displays."""
        WIFI_SETUP = COROS.Screen.ENTRY_WIFI_OVL
        URL_LOAD = COROS.Screen.ENTRY_URL_LOAD_OVL

    class WIFI_OVERLAY:
        """Layout names for Screen overlays, names of FieldValue
        in Dscreen.

        """
        HEADER = "header"
        SSID = "ssid"
        PASSWORD = "password"

    class URL_LOAD_OVERLAY:
        """Field names for url-loader.
        """
        TITLE = "header"
        URL_BASE = "url"
        YAML_FILE = "yaml"

    class ERROR_OVERLAY:
        """Field names for url-loader.
        """
        ERROR = "error"
        INSTRUCTIONS = "instructions"
        ICON = "icon"

    class QUESTION_OVERLAY:
        """Field names for confirmation/question.
        """
        TITLE = "title"
        QUESTION = "question"
        ICON = TOPICS.QUESTION_MESSAGE.ICON

    class NETWORK_INFO_OVERLAY:
        """Current network ok"""
        TITLE = "title"
        SUB_TITLE = "sub_title"
        SSID = "ssid"
        IP = "ip"

    class CONFIG_TITLE_OVERLAY:
        """Layout names for config titles for screenoverlay/Dscreen.

        """
        HEADER = "header"
        SUB_HEADER = "sub_header"
        ICON = TOPICS.CONFIG_TITLE_MESSAGE.ICON
