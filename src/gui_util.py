'''

gui_util.py: helpful utilities for the GUI

'''

from logging import disable
import PySimpleGUI as PyGUI
import threading
import queue

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
# installation function should return version string on success (user is notified via ui), empty
# string on error (user is notified via ui), or None on no result (user is not notified).
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

import time

# run a background operation with a modal progress ui.
#
# the backgrounded operation (bop_fn) must take two named args: progress_q and cancel_q in
# addition to any unamed arguments given by the tuple in bop_args.
#
#   progress_q (queue)  operation puts numbers on [0,100] representing the completion
#                       percentage, "DONE" when the operation has finished or is cancelled
#   command_q (queue)   gui puts "CANCEL" in this queue to indicate the operation should
#                       stop processing, clean up, and exit
#
def gui_backgrounded_operation(title, bop_fn=None, bop_args=None):
    layout = [[PyGUI.Text("Progress:", size=(8,1), justification="right"),
               PyGUI.ProgressBar(100, key='ux_progress', size=(25,16)),
               PyGUI.Button("Cancel", key='ux_cancel', size=(10,1), pad=(6,16))]]
    window = PyGUI.Window(title, layout, modal=True, finalize=True, disable_close=True)

    progress_q = queue.Queue()
    command_q = queue.Queue()
    bop_kwargs={ 'progress_q' : progress_q, 'command_q' : command_q }

    bop_thread = threading.Thread(target=bop_fn, args=bop_args, kwargs=bop_kwargs)
    bop_thread.start()

    logger.debug(f"Starting progress ui for backgrounded op, thread {bop_thread.ident}")

    while True:
        event, _ = window.Read(timeout=500, timeout_key='Timeout')
        if event == 'Timeout':
            try:
                progress = progress_q.get(False)
                window['ux_progress'].update(progress)
                if progress == "DONE":
                    logger.debug(f"Backgrounded op progress: DONE")
                    break
                else:
                    logger.debug(f"Backgrounded op progress: {progress:.2f}")
            except queue.Empty:
                pass
        elif event == 'ux_cancel':
            logger.debug("Sending cancel to backgrounded op, waiting for join")
            window['ux_cancel'].update(text="Cancelling...", disabled=True)
            window['ux_cancel'].update(disabled=True)
            command_q.put("CANCEL")
        if not bop_thread.is_alive():
            logger.debug("Backgrounded op thread has passed beyond the veil")
            break

    window.close()
