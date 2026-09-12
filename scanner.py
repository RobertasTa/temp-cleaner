"""scanner.py - Scanning logic: resolve bases, green list, heuristic scan, count."""

import os
from pathlib import Path

from models import (
    Candidate, GREEN_RELATIVES, GREEN_BASE_INDEX,
    BLACKLIST_NAMES, HEURISTIC_NAMES,
    SINCHRONIZACIJOS_VARDAI, MOKAMU_VARDAI, PALIKTI_VERSIJU,
)


# --- ZYDRA: "Sprendziate jus" (2026-09-12) -----------------------------------
# Sviesoforas lieka trims spalvoms = ka PROGRAMA siulo daryti. Zydra reiskia,
# kad radom ka nors, ko patys nesiulom liesti: sprendzia zmogus.
#
# Roberto masinoje 08-31 pamatuota, ka TC butu SIULES valyti GELTONAI, nors
# negalima: SynologyDrive	emp (1 018 504 failai, 6,5 GB, naujausias TA PACIA
# diena), Autodesk\Inventor 2026\Logs, hermes\cache. Synology yra gyva
# sinchronizacijos zona, Inventorius - Roberto pajamos.
#
# NAUDOJAMA_DABAR yra BENDRINIS pozymis: jokio saraso nereikia, ir butent jis
# butu pagaves ir Synology, ir Inventoriu. Vardu sarasai (sinchronizacija,
# mokamos programos) visada nepilni - tai pasakyta README, o ne apsimesta,
# kad atpazistam viska.

_VERSIJOS_SABLONAS = None


# Kiek failu, jaunesniu nei para, reiskia "cia rasoma DABAR".
# PAMATUOTA 2026-09-12 ant Roberto kompiuterio (474 rastos vietos, `_darbal/matuok_zydra.py`):
#   riba 1  -> 22 vietos, tarp ju Opera kesas su 6 svieziais failais (valyti saugu)
#   riba 20 ->  6 vietos: SynologyDrive	emp (87 022 svieziu is 1 142 091), Claude kesas
#               (veikia dabar), claude-cli kesas, USOShared\Logs - butent tos, kurias
#               ir norim rodyti
# DALIES kriterijaus (procento nuo visu failu) ATSISAKYTA: Synology sviezi failai sudaro
# tik 8 % is milijono, tad bet koks procentas ji praleistu - o jis cia pagrindinis taikinys.
SVIEZIU_FAILU_RIBA = 20


def _naudojama_dabar(age_files):
    """Ar kataloge DABAR rasoma: bent SVIEZIU_FAILU_RIBA failu jaunesni nei para.

    Amziaus kibireliai jau suskaiciuoti skeno metu (`_count_files_buckets`),
    todel sis patikrinimas NIEKO nekainuoja - jokio papildomo disko skaitymo.
    """
    return bool(age_files) and age_files[0] >= SVIEZIU_FAILU_RIBA


def _vardas_sarase(kelias, sarasas):
    """Ar kuri nors kelio dalis yra sarase (be raidziu dydzio)."""
    try:
        dalys = [d.lower() for d in Path(kelias).parts]
    except (OSError, ValueError):
        return False
    return any(d in sarasas for d in dalys)


def _versijuotas_katalogas(kelias):
    """Ar katalogo vardas atrodo kaip programos versija (app-1.2.3, 2.0.4, v3).

    Naudojama tik kaip pozymis: jei tevo kataloge tokiu yra daugiau nei
    PALIKTI_VERSIJU, senesnes laikom kandidatemis, kurias rodom, bet nesiulom.
    """
    global _VERSIJOS_SABLONAS
    if _VERSIJOS_SABLONAS is None:
        import re
        _VERSIJOS_SABLONAS = re.compile(r"(^|[-_ ])v?\d+\.\d+(\.\d+)*($|[-_ ])")
    try:
        return bool(_VERSIJOS_SABLONAS.search(Path(kelias).name.lower()))
    except (OSError, ValueError):
        return False


