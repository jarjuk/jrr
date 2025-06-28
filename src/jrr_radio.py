"""Main for radio (daemon)
"""
from typing import List, Callable, cast, Dict, Tuple
import signal
from functools import partial
import asyncio
import logging
import datetime
from dataclasses import dataclass, fields
import os
import yaml


from .console import console_output, console_close
from .config import app_config
from .publish_subsrcibe import Hub
from .stdin_coro import stdin_coro
from .debug.debugger import stdin_debugger
from .reader_coro import reader_coro
from .network_coro import network_coro, reset_network_status
from .clock_coro import clock_coro
from .channel_manager import (read_file, StreamConfig,
                              init_streams,
                              parse_channels, icon_path,
                              update_channel_configurations,
                              channel_activation_list, channel_activate, channel_activation_index,
                              channel_icon_image)
from .constants import (DSCREEN, TOPICS, COROS, RPI, APP_CONTEXT,)
from .utils import set_wifi_password, current_IP, current_ssid
from .gpio_coro import (
    gpio_init,
    init_GPIO_buttons, init_GPIO_shutdown, GPIO_button_coro, gpio_close)
from .screen_coro import (screen_coro, screen_close)
from .kb import (edit_buffer, split_buffer)
from .kb_coro import (kb_coro, is_keyboard_connected)
from .streamer_coro import streamer_coro
from .wifi import list_wifis
from .dscreen import DApp
from .jrr_dapp import screen_ovrlays
from .messages import (MsgRoot,
                       is_message_type,
                       message_halt, message_create,
                       message_exit,
                       message_screen_update, message_screen_sleep,
                       message_screen_stream_icon,
                       message_screen_refresh,
                       message_status_icons,
                       message_info,
                       message_panik,
                       message_clock_update,
                       message_button_labels,
                       message_config_title,
                       message_error, message_question,
                       message_network_info,
                       message_keyboard_start, message_keyboard_stop,
                       MsgNetwork,
                       MsgButton, MsgKey,
                       MsgHalt_HaltAck,
                       MsgStreamerStatusReply,
                       MsgKeyboardStatus,
                       message_streamer_start, message_streamer_stop,
                       )

# ------------------------------------------------------------------
# Module state


@dataclass
class ControllerState:
    """Collect controller state"""

    PERSISTENT_FIELDS = ["current_stream", ]

    # state machine executuing e.g. f_config, f_radio,
    state_machine: Callable[str | MsgRoot, Hub]
    menu_step: int                              # enumerated state in SM

    # refresh for button and keyboard activity
    user_inactivity: datetime.datetime

    # screen put in sleep after inactivity period
    screen_in_sleep: bool

    # Radio streams cached
    streams: List[StreamConfig]                  # radio streams for listening

    current_stream: int                          # index to streams
    streamer_on: bool                            # streamer process TOBE

    # sprite state
    network_status: bool                         # network ok/nok
    streamer_status: bool                        # streamer process running

    # keyboard entry
    keyboard_status: bool                        # keyboard connected/not
    keyboard_entry: str                          # collect key board data here

    # configuration screen
    # screen overlays for configuration
    config_screens: DApp = screen_ovrlays

    def __init__(self):
        self.state_machine = None
        self.menu_step = 0
        self.user_inactivity = datetime.datetime.now()
        self.screen_in_sleep = False
        self.keyboard_status = None
        self.streamer_status = None
        self.streamer_on = None
        self.network_status = None
        self.keyboard_entry = ""
        self.current_stream = 0     # NB: f_radio in lock step with current stream
        self.streams = None
        self.config_screens = screen_ovrlays

    # ------------------------------------------------------------------
    # Network status

    def set_network_status(self, status: bool):
        self.network_status = status

    # ------------------------------------------------------------------
    # Stepping state machine

    def menu_step_advance(self, advance: int, menus: List[List],
                          set_menu_step: int | None = None) -> int:
        """Adavance menu in 'menus' forward (+1), backward (-1), or
        'set_menu_step'.

        Ensure that 'menu_step' is valid index in 'menus'.

        :set_menu_step: jump to menu step (if not None), overrides :advance:

        :return: index in menus list for current menu

        """
        self.menu_step += advance

        if set_menu_step is not None:
            self.menu_step = set_menu_step

        # Cicular buffer
        if self.menu_step < 0:
            self.menu_step = len(menus) - 1
        elif self.menu_step >= len(menus):
            self.menu_step = 0

        return self.menu_step

    def menu_state_resume(self, menu_step: int | None):
        """Resume 'menu_step' (if not none) """

        if menu_step is not None:
            logger.info("step_resume: old: '%s' -> new:'%s'",
                        self.menu_step,
                        menu_step)
            self.menu_step = menu_step

    # ------------------------------------------------------------------
    # persisentence

    def save_state(self):
        state_dict = {
            k: getattr(self, k)
            for k in self.PERSISTENT_FIELDS
        }
        state_dict["now"] = datetime.datetime.now().isoformat()
        logger.info("save_state: state_dict='%s'", state_dict)
        with open(app_config.state_config, 'w', encoding="UTF-8") as f:
            yaml.dump(state_dict, f)

    def restore_state(self):
        """Restrore some fields from """
        yaml_str, stat = read_file(app_config.state_config)
        logger.debug("restore_state: yaml_str='%s', stat=%s", yaml_str, stat)
        if stat:
            state_dict = yaml.safe_load(yaml_str)
            logger.info("restore_state: state_dict='%s', apply with field:%s",
                        state_dict, dir(self))
            for k, v in state_dict.items():
                if k in dir(self):
                    setattr(self, k, v)

        # Radio menu step in lock step with stream number
        self.menu_step = self.current_stream

    # ------------------------------------------------------------------
    # Stream management

    def set_streamer_status(
            self, running: bool | None = None,
            streamer_on: bool | None = None) -> bool:
        """Set streamer -process status (and optional process TOBE -state)

        :running: streamer -process running True/False, None no change

        :streamer_on: streamer process tobe -value (=user conception)

        :return: True if status changed state
        """

        old_state = self.streamer_status
        if running is not None:
            self.streamer_status = running
        if not streamer_on is None:
            self.streamer_on = streamer_on

        return old_state != self.streamer_status

    def init_streams(self) -> bool:
        """Read StreamConfig -object from stream yaml into 'self.streams'.

        Can be called idempotently e.g. to allow lazy intialization.

        :return: true/false for factory_reset_done

        """
        if self.streams is not None:
            return False

        # Parse StreamConfig from configuration YAML
        self.streams, factory_reset_done = init_streams()

        # with open(app_config.streams_yaml) as f:
        #     self.streams = [StreamConfig(**s) for s in yaml.safe_load(f)]
        #     logger.debug("init_streams: self.streams: %s", self.streams)
        # TODO: init current_stream  persistently
        # self.current_stream = 0

        return factory_reset_done

    def stream_to_button_menu_labels(self) -> Tuple[List[List[str]], bool]:
        """Create list of button menus for radio streams.

        Uses 'init_stream' to read stream configurations from
        yaml-configurations.

        Button labels:
        - 0: btn1-short: next -channel
        - 1: btn1-long: enter config
        - 2: btn2-short: prev-channel
        - 3: btn2-long: not-used

        :return: List of lists for button menu factory reset done

        """
        # Force rearead
        self.streams = None
        factory_reset_done = self.init_streams()
        logger.debug(
            "stream_to_button_menu_labels: self.streams='%s'", self.streams)

        menu: List = []
        if self.streams is not None:
            stream_names = [s.name for s in self.streams]
            for idx in range(len(stream_names)):
                next_stream = idx + 1 if idx < len(stream_names) - 1 else 0
                prev_stream = idx - 1 if idx > 0 else len(stream_names)-1

                btn_labels = [
                    stream_names[next_stream],
                    APP_CONTEXT.MENU.CONFIG_ENTER,
                    stream_names[prev_stream],
                    APP_CONTEXT.MENU.UN_USED,
                ]
                menu.append(btn_labels)

        logger.debug("stream_to_button_menu_labels: menu='%s'", menu)
        return (menu, factory_reset_done)

    def set_and_get_stream(self, stream_adv: int = 0) -> StreamConfig | None:
        """Return 'StreamConfig' object for current stream.

        :stream_adv: optionally advance to next/prev stream, (1: next,
        0: current, -1: prev)

        :return: StreamConfig for for selected stream (None if not
        streams to choose exist).

        """
        # Lazy read for YAML confuration
        self.init_streams()

        # Advance next/prev=
        self.current_stream += stream_adv

        # Circular buffer (avoid out of bound error)
        if self.current_stream < 0:
            self.current_stream = len(self.streams)-1
        if self.current_stream >= len(self.streams):
            self.current_stream = 0

        # no streams found possible
        return None if len(self.streams) == 0 else self.streams[self.current_stream]

    def delete_stream(self, name: str | None) -> List[StreamConfig]:
        """Delete stream/streams from 'controller_state.streams'.


        :name: stream name to delete, delete all if None

        Calls channel manager method 'delete_channel_configurations'
        to update changel in yaml configuration.

        """
        logger.info("delete_stream: self.streams='%s' -before delete for name=%s",
                    self.streams, name)
        deleted_streams = [s for s in self.streams
                           if s.name == name or name is None]
        self.streams = [s for s in self.streams if s not in deleted_streams]
        logger.info("delete_stream: deleted_streams='%s'", deleted_streams)
        logger.info(
            "delete_stream: self.streams='%s' -after delete", self.streams)

        # delete from yaml configs (possibly remove yaml file),
        # remove also icon
        update_channel_configurations(self.streams, deleted_streams)

        return self.streams

    # ------------------------------------------------------------------
    # User active: user_inactivity -timer

    def maybe_user_active(self, msg: str | MsgRoot) -> bool:
        """Update 'user_inactivity' if message originates from user.

        User active:
        - GPIO_MESSAGES.GPIO: button  pressed
        - KEYBOARD_KEY: key message

        Return true if user was active

        """
        return_user_was_active = False
        check_active_messages = [
            TOPICS.GPIO_MESSAGES.GPIO,
            TOPICS.KEYBOARD_MESSAGES.KEY,
        ]

        if is_message_type(msg, check_active_messages):
            # active --> update timer
            self.user_inactivity = datetime.datetime.now()
            return_user_was_active = True
        return return_user_was_active

    def user_inactive_too_long(self) -> bool:
        """Check if user has been inactive for too long time."""
        user_inactivity = datetime.datetime.now() - self.user_inactivity
        goto_sleep = (user_inactivity.total_seconds() >
                      app_config.inactivity_timeout)
        return goto_sleep

    # ------------------------------------------------------------------
    # display sleep/awake: screen_in_sleep
    def set_display_state(self, awake: bool = True):
        """set display status: awake = not 'in_sleep')"""
        controller_state.screen_in_sleep = not awake

    def display_close_if_awake(self, hub: Hub) -> bool:
        """Idempotent goto sleep returns True on falling asleep."""
        slept = False
        logger.info("display_close_if_awake: self.screen_in_sleep='%s'",
                    self.screen_in_sleep)
        if not self.screen_in_sleep:
            hub.publish(
                topic=TOPICS.SCREEN, message=message_screen_sleep())
            self.screen_in_sleep = True
            slept = True
        return slept

    def display_maybe_awake(self, hub: Hub) -> bool:
        """Idempotent display awake return True on woked"""
        woked = False
        if self.screen_in_sleep:
            # Full update
            hub.publish(
                topic=TOPICS.SCREEN,
                message=message_screen_update())
            self.screen_in_sleep = False
            woked = True
        return woked

    # ------------------------------------------------------------------
    # Manage keyboard stuff

    def keyboard_init(self, text: str = "") -> str:
        self.keyboard_entry = text
        logger.error("keyboard_init: TODO should not use, text='%s'", text)
        return self.keyboard_entry

    def keyboard_key(self, key: str) -> str | None:
        """Accept 'key' to build 'keyboard_entry' .

        Note: Key may be an edit operation in buffer.


        :return: keyboard_entry

        """
        if self.keyboard_entry is None:
            self.keyboard_entry = ""

        # TODO: add cursor here
        self.keyboard_entry, _ = edit_buffer(buf=self.keyboard_entry, key=key)

        return self.keyboard_entry

    @property
    def get_keyboard_status(self):
        return self.keyboard_status

    def set_keyboard_status(self, keyboard_status: bool) -> bool:
        """Set keyboard connected status.

        :return: True if status changed
        """
        old_state = self.keyboard_status
        self.keyboard_status = keyboard_status
        changed = old_state != self.keyboard_status
        if changed:
            logger.info(": old_state='%s', new-status: '%s'",
                        old_state,
                        self.keyboard_status)
        return changed


