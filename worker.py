"""worker.py - QThread worker for scanning and cleaning."""

import dataclasses
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from scanner import scan as do_scan
from cleaner import clean_green_candidates


class ScanWorker(QObject):
    """Worker object that lives in a QThread. Thin wrapper around engine."""

    started = pyqtSignal()               # emitted when scanning begins
    progress = pyqtSignal(int, str)      # index, message (emitted during scan)
    done = pyqtSignal(object)            # list of Candidate (object for PyQt6 cross-thread)
    error_signal = pyqtSignal(str)       # error message

    def __init__(self):
        super().__init__()
        self._candidates = None

    @pyqtSlot()
    def run(self):
        try:
            self.started.emit()

            _counter = [0]

            def _on_candidate(c):
                """Called by scanner for each candidate found."""
                mb = c.total_bytes / 1048576.0
                self.progress.emit(_counter[0], "%s (%.2f MB)" % (c.path, mb))
                _counter[0] += 1

            results = do_scan(progress_callback=_on_candidate)
            self._candidates = results
            # Serialize to plain dicts BEFORE emitting across thread boundary.
            # dataclasses.asdict() creates new dict objects detached from the worker's
            # Candidate instances, so they are safe even after deleteLater().
            # pyqtSignal(object) handles arbitrary Python objects (list[dict] works fine);
            # pyqtSignal(list) tries QVariantList conversion which corrupts dict keys.
            self.done.emit([dataclasses.asdict(c) for c in results])
        except Exception as e:
            self.error_signal.emit("Scan error: " + str(e))


class PreviewWorker(QObject):
    """Perziuros (dry-run) darbininkas fone - GUI nestingsta (Roberto gyvo
    testo pamoka 2026-08-05: 440 vietu perziura sinchroniskai = smelio
    laikrodis be jokio zenklo)."""

    done = pyqtSignal(object)            # (per_location, total_cnt, total_bytes)
    error_signal = pyqtSignal(str)

    def __init__(self, candidates, age_days):
        super().__init__()
        self._candidates = candidates
        self._age_days = age_days

    @pyqtSlot()
    def run(self):
        try:
            from cleaner import preview_candidates
            result = preview_candidates(self._candidates, age_days=self._age_days)
            self.done.emit(result)
        except Exception as e:
            self.error_signal.emit("Preview error: " + str(e))


class CleanWorker(QObject):
    """Valymo darbininkas fone (Roberto gyvo testo pamoka 2026-08-06:
    sinchroninis Clean all GREEN = Not Responding keliolika sekundziu be
    jokio zenklo; dabar QThread + overlay MM:SS kaip Preview).

    candidates ir age_days paduodami konstruktoriuje - snapshot pagrindineje
    gijoje (OKF signalu guard 2: GUI reiksmiu is fono gijos neskaitom).
    """

    progress = pyqtSignal(str)           # zurnalo eilute po kiekvienos vietos
    done = pyqtSignal(int, float, int)   # deleted_count, size_mb, skipped
    error_signal = pyqtSignal(str)

    def __init__(self, candidates, age_days):
        super().__init__()
        self._candidates = candidates
        self._age_days = age_days

    @pyqtSlot()
    def run(self):
        try:
            from kalba import t, spalva

            def _on_location(path, d, b, s):
                self.progress.emit(
                    t("[{}] {} -> istrinta {} failu, {:.2f} MB, praleista {}").format(
                        spalva("ZALIA"), path, d, b / 1048576.0, s))

            d, mb, s = clean_green_candidates(
                self._candidates, age_days=self._age_days,
                progress_callback=_on_location)
            self.done.emit(d, mb, s)
        except Exception as e:
            self.error_signal.emit("Clean error: " + str(e))