def zydra_priezastis(kelias, age_files):
    """-> priezasties raktas arba "" (tada spalva nesikeicia).

    Tvarka = prioritetas: viena vieta gali atitikti kelis pozymius
    (Synology temp yra IR sinchronizacija, IR naudojama dabar).
    """
    if _vardas_sarase(kelias, SINCHRONIZACIJOS_VARDAI):
        return "SINCHRONIZACIJA"
    if _vardas_sarase(kelias, MOKAMU_VARDAI):
        return "MOKAMA_PROGRAMA"
    if _naudojama_dabar(age_files):
        return "NAUDOJAMA_DABAR"
    return ""


def get_bases():
    """Return tuple of 5 base roots. TESTBED -> fake; else real OS dirs."""
    tb = os.environ.get("VALYTUVAS_TESTBED")
    if tb:
        # Normalize path: MSYS /d/... -> D:/... for Python compatibility
        norm_tb = os.path.normpath(str(tb))
        return (
            Path(norm_tb) / "Users/User/AppData/Local/Temp",
            Path(norm_tb) / "Windows/Temp",
            Path(norm_tb) / "Users/User/AppData/Local",
            Path(norm_tb) / "Users/User/AppData/Roaming",
            Path(norm_tb) / "ProgramData",
        )
    import os as _os
    return (
        Path(_os.environ.get("TEMP", "")),
        Path(_os.environ.get("WINDIR", "C:/Windows")) / "Temp",
        Path(_os.environ.get("LOCALAPPDATA", "")),
        Path(_os.environ.get("APPDATA", "")),
        Path(_os.environ.get("PROGRAMDATA", "")),
    )


def _is_reparse(path):
    """True for junction or symlink (reparse point)."""
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


