# -*- coding: utf-8 -*-
"""diskas.py - disko vietos SASKAITU SUVEDIMAS (v1.3 skirtukas "Diskas").

Kodel sis modulis egzistuoja
---------------------------
Apie disko vieta yra KETURI nepriklausomi saltiniai, ir jie nieko nezino vienas
apie kita: pats diskas, skaidiniu lentele, failu sistema ir failu skenavimas.
Kiekviena programa rodo VIENA is ju ir tyli apie kitus tris.

Patikrinta 2026-09-13 skaitant WinDirStat saltini (GPL, `Item.Extended.cpp:711`):
jie palygina TIK du saltinius (failu sistema <-> ju pacius suskaiciuota) ir
skirtuma rodo kaip `<Unknown>`. Disko ir skaidinio lygio jie NELIECIA -
dirba su tomais, ne su fiziniu disku. Cia ir yra musu dalis.

⛔ Sis modulis NIEKO NEKEICIA. Tik skaito.

Teisiu klausimas (pamatuota, ne spėta)
--------------------------------------
Visi cia naudojami IOCTL veikia BE ADMIN, jei irenginys atidaromas su NULINE
prieiga (`dwDesiredAccess = 0`) - metaduomenu uzklausa duomenu neskaito.
Su `GENERIC_READ` tie patys kvietimai duoda ACCESS_DENIED.

Du ctypes spastai, del kuriu sitas failas atrodo keistai:
  1. `CreateFileW.restype` BUTINAS. Be jo ctypes grazina 32 bitu int, 64 bitu
     sistemoje rankena nukerpama, ir visi DeviceIoControl duoda klaida 6
     (INVALID_HANDLE) - atrodo kaip teisiu problema, bet nera.
  2. `IOCTL_DISK_GET_LENGTH_INFO` duoda klaida 5 net su nuline prieiga.
     Tomo dydis imamas is GetDiskFreeSpaceExW.
"""

import ctypes
import os
import string
from ctypes import wintypes

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)

_k32.CreateFileW.restype = wintypes.HANDLE
_k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                             ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                             wintypes.HANDLE]
_k32.DeviceIoControl.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
                                 wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD,
                                 ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
_k32.CloseHandle.argtypes = [wintypes.HANDLE]

_INVALID = ctypes.c_void_p(-1).value
_FILE_SHARE_RW = 0x00000003
_OPEN_EXISTING = 3

IOCTL_DISK_GET_DRIVE_GEOMETRY_EX = 0x000700A0
IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS = 0x00560000
IOCTL_DISK_GET_PARTITION_INFO_EX = 0x00070048

DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3

# Nesutapimo tipai (raktai i paaiskinimus ir i vertimus)
NS_UZ_SKAIDINIO = "uz_skaidinio"      # diskas > skaidiniu suma
NS_TOMAS_MAZESNIS = "tomas_mazesnis"  # skaidinys > tomas, kuri mato failu sistema


class _DISK_EXTENT(ctypes.Structure):
    _fields_ = [("DiskNumber", wintypes.DWORD),
                ("StartingOffset", ctypes.c_longlong),
                ("ExtentLength", ctypes.c_longlong)]


class _VOLUME_DISK_EXTENTS(ctypes.Structure):
    _fields_ = [("NumberOfDiskExtents", wintypes.DWORD),
                ("Extents", _DISK_EXTENT * 16)]


class _DISK_GEOMETRY(ctypes.Structure):
    _fields_ = [("Cylinders", ctypes.c_longlong), ("MediaType", wintypes.DWORD),
                ("TracksPerCylinder", wintypes.DWORD),
                ("SectorsPerTrack", wintypes.DWORD),
                ("BytesPerSector", wintypes.DWORD)]


class _DISK_GEOMETRY_EX(ctypes.Structure):
    _fields_ = [("Geometry", _DISK_GEOMETRY), ("DiskSize", ctypes.c_longlong),
                ("Data", ctypes.c_byte * 1)]


# ------------------------------------------------------------------
# Zemas lygis
# ------------------------------------------------------------------

def _atidaryk(kelias):
    """Atidaro irenginį TIK metaduomenims (nuline prieiga). None, jei nepavyko."""
    h = _k32.CreateFileW(kelias, 0, _FILE_SHARE_RW, None, _OPEN_EXISTING, 0, None)
    if not h or h == _INVALID:
        return None
    return h


