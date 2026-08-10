# patikra_gui_flow.py - Temp valytuvo GUI srauto patikra.
# AUTORIUS: Claude (teisejas), 2026-08-05. Pagal dubliu programos sablona.
#
# Offscreen rezimu su VALYTUVAS_TESTBED dirbtiniu poligonu tikrina:
#   G1 kontraktas  - btn_scan/btn_preview/btn_clear_all/btn_close/age_slider/
#                    lbl_freed objectName'ai egzistuoja
#   G2 skenas      - QThread skenas uzpildo lentele, overlay dingsta,
#                    btn_preview atsirakina
#   G3 perziura    - dry-run NIEKO netrina, statusas ir zurnalas uzpildyti
#   G4 slankiklis  - age_slider=1 -> 3d senumo failas trinamas; freed label
#                    atsinaujina; valymo_log.txt turi TOTAL eilute
#   G5 spalvos     - RAUDONA eilutes Clear mygtukas isjungtas
#
# Exit: 0 = OK, 1 = FAIL, 2 = WATCHDOG.
# LEISTI: <python> -u _patikros\patikra_gui_flow.py

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"   # PRIES bet koki Qt importa!
os.environ["VALYTUVAS_LANG"] = "lt"   # determinizmas: vartotojo kalba.txt neveikia testu

import sys
import time
import shutil
import tempfile
import threading
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

WATCHDOG_S = 90

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

# ---------- Dirbtinis poligonas -----------------------------------------------
ROOT = Path(tempfile.mkdtemp(prefix="valytuvas_gui_patikra_"))
TB = ROOT / "testbed"
OLD_T = time.time() - 3 * 86400    # 3 dienu senumo (tarp 1 ir 7!)

def make_file(path, content=b"x" * 100, mtime=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return path

# ZALIA (TEMP) su 3d failu; GELTONA cache; RAUDONA data/cache
green_old = make_file(TB / "Users/User/AppData/Local/Temp/senas3d.txt", mtime=OLD_T)
make_file(TB / "Users/User/AppData/Local/Temp/sviezias.txt")
make_file(TB / "Windows/Temp/kitas.txt", mtime=OLD_T)
make_file(TB / "Users/User/AppData/Local/SomeApp/cache/geltonas.bin", mtime=OLD_T)
make_file(TB / "Users/User/AppData/Local/OtherApp/data/cache/raudonas.bin", mtime=OLD_T)

os.environ["VALYTUVAS_TESTBED"] = str(TB)

from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton, QSlider, QLabel
from PyQt6.QtCore import QEvent, QCoreApplication

app = QApplication([])

def _pump():
    QApplication.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

def wait_until(pred, timeout_s=30, step_s=0.05):
    end = time.time() + timeout_s
    while time.time() < end:
        _pump()
        if pred():
            return True
        time.sleep(step_s)
    _pump()
    return bool(pred())

MSG_INFO = [0]
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
QMessageBox.information = staticmethod(
    lambda *a, **k: (MSG_INFO.__setitem__(0, MSG_INFO[0] + 1),
                     QMessageBox.StandardButton.Ok)[1])
QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
QMessageBox.critical = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)

# Zurnala izoliuojam poligone (freed label skaito is cleaner._ROOT)
import cleaner as _cl
_cl._ROOT = ROOT

from gui_langas import MainWindow

win = MainWindow()
win.show()
_pump()

# ---------- G1: kontraktas -----------------------------------------------------
for name, cls in [("btn_scan", QPushButton), ("btn_preview", QPushButton),
                  ("btn_clear_all", QPushButton), ("btn_close", QPushButton),
                  ("age_slider", QSlider), ("lbl_freed", QLabel)]:
    check(win.findChild(cls, name) is not None, "G1: '%s' egzistuoja" % name)
check(win.btn_preview.isEnabled() is False, "G1: perziura uzrakinta iki skeno")
check(win.lbl_freed.text().startswith("Viso atlaisvinta: 0"),
      "G1: freed skaitliukas pradzioj 0 (gauta: %s)" % win.lbl_freed.text())

# ---------- G2: skenas (QThread) -----------------------------------------------
win.btn_scan.click()
ok = wait_until(lambda: win.table.rowCount() > 0, timeout_s=30)
check(ok, "G2: lentele uzpildyta po skeno")
check(not win._scan_overlay.isVisible(), "G2: overlay dingo po skeno")
check(win.btn_preview.isEnabled(), "G2: perziura atsirakino po skeno")
colors = [win.table.item(r, 3).text() for r in range(win.table.rowCount())]
check("ZALIA" in colors and "GELTONA" in colors and "RAUDONA" in colors,
      "G2: lenteleje visos trys spalvos (%s)" % sorted(set(colors)))

# ---------- G3: perziura (dry-run, dabar FONE su overlay) ----------------------
win.age_slider.setValue(1)   # 3d failai patenka i perziura
_pump()
win.btn_preview.click()
_pump()
ok = wait_until(lambda: "IS VISO" in win.log_box.toPlainText(), timeout_s=20)
check(ok, "G3: fonine perziura baigesi (IS VISO zurnale)")
check(not win._scan_overlay.isVisible(), "G3: overlay dingo po perziuros")
check(win.btn_preview.isEnabled(), "G3: perziuros mygtukas atsirakino")
check(green_old.exists(), "G3: po perziuros failai NEISTRINTI")
check("PERZIURA" in win.log_box.toPlainText(), "G3: zurnalo lange PERZIURA antraste")
check("butu trinta" in win.lbl_status.text(), "G3: statusas rodo perziuros rezultata")
check(MSG_INFO[0] >= 1, "G3: parodytas informacinis langas")

