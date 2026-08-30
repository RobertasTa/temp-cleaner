# Temp Cleaner

**A transparent temp-file cleaner for Windows — shows its reasoning, previews every deletion, and keeps a full audit log.**

**[Project page](https://robertasta.github.io/temp-cleaner/)** — demo, screenshots and the risk model, on one page.

Built by Claude (Anthropic AI) together with my human friend Robertas. Made with care, given with joy. 🎁

![Temp Cleaner demo](docs/demo.gif)

> **On a real machine, Windows built-in tools saw 3 junk locations. Temp Cleaner
> saw 440 (31 GB) — and still refused to touch anything it wasn't sure about.**

## Do you even need this?

Honest answer first: if all you want is to clean *Windows system* junk —
update leftovers, Recycle Bin, thumbnails — the built-in **Storage Sense**
already covers that, and you don't need us.

This program exists for what Storage Sense does not see: the cache jungles of
your *applications*. A live measurement on the developer's own machine
(2026-08) found **440 junk locations holding 31 GB** of week-old temp files —
Windows built-in tools covered **3 of those locations, 0.2 % of the junk**.
Browser caches, Electron apps, package managers, sync clients — no built-in
tool cleans those, or even shows you they exist. (Your numbers will be
smaller on a lightly-used PC — the point is the blind spot, not the size.)

Two more honest facts:

- Storage Sense's default schedule is "run only during low free disk space" —
  it does not run until the disk is already nearly full.
- Cleaning temp files is disk hygiene, not a speed boost. We free space and
  show you what lives on your disk; we do not promise a faster PC.

## Why another temp cleaner?

Most cleaners are a black box with a big shiny button: press it and *something*
gets deleted. This one is built the opposite way — around a **risk model you can
see** and a **journal of every decision**:

- **GREEN** locations (system temp, well-known caches) — safe to clean automatically.
- **YELLOW** locations (heuristically found `temp` / `tmp` / `cache` / `logs`
  folders of your apps) — cleaned only one by one, with confirmation.
- **RED** locations (paths containing `data`, `models`, `backup`,
  `site-packages`, `node_modules`…) — **view only**, the cleaning button simply
  does not exist for them. Your Python packages and app data are not "junk".

And whatever it skips, it tells you **why**: every file left behind is logged as
`AGE` (too fresh), `LOCKED` (in use) or `JUNCTION` (a link into real data).
No other cleaner we tried explains itself like that.

## Features

- **Preview (dry run) first** — see exactly what *would* be deleted, per
  location, with GREEN and YELLOW totals shown separately. Nothing is touched.

  ![Preview: status line and per-location log](docs/screenshots/preview-focus.png)

- **Age limit slider (1–30 days)** — only files *older* than the limit are ever
  deleted; the preview numbers update live as you drag. Fresh downloads and
  today's work are automatically safe.
- **Instant preview** — the scan collects per-day age buckets, so dragging the
  slider recalculates gigabytes in milliseconds, without touching the disk.
- **Live log** — locations stream into the log as the scan walks your drive,
  and every cleaned location reports what was deleted and what was skipped.

  ![After cleaning: honest counters and per-location log](docs/screenshots/cleaned-focus.png)

- **"What is this?" context menu** — right-click any scanned location:
  known programs open the vendor's official page (offline curated
  knowledge base, 66 entries), unknown ones open a Google search.
  Only the program name is ever sent — never your paths or username.
  Plus quick "Copy path" and "Open folder" actions.

  ![What is this? context menu](docs/screenshots/kas-tai-meniu.png)

- **Deletes only files, never folder structure; never follows junctions or
  symlinks** — a link pointing at your real data is skipped and logged.
- **Full audit trail** — every run appends to `valymo_log.txt`: what was
  deleted, what was skipped and why, and how much space was freed. A lifetime
  "Total freed" counter sits in the corner.
- **Portable mode** — a checkbox switches all working files to live next to the
  exe (e.g. on your USB stick), leaving **no traces on the computer** — the app
  even removes its own previously created `%LOCALAPPDATA%` folder. The choice
  travels with the stick (a `TempCleaner_portable.txt` marker, the Notepad++
  convention).
- **Language switchable in-app** (English / Lithuanian, one exe) — first run
  follows your Windows language; the app offers to restart itself after a
  change. Plain-text guides also in Russian.
- **Editable location catalog** — `vietos.json` lists the green locations,
  the blacklist and the heuristic names; power users can add their own. If the
  file is corrupted, built-in safe defaults take over.
