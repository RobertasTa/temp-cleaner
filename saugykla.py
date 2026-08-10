"""saugykla.py - kur gyvena programos darbiniai failai (portable vs kompiuteris).

Roberto pastaba 3 (2026-08-06, laptopo testas): _darbal atsirasdavo ant
flesiuko salia exe - nenuosekliai su dubliu programa ir dyleta flash.

Pasaulio konvencija (Notepad++ doLocalConf.xml, VS Code data/): rezima
nustato ZYMEKLIO FAILAS salia exe - TempCleaner_portable.txt. Jis keliauja
kartu su flesiuku, tad ijungtas rezimas galioja visuose kompiuteriuose. GUI
ji valdo per matoma varnele (Roberto idejos ir konvencijos junginys).
Vardas prefiksuotas (ne portable.txt), kad dovanu seimos exe viename
aplanke neskaitytu vienas kito zymeklio (Roberto radinys 2026-08-07);
senas portable.txt dar skaitomas kaip fallback, bet neberasomas.

- zymeklio NERA (numatyta): darbiniai failai -> %LOCALAPPDATA%/TempCleaner.
  NE %TEMP% - programa pati ji valo ir susidegintu savo zurnala!
- zymeklis YRA: darbiniai failai -> _darbal salia exe (kompiuteryje
  pedsaku nelieka; zurnalas-auditas keliauja su flesiuku).
"""

import os
import shutil
import sys
from pathlib import Path

PORTABLE_MARKER = "TempCleaner_portable.txt"
PORTABLE_MARKER_OLD = "portable.txt"   # iki-publikacijos zymeklis: skaitomas, neberasomas
APP_DIRNAME = "TempCleaner"
_LOG_NAME = "valymo_log.txt"


def exe_dir():
    """Katalogas salia exe (frozen) arba salia .py failu (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def is_portable():
    d = exe_dir()
    return (d / PORTABLE_MARKER).exists() or (d / PORTABLE_MARKER_OLD).exists()


def data_dir():
    """Darbiniu failu katalogas pagal rezima (nekuriamas - kuria rasytojai)."""
    if is_portable():
        return exe_dir() / "_darbal"
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_DIRNAME
    return exe_dir() / "_darbal"   # atsarga sistemoms be LOCALAPPDATA


def set_portable(on):
    """Perjungia rezima: zymeklis + zurnalo perkelimas + pedsaku valymas.

    Ijungiant: TempCleaner_portable.txt sukuriamas (senas portable.txt,
    jei buvo, nuimamas - migracija i prefiksuota varda), zurnalas
    perkeliamas i _darbal salia exe, %LOCALAPPDATA%/TempCleaner istrinamas
    (pedsaku nelieka). Isjungiant: nuimami ABU zymekliai, zurnalas grizta
    i %LOCALAPPDATA%.
    Grazina (ok, klaidos_tekstas) - pvz., read-only flesiukas -> (False, ...).
    """
    marker = exe_dir() / PORTABLE_MARKER
    marker_old = exe_dir() / PORTABLE_MARKER_OLD
    try:
        src = data_dir() / _LOG_NAME          # dabartine vieta (senas rezimas)
        if on:
            marker.write_text("portable\n", encoding="utf-8")
            if marker_old.exists():
                marker_old.unlink()
        else:
            for m in (marker, marker_old):
                if m.exists():
                    m.unlink()
        dst_dir = data_dir()                  # nauja vieta (rezimas jau naujas)
        # Perkeliam VISUS darbinius failus (valymo_log.txt, kalba.txt...)
        if src.parent != dst_dir and src.parent.is_dir():
            dst_dir.mkdir(parents=True, exist_ok=True)
            for f in src.parent.iterdir():
                if f.is_file():
                    shutil.move(str(f), str(dst_dir / f.name))
        if on:
            # Pedsaku valymas: programa pati po saves susitvarko
            base = os.environ.get("LOCALAPPDATA")
            if base:
                shutil.rmtree(Path(base) / APP_DIRNAME, ignore_errors=True)
        else:
            # Tuscias _darbal salia exe nebereikalingas
            try:
                (exe_dir() / "_darbal").rmdir()
            except OSError:
                pass   # netuscias ar nera - paliekam
        return True, ""
    except OSError as e:
        return False, str(e)
