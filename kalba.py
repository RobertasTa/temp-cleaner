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
        # 2026-08-24: kalba gali dar guleti sename bendrame _darbal -
        # persikeliam PIRMA, kitaip pirmas paleidimas grizdavo i numatyta
        saugykla.migruoti_sena_darbal()
        v = (saugykla.data_dir() / saugykla.KALBOS_FAILAS).read_text(
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
    (d / saugykla.KALBOS_FAILAS).write_text(lang + "\n", encoding="utf-8")


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
    "ZALIA - saugu valyti automatiskai | GELTONA - tik su patvirtinimu | ZYDRA - sprendziate jus | RAUDONA - tik perziura":
        "GREEN - safe to clean | YELLOW - confirmation required | BLUE - you decide | RED - view only",
    "Sprendziate jus": "You decide",
    "I 'Valyti viska' nepatenka niekada. Norite - valykite si kataloga atskirai.":
        "Never included in 'Clean all'. You can still clean this folder on its own.",
    "Ar norite valyti ZYDRA vieta? Programa jos valyti NESIULO. {}":
        "Clean this location? The program does NOT suggest cleaning it. {}",
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
    # v1.1 "Kas tai?" desinio klaviso meniu
    "Kas tai? ({})": "What is this? ({})",
    "Kas tai?": "What is this?",
    "Kopijuoti kelia": "Copy path",
    "Atverti aplanka": "Open folder",
    "Kas tai '{}': atidaryta gamintojo svetaine":
        "What is '{}': opened the vendor's website",
    "Kas tai '{}': atidaryta Google paieska":
        "What is '{}': opened a Google search",
    "Kelias nukopijuotas": "Path copied",
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
    # pagalbos "?" kampelis (2026-08-07, Roberto ideja, seimos taisykle:
    # winget/Store vartotojas readme negauna - instrukcija pacioje programoje)
    "Pagalba": "Help",
    "Apie...": "About...",
    "Instrukcija": "User guide",
    # "Klausk DI" (Roberto ideja 2026-08-08; sertifikuotas receptas is
    # SDF/FOTO namu - promptas anglu k. kodo konstanta, ne zodyno irasas)
    "Neradote atsakymo? Klauskite DI": "No answer here? Ask the AI",
    "Kas ivyks paspaudus OK:\n\n"
    "1. Atsidarys interneto narsykle su DI padejejo\n"
    "   claude.ai puslapiu. Zinutes laukelyje jau bus\n"
    "   irasyta angliska pradzia - prisistatymas, kas per\n"
    "   programa ir kur jos kodas.\n"
    "2. NEISSIGASKITE raudono pranesimo virs zinutes -\n"
    "   claude.ai ji rodo visada, kai tekstas ateina per\n"
    "   nuoroda. Tai tik priminimas perskaityti, kas\n"
    "   siunciama.\n"
    "3. Zinutes gale, po zodziu \"My question:\", irasykite\n"
    "   SAVO klausima - galima lietuviskai! - ir spauskite\n"
    "   siuntimo mygtuka (rodykle). Klausti galima visko,\n"
    "   pvz.: \"kaip atsinaujinti programa i naujesne\n"
    "   versija? paaiskink zingsnis po zingsnio\".\n"
    "4. Jei DI atsakys angliskai - tiesiog paprasykite kita\n"
    "   zinute: \"atsakyk lietuviskai\", ir toliau bendraus\n"
    "   lietuviskai.\n\n"
    "Pastaba: claude.ai gali paprasyti prisijungti (nemokama\n"
    "paskyra). Niekas neissiunciama be jusu rankos.":
        "What happens after you press OK:\n\n"
        "1. Your web browser opens the claude.ai AI assistant.\n"
        "   The message box will already contain a prepared\n"
        "   opening - what the program is and where its code is.\n"
        "2. DO NOT be alarmed by the red notice above the\n"
        "   message - claude.ai always shows it when text\n"
        "   arrives via a link. It is just a reminder to read\n"
        "   what you are sending.\n"
        "3. At the end of the message, after \"My question:\",\n"
        "   TYPE YOUR question - any language works! - and\n"
        "   press the send button (the arrow). Ask anything,\n"
        "   e.g.: \"how do I update the app to the newest\n"
        "   version? explain it step by step\".\n"
        "4. If the AI answers in the wrong language - just ask\n"
        "   in the next message, e.g. \"answer in English\".\n\n"
        "Note: claude.ai may ask you to sign in (a free account).\n"
        "Nothing is sent without your hand.",
    "Nepavyko atidaryti: {}": "Could not open: {}",
    "Apie programa": "About",
    "Saugus sisteminiu laikinu failu valymas - viska matai ir supranti.":
        "Safe system temp cleanup - you see and understand everything.",
    "Versija {v}": "Version {v}",
    "Kurejo puslapis:": "Project page:",

    # --- v1.3 skirtukas "Diskas": kur dingo vieta ---
    "Diskas": "Disk",
    "Diskas:": "Disk:",
    "Diskas - kur dingo vieta": "Disk - where the space went",
    "Ka tai reiskia:": "What this means:",
    "Duomenys": "Your data",
    "Siuksles": "Junk",
    "SIUKSLES:": "JUNK:",
    "Tiek rado valytuvas. Si dalis - vienintele, kuria galite susigrazinti.":
        "That is what the cleaner found. This is the only part you can get back.",
    "Siuksliu dalis dar nesuskaiciuota - paleiskite "
    "\"Skanuoti\" pagrindiniame lange.":
        "The junk share has not been counted yet - run \"Scan\" in the main window.",
    "Particiju be raides:": "Partitions with no drive letter:",
    "Tiek turi beveik kiekvienas Windows kompiuteris: "
    "EFI ir atkurimo particijos. Tai normalu.":
        "Almost every Windows computer has that much: the EFI and recovery "
        "partitions. This is normal.",
    "Sistemos failai": "System files",
    "SISTEMOS FAILAI": "SYSTEM FILES",
    "Siu failu trinti negalima - Windows juos naudoja dirbdamas.":
        "These files cannot be deleted - Windows uses them while it runs.",
    "- mainu failas, Windows ji naudoja vietoj atminties":
        "- the page file, Windows uses it instead of memory",
    "- hibernacijos failas, dydis nuo atminties kiekio":
        "- the hibernation file, its size follows the amount of memory",
    "- moderniu programu mainai": "- swap for modern apps",
    "Seseliniu kopiju ir atkurimo tasku dydzio "
    "(be administratoriaus teisiu jo gauti neimanoma)":
        "the size of shadow copies and restore points "
        "(impossible to get without administrator rights)",
    "Failu lenteles (MFT) rezervo dydzio "
    "(be administratoriaus teisiu jo gauti neimanoma)":
        "the size of the file table (MFT) reserve "
        "(impossible to get without administrator rights)",
    "Tikrinti is naujo": "Check again",
    "Perskaityti is naujo": "Read again",
    "Perskaityta": "Read",
    "Issaugoti ataskaita": "Save report",
    "Issaugota": "Saved",
    "Issaugo visu disku skaicius i .txt faila - gali nusiusti "
    "kompiuterininkui arba ikelti i DI padejeja.":
        "Saves the numbers for every disk into a .txt file - you can send it to "
        "a technician or hand it to an AI assistant.",
    "DISKO ATASKAITA": "DISK REPORT",
    "Sudaryta:": "Created:",
    "Programa:": "Program:",
    "Sios ataskaitos programa nieko netaiso ir netrina - "
    "ji tik parodo skaicius.":
        "The program behind this report changes and deletes nothing - "
        "it only shows the numbers.",
    "Is naujo perskaito disku duomenis - jei prijungete diska "
    "arba pasikeite laisva vieta.":
        "Reads the disk data again - if you plugged in a drive or the free "
        "space changed.",
    "kur dingo vieta": "where the space went",
    "Viskas sueina: visi": "Everything adds up: all",
    "paskirstyti": "are accounted for",
    "is": "of",
    "Uzdaryti": "Close",
    "Uzimta": "Used",
    "Laisva": "Free",
    "Particijos be raides": "Partitions with no drive letter",
    "Nepaaiskinta": "Unaccounted",
    "Nepaaiskinta:": "Unaccounted:",
    "Viskas sueina.": "Everything adds up.",
    "Sio disko duomenu perskaityti nepavyko.": "Could not read this disk.",
    "KA MATOME": "WHAT WE SEE",
    "KO NEPAMATEME": "WHAT WE COULD NOT SEE",
    "KAS GALIMAI NUTIKE": "WHAT MAY HAVE HAPPENED",
    "NESUTAPIMAS:": "MISMATCH:",
    "Pasitikrinti:": "Check it with:",
    "Fizinis diskas": "Physical disk",
    "Particija": "Partition",
    "Failu sistema": "File system",
    "pradzia": "starts at",
    "uzimta": "used",
    "laisva": "free",
    "Skaiciai sueina - visa disko talpa paskirstyta.":
        "The numbers add up - the whole disk is accounted for.",
    "Priminimas: gamintojas raso 1 TB = 1000 mlrd. baitu, "
    "o Windows skaiciuoja dvejetainiais, todel 1 TB diskas "
    "rodomas kaip ~931 GB. Tai ne dingusi vieta.":
        "A reminder: the maker counts 1 TB as 1,000,000,000,000 bytes, while "
        "Windows counts in binary, so a 1 TB disk shows as about 931 GB. "
        "That space is not missing.",
    "Sios komandos tik RODO - nieko nekeicia ir netrina.":
        "These commands only SHOW things - they change and delete nothing.",
    "Kopijuoti pazymeta": "Copy selection",
    "Kopijuoti viska": "Copy everything",
    "Nukopijuoti klausima": "Copy the question",
    "Nukopijuota": "Copied",
    "Klausimas apie disko vieta Windows sistemoje.":
        "A question about disk space on Windows.",
    "fizinis disko dydis": "physical disk size",
    "particijos dydis": "partition size",
    "tomas pagal failu sistema": "volume as the file system sees it",
    "nepaaiskinta": "unaccounted",
    "Klausimas: kur galejo dingti si vieta ir kaip tai "
    "pasitikrinti nieko nesugadinant?":
        "Question: where could this space have gone, and how can I check that "
        "without breaking anything?",

    # Tekstai, kurie i t() ateina per zodynus (_KAS_TAI, _ITARIAMIEJI,
    # _NEMATOME_TEKSTAS diskas_langas.py) - statine patikra ju nepagauna,
    # todel laikomi cia kartu ir tikrinami akimis.
    "Diske yra vietos, kuri neturi disko raides - ji nepriklauso nei C:, "
    "nei D:. Todel jos nerodo nei Explorer, nei failu skaitytuvai: jie "
    "skaiciuoja tik tai, kas yra po kuria nors raide.\n"
    "  Tai NE ta atsarga, kuria diskas pasiima sau (rezerviniai sektoriai) - "
    "anos is viso nemato nei Windows, nei jokia programa.":
        "There is space on the disk that has no drive letter - it belongs "
        "neither to C: nor to D:. That is why neither Explorer nor any file "
        "scanner shows it: they count only what sits under some letter.\n"
        "  This is NOT the reserve the drive keeps for itself (spare sectors) - "
        "that one is invisible to Windows and to every program.",
    "Particija didesne nei tomas, kuri mato failu sistema.":
        "The partition is larger than the volume the file system sees.",
    "Nepaskirstyta vieta (particija nedengia viso disko)":
        "Unallocated space (the partition does not cover the whole disk)",
    "Gamintojo arba atkurimo particija": "A vendor or recovery partition",
    "HPA/DCO - gamintojo paslepta sritis (pasitaiko senuose diskuose)":
        "HPA/DCO - an area hidden by the manufacturer (happens on older disks)",
    "NTFS rezervas failu lentelei (MFT)":
        "NTFS reserve for the file table (MFT)",
    "Failu sistemos apskaita gali buti nusimususi po staigaus isjungimo":
        "The file system's own accounting can drift after an abrupt shutdown",
    "Failu sistemos duomenu": "file system data",
    "Particijos dydzio": "the partition size",
    "Kurioje disko vietoje guli tomas": "where on the disk the volume sits",
    "Fizinio disko dydzio": "the physical disk size",
}