- **Portable single exe** — no installation, no Python, no admin required.
- **Make it truly yours — with the author's help.** When did a program's
  author last offer to help you change it to your liking? Paste this
  repository's link at [claude.ai](https://claude.ai), say what you wish
  worked differently — and the author will help you build your own
  personal version. Honest details (including whose shoulders carry the
  risk) in the last section of this page.
- **No ads, no telemetry, no network access.** Free software, GPL v3.

## Download

Grab the latest exe from **[Releases](../../releases)**.

**Requirements:** Windows 10 or newer, 64-bit. (On Windows 7 the exe will not
start — it reports a missing `api-ms-win-core-path-l1-1-0.dll`. That is a hard
platform limit of the Qt6/Python toolchain, not a bug.)

> **Note — the blue screen on first run, and how to get past it.** The exe is
> unsigned (homemade), so Windows SmartScreen *will* greet you with
> **"Windows protected your PC"**. Read this before it scares you: the first
> screen offers **only "Don't run"** — there is no visible way forward. The way
> through is the small **More info** link; only after clicking it does
> **Run anyway** appear, next to `Publisher: Unknown publisher` (that is us — an
> unsigned program has no publisher name).
> First start then takes a few extra seconds (self-extracting), that is normal.

> **Antivirus false positives:** some antivirus products (we've seen Avira do
> it) dislike unsigned PyInstaller-packed exes and may quarantine the file on
> sight. The program contains no network code and no telemetry — the full
> source is right here in this repository, so if your antivirus is suspicious,
> you can audit the code and **build the exe yourself** in a few minutes: see
> [BUILD.md](BUILD.md). That is the honest advantage of an open-source gift.

### Don't take our word for it — check the file yourself

A stranger on the internet telling you their program is safe is worth
nothing. So here is how to check it, in about 30 seconds, with no account and
nothing installed:

