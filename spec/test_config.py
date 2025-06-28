import pytest
import os

import pytest
from unittest.mock import patch

from src import config


# ------------------------------------------------------------------
# Test framework

def test_framework():
    assert 1 == 1


# ------------------------------------------------------------------
# Test mock


def test_get_path_mocked():
    with patch.object(config.Config, 'firmware_local_root', return_value="there"):
        assert config.app_config.firmware_local_root() == "there"
