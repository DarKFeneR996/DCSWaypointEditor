from logging import disable
from typing import Sequence
from src.dcs_bios import detect_dcs_bios
from src.objects import Profile, Waypoint, MSN
from src.logger import get_logger
from src.prefs_gui import PrefsGUI
from src.gui_util import airframe_list, airframe_type_to_ui_text, airframe_ui_text_to_type
from peewee import DoesNotExist
from LatLon23 import LatLon, Longitude, Latitude, string2latlon
from PIL import ImageEnhance, ImageOps
import pytesseract
import keyboard
import os
import urllib.request
import urllib.error
import webbrowser
import base64
import pyperclip
from slpp import slpp as lua
import src.pymgrs as mgrs
import PySimpleGUI as PyGUI
import zlib
from desktopmagic.screengrab_win32 import getDisplaysAsImages
import cv2
import numpy
import re
import datetime

def json_zip(j):
    j = base64.b64encode(
        zlib.compress(
            j.encode('utf-8')
        )
    ).decode('ascii')
    return j

def json_unzip(j):
    return zlib.decompress(base64.b64decode(j)).decode('utf-8')

def strike(text):
    result = '\u0336'
    for i, c in enumerate(text):
        result = result + c
        if i != len(text)-1:
            result = result + '\u0336'
    return result

def unstrike(text):
    return text.replace('\u0336', '')

def exception_gui(exc_info):
    return PyGUI.PopupOK("An exception occured and the program terminated execution:\n\n" + exc_info)

def check_version(cur_version):
    version_url = "https://raw.githubusercontent.com/51st-Vfw/DCSWaypointEditor/master/release_version.txt"
    releases_url = "https://github.com/51st-Vfw/DCSWaypointEditor/releases"

    try:
        with urllib.request.urlopen(version_url) as response:
            if response.code == 200:
                html = response.read()
            else:
                return False
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False

    new_version = html.decode("utf-8")
    if new_version != cur_version:
        message = f"A new version is available ({new_version}).\nDo you want to update from {cur_version}?"
        popup_answer = PyGUI.PopupYesNo(message, title="New Version Available")

        if popup_answer == "Yes":
            webbrowser.open(releases_url)
            return True
        else:
            return False


