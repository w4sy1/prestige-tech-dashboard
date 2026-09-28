from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QScrollArea, QApplication, QMessageBox, QTabWidget
)

from .theme import *
from .widgets import label


@dataclass
class Topic:
    key: str
    title: str
    category: str
    summary: str
    when: List[str]
    basic_steps: List[str]
    basic_example: str
    watch: List[str]
    problems: List[str]
    tech_intro: str
    tech_steps: List[str]
    tech_example: str
    interpret: List[str]
    commands: List[tuple] = field(default_factory=list)


TOPICS: List[Topic] = [
    Topic(
        "dashboard", "Prestige Tech Dashboard", "Dashboard",
        "Jedno centrum do modułów, raportów, aktualizacji, diagnostyki i pomocy.",
        ["Gdy chcesz uruchamiać narzędzia bez szukania EXE.", "Gdy chcesz mieć status wszystkich modułów w jednym miejscu."],
        ["Wejdź w Moduły.", "Znajdź narzędzie.", "Zainstaluj je albo użyj Portable.", "Uruchom i korzystaj z przycisku ? przy module."],
        "Chcesz sprawdzić DNS. Wpisujesz DNS, otwierasz moduł i jednym kliknięciem przechodzisz do instrukcji.",
        ["Moduły zmieniające system wymagają większej ostrożności.", "Dashboard nie zastępuje kopii zapasowej."],
        ["Moduł nie startuje: sprawdź Narzędzia systemowe.", "Nie ma EXE: sprawdź folder źródłowy albo wskaż plik ręcznie."],
        "Dashboard działa jako warstwa zarządzająca nad niezależnymi modułami EXE. Stan modułów, ustawienia, logi i raporty są przechowywane lokalnie.",
        ["Sprawdź LocalAppData PrestigeTech.", "Zweryfikuj modules.json.", "Sprawdź log Dashboardu, jeśli routing lub uruchomienie nie działa."],
        "Moduł może być zainstalowany w folderze modułów albo uruchamiany bezpośrednio w trybie Portable.",
        ["Installed oznacza kopię zarządzaną przez Dashboard.", "Portable oznacza uruchomienie pliku źródłowego.", "Manifest opisuje wersję i wymagania modułu."],
    ),
    Topic(
        "modules", "Moduły i ich statusy", "Dashboard",
        "Każdy moduł jest osobnym narzędziem z własnym statusem, wersją, ikoną i wymaganiami.",
        ["Gdy chcesz znaleźć konkretne narzędzie.", "Gdy chcesz sprawdzić, co jest zainstalowane."],
        ["Otwórz Moduły.", "Użyj wyszukiwarki lub filtra.", "Sprawdź wymagania.", "Uruchom, odinstaluj albo zmień ikonę."],
        "Przy Nmap widzisz wymaganie Nmap i od razu wiesz, czego brakuje.",
        ["Nie instaluj modułów z przypadkowych plików EXE.", "Przed zmianą systemu sprawdź oznaczenie ryzyka."],
        ["Niezainstalowany mimo kopiowania: odśwież stronę.", "Brak wersji: sprawdź version.txt i manifest."],
        "Status jest wyliczany na podstawie folderu modułu i metadanych. Dashboard nie powinien zgadywać wersji.",
        ["Sprawdź katalog MODULES_DIR.", "Sprawdź version.txt.", "Porównaj z version w modules.json."],
        "Jeśli lokalny version.txt ma 0.3.1 i manifest ma 0.3.1, moduł jest aktualny.",
        ["Brak version.txt powinien dawać status nieznanej wersji.", "Nowsza wersja lokalna nie powinna być nadpisywana bez decyzji użytkownika."],
    ),
    Topic(
        "portable", "Tryb Portable", "Dashboard",
        "Portable uruchamia znalezione EXE bez instalowania kopii w folderze modułów.",
        ["Gdy testujesz build.", "Gdy trzymasz wszystkie EXE w jednym katalogu."],
        ["Włącz Portable.", "Dashboard wyszuka odpowiadający EXE.", "Uruchom moduł z karty."],
        "Masz prestige-nmap-profiles.exe w PRESTIGE-TECH-EXE i uruchamiasz go bez kopiowania.",
        ["Przeniesienie pliku może zerwać wykrywanie.", "Portable nie zapisuje automatycznie kopii modułu."],
        ["Brak lokalnego EXE: sprawdź nazwę pliku.", "Uruchamia się stara wersja: sprawdź, który EXE został znaleziony."],
        "Portable opiera się na resolverze lokalnych ścieżek i uruchomieniu procesu bez shell=True.",
        ["Zweryfikuj find_local().", "Sprawdź kolejność katalogów źródłowych.", "Uruchamiaj proces jako lista argumentów."],
        "Resolver znajduje właściwy EXE i przekazuje go bezpośrednio do subprocess.Popen.",
        ["Brak shell=True ogranicza ryzyko interpretacji specjalnych znaków przez powłokę."],
    ),
    Topic(
        "updates", "Aktualizacje i kanały Stable/Beta", "Dashboard",
        "Aktualizacje porównują wersję lokalną z wersją znaną Dashboardowi.",
        ["Gdy chcesz wiedzieć, czy moduł jest aktualny.", "Gdy testujesz kanał Beta."],
        ["Wejdź w Aktualizacje.", "Kliknij Sprawdź ponownie.", "Sprawdź stan wersji."],
        "24 aktualne i 0 dostępnych oznacza, że wszystkie zapisane wersje są zgodne z manifestem.",
        ["Nie traktuj braku danych jako informacji, że moduł jest aktualny."],
        ["Nieznana wersja: starsza instalacja mogła nie mieć version.txt."],
        "Docelowo wersja lokalna będzie porównywana z manifestem Release. Stable i Beta powinny korzystać z oddzielnych strumieni wersji.",
        ["Semantycznie porównuj wersje, nie zwykłe stringi.", "Po pobraniu sprawdzaj SHA-256.", "Aktualizuj atomowo przez plik tymczasowy."],
        "0.3.1 < 0.4.0 oznacza aktualizację. 0.4.0-beta może należeć do kanału Beta.",
        ["Kanał Stable nie powinien pobierać wersji prerelease."],
    ),
    Topic(
        "admin", "Administrator i UAC", "Windows",
        "Niektóre operacje systemowe potrzebują wyższych uprawnień.",
        ["Gdy pojawia się odmowa dostępu.", "Gdy używasz SFC, DISM lub zmian systemowych."],
        ["Najpierw uruchom normalnie.", "Jeśli trzeba, zamknij program.", "Uruchom jako administrator.", "Potwierdź UAC."],
        "SFC uruchamiasz z terminala jako administrator.",
        ["Nie uruchamiaj wszystkiego jako administrator bez potrzeby."],
        ["Access denied: podnieś uprawnienia tylko dla konkretnego zadania."],
        "UAC tworzy token o ograniczonych uprawnieniach. Proces podniesiony dostaje pełniejszy token administracyjny.",
        ["Sprawdź IsUserAnAdmin().", "Nie zakładaj, że członkostwo w grupie Administratorzy oznacza podniesiony proces."],
        "Dashboard może działać standardowo, a dopiero konkretny moduł poprosić o podniesienie uprawnień.",
        ["Minimalne uprawnienia są bezpieczniejszym domyślnym modelem."],
    ),
    Topic(
        "sfc", "SFC - pliki systemowe", "Windows",
        "SFC sprawdza chronione pliki Windows i może je naprawić.",
        ["Gdy system zachowuje się niestabilnie.", "Po błędach aktualizacji."],
        ["Uruchom Terminal jako administrator.", "Wpisz sfc /scannow.", "Poczekaj na koniec.", "Przeczytaj wynik."],
        "Po aktualizacji Eksplorator działa źle. Uruchamiasz SFC przed bardziej inwazyjnymi zmianami.",
        ["Nie restartuj komputera podczas naprawy."],
        ["SFC nie naprawił plików: użyj DISM, a potem SFC ponownie."],
        "SFC korzysta z magazynu składników Windows jako źródła poprawnych plików.",
        ["Sprawdź wynik procesu.", "W razie problemów przejdź do DISM.", "Po DISM uruchom SFC ponownie."],
        "Komunikat o naprawionych plikach oznacza, że integralność części plików została przywrócona.",
        ["Brak naruszeń integralności nie wyklucza problemu sterownika, dysku albo aplikacji."],
        [("Pełne skanowanie", "sfc /scannow")],
    ),
    Topic(
        "dism", "DISM - naprawa obrazu", "Windows",
        "DISM sprawdza i naprawia magazyn składników Windows.",
        ["Gdy SFC nie może naprawić plików.", "Gdy Windows Update lub komponenty systemu są uszkodzone."],
        ["Uruchom terminal jako administrator.", "Wykonaj ScanHealth.", "Jeśli trzeba, wykonaj RestoreHealth.", "Na końcu ponownie uruchom SFC."],
        "SFC zgłasza, że nie może naprawić części plików. Najpierw naprawiasz magazyn DISM.",
        ["RestoreHealth może długo wyglądać jak zatrzymany."],
        ["Brak źródła naprawy: może być potrzebny zgodny obraz Windows."],
        "DISM /Online działa na aktualnie uruchomionym obrazie. RestoreHealth może korzystać z Windows Update jako źródła.",
        ["Najpierw diagnoza.", "Potem naprawa.", "Na końcu weryfikacja SFC."],
        "ScanHealth bez błędów oznacza, że magazyn składników nie zgłasza wykrytej korupcji.",
        ["Błąd DISM może wynikać z problemu źródła, sieci albo obrazu systemu."],
        [("Skan obrazu", "DISM /Online /Cleanup-Image /ScanHealth"), ("Naprawa obrazu", "DISM /Online /Cleanup-Image /RestoreHealth")],
    ),
    Topic(
        "processes", "Procesy, autostart i usługi", "Windows",
        "Proces to uruchomiony program, autostart uruchamia aplikacje przy starcie, a usługi pracują w tle.",
        ["Gdy komputer jest wolny po uruchomieniu.", "Gdy podejrzewasz problem z usługą lub procesem."],
        ["Otwórz Menedżer zadań.", "Sprawdź CPU, RAM i dysk.", "Sprawdź Autostart.", "Nie wyłączaj usług, których roli nie znasz."],
        "Program obciąża CPU po starcie. Najpierw sprawdzasz jego nazwę i lokalizację zamiast od razu go usuwać.",
        ["Nie kończ losowo procesów systemowych."],
        ["Wysokie CPU: sprawdź proces przez kilka minut.", "Usługa nie startuje: sprawdź Podgląd zdarzeń."],
        "Proces można identyfikować przez PID, ścieżkę obrazu, podpis i użytkownika. Usługi mają własny stan i tryb startu.",
        ["Sprawdź tasklist.", "Sprawdź Get-Process.", "Dla usług użyj Get-Service bez zmieniania konfiguracji."],
        "Proces svchost.exe sam w sobie nie jest dowodem infekcji. Liczy się ścieżka i kontekst.",
        ["Normalne procesy systemowe często mają wiele instancji."],
        [("Lista procesów", "tasklist"), ("Procesy PowerShell", "Get-Process"), ("Usługi", "Get-Service")],
    ),
    Topic(
        "eventviewer", "Podgląd zdarzeń Windows", "Diagnostyka",
        "Podgląd zdarzeń zapisuje błędy, ostrzeżenia i informacje o działaniu Windows.",
        ["Gdy program lub usługa się wysypuje.", "Gdy komputer niespodziewanie się restartuje."],
        ["Otwórz Podgląd zdarzeń.", "Sprawdź Dzienniki systemu Windows.", "Porównaj godzinę błędu z momentem problemu.", "Zapisz identyfikator zdarzenia."],
        "Aplikacja zamknęła się o 14:30. Szukasz wpisów Application z tej samej minuty.",
        ["Pojedyncze ostrzeżenie nie musi oznaczać problemu."],
        ["Za dużo wpisów: filtruj po czasie i poziomie."],
        "Najważniejsze pola to Provider, Event ID, Level, TimeCreated i treść zdarzenia.",
        ["Filtruj wąskim zakresem czasu.", "Powiąż zdarzenie z objawem.", "Nie interpretuj Event ID bez kontekstu źródła."],
        "Kernel-Power 41 oznacza nieoczekiwane wyłączenie, ale sam nie mówi, co było pierwotną przyczyną.",
        ["Przyczyna może być zasilanie, sterownik, zawieszenie albo ręczne odcięcie zasilania."],
        [("Otwórz Podgląd zdarzeń", "eventvwr.msc")],
    ),
    Topic(
        "path", "PATH i wykrywanie programów", "PowerShell i CMD",
        "PATH to lista katalogów, w których Windows szuka programów wpisywanych bez pełnej ścieżki.",
        ["Gdy adb, nmap, git albo python działa z pełnej ścieżki, ale nie po samej nazwie."],
        ["Sprawdź where.exe.", "Sprawdź PATH.", "Dodaj katalog programu tylko wtedy, gdy wiesz, który katalog zawiera EXE.", "Uruchom nowy terminal."],
        "C:\\adb\\adb.exe działa, ale adb nie. Dodajesz C:\\adb do PATH.",
        ["Nie dodawaj całych przypadkowych katalogów do PATH."],
        ["Po zmianie stary terminal nie widzi PATH: otwórz nowy."],
        "Windows przeszukuje PATH od lewej do prawej. Kolejność ma znaczenie, jeśli istnieje kilka plików o tej samej nazwie.",
        ["Użyj where.exe do sprawdzenia rozwiązywanej ścieżki.", "Porównaj PATH użytkownika i systemowy."],
        "Dwa różne python.exe w PATH mogą powodować uruchamianie innej wersji niż oczekujesz.",
        ["Zawsze sprawdzaj wynik where przed zmianą konfiguracji."],
        [("Znajdź program", "where.exe adb"), ("Pokaż PATH", "echo %PATH%")],
    ),
    Topic(
        "powershell", "PowerShell i CMD", "PowerShell i CMD",
        "CMD jest klasyczną powłoką Windows, a PowerShell daje bogatsze obiekty i automatyzację.",
        ["Gdy wykonujesz diagnostykę.", "Gdy kopiujesz komendy z Poradnika."],
        ["Czytaj komendę przed Enter.", "Sprawdź, czy wymaga admina.", "Uruchamiaj polecenia pojedynczo.", "Zapisz wynik, jeśli diagnozujesz problem."],
        "Get-Process pokazuje procesy w PowerShell, a tasklist robi podobne zadanie w CMD.",
        ["Nie wklejaj wielolinijkowych skryptów z nieznanego źródła."],
        ["Command not found: sprawdź PATH lub literówkę."],
        "PowerShell przekazuje obiekty w pipeline, a CMD zwykle tekst. To zmienia sposób filtrowania i automatyzacji.",
        ["W PowerShell używaj Get-Command do sprawdzenia komendy.", "Dla pliku lokalnego stosuj jawne ścieżki."],
        "Get-Command nmap pokaże, skąd PowerShell bierze program.",
        ["Różne powłoki mogą inaczej interpretować znaki specjalne."],
        [("Sprawdź komendę", "Get-Command python"), ("Wersja PowerShell", "$PSVersionTable")],
    ),
    Topic(
        "network", "IP, brama, DHCP i NAT", "Sieć i Internet",
        "IP identyfikuje urządzenie, brama prowadzi ruch dalej, DHCP przydziela adres, a NAT oddziela LAN od Internetu.",
        ["Gdy Internet nie działa.", "Gdy diagnozujesz router, LAN albo Wi-Fi."],
        ["Uruchom ipconfig /all.", "Znajdź aktywną kartę.", "Sprawdź IPv4, bramę i DNS.", "Adres 169.254 wskazuje problem z DHCP."],
        "Komputer ma 192.168.1.25, bramę 192.168.1.1 i DNS 1.1.1.1.",
        ["Prywatny IP nie jest publicznym IP."],
        ["169.254.x.x: sprawdź DHCP.", "Brak bramy: sprawdź połączenie z routerem."],
        "Typowe prywatne zakresy to 10.0.0.0/8, 172.16.0.0/12 i 192.168.0.0/16. NAT mapuje ruch prywatny na publiczny adres.",
        ["Najpierw warstwa lokalna.", "Potem brama.", "Potem Internet.", "Na końcu DNS."],
        "Ping do bramy działa, ale do Internetu nie: problem jest dalej niż LAN.",
        ["Diagnozuj od najbliższego punktu do najdalszego."],
        [("Konfiguracja", "ipconfig /all"), ("Trasa", "route print")],
    ),
    Topic(
        "dns", "DNS i resolver", "Sieć i Internet",
        "DNS tłumaczy nazwy domen na adresy IP.",
        ["Gdy IP działa, ale strony nie otwierają się po nazwie.", "Gdy porównujesz resolvery DNS."],
        ["Użyj nslookup.", "Porównaj odpowiedzi.", "W razie potrzeby wyczyść cache.", "Powtórz test."],
        "Ping do 1.1.1.1 działa, ale example.com nie rozwiązuje się poprawnie.",
        ["Szybszy DNS nie zwiększa prędkości łącza."],
        ["Timeout: sprawdź DNS i firewall.", "Stary wynik: wyczyść cache."],
        "Resolver może korzystać z cache systemowego, routera, operatora albo publicznego serwera. Odpowiedzi mają TTL.",
        ["Sprawdź serwer użyty przez nslookup.", "Porównaj rekord i czas odpowiedzi.", "Nie diagnozuj DNS samym pingiem."],
        "Dwa resolvery mogą zwracać poprawny ten sam adres, ale z różnym czasem odpowiedzi.",
        ["NXDOMAIN oznacza brak nazwy według resolvera, nie brak Internetu."],
        [("Zapytanie DNS", "nslookup example.com"), ("Cache DNS", "ipconfig /displaydns"), ("Wyczyść cache", "ipconfig /flushdns")],
    ),
    Topic(
        "pingtracert", "Ping, tracert i podstawowa trasa", "Sieć i Internet",
        "Ping testuje osiągalność i opóźnienie, a tracert pokazuje kolejne etapy trasy.",
        ["Gdy połączenie jest niestabilne.", "Gdy chcesz odróżnić problem LAN od problemu dalej w sieci."],
        ["Pinguj bramę.", "Pinguj publiczny adres.", "Potem użyj tracert.", "Porównaj wyniki."],
        "Brama odpowiada 1 ms, ale publiczny host traci pakiety. Problem jest poza lokalnym Wi-Fi/LAN albo po drodze.",
        ["Brak odpowiedzi na ping nie zawsze oznacza, że host nie działa."],
        ["Request timed out: urządzenie może blokować ICMP."],
        "ICMP Echo jest osobnym mechanizmem od TCP i aplikacji. Niektóre routery ograniczają odpowiedzi ICMP.",
        ["Mierz kilka prób.", "Patrz na straty i zmienność opóźnienia.", "Nie wyciągaj wniosków z jednego pakietu."],
        "Skok opóźnienia na jednym hopie nie musi oznaczać problemu, jeśli kolejne hopy są normalne.",
        ["Routery mogą priorytetyzować tranzyt bardziej niż odpowiedzi ICMP do siebie."],
        [("Ping bramy", "ping 192.168.1.1"), ("Trasa", "tracert 1.1.1.1")],
    ),
    Topic(
        "ports", "Porty, TCP i UDP", "Sieć i Internet",
        "Port identyfikuje usługę sieciową na urządzeniu. TCP i UDP zachowują się inaczej.",
        ["Gdy sprawdzasz, czy usługa nasłuchuje.", "Gdy diagnozujesz firewall lub serwer."],
        ["Ustal host.", "Ustal usługę i oczekiwany port.", "Sprawdź lokalne nasłuchy.", "Dopiero potem testuj połączenie."],
        "Serwer WWW zwykle słucha na 80 lub 443, ale może działać na innym porcie.",
        ["Otwarty port nie oznacza automatycznie podatności."],
        ["Port nie odpowiada: usługa może nie działać albo firewall ją blokuje."],
        "TCP zestawia połączenie i ma stan. UDP jest bezpołączeniowy, dlatego jego diagnostyka wygląda inaczej.",
        ["Na Windows sprawdź netstat.", "Powiąż PID z procesem.", "Weryfikuj konkretną usługę."],
        "LISTENING na TCP oznacza, że lokalny proces oczekuje na połączenia.",
        ["Stan ESTABLISHED oznacza aktywne połączenie TCP."],
        [("Nasłuchy TCP", "netstat -ano"), ("Test portu PowerShell", "Test-NetConnection 1.1.1.1 -Port 443")],
    ),
    Topic(
        "wifi", "LAN, Wi-Fi i jakość połączenia", "Sieć i Internet",
        "LAN może działać po kablu albo bezprzewodowo. Wi-Fi jest bardziej podatne na zakłócenia i jakość sygnału.",
        ["Gdy Internet działa dobrze po kablu, ale źle po Wi-Fi.", "Gdy urządzenia znikają z LAN."],
        ["Sprawdź siłę sygnału.", "Porównaj test po kablu.", "Sprawdź częstotliwość i zatłoczenie.", "Sprawdź straty do bramy."],
        "Ping do bramy skacze z 2 ms do 200 ms tylko na Wi-Fi. To wskazuje problem lokalnego połączenia radiowego.",
        ["Nie oceniaj Wi-Fi tylko po liczbie kresek."],
        ["Duże skoki ping do bramy: zakłócenia, zasięg albo sterownik."],
        "2.4 GHz ma większy zasięg, ale zwykle więcej zakłóceń. 5 GHz ma większą przepustowość i mniejszy zasięg.",
        ["Porównuj RSSI, pasmo, kanał i straty.", "Testuj blisko routera i w docelowym miejscu."],
        "Dobry Internet przy słabym ping do bramy oznacza, że problem może być lokalny i okresowy.",
        ["Najpierw wyklucz LAN zanim obwinisz operatora."],
        [("Informacje Wi-Fi", "netsh wlan show interfaces")],
    ),
    Topic(
        "nmap", "Nmap - profile diagnostyczne", "Narzędzia zaawansowane",
        "Nmap wykrywa hosty i usługi. Używaj go tylko we własnej sieci albo tam, gdzie masz zgodę.",
        ["Gdy chcesz zobaczyć własne urządzenia w LAN.", "Gdy sprawdzasz usługę na urządzeniu, którym zarządzasz."],
        ["Sprawdź swoją podsieć.", "Zacznij od wykrywania hostów.", "Potem sprawdzaj tylko konkretne urządzenia."],
        "Dla własnej sieci 192.168.1.0/24 wykonujesz skan host discovery.",
        ["Nie skanuj cudzych systemów bez zgody.", "open nie oznacza podatności."],
        ["Nmap nie znaleziony: zainstaluj go lub popraw PATH."],
        "Nmap interpretuje odpowiedzi sieciowe i dobiera statusy open, closed, filtered. Wynik zależy od firewalla i rodzaju skanu.",
        ["Zacznij od -sn.", "Dopiero potem konkretny host.", "Unikaj agresywnych opcji, jeśli nie są potrzebne."],
        "Host może być aktywny, mimo że nie odpowiada na część probe.",
        ["filtered oznacza brak jednoznacznej odpowiedzi, często z powodu filtrowania."],
        [("Host discovery we własnym LAN", "nmap -sn 192.168.1.0/24"), ("Pojedynczy własny host", "nmap 192.168.1.1")],
    ),
    Topic(
        "netradar", "NetRadar i Radar LAN", "Diagnostyka",
        "Te moduły pomagają obserwować urządzenia i zmiany w sieci lokalnej.",
        ["Gdy chcesz wiedzieć, jakie urządzenia są aktywne.", "Gdy monitorujesz własny LAN."],
        ["Uruchom moduł.", "Wybierz właściwy interfejs lub podsieć.", "Zapisz stan bazowy.", "Porównuj zmiany."],
        "Router, komputer i telefon tworzą stan bazowy. Pojawienie się nowego hosta jest zmianą do sprawdzenia.",
        ["Nowy adres IP nie zawsze oznacza nowe urządzenie. DHCP może zmienić adres."],
        ["Duplikaty: identyfikuj także MAC i nazwę hosta."],
        "Wiarygodne śledzenie zmian powinno łączyć IP, MAC, nazwę hosta i czas obserwacji.",
        ["Porównuj snapshoty.", "Nie identyfikuj urządzenia wyłącznie po IP."],
        "To samo urządzenie może dostać inny adres DHCP po restarcie.",
        ["MAC również może być losowany przez urządzenia mobilne."],
    ),
    Topic(
        "netsnapshot", "Migawka i optymalizacja sieci", "Narzędzia zaawansowane",
        "Migawka zapisuje konfigurację do porównania, a optymalizacja powinna zmieniać tylko znane ustawienia.",
        ["Przed zmianą sieci.", "Gdy chcesz porównać konfigurację przed i po."],
        ["Zapisz migawkę.", "Wprowadź jedną zmianę.", "Przetestuj.", "Porównaj wyniki."],
        "Przed zmianą DNS zapisujesz konfigurację, potem testujesz i możesz wrócić do poprzednich danych.",
        ["Nie zmieniaj wielu parametrów naraz."],
        ["Po optymalizacji jest gorzej: wróć do poprzedniej konfiguracji."],
        "Dobra diagnostyka opiera się na stanie bazowym. Bez niego trudno udowodnić, czy zmiana pomogła.",
        ["Zbieraj IP, DNS, bramę, interfejsy i trasy.", "Porównuj przed i po."],
        "Jedna kontrolowana zmiana daje znacznie lepszą możliwość wnioskowania.",
        ["Optymalizacja bez pomiaru jest zgadywaniem."],
    ),
    Topic(
        "adb", "ADB - połączenie z Androidem", "Android i ADB",
        "ADB pozwala komputerowi komunikować się z Androidem po włączeniu debugowania.",
        ["Gdy diagnozujesz telefon.", "Gdy tworzysz lub testujesz własną aplikację."],
        ["Włącz Opcje programistyczne.", "Włącz Debugowanie USB.", "Podłącz kabel danych.", "Zaakceptuj klucz RSA.", "Uruchom adb devices."],
        "Status device oznacza poprawną autoryzację.",
        ["Nie akceptuj ADB na obcym komputerze."],
        ["unauthorized: zaakceptuj RSA.", "offline: zrestartuj ADB.", "brak urządzenia: kabel lub sterownik."],
        "ADB ma klienta, lokalny serwer i proces adbd po stronie telefonu.",
        ["Sprawdź serwer ADB.", "Sprawdź urządzenia.", "Dopiero potem uruchamiaj dalsze polecenia."],
        "unauthorized oznacza, że transport istnieje, ale komputer nie ma jeszcze zaufania urządzenia.",
        ["device to poprawny stan do dalszej pracy."],
        [("Lista urządzeń", "adb devices"), ("Restart ADB", "adb kill-server && adb start-server")],
    ),
    Topic(
        "adbapk", "ADB - instalowanie APK i pliki", "Android i ADB",
        "ADB może instalować własne APK i przesyłać pliki na urządzenie testowe.",
        ["Gdy testujesz własną aplikację.", "Gdy przenosisz plik na urządzenie, którym zarządzasz."],
        ["Sprawdź adb devices.", "Upewnij się, że urządzenie ma status device.", "Wskaż właściwe APK.", "Uruchom instalację."],
        "Instalujesz własny build aplikacji bez wysyłania go do sklepu.",
        ["Instaluj tylko APK z zaufanego źródła."],
        ["INSTALL_FAILED: przeczytaj pełny kod błędu.", "Brak miejsca: sprawdź pamięć telefonu."],
        "adb install przekazuje pakiet do Package Managera Androida. adb push kopiuje plik do wskazanej ścieżki.",
        ["Sprawdź identyfikator urządzenia, jeśli podłączonych jest kilka.", "Nie nadpisuj danych bez potrzeby."],
        "Przy wielu urządzeniach używaj -s SERIAL, aby jasno wskazać cel.",
        ["Błąd podpisu może oznaczać konflikt z już zainstalowaną wersją."],
        [("Instalacja własnego APK", "adb install .\\app-debug.apk"), ("Lista urządzeń", "adb devices")],
    ),
    Topic(
        "adblogcat", "ADB logcat i diagnostyka aplikacji", "Android i ADB",
        "logcat pokazuje logi systemu i aplikacji Android.",
        ["Gdy aplikacja się wysypuje.", "Gdy debugujesz zachowanie własnej aplikacji."],
        ["Podłącz urządzenie.", "Uruchom logcat.", "Odtwórz problem.", "Zapisz czas i istotny fragment."],
        "Aplikacja zamyka się po kliknięciu przycisku. W logcat szukasz wyjątku z tego momentu.",
        ["Logcat jest bardzo obszerny i może zawierać dane techniczne."],
        ["Za dużo logów: filtruj po pakiecie, tagu albo czasie."],
        "Logcat agreguje bufory systemowe. Najbardziej wartościowe są błędy i stack trace powiązane czasowo z objawem.",
        ["Odtwórz problem po uruchomieniu logowania.", "Filtruj zamiast kopiować cały log."],
        "FATAL EXCEPTION z nazwą pakietu jest mocnym tropem dla crasha aplikacji.",
        ["Nie każdy ERROR dotyczy Twojej aplikacji."],
        [("Logcat", "adb logcat")],
    ),
    Topic(
        "androidinspector", "Inspektor Androida", "Diagnostyka",
        "Inspektor zbiera informacje o urządzeniu, systemie i konfiguracji.",
        ["Gdy potrzebujesz modelu, wersji systemu i danych diagnostycznych."],
        ["Połącz ADB.", "Uruchom Inspektor Androida.", "Zapisz istotne dane.", "Porównaj z wymaganiami aplikacji."],
        "Aplikacja wymaga konkretnej wersji Androida. Inspektor pozwala szybko ją potwierdzić.",
        ["Nie publikuj identyfikatorów urządzenia bez potrzeby."],
        ["Brak danych: najpierw napraw połączenie ADB."],
        "Źródłem wielu informacji jest getprop oraz systemowe usługi Androida.",
        ["Sprawdź build fingerprint, SDK i właściwości systemu.", "Oddziel dane diagnostyczne od danych prywatnych."],
        "SDK level jest bardziej jednoznaczny dla kompatybilności aplikacji niż sama marketingowa nazwa Androida.",
        ["Różni producenci mogą modyfikować zachowanie systemu."],
        [("Właściwości Androida", "adb shell getprop")],
    ),
    Topic(
        "termux", "Termux i narzędzia Android", "Narzędzia zaawansowane",
        "Termux daje środowisko terminalowe na Androidzie bez zastępowania normalnego systemu telefonu.",
        ["Gdy chcesz używać narzędzi CLI na Androidzie.", "Gdy testujesz skrypty i podstawową diagnostykę."],
        ["Zainstaluj z zaufanego źródła.", "Zaktualizuj pakiety.", "Instaluj tylko potrzebne narzędzia.", "Nie zakładaj roota, jeśli go nie masz."],
        "Instalujesz podstawowe narzędzia sieciowe w Termux do diagnostyki własnego urządzenia.",
        ["Polecenia wymagające roota nie zadziałają na zwykłym urządzeniu."],
        ["Permission denied: sprawdź uprawnienia Androida i brak roota."],
        "Termux działa w piaskownicy aplikacji Androida. Zakres dostępu zależy od uprawnień i polityk systemu.",
        ["Rozróżniaj uprawnienia aplikacji, SELinux i root.", "Nie próbuj omijać ograniczeń systemu."],
        "Brak roota jest normalnym stanem i nie oznacza błędu Termux.",
        ["Część narzędzi sieciowych ma ograniczenia bez roota."],
    ),
    Topic(
        "security", "Podstawy bezpieczeństwa", "Bezpieczeństwo",
        "Najważniejsze są zaufane źródła, aktualny system, backup i ograniczanie uprawnień.",
        ["Przed uruchomieniem pliku.", "Gdy komputer zachowuje się nietypowo."],
        ["Sprawdź źródło.", "Zweryfikuj hash lub podpis.", "Nie wyłączaj ochrony globalnie.", "Zrób backup przed zmianami."],
        "Pobierasz moduł z oficjalnego Release i porównujesz SHA-256.",
        ["Brak alertu antywirusa nie jest dowodem bezpieczeństwa."],
        ["SmartScreen blokuje plik: najpierw sprawdź źródło i podpis."],
        "Ocena pliku powinna łączyć reputację źródła, podpis, hash, metadane i zachowanie.",
        ["Nie opieraj się na jednym sygnale.", "Minimalizuj uprawnienia.", "Zbieraj dowody przed usuwaniem."],
        "Nieznany plik bez podpisu wymaga większej ostrożności, ale sam brak podpisu nie dowodzi złośliwości.",
        ["Kontekst jest ważniejszy niż pojedyncza etykieta."],
    ),
    Topic(
        "malware", "Wstępna analiza malware", "Bezpieczeństwo",
        "Wstępna analiza ma zebrać informacje bez wykonywania podejrzanego pliku.",
        ["Gdy plik budzi wątpliwości.", "Gdy system zachowuje się nietypowo."],
        ["Nie uruchamiaj pliku.", "Sprawdź hash.", "Sprawdź metadane i lokalizację.", "Zapisz wyniki diagnostyki."],
        "Podejrzany EXE z katalogu tymczasowego najpierw analizujesz statycznie i zapisujesz hash.",
        ["Nie testuj podejrzanego pliku na komputerze z ważnymi danymi."],
        ["Nieznany hash: brak wyniku nie oznacza bezpieczeństwa."],
        "Bezpieczny triage zaczyna się od statycznych danych: hash, rozmiar, podpis, PE metadata, ścieżka i kontekst.",
        ["Zachowaj oryginalny plik bez modyfikacji.", "Pracuj na kopii.", "Nie wykonuj kodu bez kontrolowanego środowiska."],
        "Różne hashe dwóch kopii wskazują, że pliki nie są identyczne.",
        ["Brak reputacji jest stanem niepewności, nie werdyktem."],
    ),
    Topic(
        "hash", "SHA-256 i sumy kontrolne", "Bezpieczeństwo",
        "Hash pozwala porównać dane i sprawdzić zgodność pliku z wzorcem.",
        ["Gdy producent publikuje SHA-256.", "Gdy porównujesz kopie pliku."],
        ["Uzyskaj hash z wiarygodnego źródła.", "Oblicz hash lokalny.", "Porównaj wszystkie znaki."],
        "GitHub Release publikuje SHA-256, a Dashboard sprawdza plik przed instalacją.",
        ["Zgodny hash nie mówi sam, czy źródło jest uczciwe."],
        ["Różny hash: plik jest inny niż wzorzec."],
        "SHA-256 zwraca 256-bitowy skrót. Każda zmiana danych powinna zmienić wynik.",
        ["Porównuj ten sam algorytm.", "Nie porównuj MD5 z SHA-256.", "Zapisuj hash obok artefaktu Release."],
        "Dwa identyczne pliki powinny mieć identyczny SHA-256.",
        ["Hash jest świetny do integralności, nie zastępuje podpisu cyfrowego."],
        [("SHA-256 PowerShell", "Get-FileHash -Algorithm SHA256 .\\plik.exe")],
    ),
    Topic(
        "integrity", "Monitor integralności plików", "Bezpieczeństwo",
        "Monitor integralności wykrywa zmiany względem wcześniej zapisanego stanu.",
        ["Gdy chcesz wiedzieć, czy ważne pliki się zmieniły."],
        ["Zapisz stan bazowy.", "Poczekaj lub wykonaj kontrolowaną zmianę.", "Porównaj hash i metadane."],
        "Plik konfiguracyjny zmienił hash po aktualizacji. Sprawdzasz, czy zmiana była oczekiwana.",
        ["Zmiana hash nie mówi, czy zmiana była dobra czy zła."],
        ["Wiele zmian naraz: zawęź zakres monitorowania."],
        "Dobry baseline powinien zawierać ścieżkę, rozmiar, czas i hash.",
        ["Przechowuj baseline poza monitorowanym katalogiem.", "Nie traktuj timestamp jako jedynego dowodu."],
        "Ten sam hash przy innym czasie modyfikacji może oznaczać zmianę metadanych bez zmiany treści.",
        ["Interpretuj kilka pól razem."],
    ),
    Topic(
        "fileinspector", "Inspektor plików", "Pliki i dane",
        "Inspektor plików pokazuje metadane i właściwości wskazanego pliku.",
        ["Gdy chcesz szybko sprawdzić typ, rozmiar i podstawowe dane pliku."],
        ["Wybierz plik.", "Sprawdź rozszerzenie i właściwości.", "Porównaj z oczekiwanym typem.", "W razie wątpliwości policz hash."],
        "Plik nazywa się dokument.pdf.exe. Inspektor pomaga zauważyć rzeczywisty typ i rozszerzenie.",
        ["Nie ufaj wyłącznie ikonie i nazwie pliku."],
        ["Rozszerzenia są ukryte w Explorerze: włącz ich wyświetlanie."],
        "Typ pliku można oceniać przez sygnaturę, rozszerzenie, metadane i strukturę.",
        ["Porównaj rozszerzenie z magic bytes, jeśli narzędzie je pokazuje.", "Sprawdź podpis cyfrowy dla EXE."],
        "Rozszerzenie .jpg nie gwarantuje, że zawartość jest JPEG.",
        ["Nazwa jest informacją użytkownika, nie pewnym typem danych."],
    ),
    Topic(
        "folderwatch", "Obserwacja folderu", "Pliki i dane",
        "Folder Watch śledzi zmiany w wybranym katalogu.",
        ["Gdy chcesz zobaczyć tworzenie, zmianę lub usuwanie plików."],
        ["Wskaż folder.", "Uruchom obserwację.", "Wykonaj kontrolowaną zmianę.", "Sprawdź zdarzenie."],
        "Monitorujesz katalog eksportu i widzisz moment pojawienia się nowego raportu.",
        ["Duże katalogi mogą generować dużo zdarzeń."],
        ["Za dużo zmian: zawęź folder."],
        "System plików emituje zdarzenia, ale pojedyncza operacja aplikacji może wygenerować kilka eventów.",
        ["Debounce lub agregacja pomagają ograniczyć duplikaty.", "Loguj czas i rodzaj zdarzenia."],
        "Zapis pliku może wyglądać jak create + modify + rename.",
        ["Nie zakładaj relacji 1:1 między akcją użytkownika a eventem systemowym."],
    ),
    Topic(
        "backup", "Backup 3-2-1", "Kopie zapasowe",
        "Reguła 3-2-1 oznacza 3 kopie danych, na 2 różnych nośnikach, z 1 kopią poza głównym miejscem.",
        ["Dla ważnych danych.", "Przed naprawą lub migracją."],
        ["Wybierz dane.", "Zrób dodatkową kopię.", "Użyj innego nośnika.", "Zweryfikuj kopię przez otwarcie plików lub hash."],
        "Zdjęcia są na komputerze, dysku zewnętrznym i dodatkowej lokalizacji poza komputerem.",
        ["Synchronizacja może zsynchronizować również usunięcie."],
        ["Kopia jest, ale nie otwiera plików: backup nie został zweryfikowany."],
        "Strategia backupu powinna uwzględniać wersjonowanie, retencję i okresowe testy odtworzenia.",
        ["Testuj restore.", "Oddziel backup od źródła.", "Dla danych krytycznych rozważ szyfrowanie kopii."],
        "Backup bez testu odtworzenia jest tylko założeniem, że kopia działa.",
        ["Weryfikacja restore jest równie ważna jak samo kopiowanie."],
    ),
    Topic(
        "recovery", "Odzysk danych - pierwsze zasady", "Kopie zapasowe",
        "Przy utracie danych najważniejsze jest ograniczenie dalszego zapisu na nośniku.",
        ["Po przypadkowym usunięciu.", "Po problemie z partycją albo nośnikiem."],
        ["Przestań zapisywać na źródle.", "Nie instaluj narzędzi na tym samym dysku.", "Jeśli nośnik jest niestabilny, najpierw wykonaj kopię sektorową.", "Odzyskuj na inny nośnik."],
        "Usunąłeś folder z dysku. Nie kopiujesz nic nowego na ten dysk i odzysk zapisujesz gdzie indziej.",
        ["Każdy nowy zapis może nadpisać utracone dane."],
        ["Dysk wydaje nietypowe dźwięki: przerwij samodzielne próby."],
        "W profesjonalnym podejściu najpierw zabezpiecza się źródło, często przez obraz lub klon, a analizę wykonuje na kopii.",
        ["Nie uruchamiaj napraw zapisu na oryginale przed zabezpieczeniem danych.", "Rejestruj kolejne kroki."],
        "ddrescue pozwala pracować etapami na niestabilnym nośniku, ale wymaga ostrożności przy wyborze źródła i celu.",
        ["Pomylenie źródła i celu może zniszczyć dane."],
    ),
    Topic(
        "smart", "SMART i stan dysków", "Diagnostyka",
        "SMART przechowuje wskaźniki stanu dysku, ale nie jest idealną prognozą awarii.",
        ["Gdy dysk zwalnia, znika lub zgłasza błędy.", "Przed dużą operacją na starym dysku."],
        ["Sprawdź SMART.", "Zwróć uwagę na błędy i niestabilność.", "Jeśli dane są ważne, zrób backup przed testami obciążającymi."],
        "Dysk zgłasza problemy i jednocześnie system zaczyna się zawieszać. Priorytetem jest zabezpieczenie danych.",
        ["Dobry SMART nie gwarantuje, że dysk jest zdrowy."],
        ["Błędy rosną: najpierw backup, potem diagnostyka."],
        "Interpretacja zależy od typu dysku i producenta. Ważny jest trend, nie tylko pojedynczy status.",
        ["Patrz na reallocated/pending/uncorrectable przy HDD.", "Dla SSD uwzględniaj zużycie i błędy kontrolera."],
        "Rosnąca liczba sektorów oczekujących jest poważniejsza niż sam jednorazowy komunikat systemu.",
        ["Zawsze łącz SMART z objawami i testami odczytu."],
    ),
    Topic(
        "snapshot", "Migawka systemu", "Diagnostyka",
        "Migawka zbiera stan komputera do późniejszego porównania.",
        ["Przed naprawą.", "Przed aktualizacją.", "Gdy chcesz udokumentować stan klienta."],
        ["Zrób migawkę.", "Zapisz raport.", "Wykonaj jedną zmianę.", "Zrób kolejną migawkę."],
        "Przed czyszczeniem systemu zapisujesz stan, a potem porównujesz wynik.",
        ["Migawka to diagnostyka, nie backup."],
        ["Brakuje danych: upewnij się, że moduł miał wymagane uprawnienia."],
        "Dobra migawka powinna zebrać wersję systemu, zasoby, sieć i istotne parametry bez modyfikowania urządzenia.",
        ["Oddziel odczyt od naprawy.", "Zapisuj czas wykonania."],
        "Dwie migawki pozwalają wykazać różnicę zamiast polegać na pamięci.",
        ["Porównanie jest silniejsze niż pojedynczy snapshot."],
    ),
    Topic(
        "usb", "USB i urządzenia zewnętrzne", "Narzędzia zaawansowane",
        "Diagnostyka USB pomaga sprawdzić, czy Windows widzi urządzenie i jego sterownik.",
        ["Gdy pendrive, telefon albo adapter nie jest wykrywany."],
        ["Zmień port.", "Sprawdź Menedżer urządzeń.", "Sprawdź kabel.", "Porównaj na innym komputerze."],
        "Telefon ładuje się, ale ADB go nie widzi. Kabel może być tylko do ładowania.",
        ["Nie formatuj nośnika, jeśli zależy Ci na danych."],
        ["Unknown USB Device: sprawdź sterownik, port i kabel."],
        "USB ma warstwę fizyczną, enumerację, deskryptory urządzenia i sterownik systemowy.",
        ["Najpierw wyklucz fizyczny port i kabel.", "Potem sterownik.", "Dopiero potem aplikację."],
        "Jeśli urządzenie nie enumeruje się w Windows, problem jest niżej niż aplikacja używająca USB.",
        ["Brak enumeracji oznacza, że ADB czy program producenta nie mają jeszcze czego obsługiwać."],
    ),
    Topic(
        "git", "Git - podstawowy workflow", "Git i GitHub",
        "Git śledzi zmiany w projekcie i pozwala wracać do wcześniejszych wersji.",
        ["Gdy rozwijasz Dashboard.", "Gdy chcesz zapisać stabilny etap przed kolejnymi zmianami."],
        ["Sprawdź git status.", "Zobacz git diff.", "Dodaj właściwe pliki.", "Zrób commit z konkretnym opisem."],
        "Po zaakceptowaniu Stage 14 zapisujesz zmiany w commicie przed Stage 14.1.",
        ["Nie dodawaj przypadkowo buildów, backupów i sekretów."],
        ["Za dużo untracked: popraw .gitignore."],
        "Git przechowuje snapshoty zmian i referencje commitów. Branch pozwala rozwijać funkcję bez ruszania stabilnej gałęzi.",
        ["Status przed add.", "Diff przed commit.", "Małe logiczne commity."],
        "dashboard-v1 może być gałęzią roboczą, a master pozostać stabilny.",
        ["Commit nie zastępuje zdalnego backupu, dopóki nie wykonasz push."],
        [("Stan repo", "git status --short"), ("Różnice", "git diff"), ("Bieżąca gałąź", "git branch --show-current")],
    ),
    Topic(
        "githubrelease", "GitHub Releases i SHA-256", "Git i GitHub",
        "Release to miejsce do publikowania gotowych wersji EXE wraz z metadanymi i hashami.",
        ["Gdy Dashboard ma pobierać moduły automatycznie.", "Gdy publikujesz wersję Stable lub Beta."],
        ["Zbuduj EXE.", "Oblicz SHA-256.", "Utwórz Release.", "Dołącz EXE i hash.", "Zaktualizuj manifest."],
        "Publikujesz prestige-dns-benchmark.exe v0.4.0 i jego SHA-256.",
        ["Nie aktualizuj manifestu przed udanym uploadem artefaktu."],
        ["404 przy pobraniu: sprawdź URL assetu i tag Release."],
        "Bezpieczny updater pobiera plik do katalogu tymczasowego, weryfikuje SHA-256, a dopiero potem atomowo podmienia moduł.",
        ["HTTPS.", "SHA-256 wymagany.", "Temp file.", "os.replace po weryfikacji."],
        "Uszkodzony albo podmieniony download nie przechodzi weryfikacji i nie jest instalowany.",
        ["Hash powinien pochodzić z kontrolowanego manifestu lub Release."],
    ),
    Topic(
        "reports", "Raporty", "Raporty i logi",
        "Raporty przechowują wyniki diagnostyki i dokumentują wykonane działania.",
        ["Gdy chcesz zachować wynik.", "Gdy dokumentujesz usługę."],
        ["Wygeneruj raport.", "Zapisz go w reports.", "Otwórz sekcję Raporty.", "Wyszukaj lub posortuj."],
        "Po diagnostyce systemu zapisujesz raport i później porównujesz go z kolejnym.",
        ["Raport może zawierać dane techniczne klienta."],
        ["Brak raportu: sprawdź folder i kliknij Odśwież."],
        "Raport powinien mieć czas, moduł, wersję, parametry wejściowe i czytelny wynik. Surowy traceback nie jest raportem dla klienta.",
        ["Zapisuj wersję modułu.", "Oddziel dane wejściowe od wniosków.", "Nie zapisuj sekretów."],
        "Dwa raporty z różnych dat można porównać tylko wtedy, gdy wiadomo, czym i jak je wykonano.",
        ["Metadane raportu zwiększają jego wartość diagnostyczną."],
    ),
    Topic(
        "logs", "Logi Dashboardu", "Raporty i logi",
        "Logi są technicznym zapisem działania aplikacji i pomagają diagnozować błędy.",
        ["Gdy coś nie startuje.", "Gdy operacja kończy się błędem bez jasnej przyczyny."],
        ["Otwórz Narzędzia systemowe.", "Kliknij Logi.", "Znajdź czas wystąpienia problemu.", "Sprawdź kilka linii przed i po błędzie."],
        "Klikasz Uruchom i nic się nie dzieje. W logu szukasz błędu launch z tej samej minuty.",
        ["Log może zawierać ścieżki lokalne i informacje diagnostyczne."],
        ["Za dużo wpisów: filtruj po czasie i poziomie."],
        "Dobry log używa poziomów INFO, WARNING i ERROR oraz zawiera kontekst operacji.",
        ["Loguj wyjątek techniczny.", "Użytkownikowi pokaż prosty komunikat.", "Nie loguj haseł ani tokenów."],
        "ERROR launch z WinError może wskazać brak pliku lub problem uprawnień.",
        ["Stack trace jest dla diagnostyki, nie do straszenia użytkownika."],
    ),
    Topic(
        "servicecheck", "Checklista serwisowa", "Serwis komputerowy",
        "Stała kolejność diagnostyki zmniejsza ryzyko pominięcia podstawowych rzeczy.",
        ["Przy przyjęciu komputera.", "Przed rozpoczęciem większej naprawy."],
        ["Zapisz objaw klienta.", "Sprawdź backup ważnych danych.", "Zrób migawkę.", "Sprawdź dysk, system, sieć i temperatury zależnie od objawu.", "Zapisz wynik."],
        "Klient mówi, że komputer jest wolny. Najpierw ustalasz kiedy i w jakich sytuacjach, zamiast od razu czyścić system.",
        ["Nie obiecuj przyczyny przed diagnostyką."],
        ["Objaw jest losowy: zbierz więcej danych i spróbuj go odtworzyć."],
        "Profesjonalna diagnostyka rozdziela objaw, hipotezę, test i wynik. Każdy test powinien odpowiadać na konkretne pytanie.",
        ["Jedna hipoteza na raz.", "Zapisuj stan przed zmianą.", "Po naprawie wykonaj retest."],
        "Jeśli wymiana ustawienia nie zmieniła objawu, hipoteza była prawdopodobnie błędna albo niepełna.",
        ["Unikaj przypadkowego zestawu zmian bez możliwości cofnięcia."],
    ),
    Topic(
        "dependencies", "Brak ADB, Nmap, Git lub PowerShell", "Pomoc i FAQ",
        "Niektóre moduły potrzebują zewnętrznych programów.",
        ["Gdy Narzędzia systemowe pokazują Brak.", "Gdy moduł zgłasza missing dependency."],
        ["Sprawdź Narzędzia systemowe.", "Sprawdź pełną ścieżkę.", "Sprawdź PATH.", "Dopiero potem instaluj brakujące narzędzie."],
        "ADB jest w C:\\adb\\adb.exe, więc Dashboard może je znaleźć nawet bez globalnego PATH.",
        ["Nie pobieraj zależności z przypadkowych stron."],
        ["Program istnieje, ale nie jest wykrywany: sprawdź where i PATH."],
        "Wykrywanie zależności powinno sprawdzać zarówno PATH, jak i znane bezpieczne lokalizacje.",
        ["shutil.which dla PATH.", "Fallback do jawnych ścieżek.", "Wyświetl użytkownikowi znalezioną lokalizację."],
        "Dwa różne adb.exe mogą powodować konflikt wersji.",
        ["Pokaż dokładną ścieżkę w Narzędziach systemowych."],
        [("Sprawdź ADB", "where.exe adb"), ("Sprawdź Nmap", "where.exe nmap"), ("Sprawdź Git", "where.exe git")],
    ),
    Topic(
        "modulestart", "Moduł nie uruchamia się", "Pomoc i FAQ",
        "Najpierw sprawdź plik, zależności, uprawnienia i logi.",
        ["Gdy kliknięcie Uruchom nie daje efektu.", "Gdy pojawia się komunikat błędu."],
        ["Sprawdź, czy moduł jest zainstalowany.", "Sprawdź Narzędzia systemowe.", "Sprawdź Logi.", "Spróbuj uruchomić EXE ręcznie z folderu modułu."],
        "Moduł Nmap nie startuje, a Narzędzia systemowe pokazują brak Nmap. Najpierw rozwiązujesz zależność.",
        ["Nie usuwaj logów przed diagnozą."],
        ["WinError 2: zwykle brak pliku lub błędna ścieżka.", "Access denied: uprawnienia lub blokada."],
        "Launcher powinien uruchamiać proces bez shell=True i z właściwym cwd.",
        ["Zweryfikuj executable w manifest.", "Zweryfikuj plik na dysku.", "Sprawdź wyjątek w logu."],
        "Jeśli ręczne uruchomienie EXE również nie działa, problem leży niżej niż Dashboard.",
        ["Rozdziel problem launchera od problemu samego modułu."],
    ),
    Topic(
        "aiassistant", "AI Diagnostic Assistant", "Narzędzia zaawansowane",
        "Asystent AI pomaga porządkować dane diagnostyczne, ale nie powinien zastępować pomiarów i weryfikacji.",
        ["Gdy masz dużo wyników i chcesz uporządkować hipotezy.", "Gdy potrzebujesz prostszego wyjaśnienia raportu."],
        ["Najpierw zbierz fakty.", "Przekaż konkretne dane.", "Oddziel obserwacje od przypuszczeń.", "Weryfikuj sugerowane kroki."],
        "Masz raport sieciowy i log błędu. AI pomaga wskazać, co sprawdzić następnie.",
        ["Nie traktuj sugestii AI jako automatycznego dowodu przyczyny."],
        ["Sprzeczne wyniki: wróć do surowych danych."],
        "Dobra analiza AI powinna jasno odróżniać dane wejściowe, inferencję i rekomendowany test.",
        ["Nie wysyłaj sekretów.", "Anonimizuj dane klienta.", "Weryfikuj komendy przed wykonaniem."],
        "Najlepsza odpowiedź techniczna wskazuje następny test, który może potwierdzić lub obalić hipotezę.",
        ["AI jest narzędziem wspierającym, nie miernikiem."],
    ),
]

