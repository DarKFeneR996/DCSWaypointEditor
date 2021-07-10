'''
*
*  wp_editor.py: DCS Waypoint Editor main model/object
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

import os

from src.db import DatabaseInterface
from src.db_objects import default_bases
from src.drivers import HornetDriver, HarrierDriver, MirageDriver, TomcatDriver, DriverException
from src.drivers import WarthogDriver, ViperDriver
from src.logger import get_logger


class WaypointEditor:

    def __init__(self, prefs):
        self.logger = get_logger("drivers")
        self.prefs = prefs
        self.db = DatabaseInterface(self.prefs.profile_db_name)
        self.default_bases = default_bases
        self.drivers = dict(hornet=HornetDriver(self.logger, self.prefs),
                            harrier=HarrierDriver(self.logger, self.prefs),
                            mirage=MirageDriver(self.logger, self.prefs),
                            tomcat=TomcatDriver(self.logger, self.prefs),
                            warthog=WarthogDriver(self.logger, self.prefs),
                            viper=ViperDriver(self.logger, self.prefs))
        self.driver = self.drivers["viper"]

    def set_driver(self, driver_name):
        try:
            self.driver = self.drivers[driver_name]
        except KeyError:
            raise DriverException(f"Undefined driver: {driver_name}")

    def enter_all(self, profile, command_q=None, progress_q=None):
        self.logger.info(f"Entering waypoints for aircraft: {profile.aircraft}")
        self.driver.enter_all(profile, command_q=command_q, progress_q=progress_q)

    def reset_db(self):
        self.db.close()
        os.remove(self.prefs.profile_db_name)
        self.db = DatabaseInterface(self.prefs.profile_db_name)

    def stop(self):
        self.db.close()
        if self.driver is not None:
            self.driver.stop()
