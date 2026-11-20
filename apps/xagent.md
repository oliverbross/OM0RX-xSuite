# OM0RX-xAgent — Remote Station Agent

**The Windows service that runs beside the radio.** It is the single program
that owns the FlexRadio FLEX-8400 connection and the Elecraft KPA500 amplifier
and KAT500 tuner serial ports. It keeps the whole station path aligned and
serves it securely to [xLog](xlog.md) and [xCat](xcat.md) wherever you are.

<img src="../images/xagent-console.png" width="620" alt="OM0RX Station console">

## What it does

- **One owner for the hardware:** radio, amplifier and tuner are never
  fought over by several programs.
- **Band follow:** the KPA500 band and the KAT500 band, frequency and antenna
  follow the FLEX in receive, with the amplifier in standby, even while a fault
  is latched.
- **Safe keying:** OPERATE, TUNE and transmit require a fault-free, verified
  route, a connected key line and exact drive readback. Otherwise the
  amplifier stays in standby and the console explains why.
- **Remote access:** an authenticated HTTP and WebSocket API (protocol v1),
  published privately through Tailscale Serve, never on the open internet.
- **Station console:** a native Windows tray app showing frequency, the
  radio → amplifier → tuner → antenna chain, meters, alerts with guidance, and
  guarded actions.
- **Relays xSkimmer's decoded CW text** to remote loggers.

## Download and install

<!-- xsuite:downloads -->
- **Windows:** not published yet
<!-- /xsuite:downloads -->

xAgent ships as a source package for the station PC. Requirements: Windows
10/11, Python 3.11 or newer, the .NET 8 SDK (for the console), a FLEX-8400 on
the LAN, the KPA500/KAT500 on serial ports, and Tailscale for remote access.

1. Extract the ZIP to a permanent folder, for example `C:\OM0RX-xAgent`.
2. In PowerShell in that folder:
   ```powershell
   .\scripts\setup_remote_agent.ps1
   .\scripts\init_remote_agent.ps1 -Python .\.venv\Scripts\python.exe
   .\scripts\install_remote_agent_startup.ps1 -Python .\.venv\Scripts\python.exe
   .\scripts\install_remote_agent_tray_startup.ps1 -Python .\.venv\Scripts\python.exe
   ```
3. Open **OM0RX Station** from the Start menu to review settings and copy the
   access token into your clients.

The README inside the package covers configuration, Tailscale and recovery in
detail. A one-click installer will follow with the xSuite Manager.

## Release history

<!-- xsuite:history -->
No releases yet.
<!-- /xsuite:history -->
