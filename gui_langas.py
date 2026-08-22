"""gui_langas.py - MainWindow UI: table, log, colouring, scan + clean logic."""

import os
import sys
from pathlib import Path

# gui_langas.py does NOT set VALYTUVAS_TESTBED.
# Per UZDUOTIS.md 6 sk., the env var is read at scan time (runtime), not set here.

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QLabel,
    QFrame, QSlider, QMessageBox, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QEvent
from PyQt6.QtGui import QColor, QFont, QIcon

from handlers import (handler_on_scan, handler_on_clean_green,
                      handler_on_clean_row, handler_on_preview)
from models import COLOR_HEX, AGE_DAYS
from kalba import t, spalva

# Rodoma Apie... langelyje; galutini numeri nustatyti leidziant release
VERSIJA = "1.1"


def _resource_path(name):
    """PyInstaller guard Rule 4: supakuotame .exe data failai gyvena
    sys._MEIPASS laikinam kataloge, o ne salia .py failu."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)


# ------------------------------------------------------------------
# Formatting helpers
# ------------------------------------------------------------------

def fmt_size(n_bytes):
    if n_bytes < 1024:
        return "{} B".format(n_bytes)
    kib = n_bytes / 1024
    if kib < 1024:
        return "{:.0f} KB".format(kib)
    mib = kib / 1024
    if mib < 1024:
        return "{:.2f} MB".format(mib)
    gib = mib / 1024
    return "{:.2f} GB".format(gib)


# ------------------------------------------------------------------
# APP_QSS - suvienodinta su Smart Duplicate Finder (dubliu programa):
# apvalinti 10px mygtukai su 3D gradientu ir hover; btn_scan gintarinis,
# btn_preview melynas, btn_clear_all zalias, btn_close raudonas.
# ------------------------------------------------------------------

APP_QSS = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffffff, stop:1 #e4e6ee);
    border: 1px solid #b6bac8;
    border-radius: 10px;
    padding: 9px 14px;
    font-weight: 600;
    color: #2c2f38;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f3f7ff, stop:1 #d6e2f8);
    border: 1px solid #5b8def;
    color: #123a7a;
}
QPushButton:pressed {
    background: #c9d7f0;
    border: 1px solid #3c6fd8;
    padding-top: 11px; padding-bottom: 7px;
}
QPushButton:disabled {
    background: #ededf1; border: 1px solid #d3d3da; color: #a0a0ab;
}
QPushButton#btn_scan {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffd35c, stop:1 #f0a53a);
    border: 1px solid #d18a1f;
    color: #4a2c00;
}
QPushButton#btn_scan:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffe08a, stop:1 #f7b551);
    border: 1px solid #b97613;
}
QPushButton#btn_scan:pressed {
    background: #e29a2e; border: 1px solid #a56508;
    padding-top: 11px; padding-bottom: 7px;
}
QPushButton#btn_scan:disabled {
    background: #ededf1; border: 1px solid #d3d3da; color: #a0a0ab;
}
QPushButton#btn_preview {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #7fb3f2, stop:1 #3d7bd8);
    border: 1px solid #2b62b5;
    color: #ffffff;
}
QPushButton#btn_preview:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #9cc6f8, stop:1 #5590e6);
    border: 1px solid #1f4f9c;
}
QPushButton#btn_preview:pressed {
    background: #3568b8; border: 1px solid #1a4485;
    padding-top: 11px; padding-bottom: 7px;
}
QPushButton#btn_clear_all {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #8fd694, stop:1 #4d9e55);
    border: 1px solid #3a7e41;
    color: #ffffff;
}
QPushButton#btn_clear_all:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #a8e2ac, stop:1 #62b26a);
    border: 1px solid #2d6633;
}
QPushButton#btn_clear_all:pressed {
    background: #47924f; border: 1px solid #245229;
    padding-top: 11px; padding-bottom: 7px;
}
QPushButton#btn_close {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ef8a8a, stop:1 #cf3e3e);
    border: 1px solid #a82f2f;
    color: #ffffff;
}
QPushButton#btn_close:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f4a5a5, stop:1 #d95252);
    border: 1px solid #8c2626;
}
QPushButton#btn_close:pressed {
    background: #b83030; border: 1px solid #7a2020;
    padding-top: 11px; padding-bottom: 7px;
}
QPushButton#btn_clear_row {
    border-radius: 6px; padding: 4px 8px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #7fb3f2, stop:1 #3d7bd8);
    border: 1px solid #2b62b5;
    color: #ffffff;
}
QPushButton#btn_clear_row:disabled {
    background: #ededf1; border: 1px solid #d3d3da; color: #a0a0ab;
}
QPushButton#btn_help {
    border-radius: 13px;
    padding: 0px;
    font-weight: 700;
}
QPushButton#btn_help::menu-indicator { image: none; width: 0px; }
QSlider::groove:horizontal {
    height: 6px; background: #dfe3ec; border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px; margin: -6px 0; border-radius: 8px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffd35c, stop:1 #f0a53a);
    border: 1px solid #d18a1f;
}
"""


