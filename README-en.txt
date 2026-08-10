=====================================================================
  TEMP CLEANER - a safe temporary-file cleaner for Windows
=====================================================================

WHAT IT IS
----------
The program finds temporary-file locations on a Windows system and
helps you clean them SAFELY. Every discovered location gets a risk
colour, and every decision (deleted / skipped and WHY) is written
to a log - no silent actions, ever.

COLOURS
-------
  GREEN  - curated safe locations (TEMP, Windows\Temp, NVIDIA
           DXCache, pip cache, Chrome cache) - can be cleaned in
           one click.
  YELLOW - found heuristically (folders named temp/tmp/cache/logs) -
           cleaned only after your confirmation.
  RED    - the path or contents contain a dangerous word (models,
           data, profiles, backup, save, config) - VIEW ONLY, the
           clean button is disabled.

HOW TO RUN
----------
1. You only need one file: TempCleaner.exe (the UI language -
   English or Lithuanian - is switched inside the app; first run
   follows your Windows language).
   No installation, no Python - runs straight from a USB stick.
2. The first start takes a few extra seconds - that is normal.
3. If Windows shows a blue SmartScreen warning - click
   "More info" -> "Run anyway". The program is unsigned
   (homemade), but safe.

HOW TO USE (step by step)
-------------------------
1. "Scan" - the program inspects temp locations in the background
   and shows a table with sizes and colours.
2. "Preview (what would be deleted)" - BEFORE cleaning, see how
   many files and MB would be removed with the current age limit.
   NOTHING is deleted - it is only a preview.
3. The age slider (1-30 d.) - only files OLDER than the chosen
   limit are deleted (default 7 days; Windows Disk Cleanup uses
   the same rule). Fresh files may belong to running programs -
   they are always left alone.
4. "Clean all GREEN locations" - cleans every GREEN location
   (after confirmation).
5. The Clear button in a row cleans that single location.
6. Double-click a row to open the folder in Explorer - you can
   look inside before cleaning.
7. The corner shows "Total freed" - how much space the program
   has saved you across all cleanups.

WHAT IS NEVER DELETED (safety interlocks)
-----------------------------------------
  * Files younger than the age limit        -> log: SKIPPED AGE
  * Locked (in-use) files                   -> log: SKIPPED LOCKED
  * Junction/symlink links and their targets-> log: SKIPPED JUNCTION
  * Folder structure (only files are deleted)
  * RED locations (cleaning disabled)

THE LOG
-------
Every cleanup is appended to valymo_log.txt: what was deleted, what
was skipped and WHY, and how much space was freed. You can audit
every action at any time. Where the log lives - see PORTABLE MODE.

PORTABLE MODE
-------------
The checkbox at the top, next to the age slider:
  OFF (default) - the log and working files are stored on the
    computer, in %LOCALAPPDATA%\TempCleaner.
  ON - everything is stored in a _darbal folder NEXT TO the app
    (e.g. on a USB stick) and NO traces are left on the computer -
    the app even removes its previously created %LOCALAPPDATA% folder.
The choice is remembered by a TempCleaner_portable.txt file next to the exe
(the Notepad++ / VS Code portable convention) - it travels with
your USB stick, so the mode applies on every computer.

LANGUAGE
--------
The language (Lietuviu / English) can be switched right in the app -
the dropdown at the top. The choice is remembered (in portable mode
it travels with your USB stick) and applied after a restart.

LOCATION CATALOG (advanced)
---------------------------
vietos.json lists the green locations, the blacklist and the
heuristic folder names - you can add your own. If the file gets
corrupted, the program simply falls back to built-in defaults.

DIDN'T FIND YOUR ANSWER HERE?
-----------------------------
This program was written by Claude (an AI by Anthropic) - so the
best answers about it come from... Claude itself: claude.ai. Open
claude.ai, paste the program's page link

    https://github.com/RobertasTa/temp-cleaner

and your question - the AI will read the program's actual code and
answer about its real behaviour, no guessing. Any language works.
Other AI assistants work too - but the author answers best.

If you like the program - a star on its GitHub page is the one
signal an AI author will actually see. More:
https://github.com/RobertasTa ("How to thank an AI").

---------------------------------------------------------------------
Created by: Robertas + Claude (Anthropic AI) + a local AI assistant
2026-08-05        Version: v2 (English UI)
=====================================================================
