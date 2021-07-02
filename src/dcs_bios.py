from shutil import copytree, copyfile, move
import os
import requests
import tempfile
import zipfile

DCS_BIOS_VERSION = "0.7.40"
DCS_BIOS_URL = "https://github.com/DCSFlightpanels/dcs-bios/releases/download/{}/DCS-BIOS_{}.zip"

DCS_BIOS_EXPORT = "dofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])"

# back up a file/directory at a path. returns True on success, False on failure
#
def backup_path(src_path, is_move=True):
    if os.path.exists(src_path):
        for i in [ "", "_0", "_1", "_2", "_3"]:
            dst_path = src_path + f".bak{i}"
            if not os.path.exists(dst_path):
                if is_move:
                    move(src_path, dst_path)
                elif os.path.isdir(src_path):
                    copytree(src_path, dst_path)
                else:
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

# get current DCS-BIOS version
#
def dcs_bios_vers_current():
    return DCS_BIOS_VERSION

# examine DCS mods to see if DCS-BIOS is installed and returns a version string, None if
# DCS-BIOS is not installed. we use a non-standard release_version.txt file we'll add to
# DCS-BIOS on install
#
def dcs_bios_vers_install(dcs_path):
    try:
        with open(dcs_path + "\\Scripts\\DCS-BIOS\\release_version.txt") as f:
            relver_str = f.read()
    except:
        relver_str = "?.?.?"

    version = None
    if is_export_setup(dcs_path) and os.path.exists(dcs_path + "\\Scripts\\DCS-BIOS"):
        version = relver_str

    return version

# check if DCS-BIOS is up-to-date.
#
def is_dcs_bios_current(dcs_path):
    return True if dcs_bios_vers_install(dcs_path) == DCS_BIOS_VERSION else False

# install DCS-BIOS
#
def dcs_bios_install(dcs_path):
    vers_install = None

    if (backup_path(dcs_path + "\\Scripts\\DCS-BIOS", is_move=True) and \
        backup_path(dcs_path + "\\Scripts\\Export.lua", is_move=False)):
        with tempfile.TemporaryDirectory() as tmp_dir:
            url = DCS_BIOS_URL.format(DCS_BIOS_VERSION, DCS_BIOS_VERSION)
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
            except:
                return None

            with tempfile.TemporaryFile() as tmp_file:
                for block in response.iter_content(1024):
                    tmp_file.write(block)

                with zipfile.ZipFile(tmp_file) as zip_ref:
                    zip_ref.extractall(tmp_dir)

                copytree(tmp_dir + '\\DCS-BIOS', dcs_path + "\\Scripts\\DCS-BIOS")
    
        if not is_export_setup(dcs_path):
            with open(dcs_path + "\\Scripts\\Export.lua", "a") as f:
                f.write(f"\n{DCS_BIOS_EXPORT}\n")

        with open(dcs_path + "\\Scripts\\DCS-BIOS\\release_version.txt", "w") as f:
            f.write(f"{DCS_BIOS_VERSION}")

        vers_install = DCS_BIOS_VERSION

            #PyGUI.Popup(f'DCS-BIOS v{DCS_BIOS_VERSION} successfully downloaded and installed')

    return vers_install