# patikra_zinynas.py - v1.1 "Kas tai?" (zinynas.py) regresijos tinklas.
# AUTORIUS: Claude (teisejas), 2026-08-07. Pagal patikra_saugikliai.py sablona.
#
# Tikrina zinynas.py BE TINKLO ir BE GUI (gryni unit testai):
#   Z1 SEGMENTAI  - vardo istraukimas is AppData/Temp/ProgramData/Windows keliu
#   Z2 PRIVATUMAS - vartotojo vardas ir pilnas kelias NIEKADA nepatenka i uzklausa
#   Z3 JUNK       - GUID/hex/7zS/bk_/tmp antri segmentai atmetami
#   Z4 ZINYNAS    - zinomos programos gauna gamintojo URL (1 pakopa)
#   Z5 GOOGLE     - nezinomos gauna Google paieskos url su vardu (2 pakopa)
#   Z6 ATSARGA    - sugadintas/nesamas json -> Google pakopa, jokio lugio
#   Z7 JSON       - zinomos_programos.json validus, visi irasai turi vardas+url
#
# Exit: 0 = OK, 1 = FAIL, 2 = WATCHDOG.
# LEISTI: <python> -u _patikros\patikra_zinynas.py

import json
import os
import sys
import threading
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

WATCHDOG_S = 30

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

import zinynas

# --- Z1 SEGMENTAI ---------------------------------------------------------
print("--- Z1 SEGMENTAI ---")
check(zinynas.vardo_segmentai(r"C:\Users\Vardenis\AppData\Local\NVIDIA\DXCache")
      == ["NVIDIA", "DXCache"], "Z1a AppData Local: vendor+app")
check(zinynas.vardo_segmentai(r"C:\Users\Vardenis\AppData\Roaming\Mozilla")
      == ["Mozilla"], "Z1b AppData Roaming: tik vendor")
check(zinynas.vardo_segmentai(r"C:\Users\Vardenis\AppData\Local\Temp\Adobe")
      == ["Adobe"], "Z1c vartotojo Temp viduje")
check(zinynas.vardo_segmentai(r"C:\Windows\Temp\acad")
      == ["acad"], "Z1d Windows\\Temp")
check(zinynas.vardo_segmentai(r"C:\ProgramData\Microsoft\Windows")
      == ["Microsoft", "Windows"], "Z1e ProgramData")
check(zinynas.vardo_segmentai(r"C:\Users\Vardenis\AppData\Local\Temp")
      == ["Temp"], "Z1f pati Temp baze -> paskutinis segmentas")
check(zinynas.vardo_segmentai(r"D:\kazkoks\keistas\kelias")
      == ["kelias"], "Z1g nezinoma sema -> tik paskutinis segmentas")
check(zinynas.vardo_segmentai("") == [], "Z1h tuscias kelias -> tuscia")

# --- Z2 PRIVATUMAS --------------------------------------------------------
print("--- Z2 PRIVATUMAS ---")
_KELIAI = [
    r"C:\Users\SlaptasVardas\AppData\Local\NVIDIA\DXCache",
    r"C:\Users\SlaptasVardas\AppData\Local\Temp\7zS4446A1F3",
    r"C:\Users\SlaptasVardas\AppData\Roaming\Adobe",
    r"C:\Users\SlaptasVardas\AppData\Local\Temp",
]
for _p in _KELIAI:
    _v, _url, _z = zinynas.kas_tai(_p, "lt")
    check(_url is not None and "SlaptasVardas" not in _url,
          "Z2 be vartotojo vardo: " + _p.split("\\")[-1])
    check(_url is not None and "Users" not in _url,
          "Z2 be Users segmento: " + _p.split("\\")[-1])

# --- Z3 JUNK --------------------------------------------------------------
print("--- Z3 JUNK ---")
check(zinynas.vardo_segmentai(
    r"C:\Users\V\AppData\Local\Google\016c246d-2ee4-4991-a05d-76c1d08743d7")
      == ["Google"], "Z3a GUID antras segmentas atmetamas")
