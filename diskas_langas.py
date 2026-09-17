# -*- coding: utf-8 -*-
"""diskas_langas.py - skirtukas "Diskas": kur dingo vieta (v1.3).

Atskiras langas, atidaromas is pagrindinio lango mygtuku. Veikiantis
`gui_langas.py` NEKEICIAMAS, isskyrus viena mygtuka - naujas dalykas statomas
SALIA to, kas veikia, ne PER ji.

Ka sis langas daro, ko nedaro niekas kitas (patikrinta WinDirStat saltinyje
2026-09-13): jis ne tik PARODO nepaaiskinta vieta, bet ir PASAKO, ka ji reiskia
ir kaip pasitikrinti. WinDirStat turi `<Unknown>` pseudo-faila, taciau nei
viena kalba nepaaiskina, kas tai; ir jis is viso nezino apie disko/skaidinio
lygi, nes dirba su tomais.

⛔ Programa NIEKO NETAISO. Visos rodomos komandos tik RODO.
"""

import ctypes

from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import (QPainter, QColor, QFont, QPen, QAction, QGuiApplication,
                         QTextCursor)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QWidget, QTextEdit, QMenu, QSizePolicy,
)

import diskas
from kalba import t

# Spalvos TIK skaiciais - QColor vardu ir hex be # spastai (OKF colors guard).
#
# Paimtos IS ESAMOS TC paletes (APP_QSS gui_langas.py), o ne sugalvotos naujos,
# kad langas atrodytu kaip tos pacios programos dalis:
#   #3c4e99 - antrastes juosta        #3d7bd8 - "Perziura" mygtukas
#   #f0a53a - "Skanuoti" mygtukas     #dfe3ec - slankiklio griovelis
SPALVA_UZIMTA = QColor(61, 123, 216)        # #3d7bd8
# Sistemos failams - purpurine, o ne tamsiai melyna (Roberto pastaba 09-13:
# "melyna ir tamsiai melyna diagramoje iziureti tai..."). Pasirinkta ne bet
# kokia: TC lenteleje "RAUDONA" yra #ffaaff purpurine ir reiskia "TIK PERZIURA,
# neliesti" - tai tiksliai sistemos failu atvejis. Cia ta pati seima, tik
# sodresne, nes lenteles atspalvis skirtas SVIESIAM fonui su juodu tekstu.
SPALVA_SISTEMOS = QColor(163, 73, 164)      # purpurine, TC "neliesti" prasme
# Siuksles - zalia, nes TC sviesofore ZALIA reiskia "saugu valyti". Tai vienintele
# skiltis, kuria zmogus TIKRAI gali susigrazinti, ir spalva tai pasako be zodziu.
SPALVA_SIUKSLES = QColor(77, 158, 85)       # #4d9e55 - btn_clear_all spalva
SPALVA_LAISVA = QColor(223, 227, 236)       # #dfe3ec
SPALVA_NEPAAISKINTA = QColor(240, 165, 58)  # #f0a53a - TC "demesio" spalva
# Ta pati vieta be raides, kai jos maza ir nerimauti neverta: pilkai ruda,
# matoma, bet nesaukianti. Oranzine paliekam tik tikram nesutapimui.
SPALVA_SMULKME = QColor(150, 145, 135)
SPALVA_TEKSTO = QColor(26, 26, 26)          # kaip TEKSTO_SPALVA gui_langas.py

# Antrastes ir juostu stiliai - tokie patys kaip pagrindiniame lange
STILIUS_ANTRASTE = (
    "font-weight: bold; font-size: 16px; color: #ffffff;"
    "background-color: #3c4e99; padding: 8px; border-radius: 6px;"
)
STILIUS_ETIKETE = (
    "background-color: #3c4e99; color: white; padding: 3px 8px;"
    "border-radius: 3px; font-size: 12px;"
)
# Verdiktas - tokia pati desute kaip lbl_status, tik spalva pagal busena
STILIUS_VERDIKTAS_GERAI = (
    "padding: 5px 8px; color: #1a5e2e; font-size: 12px; font-weight: bold;"
    "background-color: #eafbee; border: 1px solid #b9e5c4; border-radius: 4px;"
)
STILIUS_VERDIKTAS_DEMESIO = (
    "padding: 5px 8px; color: #7a4a05; font-size: 12px; font-weight: bold;"
    "background-color: #fdf3e3; border: 1px solid #f0cf9a; border-radius: 4px;"
)

