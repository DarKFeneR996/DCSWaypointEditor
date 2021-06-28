from time import sleep
from src.objects import default_bases
from src.db import DatabaseInterface
from src.logger import get_logger
from src.drivers import HornetDriver, HarrierDriver, MirageDriver, TomcatDriver, DriverException, WarthogDriver,\
    ViperDriver


class WaypointEditor:

    def __init__(self, prefs):
        self.logger = get_logger("driver")
        self.prefs = prefs
        self.db = DatabaseInterface(self.prefs.profile_db_name)
        self.default_bases = default_bases
        self.drivers = dict(hornet=HornetDriver(self.logger, self.prefs),
                            harrier=HarrierDriver(self.logger, self.prefs),
                            mirage=MirageDriver(self.logger, self.prefs),
                            tomcat=TomcatDriver(self.logger, self.prefs),
                            warthog=WarthogDriver(self.logger, self.prefs),
                            viper=ViperDriver(self.logger, self.prefs))
        self.driver = self.drivers["hornet"]

    def set_driver(self, driver_name):
        try:
            self.driver = self.drivers[driver_name]
        except KeyError:
            raise DriverException(f"Undefined driver: {driver_name}")

    def enter_all(self, profile):
        self.logger.info(f"Entering waypoints for aircraft: {profile.aircraft}")
        sleep(int(self.prefs.dcs_grace_period))
        self.driver.enter_all(profile)

    def stop(self):
        self.db.close()
        if self.driver is not None:
            self.driver.stop()
