# suite.json — the xSuite update manifest

`suite.json` at the top of this repository is the single machine-readable list
of every xSuite app and every published release. The README tables, the app
pages, each app's own "check for updates" and the future xSuite Manager all
read it. Nothing else needs to be kept in sync by hand.

Clients fetch it from:

```
https://raw.githubusercontent.com/oliverbross/OM0RX-xSuite/main/suite.json
```

It is written only by `tools/xsuite.py` (see [RELEASING.md](RELEASING.md)).

## Shape

```jsonc
{
  "schema": 1,
  "updated": "2026-11-20T12:00:00Z",          // last change, UTC
  "apps": [
    {
      "id": "xlog",                             // stable key, also the tag prefix
      "name": "OM0RX-xLog",
      "summary": "Local-first logbook ...",     // one sentence
      "role": "core",                           // core | companion | service
      "platforms": ["windows", "macos", "linux"],
      "page": "apps/xlog.md",
      "icon": "images/xlog-icon.png",
      "releases": [                             // newest first
        {
          "version": "1.6.74",
          "tag": "xlog-v1.6.74",
          "date": "2026-11-19T21:46:18Z",
          "notes": "https://github.com/oliverbross/OM0RX-xSuite/releases/tag/xlog-v1.6.74",
          "source_commit": "3a9abd5b00f5f619ecdfaa9536e592bc1a057752",
          "source": { "file": "...-source.zip", "url": "...", "sha256": "...", "size": 123 },
          "downloads": [
            {
              "platform": "windows",            // windows | macos | linux
              "arch": "x86_64",                 // x86_64 | arm64 | universal
              "format": "nsis",                 // nsis | inno | msi | zip | dmg | deb | tar.gz | appimage | source-zip
              "variant": "current-user",        // optional: current-user | all-users
              "file": "OM0RX-xLog-1.6.74-windows-x86_64-current-user-setup.exe",
              "url": "https://github.com/oliverbross/OM0RX-xSuite/releases/download/xlog-v1.6.74/...",
              "sha256": "...",
              "size": 61462638
            }
          ]
        }
      ]
    }
  ]
}
```

## Rules for clients

- **Latest for my machine** = the first entry in `releases` that has a
  `downloads` item for the client's `platform` (and `arch`, when it matters).
  Platforms can lag: for example xLog 1.6.74 is Windows-only, so macOS and Linux
  still resolve to 1.6.0.
- Compare versions as dotted numbers, with any suffix (`-xlog.17`) compared
  after the numeric part. Never downgrade.
- Always verify the downloaded file's `sha256` before running it.
- `format` tells an installer how to install silently:
  `nsis` → `/S`, `inno` → `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`,
  `zip` (macOS) → replace the `.app` in `/Applications`, `dmg` → mount and copy,
  `deb` → `apt install ./file.deb`, `source-zip` → follow the app page.
- Ignore unknown fields; `schema` changes only for breaking changes.
