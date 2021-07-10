'''
*
*  db.py: DCS Waypoint Editor profile database models
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

from peewee import Model, IntegerField, CharField, ForeignKeyField, FloatField, SqliteDatabase
from peewee import IntegrityError

db = SqliteDatabase(None, pragmas={'foreign_keys': 1})


class ProfileModel(Model):
    name = CharField(unique=True)
    aircraft = CharField(unique=False)

    class Meta:
        database = db


class SequenceModel(Model):
    identifier = IntegerField()
    profile = ForeignKeyField(ProfileModel, backref='sequences')

    class Meta:
        database = db


class WaypointModel(Model):
    name = CharField(null=True, default="")
    latitude = FloatField()
    longitude = FloatField()
    elevation = IntegerField(default=0)
    profile = ForeignKeyField(ProfileModel, backref='waypoints')
    sequence = ForeignKeyField(SequenceModel, backref='waypoints', null=True)
    wp_type = CharField()
    station = IntegerField(default=0)

    class Meta:
        database = db
