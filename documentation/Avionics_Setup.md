# Avionics Setup

DCC Waypoint Editor (DCSWE) currently supports avionics setup for the F-16C Viper. This
allows DCSWE to setup the following state in the Viper's avionics:

- TACAN in yardstick mode
- Selected MFD formats for use in NAV, AA, AG, and DGFT master modes

As DCSWE cannot necessarily determine avionics state (e.g., it is difficult to determine
which MFD format is being displayed), DCSWE makes some assumptions around the initial
configuration of the avionics. If the state does not match the expected initial setup,
the configuration may not be correct.

> *NOTE:* This functionality will eventually be replaced by DTC support.

Avionics setup can be done as part of loading a profile or a mission (in DCSWE JSON
format) into the jet. It is not possible at present to set up the avionics through
non-native mission setups (e.g., CombatFlite). To setup the avionics while loading
a mission from a CombatFlite import, you could import the waypoints from CombatFlite
and use a separate profile (with no waypoints) to provide the avionics.

## TACAN Yardstick

The TACAN yardstick allows the user to specify a TACAN channel and a role (flight lead
or wingman) and will set up the TACAN appropriately. Yardsticks are setup with the
flight lead on channel C and the wingmen on channel C+63 (note that this implies that
legal channels for yardsticks are between 1 and 63). DCSWE handles the lead/wingman
channel modification automatically.

For example, if the UI sets up for a TACAN yardstick on 38Y, the flight lead or wingman
role will determine what is actually programmed into the jet,

- For a flight lead, the TACAN is set to channel 38Y in AA T/R mode.
- For a wingman, the TACAN is set to channel 101Y in AA T/R mode.

In both cases, the EHSI will be switched to TACAN mode.

For TACAN setup to work correctly, DCSWE expects the following initial conditions:

- TACAN band should be "X"
- TACAN operation mode should be "REC"
- EHSI mode should be "NAV"

The initial state of the Viper when powered on should match these requirements.

## MFD Formats

TODO

For MFD format setup to work correct, DCSWE expects the following initial conditions:

- Master mode should be NAV
- For all master modes that are to be updated, the current format on the left and right
  MFDs may not be the format mapped to OSB 12.
- The HOTAS DOGFIGHT switch `DOGFIGHT` position in DCS must be bound to `LCTRL+3`
- The HOTAS DOGFIGHT switch `CENTER` position in DCS must be bound to `LCTRL+4`

The initial state of the Viper when powered on should match these requirements.