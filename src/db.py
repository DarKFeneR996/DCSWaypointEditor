'''
*
*  db.py: DCS Waypoint Editor profile database
*
*  Copyright (C) 2020 Santi871
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

from src.db_models import ProfileModel, WaypointModel, SequenceModel, db
from src.logger import get_logger


class DatabaseInterface:
    def __init__(self, db_name):
        self.logger = get_logger(__name__)
        db.init(db_name)
        db.connect()
        db.create_tables([ProfileModel, WaypointModel, SequenceModel])
        self.logger.debug("Connected to database")

    @staticmethod
    def close():
        db.close()
