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
    OPT_ALLOW_SCREENSHOTS = "--screen-shots"

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
    # DEFAULT_ICON_DIR = os.path.join(
    #     os.path.dirname(__file__), "../cnf", "icons")
    # DEFAULT_STREAM_YAML = os.path.join(
    #     os.path.dirname(__file__), "../cnf", "jrr_streams.yaml")
    DEFAULT_ICON_DIR = Path().home() / "cnf/icons"
    DEFAULT_STREAM_YAML = Path().home() / "cnf/jrr_streams.yaml"

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

        STREAM_TYPE_NETWORK = "stream"             # jrr_streamer.sh command stream
        STREAM_TYPE_CHIRP = "chirp"                # jrr_streamer.sh command chrip

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
        REORIGIN = "reorigin"                      # Reset Origin on 'ILI9486'
        SNAPSHOT = "snapshot"                      # Snapshot screen to file
        # Alternatives
        STREAM_ICON = "msg-stream-icon"            # stream icon image to screen
        CONFIG_TITLE = "title-subtitle"            # bold title, sub-title
        ERROR = "error"                            # error message ()
        QUESTION = "question"                      # confirm/other question
        FIRMAWRE = "firmware"                      # firmware w. release notes
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
        ENTRY_CHOOSE_WIFI_OVL = "wifi-choose-ovlay"
        ENTRY_URL_LOAD_OVL = "url-load-ovlay"
        ENTRY_FIRMWARE1_OVL = "firmware1-ovlay"
        ENTRY_FIRMWARE2_OVL = "firmware2-ovlay"
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
        ENTRY_VERSION = "version"
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
    DEFAULT_FIRMWARE_LOCAL_ROOT = os.path.join(
        Path.home(), "jrr")
    APP_TEMP = os.path.join(
        Path.home(), "tmp")
    APP_SNAPSHOT = APP_TEMP

    USE_LGPIO = True   # = new (default), =not using direct GPIO 

    # STREAMER_SCRIPT = Path.home() / "src/jrr_streamer.sh"
    STREAMER_SCRIPT = os.path.join(
        DEFAULT_FIRMWARE_LOCAL_ROOT, "src", "jrr_streamer.sh")
    # Symbolic link name
    FIRMWARE_CURRENT_LINK = "src"
    FIRMWARE_PENDING_LINK = "src.pending"
    VERSION_FILE = "VERSION"

    # Url to download firmware versions
    # DEFAULT_FIRMWARE_REPO_URL = f"file://{Path.home()}/jrr"
    DEFAULT_FIRMWARE_REPO_URL = "https://github.com/jarjuk/jrr"
    FIRMWARE_TAG_PATTERN = r'jrr-(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>[\w-]+)'
    DEBUG_DIR = Path.home() / "src/debug/"
    DEBUG_SUFFIX = "dbg"
    APP_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")
    ERROR_IMAGE = "error-100.png"
    QUESTION_IMAGE = "question-100.png"
    # ICON_SPRITE_FILE_PATH = Path.home() / "src/resources" / "icon-sprite.png"
    ICON_SPRITE_FILE_PATH = os.path.join(APP_RESOURCES, "icon-sprite.png")
    APP_STATE_FILE = "jrr.yaml"
    CHANNEL_ICONS = CLI.DEFAULT_ICON_DIR

    class STREAMER_COMMANDS:
        WIFI_SETUP = "wifi-setup"              # wifi SSID PASSI
        FIRMWARE_ACTIVATE = "firmware"         # download zip, unpack, make pending

    class SCREEN:
        MODE_FULL = "full"                 # screen update full
        MODE_FAST = "fast"                 # only for ePaper
        MODE_PARTIAL = "partial"           # update screen entry
        MODE_NONE = "NOupdate"             # no update

        WIDTH = RPI.ILI9486.WIDTH
        HEIGHT = RPI.ILI9486.HEIGHT

        VALUE_FIELD_WIDTH = 40             # longer lines split into multiple lines

        SCREEN_ORIENTATION_DEFAULT = 0     # mapped to Origin.UPPER_LEFT
        SCREEN_ORIENTATION_FLIPPED = 1     # mapped to Origin.LOWER_RIGHT

    class EXTENSION_HOOK:
        """Extension configuration"""

        ICON_DIR = "icons"                 # icons relative to channel YAML url

    class MENU:

        """Menu labels"""

        # Common
        NEXT = "Seuraava"
        BROWSE_FWD = "Eteen"
        BROWSE_BACK = "Taakse"
        PREV = "Edellinen"
        RADIO = "Radio"
        NO_ACTION = ""                      # No menu action
        UN_USED = ""                        # Not in use
        CHOOSE = "Valitse"
        ACTIVATE = "Aktivoi"
        DO_ADD = "Lisää"
        MAY_SETUP = "Asetetaanko"
        DO_LOAD = "Lataa"
        DELETE = "Poista"
        DELETE_CONFIRM = "Poistetaan"
        ACTIVATE_CONFIRM = "Lisätään"
        MAY_DELETE = "Poistaanko"
        MAY_ACTIVATE = "Lisätäänkö?"
        MAY_UPDATE = "Päivitetäänkö?"
        MAY_REBOOT_TITLE = "Käynnistetäänkö"
        MAY_REBOOT_SUBTITLE = "uudelleen?"
        RESUME = "Takaisin"
        RESTART = "Reset"
        OK = "OK"
        LOAD_CHANNELS = "Kanavat"           # Load more channels
        MENU_SUCCESS = "Onnistui"           # Operation success
        MENU_FAILURE = "Virhe"              # Operation Failure

        VOLUME_NOT_ON = "Ääni pois päältä"
        VOLUME_TURN_ON = "Käännä nuppi auki"

        KB_NOK = "Näppäimistövirhe"
        KB_ACT = "Kytke USB näppäimistö!"

        WIFI_SETUP = "Wifi valinta"
        CHANNEL_SETUP = "Kanavahakemisto:"
        YAML_FILE = "Kanavahakemisto:"

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
        MENU_CONFIG_REORIGIN = "Näytön kierto"
        MENU_FIRMWARE_VERSION = "Ohjelmaversio"
        MENU_MAYBE_CONFIG_WIFI = "Asetetaanko Wifi?"
        MENU_MAYBE_CHOOSE_WIFI = "Valitaanko Wifi?"
        MENU_DO_CONFIG_WIFI = "Wifin konfigurointi"
        MENU_DO_CHOOSE_WIFI = "Aktivoi Wifi"
        MENU_CONFIG_SETUP = "Asetukset"
        MENU_CONFIG_KEYBOARD = "Näppis"
        MENU_CHANNELS_SETUP = "Kanavat"
        MENU_REBOOT = "Reboot"
        MENU_CHANNELS_ORIGIN = "Hakemisto"
        MENU_REORIGIN = "Näytön kierto"
        MENU_CHANNELS_DELETE = "Poista"
        MENU_IP = "Verkkoyhteys"
        MENU_CHANNELS_ADD = "Lisää"
        MENU_ACTIVATE_CHANNELS = "Lisää kanavia"
        MENU_CHANNELS_DEL_ALL = "Poista"
        # MENU_CHANNELS_RESET = "Oletusarvot"

        CONFIG_MENU_ADD_CHANNEL = "Lisää"

        class CHANNEL_ORIGIN_SCREEN:
            PROMP = "Gimme URL"
            # DEFAULT_URL = "file:///home/pi/resources/channels"
            # DEFAULT_URL = "https://github.com/jarjuk/jrr/blob/main/resources/channels"
            DEFAULT_URL = "https://raw.githubusercontent.com/jarjuk/jrr/refs/heads/main/resources/channels/index.yaml"
            YAML = "rondo.yaml"
            INVALID_CHANNEL_ORIGIN = "Virheellinen osoite"

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

    class SCREEN_SHOT_LOCATIONS:
        RADIO_STREAMING = "jrr-01-radio-stream"
        SETUP_MAIN = "jrr-02-setup-main"
        CHANNEL_ACTIVATE = "jrr-03-channel-activate"
        CHANNEL_ACTIVATE_CONFIRM = "jrr-04-channel-activate-confirm"
        CHANNEL_SETUP = "jrr-03-channel-setup"
        CHANNEL_ORIGIN = "jrr-03-channel-origin"
        CHANNEL_BROWSE_DEL = "jrr-03-channel-browse"
        CHANNEL_BROWSE_DEL_CONFIRM = "jrr-04-channel-browse-delete-confirm"
        WIFI_LIST = "jrr-03-wifi-list"
        WIFI_SETUP = "jrr-04-wifi-setup"
        WIFI_CHOOSE = "jrr-04-wifi-choose"
        FIRMARE_UPDATE = "jrr-03-firmware-update"
        FIRMARE_UPDATE_COFIRM = "jrr-04-firmware-update-confirm"
        KEYBORD_CONFIG = "jrr-03-keyboard-config"
        KEYBORD_ERROR = "jrr-04-keyboard-error"
        REBOOT = "jrr-03-reboot"
        ERROR_ACCEPT = "jrr-90-error"
        UNDEFINED = "jrr-99-undefined"


