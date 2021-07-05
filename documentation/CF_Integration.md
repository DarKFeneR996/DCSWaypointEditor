# CombatFlite Integration with DCSWE

DCS Waypoint Editor (DCSWE) can import data from XML files exported from a CombatFlite
(CF) mission. The goal of DCSWE is to allow the mission designer to export a single XML
file from CF that covers all flights in the mission. This single XML can then be passed
to pilots and used, ideally without further edits, to set up waypoints in the jets
according to the mission.

Using the XML export, DCSWE can create a profile of WP and MSN waypoints. The current
version of DCSWE is focused on the F-16C and F/A-18C airframes and the WP and MSN DCSWE
waypoint types. When importing CF XML, DCSWE will not generate some waypoint types that
DCSWE supports (specifically, HA, FP, ST, DP, IP, and HB) that are used by other
airframes.

# Overall Workflow

Assuming edits to the flight plans outside of CF are unnecessary, the expected workflow
is as follows:

1. Mission designer builds mission in CombatFlite, exports as XML.
2. Pilots enter information from XML into jet via DCSWE “mission load” hotkey.

Since there may be situations where further customization of the information in the XML
export is necessary, there is also a workflow that allows for further editing of the
information CF exports:

1. Mission designer builds mission in CombatFlite, exports as XML.
2. Editor (mission designer or pilot) imports CF XML into DCSWE profile.
3. Editor changes DCSWE profile as desired.
4. Editor exports profile as JSON file and provides to pilot(s).
5. Pilots enter information from JSON into jet via DCSWE “mission load” hotkey.

Exports can use the default settings in the CF XML export dialog. The mission designer
could elect to do per-flight XML exports if they choose. At minimum, the export should
include "Refernce Points" and "Targeted DMPIs".

# Converting From CombatFlite to DCSWE

There are two types of information in a CF mission that are of interest to DCSWE,

1. Waypoints
2. DMPI reference points

Each flight in a CF mission has a set of typed waypoints that are common to all ships
in the flight. CF supports several waypoint types including steer points, targets,
DMPI, etc. Further, target waypoints can be associated with a number of DMPI type
waypoints (note that DMPI waypoints are different from DMPI reference points).

DCSWE makes several assumptions about how missions are set up in CF,

1 Case is ignored in all names; that is, “Colt1-1” and “colt1-1” are the same callsign,
  “Enfield1” and “enfield1” refer to the same flight, etc.
2. Waypoint names include flight information as per the default CF behavior.
3. DMPI reference points names follow the DCSWE convention as discussed later.
4. Each DMPI waypoint is located at the *same* geographic location as a DMPI reference
   point (i.e., when placing a DMPI waypoint, they should be snapped to a DMPI reference
   point).
5. Multiple flights may target the same DMPI reference point.
6. Callsigns follow the standard “`[name][flight_number]-[ship_number]`” format; for example,
   “Enfield1-4”, “Colt3-2”, etc.

From the waypoints, DMPI reference points, and callsign, DCSWE builds a set of waypoints
for the mission for use by a ship with the specified callsign. At present, DCSWE only
generates WP and MSN waypoints when importing from CF.

## WP Generation

To build the set of DCSWE WP waypoints for a callsign, DCSWE selects all CF waypoints
that,

1. Have a waypoint type that is not DMPI.
2. Have a waypoint name that contains the callsign’s flight (an empty callsign matches
   waypoints with any name).

For example, the steer point waypoint with the name “Enfield1 PUSH” would be included in
any import for a ship with a callsign in the Enfield1 flight or in any import where the
callsign was not specified. Note that the mission designer in this case does not need to
take any special actions for (2) as, by default, CF includes the flight name in the
waypoint name.

## MSN Generation

DCSWE generates MSN waypoints from the DMPI reference points along with the DMPI
waypoints. The MSN waypoints correspond to targets and may include information such as
the weapon station whose weapon should be employed. These waypoints are a feature of
F/A-18C avionics and are not used by other airframes.

To build the set of DCSWE MSN waypoints for a callsign, DCSWE begins by identifying the
relevant candidate CF DMPI waypoints that may be included as DCSWE MSN waypoints. These
include all CF waypoints that,

1. Have a waypoint type of DMPI.
2. Have a waypoint name that contains the callsign’s flight (an empty callsign matches
   waypoints with any name).

