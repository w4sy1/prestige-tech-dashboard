from __future__ import annotations

import copy
import dataclasses
import re

from . import guide_page as _base


EXTRA_TOPICS = [
    {
        "title": "BSOD - niebieski ekran Windows",
        "category": "Windows",
        "basic": "Gdy komputer pokazuje niebieski ekran, zapisz kod błędu i moment, w którym problem się pojawia. Nie zaczynaj od losowego instalowania sterowników.",
        "technical": "Sprawdź minidumpy, Podgląd zdarzeń, sterowniki z ostatnich zmian, RAM, dysk i temperatury. Kody typu WHEA mogą wskazywać sprzęt, a DRIVER_* częściej sterownik.",
        "tags": ["bsod", "blue screen", "minidump", "windows"],
    },
    {
        "title": "SFC - sprawdzanie plików systemowych",
        "category": "Windows",
        "basic": "SFC sprawdza chronione pliki Windows i może naprawić ich uszkodzone kopie.",
        "technical": "Uruchom terminal jako administrator i użyj sfc /scannow. Jeśli magazyn składników jest uszkodzony, wcześniej lub później użyj DISM.",
        "tags": ["sfc", "scannow", "windows", "naprawa"],
    },
    {
        "title": "DISM - naprawa obrazu Windows",
        "category": "Windows",
        "basic": "DISM pomaga naprawić składniki Windows, z których korzysta między innymi SFC.",
        "technical": "Typowa kolejność to DISM /Online /Cleanup-Image /ScanHealth, a następnie /RestoreHealth. Po zakończeniu ponownie uruchom SFC.",
        "tags": ["dism", "restorehealth", "windows"],
    },
    {
        "title": "CHKDSK - kiedy używać",
        "category": "Windows",
        "basic": "CHKDSK sprawdza system plików. Nie jest narzędziem do naprawiania fizycznie uszkodzonego dysku.",
        "technical": "Przy podejrzeniu awarii nośnika najpierw zabezpiecz dane. Parametry /f i /r mogą mocno obciążyć uszkodzony dysk.",
        "tags": ["chkdsk", "dysk", "ntfs"],
    },
    {
        "title": "Autostart Windows - co można wyłączyć",
        "category": "Windows",
        "basic": "Wyłączaj z autostartu programy, których nie potrzebujesz od razu po uruchomieniu systemu.",
        "technical": "Sprawdź Menedżer zadań, foldery Startup, harmonogram zadań i wpisy Run. Nie wyłączaj sterowników i usług bezpieczeństwa bez identyfikacji.",
        "tags": ["autostart", "startup", "wydajność"],
    },
    {
        "title": "Plik stronicowania - pagefile",
        "category": "Windows",
        "basic": "Plik stronicowania jest zapasem pamięci dla Windows. Wyłączanie go tylko dlatego, że masz dużo RAM, zwykle nie daje korzyści.",
        "technical": "Windows wykorzystuje pagefile także do części zrzutów pamięci. Najbezpieczniej pozostawić zarządzanie systemowe, chyba że masz konkretny powód diagnostyczny.",
        "tags": ["pagefile", "ram", "virtual memory"],
    },
    {
        "title": "UEFI a Legacy BIOS",
        "category": "Sprzęt",
        "basic": "UEFI to nowszy sposób uruchamiania komputera. Nowe instalacje Windows powinny zwykle działać w UEFI.",
        "technical": "UEFI współpracuje z GPT i Secure Boot. Legacy/CSM wiąże się częściej z MBR i starszymi systemami.",
        "tags": ["uefi", "legacy", "bios", "gpt", "mbr"],
    },
    {
        "title": "Secure Boot i TPM",
        "category": "Sprzęt",
        "basic": "Secure Boot kontroluje zaufany start systemu, a TPM przechowuje klucze i wspiera funkcje bezpieczeństwa.",
        "technical": "Przed zmianami sprawdź BitLocker. Zmiana TPM, Secure Boot lub trybu startu bez przygotowania może uruchomić żądanie klucza odzyskiwania.",
        "tags": ["secure boot", "tpm", "bitlocker"],
    },
    {
        "title": "RAM - single channel i dual channel",
        "category": "Sprzęt",
        "basic": "Dwie odpowiednio dobrane kości RAM mogą działać równolegle i zwiększyć przepustowość pamięci.",
        "technical": "Dual channel zależy od kontrolera, obsadzenia właściwych slotów i zgodności modułów. Sprawdzaj instrukcję płyty głównej.",
        "tags": ["ram", "dual channel", "single channel"],
    },
    {
        "title": "RAM - XMP i EXPO",
        "category": "Sprzęt",
        "basic": "XMP i EXPO to profile ustawień pamięci, które pozwalają uruchomić RAM z parametrami zapisanymi przez producenta.",
        "technical": "Profil jest formą OC pamięci. Jeśli pojawiają się błędy, testuj RAM po wyłączeniu profilu i sprawdź QVL płyty.",
        "tags": ["xmp", "expo", "ram", "bios"],
    },
    {
        "title": "VRAM - pamięć karty graficznej",
        "category": "Sprzęt",
        "basic": "VRAM przechowuje dane używane przez GPU, między innymi tekstury i bufory obrazu.",
        "technical": "Brak VRAM może powodować doczytywanie danych i spadki wydajności. Wartość raportowana przez stare API Windows bywa niedokładna dla nowoczesnych GPU.",
        "tags": ["vram", "gpu", "grafika"],
    },
    {
        "title": "Sterownik GPU - czysta instalacja",
        "category": "Sprzęt",
        "basic": "Gdy po aktualizacji sterownika pojawiają się artefakty lub crashe, warto wykonać kontrolowaną reinstalację.",
        "technical": "Najpierw sprawdź wersję i objawy. DDU stosuj w uzasadnionych przypadkach, najlepiej offline, a potem zainstaluj właściwy sterownik producenta.",
        "tags": ["gpu", "driver", "ddu", "nvidia", "amd", "intel"],
    },
    {
        "title": "Temperatury CPU i GPU",
        "category": "Sprzęt",
        "basic": "Temperatury mają sens tylko razem z obciążeniem, modelem sprzętu i limitem producenta.",
        "technical": "Patrz na temperaturę, pobór mocy, zegary i throttling jednocześnie. Krótki pik nie jest tym samym co stałe przegrzewanie.",
        "tags": ["temperatura", "cpu", "gpu", "throttling"],
    },
    {
        "title": "SMART dysku - jak czytać",
        "category": "Dyski",
        "basic": "SMART pokazuje informacje diagnostyczne nośnika. Zielony status nie jest gwarancją, że dysk nie ulegnie awarii.",
        "technical": "Dla HDD zwracaj uwagę m.in. na realokowane i oczekujące sektory. Dla SSD/NVMe liczą się też zużycie, media errors i spare.",
        "tags": ["smart", "ssd", "hdd", "nvme"],
    },
    {
        "title": "SSD, NVMe i HDD - różnice",
        "category": "Dyski",
        "basic": "HDD jest mechaniczny, SSD nie ma ruchomych części, a NVMe zwykle komunikuje się przez PCIe.",
        "technical": "Nie każdy dysk M.2 jest NVMe. M.2 opisuje format, a SATA/NVMe sposób komunikacji.",
        "tags": ["ssd", "nvme", "hdd", "m2"],
    },
    {
        "title": "Dysk prawie pełny - co sprawdzić",
        "category": "Dyski",
        "basic": "Najpierw ustal, co zajmuje miejsce. Nie kasuj losowo katalogów Windows.",
        "technical": "Sprawdź profile użytkowników, cache, pliki tymczasowe, hibernację, Windows Update, punkty przywracania i duże pliki aplikacji.",
        "tags": ["dysk", "miejsce", "cleanup"],
    },
    {
        "title": "Rozdzielczość, Hz i skalowanie ekranu",
        "category": "Sprzęt",
        "basic": "Rozdzielczość określa liczbę pikseli, Hz częstotliwość odświeżania, a skalowanie wielkość elementów interfejsu.",
        "technical": "Sprawdź tryb aktywnego sygnału, możliwości przewodu i portu. 4K 120 Hz może wymagać odpowiedniej wersji HDMI/DisplayPort.",
        "tags": ["monitor", "hz", "rozdzielczość", "skalowanie"],
    },
    {
        "title": "Bateria laptopa - kondycja",
        "category": "Sprzęt",
        "basic": "Spadek pojemności baterii z czasem jest normalny. Liczy się różnica między pojemnością projektową a pełnym naładowaniem.",
        "technical": "W Windows możesz użyć powercfg /batteryreport. Porównaj Design Capacity, Full Charge Capacity i liczbę cykli, jeśli jest raportowana.",
        "tags": ["bateria", "laptop", "batteryreport"],
    },
    {
        "title": "DHCP - skąd komputer ma adres IP",
        "category": "Sieć",
        "basic": "DHCP automatycznie przydziela urządzeniu adres IP, bramę i często DNS.",
        "technical": "Adres 169.254.x.x zwykle oznacza brak odpowiedzi DHCP. Sprawdź dzierżawę, VLAN, serwer DHCP i łączność warstwy 2.",
        "tags": ["dhcp", "ip", "169.254"],
    },
    {
        "title": "DNS - internet działa, strony nie",
        "category": "Sieć",
        "basic": "DNS zamienia nazwy stron na adresy IP. Możesz mieć internet, ale problem z DNS.",
        "technical": "Porównaj ping do IP z zapytaniem o nazwę. Sprawdź resolver, cache DNS, DoH i konfigurację routera.",
        "tags": ["dns", "resolver", "internet"],
    },
    {
        "title": "CGNAT - dlaczego przekierowanie portów nie działa",
        "category": "Sieć",
        "basic": "Przy CGNAT kilku klientów operatora współdzieli publiczny adres IPv4.",
        "technical": "Porównaj WAN IP routera z publicznym adresem widocznym w internecie. Prywatny lub współdzielony WAN może uniemożliwiać klasyczny port forwarding.",
        "tags": ["cgnat", "nat", "port forwarding"],
    },
    {
        "title": "MTU - dziwne problemy z częścią stron",
        "category": "Sieć",
        "basic": "MTU określa maksymalny rozmiar pakietu bez fragmentacji na danym łączu.",
        "technical": "Błędne MTU lub blokada ICMP może powodować PMTUD black hole. Testuj ostrożnie pingiem z DF i różnymi rozmiarami.",
        "tags": ["mtu", "pmtu", "fragmentacja"],
    },
    {
        "title": "Utrata pakietów i wysoki ping",
        "category": "Sieć",
        "basic": "Pojedynczy wysoki ping nie oznacza awarii. Liczy się powtarzalność i miejsce, w którym pojawia się problem.",
        "technical": "Porównaj LAN, bramę, pierwszy hop operatora i dalszą trasę. Wi-Fi testuj osobno od połączenia kablowego.",
        "tags": ["ping", "packet loss", "latency"],
    },
    {
        "title": "Wi-Fi 2,4 GHz, 5 GHz i 6 GHz",
        "category": "Sieć",
        "basic": "2,4 GHz zwykle ma większy zasięg, a wyższe pasma oferują więcej przepustowości przy krótszym zasięgu.",
        "technical": "Sprawdź kanał, szerokość kanału, zakłócenia, standard 802.11 i możliwości klienta. Więcej MHz nie zawsze oznacza stabilniej.",
        "tags": ["wifi", "2.4", "5ghz", "6ghz"],
    },
    {
        "title": "Prędkość linku a prędkość internetu",
        "category": "Sieć",
        "basic": "Prędkość linku karty sieciowej nie jest tym samym co realny transfer z internetu.",
        "technical": "Link speed pokazuje negocjację warstwy lokalnej. Realny throughput ogranicza router, ISP, serwer, Wi-Fi i narzut protokołów.",
        "tags": ["link speed", "ethernet", "wifi", "speedtest"],
    },
    {
        "title": "IPv4 i IPv6 - podstawy",
        "category": "Sieć",
        "basic": "IPv4 i IPv6 to dwa protokoły adresacji. Współczesna sieć może używać obu jednocześnie.",
        "technical": "Nie wyłączaj IPv6 jako uniwersalnej naprawy. Diagnozuj DNS, routing i preferencję stosu zamiast maskować problem.",
        "tags": ["ipv4", "ipv6", "dual stack"],
    },
    {
        "title": "ADB unauthorized",
        "category": "Android",
        "basic": "Status unauthorized oznacza, że komputer widzi telefon, ale telefon nie zaakceptował klucza ADB.",
        "technical": "Odblokuj telefon, zaakceptuj fingerprint RSA, ewentualnie odwołaj autoryzacje debugowania i uruchom ponownie serwer ADB.",
        "tags": ["adb", "unauthorized", "android"],
    },
    {
        "title": "ADB offline",
        "category": "Android",
        "basic": "Status offline oznacza, że urządzenie jest wykryte, ale sesja ADB nie działa prawidłowo.",
        "technical": "Sprawdź przewód, sterownik, restart adb kill-server/start-server, port USB i konflikt kilku wersji adb w PATH.",
        "tags": ["adb", "offline", "android"],
    },
    {
        "title": "Fastboot - czym różni się od ADB",
        "category": "Android",
        "basic": "ADB działa z uruchomionym systemem lub recovery obsługującym ADB, a fastboot pracuje z bootloaderem na wspieranych urządzeniach.",
        "technical": "Nie każde urządzenie używa standardowego fastboot. Operacje odblokowania bootloadera mogą kasować dane i zmieniać stan bezpieczeństwa.",
        "tags": ["fastboot", "adb", "bootloader"],
    },
    {
        "title": "APK - instalacja przez ADB",
        "category": "Android",
        "basic": "ADB może instalować APK na własnym urządzeniu testowym bez wysyłania go do sklepu.",
        "technical": "Użyj adb install plik.apk. Konflikt podpisu lub niższy versionCode może wymagać innej komendy albo usunięcia poprzedniej wersji.",
        "tags": ["apk", "adb install", "android"],
    },
    {
        "title": "SHA-256 - po co sprawdzać plik",
        "category": "Bezpieczeństwo",
        "basic": "SHA-256 pozwala porównać, czy pobrany plik jest identyczny z plikiem opublikowanym przez autora.",
        "technical": "Hash potwierdza integralność względem zaufanej wartości referencyjnej. Sam hash nie mówi, czy program jest bezpieczny.",
        "tags": ["sha256", "hash", "integralność"],
    },
    {
        "title": "2FA - aplikacja czy SMS",
        "category": "Bezpieczeństwo",
        "basic": "Drugi składnik logowania znacząco utrudnia przejęcie konta po wycieku hasła.",
        "technical": "TOTP lub klucz sprzętowy jest zwykle odporniejszy na przejęcie numeru telefonu niż SMS. Zachowaj kody odzyskiwania offline.",
        "tags": ["2fa", "totp", "sms", "security key"],
    },
    {
        "title": "Phishing - szybka ocena wiadomości",
        "category": "Bezpieczeństwo",
        "basic": "Nie oceniaj wiadomości tylko po wyglądzie. Sprawdź nadawcę, domenę, link i presję czasu.",
        "technical": "Analizuj pełne nagłówki, SPF/DKIM/DMARC, domenę docelową i ewentualne przekierowania bez logowania się przez podejrzany link.",
        "tags": ["phishing", "email", "domena"],
    },
    {
        "title": "Backup 3-2-1",
        "category": "Bezpieczeństwo",
        "basic": "Zasada 3-2-1: trzy kopie danych, na dwóch różnych typach nośników, jedna poza głównym miejscem.",
        "technical": "Kopia podłączona cały czas nie chroni dobrze przed ransomware. Testuj odtwarzanie, nie tylko samo tworzenie backupu.",
        "tags": ["backup", "3-2-1", "ransomware"],
    },
    {
        "title": "Ransomware - pierwsze kroki",
        "category": "Bezpieczeństwo",
        "basic": "Jeśli pliki nagle zmieniają rozszerzenia lub stają się zaszyfrowane, ogranicz dalsze zapisy i odłącz zasoby sieciowe.",
        "technical": "Izoluj host, zabezpiecz logi i próbki, ustal zakres, nie nadpisuj danych. Przy ważnych danych pracuj na kopii lub obrazie nośnika.",
        "tags": ["ransomware", "malware", "incident"],
    },
    {
        "title": "Git fetch, pull i push",
        "category": "Git",
        "basic": "fetch pobiera informacje z remote, pull pobiera i integruje zmiany, a push wysyła lokalne commity.",
        "technical": "Przed pull warto rozumieć, czy projekt używa merge czy rebase. Push może zostać odrzucony, gdy remote ma nowszą historię.",
        "tags": ["git", "fetch", "pull", "push"],
    },
    {
        "title": "Git - konflikt przy merge lub rebase",
        "category": "Git",
        "basic": "Konflikt oznacza, że Git nie potrafi sam zdecydować, którą zmianę zachować.",
        "technical": "Sprawdź pliki konfliktowe, wybierz poprawną treść, git add konkretne pliki i kontynuuj merge/rebase. Nie używaj force push bez zrozumienia skutku.",
        "tags": ["git", "conflict", "merge", "rebase"],
    },
    {
        "title": "Dashboard - moduł nie startuje",
        "category": "Dashboard",
        "basic": "Sprawdź, czy moduł jest zainstalowany, czy plik EXE istnieje i czy Windows nie blokuje jego uruchomienia.",
        "technical": "Sprawdź log Dashboardu, ścieżkę modułu, uprawnienia, zależności systemowe i wynik uruchomienia EXE bezpośrednio.",
        "tags": ["dashboard", "module", "exe"],
    },
    {
        "title": "Dashboard - tryb Portable",
        "category": "Dashboard",
        "basic": "Portable pozwala uruchomić lokalny plik modułu bez kopiowania go do standardowego katalogu modułów.",
        "technical": "Tryb jest przydatny do testów i pracy serwisowej. Pamiętaj, że lokalna wersja może różnić się od wersji zainstalowanej.",
        "tags": ["dashboard", "portable", "module"],
    },
    {
        "title": "Dashboard - gdzie są logi",
        "category": "Dashboard",
        "basic": "Log pomaga ustalić, co wydarzyło się przed błędem programu.",
        "technical": "Przy zgłoszeniu zapisuj czas błędu, wersję Dashboardu, nazwę modułu i odpowiedni fragment logu bez sekretów użytkownika.",
        "tags": ["dashboard", "log", "diagnostyka"],
    },
]