class KEYBOARD:
    """Configure keys"""

    BACKSPACE = "<BACKSPACE>"
    DEL = "DEL"
    LEFT = "LEFT"
    LEFT2 = "<LEFT>"
    RIGHT = "RIGHT"
    RIGHT2 = "<RIGHT>"
    TAB = "	"        # 'normal' tab
    TAB2 = "<TAB>"       # 'normal' tab
    STAB = "STAB"        # shift tab
    HOME = "<HOME>"
    END = "<END>"
    DOT = "<DOT>"
    PRINT_SCREEN = "<SYSRQ>"    # print screen


class DSCREEN:
    """Screen data content manager used in controller."""

    class COMMON:
        HEADER = "header"

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
        WIFI_CHOOSE = COROS.Screen.ENTRY_CHOOSE_WIFI_OVL
        URL_LOAD = COROS.Screen.ENTRY_URL_LOAD_OVL
        FIRMWARE1 = COROS.Screen.ENTRY_FIRMWARE1_OVL
        FIRMWARE2 = COROS.Screen.ENTRY_FIRMWARE2_OVL

    class WIFI_OVERLAY:
        """Layout names for Screen overlays, names of FieldValue
        in Dscreen.

        """
        HEADER = "header"
        SSID = "ssid"
        PASSWORD = "password"

    class WIFI_CHOOSE_OVERLAY:
        """Layout names for Screen overlays, names of FieldValue
        in Dscreen.

        """
        HEADER = "header"
        SSID = "ssid"

    class URL_LOAD_OVERLAY:
        """Field names for url-loader.
        """
        TITLE = "header"
        URL_BASE = "url"
        YAML_FILE = "yaml"

    class FIRMWARE_OVERLAY:
        """Field names for firmware selection
        """
        HEADER = "header"
        VERSION_TAG = "version_tag"
        NOTES = "notes"

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
