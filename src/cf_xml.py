import xml.etree.ElementTree as xml
import re
from src.logger import get_logger
from src.objects import Profile, Waypoint, MSN
from LatLon23 import LatLon, Longitude, Latitude
from typing import Any

logger = get_logger(__name__)

# class to import DCSWE profiles from CombatFlite XML exports.
#
class CombatFliteXML:

    # returns a cleaned up name from a CombatFlite XML element.
    #
    @staticmethod
    def elem_get_name(elem):
        e_nam = elem.find("Name")
        if e_nam is not None:
            return e_nam.text.replace("\n", " ")
        else:
            return ""

    # returns a { LatLon, elev } position tuple from a CombatFlite XML element.
    #
    @staticmethod
    def elem_get_position(elem):
        e_pos = elem.find("Position")
        e_lat = e_pos.find("Latitude")
        e_lon = e_pos.find("Longitude")
        e_alt = e_pos.find("Altitude")
        if e_lat is None or e_lon is None:
            raise ValueError("Failed to find position in XML element")
        if e_alt is None:
            elev = 0.0
        else:
            elev = int(float(e_alt.text))
        return LatLon(Latitude(e_lat.text), Longitude(e_lon.text)), elev

    # returns True/False if the element's name matches a regex.
    #
    @staticmethod
    def elem_name_matches(elem, name_regex):
        name = CombatFliteXML.elem_get_name(elem)
        if name != "":
            res = re.match(name_regex, name, flags=re.IGNORECASE)
            if res is not None:
                return True
        return False

    # returns an array with all "Waypoint" elements from the CombatFlite XML whose name
    # matches a regex.
    #
    @staticmethod
    def find_waypoints_named(root, name_regex):
        elem_wp = []
        for elem in root.iter("Waypoint"):
            if CombatFliteXML.elem_name_matches(elem, name_regex):
                elem_wp.append(elem)
        return elem_wp

    # returns an array with all "Object" elements from the CombatFlite XML whose name matches
    # a regex.
    #
    @staticmethod
    def find_objects_named(root, name_regex):
        elem_obj = []
        for elem in root.iter("Object"):
            if CombatFliteXML.elem_name_matches(elem, name_regex):
                elem_obj.append(elem)
        return elem_obj

    # check to see if a string contains a valid XML object.
    #
    @staticmethod
    def is_xml(str):
        try:
            str.index("<?xml version")
            return True
        except:
            return False

    # create a DCSWE profile from an CombatFlite XML string.
    #
    # callsign, if given, should be in the format "<name><number>-<ship>", e.g., "Enfield1-2"
    #
    @staticmethod
    def profile_from_string(str, callsign="", name="", aircraft="viper"):
        match = re.match(r"^(?P<flight>[a-zA-Z]+[\d]+)-(?P<ship>[\d]+)$",
                         callsign, flags=re.IGNORECASE)
        if match and match.group('flight') is not None and match.group('ship') is not None:
            flight = match.group('flight')
            ship = match.group('ship')
        else:
            flight = ""
            ship = ""

        try:
            index = str.index("<?xml version")
            str = str[index:]
        except:
            raise ValueError("Data does not contain a vaild XML description")

        try:
            root = xml.fromstring(str)

            # grab "Waypoint" elements from the XML that match the flight name. these map to
            # WP waypoints in DCS.
            #
            wps = []
            for elem in CombatFliteXML.find_waypoints_named(root, f"^{flight}"):
                name = CombatFliteXML.elem_get_name(elem)
                posn, elev = CombatFliteXML.elem_get_position(elem)
                wp = Waypoint(name=name, sequence=0, position=posn, elevation=elev)
                logger.info(f"{wp}")
                wps.append(wp)
            logger.info(f"CF XML: Built {len(wps)} '{callsign}' WP waypoints")

            # grab "Object" elements from the XML that have a name beginning with "DMPI ".
            # these map to MSN waypoints in DCS.
            #
            # split this into two groups: one for DMPIs associated with a target waypoint
            # (these have names like "DMPI targeted by Colt1") for the flight, and one for
            # DMPIs for DMPI reference points (these have names like "DMPI 1").
            #
            # note that the first group is restricted to the flight, the second has *all*
            # DMPIs.
            #
            dmpi_wypt = []
            dmpi_refp = []
            name_pfx = f"DMPI targeted by " + f"{flight}"
            for elem in CombatFliteXML.find_objects_named(root, f"DMPI "):
                name = CombatFliteXML.elem_get_name(elem)
                match = re.match(r"^DMPI targeted by (?P<flight>[\S]+)",
                                 name, flags=re.IGNORECASE)
                print(f"{name}, {match}")
                if match and flight.lower() == match.group('flight').lower():
                    print(f"wp {len(dmpi_wypt)}")
                    dmpi_wypt.append(elem)
                elif not match:
                    print(f"rp {len(dmpi_refp)}")
                    dmpi_refp.append(elem)
                '''
                print(f"{CombatFliteXML.elem_get_name(elem)}")
                name = CombatFliteXML.elem_get_name(elem).lower()
                if name.startswith(name_pfx.lower()):
                    print(f"wp {len(dmpi_wypt)}")
                    dmpi_wypt.append(elem)
                elif not name.startswith(f"DMPI targeted by "):
                    print(f"rp {len(dmpi_refp)}")
                    dmpi_refp.append(elem)
                '''
            logger.info(f"CF XML: got {len(dmpi_wypt)} '{flight}' DMPI waypoints")
            logger.info(f"CF XML: got {len(dmpi_refp)} DMPI reference points")

            # build the list of MSN waypoints from the combination of the waypoint and
            # reference point elements.
            #
            # the reference point elements, through their name, can map a specific DMPI
            # to a specific jet in the flight along with a specific station on the jet.
            # it does this through the DMPI reference point name which should be of the
            # format "DMPI <number> <ship>:<station>"
            #
            msns = []
            for elem_w in dmpi_wypt:
                pos_wypt, elv_wypt = CombatFliteXML.elem_get_position(elem_w)
                for elem_r in dmpi_refp:
                    pos_refp, _ = CombatFliteXML.elem_get_position(elem_r)
                    if pos_wypt.almost_equal(pos_refp, e=0.00001):
                        name = CombatFliteXML.elem_get_name(elem_r)
                        match = re.match(r"^DMPI [\d]+[\s]+(?P<shp>[\d]+):(?P<sta>[\d]+)?",
                                         name, flags=re.IGNORECASE)
                        if match:
                            dmpi_ship = match.group('shp')
                            dmpi_station = match.group('sta')
                        else:
                            dmpi_ship = ""
                            dmpi_station = "8"
                        if dmpi_ship == "" or dmpi_ship == ship:
                            msn = MSN(name=name, station=dmpi_station,
                                      position=pos_wypt, elevation=elv_wypt)
                            logger.info(f"{msn}")
                            msns.append(msn)
            logger.info(f"CF XML: Built {len(msns)} '{callsign}' MSN waypoints")

            return Profile(name, waypoints=wps+msns, aircraft=aircraft)

        except:
            raise ValueError("Failed to parse CombatFlite XML file")