GB = 1024.0 ** 3


def fmt(baitai):
    if baitai is None:
        return "-"
    if baitai >= GB:
        return "%.1f GB" % (baitai / GB)
    return "%.0f MB" % (baitai / (1024.0 ** 2))


class Skritulys(QWidget):
    """Apvali diagrama, pieziama pacio QPainter - be QtCharts.

    2026-08-31 buvo nuspresta "jokiu pyragu", bet priezastis buvo QtCharts
    priklausomybe ir megabaitai. Pieziant patiems ta priezastis atkrinta,
    o Windows disko savybese pats rodo pyraga - zmogus vaizda atpazista.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dalys = []  # [(pavadinimas, baitai, QColor)]
        # 170, o ne 210: skritulys nera svarbiausia lango dalis - svarbiausia
        # yra paaiskinimas po juo, ir jam reikia vietos (rasta zirint nuotrauka).
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def nustatyk(self, dalys):
        self.dalys = [d for d in dalys if d[1] and d[1] > 0]
        self.update()

    def paintEvent(self, event):
        if not self.dalys:
            return
        viso = sum(d[1] for d in self.dalys)
        if viso <= 0:
            return

        dazai = QPainter(self)
        dazai.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        krastas = 12
        skersmuo = min(self.width() // 2, self.height() - 2 * krastas)
        sritis = QRectF(krastas, krastas, skersmuo, skersmuo)

        # Qt kampai matuojami 1/16 laipsnio; pradedam is virsaus (90 laipsniu)
        pradzia = 90 * 16
        for _, baitai, spalva in self.dalys:
            kampas = int(round(360 * 16 * baitai / viso))
            dazai.setBrush(spalva)
            dazai.setPen(QPen(QColor(255, 255, 255), 2))
            dazai.drawPie(sritis, pradzia, -kampas)
            pradzia -= kampas

        # Paaiskinimai desineje
        x = krastas + skersmuo + 24
        y = krastas + 8
        sriftas = QFont()
        sriftas.setPointSize(9)
        dazai.setFont(sriftas)
        for pavadinimas, baitai, spalva in self.dalys:
            dazai.setBrush(spalva)
            dazai.setPen(QPen(QColor(120, 120, 120), 1))
            dazai.drawRect(x, y, 13, 13)
            dazai.setPen(SPALVA_TEKSTO)
            proc = 100.0 * baitai / viso
            dazai.drawText(x + 20, y + 11, "%s - %s (%.1f%%)"
                           % (pavadinimas, fmt(baitai), proc))
            y += 24
        dazai.end()


class DiskoLangas(QDialog):
    """Kur dingo vieta - sasku suvedimas ir paaiskinimas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Diskas - kur dingo vieta"))
        self.resize(780, 650)
        self._duomenys = {}

        maketas = QVBoxLayout(self)

        # --- antraste: tokia pati juosta kaip pagrindiniame lange ---
        # Roberto pastaba 09-13: "pasirenki kita diska - nelabai supratau, kas
        # vyksta". Antraste dabar SAKO, kuris diskas rodomas, ir keiciasi ji
        # perjungus - perjungimas matomas be jokio papildomo teksto.
        self.antraste = QLabel(t("Diskas - kur dingo vieta"))
        self.antraste.setStyleSheet(STILIUS_ANTRASTE)
        maketas.addWidget(self.antraste)

        # --- pasirinkimas ---
        eile = QHBoxLayout()
        eile.addWidget(QLabel(t("Diskas:")))
        self.pasirinkimas = QComboBox()
        self.pasirinkimas.currentIndexChanged.connect(self._perpiesti)
        eile.addWidget(self.pasirinkimas)
        eile.addStretch(1)
        self.mygtukas_naujinti = QPushButton(t("Perskaityti is naujo"))
        self.mygtukas_naujinti.setToolTip(
            t("Is naujo perskaito disku duomenis - jei prijungete diska "
              "arba pasikeite laisva vieta."))
        self.mygtukas_naujinti.clicked.connect(self._perskaityti_is_naujo)
        eile.addWidget(self.mygtukas_naujinti)
        maketas.addLayout(eile)

        # --- skritulys ---
        self.skritulys = Skritulys()
        maketas.addWidget(self.skritulys)

        # --- verdiktas: tokia pati desute kaip lbl_status pagrindiniame lange ---
        self.verdiktas = QLabel("")
        self.verdiktas.setWordWrap(True)
        maketas.addWidget(self.verdiktas)

        # --- paaiskinimas: matomas PATS, ne pasleptas po desiniu mygtuku ---
        etikete = QLabel(t("Ka tai reiskia:"))
        etikete.setStyleSheet(STILIUS_ETIKETE)
        etikete.setSizePolicy(QSizePolicy.Policy.Maximum,
                              QSizePolicy.Policy.Fixed)
        maketas.addWidget(etikete)

        self.paaiskinimas = QTextEdit()
        self.paaiskinimas.setReadOnly(True)
        # Rysku pazymejima - kad zmogus MATYTU, kam desinys meniu bus taikomas.
        # Geltona is TC paletes (btn_scan #ffd35c), tekstas tamsus, kad skaitytusi.
        self.paaiskinimas.setStyleSheet(
            "QTextEdit { selection-background-color: #ffd35c; "
            "selection-color: #1a1a1a; }")
        self.paaiskinimas.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.paaiskinimas.customContextMenuRequested.connect(self._meniu)
        maketas.addWidget(self.paaiskinimas, 1)

        apacia = QHBoxLayout()
        apacia.addStretch(1)
        self.mygtukas_kopijuoti = QPushButton(t("Issaugoti ataskaita"))
        self.mygtukas_kopijuoti.setToolTip(
            t("Issaugo visu disku skaicius i .txt faila - gali nusiusti "
              "kompiuterininkui arba ikelti i DI padejeja."))
        self.mygtukas_kopijuoti.clicked.connect(self._issaugoti_ataskaita)
        apacia.addWidget(self.mygtukas_kopijuoti)
        uzdaryti = QPushButton(t("Uzdaryti"))
        uzdaryti.clicked.connect(self.accept)
        apacia.addWidget(uzdaryti)
        maketas.addLayout(apacia)

        self._surinkti()

    # ------------------------------------------------------------------

    def _perskaityti_is_naujo(self):
        """Perskaito ir PARODO, kad suveike.

        Roberto pastaba 2026-09-13: "panasu jis nieko nedaro" - jei skaiciai
        nepasikeite, ekrane niekas nekinta, ir mygtukas atrodo negyvas.
        """
        self._surinkti()
        self.mygtukas_naujinti.setText(t("Perskaityta"))
        QTimer.singleShot(2000, lambda: self.mygtukas_naujinti.setText(
            t("Perskaityti is naujo")))

    def _surinkti(self):
        self.pasirinkimas.blockSignals(True)
        self.pasirinkimas.clear()
        self._duomenys = {}
        for t_info in diskas.visi_tomai():
            raide = t_info["raide"]
            self._duomenys[raide] = t_info
            self.pasirinkimas.addItem("%s:" % raide, raide)
        self.pasirinkimas.blockSignals(False)
        self._perpiesti()

    def _dabartinis(self):
        raide = self.pasirinkimas.currentData()
        return self._duomenys.get(raide)

    def _siuksliu_suma(self, raide):
        """Kiek siuksliu rado PATS valytuvas - jei jis jau skenavo.

        Savo skenerio cia NERASOM: pagrindinis langas po skeno laiko rezultatus
        `_candidates`, ir uztenka juos susumuoti. Tai pirmas atvejis, kai dvi
        programos dalys viena kita pazysta (`DOVANU_ZEMELAPIS.md` mintis).

        Jei skeno dar nebuvo - grazina 0, ir skiltis tiesiog nerodoma.
        """
        tevas = self.parent()
        kandidatai = getattr(tevas, "_candidates", None) or []
        priesdelis = (raide + ":").lower()
        suma = 0
        for k in kandidatai:
            kelias = getattr(k, "path", "") or ""
            if kelias[:2].lower() == priesdelis:
                suma += getattr(k, "total_bytes", 0) or 0
        return suma

    def _ar_buvo_skenas(self):
        return bool(getattr(self.parent(), "_candidates", None))

    def _perpiesti(self):
        info = self._dabartinis()
        if not info:
            return
        fs = info.get("fs")
        if not fs:
            self.verdiktas.setText(t("Sio disko duomenu perskaityti nepavyko."))
            self.skritulys.nustatyk([])
            self.paaiskinimas.setPlainText("")
            return

        # Sistemos failai ir siuksles yra UZIMTOS vietos dalys, todel jas
        # ATSKIRIAM, o ne pridedam - kitaip suma virsytu disko dydi.
        sist = info.get("sistemos_failu_suma") or 0
        siuksles = self._siuksliu_suma(info["raide"])
        duomenys = max(fs["uzimta"] - sist - siuksles, 0)
        dalys = [(t("Duomenys"), duomenys, SPALVA_UZIMTA)]
        if sist > 0:
            dalys.append((t("Sistemos failai"), sist, SPALVA_SISTEMOS))
        if siuksles > 0:
            dalys.append((t("Siuksles"), siuksles, SPALVA_SIUKSLES))
        dalys.append((t("Laisva"), fs["laisva"], SPALVA_LAISVA))
        nesutapimai = info.get("nesutapimai", [])
        rimta = any(n["tipas"] == diskas.NS_UZ_SKAIDINIO for n in nesutapimai)
        uz_ribu = info.get("uz_skaidinio") or 0
        # Skilti rodom VISADA, kai ta vieta egzistuoja - skaicius yra tikras ir
        # slepti ji butu nesazininga. Bet SPALVA priklauso nuo to, ar verta
        # nerimauti: neutrali prie sveiko disko (kiekvienas Windows turi ~1 GB
        # EFI + atkurimo), oranzine tik tada, kai verdiktas irgi sako "nepaaiskinta".
        # Taip diagrama ir uzrasas niekada viens kitam nepriestarauja.
        if uz_ribu > 0:
            dalys.append((t("Particijos be raides"), uz_ribu,
                          SPALVA_NEPAAISKINTA if rimta else SPALVA_SMULKME))
        for n in nesutapimai:
            if n["tipas"] != diskas.NS_UZ_SKAIDINIO:
                dalys.append((t("Nepaaiskinta"), n["baitai"], SPALVA_NEPAAISKINTA))
        self.skritulys.nustatyk(dalys)

        # Antraste pasako, KURIS diskas rodomas (Roberto pastaba 09-13)
        self.antraste.setText("%s %s: - %s" % (
            t("Diskas"), info["raide"], t("kur dingo vieta")))

        # Verdiktas turi buti TEIGINYS, o ne nuotaika: Roberto pastaba 09-13
        # "'Viskas sueina' neinformatyvu - disko dydis atitinka numatyta talpa
        # ar kazkas tokio". Todel dabar visada rodom, SU KUO lyginama.
        talpa = info.get("disko_dydis") or (fs["viso"] if fs else 0)
        if nesutapimai:
            viso = sum(n["baitai"] for n in nesutapimai)
            self.verdiktas.setText("%s %s %s %s" % (
                t("Nepaaiskinta"), fmt(viso), t("is"), fmt(talpa)))
            self.verdiktas.setStyleSheet(STILIUS_VERDIKTAS_DEMESIO)
        else:
            self.verdiktas.setText("%s %s %s" % (
                t("Viskas sueina: visi"), fmt(talpa), t("paskirstyti")))
            self.verdiktas.setStyleSheet(STILIUS_VERDIKTAS_GERAI)

        self.paaiskinimas.setPlainText(self._tekstas(info))

    # ------------------------------------------------------------------

    def _tekstas(self, info):
        """Zmogiskas paaiskinimas. Faktai ir itariamieji - be diagnozes."""
        fs = info["fs"]
        eil = []
        eil.append(t("KA MATOME"))
        if info.get("disko_dydis"):
            eil.append("  %s PhysicalDrive%d: %s"
                       % (t("Fizinis diskas"), info["disko_nr"],
                          fmt(info["disko_dydis"])))
        if info.get("skaidinys"):
            eil.append("  %s: %s (%s %s)"
                       % (t("Particija"), fmt(info["skaidinys"]["ilgis"]),
                          t("pradzia"), fmt(info["skaidinys"]["pradzia"])))
        eil.append("  %s: %s %s / %s %s"
                   % (t("Failu sistema"), t("uzimta"), fmt(fs["uzimta"]),
                      t("laisva"), fmt(fs["laisva"])))
        siuksles = self._siuksliu_suma(info["raide"])
        if siuksles > 0:
            eil.append("")
            eil.append("%s %s" % (t("SIUKSLES:"), fmt(siuksles)))
            eil.append("  %s" % t("Tiek rado valytuvas. Si dalis - vienintele, "
                                  "kuria galite susigrazinti."))
        elif not self._ar_buvo_skenas():
            eil.append("")
            eil.append(t("Siuksliu dalis dar nesuskaiciuota - paleiskite "
                         "\"Skanuoti\" pagrindiniame lange."))

        sist = info.get("sistemos_failai") or {}
        if sist:
            eil.append("")
            eil.append(t("SISTEMOS FAILAI"))
            for vardas, dydis in sorted(sist.items(), key=lambda x: -x[1]):
                eil.append("  %-16s %s   %s"
                           % (vardas, fmt(dydis), t(_SISTEMOS_PAAISKINIMAI.get(vardas, ""))))
            eil.append("  %s" % t("Siu failu trinti negalima - Windows juos "
                                  "naudoja dirbdamas."))
        eil.append("")

        if info.get("nematome"):
            eil.append(t("KO NEPAMATEME"))
            for kas in info["nematome"]:
                eil.append("  - %s" % t(_NEMATOME_TEKSTAS.get(kas, kas)))
            eil.append("")

        if not info.get("nesutapimai"):
            if (info.get("uz_skaidinio") or 0) > 0:
                eil.append("%s %s" % (
                    t("Particiju be raides:"), fmt(info["uz_skaidinio"])))
                eil.append(t("Tiek turi beveik kiekvienas Windows kompiuteris: "
                             "EFI ir atkurimo particijos. Tai normalu."))
                eil.append("")
            eil.append(t("Skaiciai sueina - visa disko talpa paskirstyta."))
            eil.append("")
            eil.append(t("Priminimas: gamintojas raso 1 TB = 1000 mlrd. baitu, "
                         "o Windows skaiciuoja dvejetainiais, todel 1 TB diskas "
                         "rodomas kaip ~931 GB. Tai ne dingusi vieta."))
            return "\n".join(eil)

        for n in info["nesutapimai"]:
            eil.append("%s %s" % (t("NESUTAPIMAS:"), fmt(n["baitai"])))
            eil.append("  %s" % t(_KAS_TAI.get(n["tipas"], "")))
            eil.append("")
            eil.append("  %s" % t("KAS GALIMAI NUTIKE"))
            for raktas in n["itariamieji"]:
                pav, patikra = _ITARIAMIEJI.get(raktas, (raktas, ""))
                eil.append("   - %s" % t(pav))
                if patikra:
                    eil.append("       %s  %s" % (t("Pasitikrinti:"), patikra))
            eil.append("")
        eil.append(t("Sios komandos tik RODO - nieko nekeicia ir netrina."))
        return "\n".join(eil)

    # ------------------------------------------------------------------

    def _meniu(self, pos):
        meniu = QMenu(self)

        # Roberto pastaba 2026-09-13: "nelabai aisku, ka pazymejai ir kam tas
        # desinys bus pritaikytas". Todel desinys paspaudimas PATS pazymi zodi
        # po kursoriumi - kaip narsykleje ar Word'e: zmogus MATO, kam taikoma.
        # Jei jau buvo pazymeta fraze ir spaudziama ANT JOS - pazymejimo
        # negriaunam.
        vieta = self.paaiskinimas.cursorForPosition(pos)
        dabartinis = self.paaiskinimas.textCursor()
        ant_pazymejimo = (dabartinis.hasSelection()
                          and dabartinis.selectionStart() <= vieta.position()
                          <= dabartinis.selectionEnd())
        if not ant_pazymejimo:
            vieta.select(QTextCursor.SelectionType.WordUnderCursor)
            self.paaiskinimas.setTextCursor(vieta)

        # "Kas tai?" - toks pat kaip pagrindiniame lange (v1.1), tik cia ieskom
        # PAZYMETO teksto, pvz. "HPA/DCO" ar "pagefile.sys".
        pazymeta = (self.paaiskinimas.textCursor().selectedText() or "").strip()
        # Privatumas (ta pati zinynas.py garantija): i Google neleidziam nieko,
        # kas atrodo kaip kelias - ten gali buti vartotojo vardas.
        tinka = (pazymeta and len(pazymeta) <= 60
                 and "\\" not in pazymeta)
        # Meniu rodo TA PATI, ko bus ieskoma - t.y. istraukta termina, o ne visa
        # pazymeta fraze. Kitaip zmogus mato "Kas tai? (Failu lenteles (MFT)
        # rezervo dydzio)", o i paieska nueina "MFT" (Roberto skrinsotas 09-13).
        rodomas = self._isskirk_termina(pazymeta) if tinka else ""
        v_kas = QAction(t("Kas tai? ({})").format(rodomas) if tinka
                        else t("Kas tai?"), self)
        v_kas.setEnabled(bool(tinka))
        v_kas.triggered.connect(lambda: self._kas_tai(pazymeta))
        meniu.addAction(v_kas)
        meniu.addSeparator()

        v_kopijuoti = QAction(t("Kopijuoti pazymeta"), self)
        v_kopijuoti.triggered.connect(self.paaiskinimas.copy)
        meniu.addAction(v_kopijuoti)
        v_viskas = QAction(t("Kopijuoti viska"), self)
        v_viskas.triggered.connect(
            lambda: QGuiApplication.clipboard().setText(
                self.paaiskinimas.toPlainText()))
        meniu.addAction(v_viskas)
        meniu.addSeparator()
        v_ataskaita = QAction(t("Issaugoti ataskaita"), self)
        v_ataskaita.triggered.connect(self._issaugoti_ataskaita)
        meniu.addAction(v_ataskaita)
        meniu.exec(self.paaiskinimas.mapToGlobal(pos))

    @staticmethod
    def _isskirk_termina(tekstas):
        """Is pazymeto teksto istraukia TECHNINI termina, jei jis ten yra.

        Roberto gyvas testas 2026-09-13: pazymejus "Failu lenteles (MFT) rezervo
        dydzio" i Google nuejo visa lietuviska fraze - beprasmis klausimas.
        Naudingas yra tik terminas joje: MFT. Ieskom (1) failo su pletiniu
        (`pagefile.sys`), (2) santrumpos DIDZIOSIOMIS (MFT, EFI, HPA/DCO).
        Jei nerandam - grazinam teksta toki, koks yra.
        """
        import re
        failas = re.search(r"\b[A-Za-z0-9_]+\.(sys|dat|log|tmp)\b", tekstas)
        if failas:
            return failas.group(0)
        # (grazinam tik teksta; ar jis TECHNINIS, sako `_ar_technini_termina`)
        # ⚠️ Dydziu vienetai NERA santrumpos: be sio filtro "1.1 GB" virsdavo
        # terminu "GB", ir i paieska nueidavo klausimas apie gigabaita
        # (rasta testuojant 2026-09-13).
        NE_TERMINAI = {"GB", "MB", "KB", "TB", "PB"}
        for kandidatas in re.findall(r"\b[A-Z]{2,}(?:/[A-Z]{2,})?\b", tekstas):
            if kandidatas not in NE_TERMINAI:
                return kandidatas
        # Nei failo, nei santrumpos - lieka lietuviska fraze. Is jos ismetam
        # SKAICIUS ir dydziu vienetus: Roberto testas 09-13 parode uzklausa
        # `"Particiju be raides: 1.1 G" ka tai reiskia` - skaicius klausime
        # nereikalingas ir tik blogina rezultatus.
        svarus = re.sub(r"\([^)]*\)", " ", tekstas)          # (0.1%) ir pan.
        svarus = re.sub(r"[\d.,]+\s*(GB|MB|KB|TB|G|M|K|T)?\b", " ", svarus)
        svarus = re.sub(r"[:\-%()]+", " ", svarus)
        svarus = re.sub(r"\s+", " ", svarus).strip()
        return svarus or tekstas.strip()

    @staticmethod
    def _ar_technini_termina(terminas):
        """Ar tai ANGLISKAS techninis terminas (MFT, EFI, HPA/DCO, pagefile.sys)?

        Nuo to priklauso paieskos kalba: tokiu terminu lietuviskai internete
        beveik nera, o angliskai randa Microsoft dokumentacija.
        """
        import re
        if re.fullmatch(r"[A-Za-z0-9_]+\.(sys|dat|log|tmp)", terminas):
            return True
        return bool(re.fullmatch(r"[A-Z]{2,}(?:/[A-Z]{2,})?", terminas))

    def _kas_tai(self, pazymeta):
        """Pazymeta zodi paduoda i paieska.

        ⛔ NENAUDOJAM `zinynas.paieskos_url` - jis sukurtas KITAM klausimui:
        "kas per PROGRAMA yra sis katalogas", ir prikala fraze "kas tai per
        programa" prie bet ko. Roberto testas parode, kaip tai atrodo:
        uzklausa `"Failu lenteles (MFT) rezervo dydzio" kas tai per programa`,
        ir Google sazningai atsake, kad tai NE programa.
        ⇒ Cia klausiam apie TERMINA, ne apie programa, tad uzklausa sava.
        """
        if not pazymeta:
            return
        terminas = self._isskirk_termina(pazymeta)
        try:
            import urllib.parse
            import webbrowser

            import kalba
            # ⭐ Roberto pastaba 2026-09-13: jei terminas ANGLISKAS (MFT, EFI,
            # pagefile.sys), tai ir klausti reikia angliskai - lietuviskai ju
            # beveik nera (Google rode "nera rezultatu"), o angliskai randa
            # Microsoft dokumentacija. Atsakyma Google vis tiek pateikia
            # vartotojo kalba, tad zmogus nieko nepraranda.
            # Jei liko LIETUVISKA fraze - klausiam lietuviskai: angliskai ji
            # neduotu nieko.
            if self._ar_technini_termina(terminas):
                q = 'what is "%s" Windows disk space' % terminas
            elif kalba.LANG == "lt":
                q = '"%s" ka tai reiskia Windows diske' % terminas
            else:
                q = 'what is "%s" Windows disk space' % terminas
            webbrowser.open("https://www.google.com/search?q="
                            + urllib.parse.quote_plus(q))
        except Exception:
            pass  # naršyklės nebuvimas neturi griauti lango

    def _ataskaitos_tekstas(self):
        """VISU disku ataskaita - tokia, kad tiktu ir zmogui, ir AI padejejui.

        Roberto sprendimas 2026-09-13: atskiro "nukopijuoti klausima" nereikia -
        *"ta faila ir iklijuos, jei nores, i LLM-a"*. Vienas daiktas, du
        panaudojimai: nusiusti kompiuterininkui ARBA ikelti i AI. Todel klausimas
        iraSomas i pacio failo pabaiga.
        """
        import datetime
        try:
            from gui_langas import VERSIJA
        except Exception:
            VERSIJA = "?"
        eil = [t("DISKO ATASKAITA"),
               "%s %s" % (t("Sudaryta:"),
                          datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
               "%s %s v%s" % (t("Programa:"), t("Temp valytuvas"), VERSIJA),
               ""]
        for raide in [self.pasirinkimas.itemData(i)
                      for i in range(self.pasirinkimas.count())]:
            info = self._duomenys.get(raide)
            if not info:
                continue
            fs = info.get("fs") or {}
            eil.append("=== %s: ===" % raide)
            if info.get("disko_dydis"):
                eil.append("  %s: %s" % (t("Fizinis diskas"),
                                         fmt(info["disko_dydis"])))
            if info.get("skaidinys"):
                eil.append("  %s: %s" % (t("Particija"),
                                         fmt(info["skaidinys"]["ilgis"])))
            if fs:
                eil.append("  %s: %s %s / %s %s" % (
                    t("Failu sistema"), t("uzimta"), fmt(fs["uzimta"]),
                    t("laisva"), fmt(fs["laisva"])))
            sist = info.get("sistemos_failai") or {}
            if sist:
                eil.append("  %s:" % t("SISTEMOS FAILAI"))
                for vardas, dydis in sorted(sist.items(), key=lambda x: -x[1]):
                    eil.append("    %-16s %s" % (vardas, fmt(dydis)))
            siuksles = self._siuksliu_suma(raide)
            if siuksles:
                eil.append("  %s %s" % (t("SIUKSLES:"), fmt(siuksles)))
            if (info.get("uz_skaidinio") or 0) > 0:
                eil.append("  %s %s" % (t("Particiju be raides:"),
                                        fmt(info["uz_skaidinio"])))
            # VERDIKTAS - svarbiausia eilute. Be jos ataskaita yra tik skaiciai
            # be isvados, o isvada ir yra visos programos esme (praleista
            # rasant, pastebeta ziurint Roberto issaugota faila 2026-09-13).
            talpa = info.get("disko_dydis") or (fs.get("viso") or 0)
            nesutapimai = info.get("nesutapimai", [])
            if nesutapimai:
                viso = sum(n["baitai"] for n in nesutapimai)
                eil.append("  >>> %s %s %s %s" % (
                    t("Nepaaiskinta"), fmt(viso), t("is"), fmt(talpa)))
                for n in nesutapimai:
                    eil.append("      %s %s" % (t("NESUTAPIMAS:"), fmt(n["baitai"])))
                    eil.append("      %s" % t(_KAS_TAI.get(n["tipas"], "")))
            else:
                eil.append("  >>> %s %s %s" % (
                    t("Viskas sueina: visi"), fmt(talpa), t("paskirstyti")))
            if info.get("nematome"):
                eil.append("  %s" % t("KO NEPAMATEME"))
                for kas in info["nematome"]:
                    eil.append("    - %s" % t(_NEMATOME_TEKSTAS.get(kas, kas)))
            eil.append("")

        eil.append("-" * 60)
        eil.append(t("Klausimas: kur galejo dingti si vieta ir kaip tai "
                     "pasitikrinti nieko nesugadinant?"))
        eil.append(t("Sios ataskaitos programa nieko netaiso ir netrina - "
                     "ji tik parodo skaicius."))
        return "\n".join(eil)

    def _issaugoti_ataskaita(self):
        """Issaugo ataskaita i .txt - zmogus ja nusiuncia arba ikelia i AI."""
        import datetime
        import os

        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        numatytas = os.path.join(
            os.path.expanduser("~"), "Documents",
            "Disko-ataskaita-%s.txt" % datetime.date.today().isoformat())
        kelias, _ = QFileDialog.getSaveFileName(
            self, t("Issaugoti ataskaita"), numatytas, "Tekstas (*.txt)")
        if not kelias:
            return
        try:
            with open(kelias, "w", encoding="utf-8") as f:
                f.write(self._ataskaitos_tekstas())
        except OSError as e:
            QMessageBox.warning(self, t("Issaugoti ataskaita"),
                                t("Nepavyko issaugoti: {}").format(e))
            return
        self.mygtukas_kopijuoti.setText(t("Issaugota"))
        QTimer.singleShot(2000, lambda: self.mygtukas_kopijuoti.setText(
            t("Issaugoti ataskaita")))


# Tekstai laikomi atskirai, kad `_tekstas` liktu skaitomas.
_KAS_TAI = {
    diskas.NS_UZ_SKAIDINIO:
        "Diske yra vietos, kuri neturi disko raides - ji nepriklauso nei C:, "
        "nei D:. Todel jos nerodo nei Explorer, nei failu skaitytuvai: jie "
        "skaiciuoja tik tai, kas yra po kuria nors raide.\n"
        "  Tai NE ta atsarga, kuria diskas pasiima sau (rezerviniai sektoriai) - "
        "anos is viso nemato nei Windows, nei jokia programa.",
    diskas.NS_TOMAS_MAZESNIS:
        "Skaidinys didesnis nei tomas, kuri mato failu sistema.",
}

_ITARIAMIEJI = {
    "nepaskirstyta": ("Nepaskirstyta vieta (particija nedengia viso disko)",
                      "diskmgmt.msc"),
    "atkurimo_skaidinys": ("Gamintojo arba atkurimo particija",
                           "Get-Partition | Select DiskNumber,PartitionNumber,Size,Type"),
    "hpa_dco": ("HPA/DCO - gamintojo paslepta sritis (pasitaiko senuose diskuose)",
                ""),
    "mft_rezervas": ("NTFS rezervas failu lentelei (MFT)", "fsutil fsinfo ntfsinfo C:"),
    "failu_sistemos_apskaita": (
        "Failu sistemos apskaita gali buti nusimususi po staigaus isjungimo",
        "chkdsk C: /scan"),
}

_NEMATOME_TEKSTAS = {
    "failu_sistema": "Failu sistemos duomenu",
    "skaidinys": "Particijos dydzio",
    "vieta_diske": "Kurioje disko vietoje guli tomas",
    "fizinis_diskas": "Fizinio disko dydzio",
    "seselines_kopijos": "Seseliniu kopiju ir atkurimo tasku dydzio "
                         "(be administratoriaus teisiu jo gauti neimanoma)",
    "mft": "Failu lenteles (MFT) rezervo dydzio "
           "(be administratoriaus teisiu jo gauti neimanoma)",
}

_SISTEMOS_PAAISKINIMAI = {
    "pagefile.sys": "- mainu failas, Windows ji naudoja vietoj atminties",
    "hiberfil.sys": "- hibernacijos failas, dydis nuo atminties kiekio",
    "swapfile.sys": "- moderniu programu mainai",
}
