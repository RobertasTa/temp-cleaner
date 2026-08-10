"""handlers.py - Button handlers: QThread scan, sync clean operations."""

from pathlib import Path
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from scanner import scan, _count_files_size
from cleaner import clean_single_candidate, preview_candidates
from worker import ScanWorker
from kalba import t, spalva


def handler_on_preview(gui):
    """Perziuros (dry-run) rezimas FONE: parodo, kas BUTU trinta - NIEKO netrina.

    Roberto gyvo testo pamoka 2026-08-05: 440 vietu sinchroniskai = Not
    Responding. Dabar QThread + overlay laikrodukas, kaip skeno.
    """
    if not gui._candidates:
        QMessageBox.information(
            gui, t("Perziura"), t("Pirma paleiskite skena."))
        return

    # AKIMIRKSNINIS kelias (2026-08-05 greitinimas): jei skenas surinko
    # amziaus kibirelius - jokio disko, tik aritmetika.
    from cleaner import preview_from_buckets
    age = gui.age_days()
    instant = preview_from_buckets(gui._candidates, age)
    if instant is not None:
        gui._preview_age = age
        gui.log_box.clear()
        gui._log(t("=== PERZIURA (amziaus riba {} d.) - NIEKAS NETRINAMA ===").format(age))
        preview_show_results(gui, instant)
        return

    # Atsarga: kandidatai be kibireliu (pvz., senas kesas) - gyva perziura fone
    # Guard: laukiam ankstesnes gijos (OKF threading guard, kaip skeno)
    try:
        if gui._working_thread is not None and gui._working_thread.isRunning():
            gui._working_thread.quit()
            gui._working_thread.wait(1000)
    except RuntimeError:
        pass

    from worker import PreviewWorker
    age = gui.age_days()
    gui._preview_age = age
    gui.log_box.clear()
    gui._log(t("=== PERZIURA (amziaus riba {} d.) - NIEKAS NETRINAMA ===").format(age))

    worker = PreviewWorker(list(gui._candidates), age)
    thread = QThread()
    worker.moveToThread(thread)
    gui._worker = worker   # OKF guard: nuoroda, kad GC nesurinktu

    # OKF guard 1c: bound GUI metodai (ne lambdos) -> auto-queued i main thread
    worker.done.connect(gui._on_preview_done)
    worker.error_signal.connect(gui._on_worker_error)
    worker.done.connect(thread.quit)
    worker.error_signal.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.started.connect(worker.run)

    gui.btn_scan.setEnabled(False)
    gui.btn_preview.setEnabled(False)
    gui.btn_clear_all.setEnabled(False)
    gui._show_scan_overlay(t("Vyksta perziura"))
    gui._working_thread = thread
    thread.start()


def preview_show_results(gui, data):
    """Perziuros rezultatu isvedimas (kvieciamas is _on_preview_done, main gija).

    Roberto pastaba 6 (2026-08-06): bendra suma klaidino - Preview sumavo
    ZALIAS+GELTONAS, o mygtukas 'Valyti viska' valo TIK zalias. Dabar
    sumos rodomos atskirai.
    """
    per_loc, total_cnt, total_bytes = data
    age = getattr(gui, "_preview_age", gui.age_days())

    g_cnt = g_bytes = y_cnt = y_bytes = 0
    for path, color, cnt, nbytes in per_loc:
        mb = nbytes / 1048576.0
        gui._log(t("[{}] {} -> butu trinta {} failu, {:.2f} MB").format(
            spalva(color), path, cnt, mb))
        if color == "ZALIA":
            g_cnt += cnt
            g_bytes += nbytes
        else:
            y_cnt += cnt
            y_bytes += nbytes

    total_mb = total_bytes / 1048576.0
    g_mb = g_bytes / 1048576.0
    y_mb = y_bytes / 1048576.0
    gui._log(t("=== IS VISO butu trinta: {} failu, {:.2f} MB ===").format(
        total_cnt, total_mb))
    gui._log(t("    ZALIOS vietos (jas valo mygtukas): {} failu, {:.2f} MB").format(
        g_cnt, g_mb))
    gui._log(t("    GELTONOS vietos (tik po viena, su patvirtinimu): {} failu, {:.2f} MB").format(
        y_cnt, y_mb))
    gui.lbl_status.setText(
        t("Perziura: butu trinta ZALIOSE {} failu / {:.2f} MB, GELTONOSE {} failu / {:.2f} MB (riba {} d.)").format(
            g_cnt, g_mb, y_cnt, y_mb, age))
    QMessageBox.information(
        gui, t("Perziura baigta"),
        t("ZALIOS vietos: {} failu ({:.2f} MB) - tiek istrins mygtukas "
          "'Valyti viska is zaliu vietu'.\n"
          "GELTONOS vietos: {} failu ({:.2f} MB) - valomos tik po viena, "
          "su patvirtinimu.\n"
          "Amziaus riba: {} d.\n"
          "NIEKAS neistrinta - tai tik perziura.").format(
            g_cnt, g_mb, y_cnt, y_mb, age))


