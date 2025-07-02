"""Github API module
"""
import requests

from typing import List

import logging
logger = logging.getLogger(__name__)
from .utils import copy_file_or_directory

def github_tags(tags_url) -> List[str]:
    # url = f"https://api.github.com/repos/{owner}/{repo}/tags"
    logger.info("github_tags: tags_url=%s", tags_url)

    # Make the GET request
    response = requests.get(tags_url)
    logger.debug(": response='%s'", response)
    if response.status_code != 200:
        logger.error("github_tags: response='%s' from tags_url=%s",
                     response, tags_url)

        response.raise_for_status()

    # Check if the request was successful
    # esponse.status_code == 200:
    tags = response.json()
    logger.debug("github_tags: tags='%s'", tags)
    ret = [tag['name'] for tag in tags]
    # for tag in tags:
    #     print(f"Tag: {tag['name']}")

    return ret


if __name__ == "__main__":
    # args = sys.argv[1:]
    logging.basicConfig(level=logging.DEBUG)
    owner = "jarjuk"
    repo = "jrr"
    url = f"https://api.github.com/repos/{owner}/{repo}/tags"


    tags = github_tags(url)
    print(f"{tags=}")
    tag = tags[1]
    

    # https://github.com/jarjuk/jrr/archive/refs/tags/jrr-0.0.latest.zip
    zipfile = f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag}.zip"
    print(f"{zipfile=}")

    copy_file_or_directory(src=zipfile, dest="tmp")