logger = logging.getLogger(__name__)
controller_state = ControllerState()

# ------------------------------------------------------------------
# Helpers


# ------------------------------------------------------------------
# Actions used in state machines


def ctrl_act_screen_info_txt(hub: Hub, message: str):
    """Send 'message' to screen info-line."""
    hub.publish(topic=TOPICS.SCREEN, message=message_info(message))


def ctrl_act_reboot(hub: Hub):
    """Send 'shutdown' -message to CTRL.

    Most likely:
    - controler coro receives SHUTDOWN
    - controler coro sends SHUTDOWN to all other coros
    - coros receive SHUTDOWN and exit
    - controller coro exits
    - application exists
    - systemd restarts application

    """
    logger.warning("shutting down!!! ")
    hub.publish(
        topic=TOPICS.CONTROL,
        message=message_create(message_type=TOPICS.CONTROL_MESSAGES.REBOOT))


def ctrl_act_refresh_display(hub: Hub):
    """Refresh message to screen."""
    hub.publish(
        topic=TOPICS.SCREEN,
        message=message_screen_refresh())


def ctrl_act_sleep_display(hub: Hub):
    """Sleep message to screen."""
    hub.publish(
        topic=TOPICS.SCREEN,
        message=message_screen_sleep())


def ctrl_act_update_status(hub: Hub, network_status: bool | None = None):
    """Message with network, streaming, and keyboard- statuses.

    Optionally sets network_status.
    """
    if network_status is not None:
        reset_network_status()
        controller_state.set_network_status(network_status)

    hub.publish(
        topic=TOPICS.SCREEN,
        message=message_clock_update(
            network_status=controller_state.network_status,
            streaming_status=controller_state.streamer_status,
            keyboard_status=controller_state.keyboard_status,
        )
    )

    # hub.publish(
    #     topic=TOPICS.SCREEN,
    #     message=message_status_icons(
    #         network=controller_state.network_status,
    #         streaming=controller_state.streamer_status,
    #         keyboard=controller_state.get_keyboard_status,
    #     )
    # )


# def ctrl_act_screen_set_menu_name(hub: Hub, menu_name: str):
#     """Set 'menu_name' on configuration menu.

#     Sends CONFIG_MENU -message to SCREEN.

#     """

#     hub.publish(
#         topic=TOPICS.SCREEN,
#         message=message_create(
#             message_type=TOPICS.SCREEN_MESSAGES.CONFIG_MENU,
#             d={
#                 "header": menu_name,
#                 "selection": None,
#             }))


def ctrl_act_screen_config_prompt(
        hub: Hub,
        prompt: str,
        value: str | None = None):
    """Send 'prompt' and optionally 'value' to config screen.

    Sends CONFIG_MENU -message to SCREEN.

    """
    logger.info("ctrl_act_screen_config_prompt: promt='%s', value='%s'",
                prompt, value)

    hub.publish(
        topic=TOPICS.SCREEN,
        message=message_create(
            message_type=TOPICS.SCREEN_MESSAGES.CONFIG_TITLE,
            d={
                "prompt": prompt,
                "value": value,
            }))


def ctrl_act_menu_next_prev(
        hub: Hub,
        advance: int,
        menus: List[List[str]],
        set_menu_step: int | None = None
) -> int:
    """Set button labels (after 'controller.menu_step'
    advance/set_menu_step) from 'menus' .

    Sends 'TOPICS.SCREEN_MESSAGES.BUTTON_TXT' message to screen.

    :advance: 0= set current menu, +1 next menu, -1 prev menu,

    :set_menu_step: jump to menu step (if not None), overrides :advance:

    :menus: list of list of button labels (btn1_short, btn1_long,
    btn2_short, btn2_long)

    :return: index to 'menus' list

    """

    # advace/set controller_state.menu_step
    menu_step = controller_state.menu_step_advance(
        advance=advance,
        menus=menus, set_menu_step=set_menu_step)
    logger.debug("ctrl_act_screen_set_menu_buttons: menu_step='%s'\nmenus='%s'",
                 menu_step, menus)

    # set menu button labels on screen
    # if len(menus) > menu_step:
    hub.publish(topic=TOPICS.SCREEN,
                message=message_button_labels(
                    label1=menus[menu_step][0],
                    label2=menus[menu_step][1],
                    label3=menus[menu_step][2],
                    label4=menus[menu_step][3],
                ))

    return menu_step


def ctrl_default_entry_action(
        hub: Hub,
        menu_name: str,
        sub_title: str | None = None,
):
    """Update menu titles on screen (default action on entering
    menu)."""
    logger.debug("ctrl_act_publish_config_title: menu_name='%s'",
                 menu_name)
    hub.publish(
        topic=TOPICS.SCREEN,
        message=message_config_title(
            title=menu_name,
            sub_title=sub_title))


def ctrl_act_set_menu_buttons(
        hub: Hub,
        labels: List[str]


):
    """Set button labels from 'menus' for 'set_menu_step'

    Sends 'TOPICS.SCREEN_MESSAGES.BUTTON_TXT' message to TOPICS.SCREEN.

    :menus: list of list of button labels (btn1_short, btn1_long,
    btn2_short, btn2_long)

    """
    logger.info("ctrl_act_set_menu_buttons: labels='%s'", labels)
    # set menu button labels on screen
    hub.publish(topic=TOPICS.SCREEN,
                message=message_button_labels(
                    label1=labels[0],
                    label2=labels[1],
                    label3=labels[2],
                    label4=labels[3],
                ))


def ctrl_act_do_load_channels(hub: Hub) -> bool:
    """Load channels from url on config screen.

    Url to read configurations from 'controller_state.keyboard_entry''

    On load error output error message and resume back where load
    invoked (ctrl_act_load_channels).

    On success add yaml to configuration entries.

    :return:

    """
    raise NotImplemented("Should be fixed")
    # Keyboard entry is the url we are reading
    url = controller_state.keyboard_entry
    logger.info("ctrl_act_do_load_channels: url='%s'", url)

    # Read url content
    yaml_str, status = read_file(url=url)
    if not status:
        logger.error("ctrl_act_do_load_channels: url='%s', error:'%s'",
                     url, yaml_str)
        return status

    logger.info("ctrl_act_do_load_channels: url='%s', yaml_str:'%s'",
                url, yaml_str)
    new_channels = parse_channels(yaml_str)

    # convert icons to streaming thumbs (read icon address )
    add_channel_icons(channels=new_channels, yaml_url=url)

    # Icons just base name
    for channel in new_channels:
        channel.icon = os.path.basename(channel.icon)

    # Add to active streams
    controller_state.streams += new_channels
    logger.debug("ctrl_act_do_load_channels: streams='%s'",
                 controller_state.streams)

    return status


def ctrl_act_stop_stream(hub: Hub):
    """Stop streaming.

    Actions:
    - publish 'stream_stop' on STREAMER
    - publish '' on SCREEN
    """
    # --> STREAMER: stop streaming

    hub.publish(
        topic=TOPICS.STREAMER,
        message=message_streamer_stop()
    )

    # No change in streamer process ASIS, streamer process TOBE False
    controller_state.set_streamer_status(running=None, streamer_on=False)

    # --> SCREEN: clear streaming icon
    msg_icons = message_screen_stream_icon(icon="")
    logger.debug("ctrl_act_stop_stream: msg='%s'", msg_icons)
    hub.publish(
        topic=TOPICS.SCREEN,
        message=msg_icons,
    )


def ctrl_act_keyboard_start(hub: Hub):
    """Start reading keyboard.

    Actions:
    - publish 'START' on KEYBOARD.TOPIC

    - set sprite icon - keyboard not connected (update in status
      query)

    """
    # --> STREAMER: stop streaming

    hub.publish(
        topic=TOPICS.KEYBOARD,
        message=message_keyboard_start()
    )

    # controller_state.set_keyboard_status(keyboard_status=False)


def ctrl_act_poll_keyboard_status(hub: Hub):
    """Check keyboard status


    """

    controller_state.set_keyboard_status(is_keyboard_connected())


def ctrl_act_keyboard_stop(hub: Hub):
    """Stop reading keyboard.

    Actions:
    - publish 'STOP' on KEYBOARD.TOPIC
    """
    # --> STREAMER: stop streaming

    hub.publish(
        topic=TOPICS.KEYBOARD,
        message=message_keyboard_stop()
    )


def ctrl_act_set_stream(hub: Hub, stream_adv: int = 0) -> int:
    """Start streaming, optionally advance next/prev stream.

    Advances stream by stream_adv (next/current/prev), sends message
    to 'SCREEN' set stream icon, and to 'STREAMER' to set url.

    Sets 'streamer_on' in contreoller state (=TOBE value for streamer
    -process).

    :stream_adv: -1 prev, +1 next, 0 no change

    :return: current_stream

    """

    # dataclass StreamConfig
    stream_config = controller_state.set_and_get_stream(stream_adv=stream_adv)
    logger.info("ctrl_act_set_stream: stream_config: %s", stream_config)

    # streamer/ASIS='not running', streamer/TOBE=True
    controller_state.set_streamer_status(
        running=False, streamer_on=True)

    if stream_config is None:
        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_config_title(
                title="Ei radioita",
                sub_title="Lisää asetuksista"))
        return 0

    # Change stream icon on SCREEN
    hub.publish(
        topic=TOPICS.SCREEN,
        message=message_screen_stream_icon(icon=stream_config.icon)
    )

    # Change url for STREAM
    hub.publish(
        topic=TOPICS.STREAMER,
        message=message_streamer_start(url=stream_config.url)
    )
    return controller_state.current_stream


