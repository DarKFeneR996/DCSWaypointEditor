'''
*
*  prefs.py: DCS Waypoint Editor preferences model/object
*
*  Copyright (C) 2021 twillis/ilominar
*
*  This program is free software: you can redistribute it and/or modify
*  it under the terms of the GNU General Public License as published by
*  the Free Software Foundation, either version 3 of the License, or
*  (at your option) any later version.
*
*  This program is distributed in the hope that it will be useful,
*  but WITHOUT ANY WARRANTY; without even the implied warranty of
*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*  GNU General Public License for more details.
*
*  You should have received a copy of the GNU General Public License
*  along with this program.  If not, see <https://www.gnu.org/licenses/>.
*
'''

import os
import re

from configparser import ConfigParser
from pathlib import Path
from src.gui_util import airframe_list, airframe_type_to_ui_text


# preferences object to abstract preferences storage. preference values are always strings.
#
class Preferences:
    def __init__(self, file="settings.ini"):
        self.bs_file = file

        self.prefs = ConfigParser()
        self.prefs.add_section("PREFERENCES")

        self.path_dcs = f"{str(Path.home())}\\Saved Games\\DCS.openbeta\\"
        self.path_tesseract = f"{os.environ['PROGRAMW6432']}\\Tesseract-OCR\\tesseract.exe"
        self.path_mission = f"{str(Path.home())}\\Desktop\\dcs_mission.xml"
        self.dcs_btn_rel_delay_short = "0.15"
        self.dcs_btn_rel_delay_medium = "0.40"
        self.hotkey_capture = "ctrl+t"
        self.hotkey_capture_mode = "ctrl+shift+t"
        self.hotkey_enter_profile = "ctrl+alt+t"
        self.hotkey_enter_mission = "ctrl+alt+shift+t"
        self.hotkey_dgft_dogfight = "ctrl+3"
        self.hotkey_dgft_center = "ctrl+4"
        self.airframe_default = "viper"
        self.av_setup_default = "DCS Default"
        self.callsign_default = "Colt1-1"
        self.is_auto_upd_check = "true"
        self.is_tesseract_debug = "false"
        self.is_av_setup_for_unk = "true"
        self.profile_db_name = "profiles.db"

        try:
            open(self.bs_file, "r").close()
            self.synchronize_prefs()
            self.is_new_prefs_file = False
        except FileNotFoundError:
            self.persist_prefs()
            self.is_new_prefs_file = True

    # ================ general properties

    @property
    def is_new_prefs_file(self):
        return self._is_new_prefs_file

    @is_new_prefs_file.setter
    def is_new_prefs_file(self, value):
        self._is_new_prefs_file = value

    @property
    def prefs(self):
        return self._prefs
    
    @prefs.setter
    def prefs(self, value):
        self._prefs = value

    # ================ preferences properties

    @property
    def path_dcs(self):
        return self._path_dcs
    
    @path_dcs.setter
    def path_dcs(self, value):
        if value is not None and not value.endswith("\\") and not value.endswith("/"):
            value = value + "\\"
        self._path_dcs = value

    @property
    def path_tesseract(self):
        return self._path_tesseract

    @path_tesseract.setter
    def path_tesseract(self, value):
        self._path_tesseract = value

    @property
    def path_mission(self):
        return self._path_mission
    
    @path_mission.setter
    def path_mission(self, value):
        self._path_mission = value

    @property
    def dcs_btn_rel_delay_short(self):
        return self._dcs_btn_rel_delay_short

    @dcs_btn_rel_delay_short.setter
    def dcs_btn_rel_delay_short(self, value):
        if float(value) <= 0.0:
            raise ValueError("Short button release delay must be larger than zero")
        self._dcs_btn_rel_delay_short = value

    @property
    def dcs_btn_rel_delay_medium(self):
        return self._dcs_btn_rel_delay_medium

    @dcs_btn_rel_delay_medium.setter
    def dcs_btn_rel_delay_medium(self, value):
        if float(value) <= 0.0:
            raise ValueError("Medium button release delay must be larger than zero")
        self._dcs_btn_rel_delay_medium = value

    @property
    def hotkey_capture(self):
        return self._hotkey_capture
    
    @hotkey_capture.setter
    def hotkey_capture(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_capture = value

    @property
    def hotkey_capture_mode(self):
        return self._hotkey_capture_mode
    
    @hotkey_capture_mode.setter
    def hotkey_capture_mode(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_capture_mode = value

    @property
    def hotkey_enter_profile(self):
        return self._hotkey_enter_profile
    
    @hotkey_enter_profile.setter
    def hotkey_enter_profile(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_enter_profile = value

    @property
    def hotkey_enter_mission(self):
        return self._hotkey_enter_mission
    
    @hotkey_enter_mission.setter
    def hotkey_enter_mission(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_enter_mission = value

    @property
    def hotkey_dgft_dogfight(self):
        return self._hotkey_dgft_dogfight
    
    @hotkey_dgft_dogfight.setter
    def hotkey_dgft_dogfight(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_dgft_dogfight = value

    @property
    def hotkey_dgft_center(self):
        return self._hotkey_dgft_center
    
    @hotkey_dgft_center.setter
    def hotkey_dgft_center(self, value):
        if not self.is_hotkey_valid(value):
            raise ValueError("Invalid hotkey")
        self._hotkey_dgft_center = value

    @property
    def airframe_default(self):
        return self._airframe_default
    
    @airframe_default.setter
    def airframe_default(self, value):
        if airframe_type_to_ui_text(value) is None:
            raise ValueError("Unknown airframe type")
        self._airframe_default = value

    @property
    def av_setup_default(self):
        return self._av_setup_default
    
    @av_setup_default.setter
    def av_setup_default(self, value):
# TODO: fixme
        self._av_setup_default = value

    @property
    def callsign_default(self):
        return self._callsign_default
    
    @callsign_default.setter
    def callsign_default(self, value):
        if not self.is_callsign_valid(value):
            raise ValueError("Invalid callsign")
        self._callsign_default = value

    @property
    def is_auto_upd_check(self):
        return self._is_auto_upd_check

    @property
    def is_auto_upd_check_bool(self):
        return True if self._is_auto_upd_check == "true" else False

    @is_auto_upd_check.setter
    def is_auto_upd_check(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value == True else "false"
        self._is_auto_upd_check = value

    @property
    def is_tesseract_debug(self):
        return self._is_tesseract_debug

    @property
    def is_tesseract_debug_bool(self):
        return True if self._is_tesseract_debug == "true" else False

    @is_tesseract_debug.setter
    def is_tesseract_debug(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value else "false"
        self._is_tesseract_debug = value

    @property
    def is_av_setup_for_unk(self):
        return self._is_av_setup_for_unk

    @property
    def is_av_setup_for_unk_bool(self):
        return True if self._is_av_setup_for_unk == "true" else False

    @is_av_setup_for_unk.setter
    def is_av_setup_for_unk(self, value):
        if type(value) == bool or type(value) == int or type(value) == float:
            value = "true" if value else "false"
        self._is_av_setup_for_unk = value

    @property
    def profile_db_name(self):
        return self._profile_db_name

    @profile_db_name.setter
    def profile_db_name(self, value):
        self._profile_db_name = value

    # ================ general methods

    # validate a hot key sequence
    #
    def is_hotkey_valid(self, hotkey):
        if hotkey is not None and hotkey != "":
            tokens = hotkey.replace(" ", "+").split("+")
            if len(tokens) >= 1:
                key = tokens.pop()
                if key is None or len(key) != 1:
                    return False
                for token in tokens:
                    if token.lower() not in ("ctrl", "alt", "shift", "left", "right"):
                        return False
            else:
                return False
        return True

    # validate a callsign
    #
    def is_callsign_valid(self, callsign):
        if callsign != "" and not re.match(r"^[\D]+[\d]+-[\d]+$", callsign):
            return False
        else:
            return True

    # reset the preferences to their default values, must persist via persist_prefs to save.
    #
    def reset_prefs(self):
        self.path_dcs = f"{str(Path.home())}\\Saved Games\\DCS.openbeta\\"
        self.path_tesseract = f"{os.environ['PROGRAMW6432']}\\Tesseract-OCR\\tesseract.exe"
        self.path_mission = f"{str(Path.home())}\\Desktop\\cf_mission.xml"
        self.dcs_btn_rel_delay_short = "0.15"
        self.dcs_btn_rel_delay_medium = "0.40"
        self.hotkey_capture = "ctrl+t"
        self.hotkey_capture_mode = "ctrl+shift+t"
        self.hotkey_enter_profile = "ctrl+alt+t"
        self.hotkey_enter_mission = "ctrl+alt+shift+t"
        self.hotkey_dgft_dogfight = "ctrl+3"
        self.hotkey_dgft_center = "ctrl+4"
        self.airframe_default = "viper"
        self.av_setup_default = "DCS Default"
        self.callsign_default = "Colt1-1"
        self.is_auto_upd_check = "true"
        self.is_tesseract_debug = "false"
        self.is_av_setup_for_unk = "true"
        self.profile_db_name = "profiles.db"

    # synchronize the preferences the backing store file
    #
    def synchronize_prefs(self):
        self.persist_prefs(do_write=False)
        self.prefs.read(self.bs_file)

        self.path_dcs = self.prefs["PREFERENCES"]["path_dcs"]
        self.path_tesseract = self.prefs["PREFERENCES"]["path_tesseract"]
        self.path_mission = self.prefs["PREFERENCES"]["path_mission"]
        self.dcs_btn_rel_delay_short = self.prefs["PREFERENCES"]["dcs_btn_rel_delay_short"]
        self.dcs_btn_rel_delay_medium = self.prefs["PREFERENCES"]["dcs_btn_rel_delay_medium"]
        self.hotkey_capture = self.prefs["PREFERENCES"]["hotkey_capture"]
        self.hotkey_capture_mode = self.prefs["PREFERENCES"]["hotkey_capture_mode"]
        self.hotkey_enter_profile = self.prefs["PREFERENCES"]["hotkey_enter_profile"]
        self.hotkey_enter_mission = self.prefs["PREFERENCES"]["hotkey_enter_mission"]
        self.hotkey_dgft_dogfight = self.prefs["PREFERENCES"]["hotkey_dgft_dogfight"]
        self.hotkey_dgft_center = self.prefs["PREFERENCES"]["hotkey_dgft_center"]
        self.airframe_default = self.prefs["PREFERENCES"]["airframe_default"]
        self.av_setup_default = self.prefs["PREFERENCES"]["av_setup_default"]
        self.callsign_default = self.prefs["PREFERENCES"]["callsign_default"]
        self.is_auto_upd_check = self.prefs["PREFERENCES"]["is_auto_upd_check"]
        self.is_tesseract_debug = self.prefs["PREFERENCES"]["is_tesseract_debug"]
        self.is_av_setup_for_unk = self.prefs["PREFERENCES"]["is_av_setup_for_unk"]
        self.profile_db_name = self.prefs["PREFERENCES"]["profile_db_name"]

    # persist the preferences to the backing store file
    #
    def persist_prefs(self, do_write=True):
        self.prefs["PREFERENCES"]["path_dcs"] = self.path_dcs
        self.prefs["PREFERENCES"]["path_tesseract"] = self.path_tesseract
        self.prefs["PREFERENCES"]["path_mission"] = self.path_mission
        self.prefs["PREFERENCES"]["dcs_btn_rel_delay_short"] = self.dcs_btn_rel_delay_short
        self.prefs["PREFERENCES"]["dcs_btn_rel_delay_medium"] = self.dcs_btn_rel_delay_medium
        self.prefs["PREFERENCES"]["hotkey_capture"] = self.hotkey_capture
        self.prefs["PREFERENCES"]["hotkey_capture_mode"] = self.hotkey_capture_mode
        self.prefs["PREFERENCES"]["hotkey_enter_profile"] = self.hotkey_enter_profile
        self.prefs["PREFERENCES"]["hotkey_enter_mission"] = self.hotkey_enter_mission
        self.prefs["PREFERENCES"]["hotkey_dgft_dogfight"] = self.hotkey_dgft_dogfight
        self.prefs["PREFERENCES"]["hotkey_dgft_center"] = self.hotkey_dgft_center
        self.prefs["PREFERENCES"]["airframe_default"] = self.airframe_default
        self.prefs["PREFERENCES"]["av_setup_default"] = self.av_setup_default
        self.prefs["PREFERENCES"]["callsign_default"] = self.callsign_default
        self.prefs["PREFERENCES"]["is_auto_upd_check"] = self.is_auto_upd_check
        self.prefs["PREFERENCES"]["is_tesseract_debug"] = self.is_tesseract_debug
        self.prefs["PREFERENCES"]["is_av_setup_for_unk"] = self.is_av_setup_for_unk
        self.prefs["PREFERENCES"]["profile_db_name"] = self.profile_db_name

        if do_write:
            with open(self.bs_file, "w+") as f:
                self.prefs.write(f)