def _count_files_buckets(folder, now=None):
    """Vienu os.scandir perejimu: failu sk., baitai ir AMZIAUS KIBIRELIAI.

    Grazina (count, total, age_files, age_bytes) - kibireliai po 31:
    indeksas = amzius dienomis (0..29), paskutinis 30+. Reparse
    (junction/symlink) neseka ir neskaiciuoja. 2026-08-05 greitinimas:
    os.walk+lstat kiekvienam failui dare ~3 syscall, scandir viska
    gauna is katalogo skaitymo.
    """
    import time as _time
    if now is None:
        now = _time.time()
    count = 0
    total = 0
    age_files = [0] * 31
    age_bytes = [0] * 31
    stack = [str(folder)]
    while stack:
        current = stack.pop()
        try:
            it = os.scandir(current)
        except OSError:
            continue
        with it:
            for entry in it:
                try:
                    st = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                if getattr(st, "st_file_attributes", 0) & 0x400:
                    continue          # reparse - nei sekam, nei skaiciuojam
                try:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                except OSError:
                    continue
                count += 1
                total += st.st_size
                age_d = int((now - st.st_mtime) // 86400)
                idx = 0 if age_d < 0 else (30 if age_d > 30 else age_d)
                age_files[idx] += 1
                age_bytes[idx] += st.st_size
    return count, total, age_files, age_bytes


def _count_files_size(folder):
    """Count files and total bytes under folder. Skip reparse points."""
    cnt, total, _af, _ab = _count_files_buckets(folder)
    return cnt, total


def resolve_green_locations(bases):
    """Resolve curated green locations from bases."""
    result = []
    for rel, base_idx in zip(GREEN_RELATIVES, GREEN_BASE_INDEX):
        if base_idx == 0:
            root = bases[0]       # TEMP
        elif base_idx == 1:
            root = bases[1]       # WINTEMP
        else:
            root = bases[2]       # LOCALAPPDATA
        loc = root / rel if rel else root
        result.append(loc)
    return result


def _has_blacklist_on_path(base_dir, candidate):
    """Check whether any component of the relative path is in blacklist."""
    try:
        rel = Path(candidate).relative_to(Path(base_dir))
    except ValueError:
        return False
    for part in rel.parts:
        if part.lower() in BLACKLIST_NAMES:
            return True
    return False


def _has_blacklist_inside(candidate):
    """Quick 1-level scan inside candidate dir for blacklisted subfolder names."""
    try:
        if not _safe_is_dir(Path(candidate)):
            return False
    except (OSError, PermissionError):
        return False
    try:
        for child in Path(candidate).iterdir():
            if child.name.lower() in BLACKLIST_NAMES:
                return True
    except (OSError, PermissionError):
        pass
    return False


def heuristic_scan(bases, on_hit=None):
    """Walk LOCALAPPDATA, APPDATA, PROGRAMDATA looking for temp/tmp/cache/logs.

    on_hit: optional callable(Path) called IMMEDIATELY for each match found
    (Roberto gyvo testo pamoka 2026-08-06: zurnalas ~2 min tuscias, nes
    visas medis pereinamas PRIES pradedant skaiciuoti - dabar srautas).
    """
    results = set()
    search_roots = [bases[2], bases[3], bases[4]]
    for root in search_roots:
        if not _safe_is_dir(root):
            continue
        _walk_heuristic(root, root, results, on_hit)
    return results


def _walk_heuristic(base_root, current, results, on_hit=None):
    """Recursively walk and collect heuristic matches."""
    try:
        entries = list(current.iterdir())
    except (OSError, PermissionError):
        return

    for entry in entries:
        if not _safe_is_dir(entry):
            continue
        if _is_reparse(entry):
            continue
        if entry.name.lower() in HEURISTIC_NAMES:
            results.add(entry)
            if on_hit is not None:
                on_hit(entry)
            continue  # do not descend into a candidate
        _walk_heuristic(base_root, entry, results, on_hit)


def scan(progress_callback=None):
    """Main scan - returns list of Candidate objects.

    progress_callback: optional callable(candidate) called after each candidate is built.
    SRAUTINIS (2026-08-06, Roberto pastaba 1): zalios vietos suskaiciuojamos
    ir pranesamos PIRMOS (zurnalas atgyja per sekundes), o heuristiniai
    radiniai apdorojami IS KARTO juos radus medyje - ne po viso perejimo.
    Rezultatu aibe ta pati kaip anksciau; eile - radimo tvarka (lentele
    vis tiek rusiuojama _fill_table).
    """
    bases = get_bases()

    green_paths = resolve_green_locations(bases)

    # Green resolved set for dedup (heuristic hits inside green are skipped)
    seen_abs = set()
    for g in green_paths:
        try:
            seen_abs.add(str(g.resolve()))
        except OSError:
            pass

    candidates = []
    green_str_set = set()

    # Green locations first
    for gp in green_paths:
        p_str = str(gp)
        if p_str in green_str_set:
            continue
        if _safe_is_dir(gp):
            cnt, sz, af, ab = _count_files_buckets(gp)
            candidates.append(Candidate(path=p_str, file_count=cnt,
                                        total_bytes=sz, color="ZALIA",
                                        age_files=af, age_bytes=ab))
            if progress_callback is not None:
                progress_callback(candidates[-1])
            green_str_set.add(p_str)

    # Heuristic locations: process each hit IMMEDIATELY as the walk finds it
    seen_str = set(green_str_set)

    def _on_hit(hp):
        p_str = str(hp)
        if p_str in seen_str:
            return
        try:
            h_resolved = str(hp.resolve())
        except OSError:
            h_resolved = p_str
        for ga in seen_abs:
            if h_resolved == ga or h_resolved.startswith(ga + os.sep):
                return   # inside a green location - already covered
        if not _safe_is_dir(hp):
            return
        # Check blacklist on path from each base AND inside candidate dir
        is_red = False
        for brt in [bases[2], bases[3], bases[4]]:
            try:
                if _has_blacklist_on_path(brt, hp):
                    is_red = True
                    break
            except (ValueError, OSError):
                continue
        if not is_red and _has_blacklist_inside(hp):
            is_red = True

        cnt, sz, af, ab = _count_files_buckets(hp)
        color = "RAUDONA" if is_red else "GELTONA"
        # RAUDONA stipresne uz ZYDRA: draudimas lieka draudimu. Zydra keicia
        # tik GELTONA - t.y. ta, kuria programa butu siuliusi valyti.
        zydra_del = "" if is_red else zydra_priezastis(p_str, af)
        if zydra_del:
            color = "ZYDRA"
        candidates.append(Candidate(path=p_str, file_count=cnt,
                                    total_bytes=sz, color=color,
                                    zydra_del=zydra_del,
                                    age_files=af, age_bytes=ab))
        if progress_callback is not None:
            progress_callback(candidates[-1])
        seen_str.add(p_str)

    heuristic_scan(bases, on_hit=_on_hit)

    return candidates
