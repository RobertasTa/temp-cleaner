# patikra_saugikliai.py - Temp valytuvo SAUGIKLIU regresijos tinklas.
# AUTORIUS: Claude (teisejas), 2026-08-05. Pagal dubliu programos patikru sablona.
#
# Tikrina VARIKLI (be GUI) su DIRBTINIAIS failais laikinam kataloge:
#   T1 AGE      - trinami tik failai senesni nei AGE_DAYS; sviezi -> SKIPPED AGE
#   T2 LOCKED   - atidarytas (uzrakintas) failas -> SKIPPED LOCKED, programa nekrenta
#   T3 JUNCTION - junction NEsekamas ir NEtrinamas; failai uz junction NEPALIESTI
#   T4 KATALOGAI- clean_folder trina TIK failus, pakatalogiai lieka
#   T5 SPALVOS  - scanner klasifikacija per VALYTUVAS_TESTBED:
#                 green -> ZALIA, heuristic -> GELTONA, blacklist kelias/vidus -> RAUDONA
#   T6 SKAICIAVIMAS - _count_files_size neskaiciuoja failu uz junction
#
# VISI testai dirba TIK dirbtiniame tempfile.mkdtemp kataloge - jokiu tikru vietu.
# Exit: 0 = OK, 1 = FAIL, 2 = WATCHDOG.
# LEISTI: <python> -u _patikros\patikra_saugikliai.py

import os
import sys
import time
import shutil
import tempfile
import threading
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

WATCHDOG_S = 60

def _watchdog_fire():
    print("[WATCHDOG] kabo >%ss -> exit 2" % WATCHDOG_S)
    sys.stdout.flush()
    os._exit(2)

_wd = threading.Timer(WATCHDOG_S, _watchdog_fire)
_wd.daemon = True
_wd.start()

FAILS = []

def check(cond, msg):
    if cond:
        print("[OK]", msg)
    else:
        FAILS.append(msg)
        print("[FAIL]", msg)

from cleaner import clean_folder
from models import AGE_DAYS

OLD_T = time.time() - (AGE_DAYS + 3) * 86400   # tikrai senas
ROOT = Path(tempfile.mkdtemp(prefix="valytuvas_patikra_"))
print("Dirbtinis poligonas:", ROOT)

def make_file(path, content=b"x" * 100, mtime=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path

def make_junction(link, target):
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       capture_output=True, text=True)
    return r.returncode == 0

# ---------- T1: AGE saugiklis ------------------------------------------------
t1 = ROOT / "t1_age"
old_f = make_file(t1 / "senas.txt", mtime=OLD_T)
fresh_f = make_file(t1 / "sviezias.txt")           # mtime = dabar
log = []
d, b, s = clean_folder(t1, log)
check(not old_f.exists(), "T1: senas failas (>%dd) ISTRINTAS" % AGE_DAYS)
check(fresh_f.exists(), "T1: sviezias failas PALIKTAS")
check(d == 1 and b == 100, "T1: statistika d=1 b=100 (gauta d=%d b=%d)" % (d, b))
age_skips = [e for e in log if e.operation == "SKIPPED" and e.reason == "AGE"]
check(len(age_skips) == 1 and age_skips[0].path == str(fresh_f),
      "T1: zurnale SKIPPED..AGE su sviezio failo keliu")

# ---------- T2: LOCKED saugiklis ---------------------------------------------
t2 = ROOT / "t2_locked"
lock_f = make_file(t2 / "uzrakintas.txt", mtime=OLD_T)
free_f = make_file(t2 / "laisvas.txt", mtime=OLD_T)
fh = open(lock_f, "rb")   # atidarytas failas Windows'e netrinamas
try:
    log = []
    d, b, s = clean_folder(t2, log)
    check(lock_f.exists(), "T2: uzrakintas failas PALIKTAS (programa nekrito)")
    check(not free_f.exists(), "T2: laisvas senas failas ISTRINTAS")
    locked_skips = [e for e in log if e.reason == "LOCKED"]
    check(len(locked_skips) == 1 and locked_skips[0].path == str(lock_f),
          "T2: zurnale SKIPPED..LOCKED su uzrakinto failo keliu")
