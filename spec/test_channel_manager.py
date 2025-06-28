import pytest
import os
from typing import List
from dataclasses import asdict

from src import channel_manager


def test_framework():
    assert 1 == 1

# ------------------------------------------------------------------
# Init streams


def test_init_streams_0():
    channels, _ = channel_manager.init_streams()
    print(f"{channels=}")
    assert isinstance(channels, List)
    d = asdict(channels[0])
    assert "icon" in d


def test_init_streams_error():
    channels, _ = channel_manager.init_streams(url="file://ds")
    print(f"{channels=}")
    assert channels is None


def test_init_streams_extension_relative_path():
    # channels = channel_manager.init_streams(url="file:///home/jj/work/jarviradio-radio/resources/channels/rondo.yaml")
    channels, _ = channel_manager.init_streams(
        url="file://resources/channels/rondo.yaml")
    print(f"{channels=}")
    assert channels is not None
    assert len(channels) == 1
