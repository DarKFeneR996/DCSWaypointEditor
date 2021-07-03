from src.dcs_bios import dcs_bios_install, dcs_bios_vers_install, dcs_bios_vers_current, dcs_bios_is_current
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
        self.values = None

        self.window = self.create_gui()

    # persist preferences in settings.ini based on values extracted from the prefs window.
    #
    def prefs_persist(self, values):
        self.logger.info("Persisting preferences...")
        self.prefs.path_dcs = values.get('ux_path_dcs')
        self.prefs.path_tesseract = values.get('ux_path_tesseract')
        self.prefs.path_mission = values.get('ux_path_mission')
        errors = ""
        try:
            self.prefs.airframe_default = airframe_ui_text_to_type(values.get('ux_airframe_default'))
        except:
            errors = "default airframe"
        try:
            self.prefs.dcs_grace_period = values.get('ux_dcs_grace_period')
        except:
            errors = errors + "grace period"
        try:
            self.prefs.dcs_btn_rel_delay_short = values.get('ux_dcs_btn_rel_delay_short')
        except:
            errors = errors + ", short release"
        try:
            self.prefs.dcs_btn_rel_delay_medium = values.get('ux_dcs_btn_rel_delay_medium')
        except:
            errors = errors + ", medium release"
        try:
            self.prefs.hotkey_capture = values.get('ux_hotkey_capture')
        except:
            errors = errors + ", capture hotkey"
        try:
            self.prefs.hotkey_capture_mode = values.get('ux_hotkey_capture_mode')
        except:
            errors = errors + ", capture quick hotkey"
        try:
            self.prefs.hotkey_enter_profile = values.get('ux_hotkey_enter_profile')
        except:
            errors = errors + ", enter profile hotkey"
        try:
            self.prefs.hotkey_enter_mission = values.get('ux_hotkey_enter_mission')
        except:
            errors = errors + ", enter mission hotkey"
        if len(errors) > 0:
            PyGUI.Popup(f"Invalid value(s) for {errors}, change ignored.", title="Error")
        self.prefs.is_auto_upd_check = bool_to_pref_str(values.get('ux_is_auto_upd_check'))
        self.prefs.is_tesseract_debug = bool_to_pref_str(values.get('ux_is_tesseract_debug'))
        self.prefs.persist_prefs()

    # build the ui for the preferences window.
    #
    def create_gui(self):
        is_auto_upd_check = pref_str_to_bool(self.prefs.is_auto_upd_check)
        is_tesseract_debug = pref_str_to_bool(self.prefs.is_tesseract_debug)
        dcs_bios_ver = dcs_bios_vers_install(self.prefs.path_dcs)

        layout_paths = [
            [PyGUI.Text("DCS user directory:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.path_dcs, key='ux_path_dcs', enable_events=True),
            PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FOLDER, target='ux_path_dcs')],

            [PyGUI.Text("Tesseract executable:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.path_tesseract, key='ux_path_tesseract'),
            PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE, target='ux_path_tesseract')],

            [PyGUI.Text("Mission file:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.path_mission, key='ux_path_mission'),
            PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE, target='ux_path_mission')],
        ]
        layout_hotkeys = [
            [PyGUI.Text("DCS F10 map capture:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.hotkey_capture, key='ux_hotkey_capture', pad=((5,80),0))],

            [PyGUI.Text("Toggle capture mode:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.hotkey_capture_mode, key='ux_hotkey_capture_mode')],

            [PyGUI.Text("Load current profile into jet:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.hotkey_enter_profile, key='ux_hotkey_enter_profile')],

            [PyGUI.Text("Load mission file into jet:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.hotkey_enter_mission, key='ux_hotkey_enter_mission')]
        ]
        layout_dcsbios = [
            [PyGUI.Text("Grace period:", (20,1), justification="right"),
            PyGUI.Input(self.prefs.dcs_grace_period, key='ux_dcs_grace_period'),
            PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("Button release (short):", (20,1), justification="right"),
            PyGUI.Input(self.prefs.dcs_btn_rel_delay_short, key='ux_dcs_btn_rel_delay_short'),
            PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("Button release (medium):", (20,1), justification="right"),
            PyGUI.Input(self.prefs.dcs_btn_rel_delay_medium, key='ux_dcs_btn_rel_delay_medium'),
            PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("DCS-BIOS:", (20,1), justification="right"),
            PyGUI.Text("Status", key='ux_dcs_bios_stat', size=(19,1)),
            PyGUI.Button("Install", key='ux_install', size=(18,1),
                         disabled=(dcs_bios_ver is not None))]
        ]
        layout_misc = [
            [PyGUI.Text("Default airframe:", (20,1), justification="right"),
            PyGUI.Combo(values=airframe_list(),
                        default_value=airframe_type_to_ui_text(self.prefs.airframe_default),
                        key='ux_airframe_default', pad=((5,277),0))],

            [PyGUI.Text("Check for updates:", (20,1), justification="right"),
            PyGUI.Checkbox(text="", default=is_auto_upd_check, key='ux_is_auto_upd_check')],

            [PyGUI.Text("Log raw OCR output:", (20,1), justification="right"),
            PyGUI.Checkbox(text="", default=is_tesseract_debug, key='ux_is_tesseract_debug')]
        ]

        return PyGUI.Window("Preferences",
                            [[PyGUI.Frame("Paths & Files", layout_paths)],
                            [PyGUI.Frame("DCS Hot Keys", layout_hotkeys)],
                            [PyGUI.Frame("DCS BIOS Parameters", layout_dcsbios)],
                            [PyGUI.Frame("Miscellaneous", layout_misc)],
                            [PyGUI.Button("OK", key='ux_ok', size=(8,1), pad=((254,0),16),
                                          disabled=(dcs_bios_ver is None))]],
                            modal=True, finalize=True)

    # update gui for changes to the dcs path
    #
    def update_gui_for_dcs_path(self):
        db_ver = dcs_bios_vers_install(self.prefs.path_dcs)
        if db_ver is None:
            db_ver_latest = dcs_bios_vers_current()
            self.window['ux_ok'].update(disabled=True)
            self.window['ux_ok'].metadata = "true"
            self.window['ux_dcs_bios_stat'].update(value="Not Detected")
            self.window['ux_install'].update(text=f"Install v{db_ver_latest}", disabled=False)
        else:
            self.window['ux_ok'].update(disabled=False)
            self.window['ux_ok'].metadata = "false"
            self.window['ux_dcs_bios_stat'].update(value=f"Version {db_ver} Installed")
            if dcs_bios_is_current(self.prefs.path_dcs):
                self.window['ux_install'].update(text=f"Install v{dcs_bios_vers_current()}",
                                                 disabled=True)
            else:
                self.window['ux_install'].update(text=f"Update to v{dcs_bios_vers_current()}",
                                                 disabled=False)

    # run the gui for the preferences window.
    #
    def run(self):
        is_accepted = True

        self.update_gui_for_dcs_path()

        while True:
            event, self.values = self.window.Read()
            self.logger.debug(f"Prefs Event: {event}")
            self.logger.debug(f"Prefs Values: {self.values}")

            if event is None:
                if (self.window['ux_ok'].metadata == "true"):
                    PyGUI.Popup("Invalid preference value(s), changes will be ignored.", title="Error")
                is_accepted = False
                break

            dcs_path = self.values['ux_path_dcs']
            if dcs_path is not None and not dcs_path.endswith("\\") and not dcs_path.endswith("/"):
                dcs_path = dcs_path + "\\"

            if event == 'ux_ok':
                self.prefs_persist(self.values)
                break

            elif event == 'ux_install':
                try:
                    self.logger.info("Installing DCS BIOS...")
                    dcs_bios_install(dcs_path)
                except (FileExistsError, FileNotFoundError, requests.HTTPError) as e:
                    self.logger.error("DCS-BIOS failed to install", exc_info=True)
                    PyGUI.Popup(f"DCS-BIOS failed to install:\n{e}", title="Error")
                self.update_gui_for_dcs_path()
    
            elif event == 'ux_path_dcs':
                self.update_gui_for_dcs_path()
                if not os.path.exists(dcs_path):
                    PyGUI.Popup("Invalid DCS path, unable to install DCS-BIOS.", title="Error")
                    self.window['ux_install'].update(disabled=True)

        self.close()
        
        return is_accepted

    def close(self):
        self.window.Close()