def _ioctl(h, kodas, out):
    grazinta = wintypes.DWORD()
    ok = _k32.DeviceIoControl(h, kodas, None, 0, ctypes.byref(out),
                              ctypes.sizeof(out), ctypes.byref(grazinta), None)
    return out if ok else None


def fiziniai_diskai():
    """{disko numeris: dydis baitais}. Tylus praleidimas, jei disko nera."""
    ats = {}
    for nr in range(0, 16):
        h = _atidaryk("\\\\.\\PhysicalDrive%d" % nr)
        if h is None:
            continue
        try:
            geo = _ioctl(h, IOCTL_DISK_GET_DRIVE_GEOMETRY_EX, _DISK_GEOMETRY_EX())
            if geo is not None and geo.DiskSize > 0:
                ats[nr] = geo.DiskSize
        finally:
            _k32.CloseHandle(h)
    return ats


def tomo_vieta_diske(raide):
    """Kur tomas fiziskai guli: (disko_nr, pradzia, ilgis) arba None.

    Grazina PIRMA extent'a. Jei ju daugiau nei vienas (dinaminis tomas,
    Storage Spaces), suvedimo nedarom - zr. `kelios_dalys`.
    """
    h = _atidaryk("\\\\.\\%s:" % raide)
    if h is None:
        return None
    try:
        ext = _ioctl(h, IOCTL_VOLUME_GET_VOLUME_DISK_EXTENTS, _VOLUME_DISK_EXTENTS())
        if ext is None or ext.NumberOfDiskExtents < 1:
            return None
        e = ext.Extents[0]
        return {"disko_nr": e.DiskNumber, "pradzia": e.StartingOffset,
                "ilgis": e.ExtentLength, "daliu": ext.NumberOfDiskExtents}
    finally:
        _k32.CloseHandle(h)


def skaidinio_dydis(raide):
    """Skaidinio dydis ir pradzia is PARTITION_INFORMATION_EX arba None."""
    h = _atidaryk("\\\\.\\%s:" % raide)
    if h is None:
        return None
    try:
        buf = _ioctl(h, IOCTL_DISK_GET_PARTITION_INFO_EX, (ctypes.c_byte * 144)())
        if buf is None:
            return None
        raw = bytes(buf)
        # PARTITION_INFORMATION_EX: [0:4] style, [8:16] StartingOffset, [16:24] PartitionLength
        return {"pradzia": int.from_bytes(raw[8:16], "little"),
                "ilgis": int.from_bytes(raw[16:24], "little")}
    finally:
        _k32.CloseHandle(h)


def failu_sistema(raide):
    """(viso, laisva, klasteris) is failu sistemos. None, jei nepasiekiama."""
    viso = ctypes.c_ulonglong(0)
    laisva = ctypes.c_ulonglong(0)
    liks = ctypes.c_ulonglong(0)
    if not _k32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(raide + ":\\"),
                                    ctypes.byref(liks), ctypes.byref(viso),
                                    ctypes.byref(laisva)):
        return None
    spc = wintypes.DWORD(); bps = wintypes.DWORD()
    fc = wintypes.DWORD(); tc = wintypes.DWORD()
    klasteris = 0
    if _k32.GetDiskFreeSpaceW(ctypes.c_wchar_p(raide + ":\\"), ctypes.byref(spc),
                              ctypes.byref(bps), ctypes.byref(fc), ctypes.byref(tc)):
        klasteris = spc.value * bps.value
    return {"viso": viso.value, "laisva": laisva.value,
            "uzimta": viso.value - laisva.value, "klasteris": klasteris}


def sistemos_failai(raide):
    """Failai, kuriuos Windows laiko diske, kad galetu dirbti.

    Grazina {vardas: dydis} tik tiems, kurie EGZISTUOJA.

    ⚠️ PAMATUOTA 2026-09-13, nes TODO_kitam_kartui.md 2.7 teige prieingai
    ("be pakelimo NEMATOME ... net dydzio") - tai NETIESA:

        GetFileAttributesEx -> SHARING_VIOLATION (32)
        FindFirstFile       -> VEIKIA
        os.stat             -> VEIKIA

    Priezastis: `os.stat` (kaip ir FindFirstFile) ima dydi is KATALOGO IRASO,
    o ne atidarydamas pati faila, todel uzrakintas sisteminis failas jam
    netrukdo. Roberto masinoje be admin gautas pagefile.sys = 9,00 GB.

    ⛔ Ko cia NERA ir be admin nebus: seseliniu kopiju (VSS) dydzio ir MFT
    (FSCTL_GET_NTFS_VOLUME_DATA su nuline prieiga grazina klaida 1).
    """
    ats = {}
    for vardas in ("pagefile.sys", "hiberfil.sys", "swapfile.sys"):
        try:
            ats[vardas] = os.stat("%s:\\%s" % (raide, vardas)).st_size
        except OSError:
            continue  # nera arba neprieinamas - tyliai praleidziam, o zemiau pasakom
    return ats