# ------------------------------------------------------------------
# MainWindow
# ------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("Temp valytuvas"))
        _icon = _resource_path("valytuvas.ico")
        if os.path.exists(_icon):
            self.setWindowIcon(QIcon(_icon))
        self.resize(1050, 620)

        container = QWidget()
        self.setCentralWidget(container)
        vlayout = QVBoxLayout(container)

        # Header bar
        hheader = QHBoxLayout()
        title = QLabel(t("Temp valytuvas - Sisteminiai laikini failai"))
        title.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #ffffff;"
            "background-color: #3c4e99; padding: 8px; border-radius: 6px;"
        )

        # P5 fix: status initial text uses "Is viso" instead of "Iviskio dydis"
        self.lbl_status = QLabel(t("Rodymas: Visos vietos | Is viso: 0 MB"))
        self.lbl_status.setObjectName("StatusLabel")
        # Roberto pastaba 2026-08-05: cia gyvena svarbiausia gyva informacija
        # (skeno eiga, perziuros skaiciai) - turi buti RYSKI, ne pilka.
        self.lbl_status.setStyleSheet(
            "padding: 5px 8px; color: #1a3e6e; font-size: 12px; font-weight: bold;"
            "background-color: #eaf1fb; border: 1px solid #b9cdec; border-radius: 4px;"
        )

        # P1 fix: Color legend - added to layout between title and status
        self.lbl_legend = QLabel(
            t("ZALIA - saugu valyti automatiskai | GELTONA - tik su patvirtinimu | RAUDONA - tik perziura"))
        self.lbl_legend.setObjectName("LegendLabel")
        self.lbl_legend.setStyleSheet(
            "padding: 4px 8px; color: #666; font-size: 11px;"
            "background-color: #f8f8f8; border: 1px solid #ddd; border-radius: 4px;"
        )

        # Add all three widgets to header: title | legend | status | "?"
        hheader.addWidget(title, stretch=6)
        hheader.addWidget(self.lbl_legend, stretch=5)
        hheader.addWidget(self.lbl_status, stretch=3)
        hheader.addWidget(self._build_help_button(), stretch=0)

        # Table - 5 columns per UZDUOTIS.md contract
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            t("Katalogas"), t("Failai"), t("Dydis (MB)"), t("Tipas"), "Clear"
        ])
        self._set_col_widths()

        # Double-click -> open folder in Explorer
        self.table.itemDoubleClicked.connect(self._on_double_click)
        # Clear stulpelio paspaudimai (tekstinis Clear vietoj mygtuku)
        self.table.cellClicked.connect(self._on_cell_clicked)
        # Rankutes zymeklis ant Clear - kad jaustusi kaip mygtukas (Roberto UX)
        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self._on_cell_hover)
        self.table.viewport().installEventFilter(self)
        self._hover_clear_row = None
        self._clear_base_pts = self.font().pointSize() + 1
        # v1.1 "Kas tai?" (Roberto ideja 2026-08-07): desinis klavisas ant
        # eilutes -> gamintojo puslapis / Google paieska + kelio irankiai.
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)

        # Log box
        hlog = QHBoxLayout()
        log_lbl = QLabel(t("Valymo zurnalas:"))
        log_lbl.setStyleSheet(
            "background-color: #3c4e99; color: white; padding: 3px 8px;"
            "border-radius: 3px; font-size: 12px;"
        )
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        hlog.addWidget(log_lbl, stretch=0)
        hlog.addWidget(self.log_box, stretch=1)

        # APP_QSS per QApplication - galioja ir dialogams (kaip dubliu programoj)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(APP_QSS)

        # Valdymo juosta: amziaus slankiklis + viso-atlaisvinta skaitliukas
        hctrl = QHBoxLayout()
        lbl_age_cap = QLabel(t("Amziaus riba:"))
        lbl_age_cap.setStyleSheet("font-size: 12px; color: #444;")
        self.age_slider = QSlider(Qt.Orientation.Horizontal)
        self.age_slider.setObjectName("age_slider")
        self.age_slider.setRange(1, 30)
        self.age_slider.setValue(AGE_DAYS)
        self.age_slider.setFixedWidth(220)
        self.lbl_age_val = QLabel()
        self.lbl_age_val.setObjectName("lbl_age_val")
        self.lbl_age_val.setStyleSheet("font-size: 12px; font-weight: bold; color: #4a2c00;")
        self.age_slider.valueChanged.connect(self._on_age_changed)
        self._on_age_changed(self.age_slider.value())

        self.lbl_freed = QLabel()
        self.lbl_freed.setObjectName("lbl_freed")
        self.lbl_freed.setStyleSheet(
            "font-size: 12px; color: #2d6633; font-weight: bold;"
            "background-color: #eef7ee; border: 1px solid #cde4cd;"
            "border-radius: 4px; padding: 4px 8px;")
        self._update_freed_label()

        # Portable varnele (Roberto pastaba 3 + jo checkbox ideja, 2026-08-06):
        # matomas jungiklis GUI, atmintis - TempCleaner_portable.txt zymeklis SALIA exe
        # (Notepad++ doLocalConf.xml konvencija: keliauja su flesiuku).
        import saugykla
        self.chk_portable = QCheckBox(t("Portable rezimas (viskas salia programos)"))
        self.chk_portable.setObjectName("chk_portable")
        self.chk_portable.setChecked(saugykla.is_portable())
        # PASTABA (Roberto 2026-08-06): jokio setStyleSheet ant QCheckBox -
        # widget'o stilius ismusa natyvu Windows piesima ir varnele
        # tampa juoda melyname fone (dubliu programoj stiliaus nera - balta).
        self.chk_portable.setToolTip(t(
            "Ijungta: zurnalas ir darbiniai failai saugomi salia programos "
            "(pvz., flesiuke) - kompiuteryje pedsaku nelieka.\n"
            "Isjungta (numatyta): saugoma vartotojo kataloge "
            "%LOCALAPPDATA%\\TempCleaner."))
        self.chk_portable.toggled.connect(self._on_portable_toggled)

        # Kalbos pasirinkimas (2026-08-06, Roberto pastaba "du exe del
        # kalbos - negrazu"): vienas exe, pasirinkimas isimenamas
        # kalba.txt (portable rezime keliauja su flesiuku), isigalioja
        # perleidus programa.
        from PyQt6.QtWidgets import QComboBox
        from kalba import LANG as _dabartine_kalba
        self.cmb_kalba = QComboBox()
        self.cmb_kalba.setObjectName("cmb_kalba")
        self.cmb_kalba.addItem("Lietuvi\u0173", "lt")   # rodo "Lietuviu" su u-nosine; ASCII kode
        self.cmb_kalba.addItem("English", "en")
        self.cmb_kalba.setCurrentIndex(1 if _dabartine_kalba == "en" else 0)
        self.cmb_kalba.setToolTip(t(
            "Kalba pritaikoma paleidus programa is naujo."))
        self.cmb_kalba.currentIndexChanged.connect(self._on_kalba_changed)

        hctrl.addWidget(lbl_age_cap)
        hctrl.addWidget(self.age_slider)
        hctrl.addWidget(self.lbl_age_val)
        hctrl.addSpacing(24)
        hctrl.addWidget(self.chk_portable)
        hctrl.addSpacing(16)
        hctrl.addWidget(self.cmb_kalba)
        hctrl.addStretch(1)
        hctrl.addWidget(self.lbl_freed)

        # Buttons (with objectName for contract validation)
        btn_row = QHBoxLayout()

        self.btn_scan = QPushButton(t("Skanuoti"))
        self.btn_scan.setObjectName("btn_scan")

        self.btn_preview = QPushButton(t("Perziura (kas butu trinta)"))
        self.btn_preview.setObjectName("btn_preview")
        self.btn_preview.setEnabled(False)   # iki pirmo skeno nera ka perziureti

        self.btn_clear_all = QPushButton(t("Valyti viska is zaliu vietu"))
        self.btn_clear_all.setObjectName("btn_clear_all")

        # P5 fix: "UzdarA" -> "Uzdaryti" (ASCII only in code per AGENTS.md)
        self.btn_close = QPushButton(t("Uzdaryti"))
        self.btn_close.setObjectName("btn_close")
        self.close_button = self.btn_close

        btn_row.addWidget(self.btn_scan)
        btn_row.addWidget(self.btn_preview)
        btn_row.addWidget(self.btn_clear_all, stretch=1)
        btn_row.addWidget(self.btn_close)

        # Assemble vertical layout
        vlayout.addLayout(hheader)
        vlayout.addLayout(hctrl)
        vlayout.addWidget(self.table, stretch=3)
        vlayout.addLayout(hlog)
        vlayout.addLayout(btn_row)

        self._candidates = []
        self._row_color_data = {}
        self._working_thread = None
        self._worker = None

        # "Vyksta skenavimas" overlay - modeless (NE dialogas, NE exec():
        # kontraktas draudzia modalinius; tai tik virsutinis QFrame vaikas).
        self._scan_overlay = QFrame(self)
        self._scan_overlay.setObjectName("scan_overlay")
        self._scan_overlay.setStyleSheet(
            "QFrame#scan_overlay { background-color: #ffffff;"
            " border: 3px solid #b0b0b0; border-radius: 14px; }"
        )
        ov_lay = QHBoxLayout(self._scan_overlay)
        ov_lay.setContentsMargins(28, 18, 28, 18)
        ov_lay.setSpacing(12)
        ov_text = QLabel(t("Vyksta skenavimas"))
        ov_text.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #222; border: none;")
        self._overlay_text = ov_text   # laikrodukui MM:SS (kaip dubliu programoj)
        self._overlay_spin = QLabel("|")
        self._overlay_spin.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #3c4e99; border: none;")
        ov_lay.addWidget(ov_text)
        ov_lay.addWidget(self._overlay_spin)
        self._scan_overlay.hide()
        self._spin_frames = "|/-\\"
        self._spin_idx = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.setInterval(120)
        self._spin_timer.timeout.connect(self._spin_tick)
        self._worker = None  # OKF guard: instance-level worker reference (GC safety)

        self.btn_scan.clicked.connect(self._on_scan)
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_clear_all.clicked.connect(self._on_clean_green)
        self.btn_close.clicked.connect(self.close)

    # -- Amziaus slankiklis ir viso-atlaisvinta skaitliukas --
    def _on_age_changed(self, value):
        self.lbl_age_val.setText(t("{} d.").format(value))
        # GYVA perziura stumdant slankikli - is skeno kibireliu, be disko.
        # getattr: pirmasis kvietimas __init__ metu, kol _candidates dar nera.
        if getattr(self, "_candidates", None):
            from cleaner import preview_from_buckets
            instant = preview_from_buckets(self._candidates, value)
            if instant is not None:
                # Pastaba 6: ZALIOS/GELTONOS sumos atskirai (mygtukas valo tik zalias)
                per_l, _cnt, _nbytes = instant
                g_cnt = g_b = y_cnt = y_b = 0
                for _p, color, cnt, nbytes in per_l:
                    if color == "ZALIA":
                        g_cnt += cnt
                        g_b += nbytes
                    else:
                        y_cnt += cnt
                        y_b += nbytes
                self.lbl_status.setText(
                    t("Perziura: butu trinta ZALIOSE {} failu / {:.2f} MB, GELTONOSE {} failu / {:.2f} MB (riba {} d.)").format(
                        g_cnt, g_b / 1048576.0, y_cnt, y_b / 1048576.0, value))

    def age_days(self):
        """Slankiklio reiksme - amziaus saugiklis siai sesijai."""
        return self.age_slider.value()

    # ---- "?" pagalbos kampelis (2026-08-07, Roberto ideja, seimos
    # taisykle is dubliu programos: winget/Store vartotojas readme
    # negauna, tad instrukcija gyvena pacioje programoje) ----
    def _build_help_button(self):
        from PyQt6.QtWidgets import QMenu
        b = QPushButton("?")
        b.setObjectName("btn_help")
        b.setFixedSize(26, 26)
        b.setToolTip(t("Pagalba"))
        meniu = QMenu(b)
        meniu.addAction(t("Apie..."), self._on_apie)
        meniu.addAction(t("Instrukcija"), self._on_instrukcija)
        meniu.addAction(t("Neradote atsakymo? Klauskite DI"),
                        self._on_klausk_di)
        b.setMenu(meniu)
        return b

    def _on_klausk_di(self):
        """Atidaro claude.ai su paruostu promptu (Roberto ideja
        2026-08-08, sertifikuotas receptas is SDF/FOTO namu):
        pries narsykle - paaiskinimo langas su logotipu ('mociuciu
        instrukcija'). claude.ai/new?q= tik UZPILDO lauka - siuncia
        pats vartotojas; promptas anglu k. su TIKSLIA repo nuoroda
        (nuoroda atgis publikavus repo, kaip ir Apie lange).
        Tinklas TIK vartotojui paspaudus OK."""
        import urllib.parse
        import webbrowser
        dlg = QMessageBox(self)
        dlg.setWindowTitle(t("Neradote atsakymo? Klauskite DI"))
        ico = _resource_path("valytuvas.ico")
        if os.path.exists(ico):
            dlg.setIconPixmap(QIcon(ico).pixmap(64, 64))
        dlg.setText(t(
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
            "paskyra). Niekas neissiunciama be jusu rankos."))
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok
                               | QMessageBox.StandardButton.Cancel)
        if dlg.exec() != QMessageBox.StandardButton.Ok:
            return
        # 2026-08-22 SDF gyvo testo pamoka: be tiesioginio paminejimo
        # debesinis skaito TIK README ir brief'o neatranda.
        promptas = (
            'Hi! I am using the app "Temp Cleaner" - a safe Windows'
            " temp-file cleaner that explains what it found. Its source"
            " code is public:"
            " https://github.com/RobertasTa/temp-cleaner."
            " Please FIRST read the file AI_CONSULTANT_BRIEF.md in that"
            " repository - it is your briefing from the author - then the"
            " program's code and README, and answer my question in plain,"
            " human language - no programmer jargon."
            " My question: ")
        webbrowser.open("https://claude.ai/new?q="
                        + urllib.parse.quote(promptas))

    def _on_apie(self):
        """Apie... langelis (Roberto dizainas 2026-08-07): logo,
        pavadinimas, aprasas, versija, GitHub nuoroda apacioje.
        Nuoroda atgis publikavus repo; tinklas TIK paspaudus nuoroda."""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle(t("Apie programa"))
        lay = QVBoxLayout(dlg)
        virsus = QHBoxLayout()
        logo = QLabel()
        ico = _resource_path("valytuvas.ico")
        if os.path.exists(ico):
            logo.setPixmap(QIcon(ico).pixmap(64, 64))
        virsus.addWidget(logo, alignment=Qt.AlignmentFlag.AlignTop)
        info = QVBoxLayout()
        pavadinimas = QLabel("Temp Cleaner")
        pavadinimas.setStyleSheet("font-size: 14pt; font-weight: bold;")
        info.addWidget(pavadinimas)
        info.addWidget(QLabel(t(
            "Saugus sisteminiu laikinu failu valymas - viska matai ir supranti.")))
        info.addWidget(QLabel(t("Versija {v}").format(v=VERSIJA)))
        autoriai = QLabel("Robertas & Claude")
        autoriai.setStyleSheet("color: #5a5e6b;")
        info.addWidget(autoriai)
        virsus.addLayout(info)
        lay.addLayout(virsus)
        # Ryski melyna + bold, kad matytusi jog spaudziama (SDF pamoka)
        nuoroda = QLabel(
            t("Kurejo puslapis:") + ' <a href="https://github.com/'
            'RobertasTa/temp-cleaner" style="color:#2f7ce0;'
            'font-weight:bold;">GitHub</a>')
        nuoroda.setOpenExternalLinks(True)
        lay.addWidget(nuoroda)
        mygtukai = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        mygtukai.rejected.connect(dlg.reject)
        lay.addWidget(mygtukai)
        dlg.exec()

    def _on_instrukcija(self):
        """Instrukcija: exe viduje ikeptas README (LT/EN pagal GUI kalba)
        rodomas pacios programos lange su slinktimi (SDF pamoka
        2026-08-07: Notepad atsidarydavo tuscias - jokiu isoriniu
        programu ir jokiu failu kopiju diske)."""
        from PyQt6.QtWidgets import QDialog, QPlainTextEdit, QDialogButtonBox
        from kalba import LANG
        vardas = "README.txt" if LANG == "lt" else "README-en.txt"
        try:
            tekstas = Path(_resource_path(vardas)).read_text(
                encoding="utf-8", errors="replace")
        except OSError as e:
            QMessageBox.warning(
                self, t("Pagalba"), t("Nepavyko atidaryti: {}").format(e))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(t("Instrukcija"))
        lay = QVBoxLayout(dlg)
        rodinys = QPlainTextEdit(tekstas)
        rodinys.setReadOnly(True)
        # Monospace - kad README ASCII antrastes lygiuotusi
        rodinys.setFont(QFont("Consolas", 10))
        lay.addWidget(rodinys)
        mygtukai = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        mygtukai.rejected.connect(dlg.reject)
        lay.addWidget(mygtukai)
        dlg.resize(780, 560)
        dlg.exec()

    def _perleisti_programa(self):
        """Paleidzia nauja programos kopija ir uzdaro sia (kalbos keitimui).

        PyInstaller onefile SPASTAS (Roberto gyvas testas 2026-08-06):
        vaikas paveldi _PYI*/_MEIPASS2 aplinkos kintamuosius ir naudoja
        TEVO issipakavimo _MEI kataloga; tevas uzsidarydamas ji trina ->
        'Failed to remove temporary directory' + kitas restartas luzta
        'Failed to start embedded python interpreter'. Todel env
        isvalomas - vaikas issipakuoja SAVO kopija.
        """
        import subprocess
        env = {k: v for k, v in os.environ.items()
               if k != "_MEIPASS2" and not k.startswith("_PYI")}
        if getattr(sys, "frozen", False):
            subprocess.Popen(
                [sys.executable], env=env,
                cwd=str(Path(sys.executable).resolve().parent))
        else:
            subprocess.Popen([sys.executable] + sys.argv, env=env)
        QApplication.instance().quit()

    def _on_kalba_changed(self, _idx):
        """Kalbos pasirinkimas: irasomas i kalba.txt + pasiulomas perleidimas.

        Roberto pastaba 2026-08-06: "gal geriau pati restartuotu, painiavos
        maziau" - Taip perleidzia is karto, Ne pritaiko kita karta.
        """
        from kalba import issaugoti_kalba
        try:
            issaugoti_kalba(self.cmb_kalba.currentData())
        except OSError as e:
            QMessageBox.warning(
                self, t("Kalba"), t("Nepavyko issaugoti: {}").format(e))
            return
        reply = QMessageBox.question(
            self, t("Kalba"),
            t("Kalba issaugota. Perleisti programa dabar?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._perleisti_programa()

    def _on_portable_toggled(self, on):
        """Portable varnele: perjungia saugykla + perkelia zurnala.

        Nepavykus (pvz., read-only flesiukas) - varnele grazinama atgal
        (blockSignals, kad atstatymas nesuktu antro perjungimo).
        """
        import saugykla
        ok, err = saugykla.set_portable(on)
        if not ok:
            QMessageBox.warning(
                self, t("Portable rezimas"),
                t("Nepavyko perjungti rezimo: {}").format(err))
            self.chk_portable.blockSignals(True)
            self.chk_portable.setChecked(not on)
            self.chk_portable.blockSignals(False)
            return
        self._update_freed_label()   # skaitliukas skaitomas is naujos vietos
        self.lbl_status.setText(
            t("Portable rezimas IJUNGTAS - duomenys salia programos") if on
            else t("Portable rezimas isjungtas - duomenys vartotojo kataloge"))

    def _update_freed_label(self):
        from cleaner import read_total_freed
        from kalba import valymu_zodis
        runs, mb = read_total_freed()
        # Pastaba 7: '1 runs' gramatika - zodis parenkamas pagal skaiciu
        zodis = valymu_zodis(runs)
        if runs == 0:
            self.lbl_freed.setText(t("Viso atlaisvinta: 0 MB"))
        elif mb >= 1024:
            self.lbl_freed.setText(
                t("Viso atlaisvinta: {:.2f} GB ({} {})").format(mb / 1024.0, runs, zodis))
        elif mb >= 1:
            self.lbl_freed.setText(
                t("Viso atlaisvinta: {:.0f} MB ({} {})").format(mb, runs, zodis))
        else:
            self.lbl_freed.setText(
                t("Viso atlaisvinta: {:.1f} KB ({} {})").format(mb * 1024.0, runs, zodis))

    # -- Worker signal handlers (bound methods - OKF threading guard 1c) --
    # Bound method => Qt auto-queued connection => runs in main thread, not worker.
    @pyqtSlot(int, str)
    def _on_worker_progress(self, index, message):
        """Slot for ScanWorker.progress - dispatched to main thread by Qt."""
        self._log(message)
        # Gyva skeno eiga statusbare (Roberto pastaba - kaip dubliu kampe)
        self.lbl_status.setText(t("Skenuojama: rasta {} vietu...").format(index + 1))

    # -- "Vyksta skenavimas" overlay valdymas --
    def _spin_tick(self):
        self._spin_idx = (self._spin_idx + 1) % len(self._spin_frames)
        self._overlay_spin.setText(self._spin_frames[self._spin_idx])
        # Laikrodukas MM:SS (kaip dubliu programos faziu laikrodis)
        import time as _t
        t0 = getattr(self, "_scan_t0", None)
        if t0 is not None:
            el = int(_t.time() - t0)
            base = getattr(self, "_overlay_base", t("Vyksta skenavimas"))
            self._overlay_text.setText(
                base + " %d:%02d" % (el // 60, el % 60))

    def _position_scan_overlay(self):
        self._scan_overlay.adjustSize()
        w = self._scan_overlay.width()
        h = self._scan_overlay.height()
        self._scan_overlay.move((self.width() - w) // 2,
                                (self.height() - h) // 3)

    def _show_scan_overlay(self, text=None):
        import time as _t
        self._scan_t0 = _t.time()
        self._overlay_base = text if text is not None else t("Vyksta skenavimas")
        self._overlay_text.setText(self._overlay_base + " 0:00")
        self._position_scan_overlay()
        self._scan_overlay.show()
        self._scan_overlay.raise_()
        self._spin_timer.start()

    def _hide_scan_overlay(self):
        self._spin_timer.stop()
        self._scan_overlay.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # getattr: resizeEvent gali ateiti __init__ metu, kol overlay dar nesukurtas
        ov = getattr(self, "_scan_overlay", None)
        if ov is not None and ov.isVisible():
            self._position_scan_overlay()

    @pyqtSlot(object)
    def _on_worker_done(self, candidate_dicts):
        """Slot for ScanWorker.done - update UI from main thread.

        Receives list[dict] (serialized across thread boundary).
        Converts back to Candidate objects safely in the main thread.
        """
        from models import Candidate
        candidates = [
            Candidate(path=d["path"], file_count=d["file_count"],
                      total_bytes=d["total_bytes"], color=d["color"],
                      age_files=d.get("age_files"), age_bytes=d.get("age_bytes"))
            for d in candidate_dicts
        ]
        self._hide_scan_overlay()
        self.btn_scan.setText(t("Skanuoti"))
        self._clear_table()
        self._fill_table(candidates)
        self.btn_scan.setEnabled(True)
        self.btn_clear_all.setEnabled(True)
        self.btn_preview.setEnabled(True)   # po skeno perziura jau turi ka rodyti

    @pyqtSlot(str)
    def _on_worker_error(self, msg):
        """Slot for ScanWorker.error_signal - dispatch to main thread."""
        self._hide_scan_overlay()
        self._log("Scan error: " + msg)
        self.btn_scan.setText(t("Skanuoti"))
        self.btn_scan.setEnabled(True)
        self.btn_clear_all.setEnabled(True)
        if self._candidates:
            self.btn_preview.setEnabled(True)

    @pyqtSlot(object)
    def _on_preview_done(self, data):
        """Slot for PreviewWorker.done - rezultatai i GUI is pagrindines gijos."""
        from handlers import preview_show_results
        self._hide_scan_overlay()
        self.btn_scan.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_clear_all.setEnabled(True)
        preview_show_results(self, data)

    # -- CleanWorker slotai (2026-08-06, Roberto pastabos 4+5) --
    @pyqtSlot(str)
    def _on_clean_progress(self, line):
        """Slot for CleanWorker.progress - gyva zurnalo eilute valymo metu."""
        self._log(line)

    @pyqtSlot(int, float, int)
    def _on_clean_done(self, d, mb, s):
        """Slot for CleanWorker.done - santrauka; zurnalas LIEKA matomas."""
        self._hide_scan_overlay()
        self._update_freed_label()
        self._log(t("=== VALYMAS BAIGTAS: istrinta {} failu, {:.2f} MB, praleista {} ===").format(
            d, mb, s))
        self.lbl_status.setText(
            t("Istrinta {} failu, {:.2f} MB, praleista {}").format(d, mb, s))
        self.btn_scan.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_clear_all.setEnabled(True)
        QMessageBox.information(
            self, t("Valymas baigtas"),
            t("Istrinta {} failu\nIs viso: {:.2f} MB\nPraleista (junction/fresh): {}").format(
                d, mb, s))

    @pyqtSlot(str)
    def _on_clean_error(self, msg):
        """Slot for CleanWorker.error_signal - klaida is fono gijos."""
        self._hide_scan_overlay()
        self._log("Clean error: " + msg)
        self.btn_scan.setEnabled(True)
        self.btn_preview.setEnabled(True)
        self.btn_clear_all.setEnabled(True)
        QMessageBox.critical(
            self, t("Valymo klaida"), t("Klaida: {}").format(msg))

    # PASTABA (Claude fix, 5-as ratas): gui._worker/_working_thread nuorodu
    # NIEKUR nenulinam - jas perraso kitas skenas. Nulinimas done handleryje
    # sunaikina DAR BESISUKANCIA gija (qFatal 0xC0000409 be traceback);
    # nulinimas per thread.finished lenktyniauja su nauju skenu. Mires
    # wrapper'is kintamajame = nekenksmingas; guard'ai handlers.py turi
    # try/except RuntimeError.


    # -- Column setup --
    def _set_col_widths(self):
        # Roberto UX 2026-08-05: lentele prisitaiko prie lango - Folder
        # stulpelis tampus (ima visa laisva ploti), kiti fiksuoti; per ilgi
        # keliai trumpinami PER VIDURI (matosi pradzia ir galas, ne C:...).
        from PyQt6.QtWidgets import QHeaderView
        self.table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        # 2026-08-06: be sito ElideMiddle NEVEIKIA - numatytas wordWrap=True
        # lauzo kelia ties '\' ir ilgos eilutes vel virsdavo "C:..."
        # (patikrinta izoliuotu testu; Qt item view elidina tik be wrap).
        self.table.setWordWrap(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i, w in enumerate([480, 100, 120, 100, 90]):
            if i == 0:
                continue
            self.table.setColumnWidth(i, w)

    # -- Table helpers --
    def _clear_table(self):
        self.table.setRowCount(0)
        self._candidates.clear()
        self._row_color_data.clear()

    def _fill_table(self, candidates):
        # P5 fix: sort by color priority (ZALIA > GELTONA > RAUDONA), then path alpha
        color_priority = {"ZALIA": 0, "GELTONA": 1, "RAUDONA": 2}
        data = sorted(candidates, key=lambda c: (color_priority.get(c.color, 9), c.path))
        self._candidates = data
        self.table.setRowCount(len(data))

        for idx, cand in enumerate(data):
            # Columns: Katalogas | Failai | Dydis (MB) | Tipas | Clear
            size_mb = cand.total_bytes / 1048576.0
            items = [
                QTableWidgetItem(cand.path),
                QTableWidgetItem(str(cand.file_count)),
                QTableWidgetItem("{:.2f}".format(size_mb)),
                QTableWidgetItem(spalva(cand.color)),
            ]
            # Ilgi keliai lenteleje trumpinami (C:...) - pilnas kelias tooltip'e
            items[0].setToolTip(cand.path)
            for col, item in enumerate(items):
                self.table.setItem(idx, col, item)

            # Clear stulpelis - paspaudziamas TEKSTAS, ne QPushButton.
            # Roberto gyvo testo pamoka 2026-08-05: 440 tikru mygtuku
            # nespeja persipiesti skrolinant ir atsiskiria nuo eiluciu.
            clear_item = QTableWidgetItem("Clear" if cand.color != "RAUDONA" else "")
            clear_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if cand.color != "RAUDONA":
                clear_item.setForeground(QColor("#1a4485"))
                cf = clear_item.font()
                cf.setBold(True)
                cf.setUnderline(True)
                cf.setPointSize(self._clear_base_pts)   # ryskiau - tai mygtukas
                clear_item.setFont(cf)
            self.table.setItem(idx, 4, clear_item)

            # Row background color
            hex_ = COLOR_HEX.get(cand.color, "#ffffff")
            qcol = QColor(hex_)
            for c in range(self.table.columnCount()):
                cell = self.table.item(idx, c)
                if cell is not None:
                    cell.setBackground(qcol)
            self._row_color_data[idx] = cand.color

        # P5 fix: status text uses "Is viso" instead of "Iviskio dydis"
        total_mb = sum(c.total_bytes for c in data) / (1024 * 1024)
        self.lbl_status.setText(
            t("Surasta {} vietu | Is viso: {:.2f} MB").format(len(data), total_mb)
        )

    def _on_clear_row(self, folder_path):
        handler_on_clean_row(self, folder_path)

    def _reset_clear_hover(self):
        """Grazina ankstesnio uzvesto Clear srifta i bazini."""
        prev = getattr(self, "_hover_clear_row", None)
        if prev is not None:
            pit = self.table.item(prev, 4)
            if pit is not None and pit.text():
                pf = pit.font()
                pf.setPointSize(self._clear_base_pts)
                pit.setFont(pf)
            self._hover_clear_row = None

    def _on_cell_hover(self, row, col):
        """Clear kaip mygtukas (Roberto UX): uzvedus pele sriftas PAAUGA
        ir zymeklis virsta rankute; nuvedus - grizta."""
        it = self.table.item(row, 4) if col == 4 else None
        active = it is not None and bool(it.text())
        if getattr(self, "_hover_clear_row", None) != (row if active else None):
            self._reset_clear_hover()
        if active:
            f = it.font()
            f.setPointSize(self._clear_base_pts + 2)
            it.setFont(f)
            self._hover_clear_row = row
            self.table.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.table.viewport().unsetCursor()

    def eventFilter(self, obj, event):
        # Pelei paliekant lentele - atstatom Clear srifta ir zymekli
        if obj is self.table.viewport() and event.type() == QEvent.Type.Leave:
            self._reset_clear_hover()
            self.table.viewport().unsetCursor()
        return super().eventFilter(obj, event)

    def _on_cell_clicked(self, row, col):
        """Clear stulpelio (4) paspaudimas - kaip buves mygtukas."""
        if col != 4:
            return
        clear_item = self.table.item(row, 4)
        if clear_item is None or not clear_item.text():
            return   # RAUDONA arba jau isvalyta - nieko nedarom
        path_item = self.table.item(row, 0)
        if path_item:
            self._on_clear_row(path_item.text())

    def _on_double_click(self, item):
        import subprocess
        row = item.row()
        path_item = self.table.item(row, 0)
        if path_item:
            folder = path_item.text()
            os.startfile(folder)

    def _on_context_menu(self, pos):
        """v1.1 desinio klaviso meniu: Kas tai? / Kopijuoti kelia / Atverti.

        "Kas tai?" (Roberto ideja 2026-08-07): zinomai programai atidaromas
        GAMINTOJO puslapis is zinomos_programos.json, nezinomai - Google
        paieskos sarasas. I uzklausa eina TIK programos vardas (zinynas.py
        privatumo garantija - be pilno kelio ir be vartotojo vardo).
        """
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        path_item = self.table.item(row, 0)
        if path_item is None or not path_item.text():
            return
        folder = path_item.text()
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        import zinynas
        import kalba
        menu = QMenu(self)
        vardas = zinynas.vardas_is_kelio(folder)
        act_kas = QAction(
            t("Kas tai? ({})").format(vardas) if vardas else t("Kas tai?"),
            self)
        act_kas.setEnabled(vardas is not None)
        act_copy = QAction(t("Kopijuoti kelia"), self)
        act_open = QAction(t("Atverti aplanka"), self)
        menu.addAction(act_kas)
        menu.addSeparator()
        menu.addAction(act_copy)
        menu.addAction(act_open)
        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen is act_kas:
            v, url, is_zin = zinynas.atidaryti_kas_tai(folder, kalba.LANG)
            if url:
                self._log(
                    t("Kas tai '{}': atidaryta gamintojo svetaine").format(v)
                    if is_zin else
                    t("Kas tai '{}': atidaryta Google paieska").format(v))
        elif chosen is act_copy:
            QApplication.clipboard().setText(folder)
            self.lbl_status.setText(t("Kelias nukopijuotas"))
        elif chosen is act_open:
            os.startfile(folder)

    def _log(self, message):
        self.log_box.append(message)

    # -- Button handlers (delegate to handlers.py) --
    def _on_scan(self):
        handler_on_scan(self)

    def _on_preview(self):
        handler_on_preview(self)

    def _on_clean_green(self):
        handler_on_clean_green(self)


# Standalone launcher
if __name__ == "__main__":
    import sys as _sys
    app = QApplication(_sys.argv)
    win = MainWindow()
    win.show()
    _sys.exit(app.exec())