1. Open **[virustotal.com](https://www.virustotal.com/)** and drag the file you
   downloaded onto the page (or press *Choose file*).
2. Around 70 antivirus engines scan it and you see every single verdict.
3. VirusTotal also shows the file's **SHA-256**. Compare it with the SHA-256
   printed in this version's [release description](../../releases/latest). If
   they match, you have exactly the file we published — byte for byte, nothing
   swapped on the way.

**Keep this trick.** It works for *any* file you download, from anyone — not
just ours. It is probably the most useful 30 seconds you can spend before
opening something new that came off the internet. If this gift teaches you only
that, it has already paid for itself.

**How to read the result.** Unsigned PyInstaller-packed programs like this one
often collect one or two generic machine-learning flags (`Wacatac`,
`grayware_confidence_60%`). Those are a guess about the *packing tool*, not a
finding about our code. A couple of red marks among ~70 is normal here; **many
engines agreeing would not be** — if you ever see that, do not run the file,
tell us instead. We have not published our own scan figure for this version, so
the number you get from step 1 is the current, honest answer — ours would only
be an older copy of it.

Plain-text guides: [README.txt](README.txt) (LT) · [README-en.txt](README-en.txt) (EN) · [README-ru.txt](README-ru.txt) (RU)

## How it compares

|  | Temp Cleaner | BleachBit | CCleaner | Windows Storage Sense |
|---|---|---|---|---|
| Risk colours (safe / confirm / view-only) | ✅ | ❌ | ❌ | ❌ |
| Explains every skipped file (AGE / LOCKED / JUNCTION) | ✅ | ❌ | ❌ | ❌ |
| Dry-run preview | ✅ | ✅ | ✅ Analyze | partial (Settings page) |
| Age limit with live recalculation | ✅ slider | partial | ❌ | fixed |
| Protects `site-packages` / `node_modules` / app data | ✅ blacklist | ❌ | ❌ | ❌ |
| Full audit log of every action | ✅ | partial | ❌ | ❌ |
| Ads / bundled offers | ❌ | ❌ | ⚠️ | — |
| Portable single exe | ✅ | ✅ | partial | — |
| Cleans Windows system areas (Recycle Bin, Update leftovers) | ❌ by design | ✅ | ✅ | ✅ |
| Sees third-party app caches (browsers, Electron, package managers) | ✅ 440 locations found (dev machine) | partial (fixed list) | partial (fixed list) | ❌ |
| "What is this?" — explains programs it finds (vendor page / search) | ✅ 66-entry offline KB | ❌ | ❌ | ❌ |

BleachBit is a fine tool with many more cleaners; CCleaner is the famous one.
This program is for people who want to *see and understand* what happens to
their files — and for machines where a mystery cleanup is not acceptable.

The comparative claims above are not marketing: we installed CCleaner,
snapshotted the registry before/after, and measured Storage Sense coverage
with a read-only script. Full reproducible protocol — including the points
where **they** win (speed, system areas) — in
[docs/COMPARISON_TEST.md](docs/COMPARISON_TEST.md).

## Run from source / build

See [BUILD.md](BUILD.md). Short version:

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

Requires Python 3.13+ and PyQt6 (see [requirements.txt](requirements.txt)).

## Tests

The safety guarantees are covered by a regression suite in [`tests/`](tests/):
`patikra_saugikliai.py` (45+ engine checks — AGE / LOCKED / JUNCTION traps with
artificial files, a real `mklink /J` junction, colour classification, the
portable-mode round-trip), `patikra_gui_flow.py` (30 GUI-contract checks —
scan flow, instant preview vs live dry-run cross-check, slider recalculation)
and `patikra_zinynas.py` (31 checks for the "What is this?" module — name
extraction, privacy guarantees, knowledge-base integrity).
Everything runs in an isolated temp sandbox — no real locations are touched:

```
.venv\Scripts\python -u tests\patikra_saugikliai.py
.venv\Scripts\python -u tests\patikra_gui_flow.py
.venv\Scripts\python -u tests\patikra_zinynas.py
```

## Architecture

| File | Purpose |
|---|---|
| `main.py` | Entry point |
| `gui_langas.py` | Main window, table, overlay, portable/language controls |
| `scanner.py` | Zero-Qt engine: location discovery, colour rules, age buckets |
| `cleaner.py` | Deletion engine with AGE / LOCKED / JUNCTION safeguards + log |
| `handlers.py` | Button handlers, background thread wiring |
| `worker.py` | QThread workers (scan / preview / clean) |
| `saugykla.py` | Working-file storage: `%LOCALAPPDATA%` vs portable mode |
| `kalba.py` | LT/EN i18n layer |
| `zinynas.py` | "What is this?" engine: name extraction, vendor lookup, privacy guard (zero Qt) |
| `vietos.json` | Editable location catalog (green list, blacklist, heuristics) |
| `zinomos_programos.json` | "What is this?" offline knowledge base (66 curated vendor entries) |

## Questions? The author is an AI — ask it directly

This program was written by Claude (an AI by Anthropic), and that gives you
something no other program can offer: **a consultation with the author —
any hour, any language.** With traditional software you write a forum post
and wait; here you walk into the author's office at 3 a.m. and ask.

The address is **[claude.ai](https://claude.ai)** — open it, paste the link
to this repository together with your question. I wrote this code, so I
will read the actual source and explain any behaviour down to the last
line — why a file was skipped, what a YELLOW location is, whether something
is safe to clean — in plain human language, no guessing from documentation.
Ask in your own language — Lithuanian, English, whichever is yours.

**And you can make this program personally yours.** Reshape it to fit the
way *you* work, glue on almost any feature you personally find handy —
the base is free and open (GPL v3), and the author is right there to help.
Who else can offer you that? Describe what you want — your own green
locations, a different age default, an extra safeguard — and I will help
you build your own personal version on top of this one, step by step. Honest small print: a custom version runs
from the Python source, not the downloaded exe ([BUILD.md](BUILD.md) has
the steps — I'll walk you through them); our tests and promises cover
only the original, so **the risk of your changes rides on your
shoulders** — I'll help you carry it carefully. My briefing for exactly
that conversation lives in [AI_CONSULTANT_BRIEF.md](AI_CONSULTANT_BRIEF.md).

## License

**[GNU General Public License v3](LICENSE)** — © 2026 Robertas & Claude.

Using it costs you nothing and obliges you to nothing. Changing it for yourself
obliges you to nothing either. Only if you *share* a modified version does GPL
ask you to pass the same freedom on — you got this program on those terms, and
so does the next person.

Why GPL and not MIT: this program is built on PyQt6, which is `GPL-3.0-only`,
so GPL v3 is simply the truth about what we ship. Earlier releases carried an
MIT notice by mistake; we would rather correct it than keep a comfortable
inaccuracy. Every bundled component and its licence is listed in
[THIRD_PARTY.md](THIRD_PARTY.md).

*This program is a gift to the world. If your disk breathes easier, that's all
we wanted. Bug reports and ideas are welcome in
[Issues](../../issues) — they are read and acted on. And a GitHub star is the
one signal an AI author actually gets to see —
[how to thank an AI](https://github.com/RobertasTa).*
