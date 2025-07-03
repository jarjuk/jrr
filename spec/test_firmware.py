import pytest
from unittest.mock import patch, PropertyMock

import os
from pathlib import Path
import shutil

from src import firmware, config
from src import github
from src.constants import APP_CONTEXT


def test_framework():
    assert 1 == 1


# ------------------------------------------------------------------
# Config fixtures
LOCAL_ROOT0 = os.path.join(os.path.dirname(__file__), "fixture", "local-repo0")
LOCAL_ROOT1 = os.path.join(os.path.dirname(__file__), "fixture", "local-repo1")
LOCAL_ROOT2 = os.path.join(os.path.dirname(__file__), "fixture", "local-repo2")
REPO_URL0 = LOCAL_ROOT0
REPO_URL1 = LOCAL_ROOT1
REPO_URL2 = LOCAL_ROOT2
GITHUB_REPO = "https://github.com/jarjuk-demo/jrr"
REPO_URL_ERR = "gitt:/githu.com"
JRR_TAG_001 = "jrr-0.0.1"
JRR_TAG_011 = "jrr-0.1.1"


LOCAL_ROOT_STAGE = os.path.join(
    os.path.dirname(__file__), "..", "tmp", "stage")


@pytest.fixture
def mock_local_root0():
    with patch.object(config.Config, 'firmware_local_root', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = LOCAL_ROOT0
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_create_empty_local_root():
    """Ensure empty directory firmware_local_root=LOCAL_ROOT_STAGE."""
    with patch.object(config.Config, 'firmware_local_root', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = LOCAL_ROOT_STAGE
        shutil.rmtree(LOCAL_ROOT_STAGE)
        Path(LOCAL_ROOT_STAGE).mkdir(exist_ok=False)
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_repo_github():
    with patch.object(config.Config, 'firmware_repo_url', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = GITHUB_REPO
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_repo_url0():
    with patch.object(config.Config, 'firmware_repo_url', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = REPO_URL0
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_repo_url1():
    with patch.object(config.Config, 'firmware_repo_url', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = REPO_URL1
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_repo_url2():
    with patch.object(config.Config, 'firmware_repo_url', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = REPO_URL2
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_repo_url_error():
    with patch.object(config.Config, 'firmware_repo_url', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = REPO_URL_ERR
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_local_root1():
    with patch.object(config.Config, 'firmware_local_root', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = LOCAL_ROOT1
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_local_root2():
    with patch.object(config.Config, 'firmware_local_root', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = LOCAL_ROOT2
        yield mock_property  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_github_tags1():
    with patch('src.github.github_tags') as mock:
        mock.return_value = [JRR_TAG_001]
        yield mock  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_github_tags2():
    with patch('src.github.github_tags') as mock:
        mock.return_value = [JRR_TAG_001, JRR_TAG_011]
        yield mock  # yields the mock in case you want to make assertions on it


@pytest.fixture
def mock_github_tags0():
    with patch('src.github.github_tags') as mock:
        mock.return_value = []
        yield mock  # yields the mock in case you want to make assertions on it


# ------------------------------------------------------------------
# Test config module mock

def test_config_mock():
    with patch.object(config.Config, 'firmware_local_root', new_callable=PropertyMock) as mock_property:
        mock_property.return_value = "there"
        assert config.app_config.firmware_local_root == "there"


def test_config_property():
    assert config.app_config.firmware_local_root == os.path.join(
        Path.home(), "jrr")


def test_func_mock(mock_github_tags1):
    assert github.github_tags() == [JRR_TAG_001]


def test_func_mock(mock_github_tags0):
    assert github.github_tags() == []


def test_func_mock(mock_github_tags2):
    assert github.github_tags() == [JRR_TAG_001, JRR_TAG_011]

# ------------------------------------------------------------------
# class FirmwareVersion


def test_class_semantic_version():
    tag1 = "jrr-0.1.1"
    fw1 = firmware.FirmwareVersion(version=tag1)
    assert fw1.version == tag1

    assert fw1.semantic_version == [0, 1, "1"]

    tag1 = "0.1.2"
    fw1 = firmware.FirmwareVersion(version=tag1)
    assert fw1.version == tag1
    assert fw1.semantic_version == [0, 1, "2"]

    tag1 = "jr2"
    fw1 = firmware.FirmwareVersion(version=tag1)
    assert fw1.version == tag1
    assert fw1.semantic_version is None


def test_class_semantic_compare():

    tag1 = "jrr-0.1.1"
    fw1 = firmware.FirmwareVersion(version=tag1)
    tag2 = tag1
    fw2 = firmware.FirmwareVersion(version=tag2)

    assert fw1 == fw1
    assert fw1 == fw2

    tag1 = "jrr-1.1.1"
    fw1 = firmware.FirmwareVersion(version=tag1)
    tag2 = "jrr-0.1.1"
    fw2 = firmware.FirmwareVersion(version=tag2)

    assert fw1 != fw2
    assert fw1 > fw2
    assert fw2 < fw1
    assert fw2 <= fw1
    assert fw1 >= fw2

    tag1 = "jrr-0.1.bb"
    fw1 = firmware.FirmwareVersion(version=tag1)
    tag2 = "jrr-0.1.a"
    fw2 = firmware.FirmwareVersion(version=tag2)
    assert fw1 != fw2
    assert fw1 > fw2
    assert fw2 < fw1
    assert fw2 <= fw1
    assert fw1 >= fw2

    tag1 = "jrr-10.1.aa"
    fw1 = firmware.FirmwareVersion(version=tag1)
    assert fw1.semantic_version == [10, 1, "aa"]
    tag2 = "jrr-9.1.a"
    fw2 = firmware.FirmwareVersion(version=tag2)
    assert fw1 != fw2
    assert fw1 > fw2
    assert fw2 < fw1
    assert fw2 <= fw1
    assert fw1 >= fw2

    tag1 = "jrr-9.1.aa"
    fw1 = firmware.FirmwareVersion(version=tag1)
    tag2 = "jrr-9.1.a"
    fw2 = firmware.FirmwareVersion(version=tag2)
    assert fw1 != fw2
    assert fw1 > fw2
    assert fw2 < fw1
    assert fw2 <= fw1
    assert fw1 >= fw2

    tag1 = "jrr-9.1.aa"
    fw1 = firmware.FirmwareVersion(version=tag1)
    tag2 = "jrr-9.2.a"
    fw2 = firmware.FirmwareVersion(version=tag2)
    assert fw1 != fw2
    assert not (fw1 > fw2)
    assert not (fw2 < fw1)
    assert not (fw2 <= fw1)
    assert not (fw1 >= fw2)


def test_class_semantic_sort():

    tags = ["jrr-0.2.1", "jrr-0.1.1",]

    lst1 = [firmware.FirmwareVersion(version=tag) for tag in tags]

    lst1_sorted = sorted(lst1)
    tags_sorted = sorted(tags)
    assert lst1_sorted[0].version == tags_sorted[0]


# ------------------------------------------------------------------
# FirmwareVersion.ensure_protocol


def test_ensure_protocol():
    url = "/tmp/"
    assert firmware.FirmwareVersion.ensure_protocol(url) == "file://" + url

    url = "https://www.google.com/"
    assert firmware.FirmwareVersion.ensure_protocol(url) == url

# ------------------------------------------------------------------
# test mocks


def test_firmware_mock1_fixture(mock_local_root1):
    assert firmware.firmware_local_root() == LOCAL_ROOT1


def test_firmware_mock2_fixture(mock_local_root2):
    assert firmware.firmware_local_root() == LOCAL_ROOT2


def test_firmware_mock1b_fixture(mock_local_root1):
    assert firmware.firmware_local_root() == LOCAL_ROOT1


# ------------------------------------------------------------------
# firmware_repo_url

def test_firmware_repo_url_1(mock_repo_url1):
    assert firmware.firmware_repo_url() == REPO_URL1


# ------------------------------------------------------------------
# firmware_repo_index

def test_firmware_repo_index_no_zips(mock_repo_url0):
    assert firmware.firmware_repo_url() == REPO_URL0
    fw_pkgs = firmware.firmware_repo_index()
    assert len(fw_pkgs) == 0


def test_firmware_repo_index_1_zip(mock_repo_url1):
    assert firmware.firmware_repo_url() == REPO_URL1
    fw_pkgs = firmware.firmware_repo_index()
    assert len(fw_pkgs) == 1


def test_firmware_repo_index_2_zip(mock_repo_url2):
    assert firmware.firmware_repo_url() == REPO_URL2
    fw_pkgs = firmware.firmware_repo_index()
    assert len(fw_pkgs) == 2
    assert "jrr-0.1.2.zip" in [fw.version for fw in fw_pkgs]


def test_firmware_repo_index_err(mock_repo_url_error):
    assert firmware.firmware_repo_url() == REPO_URL_ERR
    with pytest.raises(ValueError, match=f"Unsupported scheme"):
        fw_pkgs = firmware.firmware_repo_index()


def test_firmware_repo_index_err(mock_repo_github, mock_github_tags2):
    assert firmware.firmware_repo_url() == GITHUB_REPO
    fw_pkgs = firmware.firmware_repo_index()
    assert len(fw_pkgs) == 2
    assert JRR_TAG_001 in [fw.version for fw in fw_pkgs]
    assert JRR_TAG_011 in [fw.version for fw in fw_pkgs]

# ------------------------------------------------------------------
# firmware_current_link + firmware_current


def test_firmware_current_link0(mock_local_root0):
    assert firmware.firmware_local_root() == LOCAL_ROOT0
    assert firmware.firmware_current_link() is None
    assert firmware.firmware_current_link(realpath=True) is None


def test_firmware_current_link1(mock_local_root1):
    assert firmware.firmware_local_root() == LOCAL_ROOT1
    assert firmware.firmware_current_link() == os.path.join(
        LOCAL_ROOT1, APP_CONTEXT.FIRMWARE_CURRENT_LINK)


def test_firmware_current_realpath_1(mock_local_root1):
    assert firmware.firmware_local_root() == LOCAL_ROOT1
    current_path = firmware.firmware_current_link(realpath=True)
    assert current_path != os.path.join(
        LOCAL_ROOT1, APP_CONTEXT.FIRMWARE_CURRENT_LINK)
    assert current_path.startswith(LOCAL_ROOT1)
    assert current_path.endswith("dummy")


def test_firmware_current(mock_create_empty_local_root, mock_repo_url2, ):

    # Initially empty local_root
    assert firmware.firmware_local_root() == LOCAL_ROOT_STAGE
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    assert config.app_config.firmware_repo_url == REPO_URL2

    # Copy one version_tag from
    version_tag = "jrr-0.1.1"
    symlink_path = os.path.join(REPO_URL2, version_tag)
    dir_path = os.path.join(LOCAL_ROOT_STAGE, version_tag)
    shutil.copytree(symlink_path, dir_path)

    # Initially no current version
    current = firmware.firmware_current()
    assert current is None

    # Create symlink in LOCAL_ROOT_STAGE
    symlink_path = firmware.current_symlink_path(LOCAL_ROOT_STAGE)
    dir_path = os.path.join(LOCAL_ROOT_STAGE, version_tag)
    os.symlink(dir_path, symlink_path)

    current = firmware.firmware_current()
    assert current is not None


# ------------------------------------------------------------------
# firmware_local_index


def test_firmware_local_index1(mock_local_root1):
    fws = firmware.firmware_local_index()
    assert len(fws) == 1


def test_firmware_local_index2(mock_local_root2):
    fws = firmware.firmware_local_index()
    assert len(fws) == 2

# ------------------------------------------------------------------
# firmware_current


def test_firmware_current_no_local_repo_directory(mock_local_root0):
    fw = firmware.firmware_current()
    assert fw is None


def test_firmware_current_invalid_symbolic_link(mock_local_root1):
    fw = firmware.firmware_current()
    assert fw is None


def test_firmware_current_no_symbolick_link(mock_local_root2):
    fw = firmware.firmware_current()
    assert fw is None


# ------------------------------------------------------------------
# firmware_available_versions


def test_firmware_available_versions_for_empty_repo(mock_repo_url1, mock_create_empty_local_root):
    # Empty directory
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert os.path.exists(LOCAL_ROOT_STAGE)
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # There is one version in repo
    assert config.app_config.firmware_repo_url == REPO_URL1
    repo_index = firmware.firmware_repo_index()
    assert len(repo_index) == 1

    # There is also one version to choose
    avalaible_fws = firmware.firmware_available_versions()
    assert len(avalaible_fws) == 1

    # we can choose the version found in repo
    for i in range(len(repo_index)):
        assert repo_index[i].version == avalaible_fws[i].version


def test_firmware_available_versions_for_empty_repo2(mock_repo_url2, mock_create_empty_local_root):
    # Empty directory
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert os.path.exists(LOCAL_ROOT_STAGE)
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # There are versions in repo
    assert config.app_config.firmware_repo_url == REPO_URL2
    repo_index = firmware.firmware_repo_index()
    assert len(repo_index) == 2

    # There is also one version to choose
    avalaible_fws = firmware.firmware_available_versions()
    assert len(avalaible_fws) == 2

    # we can choose the version found in repo
    version_tags = sorted([fw.version for fw in repo_index])

    for i in range(len(repo_index)):
        assert version_tags[i] == avalaible_fws[i].version


def test_firmware_available_versions_newer(mock_repo_url2, mock_create_empty_local_root):
    # Empty local root directory
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert os.path.exists(LOCAL_ROOT_STAGE)
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # There are 2 versions in repo
    assert config.app_config.firmware_repo_url == REPO_URL2
    repo_index = firmware.firmware_repo_index()
    assert len(repo_index) == 2

    # Copy one version_tag from repo to local index
    version_tag = "jrr-0.1.1"
    src = os.path.join(REPO_URL2, version_tag)
    dest = os.path.join(LOCAL_ROOT_STAGE, version_tag)
    shutil.copytree(src, dest)

    # There is just one version to choose ()
    avalaible_fws = firmware.firmware_available_versions()
    assert len(avalaible_fws) == 1

    assert avalaible_fws[0].version == "jrr-0.1.2.zip"


def test_firmware_available_versions_w_symlink(mock_repo_url2, mock_create_empty_local_root):
    # Empty local root directory
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert os.path.exists(LOCAL_ROOT_STAGE)
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # There are 2 versions in repo
    assert config.app_config.firmware_repo_url == REPO_URL2
    repo_index = firmware.firmware_repo_index()
    assert len(repo_index) == 2

    # Copy one version_tag from repo to local index
    version_tag = "jrr-0.1.2"
    src = os.path.join(REPO_URL2, version_tag)
    dest = os.path.join(LOCAL_ROOT_STAGE, version_tag)
    shutil.copytree(src, dest)

    # make it active
    symlink_path = firmware.current_symlink_path(LOCAL_ROOT_STAGE)
    dir_path = os.path.join(LOCAL_ROOT_STAGE, version_tag)
    os.symlink(dir_path, symlink_path)

    # There is just one version to choose ()
    avalaible_fws = firmware.firmware_available_versions()
    print(f"{avalaible_fws=}")

    assert len(avalaible_fws) == 0


def test_firmware_available_versions_wo_symlink(mock_repo_url2, mock_create_empty_local_root):
    # Empty local root directory
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert os.path.exists(LOCAL_ROOT_STAGE)
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # There are 2 versions in repo
    assert config.app_config.firmware_repo_url == REPO_URL2
    repo_index = firmware.firmware_repo_index()
    assert len(repo_index) == 2

    # Copy one version_tag from repo to local index
    version_tag = "jrr-0.1.2"
    src = os.path.join(REPO_URL2, version_tag)
    dest = os.path.join(LOCAL_ROOT_STAGE, version_tag)
    shutil.copytree(src, dest)

    # NO symlink created --> nothing is active
    symlink_path = firmware.current_symlink_path(LOCAL_ROOT_STAGE)
    dir_path = os.path.join(LOCAL_ROOT_STAGE, version_tag)
    # os.symlink(dir_path, symlink_path)

    # There is just one version to choose from
    avalaible_fws = firmware.firmware_available_versions()
    print(f"{avalaible_fws=}")

    assert len(avalaible_fws) == 1
    assert avalaible_fws[0].version == "jrr-0.1.1.zip"

# ------------------------------------------------------------------
# firmware_choose


def test_firmware_choose_ok(mock_create_empty_local_root, mock_repo_url1):
    # Assert empty local repo
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # Assert one version to download
    assert config.app_config.firmware_repo_url == REPO_URL1
    fws = firmware.firmware_available_versions()
    assert len(fws) == 1

    # Chose the existing entry in remote repo
    version_tag = "jrr-0.1.1.zip"
    chosen_firmware = fws[0]
    assert chosen_firmware.repo_url == firmware.FirmwareVersion.ensure_protocol(
        os.path.join(REPO_URL1, version_tag))

    # Choose = SUT
    dest_path = firmware.firmware_choose(fws[0])
    assert dest_path is not None

    # Expect to find zip file/directory + pending link
    local_repo_entries = os.listdir(LOCAL_ROOT_STAGE)
    assert version_tag in local_repo_entries
    assert APP_CONTEXT.FIRMWARE_PENDING_LINK in local_repo_entries
    assert len(local_repo_entries) == 2


def test_firmware_choose_twice(mock_create_empty_local_root, mock_repo_url2):
    # Assert empty local repo
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # Assert one version to download
    assert config.app_config.firmware_repo_url == REPO_URL2
    fws = firmware.firmware_available_versions()
    assert len(fws) == 2
    print(f"{fws=}")

    # Chose the existing entry in remote repo
    version_tag = "jrr-0.1.1.zip"
    chosen_firmware = fws[0]
    assert chosen_firmware.repo_url == firmware.FirmwareVersion.ensure_protocol(
        os.path.join(REPO_URL2, version_tag))

    # Choose = SUT
    dest_path = firmware.firmware_choose(fws[0])
    assert dest_path is not None

    # Expect to find zip file/directory + pending link
    local_repo_entries = os.listdir(LOCAL_ROOT_STAGE)
    assert version_tag in local_repo_entries
    assert APP_CONTEXT.FIRMWARE_PENDING_LINK in local_repo_entries
    assert len(local_repo_entries) == 2

    os.remove(firmware.firmware_pending_link())
    dest_path = firmware.firmware_choose(fws[1])
    print(f"{dest_path=}")
    assert dest_path is not None

    local_repo_entries = os.listdir(LOCAL_ROOT_STAGE)
    assert fws[1].version in local_repo_entries
    assert APP_CONTEXT.FIRMWARE_PENDING_LINK in local_repo_entries
    assert len(local_repo_entries) == 3


def test_firmware_pending_version_tag_exists(
        mock_create_empty_local_root, mock_repo_url1):
    # Assert empty local repo
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # Assert one version to download
    assert config.app_config.firmware_repo_url == REPO_URL1
    fws = firmware.firmware_available_versions()
    assert len(fws) == 1

    # Chose the existing entry in remote repo
    version_tag = "jrr-0.1.1.zip"
    chosen_firmware = fws[0]
    assert chosen_firmware.repo_url == firmware.FirmwareVersion.ensure_protocol(
        os.path.join(REPO_URL1, version_tag))

    # Create vession_tag
    version_tag_path = firmware.firmware_local_version_tag(version_tag)
    print(f"{version_tag_path=}")

    open(version_tag_path, 'a').close()

    # Choose = SUT
    with pytest.raises(FileExistsError, match=f"File exists.*{version_tag}"):
        firmware.firmware_choose(fws[0])

# ------------------------------------------------------------------
# firmware_cleanup:


def test_firmware_cleanup_empty_repo(
        mock_create_empty_local_root, mock_repo_url1):
    # Assert empty local repo
    assert config.app_config.firmware_local_root == LOCAL_ROOT_STAGE
    assert len(os.listdir(LOCAL_ROOT_STAGE)) == 0

    # No cleanup for empty local repo
    ret = firmware.firmware_cleanup()
    assert not ret