def _slug(text):
    value = text.lower()
    value = re.sub(r"[^a-z0-9ąćęłńóśźż]+", "-", value)
    return value.strip("-")


def _flatten_text(value, depth=0):
    if depth > 5:
        return ""

    if isinstance(value, dict):
        return " ".join(
            _flatten_text(k, depth + 1) + " " + _flatten_text(v, depth + 1)
            for k, v in value.items()
        )

    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_text(x, depth + 1) for x in value)

    if dataclasses.is_dataclass(value):
        return _flatten_text(dataclasses.asdict(value), depth + 1)

    if hasattr(value, "__dict__"):
        return _flatten_text(vars(value), depth + 1)

    return str(value)


def _container_score(name, value):
    if isinstance(value, dict):
        items = list(value.values())
        count = len(value)
    elif isinstance(value, (list, tuple)):
        items = list(value)
        count = len(value)
    else:
        return -1

    if count < 20 or count > 120 or not items:
        return -1

    text = _flatten_text(items[:60]).lower()
    score = 0

    for marker in (
        "internet działa wolno",
        "telefon nie jest wykrywany",
        "sha-256",
        "urządzenia w lan",
        "odzyskać dane",
        "ip, brama",
    ):
        if marker in text:
            score += 20

    if 35 <= count <= 55:
        score += 30

    if "topic" in name.lower() or "guide" in name.lower() or "help" in name.lower():
        score += 10

    return score


