'''
*
*  dcs_f10_capture.py: Coordinate capture from DCS F10 map based on Tesseract OCR library
*
*  Copyright (C) 2020 Santi871
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

import cv2
import datetime
import numpy
import os
import re
import pytesseract

import src.pymgrs as mgrs

from desktopmagic.screengrab_win32 import getDisplaysAsImages
from LatLon23 import LatLon, Longitude, Latitude, string2latlon
from PIL import ImageEnhance, ImageOps

from src.logger import get_logger


logger = get_logger(__name__)


# capture coordinates from the DCS F10 map using tesseract to perform OCR on the screen.
# returns an uppercase string with the extracted coordinates.
#
def dcs_f10_capture_map_coords(x_start=101, x_width=269, y_start=5, y_height=27,
                               scaled_dcs_gui=None, debug_dir=None):
    logger.debug("Attempting to capture map coords")
    gui_mult = 2 if scaled_dcs_gui else 1

    dt = datetime.datetime.now()
    if debug_dir is not None:
        debug_dirname = debug_dir + dt.strftime("%Y-%m-%d-%H-%M-%S")
        os.mkdir(debug_dirname)
        is_debug = True
    else:
        is_debug = False

    map_image = cv2.imread("data/map.bin")
    arrow_image = cv2.imread("data/arrow.bin")

    for display_number, image in enumerate(getDisplaysAsImages(), 1):
        logger.debug("Looking for map on screen " + str(display_number))

        if is_debug:
            image.save(debug_dirname + "/screenshot-"+str(display_number)+".png")

        # convert screenshot to OpenCV format and search for the "MAP" text. matchTemplate
        # returns a new greyscale image wherethe brightness of each pixel corresponds to how
        # good a match there was at that point so now we search for the 'whitest' pixel.
        #
        screen_image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
        search_result = cv2.matchTemplate(screen_image, map_image, cv2.TM_CCOEFF_NORMED)  
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(search_result)
        logger.debug("Minval: " + str(min_val) + " Maxval: " + str(max_val) +
                     " Minloc: " + str(min_loc) + " Maxloc: " + str(max_loc))
        start_x = max_loc[0] + map_image.shape[0]
        start_y = max_loc[1]

        if max_val > 0.9:  # better than a 90% match means we are on to something

            # now we search for the arrow icon
            #
            search_result = cv2.matchTemplate(screen_image, arrow_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(search_result)
            logger.debug("Minval: " + str(min_val) + " Maxval: " + str(max_val) +
                         " Minloc: " + str(min_loc) + " Maxloc: " + str(max_loc))

            end_x = max_loc[0]
            end_y = max_loc[1] + map_image.shape[1]

            logger.debug("Capturing " + str(start_x) + "x" + str(start_y) + " to " + str(end_x) +
                         "x" + str(end_y))

            lat_lon_image = image.crop([start_x, start_y, end_x, end_y])

            if is_debug:
                lat_lon_image.save(debug_dirname + "/lat_lon_image.png")

            enhancer = ImageEnhance.Contrast(lat_lon_image)
            enhanced = enhancer.enhance(2)
            if is_debug:
                enhanced.save(debug_dirname + "/lat_lon_image_enhanced.png")

            inverted = ImageOps.invert(enhanced)
            if is_debug:
                inverted.save(debug_dirname + "/lat_lon_image_inverted.png")

            captured_map_coords = pytesseract.image_to_string(inverted).replace("\x0A\x0C", "")

            logger.info(f"Raw captured text: {captured_map_coords}")

            # HACK: tesseract sometimes recognizes "E" as "£" and "J" as ")", "]", or "}".
            # HACK: since "£", ")", "]", and "}" symbols cannot appear in the coordinate
            # HACK: formats that DCS uses, we'll assume any occurance of "£", ")", and "]"
            # HACK: are something else and fix up the string here.
            #
            captured_map_coords = captured_map_coords.replace(")", "J")
            captured_map_coords = captured_map_coords.replace("]", "J")
            captured_map_coords = captured_map_coords.replace("}", "J")
            captured_map_coords = captured_map_coords.replace("£", "E")
            return captured_map_coords.upper()

    logger.debug("Raise exception (could not find the map anywhere i guess?)")

    raise ValueError("DCS F10 map not found")

# parse the coordinate string extracted from the screen via capture_map_coords. returns a
# tuple with position and elevation (which may be negative).
#
def dcs_f10_parse_map_coords_string(coords_string, tomcat_mode=False):

    # tesseract recognition is not 100% (see, for example, the issues with "E" and "£"
    # above in the capture code). as a result, we will tend to use regex's below that allow
    # latitude in the non-critical parts of the string (e.g., for a "°" delimiter).

    # "37 T FJ 36255 11628, 5300 ft" -- MGRS
    #
    # NOTE: regex handles tesseract mistake where fields run together; e.g., "TFJ" in place
    # NOTE: of "T FJ"
    #
    res = re.match(r"^(\d+[.\s]*[A-Z][.\s]*[A-Z][A-Z][.\s]*\d+[.\s]*\d+)[^-\d]+([-]?\d+)[^FTM]+(FT|M)",
                   coords_string)
    if res is not None:
        mgrs_string = res.group(1).replace(" ", "")
        decoded_mgrs = mgrs.UTMtoLL(mgrs.decode(mgrs_string))
        position = LatLon(Latitude(degree=decoded_mgrs["lat"]),
                          Longitude(degree=decoded_mgrs["lon"]))
        elevation = float(res.group(2))

        if res.group(3) == "M":
            elevation = elevation * 3.281

        logger.info(
            f"Parsed '{coords_string}' as MGRS, coords: {str(position)}, {elevation:.2f} FT")
        return position, elevation

    # "N43°10.244 E40°40.204, 477 ft" -- Degrees and decimal minutes
    #
    res = re.match(r"^([NS])(\d+)[\D]+([.\d]+)[^EW]+([EW])(\d+)[\D]+([.\d]+)[^-\d]+([-]?\d+)[^FTM]+(FT|M)",
                    coords_string)
    if res is not None:
        lat_str = res.group(2) + " " + res.group(3) + " " + res.group(1)
        lon_str = res.group(5) + " " + res.group(6) + " " + res.group(4)
        position = string2latlon(lat_str, lon_str, "d% %M% %H")
        elevation = float(res.group(7))

        if res.group(8) == "M":
            elevation = elevation * 3.281

        logger.info(
            f"Parsed '{coords_string}' as DDM, coords: {str(position)}, {elevation:.2f} FT")
        return position, elevation

    # "N42-43-17.55 E40-38-21.69, 0 ft" -- Degrees, minutes and decimal seconds
    #
    res = re.match(r"^([NS])(\d+)[\D]+(\d+)[\D]+([.\d]+)[^EW]+([EW])(\d+)[\D]+(\d+)[\D]+([.\d]+)[^-\d]+([-]?\d+)[^FTM]+(FT|M)",
                    coords_string)
    if res is not None:
        lat_str = res.group(2) + " " + res.group(3) + " " + res.group(4) + " " + res.group(1)
        lon_str = res.group(6) + " " + res.group(7) + " " + res.group(8) + " " + res.group(5)
        position = string2latlon(lat_str, lon_str, "d% %m% %S% %H")
        elevation = float(res.group(9))

        if res.group(10) == "M":
            elevation = elevation * 3.281

        logger.info(
            f"Parsed '{coords_string}' as DMDS, coords: {str(position)}, {elevation:.2f} FT")
        return position, elevation

    # "43°34'37"N 29°11'18"E, 0 ft" -- Degrees minutes and seconds
    #
    res = re.match(r"^(\d+)[\D]+(\d+)[\D]+(\d+)[^NS]+([NS])[\D]+(\d+)[\D]+(\d+)[\D]+(\d+)[^EW]+([EW])[^-\d]+([-]?\d+)[^FTM]+(FT|M)",
                    coords_string)
    if res is not None:
        lat_str = res.group(1) + " " + res.group(2) + " " + res.group(3) + " " + res.group(4)
        lon_str = res.group(5) + " " + res.group(6) + " " + res.group(7) + " " + res.group(8)
        position = string2latlon(lat_str, lon_str, "d% %m% %S% %H")
        elevation = float(res.group(9))

        if res.group(10) == "M":
            elevation = elevation * 3.281

        logger.info(
            f"Parsed '{coords_string}' as DMS, coords: {str(position)}, {elevation:.2f} FT")
        return position, elevation

    # "X-00199287 Z+00523070, 0 ft" -- X/Y
    # 
    # Not sure how to convert this yet, just fall through with an error.

    logger.info("Unable to parse captured text '{coords_string}'")
    return None, None

    '''
    TODO: taking this code out temporarily, not clear we should ever hit it. there is no
    TODO: use of tomcat_mode in the code and position is not parsed in non-tomcat_mode.

    split_string = coords_string.split(',')

    if tomcat_mode:
        latlon_string = coords_string.replace("\\", "").replace("F", "")
        split_string = latlon_string.split(' ')
        lat_string = split_string[1]
        lon_string = split_string[3]
        position = string2latlon(lat_string, lon_string, format_str="d%°%m%'%S")

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
    '''
