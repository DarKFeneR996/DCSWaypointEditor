from src.logger import get_logger, log_settings
from src.wp_editor import WaypointEditor
from src.dcs_bios import dcs_bios_vers_install
from src.gui import DCSWyptEdGUI, exception_gui, check_version
from src.objects import generate_default_bases
from src.prefs_gui import PrefsGUI
from src.prefs_manager import PrefsManager
import traceback
import logging


software_version = "v1.0.0-raven_BETA.5"


def main():
    prefs = PrefsManager()

    if prefs.is_auto_upd_check == "true" and check_version(software_version):
        return

    if prefs.is_new_prefs_file == False:
        setup_completed = True
    else:
        setup_logger = get_logger("setup")
        setup_logger.info("Running first time setup...")
        prefs_gui = PrefsGUI(prefs, setup_logger)
        setup_completed = prefs_gui.run()
        setup_logger.info("First time setup completes with {setup_completed}")

    if setup_completed:
        generate_default_bases()
        log_settings(software_version)

        dcs_bios_version = dcs_bios_vers_install(prefs.path_dcs)
        editor = WaypointEditor(prefs)

        gui = DCSWyptEdGUI(editor, software_version, dcs_bios_version)

        try:
            gui.run()
        except Exception:
            gui.close()
            raise


if __name__ == "__main__":
    logger = get_logger("root")
    logger.info("Initializing")

    try:
        main()
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logging.shutdown()
        exception_gui(traceback.format_exc())
        raise

    logger.info("Finished")