def _find_topic_container():
    ranked = []

    for name, value in vars(_base).items():
        score = _container_score(name, value)
        if score > 0:
            ranked.append((score, name, value))

    if not ranked:
        return None, None

    ranked.sort(key=lambda x: x[0], reverse=True)
    _, name, value = ranked[0]
    return name, value


def _category_values(container):
    values = set()

    items = list(container.values()) if isinstance(container, dict) else list(container)

    for item in items[:80]:
        if not isinstance(item, dict):
            continue

        for key, value in item.items():
            if str(key).lower() in ("category", "group", "section", "kategoria"):
                if isinstance(value, str) and value.strip():
                    values.add(value.strip())

    return sorted(values)


def _best_category(desired, available):
    if not available:
        return desired

    wanted = desired.lower()

    synonyms = {
        "windows": ("windows", "system"),
        "sprzęt": ("sprzęt", "sprzet", "hardware", "komputer"),
        "dyski": ("dysk", "dane", "storage", "odzysk"),
        "sieć": ("sieć", "siec", "network", "internet"),
        "android": ("android", "adb", "telefon"),
        "bezpieczeństwo": ("bezpieczeń", "bezpieczen", "security", "cyber"),
        "git": ("git", "github", "program"),
        "dashboard": ("dashboard", "prestige", "program"),
    }

    probes = synonyms.get(wanted, (wanted,))

    for item in available:
        lower = item.lower()
        if any(probe in lower for probe in probes):
            return item

    return available[0]