def ctr_act_none(hub: Hub):
    return None


def ctrl_act_null(hub: Hub):
    return None


def ctrl_act_next_prev(hub: Hub, advance: int, menu: Dict) -> int:
    """Default action to step next/prev ̈́menu_step'in 'menu'.

    Uses module global 'controller.menu_step' -variable.

    :menu: see documentation in 'f_config_enter'
    """
    # List of menu names pointed by 'controller_state.menu_step'
    menus = [k for k in menu.keys()]

    # List of List for menu button labels, pointed by
    # 'controller_state.menu_step'
    btn_labels = [menu[menu_name][APP_CONTEXT.MENU.ACTS.BTN_LABELS]
                  for menu_name in menus]

    # ctrl_act_menu_next_prev_TODO(
    #     hub=hub, advance=advance, menus=btn_labels)

    menu_step = controller_state.menu_step_advance(
        advance=advance,
        menus=menus)
    logger.debug(
        "ctrl_act_next_prev: menu_step='%s', menus: %s btn_labels: % s",
        menu_step, menus, btn_labels)

    # Return step advanced to
    return menu_step


def ctrl_act_key_to_dscreen(hub: Hub, key: str) -> int | None:
    """Pass keyboard 'key' to dscreen (in controller).

    :return: None no menu change
    """

    logger.info("ctrl_act_key_to_dscreen: key='%s'", key)

    # Put input to  dscreen (data screen)
    stat = controller_state.config_screens.putInput(dataIn=key)
    if not stat:
        logging.log(logging.ERROR, "Error '%s' in 'putInput(dataIn=%s)'",
                    controller_state.config_screens.lastError, key
                    )
        return None

    # Read dscreen message - and publish it display
    msg = controller_state.config_screens.message()
    hub.publish(topic=TOPICS.SCREEN, message=msg)

    return None


# ------------------------------------------------------------------
# Menu entreess

def ctrl_menu_wifi_ssid_setup(
        hub: Hub,
        wifi_ssid: str,
        ctrl_menu_resume: Callable,
        caller_menu_step: int,
):
    """Start wifi-setup.

    :wifi_ssid: ssid to setup

    Actions:
    - Open screen overlay WIFI for wifi_ssid.
    - Extract WIFI-message for overlay
    - Publish WIFI-message to SCREEN
    - Enter wifi setup menu

    :wifi_ssid: SSID string

    :return: None
    """
    logger.info("ctrl_menu_wifi_ssid_setup: wifi_ssid='%s', kb: '%s'",
                wifi_ssid, controller_state.get_keyboard_status)

    # remeber caller menu - later resume there
    # caller_menu_step = controller_state.menu_step

    def _enter_wifi_ssid_setup(hub: Hub, menu_name: str):
        """Publish SCREEN -message to display wifi-setup overlay."""
        logger.debug("_enter_wifi_ssid_setup: menu_name='%s'", menu_name)
        ctrl_act_update_status(hub, network_status=False)
        controller_state.config_screens.activateScreen(
            DSCREEN.SCREEN_OVERLAYS.WIFI_SETUP,
            init_values=[(DSCREEN.WIFI_OVERLAY.SSID, wifi_ssid),
                         (DSCREEN.WIFI_OVERLAY.PASSWORD, ""),
                         ])
        overlay_msg = controller_state.config_screens.message()
        hub.publish(topic=TOPICS.SCREEN, message=overlay_msg)

    def _resume_from_ssid_setup(hub: Hub):
        ctrl_menu_resume(
            hub=hub,
            step_resume=caller_menu_step,
        )

    def _config_wifi(hub: Hub) -> int | None:
        """Start wifi configuration using configuration in current/active
        screen in 'controller.screen_ovrlays'.

        """

        # read message from current/active dscreen
        overlay_msg = controller_state.config_screens.message()
        logger.debug("ctrl_act_config_wifi: overlay_msg='%s'", overlay_msg)

        # message found
        if overlay_msg is not None:
            ssid = overlay_msg.fieldStrValue(DSCREEN.WIFI_OVERLAY.SSID)
            password = overlay_msg.fieldStrValue(DSCREEN.WIFI_OVERLAY.PASSWORD)
            if ssid is not None and password is not None:
                # mark
                set_wifi_password(ssid=ssid, password=password)
            else:
                logging.log(
                    logging.ERROR,
                    "ctrl_act_config_wifi: could not SSID='%s' or PASSWORD=%s from %s - no action",
                    ssid, password,
                    overlay_msg,
                )
        else:
            logging.log(
                logging.ERROR, "ctrl_act_config_wifi: no overlay_msg - no action")

        _resume_from_ssid_setup(hub)
        # No change in menu
        return None

    menu = {
        "wifi-setup": {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.UN_USED,               # bt1-short
                APP_CONTEXT.MENU.ACTIVATE,              # bt1-long
                APP_CONTEXT.MENU.UN_USED,               # bt2-short
                APP_CONTEXT.MENU.RESUME,                # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _enter_wifi_ssid_setup,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctrl_act_key_to_dscreen,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: ctrl_act_null,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: _config_wifi,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: ctrl_act_null,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_from_ssid_setup
        },  # kb-ok - MENU_INDEX_KB_OK

    }  # menu

    # Only one menu
    f_config_enter(hub, menu=menu, step_resume=0)


def ctrl_menu_setup_with_keyboard(hub: Hub, step_resume: int | None = None):
    """Configuration menu for keyboard setups

    :step_resume: 'menu_step' to resume back (if not None).

    """

    # Default step starts from first wifi selection
    logger.debug("ctrl_menu_setup_with_keyboard: step_resume='%s', menu_step=%s",
                 step_resume, controller_state.menu_step)
    if step_resume is None:
        step_resume = 0

    # remeber caller menu - later resume there
    caller_menu_step = controller_state.menu_step

    if not controller_state.get_keyboard_status:
        ctrl_menu_keyboard_confirm(
            hub,
            ctrl_menu_kb_ok=ctrl_menu_setup_with_keyboard,
            step_kb_ok=None,
            ctrl_menu_cancel=ctrl_menu_setup_main,
            step_cancel=caller_menu_step,
        )
        return

    # Assume keyboard connected

    def _my_entry_action(hub: Hub, menu_name: str, ):
        """Publish title/sub_title, possibly icon"""
        menu_name_2_title = {
            APP_CONTEXT.MENU.MENU_CONFIG_WIFI: "Wifi verkon",
            APP_CONTEXT.MENU.MENU_CHANNELS_ORIGIN: "Radiokanava-",
        }
        menu_name_2_sub_title = {
            APP_CONTEXT.MENU.MENU_CONFIG_WIFI: "valinta",
            APP_CONTEXT.MENU.MENU_CHANNELS_ORIGIN: "hakemiston asetus",
        }

        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_config_title(
                title=menu_name_2_title[menu_name],
                sub_title=menu_name_2_sub_title[menu_name],
            ))

    def _resume_setup(hub: Hub):
        """Resume/enter radio (main)"""
        # Restart radio
        ctrl_menu_setup_main(hub, step_resume=caller_menu_step)

        # No menu step change for action
        return None

    def _setup_channel_origin(hub: Hub):
        logger.error("_setup_channel_origin: TODO")
        return None

    # See f_config_enter for documentation
    menu = {
        APP_CONTEXT.MENU.MENU_CONFIG_WIFI: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.MENU_CHANNELS_ORIGIN,  # bt1-short
                APP_CONTEXT.MENU.CHOOSE,                # bt1-long
                APP_CONTEXT.MENU.MENU_CHANNELS_ORIGIN,  # bt2-short
                APP_CONTEXT.MENU.CONFIG_RETURN,         # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: ctrl_menu_wifi_setup,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_setup,

        },  # wifi setup

        APP_CONTEXT.MENU.MENU_CHANNELS_ORIGIN: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.MENU_CONFIG_WIFI,        # bt1-short
                APP_CONTEXT.MENU.CHOOSE,                  # bt1-long
                APP_CONTEXT.MENU.MENU_CONFIG_WIFI,        # bt2-short
                APP_CONTEXT.MENU.CONFIG_RETURN,           # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: None,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: _setup_channel_origin,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: None,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_setup,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctr_act_none,
        },  # channel origin setup
    }  # menu

    f_config_enter(hub, menu, step_resume=step_resume)


def ctrl_menu_wifi_setup(
        hub: Hub,
        step_resume: int | None = None,
        wifi_names: List[str] | None = None,
        ctrl_menu_resume: Callable = ctrl_menu_setup_with_keyboard,

):
    """Enter wifi config.

    :ctrl_menu_resume: May be called from main setup (without
    keyboard), and from setup with keyboard.

    :step_resume: index to wifi_names (=menu element)

    :wifi_names: pre-populated wifi-names, read wifi names if None.

    - Reads available wifi connections.

    - Creates 'menu' using 'wifi_names'
    - NEXT/PREV wifi SSID -list
    - resume back to config menu
    - choose wifi SSID to setup

    """
    logger.debug("ctrl_menu_wifi_setup: step_resume='%s', menu_step=%s",
                 step_resume, controller_state.menu_step)

    # List of availabe WIFI networks
    if wifi_names is None:
        wifi_names = list_wifis()
    logger.info("ctrl_menu_wifi_setup: wifi_names='%s'", wifi_names)

    # remeber caller menu - later resume there
    caller_menu_step = controller_state.menu_step

    # Default step starts from first wifi selection
    if step_resume is None:
        step_resume = 0

    # Helpers to build btn_labels in menu
    def next_wifi(i):
        return wifi_names[i + 1 if i < len(wifi_names) - 1 else 0]

    def prev_wifi(i):
        return wifi_names[i - 1 if i > 0 else len(wifi_names) - 1]

    def _enter_wifi_setup(hub: Hub, menu_name: str):
        """Publish SCREEN -message to display wifi-setup overlay."""
        logger.debug("_enter_wifi_setup: menu_name='%s'", menu_name)
        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_config_title(
                title=APP_CONTEXT.MENU.MENU_MAYBE_CONFIG_WIFI,
                sub_title=menu_name))

    def _do_resume(hub: Hub):
        # ctrl_menu_setup_with_keyboard(hub, step_resume=caller_menu_step)
        ctrl_menu_resume(hub, step_resume=caller_menu_step)

    # See f_config_enter for documentation
    menu = {
        wifi_names[i]: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.NEXT,           # next_wifi(i),# bt1-short
                APP_CONTEXT.MENU.CHOOSE,         # bt1-long
                APP_CONTEXT.MENU.PREV,           # prev_wifi(i), # bt2-short
                APP_CONTEXT.MENU.CONFIG_RETURN,  # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _enter_wifi_setup,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: partial(
                ctrl_menu_wifi_ssid_setup,
                wifi_ssid=wifi_names[i],
                ctrl_menu_resume=ctrl_menu_resume,
                caller_menu_step=caller_menu_step,
            ),
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _do_resume,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctrl_act_null,
        }
        for i in range(len(wifi_names))
    }

    f_config_enter(hub, menu=menu, step_resume=step_resume)


