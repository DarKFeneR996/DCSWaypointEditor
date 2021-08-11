# Avionics Setup

DCC Waypoint Editor (DCSWE) currently supports avionics setup for the F-16C Viper. The
following state, in addition to waypoints, in the Viper's avionics can be set up:

- TACAN, in yardstick mode
- MFD formats for use on the left and right MFDs in NAV, AA, AG, and DGFT master modes

At present, this support is specific to the Viper. As other airframes may have some
analogous state, we may extend the support in the future.

> **NOTE:** This functionality will eventually be replaced by DCS DTC support if and
> when ED makes that happen.

Because DCSWE cannot always determine avionics state (e.g., it is difficult to determine
which MFD format is currently selected), DCSWE makes some assumptions, detailed below,
around the initial configuration of the avionics.

> **NOTE:** If the state does not match the expected initial configuration, the updates
> that DCSWE performs may not yield the desired results.

Avionics setup can be done as part of loading a profile or a mission (in DCSWE JSON
format) into the jet. For non-native mission setups (e.g., CombatFlite), you can either
import into a native DCSWE profile and set the avionics setup, or tell DCSWE to use a
default avionics setup (through preferences) when configuring the jet using non-native
sources.

As with waypoint entry, it is important to minimize interactions with the jet while
DCSWE is driving the cockpit switches.

## TACAN Yardstick

The TACAN yardstick support allows the user to specify a TACAN channel and a role
(flight lead or wingman) and will set up the TACAN appropriately. Yardsticks are set
up with the flight lead on channel C and the wingmen on channel C+63 (note that this
implies that legal channels for yardsticks are between 1 and 63, though legal TACAN
channels are between 1 and 126). DCSWE handles the lead/wingman channel modification
automatically.

For example, if the user configures the DCSWE UI to set up a TACAN yardstick on 38Y,
the flight lead or wingman role selected in the UI will determine what is actually
programmed into the jet,

- For a flight lead, the TACAN is set to channel 38Y in AA T/R mode.
- For a wingman, the TACAN is set to channel 101Y in AA T/R mode.

In both cases, the EHSI will be also switched to TACAN mode so you can check DME to
see if the yardstick is sweet or sour.

For TACAN setup to work correctly, DCSWE expects the following initial conditions in
the Viper:

- TACAN band should be "X"
- TACAN operation mode should be "REC"
- EHSI mode should be "NAV"

The initial state of the Viper in DCS when the jet is either powered up from a cold
start or running following a hot start should match these requirements.

## MFD Formats

Each MFD on the Viper can display one of three formats (e.g., FCR, TGP, HSD) that are
selected by OSB 12, 13, and 14 on the MFD. The formats are tied to the current master
mode (NAV, AA, AG, DGFT) allowing each master mode to have its own unique setup of MFD
formats. DCSWE provides the ability to change the MFD format configuration from the
defaults that DCS selects.

> **NOTE:** DCSWE assumes that all DGFT submodes (e.g., `DOGFIGHT`, `MISSILE OVERRIDE`)
> share the same MFD formats.

DCSWE allows per-master-mode selection of format sets to update. That is, you can update
only DGFT while leaving the other setups in their default configuration.

For MFD format setup to work correct, DCSWE expects the following initial conditions in
the Viper:

- Master mode should be NAV
- For all master modes that are to be updated, the current format selected on the left
  and right MFDs may not be whatever format is mapped to OSB 12
- The HOTAS DOGFIGHT switch `Cycle` command in DCS must be bound to the hotkey
  specified in the DCSWE preferences
- DCS must be in the foreground so that it can recieve key presses

The initial state of the Viper in DCS when the jet is either powered up from a cold
start or running following a hot start should match these requirements.

## Preferences

There are four preferences that control the behavior of the avionics setup functionality.

- *Default Avionics Setup:* Specifies the default avionics setup to use when creating new
  profiles, the setup "DCS Default" corresponds to the default setup of the jet in DCS.
  For airframes other than the Viper, this setting is effectively always "DCS Default".
- *Use When Setup Unknown:* When set, this preference causes DCSWE to use the default
  avionics setup in situations where it does not have information on the avionics setup.
  For example, if this is set, a profile created from CombatFlite would use the default
  setup. When not set, DCSWE does not change avionics setup (i.e., it behaves as if the
  default were "DCS Default")
- *F-16 HOTAS DOGFIGHT Cycle:* Specifies the keybind for the `Cycle` command on the
  HOTAS DGFT switch, the keybind should use at least one of `shift`, `alt`, or `ctrl`.
  The keybind should be specified keeping in mind that DCS uses specific modifiers
  (left or right `shift`, for example).

These can be set throught the DCSWE preferences, strangely enough. Note that the
`Cycle` hotkey will need to also be set up through the control options in DCS
(specifically, see the HOTAS section in the "F-16C Sim" controls).