from shutil import copytree
import PySimpleGUI as PyGUI
import os
import re
import requests
import tempfile
import zipfile

DCS_BIOS_VERSION = '0.10.0'
DCS_BIOS_URL = "https://github.com/dcs-bios/dcs-bios/archive/refs/tags/v{}.zip"

DCS_BIOS_VERSION = "0.7.40"
DCS_BIOS_URL = "https://github.com/DCSFlightpanels/dcs-bios/releases/download/{}/DCS-BIOS_{}.zip"

# examine DCS Export.lua to see if DCS-BIOS is installed and returns a version string.
#
def detect_dcs_bios(dcs_path):
    version = None

    try:
        with open(dcs_path + "\\Scripts\\Export.lua", "r") as f:
            export_str = f.read()
        if r"dofile(lfs.writedir()..[[Scripts\DCS-BIOS\BIOS.lua]])" in export_str and \
                os.path.exists(dcs_path + "\\Scripts\\DCS-BIOS"):
            match = re.match(r"^-- DCSFlightpanels/dcs-bios (?P<vers>[\S]+)$", export_str)
            if match:
                version = match.group('vers')
            else:
                version = "v?.?.?"
    except:
        pass
    return version

# install dcs bios
#
def install_dcs_bios(dcs_path):
    try:
        with open(dcs_path + "Scripts\\Export.lua", "r") as f:
            filestr = f.read()
    except FileNotFoundError:
        filestr = str()

    with open(dcs_path + "Scripts\\Export.lua", "a") as f:
        if "dofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])" not in filestr:
            f.write(
                "\ndofile(lfs.writedir()..[[Scripts\\DCS-BIOS\\BIOS.lua]])\n")

    with tempfile.TemporaryDirectory() as tmp_dir:
        url = DCS_BIOS_URL.format(DCS_BIOS_VERSION)
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with tempfile.TemporaryFile() as tmp_file:
            for block in response.iter_content(1024):
                tmp_file.write(block)

            with zipfile.ZipFile(tmp_file) as zip_ref:
                zip_ref.extractall(tmp_dir)

            copytree(tmp_dir + '\\dcs-bios-0.10.0', dcs_path + "Scripts\\DCS-BIOS")

            PyGUI.Popup(f'DCS-BIOS v{DCS_BIOS_VERSION} successfully downloaded and installed')