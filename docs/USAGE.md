# Użycie

`python app.py` — menu z 14 pozycjami i wyjściem.
`python app.py --list` — dostępność narzędzi.
`python app.py --tools-root D:/PrestigeTech` — niestandardowy katalog samodzielnych projektów.

Launcher sam działa bez instalacji innych narzędzi; przy próbie uruchomienia brakującego
programu wyświetla błąd. Projekty zwykle leżą obok katalogu dashboardu. Nie importuje ich kodu.
Przekazuje argumenty jako listę, bez powłoki. Nie dodaje --apply/--authorized i nie
zatwierdza operacji za użytkownika. W menu Enter na argumentach otwiera pomoc.
Ścieżki względne w argumentach są liczone od bieżącego katalogu użytkownika.
