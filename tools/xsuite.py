#!/usr/bin/env python3
"""Stage, publish and render OM0RX xSuite releases.

Standard library only (Python 3.9+), plus `git` and the GitHub CLI `gh`, so the
same tool runs on Windows, macOS and Linux build machines.

  xsuite.py stage   --app ID --version V --commit SHA (--source-repo PATH | --source-github OWNER/REPO)
                    [--from-release OWNER/REPO@TAG] [--notes FILE] [--date ISO] [ASSET ...]
  xsuite.py publish --tag TAG [--draft]
  xsuite.py render
  xsuite.py verify

`stage` collects the release files in staging/<tag>/, adds a GPL source zip of
the exact commit plus SHA256SUMS, and records the release in suite.json.
`publish` uploads a staged release to GitHub. `render` regenerates the
generated blocks in README.md and apps/*.md from suite.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform as host_platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "suite.json"
STAGING = Path(os.environ.get("XSUITE_STAGING", ROOT / "staging"))
SUITE_REPO = "oliverbross/OM0RX-xSuite"
DOWNLOAD_BASE = f"https://github.com/{SUITE_REPO}/releases/download"
RELEASE_PAGE = f"https://github.com/{SUITE_REPO}/releases/tag"
PLATFORMS = ("windows", "macos", "linux")
PLATFORM_LABEL = {"windows": "Windows", "macos": "macOS", "linux": "Linux"}


# --------------------------------------------------------------------------- helpers

def die(msg: str) -> None:
    sys.exit(f"xsuite: {msg}")


def gh_exe() -> str:
    for candidate in (os.environ.get("XSUITE_GH"), shutil.which("gh"),
                      os.path.expandvars(r"%LOCALAPPDATA%\Programs\gh\bin\gh.exe")):
        if candidate and Path(candidate).exists():
            return candidate
    die("GitHub CLI 'gh' not found (set XSUITE_GH)")
    return ""


def run(cmd: list[str], **kw) -> str:
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", **kw)
    if res.returncode != 0:
        die(f"command failed: {' '.join(cmd)}\n{res.stderr.strip()}")
    return res.stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(data: dict) -> None:
    data["updated"] = now_iso()
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def find_app(data: dict, app_id: str) -> dict:
    for app in data["apps"]:
        if app["id"] == app_id:
            return app
    die(f"unknown app '{app_id}' (known: {', '.join(a['id'] for a in data['apps'])})")
    return {}


def version_key(v: str):
    num, _, suffix = v.partition("-")
    nums = [int(x) if x.isdigit() else 0 for x in num.split(".")]
    tail = [int(x) if x.isdigit() else x for x in re.split(r"[.\-]", suffix)] if suffix else []
    return (nums, 0 if suffix else 1, [str(t).zfill(8) if isinstance(t, int) else t for t in tail])


# Non-download files that still belong on the release page.
EXTRA_PATTERNS = (r"^SHA256SUMS$", r"^PROVENANCE\.json$", r"^LICENSE$", r"^NOTICE$",
                  r"RELEASE-NOTES\.md$", r"\.sha256$", r"\.provenance\.json$", r"-source\.(zip|tar\.gz)$")


def classify(name: str) -> dict | None:
    """Describe a release file as a download, or None for checksums/notes/source."""
    low = name.lower()
    if any(re.search(p, name, re.I) for p in EXTRA_PATTERNS):
        return None
    if low.endswith(".exe") or low.endswith(".msi") or "windows" in low:
        platform = "windows"
    elif low.endswith(".dmg") or "macos" in low or "darwin" in low:
        platform = "macos"
    elif low.endswith((".deb", ".rpm", ".appimage")) or "linux" in low:
        platform = "linux"
    else:
        return None
    if "arm64" in low or "aarch64" in low:
        arch = "arm64"
    elif "universal" in low:
        arch = "universal"
    elif platform == "macos" and not re.search(r"x86_64|x64|intel", low):
        arch = "arm64"  # current Mac builds are Apple Silicon
    else:
        arch = "x86_64"
    if low.endswith(".tar.gz"):
        fmt = "tar.gz"
    elif low.endswith(".exe"):
        fmt = "nsis"  # overridden per app by "installer_format" in suite.json
    else:
        fmt = low.rsplit(".", 1)[-1]
    item = {"platform": platform, "arch": arch, "format": fmt}
    if "all-users" in low:
        item["variant"] = "all-users"
    elif "current-user" in low:
        item["variant"] = "current-user"
    return item


# --------------------------------------------------------------------------- stage

def source_zip(app: dict, version: str, commit: str, out: Path, repo_path: str | None,
               github: str | None) -> Path:
    stem = f"{app['name']}-{version}"
    target = out / f"{stem}-source.zip"
    if repo_path:
        repo = Path(repo_path)
    elif github:
        repo = STAGING / "_repos" / (github.split("/")[-1] + ".git")
        if not repo.exists():
            repo.parent.mkdir(parents=True, exist_ok=True)
            run(["git", "clone", "--bare", "--quiet", f"https://github.com/{github}.git", str(repo)])
        else:
            run(["git", "-C", str(repo), "fetch", "--quiet", "origin", "+refs/heads/*:refs/heads/*", "--tags"])
    else:
        die("give --source-repo or --source-github so the GPL source zip can be made")
    full = run(["git", "-C", str(repo), "rev-parse", "--verify", f"{commit}^{{commit}}"]).strip()
    run(["git", "-C", str(repo), "archive", "--format=zip", f"--prefix={stem}/", "-o", str(target), full])
    return target


# Material that must never appear in a public source archive. Kept deliberately
# strict (few false positives): home paths, private keys and real GitHub tokens.
PRIVATE = re.compile(rb"/Users/olive[r]/|/home/olive[r]/|[Cc]:[\\/]+Users[\\/]+(?:olive[r]|code[x])[\\/]|"
                     rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|"
                     rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b", re.I)


def privacy_scan(archive: Path) -> list[str]:
    """Return 'member: match' lines for private material inside a source archive."""
    import tarfile
    import zipfile
    hits = []

    def check(name: str, data: bytes) -> None:
        for m in PRIVATE.finditer(data):
            hits.append(f"{name}: {m.group(0)[:40].decode('utf-8', 'replace')}")
            break

    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                if not info.is_dir():
                    check(info.filename, z.read(info))
    else:
        with tarfile.open(archive) as t:
            for member in t.getmembers():
                if member.isfile():
                    check(member.name, t.extractfile(member).read())
    return hits


def cmd_stage(args) -> None:
    data = load_manifest()
    app = find_app(data, args.app)
    tag = f"{app['id']}-v{args.version}"
    out = STAGING / tag
    out.mkdir(parents=True, exist_ok=True)
    notes, date = "", args.date

    if args.from_release:
        repo, _, src_tag = args.from_release.partition("@")
        run([gh_exe(), "release", "download", src_tag, "-R", repo, "-D", str(out), "--skip-existing"])
        info = json.loads(run([gh_exe(), "release", "view", src_tag, "-R", repo, "--json", "body,publishedAt"]))
        notes = info.get("body") or ""
        date = date or info.get("publishedAt")
    for asset in args.assets:
        shutil.copy2(asset, out / Path(asset).name)
    if args.notes:
        notes = Path(args.notes).read_text(encoding="utf-8")

    existing_source = [p for p in out.iterdir() if re.search(r"-source\.(zip|tar\.gz)$", p.name)]
    src = existing_source[0] if existing_source else source_zip(
        app, args.version, args.source_ref or args.commit, out, args.source_repo, args.source_github)
    import fnmatch
    hits = privacy_scan(src)
    allowed = [h for h in hits if any(fnmatch.fnmatch(h.split(": ", 1)[0].split("/", 1)[-1], g) for g in args.allow)]
    for h in allowed:
        print(f"allowed after review: {h}")
    hits = [h for h in hits if h not in allowed]
    if hits:
        die(f"{src.name} contains private material; fix the source or use a curated --source-ref:\n  "
            + "\n  ".join(hits[:20]) + (f"\n  ... {len(hits) - 20} more" if len(hits) > 20 else ""))

    files = sorted(p for p in out.iterdir() if p.is_file() and p.name not in ("SHA256SUMS", "release-notes.md"))
    sums = {p.name: sha256(p) for p in files}
    (out / "SHA256SUMS").write_text("".join(f"{h}  {n}\n" for n, h in sums.items()), encoding="utf-8")

    if not (out / "PROVENANCE.json").exists():
        (out / "PROVENANCE.json").write_text(json.dumps({
            "product": app["name"], "version": args.version, "source_commit": args.commit,
            "staged": now_iso(), "staged_on": host_platform.node(),
            "files": {n: {"sha256": h, "bytes": (out / n).stat().st_size} for n, h in sums.items()},
        }, indent=2) + "\n", encoding="utf-8")

    origin = (f"public source snapshot `{args.source_ref[:12]}` of build commit `{args.commit[:12]}`"
              if args.source_ref and args.source_ref != args.commit else f"commit `{args.commit[:12]}`")
    footer = (f"\n\n---\n**Source code:** `{src.name}` is the complete source of this release"
              f" ({origin}), provided under GPL-3.0-only."
              f" Verify downloads with `SHA256SUMS`; build details are in `PROVENANCE.json`.\n")
    (out / "release-notes.md").write_text(notes.rstrip() + footer, encoding="utf-8")

    downloads = []
    for p in files:
        item = classify(p.name)
        if not item:
            continue
        if item["format"] == "nsis" and app.get("installer_format"):
            item["format"] = app["installer_format"]
        item.update(file=p.name, url=f"{DOWNLOAD_BASE}/{tag}/{p.name}", sha256=sums[p.name], size=p.stat().st_size)
        downloads.append(item)
    if app.get("source_is_download"):
        for platform in app["platforms"]:
            downloads.append({"platform": platform, "arch": "x86_64", "format": "source-zip", "file": src.name,
                              "url": f"{DOWNLOAD_BASE}/{tag}/{src.name}", "sha256": sums[src.name],
                              "size": src.stat().st_size})
    if not downloads:
        die(f"no installable downloads found in {out}")

    release = {
        "version": args.version, "tag": tag, "date": date or now_iso(),
        "notes": f"{RELEASE_PAGE}/{tag}", "source_commit": args.commit,
        **({"source_snapshot": args.source_ref} if args.source_ref and args.source_ref != args.commit else {}),
        "source": {"file": src.name, "url": f"{DOWNLOAD_BASE}/{tag}/{src.name}",
                   "sha256": sums[src.name], "size": src.stat().st_size},
        "downloads": sorted(downloads, key=lambda d: (PLATFORMS.index(d["platform"]), d.get("variant", ""), d["format"])),
    }
    app["releases"] = [r for r in app.get("releases", []) if r["tag"] != tag] + [release]
    app["releases"].sort(key=lambda r: version_key(r["version"]), reverse=True)
    save_manifest(data)
    print(f"staged {tag}: {len(files)} files in {out}, {len(downloads)} downloads recorded in suite.json")


# --------------------------------------------------------------------------- publish

def cmd_publish(args) -> None:
    data = load_manifest()
    out = STAGING / args.tag
    if not out.is_dir():
        die(f"nothing staged for {args.tag} ({out})")
    app = next((a for a in data["apps"] if any(r["tag"] == args.tag for r in a.get("releases", []))), None)
    if not app:
        die(f"{args.tag} is not in suite.json; run stage first")
    release = next(r for r in app["releases"] if r["tag"] == args.tag)
    files = [str(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "release-notes.md"]
    latest = app["releases"][0]["tag"] == args.tag
    cmd = [gh_exe(), "release", "create", args.tag, "-R", SUITE_REPO,
           "--title", f"{app['name']} {release['version']}",
           "--notes-file", str(out / "release-notes.md"), "--latest=false"]
    if args.draft:
        cmd.append("--draft")
    run(cmd + files)
    print(f"published {args.tag} ({len(files)} files){' as draft' if args.draft else ''}"
          f"{'; newest release of ' + app['name'] if latest else ''}")


# --------------------------------------------------------------------------- render

def latest_for(app: dict, platform: str):
    for rel in app.get("releases", []):
        items = [d for d in rel["downloads"] if d["platform"] == platform]
        if items:
            return rel, items
    return None, []


def preferred(items: list[dict]) -> dict:
    order = {"current-user": 0, "": 1, "all-users": 2}
    rank = {"nsis": 0, "inno": 0, "msi": 1, "dmg": 0, "deb": 0, "appimage": 1, "zip": 2, "tar.gz": 3, "source-zip": 4}
    return sorted(items, key=lambda d: (rank.get(d["format"], 9), order.get(d.get("variant", ""), 1)))[0]


def human_size(n: int) -> str:
    return f"{n / 1_000_000:.0f} MB" if n >= 1_000_000 else f"{n / 1000:.0f} kB"


FORMAT_LABEL = {"nsis": "installer", "inno": "installer", "msi": "installer", "dmg": "DMG", "zip": "ZIP",
                "deb": ".deb", "tar.gz": ".tar.gz", "appimage": "AppImage", "source-zip": "source ZIP"}


def download_label(d: dict) -> str:
    label = FORMAT_LABEL.get(d["format"], d["format"])
    if d.get("variant"):
        label += f" ({d['variant'].replace('-', ' ')})"
    return label


def apps_table(data: dict, prefix: str = "") -> str:
    rows = ["| | App | What it does | Windows | macOS | Linux |", "|---|---|---|:---:|:---:|:---:|"]
    for app in data["apps"]:
        cells = []
        for platform in PLATFORMS:
            if platform not in app["platforms"]:
                cells.append("—")
                continue
            rel, items = latest_for(app, platform)
            cells.append(f"[**{rel['version']}**]({preferred(items)['url']})" if rel else "soon")
        icon = f"<img src=\"{prefix}{app['icon']}\" width=\"40\" alt=\"\">" if app.get("icon") else ""
        rows.append(f"| {icon} | [**{app['name']}**]({prefix}{app['page']}) | {app['summary']} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def app_downloads(app: dict) -> str:
    lines = []
    for platform in PLATFORMS:
        if platform not in app["platforms"]:
            continue
        rel, items = latest_for(app, platform)
        if not rel:
            lines.append(f"- **{PLATFORM_LABEL[platform]}:** not published yet")
            continue
        links = " · ".join(f"[{download_label(d)}]({d['url']}) {human_size(d['size'])}"
                           for d in sorted(items, key=lambda d: preferred(items) is not d))
        lines.append(f"- **{PLATFORM_LABEL[platform]}** — {rel['version']}: {links}")
    return "\n".join(lines)


def app_history(app: dict) -> str:
    if not app.get("releases"):
        return "No releases yet."
    rows = ["| Version | Date | Platforms | Notes | Source |", "|---|---|---|---|---|"]
    for rel in app["releases"]:
        plats = ", ".join(PLATFORM_LABEL[p] for p in PLATFORMS if any(d["platform"] == p for d in rel["downloads"]))
        rows.append(f"| {rel['version']} | {rel['date'][:10]} | {plats} | [release notes]({rel['notes']}) | "
                    f"[source ZIP]({rel['source']['url']}) `{rel['source_commit'][:10]}` |")
    return "\n".join(rows)


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- xsuite:{name} -->)(.*?)(<!-- /xsuite:{name} -->)", re.S)
    if not pattern.search(text):
        die(f"marker <!-- xsuite:{name} --> not found")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", text)


def cmd_render(_args) -> None:
    data = load_manifest()
    readme = ROOT / "README.md"
    readme.write_text(replace_block(readme.read_text(encoding="utf-8"), "apps", apps_table(data)), encoding="utf-8")
    for app in data["apps"]:
        page = ROOT / app["page"]
        text = page.read_text(encoding="utf-8")
        text = replace_block(text, "downloads", app_downloads(app))
        text = replace_block(text, "history", app_history(app))
        page.write_text(text, encoding="utf-8")
    print(f"rendered README.md and {len(data['apps'])} app pages")


# --------------------------------------------------------------------------- verify

def cmd_verify(_args) -> None:
    data = load_manifest()
    problems = []
    if data.get("schema") != 1:
        problems.append("schema must be 1")
    seen = set()
    for app in data["apps"]:
        if app["id"] in seen:
            problems.append(f"duplicate app id {app['id']}")
        seen.add(app["id"])
        for key in ("name", "summary", "role", "platforms", "page"):
            if not app.get(key):
                problems.append(f"{app['id']}: missing {key}")
        if not (ROOT / app["page"]).exists():
            problems.append(f"{app['id']}: page {app['page']} missing")
        if app.get("icon") and not (ROOT / app["icon"]).exists():
            problems.append(f"{app['id']}: icon {app['icon']} missing")
        versions = [r["version"] for r in app.get("releases", [])]
        if versions != sorted(versions, key=version_key, reverse=True):
            problems.append(f"{app['id']}: releases not newest-first")
        for rel in app.get("releases", []):
            if not re.fullmatch(r"[0-9a-f]{40}", rel.get("source_commit", "")):
                problems.append(f"{rel['tag']}: source_commit must be a full SHA")
            for d in rel["downloads"] + [rel["source"]]:
                if not re.fullmatch(r"[0-9a-f]{64}", d.get("sha256", "")):
                    problems.append(f"{rel['tag']}: bad sha256 for {d.get('file')}")
                if not d["url"].startswith(f"{DOWNLOAD_BASE}/{rel['tag']}/"):
                    problems.append(f"{rel['tag']}: url outside its release: {d['url']}")
                if "platform" in d and d["platform"] not in app["platforms"]:
                    problems.append(f"{rel['tag']}: {d['file']} is for {d['platform']}, not listed for the app")
    if problems:
        die("verify failed:\n  " + "\n  ".join(problems))
    total = sum(len(a.get("releases", [])) for a in data["apps"])
    print(f"suite.json OK: {len(data['apps'])} apps, {total} releases")


# --------------------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stage", help="collect a release and record it in suite.json")
    s.add_argument("--app", required=True)
    s.add_argument("--version", required=True)
    s.add_argument("--commit", required=True, help="full source commit the binaries were built from")
    s.add_argument("--source-repo", help="local checkout containing the commit")
    s.add_argument("--source-github", help="OWNER/REPO to clone when no local checkout exists")
    s.add_argument("--source-ref", help="commit to archive as the public source when it differs from --commit "
                                        "(for example a curated public-source snapshot); recorded as source_snapshot")
    s.add_argument("--allow", action="append", default=[], metavar="GLOB",
                   help="accept privacy-scan hits in source files matching GLOB (path inside the archive) after review")
    s.add_argument("--from-release", help="copy files and notes from OWNER/REPO@TAG")
    s.add_argument("--notes", help="release notes (Markdown file)")
    s.add_argument("--date", help="release date (ISO 8601); default: source release date or now")
    s.add_argument("assets", nargs="*")
    s.set_defaults(func=cmd_stage)
    pb = sub.add_parser("publish", help="upload a staged release to GitHub")
    pb.add_argument("--tag", required=True)
    pb.add_argument("--draft", action="store_true")
    pb.set_defaults(func=cmd_publish)
    sub.add_parser("render", help="regenerate README.md and app pages").set_defaults(func=cmd_render)
    sub.add_parser("verify", help="check suite.json").set_defaults(func=cmd_verify)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