def ctrl_menu_browse_channels(
        hub: Hub,
        step_resume: int | None = None, ):
    """Browse channels. Menu actions allow delete.

    Acting on controller_state.streams.

    """

    logger.debug("ctrl_menu_browse_channels: step_resume='%s'", step_resume)

    # Default step starts from first wifi selection
    if step_resume is None:
        step_resume = 0

    # remeber caller menu - later resume there
    caller_menu_step = controller_state.menu_step

    def _my_resume(hub):
        # ctrl_menu_setup_main(hub, step_resume=caller_menu_step)
        ctrl_menu_setup_main(hub, step_resume=caller_menu_step)
        return None

    # Helpers to build btn_labels in menu
    def _next_stream_label(i):
        streams = controller_state.streams
        return streams[i + 1 if i < len(streams) - 1 else 0].name

    def _prev_stream_label(i):
        streams = controller_state.streams
        return streams[i - 1 if i > 0 else len(streams) - 1].name

    def _show_stream_info_on_entry(hub: Hub, menu_name: str, stream: StreamConfig):
        logger.debug("_show_stream_info: stream='%s'", stream)
        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_config_title(
                title=APP_CONTEXT.MENU.MENU_CHANNELS_BROWSE,
                sub_title=stream.name,
                imagepath=os.path.join(
                    APP_CONTEXT.CHANNEL_ICONS, stream.icon)
            ))

    # See f_config_enter for documentation
    menu = {
        controller_state.streams[i].name: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                _next_stream_label(i),            # bt1-short
                APP_CONTEXT.MENU.DELETE,          # bt1-long
                _prev_stream_label(i),            # bt2-short
                APP_CONTEXT.MENU.CONFIG_RETURN,   # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: partial(
                _show_stream_info_on_entry,
                stream=controller_state.streams[i],
            ),
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: partial(
                ctrl_menu_chdelete_with_confirm,
                ctrl_menu_resume=ctrl_menu_browse_channels,
                # delete current stream
                stream=controller_state.streams[i],
                step_resume=controller_state.menu_step,
            ),
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _my_resume,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctrl_act_null,
        }
        for i in range(len(controller_state.streams))
    }

    # delete make result to empty menu = No channels --> _my_resume
    if len(menu.keys()) == 0:
        _my_resume(hub)
    else:
        f_config_enter(hub, menu=menu, step_resume=step_resume)


def ctrl_menu_setup_main(hub: Hub, step_resume: int | None = None):
    """Configuration main menu.

    :step_resume: 'menu_step' to resume back (if not None).

    """

    # Default step starts from first wifi selection
    logger.debug("ctrl_menu_setup_main: step_resume='%s', menu_step=%s",
                 step_resume, controller_state.menu_step)
    if step_resume is None:
        step_resume = 0

    # remeber caller menu - later resume there
    caller_menu_step = controller_state.menu_step

    # NOTICE: Must match menu keys!
    menu_name_2_title = {
        APP_CONTEXT.MENU.MENU_CHANNELS_BROWSE: "Selaa",
        APP_CONTEXT.MENU.MENU_CHANNELS_DEL_ALL: "Poista",
        APP_CONTEXT.MENU.MENU_ACTIVATE_CHANNELS: "Aktivoi",
        APP_CONTEXT.MENU.MENU_CONFIG_WIFI: "Valitse",
        APP_CONTEXT.MENU.MENU_CONFIG_KEYBOARD: "Asetukset",
        APP_CONTEXT.MENU.MENU_REBOOT: "Uudelleen",
    }
    menu_name_2_sub_title = {
        APP_CONTEXT.MENU.MENU_CHANNELS_BROWSE: "kanavia",
        APP_CONTEXT.MENU.MENU_CHANNELS_DEL_ALL: "kaikki kanavat",
        APP_CONTEXT.MENU.MENU_ACTIVATE_CHANNELS: "kanavia",
        APP_CONTEXT.MENU.MENU_CONFIG_WIFI: "Wifi-verkko",
        APP_CONTEXT.MENU.MENU_CONFIG_KEYBOARD: "näppäimistöllä",
        APP_CONTEXT.MENU.MENU_REBOOT: "käynnistys",
    }

    ssid_in_use = current_ssid()
    ip_in_use = current_IP()

    def _my_entry_action(hub: Hub, menu_name: str, ):
        """Publish title/sub_title, possibly icon"""
        # hub.publish(
        #     topic=TOPICS.SCREEN,
        #     message=message_config_title(
        #         title=menu_name_2_title[menu_name],
        #         sub_title=menu_name_2_sub_title[menu_name]))
        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_network_info(
                title=menu_name_2_title[menu_name],
                sub_title=menu_name_2_sub_title[menu_name],
                ip=ip_in_use,
                ssid=ssid_in_use,
            ))

    def _boot_entry(hub: Hub, menu_name: str):
        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_config_title(
                title=APP_CONTEXT.MENU.MAY_REBOOT_TITLE,
                sub_title=APP_CONTEXT.MENU.MAY_REBOOT_SUBTITLE))

    def _maybe_browse_channels(hub: Hub):
        if len(controller_state.streams) > 0:
            ctrl_menu_browse_channels(hub=hub)
        else:
            ctrl_act_screen_info_txt(hub, message="Ei kanavia")
        return None

    def _resume_radio(hub: Hub):
        """Resume/enter radio (main)"""
        # Restart radio
        f_radio_enter(hub, step_resume=caller_menu_step)

        # No menu step change for action
        return None

    # See f_config_enter for documentation
    menu = {

        APP_CONTEXT.MENU.MENU_CHANNELS_BROWSE: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.NEXT,                    # bt1-short
                APP_CONTEXT.MENU.CHOOSE,                  # bt1-long
                APP_CONTEXT.MENU.PREV,                    # bt2-short
                APP_CONTEXT.MENU.CONFIG_RADIO,            # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: None,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: _maybe_browse_channels,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: None,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_radio,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctr_act_none,
        },  # Browse channels

        APP_CONTEXT.MENU.MENU_CHANNELS_DEL_ALL: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.NEXT,                    # bt1-short
                APP_CONTEXT.MENU.CHOOSE,                  # bt1-long
                APP_CONTEXT.MENU.PREV,                    # bt2-short
                APP_CONTEXT.MENU.CONFIG_RADIO,            # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: None,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: partial(
                ctrl_menu_chdelete_with_confirm,
                stream=None,  # delete all
                ctrl_menu_resume=ctrl_menu_setup_main,
                step_resume=controller_state.menu_step,
            ),
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: None,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_radio,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctr_act_none,
        },  # Delete all channels

        APP_CONTEXT.MENU.MENU_ACTIVATE_CHANNELS: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.NEXT,                    # bt1-short
                APP_CONTEXT.MENU.CHOOSE,                  # bt1-long
                APP_CONTEXT.MENU.PREV,                    # bt2-short
                APP_CONTEXT.MENU.CONFIG_RADIO,            # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: None,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: ctrl_menu_activate_channels,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: None,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_radio,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctr_act_none,
        },  # Activate channels

        APP_CONTEXT.MENU.MENU_CONFIG_WIFI: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.NEXT,                  # bt1-short
                APP_CONTEXT.MENU.CHOOSE,                # bt1-long
                APP_CONTEXT.MENU.PREV,                  # bt2-short
                APP_CONTEXT.MENU.CONFIG_RADIO,          # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: partial(
                ctrl_menu_wifi_setup,
                ctrl_menu_resume=ctrl_menu_setup_main,
            ),
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_radio,
        },  # wifi setup

        APP_CONTEXT.MENU.MENU_CONFIG_KEYBOARD: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.NEXT,                  # bt1-short
                APP_CONTEXT.MENU.CHOOSE,                # bt1-long
                APP_CONTEXT.MENU.PREV,                  # bt2-short
                APP_CONTEXT.MENU.CONFIG_RADIO,          # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: ctrl_menu_setup_with_keyboard,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_radio,

        },  # keyboard setup

        APP_CONTEXT.MENU.MENU_REBOOT: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.NEXT,                    # btn1-short
                APP_CONTEXT.MENU.CHOOSE,                  # btn1-long
                APP_CONTEXT.MENU.PREV,                    # btn2-short
                APP_CONTEXT.MENU.CONFIG_RADIO,            # btn2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _boot_entry,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: ctrl_act_reboot,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _resume_radio,
        },  # MENU_REBOOT
    }

    f_config_enter(hub, menu, step_resume=step_resume)


def ctrl_menu_activate_channels(hub: Hub, step_resume: int | None = None):
    """Browse list of channels, which may be activated.
    """

    if step_resume is None:
        step_resume = 0

    # remeber caller menu - later resume there
    caller_menu_step = controller_state.menu_step

    def _my_resume(hub):
        # ctrl_menu_setup_main(hub, step_resume=caller_menu_step)
        ctrl_menu_setup_main(hub, step_resume=caller_menu_step)
        return None

    activation_url = app_config.channel_activation_url
    logger.info("ctrl_menu_activate_channels: yaml_url='%s'", activation_url)
    try:
        active_streams = [
            stream_config.name for stream_config in controller_state.streams]
        channels_for_activation = [
            stream_config
            for stream_config in
            channel_activation_list(activation_url=activation_url) if
            stream_config.name not in active_streams]
    except FileNotFoundError as ex:
        logger.exception("Error %s in channel_activation_list, activation_url",
                         ex, app_config.channel_activation_url)
        return

    if len(channels_for_activation) == 0:
        ctrl_menu_error_confirm(
            hub,
            error="Ei uusia kanavia",
            ctrl_menu_cancel=ctrl_menu_setup_main,
            step_cancel=caller_menu_step,
        )
        return

    def _next_stream_label(i):
        return channels_for_activation[i + 1 if i < len(channels_for_activation) - 1 else 0].name

    def _prev_stream_label(i):
        return channels_for_activation[i - 1 if i > 0 else len(channels_for_activation) - 1].name

    def _show_stream_info(hub: Hub, menu_name: str, indx: int, stream: StreamConfig):
        logger.debug("_show_stream_info: stream='%s'", stream)
        # find url to channel
        yaml_url = channel_activation_index(activation_url)
        imagepath = channel_icon_image(
            channels_for_activation[indx], yaml_url=yaml_url)
        logger.debug(
            "_show_stream_info: imagepath='%s', yaml_url=%s, activation_url=%s",
            imagepath, yaml_url, activation_url)
        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_config_title(
                title=APP_CONTEXT.MENU.MAY_ACTIVATE,
                sub_title=stream.name,
                imagepath=imagepath,
            ))

    menu = {
        channels_for_activation[i].name: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                _next_stream_label(i),            # bt1-short
                APP_CONTEXT.MENU.ACTIVATE,        # bt1-long
                _prev_stream_label(i),            # bt2-short
                APP_CONTEXT.MENU.CONFIG_RETURN,   # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: partial(
                _show_stream_info,
                indx=i,
                stream=channels_for_activation[i],
            ),
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: partial(
                ctrl_menu_activate_with_confirm,
                activation_url=activation_url,
                ctrl_menu_resume=ctrl_menu_activate_channels,
                step_resume=i,
                channel=channels_for_activation[i],
            ),
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _my_resume,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctrl_act_null,
        }
        for i in range(len(channels_for_activation))
    }

    f_config_enter(hub, menu, step_resume=step_resume)


