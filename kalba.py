"""
kalba.py - GUI kalbos sluoksnis (2026-08-05, pagal dubliu programos sablona).
Lietuviskas tekstas = zodyno raktas; t() grazina vertima arba pati rakta.

Kalbos parinkimo prioritetai (2026-08-06, Roberto pastaba "du exe del
kalbos - negrazu"; dabar VIENAS exe su pasirinkimu GUI):
  1. VALYTUVAS_LANG aplinkos kintamasis (testu izoliacija / prievarta)
  2. kalba.txt darbiniu failu kataloge (GUI combobox pasirinkimas;
     portable rezime keliauja su flesiuku kartu su TempCleaner_portable.txt)
  3. lang_en.flag salia exe (senoji -en buildu veliavele, suderinamumas)
  4. OS kalba (Roberto 2026-08-06 "vienas exe visom kalbom"): lietuviska
     sistema -> LT, kitaip -> EN. Nauja kalba ateityje = zodynas + eilute
     combobox'e.
Zero Qt priklausomybiu.
"""
import os
import sys
from pathlib import Path


def _base():
    return Path(getattr(sys, "_MEIPASS", str(Path(__file__).resolve().parent)))


def _issaugota_kalba():
    """Skaito GUI pasirinkima is kalba.txt (saugyklos data_dir)."""
    try:
        import saugykla
        v = (saugykla.data_dir() / "kalba.txt").read_text(
            encoding="utf-8").strip().lower()
        return v if v in ("lt", "en") else None
    except OSError:
        return None


def issaugoti_kalba(lang):
    """Iraso pasirinkima i kalba.txt; isigalioja perleidus programa.
    Meta OSError, jei irasyti nepavyko (pvz., read-only vieta)."""
    import saugykla
    d = saugykla.data_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "kalba.txt").write_text(lang + "\n", encoding="utf-8")


def _os_kalba():
    """OS kalbos aptikimas pirmam paleidimui: lietuviska sistema -> lt."""
    try:
        import ctypes
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        if (langid & 0x3FF) == 0x27:   # LANG_LITHUANIAN
            return "lt"
        return "en"
    except Exception:
        pass
    try:
        import locale
        loc = locale.getlocale()[0] or ""
        return "lt" if loc.lower().startswith("lt") else "en"
    except Exception:
        return "en"


_env = os.environ.get("VALYTUVAS_LANG")
if _env in ("lt", "en"):
    LANG = _env
else:
    LANG = _issaugota_kalba() or (
        "en" if (_base() / "lang_en.flag").exists() else _os_kalba())

