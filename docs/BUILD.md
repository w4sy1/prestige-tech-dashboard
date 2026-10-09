# Samodzielny EXE dla Windows

W katalogu tego repozytorium, z Pythonem 3.13:

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-build.txt
.venv/Scripts/python.exe build_exe.py
```

Wynik `dist/Prestige-Tech-Dashboard-<wersja>.exe` zawiera aktualne GUI PySide6
z niebieską i czarno-złotą stroną główną. Przed udostępnieniem uruchom
`--smoke` i sprawdź oba style oraz start Centrów. Interpreter Python i generator
PDF są zawarte w EXE. Zewnętrzne narzędzia systemowe potrzebne przez wybrane operacje
(np. PowerShell 7, ADB, Nmap) trzeba zainstalować oddzielnie.
Funkcje Termuxa wymagają Androida i Termuxa.

Po zbudowaniu dziesięciu Centrów w sąsiednim repozytorium poleceniem
`python build_centers.py all` uruchom `python package_desktop.py` w katalogu
Dashboardu. Skrypt sprawdza start wszystkich jedenastu EXE, a następnie
tworzy `dist/Prestige-Tech-<wersja>-Windows.zip` z katalogiem `centers/`,
licencją i sumami SHA-256. Istniejącej paczki nie nadpisuje.

Dashboard zapisuje dane w `%LOCALAPPDATA%/PrestigeTech/`.
`--smoke` sprawdza konstrukcję okna. Centra można uruchamiać z kodu obok
repozytorium albo z plików EXE w katalogu `centers/` obok EXE Dashboardu.
Plik nie jest podpisany certyfikatem Authenticode.
Własny kod podlega Prestige Tech Free Use License; licencje zależności znajdują się w
`THIRD_PARTY_NOTICES.txt` i `assets/FONT-LICENSE.txt`.

Workflow Tests uruchamia testy na Windows z Pythonem 3.11 i 3.14.
Dodanie konfiguracji nie oznacza wykonania jej na serwerze GitHub.
