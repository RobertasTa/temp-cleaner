"""models.py - Data classes and constants for Temp Cleaner."""

from dataclasses import dataclass


@dataclass
class Candidate:
    """A single discovered temp/cache location to scan or clean."""
    path: str
    file_count: int = 0
    total_bytes: int = 0
    color: str = "GELTONA"  # ZALIA, GELTONA, ZYDRA, RAUDONA
    # ZYDRAI eilutei - KODEL ji zydra (raktas is ZYDROS_PRIEZASTYS).
    # Sviesoforas lieka trims spalvoms = ka PROGRAMA siulo daryti.
    # Zydra = programa NESIULO nieko, tik parodo; sprendzia zmogus.
    zydra_del: str = ""
    # Amziaus kibireliai (2026-08-05 greitinimas): 31 pozicija - failu
    # skaicius/baitai pagal amziu dienomis (0..29, paskutinis 30+).
    # Uzpildomi skeno metu -> Perziura tampa aritmetika be disko.
    age_files: list = None
    age_bytes: list = None


# --- vietos.json zinynas (kaip pletiniai.json dubliu programoj) ---------------
# Numatytos reiksmes lieka kode kaip ATSARGA - jei vietos.json nera ar
# sugadintas, programa veikia kaip anksciau. Kintamuju vardai nekeiciami,
# scanner/cleaner ju importai lieka tie patys.

_DEFAULT_GREEN_RELATIVES = [
    "",                             # -> TEMP (index 0)
    "",                             # -> WINTEMP (index 1)
    r"NVIDIA/DXCache",             # -> LOCALAPPDATA (index 2)
    r"pip/cache",                  # -> LOCALAPPDATA (index 2)
    r"Google/Chrome/User Data/Default/Cache",  # -> LOCALAPPDATA (index 2)
]
_DEFAULT_GREEN_BASE_INDEX = [0, 1, 2, 2, 2]
_DEFAULT_BLACKLIST = {"models", "data", "profiles", "backup", "save", "config",
                      "site-packages", "node_modules"}
_DEFAULT_HEURISTIC = {"temp", "tmp", "cache", "logs"}
_DEFAULT_AGE_DAYS = 7

# Kodel radinys zydras. Raktai keliauja i kalba.py vertimus; tvarka = prioritetas,
# nes viena vieta gali atitikti kelis pozymius (pvz. Synology temp yra IR
# sinchronizacijos aplankas, IR naudojamas dabar).
ZYDROS_PRIEZASTYS = ("NAUDOJAMA_DABAR", "SINCHRONIZACIJA", "MOKAMA_PROGRAMA",
                     "SENOS_VERSIJOS")

# Vardu sarasai zydroms priezastims. SAMONINGAI nepilni: pasakom tai README,
# o ne apsimetam, kad atpazistam viska. Bendrinis pozymis (NAUDOJAMA_DABAR)
# jokio saraso nereikalauja ir pagauna tai, ko sarasuose nera.
_DEFAULT_SINCHRONIZACIJA = {"synologydrive", "onedrive", "dropbox", "google drive",
                            "googledrive", "yandexdisk", "nextcloud", "owncloud",
                            "mega", "pcloud", "icloud", "icloud drive"}
_DEFAULT_MOKAMOS = {"autodesk", "inventor", "adobe", "solidworks", "corel",
                    "jetbrains", "altium", "ansys", "matlab", "vmware",
                    "bentley", "siemens", "dassault", "ptc", "zwsoft"}
# Kiek NAUJAUSIU programos versiju paliekama, kai randam versijuotus katalogus.
_DEFAULT_PALIKTI_VERSIJU = 2


_BASE_NAME_TO_INDEX = {"TEMP": 0, "WINTEMP": 1, "LOCALAPPDATA": 2}


def _vietos_json_path():
    """PyInstaller guard Rule 4: frozen rezime data failai gyvena _MEIPASS."""
    import os
    import sys
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "vietos.json")


def _load_vietos():
    """Skaito vietos.json; bet kokia klaida -> numatytos reiksmes (atsarga)."""
    import json
    try:
        with open(_vietos_json_path(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        rels = []
        idxs = []
        for item in data["zalios_vietos"]:
            base_idx = _BASE_NAME_TO_INDEX[item["baze"].upper()]
            rels.append(item.get("kelias", ""))
            idxs.append(base_idx)
        blacklist = {str(w).lower() for w in data["juodasis_sarasas"]}
        heuristic = {str(w).lower() for w in data["heuristiniai_vardai"]}
        age = int(data.get("amzius_dienomis", _DEFAULT_AGE_DAYS))
        if not rels or not blacklist or not heuristic or not (1 <= age <= 365):
            raise ValueError("tuscios sekcijos ar blogas amzius")
        # Zydros sekcijos NEBUTINOS: senas vietos.json be ju veikia toliau.
        sync = ({str(w).lower() for w in data.get("sinchronizacijos_vardai", [])}
                or _DEFAULT_SINCHRONIZACIJA)
        mok = ({str(w).lower() for w in data.get("mokamu_programu_vardai", [])}
               or _DEFAULT_MOKAMOS)
        palikti = int(data.get("palikti_versiju", _DEFAULT_PALIKTI_VERSIJU))
        return rels, idxs, blacklist, heuristic, age, sync, mok, max(1, palikti)
    except Exception:
        return (_DEFAULT_GREEN_RELATIVES, _DEFAULT_GREEN_BASE_INDEX,
                _DEFAULT_BLACKLIST, _DEFAULT_HEURISTIC, _DEFAULT_AGE_DAYS,
                _DEFAULT_SINCHRONIZACIJA, _DEFAULT_MOKAMOS, _DEFAULT_PALIKTI_VERSIJU)


(GREEN_RELATIVES, GREEN_BASE_INDEX, BLACKLIST_NAMES,
 HEURISTIC_NAMES, AGE_DAYS, SINCHRONIZACIJOS_VARDAI,
 MOKAMU_VARDAI, PALIKTI_VERSIJU) = _load_vietos()

# Row colours for the table background (QColor '#RRGGBB')
# ZYDRA (2026-09-12): ketvirta spalva. Sviesoforas lieka trims = ka programa SIULO;
# zydra = programa nesiulo nieko, tik parodo, ir i "Valyti viska" nepatenka NIEKADA.
# Sviesi, kad juodas tekstas ant jos matytusi (visi kiti fonai irgi sviesus).
COLOR_HEX = {
    "ZALIA": "#aaffaa",
    "GELTONA": "#ffffaa",
    "ZYDRA": "#aae6ff",
    "RAUDONA": "#ffaaff",
}

@dataclass
class LogEntry:
    """One line in the cleaning log."""
    operation: str       # DELETED or SKIPPED
    path: str
    reason: str = ""     # for SKIPPED: AGE, LOCKED, JUNCTION
    size_bytes: int = 0