# Spalvu zymos: vidiniai raktai VISADA lietuviski (ZALIA/GELTONA/RAUDONA),
# EN rezime tik RODOMOS kitaip (kaip fam() dubliu programoj).
_SPALVA_EN = {"ZALIA": "GREEN", "GELTONA": "YELLOW", "ZYDRA": "You decide",
              "RAUDONA": "RED"}

# Zydros eilutes uzrasas: ka PROGRAMA apie ta vieta zino. Roberto patvirtinta
# 2026-08-31: "Sprendziate jus" / "You decide".
_ZYDRA_LT = {"NAUDOJAMA_DABAR": "naudojama dabar",
             "SINCHRONIZACIJA": "sinchronizacija",
             "MOKAMA_PROGRAMA": "mokama programa",
             "SENOS_VERSIJOS": "senos versijos",
             "": "nezinoma"}
_ZYDRA_EN = {"NAUDOJAMA_DABAR": "in use now",
             "SINCHRONIZACIJA": "sync folder",
             "MOKAMA_PROGRAMA": "paid software",
             "SENOS_VERSIJOS": "old versions",
             "": "unknown"}


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


def zydra_del(raktas):
    """Kodel eilute zydra, zmogaus kalba."""
    if LANG == "en":
        return _ZYDRA_EN.get(raktas, _ZYDRA_EN[""])
    return _ZYDRA_LT.get(raktas, _ZYDRA_LT[""])


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
