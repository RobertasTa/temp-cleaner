# Third-party components and why this program is GPL v3

Temp Cleaner
Copyright (C) 2026 Robertas & Claude (Anthropic AI)

This program is free software: you can redistribute it and/or modify it under
the terms of the **GNU General Public License, version 3**, as published by the
Free Software Foundation. See [LICENSE](LICENSE) for the full text.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

**Complete source code** for this program — including every version ever
released — is available at <https://github.com/RobertasTa/temp-cleaner>.

## What this means for you

- **Using the program: no obligations at all.** Download it, run it, use it at
  home or at work. GPL restricts distribution, never use.
- **Changing it for yourself: no obligations either.** Build your own version,
  add what you need, keep it on your own machine. The author actively helps
  with this — see [AI_CONSULTANT_BRIEF.md](AI_CONSULTANT_BRIEF.md).
- **Sharing your changed version: pass the freedom on.** If you distribute a
  modified copy, it must also be GPL v3 and its source must be available. You
  received this program under those terms; the next person gets the same deal.

## Why GPL v3 and not something more permissive

Not a philosophical choice — an honest one. This program is built on **PyQt6**,
which its authors (Riverbank Computing) license as `GPL-3.0-only` unless you buy
a commercial licence. A program that ships GPL v3 code inside a single
executable must itself be distributed under GPL v3. Earlier releases of this
program carried an `MIT` notice; that notice was simply wrong, and this file
exists because we would rather correct it than keep a comfortable inaccuracy.

The licence text says "version 3" without "or any later version", because
PyQt6 is `GPL-3.0-only` — we cannot grant more freedom than we ourselves
received.

Nothing about the program itself changed. Not one byte. Only the label on it
is now accurate.

## Components bundled in the released executable

This program is deliberately lean — the graphical interface is the only
external dependency. Everything else is the Python standard library.

| Component | Licence | What it does here |
|---|---|---|
| [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) | GPL-3.0-only | The entire graphical interface |
| [PyQt6-Qt6](https://www.qt.io/) (Qt libraries) | LGPL v3 | Qt itself, underneath PyQt6 |
| [PyQt6-sip](https://www.riverbankcomputing.com/software/sip/) | BSD-2-Clause | C++/Python binding layer |

Each of these is somebody else's good work, doing a job we did not have to
solve ourselves. That is what open source is for, and this list is how we say
thank you.

## Python itself

The released executable is packaged with [PyInstaller](https://pyinstaller.org/)
(GPL-2.0-with-exception, which explicitly permits packaging programs under any
licence) and embeds [CPython](https://www.python.org/) (PSF Licence).

---

If you spot an error in this file — a wrong licence, a missing component —
please open an issue. We would rather be corrected than be wrong.