def vietiniai_tomai():
    """Vietiniai IR prijungti isoriniai diskai; be tinklo ir be CD.

    2026-09-13: iskart itraukiam ir DRIVE_REMOVABLE, nes Robertas testuoja su
    prijungtu isoriniu disku, o USB diskai buna ir FIXED, ir REMOVABLE -
    priklauso nuo tvarkykles. Tuscius korteliu skaitytuvus atmeta ne tipas,
    o tai, kad jiems nepavyksta `failu_sistema()`.
    """
    ats = []
    kauke = _k32.GetLogicalDrives()
    for i, raide in enumerate(string.ascii_uppercase):
        if not (kauke >> i) & 1:
            continue
        tipas = _k32.GetDriveTypeW(ctypes.c_wchar_p(raide + ":\\"))
        if tipas not in (DRIVE_FIXED, DRIVE_REMOVABLE):
            continue
        if failu_sistema(raide) is None:
            continue  # tuscias skaitytuvas ar neparuosta laikmena
        ats.append(raide)
    return ats


def _disko_tomu_suma(disko_nr, visi_tomai_sarasas=None):
    """Kiek TO PACIO fizinio disko uzima visi tomai, turintys raide.

    ⛔ BUTINA, kitaip melas: jei diske du skaidiniai (C: ir E:), lyginant disko
    dydi su VIENO skaidinio dydziu "vieta be raides" gaunasi lygi kitam
    skaidiniui. Roberto masinoje C: yra vienintelis didelis skaidinys, todel
    klaida nesimate - isliptu tik prijungus isorini diska su keliais skaidiniais.
    """
    suma = 0
    for raide in (visi_tomai_sarasas or vietiniai_tomai()):
        v = tomo_vieta_diske(raide)
        if v and v["disko_nr"] == disko_nr:
            suma += v["ilgis"]
    return suma


# ------------------------------------------------------------------
# Sasku suvedimas
# ------------------------------------------------------------------

