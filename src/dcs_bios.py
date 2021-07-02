from shutil import copytree
import PySimpleGUI as PyGUI
import os
import re
import requests
import tempfile
import zipfile

DCS_BIOS_VERSION = "0.7.40"
DCS_BIOS_URL = "https://github.com/DCSFlightpanels/dcs-bios/releases/download/{}/DCS-BIOS_{}.zip"

# examine DCS mods to see if DCS-BIOS is installed and returns a version string, None if
# DCS-BIOS is not installed. we use a non-standard release_version.txt file we'll add to
# DCS-BIOS on install
#
def detect_dcs_bios(dcs_path):
    try:
        with open(dcs_path + "\\Scripts\\Export.lua", "r") as f:
            export_str = f.read()
    except:
        export_str = ""
    try:
        with open(dcs_path + "\\Scripts\\DCS-BIOS\\release_version.txt") as f:
            relver_str = f.read()
    except:
        relver_str = "?.?.?"

    version = None
    if "dofile(lfs.writedir()..[[Scripts\DCS-BIOS\BIOS.lua]])" in export_str:
        if os.path.exists(dcs_path + "\\Scripts\\DCS-BIOS"):
                version = relver_str

    return version

# install dcs bios
#
def install_dcs_bios(dcs_path):
    try:
        with open(dcs_path + "Scripts\\Export.lua", "r") as f:
            export_str = f.read()
    except FileNotFoundError:
        export_str = str()

    with open(dcs_path + "Scripts\\Export.lua", "a") as f:
        if "dofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])" not in export_str:
            f.write(f"\n-- DCSFlightpanels/dcs-bios v{DCS_BIOS_VERSION}\n" +
                     "dofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])\n")

    with tempfile.TemporaryDirectory() as tmp_dir:
        url = DCS_BIOS_URL.format(DCS_BIOS_VERSION, DCS_BIOS_VERSION)
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with tempfile.TemporaryFile() as tmp_file:
            for block in response.iter_content(1024):
                tmp_file.write(block)

            with zipfile.ZipFile(tmp_file) as zip_ref:
                zip_ref.extractall(tmp_dir)

            copytree(tmp_dir + '\\dcs-bios-0.10.0', dcs_path + "Scripts\\DCS-BIOS")

            PyGUI.Popup(f'DCS-BIOS v{DCS_BIOS_VERSION} successfully downloaded and installed')