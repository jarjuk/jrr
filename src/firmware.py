"""Module managing firmware updates.

Firmware is a subdirectory under 'firmware_root'. Current firmware is
pointed by a symbolic link.

Uses semantic versioning policy:
- cleanup removes versions older than current
- upgradeable versions are more recent than current
-

"""

from dataclasses import dataclass
from typing import Tuple, List, Self
import os
import glob
import shutil
import re
from urllib.parse import urlparse


from src.config import app_config
from src.constants import APP_CONTEXT
from src.utils import copy_file_or_directory

import logging
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Data class


@dataclass
class FirmwareVersion:
    """Firmaware version location and version id"""
    version: str                     # semantic versioning tag, parsed
    # using FIRMWARE_TAG_PATTERN
    repo_url: str | None = None      # firmware repository (with protocol)
    local_url: str | None = None     # local file path (simple pat)

    # Factories
    @classmethod
    def create_repo_version(cls, repo_url: str) -> Self:
        """Factory method to from repo-url"""
        version_tag = FirmwareVersion.url2version_tag(repo_url)
        firmware_version = cls(
            version=version_tag, repo_url=FirmwareVersion.ensure_protocol(repo_url))
        return firmware_version

    @classmethod
    def create_local_version(cls, file_path: str) -> Self:
        """Factory method for firmware in local repo"""
        version_tag = FirmwareVersion.url2version_tag(file_path)
        firmware_version = cls(version=version_tag, local_url=file_path)
        return firmware_version

    # Comparison

    def __eq__(self, other) -> bool:
        triple1 = self.semantic_version
        triple2 = other.semantic_version
        return triple1 == triple2

    def __gt__(self, other) -> bool:
        triple1 = self.semantic_version
        triple2 = other.semantic_version
        return triple1 > triple2

    def __ge__(self, other) -> bool:
        triple1 = self.semantic_version
        triple2 = other.semantic_version
        return triple1 >= triple2

    # Utilities

    @property
    def semantic_version(self) -> Tuple[int, int, int]:
        """Semantic versioning policy triple for 'self.version' """
        pattern = r"[^0-9]*(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>\w+)"
        matchi = re.search(pattern, self.version)
        if not matchi:
            return None
        return [int(matchi['major']), int(matchi['minor']), matchi['patch']]

    def local_directory(self) -> str:
        """Version sub-directory for the firmware code."""
        raise NotImplementedError("TODO")

    @staticmethod
    def url2version_tag(url) -> str:
        """Extract version_tag from 'url'."""
        return os.path.basename(url)

    @staticmethod
    def ensure_protocol(url) -> str:
        o = urlparse(url)
        logger.debug("ensure_protocol: o='%s'", o)
        if o.scheme is None or o.scheme == "":
            return "file://" + url
        return url


# ------------------------------------------------------------------
# Locations


def firmware_local_root():
    """Root directory for version sub-directories."""
    return app_config.firmware_local_root


def firmware_local_version_tag(version_tag: str) -> str:
    """version_tag directory/file under firmware_local_root."""
    return os.path.join(firmware_local_root(), version_tag)


def firmware_repo_url() -> str:
    """Firmaware repository url."""
    return app_config.firmware_repo_url


def firmware_pending_link(local_root: str | None = None) -> str:
    """Name of symbolic link pointing to version sub-directory
    containing next firmware version to activate.

    """
    if local_root is None:
        local_root = firmware_local_root()
    symlink_path = os.path.join(local_root, APP_CONTEXT.FIRMWARE_PENDING_LINK)
    logger.debug("firmware_pending_link: symlink_path='%s'", symlink_path)
    return symlink_path


def current_symlink_path(local_root: str | None = None) -> str:
    """Symbolic link path pointing to version sub-directory."""
    if local_root is None:
        local_root = firmware_local_root()
    symlink_path = os.path.join(local_root, APP_CONTEXT.FIRMWARE_CURRENT_LINK)
    logger.debug("current_symlink_path: symlink_path='%s'", symlink_path)
    return symlink_path


def firmware_current_link(realpath: bool = False) -> str | None:
    """Symbolic link path pointing to version sub-directory containing
    current firmware.

    :realpath: convert symbolic link to realpath

    :return: None if no path exists
    """
    symlink_path = current_symlink_path()

    if not os.path.exists(symlink_path):
        logger.warning(
            "firmware_current_link: symlink_path='%s' does not exist", symlink_path)
        return None

    if not realpath:
        return symlink_path
    target_path = os.path.realpath(symlink_path)
    logger.debug("firmware_current_link: target_path='%s'", target_path)

    if not os.path.exists(target_path):
        logger.info(
            "firmware_current_link: target_path='%s' for symlink_path='%s' does not exist",
            target_path, symlink_path, )
        return None

    return target_path


# ------------------------------------------------------------------
# Basic actions/firmware_repo_index

def _local_zip_index(repo_url: str) -> List[FirmwareVersion]:
    """Return list of zip files in 'repo_url'

    :repo_url: file path to directory

    """

    zip_files_pattern = f"{repo_url}/*.zip"
    file_glob = glob.glob(zip_files_pattern)

    # return list of 'FirmwareVersion' object for subdirectory names
    firmwares = [FirmwareVersion.create_repo_version(repo_url=dirent)
                 for dirent in file_glob
                 if os.path.isfile(dirent) and
                 re.search(APP_CONTEXT.FIRMWARE_TAG_PATTERN, dirent)]

    return firmwares


