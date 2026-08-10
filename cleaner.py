"""cleaner.py - Cleaning logic and logging for Temp Cleaner."""

import os
import time
from datetime import datetime
from pathlib import Path

from models import AGE_DAYS, LogEntry


def _is_reparse(path):
    """Check if path is a reparse point (junction or symlink)."""
    try:
        st = os.lstat(str(path))
        return bool(getattr(st, "st_file_attributes", 0) & 0x400)
    except OSError:
        return False


def _safe_is_dir(path):
    """Safe is_dir - returns False on any OSError (sockets, stub files, etc)."""
    try:
        return path.is_dir()
    except OSError:
        return False


def clean_folder(folder_path, log_entries=None, age_days=None, dry_run=False):
    """Clean a single folder. Only delete FILES, not dirs. Skip fresh/locked/reparse.

    age_days: amziaus riba dienomis (None -> models.AGE_DAYS numatytoji).
    dry_run: True -> NIEKO netrina, tik zurnaluoja WOULD_DELETE (Perziuros rezimas).
    Returns (deleted_count, deleted_bytes, skipped_count).
    Appends LogEntry objects to log_entries list.
    """
    if log_entries is None:
        log_entries = []
    if age_days is None:
        age_days = AGE_DAYS

    cutoff = time.time() - age_days * 86400
    base = Path(folder_path)
    deleted_cnt = 0
    deleted_bytes = 0
    skipped_cnt = 0

    if not _safe_is_dir(base):
        return 0, 0, 0

    for root, dirs, files in os.walk(str(base)):
        rp_root = Path(root)
        # Log reparse point directories as SKIPPED, then exclude from walk
        skipped_dirs = [d for d in sorted(dirs) if _is_reparse(rp_root / d)]
        for sd in skipped_dirs:
            log_entries.append(LogEntry("SKIPPED", str(rp_root / sd), "JUNCTION", 0))
            skipped_cnt += 1
        dirs[:] = [d for d in dirs if not _is_reparse(rp_root / d)]

        for fn in files:
            fp = rp_root / fn

            # Skip reparse points entirely
            if _is_reparse(fp):
                log_entries.append(LogEntry("SKIPPED", str(fp), "JUNCTION", 0))
                skipped_cnt += 1
                continue

            try:
                st = fp.stat()
            except OSError:
                log_entries.append(LogEntry("SKIPPED", str(fp), "LOCKED", 0))
                skipped_cnt += 1
                continue

            # Age filter: only delete files older than AGE_DAYS
            if st.st_mtime >= cutoff:
                log_entries.append(
                    LogEntry("SKIPPED", str(fp), "AGE", st.st_size))
                skipped_cnt += 1
                continue

            # Perziuros rezimas: fiksuojam ka TRINTUME, nieko neliesdami.
            # LOCKED perziuroj nenustatomas (suzinoti = bandyti trinti) -
            # tas pats ribotumas kaip BleachBit Preview.
            if dry_run:
                deleted_cnt += 1
                deleted_bytes += st.st_size
                log_entries.append(
                    LogEntry("WOULD_DELETE", str(fp), "", st.st_size))
                continue

            # Attempt delete
            try:
                fp.unlink()
                deleted_cnt += 1
                deleted_bytes += st.st_size
                log_entries.append(
                    LogEntry("DELETED", str(fp), "", st.st_size))
            except (OSError, PermissionError):
                log_entries.append(
                    LogEntry("SKIPPED", str(fp), "LOCKED", st.st_size))
                skipped_cnt += 1

    return deleted_cnt, deleted_bytes, skipped_cnt


# Duomenu vieta (Roberto pastaba 3, 2026-08-06): sprendzia saugykla.py -
# portable rezime _darbal salia exe, kitaip %LOCALAPPDATA%/TempCleaner.
# _ROOT paliktas kaip TESTU OVERRIDAS: patikros nustato cleaner._ROOT =
# <poligonas> ir duomenys rasomi <poligonas>/_darbal (izoliacija).
_ROOT = None


def _data_dir():
    if _ROOT is not None:
        return Path(_ROOT) / "_darbal"
    import saugykla
    return saugykla.data_dir()


