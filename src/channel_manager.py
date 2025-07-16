"""Method managing channel/stream configurations.

Notice: both 'channel' and 'stream' are used interchangebibly, they
mean the same thing.

TWO SETS OF ROUTINES:

1) Managing streamable/active channel configurations:

- uses YAML configuration file CLI.FACTORY_STREAM_YAML

- YAML configuration CLI.FACTORY_STREAM_YAML is list of StreamConfig
  -objects

- each StreamConfig object has a property icon, which refers to stream
  icon in CLI.DEFAULT_ICON_DIR

2) Activating new channel configuration to the set of streamable/active
channel configurations

- uses channel_origin url (with default value, user may change it and
  store it for later uses)

- channel_origin url points to 'index.yaml', which is a list of 'StreamConfig'
  objects.

- each StreamConfig object has a property icon, which may be a full
  url or a relative reference with respect to 'index.yaml'

- accepting an entry from 'index.yaml' to the set of streamable/active
  channel configurations,
  - adds StreamConfig to the list in CLI.FACTORY_STREAM_YAML
  - resizes icon referenced in index.yaml entry 
  - and saves the resized icon to 'CLI.DEFAULT_ICON_DIR'
  - updates StreamConfig.icon with icon name

"""

from typing import Tuple, List

import urllib3
from urllib3.exceptions import HTTPError
from urllib.parse import urlparse, urlunparse
from dataclasses import dataclass, asdict

import os
import yaml

import logging

from .utils import copy_files_with_wildcard
from .config import app_config
from .constants import APP_CONTEXT, CLI
from .jrr_converter import image_to_thumb

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Data classes


@dataclass
class StreamConfig:
    """Data object for stream."""
    name: str        # Stream name
    icon: str        # Stream icon name OR url to icon
    url: str         # Stream url


# ------------------------------------------------------------------
# read_file (from from or from file)

def read_file(url: str, encoding="utf-8") -> Tuple[str, bool]:
    """Read 'url' content (where url may be file or http resource)

    :url: supports file://, https:// -scheme (or without scheme)

    :return: on success Tuple[url content, True], on failure
    Tuple[error-string, False]

    """
    logger.info("read_file: url='%s'", url)

    # http access
    if url.startswith(("http://", "https://")):
        http = urllib3.PoolManager()
        try:
            response = http.request("GET", url)
            return response.data.decode(encoding), True
        except HTTPError as e:
            return f"HTTP Error: {e}", False
        except Exception as e:
            return f"Error: {e}", False

    # file access
    file_path = url
    if url.startswith("file://"):
        file_path = url[7:]  # Remove 'file://' prefix

    if os.path.exists(file_path):
        with open(file_path, "r", encoding=encoding) as file:
            return file.read(), True
    else:
        return f"Error: File not found - {file_path}", False


# ------------------------------------------------------------------
#


def icon_path(channel: StreamConfig) -> str:
    image_path = os.path.join(
        app_config.icon_directory,
        os.path.basename(channel.icon))
    logger.info("icon_path: icon_path='%s' channel=%s",
                image_path, channel)
    return image_path


def add_channel_icons(channels: List[StreamConfig], yaml_url: str):
    """Save streaming icons for 'channels' from an image location
    relative to 'yaml_url'.

    """
    # parsed_yaml_url = urlparse(yaml_url)

    for channel in channels:
        # find url to icon image (relative to YAML config)
        # parsed_icon_url = urlparse(channel.icon)
        # if parsed_icon_url.scheme and parsed_icon_url.netloc:
        #     image_url = channel.icon
        # else:
        #     image_path = os.path.join(
        #         os.path.dirname(parsed_yaml_url.path),
        #         channel.icon
        #     )
        #     image_url = urlunparse(parsed_yaml_url._replace(path=image_path))

        image_url = channel_icon_image(channel, yaml_url)

        # save icon thumbs in local configuration
        channel_icon = icon_path(channel)
        logger.info("add_channel_icons: channel=%s, image_url=%s, channel_icon=%s",
                    channel.name, image_url, channel_icon)

        # Resize image to save icon
        image_to_thumb(image_path=image_url, thumb_path=channel_icon, bw=False)


def parse_channels(channel_str) -> List[StreamConfig]:
    channels = []
    logger.debug("parse_channels: channel_str='%s'", channel_str)
    if channel_str is not None:
        channels = [StreamConfig(**s) for s in yaml.safe_load(channel_str)]
    return channels