finally:
    fh.close()

# ---------- T3: JUNCTION saugiklis -------------------------------------------
t3 = ROOT / "t3_junction"
victim_dir = ROOT / "t3_auka"                       # "tikri duomenys" kitur diske
victim_f = make_file(victim_dir / "auka.txt", mtime=OLD_T)
t3.mkdir(parents=True, exist_ok=True)
jok = make_junction(t3 / "nuoroda", victim_dir)
check(jok, "T3: junction sukurtas (mklink /J)")
if jok:
    log = []
    d, b, s = clean_folder(t3, log)
    check(victim_f.exists(), "T3: failas UZ junction NEPALIESTAS")
    j_skips = [e for e in log if e.reason == "JUNCTION"]
    check(len(j_skips) == 1, "T3: zurnale SKIPPED..JUNCTION (gauta %d)" % len(j_skips))
    check((t3 / "nuoroda").exists(), "T3: pats junction nepasalintas")

# ---------- T4: katalogai netrinami ------------------------------------------
t4 = ROOT / "t4_dirs"
make_file(t4 / "gilus" / "failas.txt", mtime=OLD_T)
log = []
d, b, s = clean_folder(t4, log)
check((t4 / "gilus").is_dir(), "T4: pakatalogis PALIKTAS (trinami tik failai)")
check(not (t4 / "gilus" / "failas.txt").exists(), "T4: failas pakatalogyje istrintas")

# ---------- T5: scanner spalvos per TESTBED ----------------------------------
TB = ROOT / "testbed"
local = TB / "Users/User/AppData/Local"
make_file(TB / "Users/User/AppData/Local/Temp" / "a.txt")       # green TEMP
make_file(TB / "Windows/Temp" / "b.txt")                        # green WINTEMP
make_file(local / "NVIDIA/DXCache" / "c.bin")                   # green kuruota
make_file(local / "SomeApp/cache" / "d.bin")                    # heuristic GELTONA
make_file(local / "OtherApp/data/cache" / "e.bin")              # 'data' kelyje -> RAUDONA
make_file(local / "ThirdApp/cache/models/svarbus.bin")          # 'models' viduje -> RAUDONA
make_file(TB / "Users/User/AppData/Roaming" / "App/temp" / "f.log")  # Roaming GELTONA
make_file(TB / "ProgramData" / "dummy.txt")
# Gyvo Roberto skeno pamoka 2026-08-05: paketu vidus NE siuksles!
make_file(local / "Programs/Python/Lib/site-packages/otel/logs/kodas.py")   # RAUDONA
make_file(TB / "Users/User/AppData/Roaming/npm/node_modules/pak/lib/cache/x.js")  # RAUDONA

os.environ["VALYTUVAS_TESTBED"] = str(TB)
try:
    import scanner as _sc
    cands = _sc.scan()
finally:
    del os.environ["VALYTUVAS_TESTBED"]

by_path = {c.path: c for c in cands}

def find_color(suffix):
    for p, c in by_path.items():
        if os.path.normpath(p).lower().endswith(os.path.normpath(suffix).lower()):
            return c.color
    return None

check(find_color(r"AppData\Local\Temp") == "ZALIA", "T5: TEMP -> ZALIA")
check(find_color(r"Windows\Temp") == "ZALIA", "T5: Windows\\Temp -> ZALIA")
check(find_color(r"NVIDIA\DXCache") == "ZALIA", "T5: kuruota DXCache -> ZALIA")
check(find_color(r"SomeApp\cache") == "GELTONA", "T5: heuristic cache -> GELTONA")
check(find_color(r"OtherApp\data\cache") == "RAUDONA",
      "T5: 'data' kelyje -> RAUDONA")