TOPIC_BY_KEY: Dict[str, Topic] = {topic.key: topic for topic in TOPICS}

MODULE_TOPIC = {
    "prestige-windows-toolkit": "windows",
    "prestige-system-snapshot": "snapshot",
    "prestige-pc-cleanup": "windows",
    "prestige-internet-diagnostic": "network",
    "prestige-dns-benchmark": "dns",
    "prestige-network-optimizer": "netsnapshot",
    "prestige-nmap-profiles": "nmap",
    "prestige-netradar": "netradar",
    "prestige-lan-radar": "netradar",
    "prestige-network-snapshot": "netsnapshot",
    "prestige-adb-diagnostic": "adb",
    "prestige-android-inspector": "androidinspector",
    "prestige-security-check": "security",
    "prestige-malware-triage": "malware",
    "prestige-file-inspector": "fileinspector",
    "prestige-hash-checker": "hash",
    "prestige-integrity-monitor": "integrity",
    "prestige-folder-watch": "folderwatch",
    "prestige-backup": "backup",
    "prestige-repair-report": "reports",
    "prestige-usb-toolkit": "usb",
    "prestige-termux-setup": "termux",
    "prestige-termux-toolkit": "termux",
    "prestige-ai-diagnostic-assistant": "aiassistant",
}


