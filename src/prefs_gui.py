from src.dcs_bios import detect_dcs_bios, install_dcs_bios
from src.gui_util import airframe_list, airframe_ui_text_to_type, airframe_type_to_ui_text
import os
import PySimpleGUI as PyGUI
import requests


# convert a bool to a pref string
#
def bool_to_pref_str(value):
    if value == True:
        return "true"
    else:
        return "false"

# convert a bool to a pref string
#
def pref_str_to_bool(str):
    if str == "true":
        return True
    else:
        return False


class PrefsGUI:
    def __init__(self, prefs, logger):
        self.prefs = prefs
        self.logger = logger
        self.window = self.create_gui()

    # persist preferences in settings.ini based on values extracted from the prefs window.
    #
    def prefs_persist(self, values):
        self.logger.info("Persisting preferences...")
        self.prefs.path_dcs = values.get("ux_path_dcs")
        self.prefs.path_tesseract = values.get("ux_path_tesseract")
        self.prefs.path_mission = values.get("ux_path_mission")
        errors = ""
        try:
            self.prefs.airframe_default = airframe_ui_text_to_type(values.get("ux_airframe_default"))
        except:
            errors = "default airframe"
        try:
            self.prefs.dcs_grace_period = values.get("ux_dcs_grace_period")
        except:
            errors = errors + "grace period"
        try:
            self.prefs.dcs_btn_rel_delay_short = values.get("ux_dcs_btn_rel_delay_short")
        except:
            errors = errors + ", short release"
        try:
            self.prefs.dcs_btn_rel_delay_medium = values.get("ux_dcs_btn_rel_delay_medium")
        except:
            errors = errors + ", medium release"
        try:
            self.prefs.hotkey_capture = values.get("ux_hotkey_capture")
        except:
            errors = errors + ", capture hotkey"
        try:
            self.prefs.hotkey_capture_mode = values.get("ux_hotkey_capture_mode")
        except:
            errors = errors + ", capture quick hotkey"
        try:
            self.prefs.hotkey_enter_profile = values.get("ux_hotkey_enter_profile")
        except:
            errors = errors + ", enter profile hotkey"
        try:
            self.prefs.hotkey_enter_mission = values.get("ux_hotkey_enter_mission")
        except:
            errors = errors + ", enter mission hotkey"
        if len(errors) > 0:
            PyGUI.Popup(f"Invalid value for {errors}, change ignored.", title="Error")
        self.prefs.is_auto_upd_check = bool_to_pref_str(values.get("ux_is_auto_upd_check"))
        self.prefs.is_tesseract_debug = bool_to_pref_str(values.get("ux_is_tesseract_debug"))
        self.prefs.persist_prefs()

    # build the ui for the preferences window.
    #
    def create_gui(self):
        is_auto_upd_check = pref_str_to_bool(self.prefs.is_auto_upd_check)
        is_tesseract_debug = pref_str_to_bool(self.prefs.is_tesseract_debug)

        dcs_bios_detected = "Detected" if detect_dcs_bios(self.prefs.path_dcs) else "Not Detected"

        layout_paths = [
            [PyGUI.Text("DCS user directory:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.path_dcs, key="ux_path_dcs", enable_events=True),
            PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FOLDER, target="ux_path_dcs")],

            [PyGUI.Text("Tesseract executable:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.path_tesseract, key="ux_path_tesseract"),
            PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE, target="ux_path_tesseract")],

            [PyGUI.Text("CombatFlite mission XML:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.path_mission, key="ux_path_mission"),
            PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE, target="ux_path_mission")]
        ]
        layout_hotkeys = [
            [PyGUI.Text("DCS F10 map capture:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.hotkey_capture, key="ux_hotkey_capture", pad=((5,80),0))],

            [PyGUI.Text("Capture mode toggle:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.hotkey_capture_mode, key="ux_hotkey_capture_mode")],

            [PyGUI.Text("Load current profile:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.hotkey_enter_profile, key="ux_hotkey_enter_profile")],

            [PyGUI.Text("Load CF mission XML:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.hotkey_enter_mission, key="ux_hotkey_enter_mission")],

            [PyGUI.Text("Use \"ctrl\", \"alt\", \"shift\", and keyboard characters joined by \"+\" to build hot keys.")]
        ]
        layout_dcsbios = [
            [PyGUI.Text("Grace period:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.dcs_grace_period, key="ux_dcs_grace_period"),
            PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("Button release (short):", (20,1), justification="right"),
            PyGUI.Input(self.prefs.dcs_btn_rel_delay_short, key="ux_dcs_btn_rel_delay_short"),
            PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("Button release (medium):", (20,1), justification="right"),
            PyGUI.Input(self.prefs.dcs_btn_rel_delay_medium, key="ux_dcs_btn_rel_delay_medium"),
            PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("DCS-BIOS:", (20,1), justification="right"),
            PyGUI.Text(dcs_bios_detected, key="ux_dcs_bios_stat", size=(10,1)),
            PyGUI.Button("Install DCS-BIOS", key="ux_install", disabled=dcs_bios_detected == "Detected")]
        ]
        layout_misc = [
            [PyGUI.Text("Default airframe:", (20,1), justification="right"),
            PyGUI.Combo(values=airframe_list(), default_value=airframe_type_to_ui_text(self.prefs.airframe_default),
                        key="ux_airframe_default", pad=((5,277),0))],

            [PyGUI.Text("Check for updates:", (20,1), justification="right"),
            PyGUI.Checkbox(text="", default=is_auto_upd_check, key="ux_is_auto_upd_check")],

            [PyGUI.Text("Log raw OCR output:", (20,1), justification="right"),
            PyGUI.Checkbox(text="", default=is_tesseract_debug, key="ux_is_tesseract_debug")]
        ]

        return PyGUI.Window("Preferences",
                            [[PyGUI.Frame("Paths", layout_paths)],
                            [PyGUI.Frame("DCS Hot Keys", layout_hotkeys)],
                            [PyGUI.Frame("DCS BIOS Parameters", layout_dcsbios)],
                            [PyGUI.Frame("Miscellaneous", layout_misc)],
                            [PyGUI.Button("OK", key="ux_ok", size=(8,1), pad=((254,0),16),
                                        disabled=dcs_bios_detected != "Detected")]],
                            modal=True)

    # run the gui for the preferences window.
    #
    def run(self):
        self.window.finalize()

        is_accepted = True

        while True:
            event, values = self.window.Read()
            self.logger.debug(f"Prefs Event: {event}")
            self.logger.debug(f"Prefs Values: {values}")

            if event is None:
                if (self.window.Element("ux_ok").metadata == "true"):
                    PyGUI.Popup("Invalid preference value(s), changes will be ignored.", title="Error")
                is_accepted = False
                break

            dcs_path = values.get("dcs_path")
            if dcs_path is not None and not dcs_path.endswith("\\") and not dcs_path.endswith("/"):
                dcs_path = dcs_path + "\\"

            if event == "ux_ok":
                self.prefs_persist(values)
                break

            elif event == "ux_install":
                try:
                    self.logger.info("Installing DCS BIOS...")
                    install_dcs_bios(dcs_path)
                    self.window.Element("ux_install").Update(disabled=True)
                    self.window.Element("ux_ok").Update(disabled=False)
                    self.window.Element("ux_ok").metadata = "false"
                    self.window.Element("ux_dcs_bios_stat").Update(value="Installed")
                except (FileExistsError, FileNotFoundError, requests.HTTPError) as e:
                    self.window.Element("ux_dcs_bios_stat").Update(value="Install Failed")
                    self.logger.error("DCS-BIOS failed to install", exc_info=True)
                    PyGUI.Popup(f"DCS-BIOS failed to install:\n{e}", title="Error")
    
            elif event == "ux_path_dcs":
                dcs_bios_detected = detect_dcs_bios(values["ux_path_dcs"])
                if dcs_bios_detected:
                    self.window.Element("ux_install").Update(disabled=True)
                    self.window.Element("ux_ok").Update(disabled=False)
                    self.window.Element("ux_ok").metadata = "false"
                    self.window.Element("ux_dcs_bios_stat").Update(value="Detected")
                else:
                    if os.path.exists(values["ux_path_dcs"]):
                        self.window.Element("ux_install").Update(disabled=False)
                    else:
                        PyGUI.Popup("Invalid DCS path, unable to install DCS-BIOS.", title="Error")
                        self.window.Element("ux_install").Update(disabled=True)
                    self.window.Element("ux_ok").Update(disabled=True)
                    self.window.Element("ux_ok").metadata = "true"
                    self.window.Element("ux_dcs_bios_stat").Update(value="Not Detected")

        self.close()
        
        return is_accepted

    def close(self):
        self.window.Close()