def handler_on_scan(gui):
    """Scan in background QThread (UZDUOTIS 3 sk: GUI nestringa)."""
    # Guard: stop previous thread if still running (OKF threading guard).
    # try/except: po deleteLater wrapper'is gali buti mires -> isRunning()
    # mestu RuntimeError (guard SVARBU pastaba); mires = nebeveikia, tesiam.
    try:
        if gui._working_thread is not None and gui._working_thread.isRunning():
            gui._working_thread.quit()
            gui._working_thread.wait(1000)
    except RuntimeError:
        pass

    worker = ScanWorker()
    thread = QThread()
    worker.moveToThread(thread)

    # OKF guard: preserve instance-level reference so GC does not collect worker
    # before thread.started.connect(worker.run) fires. See diag_run_called.txt.
    gui._worker = worker

    # OKF guard 1c: connect worker signals to BOUND GUI methods (not lambdas/closures).
    # Bound QObject slots auto-dispatch via Qt.QueuedConnection to main thread.
    worker.progress.connect(gui._on_worker_progress)   # was: lambda i,m: gui._log(m)
    worker.done.connect(gui._on_worker_done)            # was: _on_done closure
    worker.error_signal.connect(gui._on_worker_error)   # was: _on_error closure

    # OKF guard 4: after GUI update, quit the thread (done and error both end work)
    worker.done.connect(thread.quit)
    worker.error_signal.connect(thread.quit)

    # OKF guard: thread.finished -> deleteLater for BOTH objects.
    # Nuorodu (gui._worker/_working_thread) NENULINAM niekur - jas
    # perraso kitas skenas. Nulinimas done handleryje = destroyed while
    # running (0xC0000409); nulinimas per finished = lenktynes su nauju
    # skenu (senos gijos finished nunulintu naujo skeno nuoroda).
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.started.connect(worker.run)

    # Set button state BEFORE thread starts - visible immediately
    gui.btn_scan.setText(t("Skenuojama..."))
    gui.btn_scan.setEnabled(False)
    gui._show_scan_overlay()
    gui._working_thread = thread
    thread.start()