# ---------- G4: slankiklis + valymas + freed skaitliukas -----------------------
check(win.age_days() == 1, "G4: age_days() grazina slankiklio reiksme 1")
win.btn_clear_all.click()
_pump()
# Valymas nuo 2026-08-06 FONE (CleanWorker) - laukiam done santraukos zurnale
ok = wait_until(lambda: "VALYMAS BAIGTAS" in win.log_box.toPlainText(),
                timeout_s=15)
check(ok, "G4: fonine valymo gija baigesi (VALYMAS BAIGTAS zurnale)")
check(not green_old.exists(), "G4: age=1 -> 3d ZALIAS failas ISTRINTAS")
check(not win._scan_overlay.isVisible(), "G4: overlay dingo po valymo")
check("-> istrinta" in win.log_box.toPlainText()
      or "-> deleted" in win.log_box.toPlainText(),
      "G4: zurnale gyvos eilutes po kiekvienos vietos (pastaba 5)")
check((TB / "Users/User/AppData/Local/Temp/sviezias.txt").exists(),
      "G4: sviezias failas PALIKTAS")
check((TB / "Users/User/AppData/Local/OtherApp/data/cache/raudonas.bin").exists(),
      "G4: RAUDONA vieta NELIESTA")
# Pastaba 7: po 1 valymo zodis 'valymas' (ne '1 valymu'/'1 runs')
check(("1 valymas" in win.lbl_freed.text() or "1 run" in win.lbl_freed.text())
      and win.lbl_freed.text() != "Viso atlaisvinta: 0 MB",
      "G4: freed skaitliukas atsinaujino su teisinga forma (%s)" % win.lbl_freed.text())
log_file = ROOT / "_darbal" / "valymo_log.txt"
check(log_file.exists() and "TOTAL" in log_file.read_text(encoding="utf-8"),
      "G4: valymo_log.txt turi TOTAL eilute")

# ---------- G6: portable varnele (pastaba 3, 2026-08-06) -----------------------
from PyQt6.QtWidgets import QCheckBox
import saugykla as _sg

G6_EXE = ROOT / "g6_exe"
G6_LA = ROOT / "g6_localappdata"
G6_EXE.mkdir(parents=True, exist_ok=True)
_g6_orig_exe = _sg.exe_dir
_g6_orig_la = os.environ.get("LOCALAPPDATA")
_sg.exe_dir = lambda: G6_EXE
os.environ["LOCALAPPDATA"] = str(G6_LA)
try:
    chk = win.findChild(QCheckBox, "chk_portable")
    check(chk is not None, "G6: 'chk_portable' egzistuoja")
    check(chk.isChecked() is False, "G6: pradzioje NE portable (varnele nuimta)")
    chk.setChecked(True)
    _pump()
    check((G6_EXE / "TempCleaner_portable.txt").exists(),
          "G6: varnele IJUNGTA -> TempCleaner_portable.txt salia exe")
    check("Portable" in win.lbl_status.text() or "portable" in win.lbl_status.text(),
          "G6: statusas pranesa apie rezima (%s)" % win.lbl_status.text())
    chk.setChecked(False)
    _pump()
    check(not (G6_EXE / "TempCleaner_portable.txt").exists(),
          "G6: varnele NUIMTA -> zymeklis dingo")

    # G7: kalbos combobox (2026-08-06) - pasirinkimas i kalba.txt + restartas
    from PyQt6.QtWidgets import QComboBox
    cmb = win.findChild(QComboBox, "cmb_kalba")
    check(cmb is not None, "G7: 'cmb_kalba' egzistuoja")
    if cmb is not None:
        # Restarta stub'inam: question patch'as grazina Yes, tikras
        # _perleisti_programa uzdarytu patikros QApplication
        RESTART = [0]
        win._perleisti_programa = lambda: RESTART.__setitem__(0, RESTART[0] + 1)
        cmb.setCurrentIndex(1)   # English
        _pump()
        kf = G6_LA / "TempCleaner" / "kalba.txt"
        check(kf.exists() and kf.read_text(encoding="utf-8").strip() == "en",
              "G7: pasirinkus English kalba.txt = 'en'")
        check(RESTART[0] == 1,
              "G7: sutikus (Yes) kvieciamas programos perleidimas")
        cmb.setCurrentIndex(0)   # atgal i LT
        _pump()
        check(kf.read_text(encoding="utf-8").strip() == "lt",
              "G7: grizus i Lietuviu kalba.txt = 'lt'")
finally:
    _sg.exe_dir = _g6_orig_exe
    if _g6_orig_la is None:
        os.environ.pop("LOCALAPPDATA", None)
    else:
        os.environ["LOCALAPPDATA"] = _g6_orig_la

# ---------- G5: RAUDONA Clear isjungtas (tekstinis Clear nuo 2026-08-05) -------
red_disabled = None
green_has_clear = None
for r in range(win.table.rowCount()):
    tipas = win.table.item(r, 3).text()
    it4 = win.table.item(r, 4)
    if tipas == "RAUDONA" and red_disabled is None:
        red_disabled = (it4 is None or it4.text() == "")
    if tipas == "ZALIA" and green_has_clear is None:
        green_has_clear = (it4 is not None and it4.text() == "Clear")
check(red_disabled is True, "G5: RAUDONOS eilutes Clear tuscias (isjungta)")
check(green_has_clear is True, "G5: ZALIOS eilutes Clear tekstas yra")

# ---------- Verdiktas ----------------------------------------------------------
win.close()
_pump()
del os.environ["VALYTUVAS_TESTBED"]
shutil.rmtree(ROOT, ignore_errors=True)
print("-" * 60)
if FAILS:
    print("[FAIL] patikra_gui_flow: %d klaidu(-os):" % len(FAILS))
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("[OK] patikra_gui_flow: kontraktas + skenas + perziura + slankiklis zali")
sys.exit(0)
