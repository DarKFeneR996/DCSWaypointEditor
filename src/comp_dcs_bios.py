'''

comp_dcs_bios.py: DCS-BIOS component version management

'''

import os
import requests
import tempfile
import zipfile

from shutil import copytree, copyfile, move

from src.logger import get_logger

DCS_BIOS_VERSION = "0.7.40"
DCS_BIOS_URL = "https://github.com/DCSFlightpanels/dcs-bios/releases/download/{}/DCS-BIOS_{}.zip"
DCS_BIOS_EXPORT = "dofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])"

logger = get_logger(__name__)

# back up a file/directory at a path. returns True on success, False on failure
#
def backup_path(src_path, is_move=True):
    if os.path.exists(src_path):
        for i in [ "", "_0", "_1", "_2", "_3"]:
            dst_path = src_path + f".bak{i}"
            if not os.path.exists(dst_path):
                if is_move:
                    logger.debug(f"backup moves {src_path} --> {dst_path}")
                    move(src_path, dst_path)
                elif os.path.isdir(src_path):
                    logger.debug(f"backup copy (tree) {src_path} --> {dst_path}")
                    copytree(src_path, dst_path)
                else:
                    logger.debug(f"backup copy (file) {src_path} --> {dst_path}")
                    copyfile(src_path, dst_path)
                return True
    else:
        return True
    return False

# check if Export.lua has the magic string to include DCS-BIOS
#
def is_export_setup(dcs_path):
    try:
        with open(dcs_path + "\\Scripts\\Export.lua", "r") as f:
            export_str = f.read()
    except:
        export_str = ""
    return True if DCS_BIOS_EXPORT in export_str else False

# get current DCS-BIOS version DCSWE expects to be using.
#
def dcs_bios_vers_latest():
    return DCS_BIOS_VERSION

# get version of installed DCS-BIOS mod.
#
# examine DCS mods to see if DCS-BIOS is installed and returns a version string, None if
# DCS-BIOS is not installed. we use a non-standard release_version.txt file we'll add to
# DCS-BIOS on install
#
def dcs_bios_vers_install(dcs_path):
    relver_str = None
    try:
        with open(dcs_path + "\\Scripts\\DCS-BIOS\\release_version.txt") as f:
            relver_str = f.read()
    except:
        relver_str = "?.?.?"

    is_export = is_export_setup(dcs_path)
    is_db_dir = os.path.exists(dcs_path + "\\Scripts\\DCS-BIOS")
    status = relver_str if is_export and is_db_dir else None
    logger.debug(f"install state: Export.lua {is_export}, DCS-BIOS {is_db_dir}," +
                 f" release_version.txt {relver_str} --> '{status}'")

    return status

# check if DCS-BIOS is up-to-date.
#
def dcs_bios_is_current(dcs_path):
    return True if dcs_bios_vers_install(dcs_path) == DCS_BIOS_VERSION else False

# install DCS-BIOS
#
def dcs_bios_install(dcs_path):
    vers_install = None

    if (backup_path(dcs_path + "\\Scripts\\DCS-BIOS", is_move=True) and \
        (is_export_setup(dcs_path) or \
         backup_path(dcs_path + "\\Scripts\\Export.lua", is_move=False))):
        with tempfile.TemporaryDirectory() as tmp_dir:
            url = DCS_BIOS_URL.format(DCS_BIOS_VERSION, DCS_BIOS_VERSION)
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
            except:
                logger.debug(f"request for {url} fails")
                return None

            with tempfile.TemporaryFile() as tmp_file:
                for block in response.iter_content(1024):
                    tmp_file.write(block)

                with zipfile.ZipFile(tmp_file) as zip_ref:
                    zip_ref.extractall(tmp_dir)

                copytree(tmp_dir + '\\DCS-BIOS', dcs_path + "\\Scripts\\DCS-BIOS")
                logger.debug(f"{url} downloaded and extracted")
    
        if not is_export_setup(dcs_path):
            with open(dcs_path + "\\Scripts\\Export.lua", "a") as f:
                f.write(f"\n{DCS_BIOS_EXPORT}\n")
            logger.debug(f"updated Export.lua")

        with open(dcs_path + "\\Scripts\\DCS-BIOS\\release_version.txt", "w") as f:
            f.write(f"{DCS_BIOS_VERSION}")
        logger.debug(f"updated release_version.txt")

        vers_install = DCS_BIOS_VERSION

    return vers_install