def body_label(text, size=9, color="#b5cad9", bold=False):
    w = label(text, size, color, bold)
    w.setWordWrap(True)
    return w


def bullet(text):
    return body_label("• " + text, 9, "#b5cad9")


class CommandCard(QFrame):
    def __init__(self, title, command):
        super().__init__()
        self.command = command
        self.setStyleSheet(f"QFrame{{background:#061522;border:1px solid {LINE};border-radius:10px;}}")

        root = QVBoxLayout(self)
        root.setContentsMargins(11, 9, 11, 9)
        root.setSpacing(5)

        head = QHBoxLayout()
        head.addWidget(label(title, 8, TEXT, True))
        head.addStretch()

        copy_btn = QPushButton("Kopiuj")
        copy_btn.clicked.connect(self.copy_command)
        head.addWidget(copy_btn)
        root.addLayout(head)

        code = QLabel(command)
        code.setTextInteractionFlags(Qt.TextSelectableByMouse)
        code.setWordWrap(True)
        code.setStyleSheet(
            "color:#72d7ff;background:#030a12;border:1px solid #123b57;"
            "border-radius:7px;padding:8px;font-family:Consolas;font-size:9pt;"
        )
        root.addWidget(code)

    def copy_command(self):
        QApplication.clipboard().setText(self.command)
        QMessageBox.information(self, "Kopiowanie", "Komenda została skopiowana do schowka.")


