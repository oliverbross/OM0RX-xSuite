# Publishing a release to xSuite

Every app is built from its own (private) repository. A finished build is
published here with `tools/xsuite.py`, which needs Python 3.9+, `git` and an
authenticated GitHub CLI (`gh auth status`). It works the same on Windows,
macOS and Linux.

## 1. Stage

From the xSuite checkout, after building and recording provenance in the app's
own repository:

```sh
python tools/xsuite.py stage --app xlog --version 1.6.78 \
    --commit <full source commit> --source-repo ../OM0RX-xLog \
    --notes ../OM0RX-xLog/docs/releases/1.6.78.md \
    path/to/OM0RX-xLog-1.6.78-windows-x86_64-current-user-setup.exe \
    path/to/OM0RX-xLog-1.6.78-windows-x86_64-all-users-setup.exe \
    path/to/PROVENANCE.json
```

- `--commit` must be the exact commit the binaries were built from. The tool
  makes `<App>-<version>-source.zip` from that commit with `git archive`. This
  is the GPL source offer, so never stage a build from a dirty tree.
- Use `--source-github oliverbross/<repo>` instead of `--source-repo` when the
  repository is not checked out on this machine.
- `--from-release OWNER/REPO@TAG` copies the files and notes of an existing
  GitHub release instead of listing files by hand.
- Files go to `staging/<app>-v<version>/` (git-ignored), with `SHA256SUMS`,
  `PROVENANCE.json` (kept if you supplied one) and `release-notes.md`.
  `suite.json` gets the new release entry.

Several platforms of the same version (for example Windows today, macOS from
the Mac tomorrow) can be staged into the same tag. Run `stage` again with the
extra files, then publish or upload them.

## 2. Render and check

```sh
python tools/xsuite.py render    # refresh README.md and apps/*.md tables
python tools/xsuite.py verify    # sanity-check suite.json
```

Review `git diff` and the staged notes.

## 3. Publish

```sh
python tools/xsuite.py publish --tag xlog-v1.6.78        # add --draft to check first
git add suite.json README.md apps && git commit -m "Publish OM0RX-xLog 1.6.78" && git push
```

Publish the GitHub release **before** pushing `suite.json`: the manifest must
never point at files that do not exist yet. Adding files to an already
published tag: `gh release upload <tag> <files> -R oliverbross/OM0RX-xSuite`,
after staging them so `suite.json` and `SHA256SUMS` include them.

## Rules

- Never reuse a version for different binaries; never replace a published file.
- Every release carries its source ZIP, `SHA256SUMS` and `PROVENANCE.json`.
- Screenshots and notes are public: no tokens, private paths, server addresses
  or personal logbook contents.
