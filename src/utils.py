"""Misc utilites
"""

import logging
import asyncio
import io
import os
import glob
import subprocess
import shutil
import re
import socket
import urllib.request
from urllib.parse import urlparse

from .constants import APP_CONTEXT

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# delegation pattern

# https://raspberrypi.stackexchange.com/questions/5100/detect-that-a-python-program-is-running-on-the-pi


def is_raspberrypi():
    """True if raspberry pi"""
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower():
                return True
    except Exception:
        pass
    return False

# ------------------------------------------------------------------
# delegation pattern


# https://gist.github.com/kkew3/2d61463397a77a898be12ac766c31c12
def delegates(method_names, to):
    def dm(method_name):
        def fwraps(self, *args, **kwargs):
            wrappedf = getattr(getattr(self, to), method_name)
            return wrappedf(*args, **kwargs)
        fwraps.__name__ = method_name
        return fwraps

    def cwraps(cls):
        for name in method_names:
            setattr(cls, name, dm(name))
        return cls
    return cwraps

# ------------------------------------------------------------------
# check_inet


async def check_inet(url: str = "www.google.com", port: int = 80):
    """Async check for internet connectivity.

    :url: address to monitor (default www.google.com)

    :port: to use in check (default 80)
    """
    try:
        logger.debug(
            "use url: %s to check inet connection on port=%s", url, port)
        # await asyncio.to_thread(request.urlopen(url))
        reader, writer = await asyncio.open_connection(url, port)
        status = True
    except Exception as err:
        logger.info("err: %s", err)
        status = False

    logger.debug("Check_inet: status= %s, url=%s", status, url)
    return status


# ------------------------------------------------------------------


def current_ssid() -> str:
    """Return SSID for current network connection.

    :return: emtpy string if no current SSID 

    """
    os_command = "iwgetid"
    result = subprocess.run(os_command, shell=True,
                            capture_output=True,
                            encoding="UTF-8")

    pattern = r'ESSID:"(?P<ssid>\w+)"'
    matchi = re.search(pattern, result.stdout)
    ssid = ""
    if matchi:
        ssid = matchi["ssid"]

    logger.info("current_ssid: stdoud='%s'", result.stdout)
    logger.info("current_ssid: ssid='%s'", ssid)
    return ssid


def current_IP() -> str:
    """Return IP for current network connection.

    :return: emtpy string if no network connection

    """
    # https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    logger.info("current_IP: ip=%s", ip)
    return ip


# ------------------------------------------------------------------
#


def copy_files_with_wildcard(src_dir: str, dest_dir: str, pattern: str):
    """
    Copy files matching a wildcard pattern from src_dir to dest_dir.

    :param src_dir: Source directory (e.g., "/path/to/source")
    :param dest_dir: Destination directory (e.g., "/path/to/destination")
    :param pattern: Wildcard pattern (e.g., "*.txt")
    """

    logger.debug("copy_files_with_wildcard: src_dir='%s'," +
                 " dest_dir=%s, patters=%s",
                 src_dir, dest_dir, pattern)

    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    # Construct full pattern path
    search_pattern = os.path.join(src_dir, pattern)

    # Iterate over matching files
    for file_path in glob.glob(search_pattern):
        if os.path.isfile(file_path):
            shutil.copy(file_path, dest_dir)
            print(f"Copied: {file_path} -> {dest_dir}")

# ------------------------------------------------------------------
# copy_file_or_directorty


def _copy_file(src_url: str, dest_path: str) -> str:
    """Handle file:// scheme (local files or directories)."""
    parsed = urlparse(src_url)
    src_path = parsed.path
    dest_dir = os.path.dirname(dest_path)

    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source path not found: {src_path}")

    if os.path.isdir(src_path):
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        shutil.copytree(src_path, dest_path)
    else:
        dest_path = dest_dir
        shutil.copy(src_path, dest_path)

    return dest_path


def _copy_http(src_url: str, dest_path: str) -> str:
    """Handle http(s):// scheme (assumed to be a downloadable file, typically zip)."""
    filename = os.path.basename(urlparse(src_url).path)
    dest_dir = os.path.dirname(dest_path)
    tempfile = os.path.join(dest_dir, f"_{filename}")

    with open(tempfile, "w") as fhandle:
        with urllib.request.urlopen(src_url) as response:
            fhandle.write(response.read())

    dest_path = os.path.join(dest_dir, filename)
    shutil.move(tempfile, dest_path)
    return dest_path


def copy_file_or_directory(src: str, dest: str) -> str:
    """Dispatch to appropriate scheme-specific function.

    :return: result directory/file path
    """
    parsed = urlparse(src)
    scheme = parsed.scheme

    dest_path = os.path.join(dest, os.path.basename(src))
    logger.info("copy_file_or_directory: dest_path='%s'",
                dest_path)
    if os.path.exists(dest_path):
        raise FileExistsError(f"File exists {dest_path}")

    # os.makedirs(dest, exist_ok=True)

    if scheme == 'file':
        result_path = _copy_file(src, dest_path=dest_path)
    elif scheme in ('http', 'https'):
        result_path = _copy_http(src, dest_path=dest_path)
    else:
        raise ValueError(f"Unsupported URL scheme: {scheme}")
    return dest_path

# ------------------------------------------------------------------
# run script


def set_wifi_password(ssid: str, password: str):
    """Choose wifi ssid/configure ssid/password.

    :password: if empty choose 'ssid' (assumed that it has been
    configured.)

    Use wrapper script to set 'password' for 'ssid' -wifi.

    """
    script = APP_CONTEXT.STREAMER_SCRIPT
    script_command = APP_CONTEXT.STREAMER_COMMANDS.WIFI_SETUP
    os_command = f"{script} {script_command} {ssid} {password}"
    status = _run_os_command(os_command)
    if not status:
        logger.error("set_wifi_password: error in running='%s'", os_command)


# ------------------------------------------------------------------
# send dmesg

def send_dmesg(msg: str):
    script = APP_CONTEXT.STREAMER_SCRIPT
    os_command = f'{script} dmesg "{msg}"'
    _run_os_command(os_command=os_command)


def _run_os_command(os_command: str) -> bool:
    """Run 'os_command' in shell.

    Log errors on failure

    :return: False in failure
    """

    logger.info("_run_os_command: os_command='%s'", os_command)

    result = subprocess.run(os_command, shell=True,
                            capture_output=True,
                            encoding="UTF-8")
    if result.returncode != 0:
        logger.error("_run_os_command: returncode: %s stdout='%s'",
                     result.returncode, result.stdout)
        logger.error("_run_os_command: returncode: %s stderr='%s'",
                     result.returncode, result.stderr)
    else:
        logger.info("_run_os_command: returncode: %s stdout='%s'",
                    result.returncode, result.stdout)
        logger.info("_run_os_command: returncode: %s stderr='%s'",
                    result.returncode, result.stderr)

    return result.returncode == 0

# Stadalone test


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG)

    asyncio.run(check_inet("dkj"))
    asyncio.run(check_inet())