def _fill_mapping(template, topic, available_categories):
    result = copy.deepcopy(template)
    desired_category = _best_category(topic["category"], available_categories)

    def value_for(key, old):
        low = str(key).strip().lower().replace(" ", "_")

        if low in ("id", "slug", "key", "topic_id"):
            return _slug(topic["title"])

        if low in (
            "title",
            "name",
            "question",
            "label",
            "topic",
            "temat",
            "problem",
        ):
            return topic["title"]

        if low in ("category", "group", "section", "kategoria"):
            return desired_category

        if low in (
            "basic",
            "simple",
            "beginner",
            "easy",
            "dla_kazdego",
            "for_everyone",
            "general",
            "answer",
            "description",
            "summary",
        ):
            return topic["basic"]

        if low in (
            "technical",
            "tech",
            "advanced",
            "expert",
            "details",
            "technicznie",
            "dla_technicznych",
        ):
            return topic["technical"]

        if low in ("tags", "keywords", "search", "search_terms"):
            if isinstance(old, str):
                return ", ".join(topic["tags"])
            if isinstance(old, tuple):
                return tuple(topic["tags"])
            return list(topic["tags"])

        if low in ("content", "texts", "body") and isinstance(old, dict):
            nested = copy.deepcopy(old)
            for nested_key, nested_old in list(nested.items()):
                nested[nested_key] = value_for(nested_key, nested_old)
            return nested

        if low in ("content", "body") and isinstance(old, str):
            return topic["basic"] + "\n\nTechnicznie:\n" + topic["technical"]

        return old

    for key in list(result.keys()):
        result[key] = value_for(key, result[key])

    # Add common keys when the template is unusually sparse.
    lower_keys = {str(k).lower() for k in result}
    if not lower_keys.intersection({"title", "name", "question", "label", "topic", "temat"}):
        result["title"] = topic["title"]
    if not lower_keys.intersection({"basic", "simple", "beginner", "dla_kazdego", "for_everyone"}):
        result["basic"] = topic["basic"]
    if not lower_keys.intersection({"technical", "tech", "advanced", "technicznie"}):
        result["technical"] = topic["technical"]

    return result


