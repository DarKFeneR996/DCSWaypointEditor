'''

comp_dcs_WE.py: DCS Waypoint Editor component version management

'''

import urllib.request
import webbrowser

from src.logger import get_logger

DCS_WE_VERSION = "v1.0.0-raven_BETA.5"

logger = get_logger(__name__)

# return version of latest DCS waypoint editor, None if unknown.
#
# latest version is pulled from master branch on github.
#
def dcs_we_vers_latest():
    # TODO: put this back when we merge back to master
    #version_url = "https://raw.githubusercontent.com/51st-Vfw/DCSWaypointEditor/master/release_version.txt"
    version_url = "https://raw.githubusercontent.com/51st-Vfw/DCSWaypointEditor/ilominar-ux-v2-xml/release_version.txt"

    try:
        with urllib.request.urlopen(version_url) as response:
            if response.code == 200:
                html = response.read()
            else:
                return None
    except (urllib.error.HTTPError, urllib.error.URLError):
        return None

    return html.decode("utf-8")

# return installed version of current DCS waypoint editor.
#
def dcs_we_vers_install():
    return DCS_WE_VERSION

# check if DCS waypoint editor is up-to-date.
#
def dcs_we_is_current():
    return True if dcs_we_vers_latest() == DCS_WE_VERSION else False

# install DCS waypoint editor.
#
# opens a web browser on releases section of the DCSWE github. user can figure the rest out....
#
def dcs_we_install():
    try:
        logger.debug("redirecting to DCSWE releases on GitHub...")
        webbrowser.open("https://github.com/51st-Vfw/DCSWaypointEditor/releases")
    except:
        pass
    return None