def handler_on_clean_green(gui):
    """Valo visas ZALIAS vietas FONE (QThread + overlay MM:SS kaip Preview).

    Roberto gyvo testo pamoka 2026-08-06: sinchroninis valymas = Not
    Responding keliolika sekundziu be jokio zenklo (laikroduka turejo visi,
    tik ne sis mygtukas), o zurnalas likdavo tuscias - matesi tik dialogo
    santrauka. Dabar: gija + overlay + gyvos eilutes po kiekvienos vietos,
    zurnalas po valymo LIEKA (Roberto pastaba 5).
    """
    # Guard: wait for previous QThread to finish (OKF threading guard).
    # try/except RuntimeError: wrapper po deleteLater gali buti mires.
    try:
        if gui._working_thread is not None and gui._working_thread.isRunning():
            gui._working_thread.quit()
            gui._working_thread.wait(1000)
    except RuntimeError:
        pass

    green_candidates = [c for c in gui._candidates if c.color == "ZALIA"]
    if not green_candidates:
        return

    # Ask confirmation once for all green locations
    reply = QMessageBox.question(
        gui, t("Patvirtinimas"),
        t("Valyti visas ZALIAS vietas?"),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if reply != QMessageBox.StandardButton.Yes:
        return

    from worker import CleanWorker
    age = gui.age_days()   # snapshot main gijoje (OKF signalu guard 2)
    gui.log_box.clear()
    gui._log(t("=== VALYMAS (amziaus riba {} d.) ===").format(age))

    worker = CleanWorker(list(green_candidates), age)
    thread = QThread()
    worker.moveToThread(thread)
    gui._worker = worker   # OKF guard: nuoroda, kad GC nesurinktu

    # OKF guard 1c: bound GUI metodai (ne lambdos) -> auto-queued i main thread
    worker.progress.connect(gui._on_clean_progress)
    worker.done.connect(gui._on_clean_done)
    worker.error_signal.connect(gui._on_clean_error)
    worker.done.connect(thread.quit)
    worker.error_signal.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.started.connect(worker.run)

    gui.btn_scan.setEnabled(False)
    gui.btn_preview.setEnabled(False)
    gui.btn_clear_all.setEnabled(False)
    gui._show_scan_overlay(t("Vyksta valymas"))
    gui._working_thread = thread
    thread.start()


def handler_on_clean_row(gui, folder_path):
    """Clean a single row's location (GELTONA/ ZALIA). RAUDONA disabled."""
    cand = None
    for c in gui._candidates:
        if c.path == folder_path:
            cand = c
            break

    if cand is None:
        return

    # GELTONA needs confirmation (UZDUOTIS 6 sk: static QMessageBox.question)
    if cand.color != "ZALIA":
        reply = QMessageBox.question(
            gui, t("Patvirtinimas"),
            t("Ar norite valyti GELTONA vieta? {}").format(folder_path),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        # OKF: returns QMessageBox.StandardButton enum
        if reply != QMessageBox.StandardButton.Yes:
            return

    try:
        d, mb, s = clean_single_candidate(cand, age_days=gui.age_days())
        gui._update_freed_label()

        # P4 fix (B2): RE-SCAN the folder instead of zeroing out.
        # After cleaning, some files remain (junctions, fresh files < 7 days).
        # Get actual remaining file count and size from disk.
        from scanner import _count_files_buckets
        remaining_count, remaining_bytes, af, ab = _count_files_buckets(
            Path(cand.path))

        # Update candidate in place with real remaining numbers (+ kibireliai,
        # kad akimirksnine perziura po valymo rodytu sviezius skaicius)
        cand.file_count = remaining_count
        cand.total_bytes = remaining_bytes
        cand.age_files = af
        cand.age_bytes = ab

        # Update table row with real remaining stats
        for idx in range(gui.table.rowCount()):
            item = gui.table.item(idx, 0)
            if item and item.text() == folder_path:
                gui.table.setItem(
                    idx, 1, QTableWidgetItem(str(remaining_count)))
                size_mb = remaining_bytes / 1048576.0
                gui.table.setItem(
                    idx, 2, QTableWidgetItem("{:.2f}".format(size_mb)))

                # Nebera ka valyti - Clear tekstas isjungiamas (istustinamas)
                clear_item = gui.table.item(idx, 4)
                if clear_item is not None and remaining_count == 0:
                    clear_item.setText("")
                break

        gui.lbl_status.setText(
            t("Istrinta {} failu, {:.2f} MB, praleista {}").format(d, mb, s))
        QMessageBox.information(
            gui, t("Valymas baigtas"),
            t("Istrinta {} failu\nIs viso: {:.2f} MB\nPraleista: {}").format(
                d, mb, s))
    except Exception as e:
        gui._log("Clean error: " + str(e))
        QMessageBox.critical(
            gui, t("Valymo klaida"),
            t("Klaida: {}").format(str(e)))