def _make_like(template, topic, available_categories):
    if isinstance(template, dict):
        return _fill_mapping(template, topic, available_categories)

    if dataclasses.is_dataclass(template):
        current = dataclasses.asdict(template)
        filled = _fill_mapping(current, topic, available_categories)
        allowed = {field.name for field in dataclasses.fields(template)}
        kwargs = {key: value for key, value in filled.items() if key in allowed}
        return dataclasses.replace(template, **kwargs)

    if hasattr(template, "_fields") and hasattr(template, "_replace"):
        mapping = {name: getattr(template, name) for name in template._fields}
        filled = _fill_mapping(mapping, topic, available_categories)
        return template._replace(
            **{key: value for key, value in filled.items() if key in template._fields}
        )

    clone = copy.copy(template)
    if hasattr(clone, "__dict__"):
        mapping = _fill_mapping(vars(clone), topic, available_categories)
        for key, value in mapping.items():
            try:
                setattr(clone, key, value)
            except Exception:
                pass
        return clone

    raise TypeError("Nieobsługiwany format tematu Poradnika.")


def _patch_defaults(old_container, new_container):
    init = getattr(_base.GuidePage, "__init__", None)
    if init is None:
        return

    defaults = getattr(init, "__defaults__", None)
    if defaults:
        init.__defaults__ = tuple(
            new_container if value is old_container else value
            for value in defaults
        )

    kwdefaults = getattr(init, "__kwdefaults__", None)
    if kwdefaults:
        init.__kwdefaults__ = {
            key: (new_container if value is old_container else value)
            for key, value in kwdefaults.items()
        }

    for key, value in list(vars(_base.GuidePage).items()):
        if value is old_container:
            try:
                setattr(_base.GuidePage, key, new_container)
            except Exception:
                pass


