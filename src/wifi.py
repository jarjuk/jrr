# https://raspberrypi.stackexchange.com/questions/7686/detect-available-open-wifi-networks-using-python

from typing import List
import re
import os

import logging
logger = logging.getLogger(__name__)


def list_wifis() -> List[str]:
    """Return list of wife networks found."""
    # os.popen(): https://www.tutorialspoint.com/python3/os_popen.htm
    networks = os.popen('sudo iwlist wlan0 scanning | grep ESSID').read()
    # Parse all found networks list in a clean list 'networkslist'
    networkslist = re.findall(r'"(.+?)"', networks)
    networkset = set(networkslist)
    logger.info("list_wifis: networks='%s', networkslist=%s, networkset=%s",
                networks, networkslist, networkset)

    return list(networkset)


def main():
    wifis = list_wifis()
    print(f"{wifis=}")


if __name__ == '__main__':
    main()
