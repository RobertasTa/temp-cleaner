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

# --- SEIMOS KOLIZIJA, ANTRA DALIS (Roberto radinys 2026-08-24) ------------
# 08-07 buvo prefiksuotas ZYMEKLIS, bet KATALOGAS liko bendras: ir sita
# dovana, ir Smart Duplicate Finder portable rezime rase i ta pati "_darbal"
# salia exe. Pasekmes flesiuke, kur guli abu exe:
#   1) abi rase "kalba.txt" tuo paciu vardu - kalba "nutekedavo" is vienos
#      programos i kita;
#   2) BLOGIAU: set_portable() perkeldavo VISUS is _darbal rastus failus i
#      savo %LOCALAPPDATA% kataloga - t. y. SDF issivesdavo musu valymo
#      zurnala (o jis yra AUDITAS, ka programa trine), arba mes - jo kesa.
# Sprendimas: portable duomenys gyvena PO-KATALOGE pagal programos varda -
# lygiai kaip %LOCALAPPDATA%\\TempCleaner. Struktura abiem rezimam vienoda.
DARBAL_DIRNAME = "_darbal"

# Musu darbiniai failai (migracijai is seno bendro _darbal).
# "kalba.txt" TYCIA cia nera - jis bendravardis su SDF, todel migruojamas
# KOPIJUOJANT: abi programos pasiima po kopija ir viena kitos nebeliecia.
_SAVI_FAILAI = (_LOG_NAME,)
_BENDRAVARDIS = "kalba.txt"
_migruota = False   # migracija vykdoma viena karta per procesa


def exe_dir():
    """Katalogas salia exe (frozen) arba salia .py failu (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def is_portable():
    d = exe_dir()
    return (d / PORTABLE_MARKER).exists() or (d / PORTABLE_MARKER_OLD).exists()


def _senas_darbal():
    """Iki-2026-08-24 bendra vieta, kuria dalinomes su Duplicate Finder."""
    return exe_dir() / DARBAL_DIRNAME


def data_dir():
    """Darbiniu failu katalogas pagal rezima (nekuriamas - kuria rasytojai)."""
    if is_portable():
        return exe_dir() / DARBAL_DIRNAME / APP_DIRNAME
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_DIRNAME
    # atsarga sistemoms be LOCALAPPDATA - ta pati po-katalogo struktura
    return exe_dir() / DARBAL_DIRNAME / APP_DIRNAME


def migruoti_sena_darbal():
    """Vienkartinis perkelimas is bendro _darbal i _darbal/TempCleaner.

    Kvieciama paleidziant programa. Saugi bet kokioje busenoje:
    - jei seno katalogo nera arba jis jau musiskis - nedaro nieko;
    - SAVO valymo zurnala PERKELIA, bendravardi kalba.txt KOPIJUOJA;
    - svetimu failu NELIECIA;
    - klaida (read-only flesiukas) nutylima: programa turi startuoti.

    Grazina perkeltu failu skaiciu (0 - nebuvo ko).
    """
    global _migruota
    if _migruota:
        return 0
    _migruota = True
    senas = _senas_darbal()
    naujas = data_dir()
    if senas == naujas or not senas.is_dir():
        return 0
    perkelta = 0
    try:
        for vardas in _SAVI_FAILAI:
            f = senas / vardas
            if f.is_file() and not (naujas / vardas).exists():
                naujas.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(naujas / vardas))
                perkelta += 1
        k = senas / _BENDRAVARDIS
        if k.is_file() and not (naujas / _BENDRAVARDIS).exists():
            naujas.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(k), str(naujas / _BENDRAVARDIS))
            perkelta += 1
    except OSError:
        pass
    return perkelta


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
            # Isjungiant portable: nuimam SAVO po-kataloga, o bendra _darbal
            # tik tuomet, jei jame nebeliko nieko - ten gali gyventi kitos
            # dovanos duomenys (Roberto radinys 2026-08-24).
            try:
                (exe_dir() / DARBAL_DIRNAME / APP_DIRNAME).rmdir()
            except OSError:
                pass
            try:
                (exe_dir() / DARBAL_DIRNAME).rmdir()
            except OSError:
                pass   # netuscias ar nera - paliekam
        return True, ""
    except OSError as e:
        return False, str(e)
