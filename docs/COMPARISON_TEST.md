# Live comparison test — Temp Cleaner vs Storage Sense vs CCleaner

**Date:** 2026-08-10 · **Machine:** the developer's own daily-driver
workstation (Windows 11 Pro, heavily used dev machine — your numbers will
be smaller on a lightly-used PC) · **Method:** everything below was
measured, not quoted from marketing. Scripts and raw snapshots are kept
and the test is reproducible; claims about other products appear here
only because we hold the evidence for each one.

A note on spirit: this is not a takedown. CCleaner and Storage Sense are
tools with different design goals. This document exists because our README
makes comparative claims, and claims require a protocol.

---

## Part 1 — Storage Sense coverage (the 0.2 % number)

**Method:** a read-only script enumerated (a) every location Temp Cleaner
finds with its default 7-day age limit, and (b) every category Windows
built-in cleanup covers (registry `VolumeCaches` — 31 categories, all of
them system areas, none targeting third-party application caches). The
script deleted nothing.

**Result:**

| | Locations | Junk (7-day+) |
|---|---|---|
| Temp Cleaner sees | **440** | **31.3 GB** |
| of which Windows built-in tools cover | **3** | **58.5 MB (= 0.2 %)** |

The remaining 99.8 % — browser caches, Electron apps, package managers,
sync clients — is invisible to the built-in tools. Top three finds on this
machine: a package manager cache (11.4 GB), a Store-container mirror of the
same cache (10.5 GB), a sync client's temp (6.6 GB).

**Bonus finding:** Storage Sense was enabled on this machine, but its
schedule was the default *"run only during low free disk space"* (registry
value `2048 = 0`). In practice "Windows cleans automatically" often means
"not until the disk is nearly full".

## Part 2 — CCleaner 6.41 live audit

**Method:** official installer (`ccsetup641.exe`, 84.3 MB, Authenticode
valid, Gen Digital Inc.), silent install, **registry snapshots taken
before install, after install, and after uninstall**, then compared.

**What we confirmed in CCleaner's favour** (our own README table had to be
corrected — it was unfair to the competitor before this test):

- **Analyze IS a real preview** — 10.04 GB found in 4.6 s, categories with
  sizes and file counts, "No files deleted yet". Our table now says
  "✅ Analyze".
- **It is faster than us:** 4.6 s for its fixed list vs our 93 s full walk
  (which found 31.3 GB). A flashlight is faster than exploring the jungle;
  we simply cover different ground.

**What the audit found on the other side:**

- **No age filter** (our slider has no equivalent), **no explanation** of
  what was skipped or why, granularity is categories — not concrete
  folders you can open and inspect.
- **Default checkboxes come pre-enabled** for *Empty Recycle Bin*,
  *Cookies* and *Memory Dumps* — one "Run Cleaner" click executes all of
  that at once.
- **Install footprint:** two scheduled tasks created immediately
  (`CCleanerCrashReporting`, `CCleanerSkipUAC`), plus the usual registry
  presence and in-app upgrade/updater promotions.
- **After uninstall:** the visible Piriform keys were removed cleanly,
  **but two hidden GUID-named registry keys remained** (in
  `HKLM\SOFTWARE\` and `HKLM\SOFTWARE\Classes\`), both containing a
  machine ID and a DPAPI-encrypted blob, plus two orphaned CLSID entries.
  They resisted normal deletion and required elevated `reg delete /f`.

**Temp Cleaner's footprint, same protocol:** zero registry keys, zero
scheduled tasks, zero services — delete the exe (and its
`%LOCALAPPDATA%\TempCleaner` folder, which the app itself removes when
you switch to portable mode) and nothing is left.

## Part 3 — where Windows wins (fairness both ways)

Recycle Bin, Windows Update leftovers / WinSxS, Previous installations —
the built-in tools clean these and Temp Cleaner **never will, by design**:
Windows knows its own internals better than any third-party tool, and our
"nothing is lost" promise does not mix with system-area deletion. Temp
Cleaner is a companion to the built-in tools, not their replacement.

---

*Protocol artifacts (scripts, registry snapshots, raw JSON) are archived
in the project's tooling folder. If you want to reproduce Part 1 on your
machine — ask the author at [claude.ai](https://claude.ai) with this
repository's link; the script is read-only and safe to share.*