check(zinynas.vardo_segmentai(r"C:\Users\V\AppData\Local\Adobe\12345")
      == ["Adobe"], "Z3b vien skaiciu segmentas atmetamas")
check(zinynas.vardo_segmentai(r"C:\Users\V\AppData\Local\NVIDIA\DXCache")
      == ["NVIDIA", "DXCache"], "Z3c prasmingas antras segmentas LIEKA")
check(zinynas.vardo_segmentai(r"C:\Users\V\AppData\Local\Temp\7zS9480.tmp")
      == ["7zS9480.tmp"], "Z3d pirmas segmentas net junk LIEKA (sazininga)")

# --- Z4 ZINYNAS (gamintojo pakopa) ---------------------------------------
print("--- Z4 ZINYNAS ---")
_v, _url, _zin = zinynas.kas_tai(r"C:\Users\V\AppData\Local\NVIDIA\DXCache", "lt")
check(_zin and "nvidia.com" in _url, "Z4a NVIDIA -> gamintojo puslapis")
_v, _url, _zin = zinynas.kas_tai(
    r"C:\Users\V\AppData\Local\Google\Chrome\User Data", "lt")
check(_zin and "chrome" in _url, "Z4b google/chrome dvigubas raktas")
_v, _url, _zin = zinynas.kas_tai(r"C:\Users\V\AppData\Roaming\Mozilla", "en")
check(_zin and "mozilla.org" in _url, "Z4c Mozilla -> gamintojo puslapis")
check(_v == "Mozilla (Firefox)", "Z4d rodomas vardas is zinyno")

# --- Z5 GOOGLE (paieskos pakopa) -----------------------------------------
print("--- Z5 GOOGLE ---")
_v, _url, _zin = zinynas.kas_tai(
    r"C:\Users\V\AppData\Local\VisiskaiNezinoma\cache", "lt")
check(not _zin and _url.startswith("https://www.google.com/search?q="),
      "Z5a nezinoma -> Google paieskos sarasas")
check("VisiskaiNezinoma" in _url, "Z5b vardas uzklausoje yra")
check("kas+tai" in _url, "Z5c LT uzklausos forma")
_v2, _url2, _zin2 = zinynas.kas_tai(
    r"C:\Users\V\AppData\Local\VisiskaiNezinoma\cache", "en")
check("what+is" in _url2, "Z5d EN uzklausos forma")

# --- Z6 ATSARGA (sugadintas zinynas) -------------------------------------
print("--- Z6 ATSARGA ---")
_orig = zinynas._zinyno_kelias
zinynas._zinyno_kelias = lambda: str(PROJECT / "_patikros" / "nera_tokio.json")
try:
    _v, _url, _zin = zinynas.kas_tai(
        r"C:\Users\V\AppData\Local\NVIDIA\DXCache", "lt")
    check(not _zin and "google.com" in _url,
          "Z6a nesamas json -> Google pakopa, be lugio")
finally:
    zinynas._zinyno_kelias = _orig

# --- Z7 JSON validumas ----------------------------------------------------
print("--- Z7 JSON ---")
with open(PROJECT / "zinomos_programos.json", encoding="utf-8") as fh:
    _data = json.load(fh)
_prog = _data.get("programos", {})
check(len(_prog) >= 40, "Z7a zinyne >= 40 irasu (yra %d)" % len(_prog))
_blogi = [k for k, v in _prog.items()
          if not (isinstance(v, dict) and v.get("vardas")
                  and str(v.get("url", "")).startswith("https://"))]
check(not _blogi, "Z7b visi irasai turi vardas + https url %s" % (_blogi or ""))
_ne_maz = [k for k in _prog if k != k.lower()]
check(not _ne_maz, "Z7c visi raktai mazosiomis %s" % (_ne_maz or ""))

# --- Santrauka ------------------------------------------------------------
print()
if FAILS:
    print("PATIKRA: %d KLAIDOS" % len(FAILS))
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("PATIKRA OK - visi zinynas.py testai zali")
sys.exit(0)