_EN = {
    # gui_langas: langas, antrastes, valdikliai
    "Temp valytuvas": "Temp Cleaner",
    "Temp valytuvas - Sisteminiai laikini failai":
        "Temp Cleaner - System temporary files",
    "Rodymas: Visos vietos | Is viso: 0 MB": "View: All locations | Total: 0 MB",
    "ZALIA - saugu valyti automatiskai | GELTONA - tik su patvirtinimu | RAUDONA - tik perziura":
        "GREEN - safe to clean | YELLOW - confirmation required | RED - view only",
    "Katalogas": "Folder",
    "Failai": "Files",
    "Dydis (MB)": "Size (MB)",
    "Tipas": "Type",
    "Valymo zurnalas:": "Cleaning log:",
    "Skanuoti": "Scan",
    "Skenuojama...": "Scanning...",
    "Perziura (kas butu trinta)": "Preview (what would be deleted)",
    "Valyti viska is zaliu vietu": "Clean all GREEN locations",
    "Uzdaryti": "Close",
    "Vyksta skenavimas": "Scanning",
    "Vyksta perziura": "Preview running",
    "Vyksta valymas": "Cleaning",
    "Amziaus riba:": "Age limit:",
    "{} d.": "{} d.",
    "Portable rezimas (viskas salia programos)":
        "Portable mode (everything next to the app)",
    "Ijungta: zurnalas ir darbiniai failai saugomi salia programos (pvz., flesiuke) - kompiuteryje pedsaku nelieka.\nIsjungta (numatyta): saugoma vartotojo kataloge %LOCALAPPDATA%\\TempCleaner.":
        "On: the log and working files are stored next to the app (e.g. on a USB stick) - no traces left on the computer.\nOff (default): stored in the user profile at %LOCALAPPDATA%\\TempCleaner.",
    "Portable rezimas": "Portable mode",
    "Kalba": "Language",
    "Kalba pritaikoma paleidus programa is naujo.":
        "The language is applied after restarting the app.",
    "Kalba pasikeis paleidus programa is naujo.":
        "The language will change after you restart the app.",
    "Kalba issaugota. Perleisti programa dabar?":
        "Language saved. Restart the app now?",
    "Nepavyko issaugoti: {}": "Could not save: {}",
    "Nepavyko perjungti rezimo: {}": "Could not switch mode: {}",
    "Portable rezimas IJUNGTAS - duomenys salia programos":
        "Portable mode ON - data lives next to the app",
    "Portable rezimas isjungtas - duomenys vartotojo kataloge":
        "Portable mode off - data lives in the user profile",
    "Viso atlaisvinta: 0 MB": "Total freed: 0 MB",
    "Viso atlaisvinta: {:.2f} GB ({} {})": "Total freed: {:.2f} GB ({} {})",
    "Viso atlaisvinta: {:.0f} MB ({} {})": "Total freed: {:.0f} MB ({} {})",
    "Viso atlaisvinta: {:.1f} KB ({} {})": "Total freed: {:.1f} KB ({} {})",
    "Surasta {} vietu | Is viso: {:.2f} MB":
        "Found {} locations | Total: {:.2f} MB",
    "Skenuojama: rasta {} vietu...": "Scanning: {} locations found...",
    # handlers: dialogai ir statusai
    "Patvirtinimas": "Confirmation",
    "Valyti visas ZALIAS vietas?": "Clean all GREEN locations?",
    "Istrinta {} failu, {:.2f} MB, praleista {}":
        "Deleted {} files, {:.2f} MB, skipped {}",
    "Valymas baigtas": "Cleaning finished",
    "Istrinta {} failu\nIs viso: {:.2f} MB\nPraleista (junction/fresh): {}":
        "Deleted {} files\nTotal: {:.2f} MB\nSkipped (junction/fresh): {}",
    "Istrinta {} failu\nIs viso: {:.2f} MB\nPraleista: {}":
        "Deleted {} files\nTotal: {:.2f} MB\nSkipped: {}",
    "Valymo klaida": "Cleaning error",
    "=== VALYMAS (amziaus riba {} d.) ===":
        "=== CLEANING (age limit {} d.) ===",
    "[{}] {} -> istrinta {} failu, {:.2f} MB, praleista {}":
        "[{}] {} -> deleted {} files, {:.2f} MB, skipped {}",
    "=== VALYMAS BAIGTAS: istrinta {} failu, {:.2f} MB, praleista {} ===":
        "=== CLEANING FINISHED: deleted {} files, {:.2f} MB, skipped {} ===",
    "Klaida: {}": "Error: {}",
    "Ar norite valyti GELTONA vieta? {}":
        "Clean this YELLOW location? {}",
    "Perziura": "Preview",
    "Pirma paleiskite skena.": "Run a scan first.",
    "=== PERZIURA (amziaus riba {} d.) - NIEKAS NETRINAMA ===":
        "=== PREVIEW (age limit {} d.) - NOTHING IS DELETED ===",
    "[{}] {} -> butu trinta {} failu, {:.2f} MB":
        "[{}] {} -> would delete {} files, {:.2f} MB",
    "=== IS VISO butu trinta: {} failu, {:.2f} MB ===":
        "=== TOTAL would delete: {} files, {:.2f} MB ===",
    "    ZALIOS vietos (jas valo mygtukas): {} failu, {:.2f} MB":
        "    GREEN locations (cleaned by the button): {} files, {:.2f} MB",
    "    GELTONOS vietos (tik po viena, su patvirtinimu): {} failu, {:.2f} MB":
        "    YELLOW locations (one by one, with confirmation): {} files, {:.2f} MB",
    "Perziura: butu trinta {} failu, {:.2f} MB (riba {} d.)":
        "Preview: would delete {} files, {:.2f} MB (limit {} d.)",
    "Perziura: butu trinta ZALIOSE {} failu / {:.2f} MB, GELTONOSE {} failu / {:.2f} MB (riba {} d.)":
        "Preview: would delete GREEN {} files / {:.2f} MB, YELLOW {} files / {:.2f} MB (limit {} d.)",
    "Perziura baigta": "Preview finished",
    "Butu trinta {} failu ({:.2f} MB) su {} d. amziaus riba.\nNIEKAS neistrinta - tai tik perziura.":
        "Would delete {} files ({:.2f} MB) with a {} d. age limit.\nNOTHING was deleted - this is only a preview.",
    "ZALIOS vietos: {} failu ({:.2f} MB) - tiek istrins mygtukas 'Valyti viska is zaliu vietu'.\nGELTONOS vietos: {} failu ({:.2f} MB) - valomos tik po viena, su patvirtinimu.\nAmziaus riba: {} d.\nNIEKAS neistrinta - tai tik perziura.":
        "GREEN locations: {} files ({:.2f} MB) - this is what 'Clean all GREEN locations' will delete.\nYELLOW locations: {} files ({:.2f} MB) - cleaned one by one, with confirmation.\nAge limit: {} d.\nNOTHING was deleted - this is only a preview.",
}

# Spalvu zymos: vidiniai raktai VISADA lietuviski (ZALIA/GELTONA/RAUDONA),
# EN rezime tik RODOMOS kitaip (kaip fam() dubliu programoj).
_SPALVA_EN = {"ZALIA": "GREEN", "GELTONA": "YELLOW", "RAUDONA": "RED"}


def t(raktas):
    """Vertimas: LT rezime grazina rakta, EN - vertima (arba rakta, jei nera)."""
    if LANG == "en":
        return _EN.get(raktas, raktas)
    return raktas


def spalva(zyma):
    """Spalvos zyma rodymui (vidiniai raktai visada lietuviski)."""
    if LANG == "en":
        return _SPALVA_EN.get(zyma, zyma)
    return zyma


def valymu_zodis(n):
    """Teisinga 'valymu' forma pagal skaiciu (Roberto pastaba 7: '1 runs').

    LT: 1 valymas, 2-9 valymai, 10-20/0 valymu (21 valymas, 111 valymu...).
    EN: 1 run, kiti runs.
    """
    if LANG == "en":
        return "run" if n == 1 else "runs"
    n100 = n % 100
    n10 = n % 10
    if n10 == 1 and n100 != 11:
        return "valymas"
    if 2 <= n10 <= 9 and not (12 <= n100 <= 19):
        return "valymai"
    return "valymu"
