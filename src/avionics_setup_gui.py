'''
*
*  avionics_setup.py: DCS Waypoint Editor Avionics Setup template editor GUI 
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

import copy
import PySimpleGUI as PyGUI

from src.db_models import AvionicsSetupModel
from src.gui_util import airframe_type_to_ui_text
from src.logger import get_logger


# Maps UI text : MFD OSB button (from format selection screen) for MFD formats.
#
mfd_format_map = { ""     : 1,
                   "DTE"  : 8,
                   "FCR"  : 20,
                   "FLCS" : 10,
                   "HSD"  : 7,
                   "SMS"  : 6,
                   "TEST" : 9,
                   "TGP"  : 19,
                   "WPN"  : 18
}

# Maps UI MFD format key base onto default MFD format setups (as of DCS v2.7.4.9632).
#
mfd_default_setup_map = { 'ux_nav' : [ 20, 9, 8, 6, 7, 1 ],     # L: FCR, TEST, DTE; R: SMS, HSD, -
                          'ux_air' : [ 20, 10, 9, 6, 7, 1 ],    # L: FCR, FLCS, TEST; R: SMS, HSD -
                          'ux_gnd' : [ 20, 10, 9, 6, 7, 1 ],    # L: FCR, FLCS, TEST; R: SMS, HSD -
                          'ux_dog' : [ 20, 1, 1, 6, 1, 1 ]      # L: FCR, -, -; R: SMS, -, -
}

# Suffixes for MFD format selection combo boxes in the UI. These appear in the order the
# corresponding formats appear on the MFDs when reading from left to right.
#
mfd_key_suffixes = [ '_l14', '_l13', '_l12', '_r14', '_r13', '_r12' ]


class AvionicsSetupGUI:

    def __init__(self, airframe=None, cur_av_setup=None):
        self.logger = get_logger(__name__)
        self.dbase_setup = None
        self.values = None
        self.window = self.create_gui(airframe)
        self.cur_av_setup = cur_av_setup

        if self.cur_av_setup is not None:
            self.dbase_setup = AvionicsSetupModel.get(AvionicsSetupModel.name == self.cur_av_setup)
        else:
            self.cur_av_setup = "DCS Default"

        self.is_dirty = False

    def is_setup_default(self):
        if self.values.get('ux_tmplt_select') == "DCS Default":
            return True
        return False

    def create_gui(self, airframe="viper"):
        mfd_formats = list(mfd_format_map.keys())
        airframe_ui = airframe_type_to_ui_text(airframe)

        layout_nav = [
            [PyGUI.Checkbox("Reconfigure MFD formats:", key='ux_nav_ckbx', enable_events=True,
                            size=(19,1)),
             PyGUI.Combo(values=mfd_formats, default_value="FCR", key='ux_nav_l14',
                         enable_events=True, size=(8,1), pad=((0,6),0)),
             PyGUI.Combo(values=mfd_formats, default_value="TEST", key='ux_nav_l13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="DTE", key='ux_nav_l12',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.VerticalSeparator(pad=(12,0)),
             PyGUI.Combo(values=mfd_formats, default_value="SMS", key='ux_nav_r14',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="HSD", key='ux_nav_r13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_nav_r12',
                         enable_events=True, size=(8,1), pad=(6,0))],

            [PyGUI.Text("L OSB 14", key='ux_nav_txt_l14', size=(8,1), pad=((200,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 13", key='ux_nav_txt_l13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 12", key='ux_nav_txt_l12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 14", key='ux_nav_txt_r14', size=(8,1), pad=((58,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 13", key='ux_nav_txt_r13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 12", key='ux_nav_txt_r12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8")]
        ]

        layout_air = [
            [PyGUI.Checkbox("Reconfigure MFD formats:", key='ux_air_ckbx', enable_events=True,
                            size=(19,1)),
             PyGUI.Combo(values=mfd_formats, default_value="FCR", key='ux_air_l14',
                         enable_events=True, size=(8,1), pad=((0,6),0)),
             PyGUI.Combo(values=mfd_formats, default_value="FLCS", key='ux_air_l13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="TEST", key='ux_air_l12',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.VerticalSeparator(pad=(12,0)),
             PyGUI.Combo(values=mfd_formats, default_value="SMS", key='ux_air_r14',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="HSD", key='ux_air_r13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_air_r12',
                         enable_events=True, size=(8,1), pad=(6,0))],

            [PyGUI.Text("L OSB 14", key='ux_air_txt_l14', size=(8,1), pad=((200,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 13", key='ux_air_txt_l13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 12", key='ux_air_txt_l12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 14", key='ux_air_txt_r14', size=(8,1), pad=((58,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 13", key='ux_air_txt_r13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 12", key='ux_air_txt_r12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8")]
        ]

        layout_gnd = [
            [PyGUI.Checkbox("Reconfigure MFD formats:", key='ux_gnd_ckbx', enable_events=True,
                            size=(19,1)),
             PyGUI.Combo(values=mfd_formats, default_value="FCR", key='ux_gnd_l14',
                         enable_events=True, size=(8,1), pad=((0,6),0)),
             PyGUI.Combo(values=mfd_formats, default_value="FLCS", key='ux_gnd_l13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="TEST", key='ux_gnd_l12',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.VerticalSeparator(pad=(12,0)),
             PyGUI.Combo(values=mfd_formats, default_value="SMS", key='ux_gnd_r14',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="HSD", key='ux_gnd_r13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_gnd_r12',
                         enable_events=True, size=(8,1), pad=(6,0))],

            [PyGUI.Text("L OSB 14", key='ux_gnd_txt_l14', size=(8,1), pad=((200,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 13", key='ux_gnd_txt_l13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 12", key='ux_gnd_txt_l12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 14", key='ux_gnd_txt_r14', size=(8,1), pad=((58,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 13", key='ux_gnd_txt_r13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 12", key='ux_gnd_txt_r12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8")]
        ]

        layout_dog = [
            [PyGUI.Checkbox("Reconfigure MFD formats:", key='ux_dog_ckbx', enable_events=True,
                            size=(19,1)),
             PyGUI.Combo(values=mfd_formats, default_value="FCR", key='ux_dog_l14',
                         enable_events=True, size=(8,1), pad=((0,6),0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_dog_l13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_dog_l12',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.VerticalSeparator(pad=(12,0)),
             PyGUI.Combo(values=mfd_formats, default_value="SMS", key='ux_dog_r14',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_dog_r13',
                         enable_events=True, size=(8,1), pad=(6,0)),
             PyGUI.Combo(values=mfd_formats, default_value="", key='ux_dog_r12',
                         enable_events=True, size=(8,1), pad=(6,0))],

            [PyGUI.Text("L OSB 14", key='ux_dog_txt_l14', size=(8,1), pad=((200,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 13", key='ux_dog_txt_l13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("L OSB 12", key='ux_dog_txt_l12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 14", key='ux_dog_txt_r14', size=(8,1), pad=((58,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 13", key='ux_dog_txt_r13', size=(8,1), pad=((34,0),(0,8)),
                        font="Helvetica 8"),
             PyGUI.Text("R OSB 12", key='ux_dog_txt_r12', size=(8,1), pad=((32,0),(0,8)),
                        font="Helvetica 8")]
        ]

        layout_tacan = [
            [PyGUI.Checkbox("Setup TACAN yardstick at:", key='ux_tacan_ckbx', enable_events=True,
                            size=(19,1), pad=(6,(6,8))),
             PyGUI.Input(default_text="1", key='ux_tacan_chan', enable_events=True,
                         size=(4,1), pad=(6,(6,8))),
             PyGUI.Combo(values=[ "X", "Y" ], default_value="X", key='ux_tacan_xy_select',
                         readonly=True, enable_events=True, size=(2,1), pad=(6,(6,8))),
             PyGUI.Text("for role", key='ux_tacan_role', pad=(6,(6,8))),
             PyGUI.Combo(values=[ "Flight Lead", "Wingman" ], default_value="Flight Lead",
                         key='ux_tacan_lw_select', enable_events=True, readonly=True,
                         size=(10,1), pad=(6,(6,8))),
             PyGUI.Text("", key='ux_tacan_info',
                        size=(34,1), pad=(6,(6,8)))]
        ]

        layout_mgmt = [
            [PyGUI.Text("Avionics setup name:"),
             PyGUI.Combo(values=["DCS Default"], key='ux_tmplt_select', readonly=True,
                         enable_events=True, size=(30,1)),
             PyGUI.Button("Save...", key='ux_tmplt_save', size=(10,1)),
             PyGUI.Button("Delete...", key='ux_tmplt_delete', size=(10,1)),
             PyGUI.VerticalSeparator(pad=(22,12)),
             PyGUI.Button("Done", key='ux_done', size=(10,1), pad=(6,12))]
        ]

        return PyGUI.Window(f"{airframe_ui} Avionics Setup",
                            [[PyGUI.Frame("NAV: Navigation Master Mode", layout_nav)],
                             [PyGUI.Frame("AG: Air-to-Ground Master Mode", layout_gnd)],
                             [PyGUI.Frame("AA: Air-to-Air Master Mode", layout_air)],
                             [PyGUI.Frame("DGFT: Dogfight Master Mode", layout_dog)],
                             [PyGUI.Frame("TACAN Yardstick", layout_tacan)],
                             [layout_mgmt]],
                            modal=True, disable_close=True, finalize=True)

    # update the gui for the enable state of a MFD master mode
    #
    def update_gui_enable_mfd_row(self, key_base):
        if self.values[f"{key_base}_ckbx"]:
            label_color = "#ffffff"
            for key_suffix in mfd_key_suffixes:
                self.window[f"{key_base}{key_suffix}"].update(disabled=False)
        else:
            label_color = "#b8b8b8"
            self.window[f"{key_base}_l14"].update(value="FCR", disabled=True)
            if key_base == 'ux_nav':
                self.window[f"{key_base}_l13"].update(value="TEST", disabled=True)
                self.window[f"{key_base}_l12"].update(value="DTE", disabled=True)
            elif key_base == 'ux_gnd' or key_base == 'ux_air':
                self.window[f"{key_base}_l13"].update(value="FLCS", disabled=True)
                self.window[f"{key_base}_l12"].update(value="TEST", disabled=True)
            else:
                self.window[f"{key_base}_l13"].update(value="", disabled=True)
                self.window[f"{key_base}_l12"].update(value="", disabled=True)
            self.window[f"{key_base}_r14"].update(value="SMS", disabled=True)
            if key_base == 'ux_dog':
                self.window[f"{key_base}_r13"].update(value="", disabled=True)
            else:
                self.window[f"{key_base}_r13"].update(value="HSD", disabled=True)
            self.window[f"{key_base}_r12"].update(value="", disabled=True)
        for key_suffix in mfd_key_suffixes:
            self.window[f"{key_base}_txt{key_suffix}"].update(text_color=label_color)

    # update the gui to ensure a format appears only once in a master mode
    #
    def update_gui_unique_mfd_row(self, key, key_base):
        value = self.values[key]
        for key_suffix in mfd_key_suffixes:
            row_key = f"{key_base}{key_suffix}"
            if row_key != key and self.values[row_key] == value:
                self.window[row_key].update(value="")

    # update the gui for the enable state of a MFD master mode
    #
    def update_gui_enable_tacan_row(self):
        if self.values[f"ux_tacan_ckbx"]:
            label_color = "#ffffff"
            input_color = "#000000"
            chan = self.values['ux_tacan_chan']
            if self.values['ux_tacan_lw_select'] == "Wingman":
                chan = int(chan) + 63
            xy = self.values['ux_tacan_xy_select']
            summary_txt = f" (setup will program TACAN to {chan}{xy} A/A)"
            self.window['ux_tacan_chan'].update(disabled=False, text_color=input_color)
            self.window['ux_tacan_xy_select'].update(disabled=False, readonly=True)
            self.window['ux_tacan_lw_select'].update(disabled=False, readonly=True)
        else:
            label_color = "#b8b8b8"
            input_color = "#b8b8b8"
            summary_txt = ""
            self.window['ux_tacan_chan'].update(disabled=True, text_color=input_color)
            self.window['ux_tacan_xy_select'].update(disabled=True)
            self.window['ux_tacan_lw_select'].update(disabled=True)
        self.window['ux_tacan_role'].update(text_color=label_color)
        self.window['ux_tacan_info'].update(summary_txt)

    # update the gui state based on a change to the template list
    #
    def update_gui_template_list(self):
        tmplts = [ "DCS Default" ] + AvionicsSetupModel.list_all_names()
        if self.dbase_setup is None:
            cur_av_setup = "DCS Default"
        else:
            cur_av_setup = self.dbase_setup.name
        self.window['ux_tmplt_select'].update(values=tmplts, set_to_index=tmplts.index(cur_av_setup))
        self.values['ux_tmplt_select'] = cur_av_setup
        self.update_gui_control_enable_state()

    # update the gui button state based on current setup
    #
    def update_gui_control_enable_state(self):
        if (not self.values['ux_nav_ckbx'] and
            not self.values['ux_air_ckbx'] and
            not self.values['ux_gnd_ckbx'] and
            not self.values['ux_dog_ckbx'] and
            not self.values['ux_tacan_ckbx']):
            self.dbase_setup = None
            self.is_dirty = False

        if self.is_dirty:
            save_disabled = False
        else:
            save_disabled = True
        if self.is_setup_default():
            self.window['ux_tmplt_save'].update(text="Save As...", disabled=save_disabled)
            self.window['ux_tmplt_delete'].update(disabled=True)
        else:
            self.window['ux_tmplt_save'].update(text="Update", disabled=save_disabled)
            self.window['ux_tmplt_delete'].update(disabled=False)


    # get/set mfd format row ui state
    #
    def get_gui_mfd_row(self, key_base):
        if self.values[f"{key_base}_ckbx"] == False:
            config = None
        else:
            osb_list = []
            for key_suffix in mfd_key_suffixes:
                osb_list.append(mfd_format_map[self.values[f"{key_base}{key_suffix}"]])
            config = ','.join([str(item) for item in osb_list])
        return config
    
    def set_gui_mfd_row(self, key_base, value):
        if value is None:
            self.window[f"{key_base}_ckbx"].update(value=False)
            osb_list = copy.copy(mfd_default_setup_map[key_base])
        else:
            self.window[f"{key_base}_ckbx"].update(value=True)
            osb_list = [ int(osb) for osb in value.split(",") ]
        for key_suffix in mfd_key_suffixes:
            osb = osb_list.pop(0)
            hits = [k for k,v in mfd_format_map.items() if v == osb]
            if (len(hits) == 0):
                hits = [""]
            self.window[f"{key_base}{key_suffix}"].update(value=hits[0])

    # synchronize TACAN setup UI and database
    #
    def copy_tacan_dbase_to_ui(self):
        if self.dbase_setup is not None:
            if self.dbase_setup.tacan_yard is None:
                self.window['ux_tacan_ckbx'].update(value=False)
                self.window['ux_tacan_chan'].update("1")
            else:
                fields = [ str(field) for field in self.dbase_setup.tacan_yard.split(",") ]
                if fields[2] == "L":
                    role_index = 0
                else:
                    role_index = 1
                self.window['ux_tacan_ckbx'].update(value=True)
                self.window['ux_tacan_chan'].update(fields[0])
                self.window['ux_tacan_xy_select'].update(value=fields[1])
                self.window['ux_tacan_lw_select'].update(set_to_index=role_index)
        else:
            self.window['ux_tacan_ckbx'].update(value=False)
            self.window['ux_tacan_chan'].update("1")
            self.window['ux_tacan_xy_select'].update(value="X")
            self.window['ux_tacan_lw_select'].update(value="Flight Lead")
        self.is_dirty = False

    def copy_tacan_ui_to_dbase(self, db_save=True):
        if self.dbase_setup is not None:
            if self.values['ux_tacan_ckbx'] == False:
                tacan_yard = None
            else:
                chan = int(self.values['ux_tacan_chan'])
                xy = self.values['ux_tacan_xy_select']
                if self.values['ux_tacan_lw_select'] == "Flight Lead":
                    lw = "L"
                else:
                    lw = "W"
                tacan_yard = f"{chan},{xy},{lw}"
            self.dbase_setup.tacan_yard = tacan_yard
            if db_save:
                try:
                    self.dbase_setup.save()
                except:
                    PyGUI.PopupError("Unable to save TACAN yardstick information to database?")
            self.is_dirty = False
    
    # synchronize F-16 MFD setup UI and database
    #
    def copy_f16_mfd_dbase_to_ui(self):
        if self.dbase_setup is not None:
            self.set_gui_mfd_row('ux_nav', self.dbase_setup.f16_mfd_setup_nav)
            self.set_gui_mfd_row('ux_air', self.dbase_setup.f16_mfd_setup_air)
            self.set_gui_mfd_row('ux_gnd', self.dbase_setup.f16_mfd_setup_gnd)
            self.set_gui_mfd_row('ux_dog', self.dbase_setup.f16_mfd_setup_dog)
        else:
            self.set_gui_mfd_row('ux_nav', None)
            self.set_gui_mfd_row('ux_air', None)
            self.set_gui_mfd_row('ux_gnd', None)
            self.set_gui_mfd_row('ux_dog', None)
        self.is_dirty = False
    
    def copy_f16_mfd_ui_to_dbase(self, db_save=True):
        if self.dbase_setup is not None:
            self.dbase_setup.f16_mfd_setup_nav = self.get_gui_mfd_row('ux_nav')
            self.dbase_setup.f16_mfd_setup_air = self.get_gui_mfd_row('ux_air')
            self.dbase_setup.f16_mfd_setup_gnd = self.get_gui_mfd_row('ux_gnd')
            self.dbase_setup.f16_mfd_setup_dog = self.get_gui_mfd_row('ux_dog')
            if db_save:
                try:
                    self.dbase_setup.save()
                except:
                    PyGUI.PopupError("Unable to save MFD setup information to database?")
            self.is_dirty = False


    # gui action handlers
    #
    def do_mfd_osb_ckbx(self, event):
        self.is_dirty = True
        fields = event.split("_")
        self.update_gui_enable_mfd_row(f"{fields[0]}_{fields[1]}")

    def do_mfd_osb_combo(self, event):
        self.is_dirty = True
        fields = event.split("_")
        self.update_gui_unique_mfd_row(event, f"{fields[0]}_{fields[1]}")

    def do_tacan_dirty(self, event):
        self.is_dirty = True

    def do_tacan_chan(self, event):
        if self.values[event]:
            try:
                input_as_int = int(self.values[event])
                if input_as_int < 1 or input_as_int > 63:
                    raise ValueError("Out of bounds")
                self.is_dirty = True
            except:
                PyGUI.Popup("The TACAN channel must be between 1 and 63 for use as a yardstick.",
                            title="Invalid Channel")
                self.window[event].update(self.values[event][:-1])

    def do_template_select(self, event):
        if self.is_dirty:
            action = PyGUI.PopupOKCancel(f"You have unsaved changes to the current template." +
                                            " Closing the window will discard these changes.",
                                            title="Unsaved Changes")
            if action == "Cancel":
                self.window['ux_tmplt_select'].update(value=self.cur_av_setup)
                return

        if self.is_setup_default():
            self.dbase_setup = None
        else:
            self.dbase_setup = AvionicsSetupModel.get(AvionicsSetupModel.name == self.values[event])
        self.cur_av_setup = self.values['ux_tmplt_select']
        self.copy_f16_mfd_dbase_to_ui()
        self.copy_tacan_dbase_to_ui()

    def do_template_save(self, event):
        if self.is_setup_default():
            name = PyGUI.PopupGetText("Template Name", "Saving New Template")
            if name is not None:
                try:
                    self.dbase_setup = AvionicsSetupModel.create(name=name)
                    self.copy_f16_mfd_ui_to_dbase(db_save=False)
                    self.copy_tacan_ui_to_dbase(db_save=True)
                    self.update_gui_template_list()
                except:
                    PyGUI.Popup(f"Unable to create a template named '{name}'. Is there already" +
                                 " a template with that name?", title="Error")
        else:
            self.copy_f16_mfd_ui_to_dbase(db_save=False)
            self.copy_tacan_ui_to_dbase(db_save=True)

    def do_template_delete(self, event):
        action = PyGUI.PopupOKCancel(f"Are you sure you want to delete the settings {self.cur_av_setup}?",
                                     title="Confirm Delete")
        if action == "OK":
            try:
                self.dbase_setup.delete_instance()
                self.dbase_setup = None
                self.is_dirty = False
                self.update_gui_template_list()
            except Exception as e:
                PyGUI.PopupError(f"Unable to delete the settings {self.cur_av_setup} from the database.")

    # run the gui for the preferences window.
    #
    def run(self):
        self.window.disappear()

        self.copy_f16_mfd_dbase_to_ui()
        self.copy_tacan_dbase_to_ui()

        event, self.values = self.window.read(timeout=0)

        self.update_gui_control_enable_state()
        for key_base in ['ux_nav', 'ux_gnd', 'ux_air', 'ux_dog']:
            self.update_gui_enable_mfd_row(key_base)
        self.update_gui_enable_tacan_row()
        self.update_gui_template_list()

        self.window['ux_tmplt_select'].update(value=self.cur_av_setup)

        self.window.reappear()

        handler_map = { 'ux_nav_ckbx' : self.do_mfd_osb_ckbx,
                        'ux_nav_l14' : self.do_mfd_osb_combo,
                        'ux_nav_l13' : self.do_mfd_osb_combo,
                        'ux_nav_l12' : self.do_mfd_osb_combo,
                        'ux_nav_r14' : self.do_mfd_osb_combo,
                        'ux_nav_r13' : self.do_mfd_osb_combo,
                        'ux_nav_r12' : self.do_mfd_osb_combo,
                        'ux_air_ckbx' : self.do_mfd_osb_ckbx,
                        'ux_air_l14' : self.do_mfd_osb_combo,
                        'ux_air_l13' : self.do_mfd_osb_combo,
                        'ux_air_l12' : self.do_mfd_osb_combo,
                        'ux_air_r14' : self.do_mfd_osb_combo,
                        'ux_air_r13' : self.do_mfd_osb_combo,
                        'ux_air_r12' : self.do_mfd_osb_combo,
                        'ux_gnd_ckbx' : self.do_mfd_osb_ckbx,
                        'ux_gnd_l14' : self.do_mfd_osb_combo,
                        'ux_gnd_l13' : self.do_mfd_osb_combo,
                        'ux_gnd_l12' : self.do_mfd_osb_combo,
                        'ux_gnd_r14' : self.do_mfd_osb_combo,
                        'ux_gnd_r13' : self.do_mfd_osb_combo,
                        'ux_gnd_r12' : self.do_mfd_osb_combo,
                        'ux_dog_ckbx' : self.do_mfd_osb_ckbx,
                        'ux_dog_l14' : self.do_mfd_osb_combo,
                        'ux_dog_l13' : self.do_mfd_osb_combo,
                        'ux_dog_l12' : self.do_mfd_osb_combo,
                        'ux_dog_r14' : self.do_mfd_osb_combo,
                        'ux_dog_r13' : self.do_mfd_osb_combo,
                        'ux_dog_r12' : self.do_mfd_osb_combo,
                        'ux_tacan_ckbx' : self.do_tacan_dirty,
                        'ux_tacan_chan' : self.do_tacan_chan,
                        'ux_tacan_xy_select' : self.do_tacan_dirty,
                        'ux_tacan_lw_select' : self.do_tacan_dirty,
                        'ux_tmplt_select' : self.do_template_select,
                        'ux_tmplt_save' : self.do_template_save,
                        'ux_tmplt_delete' : self.do_template_delete,
        }

        tout_val = 1000000
        while True:
            event, self.values = self.window.Read(timeout=tout_val, timeout_key='timeout')
            if event != 'timeout':
                self.logger.debug(f"MFD Event: {event}")
                self.logger.debug(f"MFD Values: {self.values}")
                tout_val = 1000000

            self.update_gui_control_enable_state()
            for key_base in ['ux_nav', 'ux_air', 'ux_gnd', 'ux_dog']:
                self.update_gui_enable_mfd_row(key_base)
            self.update_gui_enable_tacan_row()

            if event == 'ux_done':
                if self.is_dirty:
                    action = PyGUI.PopupOKCancel(f"You have unsaved changes to the current template." +
                                                  " Closing the window will discard these changes.",
                                                 title="Unsaved Changes")
                    if action == "OK":
                        break
                else:
                    break

            elif event != 'timeout':
                try:
                    (handler_map[event])(event)
                except Exception as e:
                    self.logger.debug(f"ERROR: {e}")
                tout_val = 0
        
        self.close()

    def close(self):
        self.window.close()