def ctrl_menu_activate_with_confirm(
        hub: Hub,
        channel: StreamConfig,
        activation_url: str,
        ctrl_menu_resume: Callable,
        step_resume: int,
):
    """Ask confirmation to activate 'channel'.

    :ctrl_menu_resume: lambda of controller where to resume back to.

    :step_resume: menu_step to resume to 'ctrl_menu_resume' -lambda

    :stream: new stream to activate
    """
    logger.info("ctrl_menu_activate_with_confirm: activation_url='%s, channel=%s",
                activation_url, channel.name)

    def _entry_to_confirmation(hub: Hub, menu_name: str | None):
        """Ask for confirmation to activate 'stream'.
        """
        # confirm delete on one channel
        yaml_url = channel_activation_index(activation_url)
        imagepath = channel_icon_image(
            channel, yaml_url=yaml_url)

        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_question(
                title=APP_CONTEXT.MENU.MAY_ACTIVATE,
                question=f"Kanava '{channel.name}'",
                imagepath=imagepath,
            ))

    def _do_resume(hub: Hub):
        """Continue in lambda passed in parameter 'ctrl_menu_resume'."""
        # ctrl_menu_browse_channels(hub=hub, step_resume=step_resume)
        ctrl_menu_resume(hub, step_resume=step_resume)

    def _do_activate_stream(hub: Hub, new_stream: StreamConfig):
        """Active 'new_stream'. Resume back to 'step_resume' in upper
        menu.

        """
        controller_state.streams = channel_activate(
            controller_state.streams,
            new_stream=new_stream,
            activation_url=activation_url,
        )
        _do_resume(hub)

    # See f_config_enter for documentation

    menu = {
        "actvate": {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.UN_USED,         # bt1-short
                APP_CONTEXT.MENU.ACTIVATE_CONFIRM,  # bt1-long
                APP_CONTEXT.MENU.UN_USED,         # bt2-short
                APP_CONTEXT.MENU.CONFIG_RETURN,   # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _entry_to_confirmation,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: partial(
                _do_activate_stream,
                new_stream=channel,
            ),
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _do_resume,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctrl_act_null,
        }
    }

    # Start executing menu
    f_config_enter(hub, menu=menu, step_resume=0)


def ctrl_menu_setup_channel_origin(hub: Hub, step_resume: int | None = None):
    """Menu to load channels from url.

    TODO: should update configuration

    menu_step -values:
    0 : data entry screen
    1 : loading finished
    2 : loading error

    Add to menu configuration screen:
    -prompt: URL to load channels from
    -value: default url value

    On MsgKey: 1) edit buffer in control_state, 2) put formatted
    buffer on config value

    """

    logger.debug("ctrl_menu_load_channels_url: step_resume='%s'", step_resume)

    # remeber caller menu - later resume there
    caller_menu_step = controller_state.menu_step

    # no advance beyond this point when NO keyboard
    if not controller_state.get_keyboard_status:
        ctrl_menu_keyboard_confirm(
            hub,
            ctrl_menu_kb_ok=ctrl_menu_setup_channel_origin,
            step_kb_ok=None,
            ctrl_menu_cancel=ctrl_menu_setup_main,
            step_cancel=caller_menu_step,
        )
        return

    # Keyboard is connected

    # Allow fwd reference to access menu
    menu = {}

    def _status_to_step(status: bool) -> int:
        """:return: index to menu step"""
        return 1 if status else 2

    def _keyboard_input(hub, key):
        """Collect key presses in controller_state buffer."""
        current_input = controller_state.keyboard_key(key=key)
        # show current input on screen
        formatted_input = split_buffer(
            current_input,
            line_limit=APP_CONTEXT.SCREEN.VALUE_FIELD_WIDTH)
        ctrl_act_screen_config_prompt(
            hub=hub,
            prompt=APP_CONTEXT.MENU.LOAD_CHANNELS_DEFAULTS.PROMP,
            value=formatted_input,
        )
        return None

    def _menu_act_load(hub: Hub):
        """Choose menu_step after looad OK/failuer"""
        status = ctrl_act_do_load_channels(hub)

        # Choose of steps below
        set_menu_step = _status_to_step(status)
        return set_menu_step

    def _menu_act_resume(hub):
        # TODO: add code to resume where started from
        ctrl_menu_setup_main(hub)
        return None

    def _enter_url_loading(hub, menu_name: str):
        """Activate DSCREEN with initial values, and send overlay
        messsage to show the values on screen.
        """
        logger.debug("_enter_url_loading: menu_name='%s'", menu_name)
        # Init data screen (dscreen)
        controller_state.config_screens.activateScreen(
            DSCREEN.SCREEN_OVERLAYS.URL_LOAD,
            init_values=[
                (DSCREEN.URL_LOAD_OVERLAY.TITLE,
                 APP_CONTEXT.MENU.LOAD_CHANNELS_DEFAULTS.PROMP,
                 ),
                (DSCREEN.URL_LOAD_OVERLAY.URL_BASE,
                 APP_CONTEXT.MENU.LOAD_CHANNELS_DEFAULTS.DEFAULT_URL),
                (DSCREEN.URL_LOAD_OVERLAY.YAML_FILE,
                 APP_CONTEXT.MENU.LOAD_CHANNELS_DEFAULTS.YAML,
                 )
            ])
        # Show initial values on screen
        overlay_msg = controller_state.config_screens.message()
        hub.publish(topic=TOPICS.SCREEN, message=overlay_msg)

    # See f_config_enter for documentation
    menu = {
        APP_CONTEXT.MENU.LOAD_CHANNELS: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.UN_USED,         # bt1-short
                APP_CONTEXT.MENU.DO_LOAD,         # bt1-long
                APP_CONTEXT.MENU.UN_USED,         # bt2-short
                APP_CONTEXT.MENU.CONFIG_RETURN,   # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _enter_url_loading,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: _menu_act_load,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: partial(
                ctrl_menu_setup_main,
                step_resume=caller_menu_step),
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctrl_act_key_to_dscreen,
        },  # Load

        APP_CONTEXT.MENU.MENU_SUCCESS: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.UN_USED,         # bt1-short
                APP_CONTEXT.MENU.UN_USED,         # bt1-long
                APP_CONTEXT.MENU.UN_USED,         # bt2-short
                APP_CONTEXT.MENU.CONFIG_OK,       # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: None,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _menu_act_resume,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctr_act_none,
        },  # OK

        APP_CONTEXT.MENU.MENU_FAILURE: {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.UN_USED,         # bt1-short
                APP_CONTEXT.MENU.UN_USED,         # bt1-long
                APP_CONTEXT.MENU.UN_USED,         # bt2-short
                APP_CONTEXT.MENU.CONFIG_OK,       # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: None,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _menu_act_resume,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctr_act_none,
        },  # ERROR

    }

    # Start from first menu element above
    controller_state.menu_state_resume(0)

    if step_resume is None:
        step_resume = 0

    f_config_enter(hub, menu=menu, step_resume=step_resume)

# ------------------------------------------------------------------
# Callable sub-menus


def ctrl_menu_error_confirm(
        hub: Hub,
        error: str,
        ctrl_menu_cancel: Callable,
        step_cancel: int | None,
        instructions: str | None = None,
):
    """Report error and wait for any button-press.

    :instructions: default text 'Paina jotain näppäintä jatkaaksesi'.

    """
    logger.debug("ctrl_menu_error_confirm - starting, error=%s", error)
    if instructions is None:
        instructions = "Paina jotain näppäintä jatkaaksesi"

    def _my_entry(hub: Hub, menu_name: str):
        logger.debug("_enter_no_keyboard: menu_name='%s'", menu_name)
        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_error(
                error=error,
                instructions=instructions))

    def _do_resume(hub: Hub):
        """Continue in lambda passed in parameter 'ctrl_menu_resume'."""
        # ctrl_menu_browse_channels(hub=hub, step_resume=step_resume)
        ctrl_menu_cancel(hub, step_resume=step_cancel)

    menu = {
        "kb-nok": {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.RESUME,               # bt1-short
                APP_CONTEXT.MENU.RESUME,              # bt1-long
                APP_CONTEXT.MENU.RESUME,               # bt2-short
                APP_CONTEXT.MENU.RESUME,                # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctrl_act_null,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: _do_resume,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: _do_resume,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: _do_resume,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _do_resume
        }  # kb-nok MENU_INDEX_KB_NOK

    }  # menu

    f_config_enter(hub, menu=menu, step_resume=0)


def ctrl_menu_keyboard_confirm(
        hub: Hub,
        ctrl_menu_kb_ok: Callable,
        step_kb_ok: int | None,
        ctrl_menu_cancel: Callable,
        step_cancel: int | None,
):
    """Wait for keyboard connection and key-press before resuming to
    'ctrl_menu_kb_ok'. Button2 long resume back to 'ctrl_menu_cancel'.

    """
    logger.debug("ctrl_menu_keyboard_confirm - starting")

    def _my_entry(hub: Hub, menu_name: str):
        logger.debug("_enter_no_keyboard: menu_name='%s'", menu_name)
        hub.publish(
            topic=TOPICS.SCREEN,
            message=message_error(
                error=APP_CONTEXT.MENU.KB_NOK,
                instructions=APP_CONTEXT.MENU.KB_ACT))

    def _do_resume(hub: Hub):
        """Continue in lambda passed in parameter 'ctrl_menu_resume'."""
        # ctrl_menu_browse_channels(hub=hub, step_resume=step_resume)
        ctrl_menu_cancel(hub, step_resume=step_cancel)

    def _first_key_pressed(hub: Hub, key):
        """First key on keyboard pressed -> kb-ok menu"""
        logger.info("_first_key_pressed: key='%s'", key)
        ctrl_menu_kb_ok(hub, step_resume=step_kb_ok)

    menu = {
        "kb-nok": {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.UN_USED,               # bt1-short
                APP_CONTEXT.MENU.UN_USED,              # bt1-long
                APP_CONTEXT.MENU.UN_USED,               # bt2-short
                APP_CONTEXT.MENU.RESUME,                # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: _first_key_pressed,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: ctrl_act_null,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: ctrl_act_null,
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: ctrl_act_null,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _do_resume
        }  # kb-nok MENU_INDEX_KB_NOK

    }  # menu

    f_config_enter(hub, menu=menu, step_resume=0)


