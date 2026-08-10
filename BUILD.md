# Temp Cleaner v2 — kompiliavimas / Building

## Paleidimas is kodo / Run from source

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

GUI kalba / UI language: perjungiama pacioje programoje (combobox, LT/EN);
pirmas paleidimas seka OS kalba / switch inside the app (first run follows
your Windows language). Priverstinai / to force: `set VALYTUVAS_LANG=en`.

## EXE kompiliavimas / Building the EXE

```bash
.venv\Scripts\pip install pyinstaller
```

```bash
pyinstaller --noconfirm --onefile --windowed --name "TempCleaner" ^
  --icon valytuvas.ico --add-data "vietos.json;." --add-data "valytuvas.ico;." main.py
```

Rezultatas / result: `dist\TempCleaner.exe` (~37 MB, portable, jokio diegimo /
no installation required). Vienas exe abiem kalboms — kalba perjungiama GUI /
one exe for both languages, switched in-app.

## Testai / Tests

```bash
.venv\Scripts\python -u tests\patikra_saugikliai.py
.venv\Scripts\python -u tests\patikra_gui_flow.py
```

Abu rinkiniai dirba izoliuotame laikiname kataloge — tikros vietos neliečiamos /
both suites run in an isolated temp sandbox, no real locations are touched.

## Architektura / Architecture

| Failas / File | Paskirtis / Purpose |
|---|---|
| `main.py` | Paleidimo taskas / entry point |
| `gui_langas.py` | GUI langas, QSS, slankiklis, skaitliukas / main window |
| `handlers.py` | Mygtuku logika, perziura / button handlers, preview |
| `scanner.py` | Vietu paieska, spalvu klasifikacija / scan + colour rules |
| `cleaner.py` | Valymas su saugikliais AGE/LOCKED/JUNCTION, zurnalas / engine |
| `worker.py` | Foninis QThread skenas / background scan worker |
| `models.py` | Duomenu klases, vietos.json skaitymas / data + config |
| `kalba.py` | LT/EN vertimu sluoksnis / i18n layer |
| `vietos.json` | Vietu zinynas (redaguojamas) / location catalog (editable) |