def firmware_repo_index() -> List[FirmwareVersion]:
    """Return list of firmware versions in 'firmware repo'."""
    repo_url = app_config.firmware_repo_url
    parsed = urlparse(repo_url)

    if parsed.scheme == "file" or parsed.scheme == "":
        return _local_zip_index(repo_url=repo_url)
    else:
        raise ValueError(
            f"Unsupported scheme='{parsed.scheme}' in {repo_url=}")

# ------------------------------------------------------------------
# Basic actions/firmware_repo_index


def firmware_local_index() -> List[FirmwareVersion]:
    """return list of 'FirmwareVersion' object under directory
    'firmware_local_root'

    Valid entries:
    - is sub-directory
    - sub-directory pattern/tag like 'jrr-0.1.2'

    """

    version_sub_directory_pattern = f"{firmware_local_root()}/*"
    local_repo_glob = glob.glob(version_sub_directory_pattern)
    logger.info("firmware_local_index: version_sub_directories='%s' for pattern='%s'",
                local_repo_glob, version_sub_directory_pattern,
                )
    logger.info("firmware_local_index: app_config.firmware_local_root=%s",
                app_config.firmware_local_root)

    # return list of 'FirmwareVersion' object for subdirectory names
    firmwares = [FirmwareVersion.create_local_version(file_path=dirent)
                 for dirent in local_repo_glob
                 if os.path.isdir(dirent) and
                 re.search(APP_CONTEXT.FIRMWARE_TAG_PATTERN, dirent)]

    return firmwares


def firmware_current() -> FirmwareVersion | None:
    """Return version for current firmware in 'firmware_current_link'."""
    dir_path = firmware_current_link(realpath=True)
    if dir_path is None:
        return None

    matchi = re.search(APP_CONTEXT.FIRMWARE_TAG_PATTERN, dir_path)
    logger.debug("firmware_current: matchi='%s'", matchi)
    if not matchi:
        return None

    return FirmwareVersion.create_local_version(dir_path)


def firmware_repo_download(firmware_version: FirmwareVersion):
    """Download 'firmware_version' from repo into a local sub-directory.
    """
    raise NotImplementedError("TODO")


def firmware_set_pending(firmware_version: FirmwareVersion):
    """Set 'firmware_version' as a pending version (=to be activated on
    next app reboot).
    """

    raise NotImplementedError("TODO")


# ------------------------------------------------------------------
# Rules

def _loadable(
        repo_versions: List[FirmwareVersion],
        local_versions: List[FirmwareVersion],
        current_version: FirmwareVersion | None,
) -> List[FirmwareVersion]:
    """Return firmware versions, which may be downloaded from repo."""
    raise NotImplementedError("TODO")


# ------------------------------------------------------------------
# Module services


def firmware_available_versions() -> List[FirmwareVersion]:
    """Return sorted list of available firmware versions.

    Available firmaware versions:

    - are found in remote repo

    - which do not exist in local repo

    - newer than current firmware (=version_tag greater in current
      firmware)

    """
    repo_index = firmware_repo_index()
    local_index = firmware_local_index()

    # maybe None (if no FIRMWARE_CURRENT_LINK exist)
    current_firmware = firmware_current()

    def choose_applicable(remotes: List[FirmwareVersion],
                          downloaded: List[FirmwareVersion],
                          current: FirmwareVersion | None,
                          ) -> List[FirmwareVersion]:
        """Rule for including remote repo firmware version."""
        return [fw for fw in remotes
                if fw not in downloaded and (
                    current is None or current < fw
                )]

    available = choose_applicable(
        remotes=repo_index,
        downloaded=local_index,
        current=current_firmware)

    return sorted(available)


def firmware_cleanup():
    """Remove old firmaware versions from local repo

    """
    local_index = firmware_local_index()
    logger.debug("firmware_cleanup: local_index='%s'", local_index)

    current_firmware = firmware_current()

    if current_firmware is None:
        logger.warning(
            "firmware_cleanup: No current firmaware local_index='%s'",
            local_index)
        return False

    for fw in local_index:
        if fw < current_firmware:
            logger.info("firmware_cleanup: fw='%s' < %s", fw, current_firmware)
            shutil.rmtree(fw.local_url)

    return True


def firmware_choose(firmware_version: FirmwareVersion) -> str | None:
    """Ensure 'firmware_version' is downloaded to local repo, and add
    pending symlink pointing to this entry.

    Downloads 'firmware_version.repo_url' unless already downloaded.

    Creates symlink pointing to the local firmware version entry in
    local.

    :raises: FileExistsError is pending symlink already exists

    :return: True on success

    """
    logger.info("firmware_choose: firmware_version.repo_url='%s'",
                firmware_version.repo_url)
    if firmware_version.repo_url is None:
        raise ValueError(f"No repo url: {firmware_version}")

    # Copy remote repo -> local repo
    dest_path = copy_file_or_directory(src=firmware_version.repo_url,
                                       dest=firmware_local_root())

    # Create symlink to dest_path (in local repo)
    symlink_path = firmware_pending_link()
    os.symlink(dest_path, symlink_path)

    return dest_path
