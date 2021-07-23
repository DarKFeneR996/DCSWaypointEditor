'''
*
*  prefs_gui.py: DCS Waypoint Editor preferences GUI
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
import PySimpleGUI as PyGUI
import requests

from src.comp_dcs_bios import dcs_bios_vers_install, dcs_bios_vers_latest, dcs_bios_is_current
from src.comp_dcs_bios import dcs_bios_install
from src.db_models import AvionicsSetupModel
from src.gui_util import airframe_list, airframe_ui_text_to_type, airframe_type_to_ui_text
from src.logger import get_logger


class PreferencesGUI:
    def __init__(self, prefs):
        self.prefs = prefs

        self.logger = get_logger(__name__)
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
            self.prefs.av_setup_default = values.get('ux_av_setup_default')
            if self.prefs.av_setup_default not in AvionicsSetupModel.list_all_names():
                raise Exception("Unknown avionics setup")
        except:
            self.prefs.av_setup_default = "DCS Default"
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
        try:
            self.prefs.hotkey_dgft_dogfight = values.get('ux_hotkey_dgft_dogfight')
        except:
            errors = errors + ", DGFT dogfight hotkey"
        try:
            self.prefs.hotkey_dgft_center = values.get('ux_hotkey_dgft_center')
        except:
            errors = errors + ", DGFT center hotkey"
        if len(errors) > 0:
            PyGUI.Popup(f"Invalid value(s) for {errors}, changes ignored.", title="Error")
        self.prefs.is_auto_upd_check = values.get('ux_is_auto_upd_check')
        self.prefs.is_tesseract_debug = values.get('ux_is_tesseract_debug')
        self.prefs.persist_prefs()

    # build the ui for the preferences window.
    #
    def create_gui(self):
        is_auto_upd_check = self.prefs.is_auto_upd_check_bool
        is_tesseract_debug = self.prefs.is_tesseract_debug_bool
        dcs_bios_ver = dcs_bios_vers_install(self.prefs.path_dcs)
        as_tmplts = [ "DCS Default" ] + AvionicsSetupModel.list_all_names()

        if self.prefs.av_setup_default not in as_tmplts:
            self.prefs.av_setup_default = "DCS Default"


        layout_paths = [
            [PyGUI.Text("DCS saved games directory:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.path_dcs, key='ux_path_dcs', enable_events=True),
             PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FOLDER, target='ux_path_dcs')],

            [PyGUI.Text("Tesseract executable:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.path_tesseract, key='ux_path_tesseract'),
             PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE, target='ux_path_tesseract')],
 
            [PyGUI.Text("Mission file:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.path_mission, key='ux_path_mission'),
             PyGUI.Button("Browse...", button_type=PyGUI.BUTTON_TYPE_BROWSE_FILE, target='ux_path_mission')],
        ]

        layout_hotkeys = [
            [PyGUI.Text("DCS F10 map capture:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_capture, key='ux_hotkey_capture', pad=((5,80),0))],

            [PyGUI.Text("Toggle capture mode:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_capture_mode, key='ux_hotkey_capture_mode')],

            [PyGUI.Text("Load current profile into jet:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_enter_profile, key='ux_hotkey_enter_profile')],

            [PyGUI.Text("Load mission file into jet:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_enter_mission, key='ux_hotkey_enter_mission')],

            [PyGUI.Text("", font="Helvetica 6", pad=(0,0))],

            [PyGUI.Text("F-16 HOTAS DGFT dogfight:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_dgft_dogfight, key='ux_hotkey_dgft_dogfight')],

            [PyGUI.Text("F-16 HOTAS DGFT center:", (21,1), justification="right"),
             PyGUI.Input(self.prefs.hotkey_dgft_center, key='ux_hotkey_dgft_center')]
        ]

        layout_dcsbios = [
            [PyGUI.Text("Button press (short):", (21,1), justification="right"),
             PyGUI.Input(self.prefs.dcs_btn_rel_delay_short, key='ux_dcs_btn_rel_delay_short'),
             PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("Button press (medium):", (21,1), justification="right"),
             PyGUI.Input(self.prefs.dcs_btn_rel_delay_medium, key='ux_dcs_btn_rel_delay_medium'),
             PyGUI.Text("(seconds)", justification="left", pad=((0,14),0))],

            [PyGUI.Text("DCS-BIOS:", (21,1), justification="right"),
             PyGUI.Text("Status", key='ux_dcs_bios_stat', size=(19,1)),
             PyGUI.Button("Install", key='ux_install', size=(18,1),
                          disabled=(dcs_bios_ver is not None))]
        ]

        layout_misc = [
            [PyGUI.Text("Default airframe:", (21,1), justification="right"),
             PyGUI.Combo(values=airframe_list(),
                         default_value=airframe_type_to_ui_text(self.prefs.airframe_default),
                         key='ux_airframe_default', readonly=True, enable_events=True,
                         size=(30,1), pad=((5,172),0))],

            [PyGUI.Text("Default avionics setup:", (21,1), key='ux_av_setup_txt', justification="right"),
             PyGUI.Combo(values=as_tmplts, default_value=self.prefs.av_setup_default,
                         key='ux_av_setup_default', readonly=True,
                         size=(30,1), pad=((5,172),0))],

            [PyGUI.Text("Check for updates:", (21,1), justification="right"),
             PyGUI.Checkbox(text="", default=is_auto_upd_check, key='ux_is_auto_upd_check')],

            [PyGUI.Text("Log raw OCR output:", (21,1), justification="right"),
             PyGUI.Checkbox(text="", default=is_tesseract_debug, key='ux_is_tesseract_debug')]
        ]

        return PyGUI.Window("Preferences",
                            [[PyGUI.Frame("Paths & Files", layout_paths)],
                             [PyGUI.Frame("DCS/DCSWE Interaction Hot Keys", layout_hotkeys)],
                             [PyGUI.Frame("DCS BIOS Parameters", layout_dcsbios)],
                             [PyGUI.Frame("Miscellaneous", layout_misc)],
                             [PyGUI.Button("OK", key='ux_ok', size=(8,1), pad=((264,0),16))]],
                            modal=True, disable_close=True, finalize=True)

    # update gui for changes to the dcs path
    #
    def update_gui_for_dcs_path(self):
        db_ver = dcs_bios_vers_install(self.prefs.path_dcs)
        if db_ver is None:
            db_ver_latest = dcs_bios_vers_latest()
            self.window['ux_dcs_bios_stat'].update(value="Not Detected")
            self.window['ux_install'].update(text=f"Install v{db_ver_latest}", disabled=False)
        else:
            self.window['ux_dcs_bios_stat'].update(value=f"Version {db_ver} Installed")
            if dcs_bios_is_current(self.prefs.path_dcs):
                self.window['ux_install'].update(text=f"Install v{dcs_bios_vers_latest()}",
                                                 disabled=True)
            else:
                self.window['ux_install'].update(text=f"Update to v{dcs_bios_vers_latest()}",
                                                 disabled=False)

    # update gui for changes to the default airframe
    #
    def update_gui_for_airframe(self):
        if airframe_ui_text_to_type(self.values['ux_airframe_default']) == "viper":
            self.window['ux_av_setup_default'].update(disabled=False, readonly=True)
            self.window['ux_av_setup_txt'].update(text_color="#ffffff")
        else:
            self.window['ux_av_setup_default'].update(value="DCS Default", disabled=True)
            self.window['ux_av_setup_txt'].update(text_color="#b8b8b8")

    # run the gui for the preferences window.
    #
    def run(self):
        is_accepted = True

        event, self.values = self.window.read(timeout=0)

        self.update_gui_for_dcs_path()
        self.update_gui_for_airframe()

        while True:
            event, self.values = self.window.Read()
            self.logger.debug(f"Prefs Event: {event}")
            self.logger.debug(f"Prefs Values: {self.values}")

            path_dcs = self.values['ux_path_dcs']
            if path_dcs is not None and not path_dcs.endswith("\\") and not path_dcs.endswith("/"):
                path_dcs = path_dcs + "\\"

            if event == 'ux_ok':
                if not os.path.exists(self.values['ux_path_dcs']):
                    PyGUI.Popup("A valid path to the saved games tree for your DCS installation is required.",
                                title="Error")
                    continue
                else:
                    if not dcs_bios_vers_install(path_dcs):
                        PyGUI.Popup("DCS-BIOS not detected. Some functionality will not be available.",
                                    title="Note")
                    self.prefs_persist(self.values)
                    break

            elif event == 'ux_install':
                try:
                    self.logger.info("Installing DCS BIOS...")
                    dcs_bios_install(path_dcs)
                except (FileExistsError, FileNotFoundError, requests.HTTPError) as e:
                    self.logger.error("DCS-BIOS failed to install", exc_info=True)
                    PyGUI.Popup(f"DCS-BIOS failed to install:\n{e}", title="Error")
                self.update_gui_for_dcs_path()
    
            elif event == 'ux_path_dcs':
                self.update_gui_for_dcs_path()
            
            elif event == 'ux_airframe_default':
                self.update_gui_for_airframe()

        self.close()
        
        return is_accepted

    def close(self):
        self.window.Close()
