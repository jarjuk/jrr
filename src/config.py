"""Singleton confuration
"""

# from typing import Annotated
import logging
from typing import Tuple
import os
from argparse import Namespace
from pathlib import Path
from datetime import datetime, timedelta


from .constants import APP_CONTEXT, CLI

logger = logging.getLogger(__name__)


class Config():

    _self = None

    def __init__(self, *args, **kwargs):
        # set exactly one True
        self._epd = {
            "epd2in13bc": False,
            "epd2in7_V2": False,
            "epd2in7b_V2": False,
            "tft_ili9486": True,
        }
        logger.info("config.init: kwargs='%s'", kwargs)
        for k, v in kwargs.items():
            # self.__setattr__(k, v)
            setattr(self, k, v)

    def __new__(cls, *args, **kwargs):
        logger.info("config.new: called kwargs='%s'", kwargs)
        if cls._self is None:
            logger.info("config.new: kwargs='%s'", kwargs)
            # cls._self = super().__new__(cls, *args, **kwargs)
            cls._self = super().__new__(cls)
        return cls._self

    @property
    def cliArgs(self) -> Namespace | None:
        """Read cliArgs."""
        if not hasattr(self, "_cliArgs"):
            return None
        return self._cliArgs

    @cliArgs.setter
    def cliArgs(self, cliArgs: Namespace):
        """Set cliArgs."""
        self._cliArgs = cliArgs

    @property
    def debug_dir(self):
        return APP_CONTEXT.DEBUG_DIR

    def epd_include(self, driver: str) -> bool:
        """Should include ePaper 'driver'."""
        return self._epd[driver]

    @property
    def should_include_epd2in13bc(self):
        return self.epd_include("epd2in13bc")

    @property
    def should_include_epd2in7b_V2(self):
        return self.epd_include("epd2in7b_V2")

    @property
    def should_include_epd2in7_V2(self):
        """Ref  https://www.waveshare.com/wiki/2.7inch_e-Paper_HAT"""
        return self.epd_include("epd2in7_V2")

    @property
    def should_include_tft_ili9486(self):
        """https://github.com/SirLefti/Python_ILI9486"""
        return self.epd_include("tft_ili9486")

    @property
    def pic_directory(self):
        """Return directory for pictures and fonts"""
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')

    @property
    def icon_directory(self) -> str | Path:
        """Return directory for iconds"""
        # return Path.home() / '.icons/v2')
        return CLI.DEFAULT_ICON_DIR

    @property
    def cnf_directory(self) -> str | Path:
        """Return directory for configurations"""
        return os.path.dirname(self.streams_yaml)

    @property
    def state_config(self) -> str | Path:
        """Return file for app state"""
        return os.path.join(self.cnf_directory, APP_CONTEXT.APP_STATE_FILE)

    @property
    def clock_tick(self) -> float:
        """Length of clock tick"""
        return CLI.DEFAULT_CLOCK_TICK

    @property
    def full_update_limit(self):
        """Full update on ePaper after when partial updates execeeds limit."""
        return CLI.DEFAULT_FULL_UPDATE_LIMIT

    @property
    def inactivity_timeout(self) -> int | float:
        """Seconds of allowed inactivity before screen put to sleep."""
        return CLI.DEFAULT_INACTIVITY_TIMEOUT

    @property
    def sprite_icon_size(self) -> int:
        """Width/height of sprite icon."""
        return CLI.DEFAULT_SPRITE_ICON_SIZE

    @property
    def streaming_icon_size(self) -> Tuple[int, int]:
        """Width/height of sprite icon."""
        return (CLI.DEFAULT_STREAMING_ICON_WIDTH, CLI.DEFAULT_STREAMING_ICON_HEIGHT)

    @property
    def streams_yaml(self) -> str:
        """YAML file for streams."""
        return CLI.DEFAULT_STREAM_YAML

    @property
    def channel_activation_url(self) -> str:
        """Url where to load activations."""
        return APP_CONTEXT.MENU.LOAD_CHANNELS_DEFAULTS.DEFAULT_URL

    @property
    def firmware_local_root(self) -> str | None:
        """Read root directory for version sub-directories."""
        if not hasattr(self, "_firmware_local_root"):
            return APP_CONTEXT.DEFAULT_FIRMWARE_LOCAL_ROOT
        return self._firmware_local_root

    @property
    def firmware_repo_url(self) -> str:
        """Default remote repo url"""
        if not hasattr(self, "_firmware_repo_url"):
            return APP_CONTEXT.DEFAULT_FIRMWARE_REPO_URL
        return self._firmware_repo_url

    @firmware_local_root.setter
    def firmware_local_root(self, firmware_local_root: str):
        """set root directory for version sub-directories."""
        self._firmware_local_root = firmware_local_root

    # @firmware_local_root.deleter
    # def firmware_local_root(self):
    #     del self._firmware_local_root

    @property
    def console_output_all_lines(self) -> bool:
        """Show all lines on console mode"""
        return self.cliArgs.all_lines


# Annotated[Config(), "Singleton configuration init from cli arguments"]
app_config = Config()
