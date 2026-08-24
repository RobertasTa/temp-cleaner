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
# Sprendimas: portable duomenys gyvena atskirame, PROGRAMOS VARDU PASIRASYTAME
# kataloge salia exe. Bendro tevo nebera is viso, tad susimaisyti nebeturi su
# kuo - nei su seserine dovana, nei su svetima programa flesiuke.
#
# --- VARDAI ANGLISKAI (Roberto klausimas 2026-08-24) ---------------------
# "tuos failiukus lietuviu kalba tik meskai supras, kitom kalbom kaip bus?"
# Rizika konkreti: flesiuko saknyje gulejo "_darbal" - kitakalbis jo
# nesupranta ir gali istrinti kaip siuksle. Failu vardai NIEKADA nesikeicia
# pagal sasajos kalba - jie tiesiog tampa tarptautiskai skaitomi. Kirilicos
# ar diakritiku varduose NENAUDOJAM NIEKADA (FAT32 + svetima koduote).
DATA_DIRNAME = "TempCleaner_data"          # portable duomenys salia exe

SENAS_DARBAL = "_darbal"                   # iki 2026-08-24: bendras su SDF
SENAS_PO_KATALOGIS = APP_DIRNAME           # tarpine forma: _darbal/TempCleaner

LOG_NAME = "cleaning_log.txt"              # buvo valymo_log.txt
_VARDAI = {_LOG_NAME: LOG_NAME}
_BENDRAVARDIS = "kalba.txt"
BENDRAVARDIS_NAUJAS = "language.txt"
KALBOS_FAILAS = BENDRAVARDIS_NAUJAS
_migruota = False   # migracija vykdoma viena karta per procesa


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
        return exe_dir() / DATA_DIRNAME
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_DIRNAME
    return exe_dir() / DATA_DIRNAME   # atsarga sistemoms be LOCALAPPDATA


def _senos_vietos():
    """Kur duomenys galejo guleti iki 2026-08-24 (portable rezime)."""
    if not is_portable():
        return []
    d = exe_dir()
    return [d / SENAS_DARBAL / SENAS_PO_KATALOGIS, d / SENAS_DARBAL]


def _perkelk(senas_kat, naujas_kat, musu_katalogas):
    """Perkelia musu failus is senos vietos i nauja, kartu pervadindamas.
    Bendrame kataloge bendravardis KOPIJUOJAMAS (ji dar turi rasti SDF)."""
    perkelta = 0
    for senas_v, naujas_v in _VARDAI.items():
        f = senas_kat / senas_v
        if f.is_file() and not (naujas_kat / naujas_v).exists():
            naujas_kat.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(naujas_kat / naujas_v))
            perkelta += 1
    for vardas in (_BENDRAVARDIS, BENDRAVARDIS_NAUJAS):
        k = senas_kat / vardas
        if k.is_file() and not (naujas_kat / BENDRAVARDIS_NAUJAS).exists():
            naujas_kat.mkdir(parents=True, exist_ok=True)
            if musu_katalogas:
                shutil.move(str(k), str(naujas_kat / BENDRAVARDIS_NAUJAS))
            else:
                shutil.copy2(str(k), str(naujas_kat / BENDRAVARDIS_NAUJAS))
            perkelta += 1
    return perkelta


def _pervadink_vietoje(katalogas):
    """Naujoje vietoje dar gali guleti seni vardai (%LOCALAPPDATA% atvejis:
    katalogas nesikeicia, keiciasi tik failu vardai)."""
    if not katalogas.is_dir():
        return 0
    pervadinta = 0
    pora = list(_VARDAI.items()) + [(_BENDRAVARDIS, BENDRAVARDIS_NAUJAS)]
    for senas_v, naujas_v in pora:
        if senas_v == naujas_v:
            continue
        f = katalogas / senas_v
        if f.is_file() and not (katalogas / naujas_v).exists():
            shutil.move(str(f), str(katalogas / naujas_v))
            pervadinta += 1
    return pervadinta


def migruoti_sena_darbal():
    """Vienkartinis perejimas i nauja vieta IR naujus (angliskus) vardus.

    Kvieciama paleidziant programa. Saugi bet kokioje busenoje:
    - senos vietos nera arba ji jau musiske - praleidziama;
    - SAVO failus PERKELIA, bendravardi is BENDRO katalogo KOPIJUOJA;
    - svetimu failu NELIECIA;
    - klaida (read-only flesiukas) nutylima: programa turi startuoti.
    """
    global _migruota
    if _migruota:
        return 0
    _migruota = True
    naujas = data_dir()
    perkelta = 0
    try:
        for i, senas in enumerate(_senos_vietos()):
            if senas == naujas or not senas.is_dir():
                continue
            perkelta += _perkelk(senas, naujas, musu_katalogas=(i == 0))
            if i == 0:
                try:
                    senas.rmdir()
                except OSError:
                    pass
        perkelta += _pervadink_vietoje(naujas)
        # Paskutinis iseinantis uzgesina sviesa: bendravardis kalba.txt
        # KOPIJUOJAMAS (kad kaimynas ji dar rastu), todel pats senas _darbal
        # niekada neistustetu ir liktu flesiuke amzinai - o butent to
        # nesuprantamo katalogo ir atsikratom. Todel: jei _darbal beturi TIK
        # ta viena bendravardi, vadinasi visi savo jau pasieme.
        if is_portable():
            senas_bendras = exe_dir() / SENAS_DARBAL
            try:
                if senas_bendras.is_dir():
                    likutis = [f.name for f in senas_bendras.iterdir()]
                    if likutis == [_BENDRAVARDIS]:
                        (senas_bendras / _BENDRAVARDIS).unlink()
                senas_bendras.rmdir()   # tik jei tuscias
            except OSError:
                pass
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
        src = data_dir() / LOG_NAME          # dabartine vieta (senas rezimas)
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
                (exe_dir() / DATA_DIRNAME).rmdir()   # tik jei tuscias
            except OSError:
                pass   # netuscias ar nera - paliekam
        return True, ""
    except OSError as e:
        return False, str(e)