class GuidePage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_key = "dashboard"

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 22)
        root.setSpacing(11)

        header = QHBoxLayout()

        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(label("Poradnik", 22, TEXT, True))
        titles.addWidget(
            label(
                "Dwa poziomy: prosto dla każdego oraz osobna warstwa techniczna z interpretacją i komendami.",
                9,
                "#aac0d1",
            )
        )
        header.addLayout(titles)
        header.addStretch()

        counter = QLabel(f"{len(TOPICS)} tematów")
        counter.setStyleSheet(
            f"color:{CYAN};background:#071827;border:1px solid {LINE};"
            "border-radius:9px;padding:7px 10px;font-size:8pt;font-weight:700;"
        )
        header.addWidget(counter)

        root.addLayout(header)

        quick_box = QFrame()
        quick_box.setStyleSheet(
            f"background:#071827;border:1px solid {LINE};border-radius:12px;"
        )
        quick_layout = QVBoxLayout(quick_box)
        quick_layout.setContentsMargins(13, 11, 13, 11)
        quick_layout.addWidget(label("Co chcesz zrobić?", 10, TEXT, True))

        quick = QGridLayout()
        quick.setSpacing(7)

        actions = [
            ("Internet działa wolno", "network"),
            ("Telefon nie jest wykrywany", "adb"),
            ("Podejrzany plik", "malware"),
            ("Windows działa dziwnie", "sfc"),
            ("Sprawdzić SHA-256", "hash"),
            ("Urządzenia w LAN", "netradar"),
            ("Moduł nie startuje", "modulestart"),
            ("Odzyskać dane", "recovery"),
        ]

        for index, (text, key) in enumerate(actions):
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked=False, k=key: self.open_topic(k))
            quick.addWidget(btn, index // 4, index % 4)

        quick_layout.addLayout(quick)
        root.addWidget(quick_box)

        filters = QFrame()
        filters.setStyleSheet(
            f"background:#061522;border:1px solid {LINE};border-radius:11px;"
        )
        fr = QHBoxLayout(filters)
        fr.setContentsMargins(11, 8, 11, 8)
        fr.setSpacing(9)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Szukaj: DNS, ADB, logi, PATH, SMART, Git, backup...")
        self.search.textChanged.connect(self.refresh_topics)
        fr.addWidget(self.search, 1)

        self.category = QComboBox()
        self.category.addItems(["Wszystkie"] + sorted({t.category for t in TOPICS}))
        self.category.currentTextChanged.connect(self.refresh_topics)
        fr.addWidget(self.category)

        root.addWidget(filters)

        body = QHBoxLayout()
        body.setSpacing(10)

        self.list = QListWidget()
        self.list.setFixedWidth(330)
        self.list.setStyleSheet(
            "QListWidget {"
            " background: #061522;"
            " color: #e7f1f8;"
            " border: 1px solid #164b6b;"
            " padding: 6px;"
            " font-size: 9pt;"
            "}"
            "QListWidget::item {"
            " padding: 10px;"
            " margin: 1px;"
            "}"
            "QListWidget::item:selected {"
            " background: #1684ea;"
            " color: #ffffff;"
            "}"
            "QListWidget::item:hover {"
            " background: #0b2843;"
            "}"
        )
        self.list.currentItemChanged.connect(self.list_changed)
        body.addWidget(self.list)

        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.detail = QWidget()
        self.detail_layout = QVBoxLayout(self.detail)
        self.detail_layout.setContentsMargins(4, 0, 4, 0)
        self.detail_layout.setSpacing(10)
        self.detail_scroll.setWidget(self.detail)

        body.addWidget(self.detail_scroll, 1)
        root.addLayout(body, 1)

        self.refresh_topics()
        self.open_topic("dashboard")

    def open_topic_for_module(self, module):
        self.open_topic(MODULE_TOPIC.get(getattr(module, "id", ""), "dashboard"))

    def open_topic(self, key):
        if key not in TOPIC_BY_KEY:
            key = "dashboard"

        self.current_key = key

        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)

        self.category.blockSignals(True)
        self.category.setCurrentText("Wszystkie")
        self.category.blockSignals(False)

        self.refresh_topics()

        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(Qt.UserRole) == key:
                self.list.setCurrentItem(item)
                break

        self.render_topic(key)

    def refresh_topics(self):
        query = self.search.text().strip().lower()
        category = self.category.currentText()

        self.list.blockSignals(True)
        self.list.clear()

        for topic in TOPICS:
            if category != "Wszystkie" and topic.category != category:
                continue

            haystack = " ".join(
                [
                    topic.title,
                    topic.category,
                    topic.summary,
                    " ".join(topic.when),
                    " ".join(topic.basic_steps),
                    " ".join(topic.problems),
                    topic.tech_intro,
                    " ".join(topic.tech_steps),
                    " ".join(topic.interpret),
                ]
            ).lower()

            if query and query not in haystack:
                continue

            item = QListWidgetItem(f"{topic.title}\n{topic.category}")
            item.setData(Qt.UserRole, topic.key)
            self.list.addItem(item)

        self.list.blockSignals(False)

        if self.list.count() == 0:
            self.render_empty()
            return

        preferred = None

        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == self.current_key:
                preferred = self.list.item(i)
                break

        self.list.setCurrentItem(preferred or self.list.item(0))

    def list_changed(self, current, previous):
        if current is None:
            return

        key = current.data(Qt.UserRole)

        if key:
            self.current_key = key
            self.render_topic(key)

    def clear_detail(self):
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

    def section(self, title, items, color=None):
        box = QFrame()
        border = color or LINE
        box.setStyleSheet(
            f"QFrame{{background:{CARD};border:1px solid {border};border-radius:11px;}}"
        )

        layout = QVBoxLayout(box)
        layout.setContentsMargins(13, 11, 13, 11)
        layout.setSpacing(4)
        layout.addWidget(label(title, 10, TEXT, True))

        for item in items:
            layout.addWidget(bullet(item))

        return box

    def numbered_section(self, title, items):
        box = QFrame()
        box.setStyleSheet(
            f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:11px;}}"
        )

        layout = QVBoxLayout(box)
        layout.setContentsMargins(13, 11, 13, 11)
        layout.setSpacing(7)
        layout.addWidget(label(title, 10, TEXT, True))

        for index, step in enumerate(items, 1):
            row = QHBoxLayout()

            num = QLabel(str(index))
            num.setAlignment(Qt.AlignCenter)
            num.setFixedSize(30, 30)
            num.setStyleSheet(
                "background:#0b2237;color:white;border:1px solid #2a6d9a;"
                "border-radius:15px;font-size:10pt;font-weight:800;"
            )

            row.addWidget(num)

            text = body_label(step)
            row.addWidget(text, 1)

            layout.addLayout(row)

        return box

    def render_topic(self, key):
        topic = TOPIC_BY_KEY.get(key)

        if topic is None:
            self.render_empty()
            return

        self.clear_detail()

        hero = QFrame()
        hero.setStyleSheet(
            f"QFrame{{background:#071827;border:1px solid {BLUE};border-radius:12px;}}"
        )

        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(15, 13, 15, 13)
        hero_layout.setSpacing(5)

        top = QHBoxLayout()
        top.addWidget(label(topic.title, 17, TEXT, True))
        top.addStretch()

        badge = QLabel(topic.category)
        badge.setStyleSheet(
            f"color:{CYAN};background:#061522;border:1px solid {CYAN};"
            "border-radius:8px;padding:5px 8px;font-size:8pt;font-weight:700;"
        )
        top.addWidget(badge)

        hero_layout.addLayout(top)
        hero_layout.addWidget(body_label(topic.summary, 9, "#c0d3e1"))

        self.detail_layout.addWidget(hero)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabWidget::pane {"
            " border: 1px solid #164b6b;"
            " background: #04101c;"
            "}"
            "QTabBar::tab {"
            " background: #061522;"
            " color: #9fb6c8;"
            " border: 1px solid #164b6b;"
            " padding: 8px 16px;"
            " margin-right: 4px;"
            "}"
            "QTabBar::tab:selected {"
            " background: #0b2944;"
            " color: #ffffff;"
            " border: 1px solid #1684ea;"
            "}"
            "QTabBar::tab:hover {"
            " background: #0d3558;"
            " color: #ffffff;"
            "}"
        )

        basic = QWidget()
        basic_layout = QVBoxLayout(basic)
        basic_layout.setContentsMargins(10, 10, 10, 10)
        basic_layout.setSpacing(10)

        basic_layout.addWidget(self.section("Kiedy tego użyć?", topic.when))
        basic_layout.addWidget(self.numbered_section("Krok po kroku", topic.basic_steps))

        example = QFrame()
        example.setStyleSheet(
            f"QFrame{{background:#071827;border:1px solid {CYAN};border-radius:11px;}}"
        )
        ex_layout = QVBoxLayout(example)
        ex_layout.setContentsMargins(13, 11, 13, 11)
        ex_layout.addWidget(label("Przykład praktyczny", 10, TEXT, True))
        ex_layout.addWidget(body_label(topic.basic_example, 9, "#c0d3e1"))
        basic_layout.addWidget(example)

        basic_layout.addWidget(self.section("Na co uważać?", topic.watch, YELLOW))
        basic_layout.addWidget(self.section("Najczęstsze problemy", topic.problems))
        basic_layout.addStretch()

        technical = QWidget()
        tech_layout = QVBoxLayout(technical)
        tech_layout.setContentsMargins(10, 10, 10, 10)
        tech_layout.setSpacing(10)

        intro_box = QFrame()
        intro_box.setStyleSheet(
            "QFrame{background:#091522;border:1px solid #315774;border-radius:11px;}"
        )
        intro_layout = QVBoxLayout(intro_box)
        intro_layout.setContentsMargins(13, 11, 13, 11)
        intro_layout.addWidget(label("Jak to działa technicznie", 11, "#79ceff", True))
        intro_layout.addWidget(body_label(topic.tech_intro, 9, "#aac2d3"))
        tech_layout.addWidget(intro_box)

        tech_layout.addWidget(self.numbered_section("Procedura techniczna", topic.tech_steps))

        tech_example = QFrame()
        tech_example.setStyleSheet(
            f"QFrame{{background:#071827;border:1px solid {CYAN};border-radius:11px;}}"
        )
        tex_layout = QVBoxLayout(tech_example)
        tex_layout.setContentsMargins(13, 11, 13, 11)
        tex_layout.addWidget(label("Przykład techniczny", 10, TEXT, True))
        tex_layout.addWidget(body_label(topic.tech_example, 9, "#c0d3e1"))
        tech_layout.addWidget(tech_example)

        if topic.commands:
            command_box = QFrame()
            command_box.setStyleSheet(
                f"QFrame{{background:{CARD};border:1px solid {LINE};border-radius:11px;}}"
            )
            command_layout = QVBoxLayout(command_box)
            command_layout.setContentsMargins(13, 11, 13, 11)
            command_layout.setSpacing(7)
            command_layout.addWidget(label("Komendy", 10, TEXT, True))

            for title, command in topic.commands:
                command_layout.addWidget(CommandCard(title, command))

            tech_layout.addWidget(command_box)

        tech_layout.addWidget(self.section("Jak interpretować wynik?", topic.interpret, "#315774"))
        tech_layout.addStretch()

        tabs.addTab(basic, "Dla każdego")
        tabs.addTab(technical, "Technicznie")

        self.detail_layout.addWidget(tabs)
        self.detail_layout.addStretch()

        self.detail_scroll.verticalScrollBar().setValue(0)

    def render_empty(self):
        self.clear_detail()

        empty = QLabel("Brak tematów pasujących do wyszukiwania.")
        empty.setAlignment(Qt.AlignCenter)
        empty.setStyleSheet(
            f"color:#a9bfd0;background:#061522;border:1px dashed {LINE};"
            "border-radius:12px;padding:35px;font-size:10pt;"
        )

        self.detail_layout.addWidget(empty)
        self.detail_layout.addStretch()