def ctrl_menu_chdelete_with_confirm(
        hub: Hub,
        stream: StreamConfig | None,
        ctrl_menu_resume: Callable,
        step_resume: int,
):
    """Confirm delete 'stream_name' in 'controller_state.streams'.


    :stream: Stream about to be deleted, delete all streams if None.

    :ctrl_menu_resume: lambda of controller where to resume back to.

    :step_resume: menu_step to resume to 'ctrl_menu_resume' -lambda

    """

    def _entry_to_confirmation(hub: Hub, menu_name: str | None):
        """Ask for confirmation to delete 'stream'.

        :stream: if None ask confirmation to delete all streams.

        """
        if stream is not None:
            # confirm delete on one channel
            hub.publish(
                topic=TOPICS.SCREEN,
                message=message_question(
                    title=APP_CONTEXT.MENU.MAY_DELETE,
                    question=f"Kanava '{stream.name}'",
                    imagepath=icon_path(stream),
                    # imagepath=os.path.join(
                    #     APP_CONTEXT.CHANNEL_ICONS, stream.icon)
                ))
        else:
            # confirm delete on all channel
            hub.publish(
                topic=TOPICS.SCREEN,
                message=message_question(
                    title=APP_CONTEXT.MENU.MAY_DELETE,
                    question="kaikki kanavat?",
                    imagepath=os.path.join(
                        APP_CONTEXT.APP_RESOURCES, "question-100.png")
                ))

    def _do_resume(hub: Hub):
        """Continue in lambda passed in parameter 'ctrl_menu_resume'."""
        # ctrl_menu_browse_channels(hub=hub, step_resume=step_resume)
        ctrl_menu_resume(hub, step_resume=step_resume)

    def _do_delete_stream(hub: Hub, stream_name: str | None):
        """Delete 'stream_name'. Resume back to 'step_resume' in upper
        menu.

        :stream_name: delete named stream or delete all streams if
        'stream_name' is None.

        """
        controller_state.delete_stream(name=stream_name)
        _do_resume(hub)

    # See f_config_enter for documentation

    menu = {
        "delete": {
            APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
                APP_CONTEXT.MENU.UN_USED,         # bt1-short
                APP_CONTEXT.MENU.DELETE_CONFIRM,  # bt1-long
                APP_CONTEXT.MENU.UN_USED,         # bt2-short
                APP_CONTEXT.MENU.CONFIG_RETURN,   # bt2-long
            ],
            APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _entry_to_confirmation,
            APP_CONTEXT.MENU.ACTS.BTN1_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN1_LONG: partial(
                _do_delete_stream,
                stream_name=stream.name if stream is not None else None
            ),
            APP_CONTEXT.MENU.ACTS.BTN2_SHORT: ctr_act_none,
            APP_CONTEXT.MENU.ACTS.BTN2_LONG: _do_resume,
            APP_CONTEXT.MENU.ACTS.KEYBOARD: ctrl_act_null,
        }
    }

    # Start executing menu
    f_config_enter(hub, menu=menu, step_resume=0)


# def ctrl_menu_channel_setup(hub: Hub, step_resume: int | None = None):
#     """Menu for choosing actions in channel setup.

#     """
#     logger.debug("ctrl_menu_channel_setup: step_resume='%s', menu_step=%s",
#                  step_resume, controller_state.menu_step)

#     # Default step starts from first wifi selection
#     if step_resume is None:
#         step_resume = 0

#     # remeber caller menu - later resume there
#     caller_menu_step = controller_state.menu_step

#     def _my_resume(hub):
#         ctrl_menu_setup_main(hub, step_resume=caller_menu_step)
#         return None

#     # NOTICE: update menu_name_2_title and menu_name_2_sub_title
#     # when updating menu

#     menu_name_2_title = {
#         APP_CONTEXT.MENU.MENU_CHANNELS_BROWSE: "Selaa",
#         APP_CONTEXT.MENU.MENU_CHANNELS_ADD: "Lisää",
#         APP_CONTEXT.MENU.MENU_CHANNELS_LOAD_URL: "Kanavien",
#         APP_CONTEXT.MENU.MENU_CHANNELS_DEL_ALL: "Poista kaikki",
#         # APP_CONTEXT.MENU.MENU_CHANNELS_RESET: "Resetoi",
#     }
#     menu_name_2_sub_title = {
#         APP_CONTEXT.MENU.MENU_CHANNELS_BROWSE: "kanavia",
#         APP_CONTEXT.MENU.MENU_CHANNELS_ADD: "kanava",
#         APP_CONTEXT.MENU.MENU_CHANNELS_LOAD_URL: "URL -latus",
#         APP_CONTEXT.MENU.MENU_CHANNELS_DEL_ALL: "kanavat",
#         # APP_CONTEXT.MENU.MENU_CHANNELS_RESET: "kanavat",
#     }

#     def _my_entry_action(hub: Hub, menu_name: str, ):
#         hub.publish(
#             topic=TOPICS.SCREEN,
#             message=message_config_title(
#                 title=menu_name_2_title[menu_name],
#                 sub_title=menu_name_2_sub_title[menu_name]))

#     def _maybe_brose_channels(hub: Hub):
#         if len(controller_state.streams) > 0:
#             ctrl_menu_browse_channels(hub=hub)
#         else:
#             ctrl_act_screen_info_txt(hub, message="Ei kanavia")
#         return None

#     # NOTICE: update menu_name_2_title and menu_name_2_sub_title
#     # when updating menu

#     menu = {
#         APP_CONTEXT.MENU.MENU_CHANNELS_BROWSE: {
#             APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
#                 APP_CONTEXT.MENU.MENU_CHANNELS_ADD,       # bt1-short
#                 APP_CONTEXT.MENU.CHOOSE,                  # bt1-long
#                 APP_CONTEXT.MENU.MENU_CHANNELS_DEL_ALL,   # bt2-short
#                 APP_CONTEXT.MENU.CONFIG_RETURN,           # bt2-long
#             ],
#             APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
#             APP_CONTEXT.MENU.ACTS.BTN1_SHORT: None,
#             APP_CONTEXT.MENU.ACTS.BTN1_LONG: _maybe_brose_channels,
#             APP_CONTEXT.MENU.ACTS.BTN2_SHORT: None,
#             APP_CONTEXT.MENU.ACTS.BTN2_LONG: _my_resume,
#             APP_CONTEXT.MENU.ACTS.KEYBOARD: ctr_act_none,
#         },  # Browse channels

#         APP_CONTEXT.MENU.MENU_CHANNELS_ADD: {
#             APP_CONTEXT.MENU.ACTS.BTN_LABELS: [
#                 APP_CONTEXT.MENU.MENU_CHANNELS_LOAD_URL,  # bt1-short
#                 APP_CONTEXT.MENU.CHOOSE,                  # bt1-long
#                 APP_CONTEXT.MENU.MENU_CHANNELS_BROWSE,    # bt2-short
#                 APP_CONTEXT.MENU.CONFIG_RETURN,           # bt2-long
#             ],
#             APP_CONTEXT.MENU.ACTS.ENTRY_ACTION: _my_entry_action,
#             APP_CONTEXT.MENU.ACTS.BTN1_SHORT: None,
#             APP_CONTEXT.MENU.ACTS.BTN1_LONG: ctr_act_none,
#             APP_CONTEXT.MENU.ACTS.BTN2_SHORT: None,
#             APP_CONTEXT.MENU.ACTS.BTN2_LONG: _my_resume,
#             APP_CONTEXT.MENU.ACTS.KEYBOARD: ctr_act_none,
#         },  # Add channel

#     }

#     if step_resume is None:
#         step_resume = 0
#     f_config_enter(hub, menu=menu, step_resume=step_resume)


# ------------------------------------------------------------------
# State machines

