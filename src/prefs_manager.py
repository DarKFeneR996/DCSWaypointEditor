from configparser import ConfigParser
from pathlib import Path
from src.gui_util import airframe_list, airframe_type_to_ui_text
import os


# preferences object to abstract preferences storage. preference values are always strings.
#
class PrefsManager:
    def __init__(self, file="settings.ini"):
        self.prefs = ConfigParser()
        self.bs_file = file

        self.path_dcs = f"{str(Path.home())}\\Saved Games\\DCS.openbeta\\"
        self.path_tesseract = f"{os.environ['PROGRAMW6432']}\\Tesseract-OCR\\tesseract.exe"
        self.path_mission = f"{str(Path.home())}\\Desktop\\cf_mission.xml"
        self.dcs_grace_period = "5"
        self.dcs_btn_rel_delay_short = "0.2"
        self.dcs_btn_rel_delay_medium = "0.5"
        self.hotkey_capture = "ctrl+t"
        self.hotkey_capture_mode = "ctrl+shift+t"
        self.hotkey_enter_profile = "ctrl+alt+t"
        self.hotkey_enter_mission = ""
        self.airframe_default = airframe_list()[0]
        self.is_auto_upd_check = "true"
        self.is_tesseract_debug = "false"
        self.profile_db_name = "profiles.db"

        try:
            open(self.bs_file, "r").close()
            self.synchronize_prefs()
            self.is_new_prefs_file = False
        except FileNotFoundError:
            self.prefs.add_section("PREFERENCES")
            self.reset_prefs()
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
    def dcs_grace_period(self):
        return self._dcs_grace_period

    @dcs_grace_period.setter
    def dcs_grace_period(self, value):
        if float(value) < 0.0:
            raise ValueError("Grace period must be a positive number")
        self._dcs_grace_period = value

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
    def airframe_default(self):
        return self._airframe_default
    
    @airframe_default.setter
    def airframe_default(self, value):
        if airframe_type_to_ui_text(value) is None:
            raise ValueError("Unknown airframe type")
        self._airframe_default = value

    @property
    def is_auto_upd_check(self):
        return self._is_auto_upd_check

    @is_auto_upd_check.setter
    def is_auto_upd_check(self, value):
        self._is_auto_upd_check = value

    @property
    def is_tesseract_debug(self):
        return self._is_tesseract_debug

    @is_tesseract_debug.setter
    def is_tesseract_debug(self, value):
        self._is_tesseract_debug = value

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
            tokens = hotkey.replace(" ", "").split("+")
            if len(tokens) >= 1:
                key = tokens.pop()
                if key is None or len(key) != 1:
                    return False
                for token in tokens:
                    if token.lower() not in ("ctrl", "alt", "shift"):
                        return False
            else:
                return False
        return True

    # reset the preferences to their default values, must persist via persist_prefs to save.
    #
    def reset_prefs(self):
        self.path_dcs = f"{str(Path.home())}\\Saved Games\\DCS.openbeta\\"
        self.path_tesseract = f"{os.environ['PROGRAMW6432']}\\Tesseract-OCR\\tesseract.exe"
        self.path_mission = f"{str(Path.home())}\\Desktop\\cf_mission.xml"
        self.dcs_grace_period = "5"
        self.dcs_btn_rel_delay_short = "0.2"
        self.dcs_btn_rel_delay_medium = "0.5"
        self.hotkey_capture = "ctrl+t"
        self.hotkey_capture_mode = "ctrl+shift+t"
        self.hotkey_enter_profile = "ctrl+alt+t"
        self.hotkey_enter_mission = "ctrl+alt+shift+t"
        self.airframe_default = airframe_list()[0]
        self.is_auto_upd_check = "true"
        self.is_tesseract_debug = "false"
        self.profile_db_name = "profiles.db"

    # synchronize the preferences the backing store file
    #
    def synchronize_prefs(self):
        self.prefs.read(self.bs_file)

        self.path_dcs = self.prefs["PREFERENCES"]["path_dcs"]
        self.path_tesseract = self.prefs["PREFERENCES"]["path_tesseract"]
        self.path_mission = self.prefs["PREFERENCES"]["path_mission"]
        self.dcs_grace_period = self.prefs["PREFERENCES"]["dcs_grace_period"]
        self.dcs_btn_rel_delay_short = self.prefs["PREFERENCES"]["dcs_btn_rel_delay_short"]
        self.dcs_btn_rel_delay_medium = self.prefs["PREFERENCES"]["dcs_btn_rel_delay_medium"]
        self.hotkey_capture = self.prefs["PREFERENCES"]["hotkey_capture"]
        self.hotkey_capture_mode = self.prefs["PREFERENCES"]["hotkey_capture_mode"]
        self.hotkey_enter_profile = self.prefs["PREFERENCES"]["hotkey_enter_profile"]
        self.hotkey_enter_mission = self.prefs["PREFERENCES"]["hotkey_enter_mission"]
        self.airframe_default = self.prefs["PREFERENCES"]["airframe_default"]
        self.is_auto_upd_check = self.prefs["PREFERENCES"]["is_auto_upd_check"]
        self.is_tesseract_debug = self.prefs["PREFERENCES"]["is_tesseract_debug"]
        self.profile_db_name = self.prefs["PREFERENCES"]["profile_db_name"]

    # persist the preferences to the backing store file
    #
    def persist_prefs(self):
        self.prefs["PREFERENCES"]["path_dcs"] = self.path_dcs
        self.prefs["PREFERENCES"]["path_tesseract"] = self.path_tesseract
        self.prefs["PREFERENCES"]["path_mission"] = self.path_mission
        self.prefs["PREFERENCES"]["dcs_grace_period"] = self.dcs_grace_period
        self.prefs["PREFERENCES"]["dcs_btn_rel_delay_short"] = self.dcs_btn_rel_delay_short
        self.prefs["PREFERENCES"]["dcs_btn_rel_delay_medium"] = self.dcs_btn_rel_delay_medium
        self.prefs["PREFERENCES"]["hotkey_capture"] = self.hotkey_capture
        self.prefs["PREFERENCES"]["hotkey_capture_mode"] = self.hotkey_capture_mode
        self.prefs["PREFERENCES"]["hotkey_enter_profile"] = self.hotkey_enter_profile
        self.prefs["PREFERENCES"]["hotkey_enter_mission"] = self.hotkey_enter_mission
        self.prefs["PREFERENCES"]["airframe_default"] = self.airframe_default
        self.prefs["PREFERENCES"]["is_auto_upd_check"] = self.is_auto_upd_check
        self.prefs["PREFERENCES"]["is_tesseract_debug"] = self.is_tesseract_debug
        self.prefs["PREFERENCES"]["profile_db_name"] = self.profile_db_name

        with open(self.bs_file, "w+") as f:
            self.prefs.write(f)
