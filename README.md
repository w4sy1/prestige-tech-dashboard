# Prestige Tech Dashboard
PRESTIGE TECH — by Dominik Wasilak

Dashboard uruchamia samodzielne narzędzia Prestige Tech oraz dziesięć nowych
Centrów z sąsiedniego repozytorium
[prestige-tech](https://github.com/w4sy1/prestige-tech). Wygląd Dashboardu
pozostaje bez zmian. Stare moduły pozostają w katalogu jako historia projektu.

Karta **Security Center** uruchamia aktualną inspekcję plików z eksportem
JSON/TXT/HTML/PDF z kodu `prestige-tech`. Karta **Inspektor plików** nadal
uruchamia starszy, lokalnie wskazany EXE. Dzięki temu oba sposoby pracy są
dostępne bez zmiany wyglądu Dashboardu. PDF wymaga zależności `reportlab`.

## Uruchomienie Centrów z kodu

Sklonuj `prestige-tech` i `prestige-tech-dashboard` do jednego katalogu
nadrzędnego. W środowisku Python 3.11+ zainstaluj zależności:

```powershell
cd ./prestige-tech
python -m pip install -e ".[gui,pdf,signing]"
cd ../prestige-tech-dashboard
python gui_pyside.py
```

W karcie Centrum kliknij **Uruchom z kodu**. Dashboard korzysta z ustalonej
listy lokalnych skryptów; nie przyjmuje dowolnej ścieżki z manifestu.
Nowe EXE Centrów nie zostały jeszcze zweryfikowane i nie są częścią starszych
wydań do pobrania. Dostępność funkcji i brakujące testy opisuje
[status projektu](https://github.com/w4sy1/prestige-tech/blob/master/PROJECT-STATUS.md).

## Starsze narzędzia i wersja 0.3.1

Polski launcher konsolowy samodzielnych narzędzi Prestige Tech, bez kopiowania ich logiki.

## Instalacja i uruchomienie
Python 3.11+. Skopiuj katalog projektu. Podstawowy CLI używa biblioteki standardowej. PDF wymaga requirements-gui.txt; podpisy, jeśli dostępne, wymagają requirements-signing.txt.
```text
python app.py --help
python app.py --support
python -m unittest discover -s tests -v
```
Szczegóły i przykłady: `docs/USAGE.md`. Zależności systemowe opisano w tym pliku.

## Raporty i logi
Opcja `--output` zapisuje lokalnie JSON, TXT i HTML. Bez niej JSON trafia na stdout.
Log JSONL w `logs/` zawiera czas, moduł, akcję, wynik i typ błędu, bez treści wyjątków.
Kod 1 oznacza błąd, kod 2 oznacza negatywny wynik weryfikacji lub niekompletne dane,
jeżeli dane polecenie zwraca takie rozstrzygnięcie. `--dry-run` pokazuje plan bez wykonania.

## Bezpieczeństwo i ograniczenia
Narzędzie przeznaczone do celów edukacyjnych, diagnostycznych oraz do pracy z systemami i sieciami, których właścicielem jest użytkownik lub na których testowanie posiada zgodę.
Dane pozostają lokalne. Polecenia sieciowe wymagają świadomego wywołania;
zapytania DNS i połączenia do wskazanych hostów ujawniają im adres klienta.
Brak uprawnień lub backendu jest błędem, nie pozytywnym wynikiem audytu.
Zakres MVP i ograniczenia platformowe opisano w `docs/USAGE.md`.

## Autor i licencja
Dominik Wasilak, Prestige Tech, prestigetech@gmail.com. Własny kod:
[Prestige Tech Free Use License](LICENSE).

## Wesprzyj autora
Opcja wsparcia autora zostanie udostępniona w przyszłości.
Linki w `config/author.json`.

## GUI i EXE 0.3.1

Uruchom `python gui.py` albo samodzielny EXE. W EXE interpreter, PDF i potrzebne
biblioteki Python są dołączone. Zewnętrzne backendy systemowe pozostają wymagane.
Budowa: [docs/BUILD.md](docs/BUILD.md). Obsługa: [docs/GUI.md](docs/GUI.md).
Ograniczenia bufora i testów: [docs/DESKTOP-STATUS.md](docs/DESKTOP-STATUS.md).
Własny kod podlega Prestige Tech Free Use License. Licencje zależności:
THIRD_PARTY_NOTICES.txt.