check(find_color(r"ThirdApp\cache") == "RAUDONA",
      "T5: 'models' viduje -> RAUDONA")
check(find_color(r"App\temp") == "GELTONA", "T5: Roaming temp -> GELTONA")
check(find_color(r"otel\logs") == "RAUDONA",
      "T5: site-packages viduje 'logs' -> RAUDONA (Python paketu apsauga)")
check(find_color(r"lib\cache") == "RAUDONA",
      "T5: node_modules viduje 'cache' -> RAUDONA (npm paketu apsauga)")

# ---------- T6: skaiciavimas neseka junction ---------------------------------
t6 = ROOT / "t6_count"
make_file(t6 / "vietinis.txt", content=b"y" * 50)
if make_junction(t6 / "salutinis", victim_dir):
    from scanner import _count_files_size
    cnt, total = _count_files_size(t6)
    check(cnt == 1 and total == 50,
          "T6: _count_files_size neskaiciuoja uz junction (cnt=%d total=%d)" % (cnt, total))

# ---------- T7: dry-run Perziura (NIEKO netrina) ------------------------------
import cleaner as _cl
from models import Candidate

t7 = ROOT / "t7_dry"
old7 = make_file(t7 / "senas.txt", content=b"z" * 200, mtime=OLD_T)
fresh7 = make_file(t7 / "sviezias.txt")
log = []
d, b, s = clean_folder(t7, log, dry_run=True)
check(old7.exists() and fresh7.exists(), "T7: dry-run NIEKO neistrina")
check(d == 1 and b == 200, "T7: dry-run suskaiciuoja butu-trinta (d=%d b=%d)" % (d, b))
wd = [e for e in log if e.operation == "WOULD_DELETE"]
check(len(wd) == 1 and wd[0].path == str(old7), "T7: zurnale WOULD_DELETE su keliu")

# preview_candidates: ZALIA+GELTONA perziurima, RAUDONA ne; log failas nerasomas
_orig_root = _cl._ROOT
_cl._ROOT = ROOT   # izoliuojam zurnala poligone
try:
    cands7 = [Candidate(path=str(t7), color="ZALIA"),
              Candidate(path=str(t7), color="RAUDONA")]
    per_loc, tc, tb = _cl.preview_candidates(cands7)
    check(len(per_loc) == 1 and tc == 1 and tb == 200,
          "T7: preview_candidates ima ZALIA, ignoruoja RAUDONA")
    check(not (ROOT / "_darbal" / "valymo_log.txt").exists(),
          "T7: perziura NEraso valymo_log.txt")
    check(old7.exists(), "T7: po preview_candidates failai tebera")
finally:
    _cl._ROOT = _orig_root

# ---------- T8: age_days parametras -------------------------------------------
t8 = ROOT / "t8_age_param"
mid_f = make_file(t8 / "vidutinis.txt", mtime=time.time() - 3 * 86400)  # 3 d.
log = []
d, b, s = clean_folder(t8, log, age_days=7)
check(mid_f.exists(), "T8: age_days=7 -> 3d failas PALIKTAS")
log = []
d, b, s = clean_folder(t8, log, age_days=1)
check(not mid_f.exists(), "T8: age_days=1 -> 3d failas ISTRINTAS")

# ---------- T9: read_total_freed skaitliukas ----------------------------------
_cl._ROOT = ROOT
try:
    from models import LogEntry as _LE
    _cl.write_log([_LE("DELETED", "x", "", 10 * 1048576)])
    _cl.write_log([_LE("DELETED", "y", "", 5 * 1048576),
                   _LE("SKIPPED", "z", "AGE", 0)])
    runs, mb = _cl.read_total_freed()
    check(runs == 2 and abs(mb - 15.0) < 0.01,
          "T9: read_total_freed sumuoja TOTAL eilutes (runs=%d mb=%.2f)" % (runs, mb))
finally:
    _cl._ROOT = _orig_root

