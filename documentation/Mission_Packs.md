# DCS Waypoint Editor Mission Packs

DCS Waypoint Editor can use mission packs to allow waypoints and kneeboard pages to
be setup with minimal interaction. In these packs, waypoints are set up using the
JSON or CombatFlite XML import capabilities of DCSWE while kneeboards are provided
as image files to be copied to the correct directory for use by DCS.

With a mission pack, a mission designer can provide a single `.zip` file to all
participating flights with waypoints and kneeboard pages relevant to the mission.
Each flight member can use DCSWE to install the appropriate information in to their
jet at startup.

## How to Create a Mission Pack

Building mission packs is straight forward. A mission pack is simply a .zip file with
the following structure:

> `{flight_directory_1}`<br>
> . . .<br>
> `{flight_directory_n}`<br>
> `{default_waypoints}`

where `{flight_directory_i}` is a directory named with the corresponding flight name
and `{default_waypoints}` is an optional JSON or XML file that specifies the waypoints
to set up. The only restriction on the default waypoints file is that it has a `.xml`
or `.json` extension; the name is otherwise unrestricted. In the event there are
multiple `.xml` or `.json` files, DCSWE will select the first and ignore the others.

Each flight directory is set up as follows:

> `{kneeboard_page_1}`<br>
> . . .<br>
> `{kneeboard_page_n}`<br>
> `{waypoints}`<br>

where `{kneeboard_page_i}` is a .png or .jpg file containing an image to add to the
kneeboard and `{waypoints}` is an optional JSON or XML file that specifies the waypoints
to set up. If present, `{waypoints}` always takes priority over `{default_waypoints}`.
The `{waypoints}` file has the same naming restrictions as the `{default_waypoints}`
file at the top level of the mission pack.

> **NOTE**: DCS appears to like its kneeboard pages in a 3:4 aspect ratio, with portrait
> orientation.

DCSWE uses the current callsign and airframe to determine which data to use. The callsign
deterines which `{flight_diretory_i}` to pull data from. The airframe determines which
subdirectory of the user's kneeboards to put the images.

The base name of the mission pack `.zip` file provides the name of the mission pack.
That is, the mission pack from "51st VFW Kish OCA.zip" has the name
"51st VFW Kish OCA".

**TODO:** More on mission packs interaction with avionics setup...

## Loading a Mission Pack

To load a mission pack from DCS Waypoint editor:

1. Make sure the proper airframe is selected from the airframe pulldown menu in the
   profile panel of the main DCS Waypoint Editor window.
2. Make sure the callsign is set appropriately in the main DCS Waypoint Editor window.
3. Select the mission package using the "Install Mission Package..." item from the
   "Missions" menu.
4. Use the "Load Profile into Jet" hotkey from DCS (`ctrl`-`alt`-`T` by default) or the
   DCS Waypoint Editor UI to enter the waypoint information from the mission package
   into your jet.

This will copy the appropriate kneeboard images from the mission package into the
directory `[DCS_Path]/Kneeboards/[airframe]` where `[DCS_Path]` is the location of
the DCS information in "Saved Games" (specified through the DCS Waypoint Editor
preferences) and `[airframe]` is the appropriate directory within the "Kneeboards"
directory based on the airframe you selected in step 1.

> A-10C Warthog = `A-10C`
> AV-8B Harrier = `AV8BNA`
> F-14A/B Tomcat = `F-14B`
> F-16C Viper = `F-16C_50`
> F/A-18C Hornet = `FA-18C_hornet`
> M-200C Mirage = `M-2000C`

The waypoints will be loaded from the appropriate file within the package and used to
populate a new profile named according to the mission package. This profile will be
selected.

## Example

For example, let's say the file "51st VFW Kish OCA.zip" has the following contents:

> `Enfield1`<br>
> `Enfield1/001-kboard-001.png`<br>
> `Enfield1/Enfield1_data.json`<br>
> `Colt1`<br>
> `Colt1/001-viper-001.png`<br>
> `Colt1/001-viper-002.png`<br>
> `51st VFW Kish OCA.xml`<br>

This mission package supports two flights: Enfield1 and Colt1. When loading any ship
from the Enfield1 flight, the `001-kboard-001.png` is copied into the appropriate
kneeboard directory and the `Enfield1_data.json` provides the data from which DCS
Waypoint Editor will build the waypoint information for a profile. When loading any ship
from the Colt1 flight, the two files `001-viper-001.png` and `001-viper-002.png` are
copied into the appropriate kneeboard directory and the `51st VFW Kish OCA.xml` file
provides the data from which DCS Waypoint Editor will build the waypoint information
for the profile since there is no XML or JSON file in the `Colt1` flight directory.