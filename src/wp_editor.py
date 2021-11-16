from time import sleep
from src.objects import default_bases
from src.db import DatabaseInterface
from src.logger import get_logger
from src.drivers import HornetBaseDriver, HarrierBaseDriver, MirageBaseDriver, TomcatBaseDriver, DriverException, WarthogBaseDriver
from src.writer import FileWriter


class WaypointEditor:

    def __init__(self, settings):
        self.logger = get_logger("driver")
        self.settings = settings
        self.db = DatabaseInterface(settings['PREFERENCES'].get("DB_Name", "profiles.db"))
        self.default_bases = default_bases

        writer = FileWriter("output.txt")
        self.drivers = dict(hornet=HornetBaseDriver(self.logger, settings, writer),
                            harrier=HarrierBaseDriver(self.logger, settings, writer),
                            mirage=MirageBaseDriver(self.logger, settings, writer),
                            tomcat=TomcatBaseDriver(self.logger, settings, writer),
                            warthog=WarthogBaseDriver(self.logger, settings, writer))
        self.driver = self.drivers["hornet"]

    def set_driver(self, driver_name):
        try:
            self.driver = self.drivers[driver_name]
        except KeyError:
            raise DriverException(f"Undefined driver: {driver_name}")

    def enter_all(self, profile):
        self.logger.info(f"Entering waypoints for aircraft: {profile.aircraft}")
        sleep(int(self.settings['PREFERENCES'].get('Grace_Period', 5)))
        self.driver.start()
        self.driver.enter_all(profile)
        self.driver.stop()

    def stop(self):
        self.db.close()