# ---------- T10: vietos.json zinynas ------------------------------------------
import models as _md

check(len(_md.GREEN_RELATIVES) == 5 and _md.GREEN_BASE_INDEX[:2] == [0, 1],
      "T10: zalios vietos uzsikrove is vietos.json (5 irasu)")
check("models" in _md.BLACKLIST_NAMES and "cache" in _md.HEURISTIC_NAMES,
      "T10: juodasis sarasas ir heuristika is vietos.json")
check(_md.AGE_DAYS == 7, "T10: amzius_dienomis=7 is vietos.json")

# Atsarga: sugadintas/nerastas json -> numatytos reiksmes, programa nekrenta
_orig_path_fn = _md._vietos_json_path
_md._vietos_json_path = lambda: str(ROOT / "nera_tokio.json")
try:
    vals = _md._load_vietos()
    check(vals[0] == _md._DEFAULT_GREEN_RELATIVES and vals[4] == 7,
          "T10: dingus vietos.json -> numatytos reiksmes (atsarga veikia)")
finally:
    _md._vietos_json_path = _orig_path_fn

# ---------- T11: amziaus kibireliai + akimirksnine perziura --------------------
from scanner import _count_files_buckets
from cleaner import preview_from_buckets

t11 = ROOT / "t11_buckets"
now11 = time.time()
make_file(t11 / "d0.txt", content=b"a" * 10)                              # 0 d.
make_file(t11 / "d3.txt", content=b"b" * 20, mtime=now11 - 3.5 * 86400)   # 3 d.
make_file(t11 / "d10.txt", content=b"c" * 30, mtime=now11 - 10.5 * 86400) # 10 d.
make_file(t11 / "d40.txt", content=b"d" * 40, mtime=now11 - 40 * 86400)   # 30+
if make_junction(t11 / "salutinis11", victim_dir):
    pass   # junction kibireliuose neskaiciuojamas

cnt, total, af, ab = _count_files_buckets(t11, now=now11)
check(cnt == 4 and total == 100,
      "T11: scandir suskaiciavo 4 failus/100 B (cnt=%d total=%d)" % (cnt, total))
check(af[0] == 1 and af[3] == 1 and af[10] == 1 and af[30] == 1,
      "T11: kibireliai 0/3/10/30+ uzpildyti teisingai")
check(ab[3] == 20 and ab[30] == 40, "T11: kibireliu baitai teisingi")

c11 = Candidate(path=str(t11), color="ZALIA", age_files=af, age_bytes=ab)
res = preview_from_buckets([c11], 7)
check(res is not None and res[1] == 2 and res[2] == 70,
      "T11: perziura is kibireliu riba=7 -> 2 failai/70 B (%s)" % (res,))
res1 = preview_from_buckets([c11], 1)
check(res1[1] == 3 and res1[2] == 90, "T11: riba=1 -> 3 failai/90 B")
res30 = preview_from_buckets([c11], 30)
check(res30[1] == 1 and res30[2] == 40, "T11: riba=30 -> tik 30+ kibirelis")
check(preview_from_buckets([Candidate(path="x", color="ZALIA")], 7) is None,
      "T11: be kibireliu -> None (atsarga i gyva perziura)")

# Kryzmine kontrole: kibireliu perziura == gyvo dry-run rezultatas
log11 = []
d_live, b_live, _s = clean_folder(t11, log11, age_days=7, dry_run=True)
check(d_live == res[1] and b_live == res[2],
      "T11: kibireliai sutampa su gyvu dry-run (live %d/%d)" % (d_live, b_live))

# ---------- T12: saugykla (portable rezimas, pastaba 3) ------------------------
import saugykla as _sg

