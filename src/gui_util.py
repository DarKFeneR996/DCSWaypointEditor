'''

gui_util.py: helpful utilities for the GUI

'''

import PySimpleGUI as PyGUI

from src.logger import get_logger

logger = get_logger(__name__)

# maps UI text : internal type for airframe pulldown menus in the ui.
#
airframe_map = { "A-10C Warthog" : "warthog",
                 "AV-8B Harrier" : "harrier",
                 "F-14A/B Tomcat" : "tomcat",
                 "F-16C Viper" : "viper",
                 "F/A-18C Hornet" : "hornet",
                 "M-2000C Mirage" : "mirage"
}

# return list of supported airframes. second token (" " separated) of items is internal name.
#
def airframe_list():
    return list(airframe_map.keys())

# convert ui airframe text to internal airframe type.
#  
def airframe_ui_text_to_type(ui_text):
    type = airframe_map[ui_text]
    if type is None:
        type = "viper"
    return type

# convert interanl airframe type to text suitable for ui
#
def airframe_type_to_ui_text(type):
    hits = [k for k,v in airframe_map.items() if v == type]
    if (len(hits) == 0):
        hits = ["F-16C Viper"]
    return hits[0]

# ui for exceptions.
#
def gui_exception(exc_info):
    return PyGUI.PopupOK("An exception occured and the program terminated execution:\n\n" + exc_info)

# handle an update request if the current and new version of a component are not the same.
#
# installation function should return version string on success (notified), empty string on error
# (notified), or None on no result (quiet).
#
def gui_update_request(comp, cur_vers, new_vers, install_fn):
    message = f"A new version of {comp} is available ({new_vers}).\nDo you want to update from {cur_vers}?"
    if cur_vers != new_vers and PyGUI.PopupYesNo(message, title="New Version Available") == "Yes":
        logger.info(f"Update {comp} from {cur_vers} to {new_vers} accepted")
        version = install_fn()
        if version is not None and version != "":
            PyGUI.Popup(f"{comp} {new_vers} was successfully installed.", title="Success")
        elif version is not None:
            PyGUI.Popup(f"{comp} {new_vers} installation failed.", title="Error")
        return True
    else:
        logger.info(f"Update {comp} from {cur_vers} to {new_vers} declined")
    return False