"""zinynas.py - "Kas tai?" pagalba: programos vardas is kelio + URL.

v1.1 (Roberto ideja 2026-08-07): desinis peles klavisas ant lenteles
eilutes -> "Kas tai?" -> numatytoji naryskle atidaro gamintojo puslapi
(jei programa yra zinomos_programos.json zinyne) arba Google paieskos
sarasa su programos pavadinimu.

PRIVATUMAS: i paieskos uzklausa NIEKADA nededamas pilnas kelias nei
vartotojo vardas - imami tik segmentai UZ baziniu vietu (AppData /
Temp / ProgramData / Windows\\Temp) ribos; vartotojo vardas kelyje
visada yra PRIES AppData, todel i uzklausa nepatenka.

Zero Qt priklausomybiu - testuojama be GUI (kaip kalba.py).
"""
import json
import os
import re
import sys
import urllib.parse

# Antras segmentas praleidziamas, jei tai atsitiktinis/techninis vardas
# (GUID, hex, vien skaiciai, 7-Zip SFX likuciai, tmp/bk_ šablonai).
_JUNK_RE = re.compile(
    r"^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    r"|[0-9a-f]{8,}|\d+|7zS.*|bk_.*|\..*|.*\.tmp)$", re.IGNORECASE)


def _zinyno_kelias():
    """PyInstaller guard Rule 4: frozen rezime data failai gyvena _MEIPASS."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "zinomos_programos.json")


def _load_zinynas():
    """Skaito zinomos_programos.json; bet kokia klaida -> tuscias (atsarga:
    tada visos programos eina Google pakopa, programa nelusta)."""
    try:
        with open(_zinyno_kelias(), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        prog = data.get("programos", {})
        return prog if isinstance(prog, dict) else {}
    except (OSError, ValueError):
        return {}


def vardo_segmentai(path):
    """Programos/gamintojo segmentai (iki 2) is pilno kelio, BE vartotojo vardo.

    Semos: ...\\AppData\\{Local|LocalLow|Roaming}[\\Temp]\\<vendor>[\\<app>],
    C:\\Windows\\Temp\\<name>, ...\\ProgramData\\<vendor>. Nezinomai semai
    grazinamas tik paskutinis kelio segmentas (jokiu tarpiniu katalogu).
    """
    dalys = [d for d in re.split(r"[\\/]+", path) if d and not d.endswith(":")]
    if not dalys:
        return []
    low = [d.lower() for d in dalys]
    idx = None
    if "appdata" in low:
        j = low.index("appdata") + 1
        if j < len(low) and low[j] in ("local", "locallow", "roaming"):
            j += 1
        if j < len(low) and low[j] == "temp":
            j += 1
        idx = j
    elif "programdata" in low:
        idx = low.index("programdata") + 1
    elif "temp" in low:
        idx = low.index("temp") + 1
    if idx is not None and idx < len(dalys):
        seg = dalys[idx:idx + 2]
    else:
        seg = dalys[-1:]
    # antras segmentas tik jei prasmingas (ne GUID/hex/tmp slamstas)
    if len(seg) == 2 and _JUNK_RE.match(seg[1]):
        seg = seg[:1]
    return seg


def vardas_is_kelio(path):
    """Zmogui rodomas programos vardas is kelio (arba None, jei kelio nera)."""
    seg = vardo_segmentai(path)
    if not seg:
        return None
    # dublikatas "NVIDIA NVIDIA Corporation" stiliaus negresia - imam kaip yra
    return " ".join(seg)


def paieskos_url(vardas, lang):
    """Google paieskos SARASO url (2 pakopa - nezinomoms programoms)."""
    if lang == "lt":
        q = '"{}" kas tai per programa'.format(vardas)
    else:
        q = 'what is "{}" program'.format(vardas)
    return "https://www.google.com/search?q=" + urllib.parse.quote_plus(q)


def kas_tai(path, lang="lt"):
    """Pagrindinis iejimas: (vardas, url, is_zinynas).

    is_zinynas True  -> url yra gamintojo puslapis is zinyno (1 pakopa);
    is_zinynas False -> url yra Google paieskos sarasas (2 pakopa).
    Grazina (None, None, False), jei is kelio vardo istraukti nepavyko.
    """
    seg = vardo_segmentai(path)
    if not seg:
        return None, None, False
    prog = _load_zinynas()
    rec = None
    if len(seg) > 1:
        rec = prog.get("/".join(s.lower() for s in seg[:2]))
    if rec is None:
        rec = prog.get(seg[0].lower())
    if isinstance(rec, dict) and rec.get("url"):
        return rec.get("vardas") or " ".join(seg), rec["url"], True
    vardas = " ".join(seg)
    return vardas, paieskos_url(vardas, lang), False


def atidaryti_kas_tai(path, lang="lt"):
    """Atidaro url numatytoje naryskleje. Grazina (vardas, url, is_zinynas)."""
    import webbrowser
    vardas, url, is_zinynas = kas_tai(path, lang)
    if url:
        webbrowser.open(url)
    return vardas, url, is_zinynas