def write_log(log_entries):
    """Append a RUN block to <data_dir>/valymo_log.txt (APPEND mode)."""
    log_path = _data_dir() / "valymo_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    deleted_bytes = sum(e.size_bytes for e in log_entries if e.operation == "DELETED")
    n_deleted = sum(1 for e in log_entries if e.operation == "DELETED")
    n_skipped = sum(1 for e in log_entries if e.operation == "SKIPPED")

    lines = []
    ts = datetime.now().isoformat()
    lines.append("RUN %s" % ts)

    for e in log_entries:
        if e.operation == "DELETED":
            lines.append("DELETED %s" % e.path)
        elif e.operation == "SKIPPED":
            lines.append("SKIPPED %s | %s" % (e.path, e.reason))

    size_mb = deleted_bytes / 1048576.0
    # size_b= tikslumui (size_mb=0.00 pamesdavo smulkius kiekius skaitliuke);
    # senos TOTAL eilutes be size_b lieka skaitomos per size_mb.
    lines.append(
        "TOTAL deleted=%d size_mb=%.2f skipped=%d size_b=%d"
        % (n_deleted, size_mb, n_skipped, deleted_bytes))

    with open(log_path, "a", encoding="utf-8") as fh:
        for line in lines:
            fh.write(line + "\n")

    return n_deleted, size_mb, n_skipped


def clean_green_candidates(candidates, age_days=None, progress_callback=None):
    """Clean all ZALIA candidates. Returns (deleted, size_mb, skipped).

    progress_callback: optional callable(path, deleted, bytes, skipped)
    called after each location is cleaned (gyvas zurnalas valymo metu).
    """
    all_log = []
    total_del = 0
    total_bytes = 0
    total_skip = 0

    for c in candidates:
        if c.color != "ZALIA":
            continue
        d, b, s = clean_folder(c.path, all_log, age_days=age_days)
        total_del += d
        total_bytes += b
        total_skip += s
        if progress_callback is not None:
            progress_callback(c.path, d, b, s)

    n_del, size_mb, n_skip = write_log(all_log)
    return n_del, size_mb, n_skip


def clean_single_candidate(candidate, age_days=None):
    """Clean one candidate. Returns (deleted, size_mb, skipped)."""
    log_entries = []
    d, b, s = clean_folder(candidate.path, log_entries, age_days=age_days)
    n_del, size_mb, n_skip = write_log(log_entries)
    return n_del, size_mb, n_skip


def preview_candidates(candidates, age_days=None):
    """Perziuros (dry-run) rezimas: kas BUTU istrinta is ZALIU ir GELTONU vietu.

    NIEKO netrina ir valymo_log.txt NErasomas (zurnalas - tik tikru veiksmu
    auditas). Grazina (per_location, total_cnt, total_bytes), kur per_location -
    sarasas (path, color, would_cnt, would_bytes).
    """
    per_location = []
    total_cnt = 0
    total_bytes = 0
    for c in candidates:
        if c.color not in ("ZALIA", "GELTONA"):
            continue
        entries = []
        d, b, _s = clean_folder(c.path, entries, age_days=age_days, dry_run=True)
        per_location.append((c.path, c.color, d, b))
        total_cnt += d
        total_bytes += b
    return per_location, total_cnt, total_bytes


def preview_from_buckets(candidates, age_days):
    """AKIMIRKSNINE perziura is skeno amziaus kibireliu - be jokio disko.

    Grazina (per_location, total_cnt, total_bytes) kaip preview_candidates,
    arba None, jei bent vienam ZALIA/GELTONA kandidatui kibireliu nera
    (tada krenta atgal i gyva perziura). Skaiciai - skeno momento bukles
    ivertis; tikras valymas mtime tikrina is naujo.
    """
    per_location = []
    total_cnt = 0
    total_bytes = 0
    for c in candidates:
        if c.color not in ("ZALIA", "GELTONA"):
            continue
        af = getattr(c, "age_files", None)
        ab = getattr(c, "age_bytes", None)
        if not af or not ab or len(af) != 31 or len(ab) != 31:
            return None
        idx = 30 if age_days > 30 else int(age_days)
        cnt = sum(af[idx:])
        b = sum(ab[idx:])
        per_location.append((c.path, c.color, cnt, b))
        total_cnt += cnt
        total_bytes += b
    return per_location, total_cnt, total_bytes


def read_total_freed():
    """Suskaiciuoja viso atlaisvinta MB is valymo_log.txt TOTAL eiluciu.

    Grazina (runs_count, total_mb). Zurnalo nera -> (0, 0.0).
    """
    log_path = _data_dir() / "valymo_log.txt"
    runs = 0
    total_mb = 0.0
    try:
        with open(log_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("TOTAL "):
                    runs += 1
                    toks = dict(t.split("=", 1) for t in line.split()[1:] if "=" in t)
                    try:
                        if "size_b" in toks:      # nauja tiksli forma
                            total_mb += int(toks["size_b"]) / 1048576.0
                        else:                     # senos eilutes be size_b
                            total_mb += float(toks.get("size_mb", "0"))
                    except ValueError:
                        pass
    except OSError:
        pass
    return runs, total_mb