class DCSWyptEdGUI:
    def __init__(self, editor, software_version):
        self.logger = get_logger("gui")
        self.editor = editor
        self.software_version = software_version
        self.scaled_dcs_gui = False
        self.is_dcs_f10_enabled = False
        self.is_dcs_f10_tgt_add = False
        self.values = None
        self.selected_wp_type = "WP"

        self.load_new_profile()

        try:
            with open(f"{self.editor.prefs.path_dcs}\\Config\\options.lua", "r") as f:
                dcs_settings = lua.decode(f.read().replace("options = ", ""))
                self.scaled_dcs_gui = dcs_settings["graphics"]["scaleGui"]
            self.logger.info(f"DCS GUI scale is: {self.scaled_dcs_gui}")
        except (FileNotFoundError, ValueError, TypeError):
            self.logger.error("Failed to decode DCS settings", exc_info=True)

        self.logger.info(f"Tesseract path is: {self.editor.prefs.path_tesseract}")
        pytesseract.pytesseract.tesseract_cmd = self.editor.prefs.path_tesseract
        try:
            self.tesseract_version = pytesseract.get_tesseract_version()
        except pytesseract.pytesseract.TesseractNotFoundError:
            self.tesseract_version = None
            PyGUI.Popup("Unable to find tesseract, DCS coordinate capture will be disabled.", title="Error")
        self.logger.info(f"Tesseract version is: {self.tesseract_version}")

        self.window = self.create_gui()


    # ================ profile support


    def load_new_profile(self):
        self.profile = Profile('')
        self.profile.aircraft = self.editor.prefs.airframe_default

    def profile_names(self):
        return [profile.name for profile in Profile.list_all()]

    def profile_name_for_ui(self):
        if self.profile.profilename == "":
            return "Untitled"
        else:
            return self.profile.profilename


    # ================ waypoint support


    def find_selected_waypoint(self):
        valuestr = unstrike(self.values['ux_prof_wypt_list'][0])
        for wp in self.profile.waypoints:
            if str(wp) == valuestr:
                return wp

    def add_waypoint(self, position, elevation, name=None):
        if name is None:
            name = str()

        try:
            if self.selected_wp_type == "MSN":
                station = int(self.values.get('ux_seq_stn_select', 0))
                number = len(self.profile.stations_dict.get(station, list()))+1
                print(f"*** MSN station {station}, number {number}")
                print(f"station_dict {self.profile.stations_dict}")
                wp = MSN(position=position, elevation=int(elevation) or 0, name=name,
                         station=station, number=number)

            else:
                sequence = self.values['ux_seq_stn_select']
                if sequence == "None":
                    sequence = 0
                else:
                    sequence = int(sequence)

                if sequence and len(self.profile.get_sequence(sequence)) >= 15:
                    return False

                wp = Waypoint(position, elevation=int(elevation or 0),
                              name=name, sequence=sequence, wp_type=self.selected_wp_type,
                              number=len(self.profile.waypoints_of_type(self.selected_wp_type))+1)

                if sequence not in self.profile.sequences:
                    self.profile.sequences.append(sequence)

            self.profile.waypoints.append(wp)
            self.update_for_waypoint_list_change()
        except ValueError:
            PyGUI.Popup("Error: missing data or invalid data format.")

        return True


    # ================ dcs f10 map coordinate capture


    # capture coordinates from the DCS F10 map using tesseract to perform OCR on the screen. returns
    # a string with the extracted coordinates.
    #
    def capture_map_coords(self, x_start=101, x_width=269, y_start=5, y_height=27):
        self.logger.debug("Attempting to capture map coords")
        gui_mult = 2 if self.scaled_dcs_gui else 1

        dt = datetime.datetime.now()
        debug_dirname = dt.strftime("%Y-%m-%d-%H-%M-%S")

        if self.editor.prefs.is_tesseract_debug == "true":
            os.mkdir(debug_dirname)

        map_image = cv2.imread("data/map.bin")
        arrow_image = cv2.imread("data/arrow.bin")

        for display_number, image in enumerate(getDisplaysAsImages(), 1):
            self.logger.debug("Looking for map on screen " + str(display_number))

            if self.editor.prefs.is_tesseract_debug == "true":
                image.save(debug_dirname + "/screenshot-"+str(display_number)+".png")

            # convert screenshot to OpenCV format and search for the "MAP" text. matchTemplate returns a
            # new greyscale image wherethe brightness of each pixel corresponds to how good a match there
            # was at that point so now we search for the 'whitest' pixel.
            #
            screen_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
            search_result = cv2.matchTemplate(screen_image, map_image, cv2.TM_CCOEFF_NORMED)  
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(search_result)
            self.logger.debug("Minval: " + str(min_val) + " Maxval: " + str(max_val) +
                              " Minloc: " + str(min_loc) + " Maxloc: " + str(max_loc))
            start_x = max_loc[0] + map_image.shape[0]
            start_y = max_loc[1]

            if max_val > 0.9:  # better than a 90% match means we are on to something

                # now we search for the arrow icon
                #
                search_result = cv2.matchTemplate(screen_image, arrow_image, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(search_result)
                self.logger.debug("Minval: " + str(min_val) + " Maxval: " + str(max_val) +
                                  " Minloc: " + str(min_loc) + " Maxloc: " + str(max_loc))

                end_x = max_loc[0]
                end_y = max_loc[1] + map_image.shape[1]

                self.logger.debug("Capturing " + str(start_x) + "x" + str(start_y) + " to " + str(end_x) +
                                  "x" + str(end_y))

                lat_lon_image = image.crop([start_x, start_y, end_x, end_y])

                if self.editor.prefs.is_tesseract_debug == "true":
                    lat_lon_image.save(debug_dirname + "/lat_lon_image.png")

                enhancer = ImageEnhance.Contrast(lat_lon_image)
                enhanced = enhancer.enhance(6)
                if self.editor.prefs.is_tesseract_debug == "true":
                    enhanced.save(debug_dirname + "/lat_lon_image_enhanced.png")

                inverted = ImageOps.invert(enhanced)
                if self.editor.prefs.is_tesseract_debug == "true":
                    inverted.save(debug_dirname + "/lat_lon_image_inverted.png")

                captured_map_coords = pytesseract.image_to_string(inverted)

                self.logger.debug("Raw captured text: " + captured_map_coords)
                return captured_map_coords

        self.logger.debug("Raise exception (could not find the map anywhere i guess?)")

        raise ValueError("DCS F10 map not found")

    # parse the coordinate string extracted from the screen via capture_map_coords. returns a tuple
    # with position and elevation.
    #
    def parse_map_coords_string(self, coords_string, tomcat_mode=False):
        coords_string = coords_string.upper()
        # "X-00199287 Z+00523070, 0 ft"   Not sure how to convert this yet

        # "37 T FJ 36255 11628, 5300 ft"  tesseract did not like this one because the DCS font J looks too much like )
        res = re.match("^(\d+ [a-zA-Z] [a-zA-Z][a-zA-Z] \d+ \d+), ([-]?\d+) (FT|M)", coords_string)
        if res is not None:
            mgrs_string = res.group(1).replace(" ", "")
            decoded_mgrs = mgrs.UTMtoLL(mgrs.decode(mgrs_string))
            position = LatLon(Latitude(degree=decoded_mgrs["lat"]), Longitude(
                degree=decoded_mgrs["lon"]))
            elevation = float(res.group(2))

            if res.group(3) == "M":
                elevation = elevation * 3.281

            return position, elevation

        # "N43°10.244 E40°40.204, 477 ft"  Degrees and decimal minutes
        res = re.match("^([NS])(\d+)°([^\s]+) ([EW])(\d+)°([^,]+), ([-]?\d+) (FT|M)", coords_string)
        if res is not None:
            lat_str = res.group(2) + " " + res.group(3) + " " + res.group(1)
            lon_str = res.group(5) + " " + res.group(6) + " " + res.group(4)
            position = string2latlon(lat_str, lon_str, "d% %M% %H")
            elevation = float(res.group(7))

            if res.group(8) == "M":
                elevation = elevation * 3.281

            return position, elevation

        # "N42-43-17.55 E40-38-21.69, 0 ft" Degrees, minutes and decimal seconds
        res = re.match("^([NS])(\d+)-(\d+)-([^\s]+) ([EW])(\d+)-(\d+)-([^,]+), ([-]?\d+) (FT|M)", coords_string)
        if res is not None:
            lat_str = res.group(2) + " " + res.group(3) + " " + res.group(4) + " " + res.group(1)
            lon_str = res.group(6) + " " + res.group(7) + " " + res.group(8) + " " + res.group(5)
            position = string2latlon(lat_str, lon_str, "d% %m% %S% %H")
            elevation = float(res.group(9))

            if res.group(10) == "M":
                elevation = elevation * 3.281

            return position, elevation

        # "43°34'37"N 29°11'18"E, 0 ft" Degrees minutes and seconds
        res = re.match("^(\d+)°(\d+)'([^\"]+)\"([NS]) (\d+)°(\d+)'([^\"]+)\"([EW]), ([-]?\d+) (FT|M)", coords_string)
        if res is not None:
            lat_str = res.group(1) + " " + res.group(2) + " " + res.group(3) + " " + res.group(4)
            lon_str = res.group(5) + " " + res.group(6) + " " + res.group(7) + " " + res.group(8)
            position = string2latlon(lat_str, lon_str, "d% %m% %S% %H")
            elevation = float(res.group(9))

            if res.group(10) == "M":
                elevation = elevation * 3.281

            return position, elevation

        split_string = coords_string.split(',')

        if tomcat_mode:
            latlon_string = coords_string.replace("\\", "").replace("F", "")
            split_string = latlon_string.split(' ')
            lat_string = split_string[1]
            lon_string = split_string[3]
            position = string2latlon(
                lat_string, lon_string, format_str="d%°%m%'%S")

        if not tomcat_mode:
            elevation = split_string[1].replace(' ', '')
            if "FT" in elevation:
                elevation = int(elevation.replace("FT", ""))
            elif "M" in elevation:
                elevation = round(int(elevation.replace("M", ""))*3.281)
            else:
                raise ValueError("Unable to parse elevation: " + elevation)
        else:
            elevation = self.capture_map_coords(2074, 97, 966, 32)

        self.logger.info("Parsed captured text: " + str(position))
        return position, elevation


    # ================ ui/ux support


    # instantiate the gui and set it up according to the editor and preferences
    #
    def create_gui(self):
        self.logger.debug("Creating GUI")

        pois = [""] + sorted([poi.name for _, poi in self.editor.default_bases.items()],)
        arfm_ui_text = airframe_type_to_ui_text(self.editor.prefs.airframe_default)

        if self.tesseract_version is None:
            is_dcs_f10_disabled = True
        else:
            is_dcs_f10_disabled = False

        menu_bar = PyGUI.MenuBar([["DCS WE", ["Preferences...::ux_menu_prefs",
                                              "---",
                                              "Check for Updates...::ux_menu_update"]],
                                  ["File", [[["Import Profile", ["From Clipboard Encoded JSON::ux_menu_imp_clip",
                                                                 "From Text JSON or CombatFlite XML File...::ux_menu_imp_file"]]],
                                              "Export Profile", ["To Clipboard as Encoded JSON::ux_menu_exp_clip_enc",
                                                                 "To Clipboard as Text::ux_menu_exp_clip_plain",
                                                                 "To Text JSON File...::ux_menu_exp_file"]]],
                                 ])

        frame_prof = PyGUI.Frame("Profile",
                                 [[PyGUI.Text("Profile:", size=(8,1), justification="right"),
                                   PyGUI.Combo(values=[""] + self.profile_names(), readonly=True,
                                               enable_events=True, key='ux_prof_select', size=(21,1))],
                                  [PyGUI.Text("Airframe:", size=(8,1), justification="right"),
                                   PyGUI.Combo(values=airframe_list(), default_value=arfm_ui_text,
                                               enable_events=True, key='ux_prof_afrm_select', size=(21,1))],
                                  [PyGUI.Text("Waypoints in Profile:")],
                                  [PyGUI.Listbox(values=list(), size=(32,18),
                                                 enable_events=True, key='ux_prof_wypt_list')],
                                  [PyGUI.Button("Save", key='ux_prof_save', size=(6,1), pad=(6,(10,6))),
                                   PyGUI.Button("Delete", key='ux_prof_delete', size=(6,1), pad=(6,(10,6))),
                                   PyGUI.Button("Enter in Jet", key='ux_prof_enter', size=(10,1), pad=((26,6),(10,6)))],
                                 ])

        frame_coord = PyGUI.Frame("Coordinates",
                                  [[PyGUI.Text("Latitude:", size=(8,1), justification="right"),
                                    PyGUI.InputText(size=(8, 1), key='ux_lat_deg', enable_events=True),
                                    PyGUI.Text("(deg)", pad=((0,12),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_lat_min', enable_events=True),
                                    PyGUI.Text("(min)", pad=((0,12),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_lat_sec', enable_events=True),
                                    PyGUI.Text("(sec)", pad=((0,12),0))],
 
                                   [PyGUI.Text("Longitude:", size=(8,1), justification="right"),
                                    PyGUI.InputText(size=(8, 1), key='ux_lon_deg', enable_events=True),
                                    PyGUI.Text("(deg)", pad=((0,12),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_lon_min', enable_events=True),
                                    PyGUI.Text("(min)", pad=((0,12),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_lon_sec', enable_events=True),
                                    PyGUI.Text("(sec)", pad=((0,12),0))],
 
                                   [PyGUI.Text("MGRS:", size=(8,1), justification="right", pad=(5,(12,12))),
                                    PyGUI.InputText(size=(25, 1), key='ux_mgrs', enable_events=True)],
 
                                   [PyGUI.Text("Elevation:", size=(8,1), justification="right"),
                                    PyGUI.InputText(size=(8, 1), key='ux_elev_ft', enable_events=True),
                                    PyGUI.Text("(ft)", pad=((0,29),0)),
                                    PyGUI.InputText(size=(8, 1), key='ux_elev_m', enable_events=True),
                                    PyGUI.Text("(m)", pad=((0,12),0))]
                                  ])

        frame_capt = PyGUI.Frame("DCS Coordinate Capture",
                                 [[PyGUI.Checkbox("Enable capture from DCS F10 map into", pad=((6,3),6),
                                                  default=False, enable_events=True, key='ux_dcs_f10_enable',
                                                  disabled=is_dcs_f10_disabled),
                                   PyGUI.Combo(values=["Coordinate Fields", "New Waypoint"],
                                               enable_events=True, key='ux_dcs_f10_tgt_select',
                                               default_value="Coordinate Fields", pad=((0,18),6))],
                                 ])

        frame_wypt = PyGUI.Frame("Waypoint",
                                 [[PyGUI.Text("Set up from predefined location:", pad=(6,(0,16))),
                                   PyGUI.Combo(values=pois, readonly=False, enable_events=True,
                                               key='ux_poi_wypt_select', size=(20,1), pad=(6,(0,16))),
                                   PyGUI.Button(button_text="Filter", size=(6,1), key='ux_poi_filter', pad=(6,(0,16)))],
                                  [PyGUI.Text("Name:", size=(8,1), justification="right"),
                                   PyGUI.InputText(size=(50, 1), key='ux_wypt_name')],
                                  [PyGUI.Text("Type:", size=(8,1), justification="right"),
                                    PyGUI.Combo(values=["WP", "MSN", "FP", "ST", "IP", "DP", "HA", "HB"],
                                               default_value="WP", enable_events=True, readonly=True,
                                               key='ux_wypt_type_select', size=(8,1))],
                                  [PyGUI.Text("Sequence:", key="ux_seq_sta_text", size=(8,1), justification="right"),
                                   PyGUI.Combo(values=("None", 1, 2, 3), default_value="None",
                                               enable_events=True, readonly=True, key='ux_seq_stn_select',
                                               size=(8,1))],
                                  [frame_coord],
                                  [frame_capt],
                                  [PyGUI.Button("Add", key='ux_wypt_add', size=(14, 1), pad=((6,16),(12,6))),
                                   PyGUI.Button("Update", key='ux_wypt_update', size=(14, 1), pad=((16,16),(12,6))),
                                   PyGUI.Button("Remove", key='ux_wypt_delete', size=(14, 1), pad=((16,6),(12,6)))]
                                 ])

        frame_stat = PyGUI.Frame("Status",
                                 [[PyGUI.Text("Progress:", size=(8,1), justification="right"),
                                   PyGUI.ProgressBar(1.0, size=(27,16)),
                                   PyGUI.Button("Cancel", disabled=True)]
                                 ])

        col_0 = PyGUI.Column([[menu_bar],
                              [frame_prof],
                              [PyGUI.Text(f"Version: {self.software_version}")]], vertical_alignment="top")
        col_1 = PyGUI.Column([[frame_wypt], [frame_stat]], vertical_alignment="top")

        return PyGUI.Window('DCS Waypoint Editor', [[col_0, col_1]])

    # update state in response to a profile change.
    #
    def update_for_profile_change(self, set_to_first=False, update_enable=True):
        profiles = [""] + self.profile_names()
        self.window.Element('ux_prof_select').Update(values=profiles,
                                                     set_to_index=profiles.index(self.profile.profilename))
        self.window.Element('ux_poi_wypt_select').Update(set_to_index=0)
        ac_ui_text = airframe_type_to_ui_text(self.profile.aircraft)
        self.window.Element('ux_prof_afrm_select').Update(value=ac_ui_text)
        self.editor.set_driver(self.profile.aircraft)
        self.update_for_waypoint_list_change(set_to_first=set_to_first, update_enable=False)
        self.update_for_coords_change()
        self.window.Element('ux_prof_wypt_list').Update(set_to_index=[])
        if update_enable:
            self.update_gui_control_enable_state()

    # update state in response to changes to the waypoint list.
    #
    def update_for_waypoint_list_change(self, set_to_first=False, update_enable=True):
        values = list()
        self.profile.update_waypoint_numbers()

        for wp in sorted(self.profile.waypoints,
                         key=lambda waypoint: waypoint.wp_type if waypoint.wp_type != "MSN" else str(waypoint.station)):
            namestr = str(wp)
            if not self.editor.driver.validate_waypoint(wp):
                namestr = strike(namestr)
            values.append(namestr)

        if set_to_first:
            self.window.Element('ux_prof_wypt_list').Update(values=values, set_to_index=0)
        else:
            self.window.Element('ux_prof_wypt_list').Update(values=values)
        if update_enable:
            self.update_gui_control_enable_state()

    # update state in response to changes to the waypoint type.
    #
    def update_for_waypoint_type_change(self):
        if self.selected_wp_type == "WP":
            self.window.Element("ux_seq_sta_text").Update(value="Sequence:")
            self.window.Element('ux_seq_stn_select').Update(values=("None", 1, 2, 3), value="None",
                                                            disabled=False, readonly=True)
        elif self.selected_wp_type == "MSN":
            self.window.Element("ux_seq_sta_text").Update(value="Station:")
            self.window.Element('ux_seq_stn_select').Update(values=(8, 7, 3, 2), value=8,
                                                            disabled=False, readonly=True)
        else:
            self.window.Element("ux_seq_sta_text").Update(value="Sequence:")
            self.window.Element('ux_seq_stn_select').Update(values=("None", 1, 2, 3), value="None",
                                                            disabled=True, readonly=False)

    # update state in response to changes in the coordinates.
    #
    def update_for_coords_change(self, position=None, elevation=None, name=None, update_mgrs=True,
                                 wypt_type=None, wypt_seq_sta=None, update_enable=True):
        if position is not None:
            self.window.Element('ux_lat_deg').Update(round(position.lat.degree))
            self.window.Element('ux_lat_min').Update(round(position.lat.minute))
            self.window.Element('ux_lat_sec').Update(round(position.lat.second, 2))

            self.window.Element('ux_lon_deg').Update(round(position.lon.degree))
            self.window.Element('ux_lon_min').Update(round(position.lon.minute))
            self.window.Element('ux_lon_sec').Update(round(position.lon.second, 2))

            mgrs_val = mgrs.encode(mgrs.LLtoUTM(position.lat.decimal_degree, position.lon.decimal_degree), 5)

        else:
            self.window.Element('ux_lat_deg').Update("")
            self.window.Element('ux_lat_min').Update("")
            self.window.Element('ux_lat_sec').Update("")

            self.window.Element('ux_lon_deg').Update("")
            self.window.Element('ux_lon_min').Update("")
            self.window.Element('ux_lon_sec').Update("")

            mgrs_val = ""

        if update_mgrs:
            self.window.Element('ux_mgrs').Update(mgrs_val)

        if elevation is not None:
            self.window.Element('ux_elev_ft').Update(int(float(elevation)))
            self.window.Element('ux_elev_m').Update(int(round(float(elevation)/3.281)))
        else:
            self.window.Element('ux_elev_ft').Update("")
            self.window.Element('ux_elev_m').Update("")
        
        if name is not None:
            self.window.Element('ux_wypt_name').Update(name)
        else:
            self.window.Element('ux_wypt_name').Update("")

        if wypt_type is not None:
            self.selected_wp_type = wypt_type
            self.window.Element('ux_wypt_type_select').Update(value=wypt_type)
            self.update_for_waypoint_type_change()
    
        if wypt_seq_sta is not None:
            self.window.Element('ux_seq_stn_select').Update(value=wypt_seq_sta)
        else:
            self.window.Element('ux_seq_stn_select').Update(value="None")

        if update_enable:
            self.update_gui_control_enable_state()

        self.window.Refresh()

    # update gui state for control enables based on current interface state.
    #
    def update_gui_control_enable_state(self):
        if self.is_dcs_f10_enabled == True and self.tesseract_version is not None:
            self.window.Element('ux_dcs_f10_tgt_select').Update(disabled=False, readonly=True)
        else:
            self.window.Element('ux_dcs_f10_tgt_select').Update(disabled=True, readonly=False)

        if self.is_dcs_f10_tgt_add:
            self.window.Element('ux_dcs_f10_tgt_select').Update(set_to_index=1)
        else:
            self.window.Element('ux_dcs_f10_tgt_select').Update(set_to_index=0)

        if self.profile.profilename != '':
            self.window.Element('ux_prof_delete').Update(disabled=False)
        else:
            self.window.Element('ux_prof_delete').Update(disabled=True)

        if self.profile.has_waypoints == True:
            self.window.Element('ux_prof_save').Update(disabled=False)
            self.window.Element('ux_prof_enter').Update(disabled=False)
        else:
            self.window.Element('ux_prof_save').Update(disabled=True)
            if detect_dcs_bios(self.editor.prefs.path_dcs):
                self.window.Element('ux_prof_enter').Update(disabled=True)
            else:
                self.window.Element('ux_prof_enter').Update(disabled=False)

        posn, elev, _ = self.validate_coords()
        if posn is not None and elev is not None:
            self.window.Element('ux_wypt_add').Update(disabled=False)
        else:
            self.window.Element('ux_wypt_add').Update(disabled=True)

        if len(self.window.Element('ux_prof_wypt_list').get()) > 0:
            self.window.Element('ux_wypt_update').Update(disabled=False)
            self.window.Element('ux_wypt_delete').Update(disabled=False)
        else:
            self.window.Element('ux_wypt_update').Update(disabled=True)
            self.window.Element('ux_wypt_delete').Update(disabled=True)

    # update the coordinates elements enable/disable state
    #
    def update_gui_coords_input_disabled(self, disabled):
        for element_name in ('ux_lat_deg', 'ux_lat_min', 'ux_lat_sec', 'ux_lon_deg', 'ux_lon_min',
                             'ux_lon_sec', 'ux_mgrs', 'ux_elev_ft', 'ux_elev_m'):
            self.window.Element(element_name).Update(disabled=disabled)

    # change the binding of a hotkey. providing only previous will unbind the key.
    #
    # to change the callback, first unbind, then rebind.
    #
    def rebind_hotkey(self, previous, current=None, callback=None):
        try:
            if previous is not current:
                self.logger.info(f"Rebinding hotkey from '{previous}' to '{current}'")
                if previous is not None and previous != "":
                    keyboard.remove_hotkey(previous)
                if current is not None and current != "" and callback is not None:
                    keyboard.add_hotkey(current, callback)
        except KeyError:
            self.logger.debug(f"Cannot change hotkey binding from '{previous}' to '{current}'")

    # validate coordinates in ui. returns an {position, elevation, name} tuple; None's if invalid
    #
    def validate_coords(self):
        lat_deg = self.window.Element('ux_lat_deg').Get()
        lat_min = self.window.Element('ux_lat_min').Get()
        lat_sec = self.window.Element('ux_lat_sec').Get()

        lon_deg = self.window.Element('ux_lon_deg').Get()
        lon_min = self.window.Element('ux_lon_min').Get()
        lon_sec = self.window.Element('ux_lon_sec').Get()

        try:
            position = LatLon(Latitude(degree=lat_deg, minute=lat_min, second=lat_sec),
                              Longitude(degree=lon_deg, minute=lon_min, second=lon_sec))
            elevation = int(self.window.Element('ux_elev_ft').Get())
            name = self.window.Element('ux_wypt_name').Get()
            return position, elevation, name
        except ValueError as e:
            self.logger.error(f"Failed to validate coords: {e}")
            return None, None, None


    # ================ ui menu item handlers


    def do_preferences(self):
        prefs = self.editor.prefs
        hotkey_capture = prefs.hotkey_capture
        hotkey_capture_mode = prefs.hotkey_capture_mode
        hotkey_enter_profile = prefs.hotkey_enter_profile
        hotkey_enter_mission = prefs.hotkey_enter_mission

        prefs_gui = PrefsGUI(prefs, self.logger)
        prefs_gui.run()

        if self.profile.profilename == "":
            self.profile.aircraft = prefs.airframe_default
            self.update_for_profile_change()

        if self.is_dcs_f10_enabled:
            self.rebind_hotkey(hotkey_capture, prefs.hotkey_capture, self.do_dcs_f10_capture)
            self.rebind_hotkey(hotkey_capture_mode, prefs.hotkey_capture_mode, self.do_dcs_f10_capture_tgt_toggle)
        else:
            self.rebind_hotkey(hotkey_capture)
            self.rebind_hotkey(hotkey_capture_mode)
        self.rebind_hotkey(hotkey_enter_profile, prefs.hotkey_enter_profile, self.do_profile_enter_in_jet)
        self.rebind_hotkey(hotkey_enter_mission, prefs.hotkey_enter_mission, self.do_mission_enter_in_jet)

        self.update_gui_control_enable_state()
    
    def do_check_updates(self):
        return check_version(self.software_version)

    # exports profile to clipboard as a zip'd JSON encoded in ASCII
    #
    def do_profile_export_to_encoded_string(self):
        name = self.profile_name_for_ui()
        encoded = json_zip(str(self.profile))
        pyperclip.copy(encoded)
        PyGUI.Popup(f"Profile '{name}' copied as encoded text to clipboard.")

    # exports profile to clipboard as a human-readable string
    #
    def do_profile_export_to_plain_string(self):
        name = self.profile_name_for_ui()
        profile_string = self.profile.to_readable_string()
        pyperclip.copy(profile_string)
        PyGUI.Popup(f"Profile '{name}' copied as plain text to clipboard.")

    # exports profile to file as JSON
    #
    def do_profile_export_to_file(self):
        name = self.profile_name_for_ui()
        filename = PyGUI.PopupGetFile("File Name", f"Exporting Profile '{name}' from Database",
                                      default_extension=".json", save_as=True,
                                      file_types=(("JSON File", "*.json"),))
        if filename is not None:
            with open(filename + ".json", "w+") as f:
                f.write(str(self.profile))
            PyGUI.Popup(f"Profile '{name}' successfullly written to '{filename}'.")

    # imports profile from zip'd JSON encoded as ASCII on clipboard into empty/new profile
    #
    def do_profile_import_from_encoded_string(self):
        encoded = pyperclip.paste()
        try:
            decoded = json_unzip(encoded)
            #
            # note that encoded JSON may carry profile name, we will force the name to the name of
            # the empty slot, "" here.
            #
            self.profile = Profile.from_string(decoded)
            self.profile.profilename = ""
            if self.profile.aircraft is None:
                self.profile.aircraft = self.editor.prefs.airframe_default
            self.window.Element('ux_prof_select').Update(set_to_index=0)
            self.update_for_profile_change(set_to_first=True)
            self.logger.debug(self.profile.to_dict())
        except Exception as e:
            PyGUI.Popup("Failed to parse encoded profile from clipboard.")
            self.logger.error(e, exc_info=True)

    # imports profile from text JSON or combatflite XML file into empty/new profile
    #
    def do_profile_import_from_file(self):
        filename = PyGUI.PopupGetFile("File Name", "Importing Profile from File")
        if filename is not None:
            with open(filename, "r") as f:
                self.profile = Profile.from_string(f.read())
            #
            # note that text JSON may carry profile name, we will force the name to the name of the
            # empty slot, "" here.
            #
            self.profile.profilename = ""
            if self.profile.aircraft is None:
                self.profile.aircraft = self.editor.prefs.airframe_default
            self.window.Element('ux_prof_select').Update(set_to_index=0)
            self.update_for_profile_change(set_to_first=True)
            self.logger.debug(self.profile.to_dict())


    # ================ ui profile panel handlers


    def do_profile_select(self):
        try:
            profile_name = self.values['ux_prof_select']
            if profile_name != '':
                self.profile = Profile.load(profile_name)
            else:
                self.load_new_profile()
        except DoesNotExist:
            PyGUI.Popup(f"Profile '{profile_name}'' was not found in the database.", title="Error")
            self.load_new_profile()
        self.update_for_profile_change(set_to_first=True)

    def do_airframe_select(self):
        airframe_type = airframe_ui_text_to_type(self.values['ux_prof_afrm_select'])
        self.profile.aircraft = airframe_type
        if self.profile.profilename != "":
            self.profile.save(self.profile.profilename)
        self.update_for_profile_change()

    def do_profile_save(self):
        name = self.profile.profilename
        if not name:
            name = PyGUI.PopupGetText("Profile Name", "Saving Profile to Database")
            if name and len(name) > 0:
                if len([obj for obj in Profile.list_all() if obj.name == name]) == 0:
                    self.profile.save(name)
                    self.update_for_profile_change()
                else:
                    PyGUI.Popup(f"There is already a profile named '{name}'.", title="Error")

    def do_profile_delete(self):
        if self.profile.profilename != "":
            Profile.delete(self.profile.profilename)
            self.load_new_profile()
            self.update_for_profile_change()

    def do_profile_enter_in_jet(self):
        if self.profile.has_waypoints == True:
            self.logger.info(f"Entering profile '{self.profile_name_for_ui()}' into jet...")
            self.window.Element('ux_prof_enter').Update(disabled=True)
            # TODO: setup callback and so on for progress ui
            self.editor.enter_all(self.profile)
            self.window.Element('ux_prof_enter').Update(disabled=False)

    def do_profile_waypoint_list(self):
        if self.values['ux_prof_wypt_list']:
            wypt = self.find_selected_waypoint()
            if wypt.wp_type == "MSN":
                seq_stn = wypt.station
            elif wypt.wp_type == "WPT":
                seq_stn = wypt.Sequence
            else:
                seq_stn = None
            self.update_for_coords_change(wypt.position, wypt.elevation, wypt.name, wypt_type=wypt.wp_type,
                                          wypt_seq_sta=seq_stn)


    # ================ ui waypoint panel handlers


    def do_wypt_type_select(self):
        self.selected_wp_type = self.values['ux_wypt_type_select']
        self.update_for_waypoint_type_change()

    def do_seq_stn_select(self):
        return

    def do_poi_wypt_select(self):
        poi = self.editor.default_bases.get(self.values['ux_poi_wypt_select'])
        if poi is not None:
            self.update_for_coords_change(poi.position, poi.elevation, poi.name)

    def do_dcs_f10_tgt_select(self):
        if self.is_dcs_f10_enabled:
            if self.values['ux_dcs_f10_tgt_select'] == "Coordinate Fields":
                self.is_dcs_f10_tgt_add = False
            else:
                self.is_dcs_f10_tgt_add = True

    def do_poi_wypt_filter(self):
        text = self.values['ux_poi_wypt_select']
        self.window.Element('ux_poi_wypt_select').\
            Update(values=[""] + [poi.name for _, poi in self.editor.default_bases.items() if
                                  text.lower() in poi.name.lower()],
                   set_to_index=0)

    def do_waypoint_add(self):
        position, elevation, name = self.validate_coords()
        if position is not None:
            self.add_waypoint(position, elevation, name)
        else:
            PyGUI.Popup("Cannot add waypoint without coordinates.")
        self.window.Element('ux_poi_wypt_select').Update(set_to_index=0)
        self.update_for_waypoint_list_change()

    def do_waypoint_update(self):
        if self.values['ux_prof_wypt_list']:
            waypoint = self.find_selected_waypoint()
            position, elevation, name = self.validate_coords()
            if position is not None:
                waypoint.position = position
                waypoint.elevation = elevation
                waypoint.name = name
            else:
                PyGUI.Popup("Cannot update waypoint without coordinates.")
        self.window.Element('ux_poi_wypt_select').Update(set_to_index=0)
        self.update_for_waypoint_list_change()

    def do_waypoint_delete(self):
        if self.values['ux_prof_wypt_list']:
            valuestr = unstrike(self.values['ux_prof_wypt_list'][0])
            for wp in self.profile.waypoints:
                if str(wp) == valuestr:
                    self.profile.waypoints.remove(wp)
            self.update_for_waypoint_list_change()
        self.window.Element('ux_poi_wypt_select').Update(set_to_index=0)

    def do_dcs_f10_enable(self):
        self.is_dcs_f10_enabled = self.values['ux_dcs_f10_enable']
        if self.is_dcs_f10_enabled:
            self.rebind_hotkey(None, self.editor.prefs.hotkey_capture, self.do_dcs_f10_capture)
            self.rebind_hotkey(None, self.editor.prefs.hotkey_capture_mode, self.do_dcs_f10_capture_tgt_toggle)
        else:
            self.rebind_hotkey(self.editor.prefs.hotkey_capture)
            self.rebind_hotkey(self.editor.prefs.hotkey_capture_mode)
        self.update_gui_control_enable_state()

    # update ui state of widgets linked to a change in elevation (ft)
    #
    def do_waypoint_linked_update_elev_ft(self):
        elevation = self.values['ux_elev_ft']
        if elevation:
            self.window.Element('ux_elev_m').Update(round(int(elevation)/3.281))
        else:
            self.window.Element('ux_elev_m').Update("")
        self.update_gui_control_enable_state()

    # update ui state of widgets linked to a change in elevation (m)
    #
    def do_waypoint_linked_update_elev_m(self):
        elevation = self.values['ux_elev_m']
        if elevation:
            self.window.Element('ux_elev_ft').Update(round(int(elevation)*3.281))
        else:
            self.window.Element('ux_elev_ft').Update("")
        self.update_gui_control_enable_state()

    # update ui state of widgets linked to a change in mgrs
    #
    def do_waypoint_linked_update_mgrs(self):
        position, _, _ = self.validate_coords()
        if position is not None:
            m = mgrs.encode(mgrs.LLtoUTM(position.lat.decimal_degree, position.lon.decimal_degree), 5)
            self.window.Element('ux_mgrs').Update(m)
        self.update_gui_control_enable_state()

    # update ui state of widgets linked to a change in position (lat/lon)
    #
    def do_waypoint_linked_update_position(self):
        mgrs_str = self.values['ux_mgrs']
        if mgrs_str is not None:
            try:
                decoded_mgrs = mgrs.UTMtoLL(mgrs.decode(mgrs_str.replace(" ", "")))
                position = LatLon(Latitude(degree=decoded_mgrs["lat"]), Longitude(degree=decoded_mgrs["lon"]))
                self.update_for_coords_change(position, update_mgrs=False)
            except (TypeError, ValueError, UnboundLocalError) as e:
                PyGUI.Popup(f"Cannot decode MGRS '{mgrs_str}', {e}")


    # ================ non-gui handlers


    # as these are not typically called form the run loop (as they represent hotkeys and so on that
    # might not have widgets), make sure to do appropriate ui updates here.

    def do_dcs_f10_capture(self):
        self.update_gui_coords_input_disabled(True)
        if self.is_dcs_f10_tgt_add:
            try:
                captured_coords = self.capture_map_coords()
                position, elevation = self.parse_map_coords_string(captured_coords)
                self.logger.debug("Parsed text as coords succesfully: " + str(position))
                added = self.add_waypoint(position, elevation)
                if added is None:
                    self.logger.error("Failed to add waypoint from capture")
            except (IndexError, ValueError, TypeError):
                self.logger.error("Failed to parse captured text", exc_info=True)
        else:
            try:
                captured_coords = self.capture_map_coords()
                position, elevation = self.parse_map_coords_string(captured_coords)
                self.logger.debug("Parsed text as coords succesfully: " + str(position))
                self.update_for_coords_change(position, elevation, update_mgrs=True, update_enable=False)
                self.do_waypoint_linked_update_elev_ft()
            except (IndexError, ValueError, TypeError):
                self.logger.error("Failed to parse captured text", exc_info=True)
        self.update_gui_coords_input_disabled(False)
        self.update_for_waypoint_list_change()

    def do_dcs_f10_capture_tgt_toggle(self):
        self.is_dcs_f10_tgt_add = not self.is_dcs_f10_tgt_add
        self.update_gui_control_enable_state()

    def do_mission_enter_in_jet(self):
        self.logger.info(f"Entering mission '{self.editor.prefs.path_mission}' into jet...")
        try:
            with open(self.editor.prefs.path_mission, "r") as f:
                tmp_profile = Profile.from_string(f.read())
                tmp_profile.aircraft = self.editor.prefs.airframe_default
                self.editor.set_driver(tmp_profile.aircraft)
                self.editor.enter_all(tmp_profile)
                self.editor.set_driver(self.profile.aircraft)
        except:
            self.logger.error(f"Failed to load mission file '{self.editor.prefs.path_mission}'")
        

    # ================ ui main loop


    def run(self):
        self.window.finalize()
    
        if self.is_dcs_f10_enabled:
            self.rebind_hotkey(None, self.editor.prefs.hotkey_capture, self.do_dcs_f10_capture)
            self.rebind_hotkey(None, self.editor.prefs.hotkey_capture_mode, self.do_dcs_f10_capture_tgt_toggle)
        self.rebind_hotkey(None, self.editor.prefs.hotkey_enter_profile, self.do_profile_enter_in_jet)
        self.rebind_hotkey(None, self.editor.prefs.hotkey_enter_mission, self.do_mission_enter_in_jet)

        self.update_for_profile_change()

        while True:
            event, self.values = self.window.Read()
            self.logger.debug(f"DCSWE Event: {event}")
            self.logger.debug(f"DCSWE Values: {self.values}")

            if event is None or event == 'Exit':
                self.logger.info("Exiting...")
                break

            # ======== menu items

            elif 'ux_menu_prefs' in event:
                self.do_preferences()

            elif 'ux_menu_update' in event:
                if self.do_check_updates():
                    break

            elif 'ux_menu_exp_clip_enc' in event:
                self.do_profile_export_to_encoded_string()

            elif 'ux_menu_exp_clip_plain' in event:
                self.do_profile_export_to_plain_string()

            elif 'ux_menu_exp_file' in event:
                self.do_profile_export_to_file()

            elif 'ux_menu_imp_clip' in event:
                self.do_profile_import_from_encoded_string()

            elif 'ux_menu_imp_file' in event:
                self.do_profile_import_from_file()

            # ======== profile panel, combo controls

            elif event == 'ux_prof_select':
                self.do_profile_select()

            elif event == 'ux_prof_afrm_select':
                self.do_airframe_select()

            # ======== profile panel, button controls

            elif event == 'ux_prof_save':
                self.do_profile_save()

            elif event == 'ux_prof_delete':
                self.do_profile_delete()

            elif event == 'ux_prof_enter':
                self.do_profile_enter_in_jet()

            # ======== profile panel, list controls

            elif event == 'ux_prof_wypt_list':
                self.do_profile_waypoint_list()

            # ======== waypoint panel, combo controls

            elif event == 'ux_wypt_type_select':
                self.do_wypt_type_select()

            elif event == 'ux_seq_stn_select':
                self.do_seq_stn_select()

            elif event == 'ux_poi_wypt_select':
                self.do_poi_wypt_select()

            elif event == 'ux_dcs_f10_tgt_select':
                self.do_dcs_f10_tgt_select()

            elif event == 'ux_poi_filter':
                self.do_poi_wypt_filter()

            # ======== waypoint panel, button controls

            elif event == 'ux_wypt_add':
                self.do_waypoint_add()

            elif event == 'ux_wypt_update':
                self.do_waypoint_update()

            elif event == 'ux_wypt_delete':
                self.do_waypoint_delete()

            elif event == 'ux_dcs_f10_enable':
                self.do_dcs_f10_enable()

            # ======== waypoint panel, text field controls

            elif event == 'ux_elev_ft':
                self.do_waypoint_linked_update_elev_ft()

            elif event == 'ux_elev_m':
                self.do_waypoint_linked_update_elev_m()

            elif event in ('ux_lat_deg', 'ux_lat_min', 'ux_lat_sec', 'ux_lon_deg', 'ux_lon_min', 'ux_lon_sec'):
                self.do_waypoint_linked_update_mgrs()

            elif event == 'ux_mgrs':
                self.do_waypoint_linked_update_position()

        self.close()

    def close(self):
        self.rebind_hotkey(self.editor.prefs.hotkey_capture)
        self.rebind_hotkey(self.editor.prefs.hotkey_capture_mode)
        self.rebind_hotkey(self.editor.prefs.hotkey_enter_profile)
        self.rebind_hotkey(self.editor.prefs.hotkey_enter_mission)

        self.window.Close()

        self.editor.stop()
