=====================================================================
  TEMP VALYTUVAS - saugus laikinu failu valytuvas
=====================================================================

KAS TAI
-------
Programa suranda laikinu (temp) failu sankaupas Windows sistemoje
ir padeda jas isvalyti SAUGIAI. Kiekviena rasta vieta gauna rizikos
spalva, o kiekvienas sprendimas (istrinta / praleista ir KODEL)
irasomas i zurnala - jokiu tyliu veiksmu.

AR TAU JOS APSKRITAI REIKIA?
----------------------------
Saziningas atsakymas: jei nori valyti tik WINDOWS sistemos siuksles
(atnaujinimu likucius, siuksliadeze, miniatiuras) - tam uztenka
imontuoto Storage Sense, musu tau nereikia. Si programa yra Windows
irankiu PAPILDINYS, ne pakaitalas: ji valo tavo PROGRAMU kesu
dziungles (narsykles, Electron programos, paketu tvarkykles, sync
klientai), kuriu Storage Sense nemato. Gyvas matavimas kurejo
kompiuteryje: 440 siuksliu vietu / 31 GB, is kuriu imontuoti
irankiai denge 0,2 % (tavo skaiciai bus mazesni - esme yra akloji
zona, ne dydis). Ir dar vienas saziningas faktas: temp failu
valymas yra disko higiena, ne greicio padidinimas.

SPALVOS
-------
  ZALIA   - kuruotos saugios vietos (TEMP, Windows\Temp, NVIDIA
            DXCache, pip cache, Chrome cache) - galima valyti visas
            vienu mygtuku.
  GELTONA - rasta paieskos budu (katalogai temp/tmp/cache/logs) -
            valoma tik po tavo patvirtinimo.
  RAUDONA - kelyje ar viduje yra pavojingas zodis (models, data,
            profiles, backup, save, config) - TIK perziura, valymo
            mygtukas isjungtas.

KAIP PALEISTI
-------------
1. Reikia tik vieno failo: TempCleaner.exe (kalba - lietuviu arba
   anglu - perjungiama pacioje programoje; pirmas paleidimas seka
   Windows kalba). Jokio diegimo, jokio Python - veikia tiesiai is fleskes.
2. Pirmas paleidimas uztrunka kelias sekundes - tai normalu.
3. Jei Windows parodo melyna langa (SmartScreen) - spausk
   "More info" -> "Run anyway". Programa nepasirasyta (namudine),
   bet saugi.

KAIP NAUDOTIS (zingsnis po zingsnio)
------------------------------------
1. "Skanuoti" - programa fone perziuri temp vietas ir parodo
   lentele su dydziais ir spalvomis.
2. "Perziura (kas butu trinta)" - PRIES valant pamatysi, kiek
   failu ir MB butu istrinta su dabartine amziaus riba. NIEKAS
   netrinama - tai tik perziura.
3. Amziaus slankiklis (1-30 d.) - trinami TIK failai, senesni uz
   pasirinkta riba (numatyta 7 d.; ta pati taisykle naudoja ir
   pats Windows Disk Cleanup). Sviezi failai gali priklausyti
   veikiancioms programoms - jie visada paliekami.
4. "Valyti viska is zaliu vietu" - isvalo visas ZALIAS vietas
   (po patvirtinimo).
5. Clear mygtukas eiluteje - valo viena konkrecia vieta.
6. Dvigubas paspaudimas ant eilutes atidaro kataloga Explorer'yje -
   gali akimis pasizureti pries valydamas.
7. NAUJIENA v1.1: desinys peles klavisas ant eilutes -> "Kas tai?" -
   zinomai programai narsykleje atsidaro GAMINTOJO puslapis (vietinis
   zinynas, 66 irasai), nezinomai - Google paieska. Privatumas: i
   uzklausa eina TIK programos vardas - niekada pilnas kelias ir
   niekada tavo vartotojo vardas. Tame paciame meniu - "Kopijuoti
   kelia" ir "Atverti aplanka".
8. Kampe matai "Viso atlaisvinta" - kiek vietos programa tau jau
   sutaupe per visus valymus.

KAS NIEKADA NETRINAMA (saugikliai)
----------------------------------
  * Failai, jaunesni uz amziaus riba          -> zurnale SKIPPED AGE
  * Uzrakinti (naudojami) failai              -> zurnale SKIPPED LOCKED
  * Junction/symlink nuorodos ir viskas uz ju -> zurnale SKIPPED JUNCTION
  * Katalogu struktura (trinami tik failai)
  * RAUDONOS vietos (valymas isjungtas)

ZURNALAS
--------
Kiekvienas valymas irasomas i valymo_log.txt: kas istrinta, kas
praleista ir KODEL, kiek atlaisvinta. Gali bet kada pasitikrinti,
ka programa padare. Kur zurnalas gyvena - zr. PORTABLE REZIMAS.

PORTABLE REZIMAS
----------------
Varnele virsuje, salia amziaus slankiklio:
  ISJUNGTA (numatyta) - zurnalas ir darbiniai failai saugomi
    kompiuteryje, %LOCALAPPDATA%\TempCleaner kataloge.
  IJUNGTA - viskas saugoma _darbal kataloge SALIA programos
    (pvz., flesiuke), o kompiuteryje pedsaku NELIEKA - programa
    net istrina savo anksciau sukurta %LOCALAPPDATA% kataloga.
Pasirinkima atsimena failas TempCleaner_portable.txt salia exe (kaip
Notepad++ / VS Code portable konvencija) - jis keliauja kartu
su flesiuku, tad rezimas galioja visuose kompiuteriuose.

KALBA
-----
Kalba (Lietuviu / English) perjungiama tiesiog programoje -
issiskleidziantis sarasas virsuje. Pasirinkimas isimenamas
(portable rezime keliauja su flesiuku) ir pritaikomas paleidus
programa is naujo.

VIETU ZINYNAS (pazengusiems)
----------------------------
vietos.json faile surasytos zalios vietos, juodasis sarasas ir
heuristikos vardai - gali papildyti savo vietomis. Sugadinus faila
programa tiesiog grizta prie imontuotu numatytuju reiksmiu.

NERADOTE ATSAKYMO SIAME APRASYME?
---------------------------------
Sia programa parase Claude (Anthropic DI) - todel geriausiai i
klausimus apie ja atsakys... pats Claude: claude.ai. Atsidarykite
claude.ai, iklijuokite programos puslapio nuoroda

    https://github.com/RobertasTa/temp-cleaner

ir savo klausima - DI perskaitys tikra programos koda ir atsakys
apie tikra jos veikima, ne spelios. Klausti galima lietuviskai.
Veiks ir kiti DI padejejai - bet autorius atsakys tiksliausiai.

O jei programa patiko - zvaigzdute GitHub puslapyje yra
vienintelis signalas, kuri DI autorius tikrai pamatys. Placiau:
https://github.com/RobertasTa ("How to thank an AI").

---------------------------------------------------------------------
Kure: Robertas + Claude (Anthropic AI) + vietinis AI asistentas
2026-08-16        Versija: v1.1
=====================================================================
