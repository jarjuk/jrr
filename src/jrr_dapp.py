"""Configuration screen contents used in controler
"""

from .constants import DSCREEN
from . import dscreen


import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# data types
type_alphanum = dscreen.AlphanuNumericType()
type_alphanum_10 = dscreen.AlphanuNumericType(max_len=10)
type_alphanum_4 = dscreen.AlphanuNumericType(max_len=4)
type_numeric = dscreen.NumericType(max_len=10)
type_no_input = dscreen.ReadonlyType()

# Field types
ft_ssid = dscreen.FieldType(DSCREEN.WIFI_OVERLAY.SSID, type_no_input)
ft_password = dscreen.FieldType(DSCREEN.WIFI_OVERLAY.PASSWORD, type_alphanum)
ft_title = dscreen.FieldType(DSCREEN.URL_LOAD_OVERLAY.TITLE, type_no_input)
ft_url_base = dscreen.FieldType(
    DSCREEN.URL_LOAD_OVERLAY.URL_BASE, type_alphanum)
ft_yaml_file = dscreen.FieldType(
    DSCREEN.URL_LOAD_OVERLAY.YAML_FILE, type_alphanum)
ft_firmware_version = dscreen.FieldType(
    DSCREEN.FIRMWARE_OVERLAY.VERSION_TAG, type_alphanum_10)
ft_firmware_notes = dscreen.FieldType(
    DSCREEN.FIRMWARE_OVERLAY.NOTES, type_alphanum)


# Screen
wifi_screen = dscreen.DScreen(fieldTypes=[ft_ssid, ft_password,])
url_load_screen = dscreen.DScreen(
    fieldTypes=[ft_title, ft_url_base, ft_yaml_file])

firmware_screen1 = dscreen.DScreen(
    fieldTypes=[ft_title, ft_firmware_version])
firmware_screen2 = dscreen.DScreen(
    fieldTypes=[ft_title, ft_firmware_version, ft_firmware_notes])


# Screen collections (zero or one screen is active/current)
screen_ovrlays = dscreen.DApp()
screen_ovrlays.addScreen(DSCREEN.SCREEN_OVERLAYS.WIFI_SETUP, wifi_screen)
screen_ovrlays.addScreen(DSCREEN.SCREEN_OVERLAYS.URL_LOAD, url_load_screen)
screen_ovrlays.addScreen(DSCREEN.SCREEN_OVERLAYS.FIRMWARE1, firmware_screen1)
screen_ovrlays.addScreen(DSCREEN.SCREEN_OVERLAYS.FIRMWARE2, firmware_screen2)