def update_channel_configurations(
        streams: List[StreamConfig],
        deleted_streams: List[StreamConfig] = [],
        added_streams: List[StreamConfig] = []
) -> List[StreamConfig]:
    """Update (=delete, keep) channel/stream configuration in
    yaml-configuration.

    Delete YAML configuration file if no more streams to keep
    (=len(streams)== 0).

    Deletes also icons for 'deleted_streams'.

    """
    yaml_file = app_config.streams_yaml
    logger.info("delete_channel_configurations: yaml_file='%s', strems=%s",
                yaml_file, streams)

    # First append
    streams += added_streams

    if len(streams) == 0:
        logger.info("delete_channel_configurations: file='%s'", yaml_file)
        if os.path.exists(yaml_file):
            os.remove(yaml_file)
    else:
        with open(yaml_file, 'w', encoding="UTF-8") as f:
            channel_list = [asdict(s) for s in streams]
            yaml.dump(channel_list, f)

    # delete icons - if it exists
    for s in deleted_streams:
        image_path = icon_path(s)
        if os.path.exists(image_path):
            os.remove(image_path)

    return streams


def _factory_reset_channels():
    """Copy initial (=factory setting) for channel streams.
    """
    logger.info("factory_reset_channels: starting")
    copy_files_with_wildcard(src_dir=CLI.FACTORY_ICON_DIR,
                             dest_dir=CLI.DEFAULT_ICON_DIR,
                             pattern="*.png"
                             )
    copy_files_with_wildcard(src_dir=os.path.dirname(CLI.FACTORY_STREAM_YAML),
                             dest_dir=os.path.dirname(app_config.streams_yaml),
                             pattern="*.yaml"
                             )


def init_streams(url: str | None = None) -> Tuple[List[StreamConfig] | None, bool]:
    """Read channel YAML from 'url' and parse list of StreamConfig's.

    If 'url' not found use 'factory_reset_channels' to init channels.

    :url: defaults to 'app_config.streams_yaml'

    :return: list of stream config/None if not found, bool if factory reset done

    """
    factory_reset_done = False
    if url is None:
        url = f"file://{app_config.streams_yaml}"
    yaml_str, status = read_file(url)
    if not status or len(yaml_str) == 0:
        # Factory reset
        factory_reset_done = True
        _factory_reset_channels()

    yaml_str, status = read_file(url)
    if not status:
        # Factory did not help
        logger.warning(
            "init_streams: could not read channel configs from url='%s'", url)
        return (None, factory_reset_done)

    channels = parse_channels(yaml_str)
    return (channels, factory_reset_done)

# ------------------------------------------------------------------
#


def channel_activation_index(activation_url: str) -> str:
    """Return yaml-file (index.yaml) in 'activation_url' -path."""
    return f"{activation_url}/index.yaml"


def channel_activation_list(activation_url: str) -> List[StreamConfig]:
    """Read 'index.yaml' from 'activation_url' to return list of
    channels to activate.

    :activation_url: path, file-url,or http-url pointing to location
    of 'channel_activation_index'

    :raises: FileNotFoundError

    :return: list of channel configurations for activation 

    """

    index_urls = [channel_activation_index(activation_url)]

    yaml_str = None
    for index_url in index_urls:
        yaml_str, status = read_file(index_url)
        if status:
            break
        yaml_str = None

    if yaml_str is None:
        raise FileNotFoundError(
            f"Could not find channel index from {index_urls}")

    channels = parse_channels(yaml_str)

    return channels


def channel_activate(
        streams: List[StreamConfig],
        new_stream: StreamConfig,
        activation_url,

) -> List[StreamConfig]:
    """Activate 'new_stream' to the set of activate stream in
    'streams'

    Reads image from 'new_stream', resizes the image and saves it to
    set icon -directory.

    Chanes truncates new_stream.icon to just icon name.

    Stores YAML-configuration file

    :activation_url: url where new_stream is configured

    """

    # yaml_file = app_config.streams_yaml

    activation_yaml_file = channel_activation_index(activation_url)

    add_channel_icons(channels=[new_stream], yaml_url=activation_yaml_file)

    # just icon name
    new_stream.icon = os.path.basename(new_stream.icon)

    streams = update_channel_configurations(
        streams, added_streams=[new_stream])

    return streams


def channel_icon_image(channel: StreamConfig, yaml_url: str) -> str:
    """Return url pointing to channel.icon image

    :yaml_url: url/path to yaml configuration file

    Icon image may be:
    - real url in 'channel.icon'
    - realative to 'yaml_url' in 'channel.icon' 

    """
    parsed_icon_url = urlparse(channel.icon)
    if parsed_icon_url.scheme and parsed_icon_url.netloc:
        # real url in 'channel.icon'
        image_url = channel.icon
    else:
        # realative to 'yaml_url' in 'channel.icon'
        parsed_yaml_url = urlparse(yaml_url)
        image_path = os.path.join(
            os.path.dirname(parsed_yaml_url.path),
            channel.icon
        )
        image_url = urlunparse(parsed_yaml_url._replace(path=image_path))

    logger.debug(
        "channel_icon_image: image_url=%s, yaml_url=%s, channel.icon=%s",
        image_url, yaml_url, channel.icon)
    return image_url
