from __future__ import annotations

import base64
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime


def _safe_number(value, default=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return default


def _first(value, default=None):
    if isinstance(value, list):
        return value[0] if value else default
    return value if value is not None else default


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def format_bytes(value):
    size = float(_safe_number(value))
    units = ("B", "KB", "MB", "GB", "TB")

    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit in ("B", "KB"):
                return f"{size:.0f} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{value} B"


def format_speed_bps(value):
    speed = float(_safe_number(value))
    if speed <= 0:
        return "brak danych"

    units = ("b/s", "Kb/s", "Mb/s", "Gb/s", "Tb/s")
    for unit in units:
        if speed < 1000.0 or unit == units[-1]:
            if unit in ("b/s", "Kb/s"):
                return f"{speed:.0f} {unit}"
            return f"{speed:.1f} {unit}"
        speed /= 1000.0

    return "brak danych"


def _run_powershell_json(script: str, timeout=25):
    exe = shutil.which("pwsh") or shutil.which("powershell")
    if not exe:
        raise FileNotFoundError("Nie znaleziono PowerShell.")

    preamble = (
        "$ErrorActionPreference='SilentlyContinue';"
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
    )

    encoded = base64.b64encode(
        (preamble + script).encode("utf-16le")
    ).decode("ascii")

    result = subprocess.run(
        [
            exe,
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            encoded,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )

    if result.returncode != 0:
        raise RuntimeError(
            (result.stderr or result.stdout or "PowerShell error").strip()
        )

    text = (result.stdout or "").lstrip("\ufeff").strip()
    if not text:
        return {}

    return json.loads(text)


_POWERSHELL_SNAPSHOT = r'''
$os = Get-CimInstance Win32_OperatingSystem
$cs = Get-CimInstance Win32_ComputerSystem
$cpu = @(Get-CimInstance Win32_Processor)
$ram = @(Get-CimInstance Win32_PhysicalMemory)
$gpu = @(Get-CimInstance Win32_VideoController)
$board = Get-CimInstance Win32_BaseBoard
$bios = Get-CimInstance Win32_BIOS
$diskDrive = @(Get-CimInstance Win32_DiskDrive)
$logical = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3")
$physical = @()
try {
    $physical = @(Get-PhysicalDisk | Select-Object FriendlyName,MediaType,BusType,Size,HealthStatus,OperationalStatus)
} catch {}
$netCfg = @(Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True")
$netAdapter = @(Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.NetEnabled -eq $true })
$battery = @(Get-CimInstance Win32_Battery)

$network = @()
foreach($cfg in $netCfg) {
    $adapter = $netAdapter | Where-Object { $_.InterfaceIndex -eq $cfg.InterfaceIndex } | Select-Object -First 1
    $network += [ordered]@{
        Description = $cfg.Description
        InterfaceIndex = $cfg.InterfaceIndex
        IPAddress = @($cfg.IPAddress)
        DefaultIPGateway = @($cfg.DefaultIPGateway)
        DNSServerSearchOrder = @($cfg.DNSServerSearchOrder)
        MACAddress = $cfg.MACAddress
        DHCPEnabled = $cfg.DHCPEnabled
        Speed = if($adapter) { $adapter.Speed } else { $null }
        AdapterName = if($adapter) { $adapter.Name } else { $null }
    }
}

$ramItems = @()
foreach($item in $ram) {
    $ramItems += [ordered]@{
        Manufacturer = $item.Manufacturer
        PartNumber = $item.PartNumber
        Capacity = $item.Capacity
        Speed = $item.Speed
        ConfiguredClockSpeed = $item.ConfiguredClockSpeed
        DeviceLocator = $item.DeviceLocator
        BankLabel = $item.BankLabel
    }
}

$gpuItems = @()
foreach($item in $gpu) {
    $gpuItems += [ordered]@{
        Name = $item.Name
        AdapterRAM = $item.AdapterRAM
        DriverVersion = $item.DriverVersion
        VideoProcessor = $item.VideoProcessor
        CurrentHorizontalResolution = $item.CurrentHorizontalResolution
        CurrentVerticalResolution = $item.CurrentVerticalResolution
        CurrentRefreshRate = $item.CurrentRefreshRate
    }
}

$diskItems = @()
foreach($item in $diskDrive) {
    $diskItems += [ordered]@{
        Model = $item.Model
        MediaType = $item.MediaType
        InterfaceType = $item.InterfaceType
        Size = $item.Size
        SerialNumber = $item.SerialNumber
        Status = $item.Status
    }
}

$logicalItems = @()
foreach($item in $logical) {
    $logicalItems += [ordered]@{
        DeviceID = $item.DeviceID
        VolumeName = $item.VolumeName
        FileSystem = $item.FileSystem
        Size = $item.Size
        FreeSpace = $item.FreeSpace
    }
}

$physicalItems = @()
foreach($item in $physical) {
    $physicalItems += [ordered]@{
        FriendlyName = $item.FriendlyName
        MediaType = [string]$item.MediaType
        BusType = [string]$item.BusType
        Size = $item.Size
        HealthStatus = [string]$item.HealthStatus
        OperationalStatus = @($item.OperationalStatus | ForEach-Object { [string]$_ })
    }
}

$cpuItems = @()
foreach($item in $cpu) {
    $cpuItems += [ordered]@{
        Name = $item.Name
        NumberOfCores = $item.NumberOfCores
        NumberOfLogicalProcessors = $item.NumberOfLogicalProcessors
        MaxClockSpeed = $item.MaxClockSpeed
        CurrentClockSpeed = $item.CurrentClockSpeed
    }
}

$batteryItems = @()
foreach($item in $battery) {
    $batteryItems += [ordered]@{
        Name = $item.Name
        EstimatedChargeRemaining = $item.EstimatedChargeRemaining
        EstimatedRunTime = $item.EstimatedRunTime
        Status = $item.Status
    }
}

$result = [ordered]@{
    collected_at = (Get-Date).ToString("o")
    os = [ordered]@{
        Caption = $os.Caption
        Version = $os.Version
        BuildNumber = $os.BuildNumber
        OSArchitecture = $os.OSArchitecture
        LastBootUpTime = if($os.LastBootUpTime) { $os.LastBootUpTime.ToString("o") } else { $null }
        TotalVisibleMemorySize = $os.TotalVisibleMemorySize
        FreePhysicalMemory = $os.FreePhysicalMemory
    }
    computer = [ordered]@{
        Manufacturer = $cs.Manufacturer
        Model = $cs.Model
        TotalPhysicalMemory = $cs.TotalPhysicalMemory
    }
    cpu = $cpuItems
    ram = $ramItems
    gpu = $gpuItems
    motherboard = [ordered]@{
        Manufacturer = $board.Manufacturer
        Product = $board.Product
        SerialNumber = $board.SerialNumber
    }
    bios = [ordered]@{
        Manufacturer = $bios.Manufacturer
        SMBIOSBIOSVersion = $bios.SMBIOSBIOSVersion
        ReleaseDate = if($bios.ReleaseDate) { $bios.ReleaseDate.ToString("o") } else { $null }
    }
    disk_drives = $diskItems
    logical_disks = $logicalItems
    physical_disks = $physicalItems
    network = $network
    battery = $batteryItems
}

$result | ConvertTo-Json -Depth 8 -Compress
'''


def collect_snapshot():
    if os.environ.get("PRESTIGE_SKIP_SYSTEM_PROBE") == "1":
        return {
            "collected_at": datetime.now().isoformat(),
            "os": {
                "Caption": platform.platform(),
                "Version": platform.version(),
                "BuildNumber": "",
                "OSArchitecture": platform.machine(),
            },
            "computer": {},
            "cpu": [],
            "ram": [],
            "gpu": [],
            "motherboard": {},
            "bios": {},
            "disk_drives": [],
            "logical_disks": [],
            "physical_disks": [],
            "network": [],
            "battery": [],
            "_probe_skipped": True,
        }

    if os.name != "nt":
        return {
            "collected_at": datetime.now().isoformat(),
            "os": {
                "Caption": platform.system(),
                "Version": platform.version(),
                "BuildNumber": platform.release(),
                "OSArchitecture": platform.machine(),
            },
            "computer": {},
            "cpu": [],
            "ram": [],
            "gpu": [],
            "motherboard": {},
            "bios": {},
            "disk_drives": [],
            "logical_disks": [],
            "physical_disks": [],
            "network": [],
            "battery": [],
        }

    return _run_powershell_json(_POWERSHELL_SNAPSHOT)


def _date_only(value):
    if not value:
        return "brak danych"
    return str(value)[:10]


def _clean(value, default="brak danych"):
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def build_summary(snapshot, display=None):
    os_data = snapshot.get("os") or {}
    computer = snapshot.get("computer") or {}

    cpus = _as_list(snapshot.get("cpu"))
    cpu = _first(cpus, {}) or {}

    ram_items = _as_list(snapshot.get("ram"))
    gpus = _as_list(snapshot.get("gpu"))
    gpu = _first(gpus, {}) or {}

    physical = _as_list(snapshot.get("physical_disks"))
    disk_drives = _as_list(snapshot.get("disk_drives"))
    logical = _as_list(snapshot.get("logical_disks"))
    network = _as_list(snapshot.get("network"))
    battery = _first(_as_list(snapshot.get("battery")), {}) or {}

    total_kb = _safe_number(os_data.get("TotalVisibleMemorySize"))
    free_kb = _safe_number(os_data.get("FreePhysicalMemory"))
    used_kb = max(total_kb - free_kb, 0)

    if total_kb:
        ram_line = (
            f"{format_bytes(total_kb * 1024)}  |  "
            f"użyte {format_bytes(used_kb * 1024)}  |  "
            f"wolne {format_bytes(free_kb * 1024)}"
        )
    else:
        total_ram = _safe_number(computer.get("TotalPhysicalMemory"))
        ram_line = format_bytes(total_ram) if total_ram else "brak danych"

    speeds = sorted(
        {
            _safe_number(item.get("ConfiguredClockSpeed") or item.get("Speed"))
            for item in ram_items
            if _safe_number(item.get("ConfiguredClockSpeed") or item.get("Speed")) > 0
        }
    )

    if ram_items:
        ram_line += f"\nKości: {len(ram_items)}"
        if speeds:
            ram_line += "  |  " + "/".join(str(x) for x in speeds) + " MHz"

    cpu_clock = _safe_number(cpu.get("MaxClockSpeed"))
    cpu_line = _clean(cpu.get("Name"))

    if cpu:
        cpu_line += (
            f"\n{_safe_number(cpu.get('NumberOfCores'))} rdzeni / "
            f"{_safe_number(cpu.get('NumberOfLogicalProcessors'))} wątków"
        )
        if cpu_clock:
            cpu_line += f"  |  max {cpu_clock / 1000:.2f} GHz"

    gpu_line = _clean(gpu.get("Name"))
    adapter_ram = _safe_number(gpu.get("AdapterRAM"))
    if adapter_ram > 0:
        gpu_line += f"\nVRAM raportowany przez Windows: {format_bytes(adapter_ram)}"

    driver = _clean(gpu.get("DriverVersion"), "")
    if driver:
        gpu_line += f"\nSterownik: {driver}"

    if display:
        display_line = (
            f"{display.get('width', '?')} × {display.get('height', '?')}"
            f"  |  {display.get('refresh_hz', '?')} Hz"
            f"  |  skala {display.get('scale_percent', '?')}%"
        )
        if display.get("name"):
            display_line += "\n" + str(display["name"])
    else:
        w = _safe_number(gpu.get("CurrentHorizontalResolution"))
        h = _safe_number(gpu.get("CurrentVerticalResolution"))
        hz = _safe_number(gpu.get("CurrentRefreshRate"))
        display_line = f"{w} × {h}" if w and h else "brak danych"
        if hz:
            display_line += f"  |  {hz} Hz"

    disk_lines = []

    if physical:
        for item in physical[:4]:
            name = _clean(item.get("FriendlyName"))
            media = _clean(item.get("MediaType"), "")
            bus = _clean(item.get("BusType"), "")
            size = format_bytes(item.get("Size"))
            health = _clean(item.get("HealthStatus"), "")
            extra = " / ".join(x for x in (media, bus, health) if x)
            disk_lines.append(
                f"{name} - {size}" + (f" ({extra})" if extra else "")
            )
    else:
        for item in disk_drives[:4]:
            disk_lines.append(
                f"{_clean(item.get('Model'))} - {format_bytes(item.get('Size'))}"
            )

    if logical:
        volumes = []
        for item in logical[:5]:
            volumes.append(
                f"{_clean(item.get('DeviceID'))} "
                f"{format_bytes(item.get('FreeSpace'))} wolne / "
                f"{format_bytes(item.get('Size'))}"
            )
        if volumes:
            disk_lines.append("Woluminy: " + " | ".join(volumes))

    disk_line = "\n".join(disk_lines) if disk_lines else "brak danych"

    net_lines = []
    for item in network[:3]:
        ipv4 = next(
            (
                str(ip)
                for ip in _as_list(item.get("IPAddress"))
                if "." in str(ip) and ":" not in str(ip)
            ),
            "",
        )
        gw = next(
            (
                str(ip)
                for ip in _as_list(item.get("DefaultIPGateway"))
                if ip
            ),
            "",
        )
        dns = ", ".join(
            str(x) for x in _as_list(item.get("DNSServerSearchOrder"))[:3]
        )

        line = _clean(item.get("AdapterName") or item.get("Description"))

        speed = _safe_number(item.get("Speed"))
        if speed:
            line += f"  |  {format_speed_bps(speed)}"

        if ipv4:
            line += f"\nIP {ipv4}"
        if gw:
            line += f"  |  brama {gw}"
        if dns:
            line += f"\nDNS {dns}"

        net_lines.append(line)

    network_line = "\n\n".join(net_lines) if net_lines else "brak danych"

    board = snapshot.get("motherboard") or {}
    bios = snapshot.get("bios") or {}

    board_line = (
        f"{_clean(board.get('Manufacturer'))} "
        f"{_clean(board.get('Product'), '')}"
    ).strip()

    bios_version = _clean(bios.get("SMBIOSBIOSVersion"), "")
    if bios_version:
        board_line += f"\nBIOS/UEFI: {bios_version}"

    bios_date = _date_only(bios.get("ReleaseDate"))
    if bios_date != "brak danych":
        board_line += f"  |  {bios_date}"

    if not board_line:
        board_line = "brak danych"

    battery_line = "brak baterii / komputer stacjonarny"
    if battery:
        charge = _safe_number(battery.get("EstimatedChargeRemaining"), -1)
        battery_line = _clean(battery.get("Name"), "Bateria")
        if charge >= 0:
            battery_line += f"\nNaładowanie: {charge}%"
        status = _clean(battery.get("Status"), "")
        if status:
            battery_line += f"  |  {status}"

    uptime_line = "brak danych"
    boot = os_data.get("LastBootUpTime")
    if boot:
        try:
            boot_dt = datetime.fromisoformat(str(boot).replace("Z", "+00:00"))
            now = datetime.now(boot_dt.tzinfo)
            delta = now - boot_dt
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            uptime_line = f"{days} d {hours} h {minutes} min"
        except (ValueError, TypeError, OverflowError):
            uptime_line = _clean(boot)

    os_line = (
        f"{_clean(os_data.get('Caption'))}\n"
        f"Build {_clean(os_data.get('BuildNumber'))}  |  "
        f"{_clean(os_data.get('OSArchitecture'))}\n"
        f"Uptime: {uptime_line}"
    )

    return {
        "System": os_line,
        "CPU": cpu_line,
        "RAM": ram_line,
        "GPU": gpu_line,
        "Ekran": display_line,
        "Dyski": disk_line,
        "Sieć": network_line,
        "Płyta / BIOS": board_line,
        "Bateria": battery_line,
    }


def format_snapshot_text(snapshot, display=None):
    summary = build_summary(snapshot, display)

    lines = [
        "PRESTIGE TECH - SPECYFIKACJA I SNAPSHOT SYSTEMU",
        "",
    ]

    for title, value in summary.items():
        lines.append(title.upper())
        lines.append(str(value))
        lines.append("")

    ram_items = _as_list(snapshot.get("ram"))
    if ram_items:
        lines.append("RAM - MODUŁY")
        for index, item in enumerate(ram_items, 1):
            cap = format_bytes(item.get("Capacity"))
            speed = _safe_number(
                item.get("ConfiguredClockSpeed") or item.get("Speed")
            )
            manufacturer = _clean(item.get("Manufacturer"), "")
            part = _clean(item.get("PartNumber"), "")
            locator = _clean(
                item.get("DeviceLocator") or item.get("BankLabel"),
                "",
            )
            details = " | ".join(
                x
                for x in (
                    cap,
                    f"{speed} MHz" if speed else "",
                    manufacturer,
                    part,
                    locator,
                )
                if x
            )
            lines.append(f"{index}. {details}")
        lines.append("")

    gpus = _as_list(snapshot.get("gpu"))
    if len(gpus) > 1:
        lines.append("GPU - WSZYSTKIE")
        for index, item in enumerate(gpus, 1):
            lines.append(
                f"{index}. {_clean(item.get('Name'))} | "
                f"driver {_clean(item.get('DriverVersion'))}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"