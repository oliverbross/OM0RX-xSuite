# OM0RX-xSkimmer

**A CW skimmer for FlexRadio and TCI radios.** It takes the radio's wideband
IQ, finds every CW signal, decodes each one with the DeepCW neural model, works
out who is calling CQ, and shows it all on a band map, a signal list and a spot
list.

![OM0RX-xSkimmer](../images/xskimmer-main.png)

## What it does

- **FlexRadio without using a receiver slot:** binds to SmartSDR or Maestro as
  an API client and skims that client's own panadapter through DAX IQ. Coverage
  follows your panadapter.
- **TCI radios:** SunSDR (ExpertSDR), ANAN (Thetis) and any radio behind
  AetherSDR's TCI server.
- **Click to tune:** click a signal in the list or band map to put your slice
  on it.
- **SDC-style spot verification:** copies required against MASTER.SCP, minimum
  S/N, re-spot interval, your own master file and blacklist.
- **Spots everywhere:** a local telnet server (RBN-style comments) for your
  logger, an optional remote DX cluster, and the radio's own panadapter.
- **Decoded text for xLog:** the copy of the signal you are tuned to appears
  in [xLog](xlog.md), locally or through [xAgent](xagent.md) for remote
  operation.
- **Callsign data that maintains itself:** MASTER.SCP, Club Log, LoTW activity
  and cty.dat download automatically and refresh daily.

## Download

<!-- xsuite:downloads -->
- **Windows:** not published yet
<!-- /xsuite:downloads -->

Requires Windows 10/11 x64 and a FlexRadio (SmartSDR or Maestro running) or a
TCI radio. The installer upgrades earlier OM0RX Skimmer versions in place and
keeps your settings.

## Release history

<!-- xsuite:history -->
No releases yet.
<!-- /xsuite:history -->