def suvesk(raide, visi_tomai_sarasas=None):
    """Suveda visus prieinamus saltinius vienam tomui.

    Grazina dict su skaiciais IR su `nesutapimai` sarasu. Kiekvienas
    nesutapimas turi `tipas` (NS_*), `baitai` ir `itariamieji` - raktu sarasa,
    kuri sluoksnis virsuje pavercia tekstu.

    Nieko nespeja: jei saltinis nepasiekiamas, jo reiksme None ir jokia isvada
    is jo nedaroma.
    """
    fs = failu_sistema(raide)
    vieta = tomo_vieta_diske(raide)
    skaidinys = skaidinio_dydis(raide)
    diskai = fiziniai_diskai()

    disko_dydis = None
    if vieta is not None:
        disko_dydis = diskai.get(vieta["disko_nr"])

    sist = sistemos_failai(raide)

    r = {
        "raide": raide,
        "fs": fs,
        "skaidinys": skaidinys,
        "vieta": vieta,
        "disko_nr": vieta["disko_nr"] if vieta else None,
        "disko_dydis": disko_dydis,
        "kelios_dalys": bool(vieta and vieta["daliu"] > 1),
        "sistemos_failai": sist,
        "sistemos_failu_suma": sum(sist.values()),
        "nesutapimai": [],
        "nematome": [],
    }

    # Ko NEMATOME - sakom garsiai, o ne tyliai praleidziam
    if fs is None:
        r["nematome"].append("failu_sistema")
    if skaidinys is None:
        r["nematome"].append("skaidinys")
    if vieta is None:
        r["nematome"].append("vieta_diske")
    if disko_dydis is None:
        r["nematome"].append("fizinis_diskas")
    # Sito be admin negausim NIEKADA - sakom garsiai, o ne tyliai praleidziam
    r["nematome"].append("seselines_kopijos")
    r["nematome"].append("mft")

    # 1) diskas vs VISI jo skaidiniai - TAI, ko nedaro niekas kitas.
    #    Lyginam tik kai tomas guli viename gabale: kitaip suma neturi prasmes.
    if disko_dydis and skaidinys and not r["kelios_dalys"]:
        # Atimam VISUS to disko tomus, ne tik si - kitaip antras skaidinys
        # butu paskelbtas "vieta be raides" (zr. _disko_tomu_suma).
        tomu_suma = _disko_tomu_suma(r["disko_nr"], visi_tomai_sarasas)
        uz_ribu = disko_dydis - tomu_suma
        r["disko_tomu_suma"] = tomu_suma
        r["uz_skaidinio"] = uz_ribu
        # SLENKSTIS 3 GB, ne 1 GB (pataisyta 2026-09-13 pamatavus).
        # Kiekvienas Windows kompiuteris TURI vietos be raides: EFI 100-300 MB,
        # MSR iki 128 MB, atkurimo skaidinys 500-1000 MB - is viso iki ~1,5 GB.
        # Su 1 GB riba programa butu skelbusi "nepaaiskinta" VISIEMS sveikiems
        # diskams (Roberto C: = 1,1 GB). Klaidingas pavojus butu blogiau nei
        # praleistas: zmogus, kuriam viskas gerai, isigastu be reikalo.
        # Pats skaicius vis tiek matomas skiltyje - slepiam tik VERDIKTA.
        if uz_ribu > 3 * 1024 ** 3:
            r["nesutapimai"].append({
                "tipas": NS_UZ_SKAIDINIO,
                "baitai": uz_ribu,
                "itariamieji": ["nepaskirstyta", "atkurimo_skaidinys", "hpa_dco"],
            })

    # 2) skaidinys vs tomas, kuri mato failu sistema
    if skaidinys and fs:
        skirtumas = skaidinys["ilgis"] - fs["viso"]
        r["skaidinys_vs_tomas"] = skirtumas
        if skirtumas > 1024 ** 3:
            r["nesutapimai"].append({
                "tipas": NS_TOMAS_MAZESNIS,
                "baitai": skirtumas,
                "itariamieji": ["mft_rezervas", "failu_sistemos_apskaita"],
            })

    return r


def visi_tomai():
    """Suvestine visiems tomams. Sarasa surenkam VIENA karta ir paduodam
    kiekvienam `suvesk`, kad kiekvienas tomas nekartotu tos pacios apklausos."""
    sarasas = vietiniai_tomai()
    return [suvesk(raide, sarasas) for raide in sarasas]


# ------------------------------------------------------------------
# Zmoniskas dydis (TC jau turi fmt_size GUI pusėje; cia - savarankiskas)
# ------------------------------------------------------------------

def gb(baitai):
    if baitai is None:
        return "-"
    return "%.1f GB" % (baitai / (1024.0 ** 3))


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    for t in visi_tomai():
        print("=== %s: ===" % t["raide"])
        if t["fs"]:
            print("  failu sistema : viso %s, uzimta %s, laisva %s (klasteris %d B)"
                  % (gb(t["fs"]["viso"]), gb(t["fs"]["uzimta"]),
                     gb(t["fs"]["laisva"]), t["fs"]["klasteris"]))
        if t["skaidinys"]:
            print("  skaidinys     : %s (pradzia %s)"
                  % (gb(t["skaidinys"]["ilgis"]), gb(t["skaidinys"]["pradzia"])))
        if t["disko_dydis"]:
            print("  fizinis diskas: PhysicalDrive%d = %s"
                  % (t["disko_nr"], gb(t["disko_dydis"])))
        if t.get("uz_skaidinio") is not None:
            print("  uz skaidinio  : %s" % gb(t["uz_skaidinio"]))
        if t.get("sistemos_failai"):
            print("  sistemos failai: %s" % ", ".join(
                "%s %s" % (v, gb(d)) for v, d in
                sorted(t["sistemos_failai"].items(), key=lambda x: -x[1])))
        if t["nematome"]:
            print("  NEMATOME      : %s" % ", ".join(t["nematome"]))
        for n in t["nesutapimai"]:
            print("  ⚠️ NESUTAPIMAS %s: %s (itariamieji: %s)"
                  % (n["tipas"], gb(n["baitai"]), ", ".join(n["itariamieji"])))
        print()