In order to generate the DCSWE MSN waypoint, two further pieces of information are
needed that are not available in the candidate CF DMPI waypoints,

1. The ship(s) that target the DMPI.
2. The station that provides the weapon to employ on the target (as MSN waypoints are a
   feature of F/A-18C, the station may be: 8, 7, 3, or 2).

By convention, DCSWE expects the name of the CF DMPI reference point to provide this
information. This requires mission designers to ensure that all DMPIs that may appear in
the waypoint list for a ship have a name with the following format:

> `DMPI {number} [ss_list]`

where,

- `{number}` is the DMPI number.
- `[ss_list]` is an optional list of the ship(s) that target the DMPI and the station each
  ship uses, all ships in this list must belong to a flight from a CF DMPI waypoint that
  targets this DMPI reference point.

The default format for DMPI reference point names in CF is “DMPI {number}”. DCSWE
requires the addition of the `[ss_list]` to further specify how to convert the CF DMPI
waypoint into a MSN waypoint.

A `[ss_list]` is an optional list of elements separated by whitespace of the format:

> `{ships}[:{station}]`

where,

- `{ships}` specifies ship(s), either by flight name or callsign, and must match a flight
  from a CF DMPI waypoint at the same geographic location as the DMPI reference point.
- `{station}` is an optional station number (ignored if `{ships}` is a flight name instead of a full callsign), valid
  values are 8, 7, 3, or 2 with 8 being assumed if the station is not specified.

When specifying `{ships}`, DCSWE allows the use of “`*`” to prefix match on the name to cut
down on typing. Some examples of `{ships}` include,

- “`Enfield1`” refers to all ships in the Enfield1 flight.
- “`En*2`” refers to all ships in any #2 flight with a name beginning with “En” (e.g.,
  Enron2-3, Enfield2-2), this will not match a callsign like “Enfield12-1”.
- "`En*`" refers to all ships in any flight with a name beginning with “En” (e.g.,
  Enfiled1-1, Enfield2-3).
- “`Enfield1-4`” refers to ship 4 in the Enfield1 flight.
- “`En*2-3`” refers to ship 3 in any #2 flight with a name beginning with “En” (e.g.,
  Enron2-3, Enfield2-3), this will not match a callsign like “Enfield12-1”.

With the candidate CF DMPI waypoints and the CF DMPI reference points with appropriate
information in the name DCSWE can build the set of MSN waypoints for a callsign. First,
each candidate CF DMPI waypoint is correlated with a CF DMPI reference point by geographic
location. Multiple CF DMPI waypoints can be associated with a single CF DMPI reference
point (i.e., several flights might be tasked onto the same target). Once correlated, a
candidate CF DMPI waypoint will be included in the MSN waypoints for a callsign if the
callsign a ship from the ship list in the CF DMPI reference point associated with the CF
DMPI waypoint. There are several rules,

- An empty callsign matches any ship in the ship list; in this case, the station is
  always the default value, 8.
- A callsign may only match one element from the ship list, multiple matches constitute
  an error.
- Callsigns match flights and callsigns from the ship list in the expected ways.

For example, consider the following scenario with two three-ship Enfield1 flight and
two-ship Enfield2 flight,

> `CF DMPI Waypoint at L1 for flight “Enfield1”`<br>
> `CF DMPI Waypoint at L2 for flight “Enfield1”`<br>
> `CF DMPI Waypoint at L2 for flight “Enfield2”`<br>
> `CF DMPI Ref. Point at L1 with name “DMPI 1 Enfield1-1:7 Enfield1-2”`<br>
> `CF DMPI Ref. Point at L2 with name “DMPI 2 E*1 E*2-1:3”`<br>

Based on callsign, the following MSN waypoints would be generated when importing from
the XML generated from this CF mission,

- Empty Callsign: MSN at L1, station 8 (default); MSN at L2, station 8
- Enfield1-1: MSN at L1, station 7; MSN at L2, station 8
- Enfield1-2: MSN at L1, station 8; MSN at L2, station 8
- Enfield1-3: No MSN waypoints
- Enfield2-1: MSN at L2, station 3
- Enfield2-2: No MSN waypoints

MSN waypoints will appear with strike-through text on airframes that do not support
this type of waypoint.