def f_config_enter(hub: Hub,
                   menu: Dict,
                   step_resume: int | None = None,
                   info_message: str | None = None,
                   ):
    """Enter config statemachine, messages are processed in 'f_config'.

    :step_resume: optionally resume menu step.

    controller_state.menu_step keeps track, where we are in
    'menu'.  btn1_short and btn2_short hardwired to advance menu
    choice in 'menu'.

    :menu: dict of dicts. First level maps 'menu_names' to dict for
    menu configuration -dict. Keys for menu configuration -dict:

    - ENTRY_ACTION: Lamba to execute, when entering menu. Default
    action ctrl_act_default_menu_enter.

    - APP_SCREEN: Name of data screen (indexing DApp.screens) with
    content passed to screen using 'TOPICS.SCREEN_MESSAGES.DSCREEN'.
    (if not defined use 'TOPICS.SCREEN_MESSAGES.CONFIG_MENU'
     -message).

    - BTN_LABELS: list of lenght 4 to set btn1-short, btn1-long,
    btn2-short, btn2-long

    - BTN1_LONG: lamdba to call for btn1-long

    - BTN2_LONG: lamdba to call for btn2-long

    - BTN1-SHORT and BTN2-SHORT: default advance fwd/bacward in 'menu'

    """

    logger.info("**f_config_enter - starting**, step_resume='%s'",
                step_resume)

    # optionall flash info message on screeen
    if info_message is not None:
        ctrl_act_screen_info_txt(hub, message=info_message)

    # List of menu names pointed by 'controller_state.menu_step'
    menu_names = [k for k in menu.keys()]
    logger.debug("f_config_enter: menu_names='%s'", menu_names)

    def _menu_entry(menu_step: int):
        """Switch to  'menu[menus_names[menu_step]]'

        :menu_step: index to to menu_names.

        """
        if menu_step not in range(len(menu_names)):
            msg = f"_menu_entry: menu_step='{menu_step}' not in {range(len(menu_names))}, {menu_names=}"
            logger.error(msg)
            # raise KeyError(msg)
            return

        menu_name = menu_names[menu_step]
        logger.debug(
            "_menu_entry: enter menu menu_step='%s', menu_name='%s'",
            menu_step, menu_name)

        # Allways set menu buttons
        ctrl_act_set_menu_buttons(
            hub, labels=menu[menu_name][APP_CONTEXT.MENU.ACTS.BTN_LABELS])

        # Enter new menu
        if (APP_CONTEXT.MENU.ACTS.ENTRY_ACTION not in menu[menu_name] or
                menu[menu_name][APP_CONTEXT.MENU.ACTS.ENTRY_ACTION] is None):
            # default entry action: set menu title
            ctrl_default_entry_action(hub=hub,
                                      menu_name=menu_name,)
        elif menu[menu_name][APP_CONTEXT.MENU.ACTS.ENTRY_ACTION] is not None:
            menu[menu_name][APP_CONTEXT.MENU.ACTS.ENTRY_ACTION](
                hub=hub, menu_name=menu_name)

    def f_config(msg: str | MsgRoot, hub: Hub) -> bool:
        """Config statemachine w. state_machine_state)"""
        logger.debug("f_config: msg: %s", msg)
        goon = True

        # menu_name = menu_names[controller_state.menu_step] if controller_state.menu_step < len(
        #     menu_names) else ""
        if controller_state.menu_step > len(menu_names) or controller_state.menu_step < 0:
            logger.error(
                "f_config: controller_start.menu_step='%s', menu_names= % s",
                controller_state.menu_step,
                menu_names)
            goon = False
            return goon
        try:
            menu_name = menu_names[controller_state.menu_step]
        except IndexError:
            logger.error(
                "f_config: controller_start.menu_step='%s', menu_names= % s",
                controller_state.menu_step,
                menu_names)
            raise

        # change menu if not None
        set_menu_step = None
        if is_message_type(msg, TOPICS.GPIO_MESSAGES.GPIO):
            msg_button = cast(MsgButton, msg)
            if msg_button.button == RPI.BUTTON1_GPIO:
                if msg_button.short_press:
                    if (APP_CONTEXT.MENU.ACTS.BTN1_SHORT not in menu[menu_name] or
                            menu[menu_name][APP_CONTEXT.MENU.ACTS.BTN1_SHORT] is None):
                        set_menu_step = ctrl_act_next_prev(
                            hub, advance=+1, menu=menu)
                    else:
                        set_menu_step = menu[menu_name][APP_CONTEXT.MENU.ACTS.BTN1_SHORT](
                            hub)
                elif msg_button.long_press:
                    # invoke action btn1 -long press
                    set_menu_step = menu[menu_name][APP_CONTEXT.MENU.ACTS.BTN1_LONG](
                        hub=hub)
            elif msg_button.button == RPI.BUTTON2_GPIO:
                if msg_button.short_press:
                    if (APP_CONTEXT.MENU.ACTS.BTN2_SHORT not in menu[menu_name] or
                            menu[menu_name][APP_CONTEXT.MENU.ACTS.BTN2_SHORT] is None):
                        set_menu_step = ctrl_act_next_prev(
                            hub, advance=-1, menu=menu)
                    else:
                        set_menu_step = menu[menu_name][APP_CONTEXT.MENU.ACTS.BTN2_SHORT](
                            hub)
                elif msg_button.long_press:
                    # invoke action btn2 -long press
                    set_menu_step = menu[menu_name][APP_CONTEXT.MENU.ACTS.BTN2_LONG](
                        hub=hub)
        elif is_message_type(msg, TOPICS.KEYBOARD_MESSAGES.KEY):
            if APP_CONTEXT.MENU.ACTS.KEYBOARD in menu[menu_name]:
                msg_key = cast(MsgKey, msg)
                set_menu_step = menu[menu_name][APP_CONTEXT.MENU.ACTS.KEYBOARD](
                    hub=hub, key=msg_key.key)

        if set_menu_step is not None:
            _menu_entry(menu_step=set_menu_step)
            controller_state.menu_step = set_menu_step

        # Continue/exit
        return goon

    # Optionally (step_resume is not None) resume menu step
    controller_state.menu_state_resume(step_resume)

    # Stop streaming
    ctrl_act_stop_stream(hub=hub)

    # Activate keyboard
    ctrl_act_keyboard_start(hub=hub)

    # Start menu
    _menu_entry(menu_step=controller_state.menu_step)

    # Start main loop
    controller_state.state_machine = f_config
    logger.debug("f_config_enter: controller_state.state_machine='%s'",
                 controller_state.state_machine)


def f_radio_enter(hub: Hub, step_resume: int | None = None):
    """Radio streamerer FST.

    :step_resume: optionally resume menu step.

    """

    logger.info("**f_radio_enter - starting**")
    # info message
    ctrl_act_screen_info_txt(hub, message="Radio")

    menu_choices, factory_reset_done = controller_state.stream_to_button_menu_labels()
    if factory_reset_done:
        ctrl_act_screen_info_txt(hub, message="Kanavalista palautettu")

    def f_radio(msg: str | MsgRoot, hub: Hub) -> bool:
        """Controller actions for radio streamer"""
        logger.info("f_radio: msg: %s", msg)
        if is_message_type(msg, TOPICS.GPIO_MESSAGES.GPIO):
            msg_button = cast(MsgButton, msg)

            if msg_button.button == RPI.BUTTON1_GPIO:
                if msg_button.short_press:
                    # next stream
                    controller_state.menu_step = ctrl_act_set_stream(
                        hub=hub, stream_adv=1)
                    ctrl_act_menu_next_prev(
                        hub=hub, advance=0, menus=menu_choices)
                elif msg_button.long_press:
                    # enter configuration
                    ctrl_menu_setup_main(hub=hub)

            elif msg_button.button == RPI.BUTTON2_GPIO:
                if msg_button.short_press:
                    # prev stream
                    controller_state.menu_step = ctrl_act_set_stream(
                        hub=hub, stream_adv=-1)
                    ctrl_act_menu_next_prev(
                        hub=hub, advance=0, menus=menu_choices)
                elif msg_button.long_press:
                    pass

            else:
                pass

        return True

    # Optionally resume menu step
    controller_state.menu_state_resume(step_resume)

    # De-activate keyboard
    ctrl_act_keyboard_stop(hub=hub)

    # Start streaming (msg to screen&streamer)
    controller_state.menu_step = ctrl_act_set_stream(hub=hub, stream_adv=0)

    # Label buttons used in f_radio loop
    ctrl_act_menu_next_prev(
        hub=hub, advance=0, menus=menu_choices)

    # Start main loop
    controller_state.state_machine = f_radio


def f_init_enter(hub: Hub):
    """Init controller_state and coros(screen, streamer).

    Details:

    - screen!info_message 'starting'
    - screen!sprite
    - screen!screen_update 'full' - -> display=awake


    """
    logger.info("**f_idle_enter - starting**")

    # info message
    ctrl_act_screen_info_txt(hub, message="Initialize")

    # empty button labels
    menus = [
        ["", "", "", ""],
    ]

    def f_init_done(msg: str | MsgRoot, hub: Hub) -> bool:
        """Any message changes to f_radio_enter."""
        logger.info("f_init_done: msg: %s", msg)
        f_radio_enter(hub)
        logger.debug("f_init_done: returning")
        return True

    # --> SCREEN msg: streaming status, network status
    ctrl_act_update_status(hub=hub)
    controller_state.menu_step = 0

    # buttons w. initial labels
    ctrl_act_menu_next_prev(
        hub=hub, advance=0,
        menus=menus)

    # send PING to SCREEN --> await PONG init f_init_done
    hub.publish(topic=TOPICS.SCREEN,
                message=message_create(message_type=TOPICS.COMMON_MESSAGES.PING))

    # --> To my understanding display is awake after all this
    controller_state.set_display_state(awake=True)

    # start main loop
    controller_state.state_machine = f_init_done


# ------------------------------------------------------------------
# Controller core (calling main controller state functions)

async def master_coro(
        name: str,
        hub: Hub,
        topic: str,
        tasks: List[asyncio.Task]):
    """Process common messages and call sub-controllers.

    Details
    ----
    See control_action for message processing

    Parameters
    ----

    :name: name for documenting purposes

    :hub: publish/subscribe patter data manager

    :topic: being listened to: tasks: List of co-routine tasks to
    manage(to cancel)
    Return
    ----

    """

    # Last time user has been active
    user_lasttime_active: datetime.datetime = datetime.datetime.now()

    def exit_message_to_coro_topics(source: TOPICS.HALT_SOURCE):
        """Exit messsage to all other coros, expect for control
        coro."""
        # exit_msg = message_create(message_type=TOPICS.COMMON_MESSAGES.EXIT)
        exit_msg = message_exit(source=source)
        topics = [TOPICS.SCREEN, TOPICS.STREAMER,
                  TOPICS.NETWORK_MONITOR, TOPICS.KEYBOARD]
        for topic in topics:
            logger.info("exit_message_to_topics: topic='%s'", topic)
            hub.publish(topic=topic, message=exit_msg)

    def cancel_tasks(tasks: List[asyncio.Task]):
        for task in tasks:
            logger.warning(
                "name: '%s' -->  cancel task '%s': %s",
                name, task.get_name(), task)
            task.cancel()

    def control_action(msg: str | MsgRoot, hub: Hub):
        """Common actions for all state machines listening CONTROL -
        topic.

        State:

        - f_menu_state: function pointer to menu state

        - user_lasttime_active: manage

        Messages intercepted:

        - SHUTDOWN: send EXIT message to selected topics & & exit
          myself

        - EXIT: send EXIT message to selected topics & & exit myself

        - CLOCK_TICK: MAYBE clear screen on user inactivity, send
        clock signal to screen.

        - NETWORK_STATUS: network staus up/down set to controller status

        Messages to state machine

        - all other messages sent to state specific contorollers

        """
        goon = True

        logger.info("master_coro: name='%s', got msg='%s'", name, msg)
        if is_message_type(msg, TOPICS.CONTROL_MESSAGES.REBOOT):

            # On shutdown send 'exit' -message to all  relevant topics
            exit_message_to_coro_topics(source=TOPICS.HALT_SOURCE.MESSAGE)
            # # Allow gracefull exit
            # await asyncio.sleep(1)
            cancel_tasks(tasks)

            # finally cancel myself - return goon = False
            logger.warning(
                "name: %s - cancelling myself by returning false", name)
            return False

        elif is_message_type(msg, TOPICS.CONTROL_MESSAGES.HALT):
            # origin?: see gpio and SIGTERM
            msg_halt = cast(MsgHalt_HaltAck, msg)
            exit_message_to_coro_topics(source=msg_halt.source)

        elif is_message_type(msg, TOPICS.CONTROL_MESSAGES.HALT_ACK):
            msg_ack = cast(MsgHalt_HaltAck, msg)
            # graceful exit --> save radion state for next reboot
            controller_state.save_state()
            # origins from screen_coro:
            logger.warning(
                "master_coro: halt_ack received: msg='%s'", msg)
            cancel_tasks(tasks)
            # system_halt on volume button knob GPIO singnal
            # --> sudo halt
            # --> journalctl > LCD output
            system_shutdown(system_halt=msg_ack.source ==
                            TOPICS.HALT_SOURCE.GPIO)
        elif is_message_type(msg, TOPICS.COMMON_MESSAGES.EXIT):
            # Pass exit message to relevavant topics
            raise NotImplementedError(f"Control coro should no receive {msg}")

        elif is_message_type(msg, TOPICS.NETWORK_MESSAGES.STATUS):
            # Set network status in controller state
            msg_network = cast(MsgNetwork, msg)
            controller_state.set_network_status(msg_network.status)

        elif is_message_type(msg, TOPICS.KEYBOARD_MESSAGES.STATUS):
            # Set keyboard status
            msg_keyboard = cast(MsgKeyboardStatus, msg)
            changed = controller_state.set_keyboard_status(
                keyboard_status=msg_keyboard.status)
            if changed:
                logger.info("status: keyboard status changed='%s'",
                            msg_keyboard.status)

        elif is_message_type(msg, TOPICS.CONTROL_MESSAGES.STREAMER_STATUS_REPLY):
            # Set network status in controller state
            msg_streamer_status = cast(MsgStreamerStatusReply, msg)
            streamer_status_changed = controller_state.set_streamer_status(
                running=msg_streamer_status.running)
            if streamer_status_changed:
                logger.info(
                    "status: streamer-process ASIS='%s'" +
                    ", streamer-process TOBE:'%s'",
                    msg_streamer_status.running,
                    controller_state.streamer_on)
            if controller_state.streamer_on and not msg_streamer_status.running:
                # TODO: test if works in all cases, try to restart
                # streamer
                controller_state.menu_step = ctrl_act_set_stream(hub)

        elif is_message_type(msg, TOPICS.COMMON_MESSAGES.CLOCK_TICK):

            # maybe put screen on sleep due to user inactivity
            if (controller_state.user_inactive_too_long() and
                    not controller_state.screen_in_sleep):

                # inactive too long --> put display in sleep
                logger.info(
                    "user_inactive_too_long: user_lasttime_active: %s -> going to sleep",
                    controller_state.user_inactivity)

                controller_state.display_close_if_awake(hub=hub)

            # sets controller_state.keyboard_status
            ctrl_act_poll_keyboard_status(hub=hub)

            # send clock message to screen, refersh display if screen
            # not asleep inactivity check above sets
            # controller_state.screen_in_sleep
            ctrl_act_update_status(hub)
            # hub.publish(
            #     topic=TOPICS.SCREEN,
            #     message=message_clock_update(
            #         network_status=controller_state.network_status,
            #         streaming_status=controller_state.streamer_status,
            #         keyboard_status=controller_state.keyboard_status,
            #     )
            # )

            # Send status query to stream (exect STREAMER_STATUS_REPLY)
            hub.publish(
                topic=TOPICS.STREAMER,
                message=message_create(
                    message_type=TOPICS.STREAMER_MESSAGES.STATUS_QUERY)
            )

        else:
            # Maybe wake display up for user activity
            if controller_state.maybe_user_active(msg=msg):
                # User was active
                if controller_state.display_maybe_awake(hub=hub):
                    # user active && display awoke --> discard user action
                    return goon

            # non blocking state machine execution (maybe exit)
            goon = controller_state.state_machine(msg, hub)
            # Continue
        return goon

    # Master coro waits on topic and dispatches responses in 'control_action
    f_init_enter(hub=hub)
    # Main control loop waiting on 'topic' (CONTROL topic in this case)
    try:
        await reader_coro(name=name, hub=hub, topic=topic, action=control_action)
    except Exception as ex:
        logger.error(f"{ex}")
        logger.exception(f"master_coro got exception {ex}")
        # notifi all other coros on exit
        exit_message_to_coro_topics(source=TOPICS.HALT_SOURCE.MESSAGE)
        # # Allow gracefull exit
        # await asyncio.sleep(1)
        cancel_tasks(tasks)
        raise

    # Gracefull exit -> save controller_state
    controller_state.save_state()
    exit_msg = f"{name} - exiting"
    logger.info("coro: %s exiting", exit_msg)
    return exit_msg