def extend_topics():
    name, container = _find_topic_container()

    if container is None:
        raise RuntimeError(
            "Nie znaleziono kolekcji tematów starego Poradnika. "
            "Nie zmieniono jego wyglądu ani danych."
        )

    existing_text = _flatten_text(container).lower()
    available_categories = _category_values(container)

    if isinstance(container, dict):
        values = list(container.values())
    else:
        values = list(container)

    if not values:
        raise RuntimeError("Kolekcja tematów Poradnika jest pusta.")

    template = values[0]
    additions = []

    for topic in EXTRA_TOPICS:
        if topic["title"].lower() in existing_text:
            continue
        additions.append(
            _make_like(template, topic, available_categories)
        )

    if isinstance(container, list):
        container.extend(additions)
        new_container = container

    elif isinstance(container, tuple):
        new_container = container + tuple(additions)
        setattr(_base, name, new_container)
        _patch_defaults(container, new_container)

    elif isinstance(container, dict):
        new_container = container
        for topic, item in zip(
            [t for t in EXTRA_TOPICS if t["title"].lower() not in existing_text],
            additions,
        ):
            new_container[_slug(topic["title"])] = item

    else:
        raise RuntimeError("Nieobsługiwany kontener tematów.")

    return len(additions), name, new_container


ADDED_TOPICS, TOPIC_CONTAINER_NAME, TOPIC_CONTAINER = extend_topics()

GuidePage = _base.GuidePage