_t12_exe = ROOT / "t12_exe"
_t12_la = ROOT / "t12_localappdata"
_t12_exe.mkdir(parents=True, exist_ok=True)
_orig_exe_dir = _sg.exe_dir
_orig_la = os.environ.get("LOCALAPPDATA")
_sg.exe_dir = lambda: _t12_exe
os.environ["LOCALAPPDATA"] = str(_t12_la)
try:
    check(_sg.is_portable() is False, "T12: be zymeklio - NE portable")
    check(_sg.data_dir() == _t12_la / "TempCleaner",
          "T12: numatyta vieta %LOCALAPPDATA%/TempCleaner")

    # Kompiuterio rezime atsiranda zurnalas...
    la_log = _t12_la / "TempCleaner" / "valymo_log.txt"
    la_log.parent.mkdir(parents=True, exist_ok=True)
    la_log.write_text("TOTAL deleted=1 size_mb=1.00 skipped=0 size_b=1048576\n",
                      encoding="utf-8")

    # ...ijungiam portable: zymeklis + zurnalas persikelia + pedsaku nelieka
    ok12, err12 = _sg.set_portable(True)
    check(ok12, "T12: set_portable(True) pavyko (%s)" % err12)
    check((_t12_exe / "TempCleaner_portable.txt").exists(),
          "T12: TempCleaner_portable.txt sukurtas salia exe")
    check(_sg.is_portable() is True, "T12: rezimas dabar portable")
    check(_sg.data_dir() == _t12_exe / "_darbal", "T12: portable vieta _darbal salia exe")
    check((_t12_exe / "_darbal" / "valymo_log.txt").exists(),
          "T12: zurnalas persikele i _darbal (istorija islieka)")
    check(not (_t12_la / "TempCleaner").exists(),
          "T12: %LOCALAPPDATA%/TempCleaner istrintas (pedsaku nelieka)")

    # Isjungiam: zymeklis dingsta, zurnalas grizta
    ok12b, err12b = _sg.set_portable(False)
    check(ok12b, "T12: set_portable(False) pavyko (%s)" % err12b)
    check(not (_t12_exe / "TempCleaner_portable.txt").exists(), "T12: zymeklis nuimtas")
    check(la_log.exists(), "T12: zurnalas grizo i %LOCALAPPDATA%")
    check(not (_t12_exe / "_darbal").exists(), "T12: tuscias _darbal isvalytas")

    # T12c: senas portable.txt (iki-publikacijos testai) tebeatpazistamas,
    # o ijungus rezima migruojamas i prefiksuota varda (seimos kolizijos remontas)
    (_t12_exe / "portable.txt").write_text("portable\n", encoding="utf-8")
    check(_sg.is_portable() is True, "T12c: senas portable.txt atpazistamas (fallback)")
    ok12c, err12c = _sg.set_portable(True)
    check(ok12c, "T12c: set_portable(True) pavyko (%s)" % err12c)
    check((_t12_exe / "TempCleaner_portable.txt").exists()
          and not (_t12_exe / "portable.txt").exists(),
          "T12c: migracija - naujas zymeklis yra, senas nuimtas")
    ok12d, err12d = _sg.set_portable(False)
    check(ok12d and _sg.is_portable() is False,
          "T12c: isjungus nelieka nei vieno zymeklio")

    # cleaner._data_dir: testu overridas _ROOT turi virsyti saugykla
    _cl._ROOT = ROOT
    try:
        check(_cl._data_dir() == ROOT / "_darbal",
              "T12: cleaner._ROOT overridas veikia (patikru izoliacija)")
    finally:
        _cl._ROOT = _orig_root
finally:
    _sg.exe_dir = _orig_exe_dir
    if _orig_la is None:
        os.environ.pop("LOCALAPPDATA", None)
    else:
        os.environ["LOCALAPPDATA"] = _orig_la

# ---------- Verdiktas ---------------------------------------------------------
shutil.rmtree(ROOT, ignore_errors=True)
print("-" * 60)
if FAILS:
    print("[FAIL] patikra_saugikliai: %d klaidu(-os):" % len(FAILS))
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("[OK] patikra_saugikliai: visi saugikliai zali")
sys.exit(0)