async def runner(hub: Hub):
    """Launch application co-routines, and wait them all finishing.

    Details
    - ---

    Parameters
    - ---: hub: Publish/subscribe data controller


    Return
    - ----
    True

    """
    logger.info("runnner starting")
    logger.debug("runner: app_config.console_output_all_lines='%s'",
                 app_config.console_output_all_lines)
    managed_tasks = []
    try:
        async with asyncio.TaskGroup() as tg:
            # t_display = tg.create_task(display())
            # t_reader = tg.create_task(reader_coro(name="reader1", hub=hub ))
            managed_tasks.append(tg.create_task(
                network_coro(
                    name=COROS.NETWORK_MONITOR,
                    hub=hub,
                    topic=TOPICS.NETWORK_MONITOR,
                    status_topic=TOPICS.CONTROL,
                ), name=COROS.NETWORK_MONITOR))
            managed_tasks.append(tg.create_task(
                clock_coro(
                    name=COROS.CLOCK,
                    hub=hub,
                    tick=app_config.clock_tick,
                    topics=[TOPICS.CONTROL],
                ), name=COROS.CLOCK))
            # Keyboard
            managed_tasks.append(tg.create_task(
                kb_coro(
                    name=COROS.KB_READER,
                    hub=hub,
                    topic=TOPICS.KEYBOARD,
                    topic_out=TOPICS.CONTROL,
                    # action=None,                # None = default
                ), name=COROS.KB_READER))
            managed_tasks.append(tg.create_task(
                stdin_coro(
                    name=COROS.STDIN_READER,
                    hub=hub,
                    topic=TOPICS.DEFAULT,
                    topic_ctr=TOPICS.CONTROL,
                    action=stdin_debugger,      # debugger on keyboard
                ), name=COROS.STDIN_READER))
            # TODO: add config option to launch SPY
            managed_tasks.append(tg.create_task(
                reader_coro(
                    name=COROS.SPY_DEFAULT,
                    hub=hub,
                    topic=TOPICS.DEFAULT,
                ), name=COROS.SPY_DEFAULT))
            # managed_tasks.append(tg.create_task(
            #     reader_coro(
            #         name=COROS.SPY_CONTROL,
            #         hub=hub,
            #         topic=TOPICS.CONTROL,
            #     ), name=COROS.SPY_CONTROL))
            # Pushbuttons
            managed_tasks.append(tg.create_task(
                GPIO_button_coro(
                    name=COROS.GPIO_PB,
                    hub=hub,
                    topic=TOPICS.CONTROL,
                ), name=COROS.GPIO_PB))
            # Dispaly
            managed_tasks.append(tg.create_task(
                screen_coro(
                    name=COROS.SCREEN,
                    hub=hub,
                    topic=TOPICS.SCREEN,
                ), name=COROS.SCREEN))
            # Streamer
            managed_tasks.append(tg.create_task(
                streamer_coro(
                    name=COROS.STREAMER,
                    hub=hub,
                    topic=TOPICS.STREAMER,
                ), name=COROS.STREAMER))
            # master controller
            master_task = tg.create_task(master_coro(
                name=COROS.MASTER,
                topic=TOPICS.CONTROL,
                hub=hub,
                tasks=managed_tasks), name=COROS.MASTER)
    except* Exception as exs:
        for e in exs.exceptions:
            logger.error(f"runner: {e}")
            logger.exception(e)

    # All tasks finished
    logger.info("All coroutines done")
    logger.info("master_task.result(): %s", master_task.result())

    # report or cancel
    for taskno, task in enumerate(managed_tasks):
        if task.cancelled():
            # should not happed?
            logger.info("task %s - %s - already cancelled",
                        taskno, task.get_name())
        else:
            logger.info("task %s - %s - result(): %s", taskno,
                        task.get_name(), task.result())
    return True

# ------------------------------------------------------------------
# systemd shutdown


def system_shutdown(system_halt: bool):
    """Init lcd and pipe console messages to LCD.

    Called after HALT_ACK from master-coro."""
    logger.warning("system_shutdown: starting")
    if system_halt:
        cmd = "(sleep 1;  sudo halt)&"
        logger.error("system_shutdown: os.sysmtem cmd='%s'", cmd)
        os.system(cmd)
    # Loop forever within
    console_output(
        console_output_all_lines=app_config.console_output_all_lines)


def enable_SIGTERM(hub: Hub):
    """Set listener for 'SIGTERM' to shuddown the service."""

    def shutdown_handler_2nd(signum, frame):
        """Second SIGTERM exit.

        Maybe sent by systemd to signal all remaining procesess?

        I my case (see shutdown_handler_1st), I ignored the first
        SIGTERM and started to loop console output to LCD.

        For the second SIGTERM, I will blank the LCD and exit.

        """
        signame = signal.Signals(signum).name
        logger.warning(
            "shutdown_handler_2nd: console_close & EXITING - signame=%s, signum=%s",
            signame, signum)
        # blank on console
        console_close()
        # exit (-> systemd would hang for 90sec before SIGKILL)
        os._exit(0)

        # hub.publish(
        #     topic=TOPICS.CONTROL,
        #     message=message_halt(
        #         source=TOPICS.HALT_SOURCE.SIGNAL)  # on sigterm
        # )

    def shutdown_handler_1st(signum, frame):
        """Normal operation: SIGTERM starts console logger"""
        signame = signal.Signals(signum).name
        logger.warning(
            "shutdown_handler_1st: start console for signame=%s, signum=%s",
            signame, signum)
        hub.publish(
            topic=TOPICS.CONTROL,
            message=message_halt(
                source=TOPICS.HALT_SOURCE.SIGNAL)  # on sigterm
        )
        # shudown handle only once
        signal.signal(signum, shutdown_handler_2nd)

    # https://www.freedesktop.org/software/systemd/man/latest/systemd.kill.html
    # Signal to use when stopping a service.  Defaults to SIGTERM
    sigterm_signal = signal.SIGTERM
    logger.info("enable_SIGTERM: signal='%s'", sigterm_signal)
    signal.signal(sigterm_signal, shutdown_handler_1st)


# ------------------------------------------------------------------
# Command mains


def radio_main(parsed):
    hub = Hub()
    controller_state.restore_state()

    # Init gpi stuff-here
    gpio_init()

    # Send message to 'topic' when button in buttons pushed. Thread
    # management requires access controller 'loop'

    loop = asyncio.get_event_loop()
    init_GPIO_buttons(buttons=RPI.BUTTON_GPIOS, hub=hub,
                      topic=TOPICS.CONTROL, loop=loop)
    # send halt message on 'RPI.BUTTON_SHUTDOWN'
    init_GPIO_shutdown(button=RPI.BUTTON_SHUTDOWN, hub=hub,
                       topic=TOPICS.CONTROL, loop=loop)

    enable_SIGTERM(hub=hub)

    # Run application - for ever
    try:
        asyncio.run(runner(hub))
    except Exception as ex:
        logger.error(f"{ex}")
        logger.exception(f"radio_main got exception {ex}")
        raise
        # except Exception as e:
        #     logger.error(f"{e}")
        # except Exception as e:
        #     logger.error(f"{e}")
        # except KeyboardInterrupt as e:
        #     logger.info("Keyboard interrupts %s", e)
        #     close_GPIO_buttons()
        #     raise
    finally:
        # Cleanup
        gpio_close()
        screen_close()
