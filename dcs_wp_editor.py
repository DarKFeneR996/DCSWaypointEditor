'''

dcs_wp_editor.py: DCS waypoint editor

'''

import logging
import traceback

from src.comp_dcs_bios import dcs_bios_vers_install, dcs_bios_vers_latest, dcs_bios_install
from src.comp_dcs_we import dcs_we_vers_install, dcs_we_vers_latest, dcs_we_install
from src.gui_util import gui_update_request, gui_exception
from src.logger import get_logger, log_settings
from src.objects import generate_default_bases
from src.prefs_gui import DCSWEPreferencesGUI
from src.prefs_manager import PrefsManager
from src.wp_editor import WaypointEditor
from src.wp_editor_gui import WaypointEditorGUI


def main(logger):
    prefs = PrefsManager()
    vers_sw_cur = dcs_we_vers_install()
    vers_sw_latest = dcs_we_vers_latest()

    sw_install_fn = lambda: dcs_we_install()
    if (prefs.is_auto_upd_check == "true" and
        gui_update_request("DCS Waypoint Editor", vers_sw_cur, vers_sw_latest, sw_install_fn)):
        return

    if prefs.is_new_prefs_file == False:
        setup_completed = True
    else:
        logger.info("Running first time setup...")
        prefs_gui = DCSWEPreferencesGUI(prefs)
        setup_completed = prefs_gui.run()
        logger.info("First time setup returns {setup_completed}")

    if setup_completed:
        logger.info("Setup complete, starting waypoint editor")

        generate_default_bases()
        log_settings(vers_sw_cur)

        vers_db_cur = dcs_bios_vers_install(prefs.path_dcs)
        vers_db_latest = dcs_bios_vers_latest()
        db_install_fn = lambda: dcs_bios_install(prefs.path_dcs)
        if (prefs.is_auto_upd_check == "true" and
            gui_update_request("DCS-BIOS", vers_db_cur, vers_db_latest, db_install_fn)):
            vers_db_cur = dcs_bios_vers_install(prefs.path_dcs)

        editor = WaypointEditor(prefs)

        gui = WaypointEditorGUI(editor, vers_sw_cur, vers_db_cur)

        try:
            gui.run()
        except Exception:
            gui.close()
            raise

if __name__ == "__main__":
    logger = get_logger("dcswe")
    logger.info("Launching")

    try:
        main(logger)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logging.shutdown()
        gui_exception(traceback.format_exc())
        raise

    logger.info("Exiting")
