#requires -Version 5.1
<#
    PRESTIGE TECH
    NETWORK SENTINEL v2.0

    Defensive host and LAN monitoring for Windows.

    Najwazniejsze funkcje:
    * czytelne oznaczenie "TEN KOMPUTER" i "ROUTER / BRAMA"
    * filtrowanie broadcast, multicast i obcych interfejsow
    * aktywne wykrywanie hostow w monitorowanym LAN
    * reverse DNS, MAC, vendor OUI, heurystyczny typ urzadzenia
    * lokalna baza OUI z opcjonalna aktualizacja z IEEE
    * urzadzenia znane, zaufane, nowe, online i offline
    * historia zmian urzadzen
    * Start / Stop monitoringu
    * Skanuj teraz
    * harmonogram skanu 1, 5, 10, 15, 30, 60 minut
    * monitoring Windows Firewall
    * opcjonalny Deep Capture przez TShark + Npcap
    * wykrywanie TCP/UDP port sweep, ICMP burst i ARP sweep
    * blokowanie / odblokowanie IP przez Windows Firewall
    * HTML report
    * status Npcap, TShark, Nmap i Firewall
    * autostart zwykly oraz pelny autostart ADMIN przez Task Scheduler
    * bridge JSON do Prestige Tech Dashboard
    * bridge celu do modulu Nmap

    Uwaga:
    Ten modul jest przeznaczony do ochrony wlasnego hosta i wlasnej sieci.
#>

param(
    [string]$DashboardRoot = "",
    [string]$BridgeDir = "",
    [switch]$NoAutoStart
)

$ErrorActionPreference = "Continue"

# ============================================================
# CONSTANTS
# ============================================================

$Script:Version = "2.0.0"
$Script:ModuleId = "network-sentinel"
$Script:ModuleName = "Network Sentinel"
$Script:StartedAt = Get-Date

# ============================================================
# STA / WPF
# ============================================================

if ([System.Threading.Thread]::CurrentThread.ApartmentState -ne "STA") {
    if ($PSCommandPath) {
        $args2 = @(
            "-NoProfile",
            "-STA",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$PSCommandPath`""
        )

        if ($DashboardRoot) {
            $args2 += @("-DashboardRoot", "`"$DashboardRoot`"")
        }

        if ($BridgeDir) {
            $args2 += @("-BridgeDir", "`"$BridgeDir`"")
        }

        if ($NoAutoStart) {
            $args2 += "-NoAutoStart"
        }

        Start-Process powershell.exe -ArgumentList $args2
        exit
    }
}

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ============================================================
# PATHS
# ============================================================

$Script:DataRoot = Join-Path $env:LOCALAPPDATA "PrestigeTech\NetworkSentinel"

$Script:Dirs = @{
    Root      = $Script:DataRoot
    Database  = Join-Path $Script:DataRoot "database"
    Logs      = Join-Path $Script:DataRoot "logs"
    Reports   = Join-Path $Script:DataRoot "reports"
    Capture   = Join-Path $Script:DataRoot "capture"
}

foreach ($dir in $Script:Dirs.Values) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

if (-not $BridgeDir) {
    if ($DashboardRoot) {
        $BridgeDir = Join-Path $DashboardRoot "runtime\bridge"
    } else {
        $BridgeDir = Join-Path $Script:DataRoot "bridge"
    }
}

if (-not (Test-Path $BridgeDir)) {
    New-Item -ItemType Directory -Path $BridgeDir -Force | Out-Null
}

$Script:BridgeDir = $BridgeDir

$Script:SettingsFile   = Join-Path $Script:Dirs.Database "settings.json"
$Script:KnownFile      = Join-Path $Script:Dirs.Database "known-devices.json"
$Script:TrustedFile    = Join-Path $Script:Dirs.Database "trusted-devices.json"
$Script:HistoryFile    = Join-Path $Script:Dirs.Logs "device-history.jsonl"
$Script:EventsJson     = Join-Path $Script:Dirs.Logs "events.jsonl"
$Script:EventsCsv      = Join-Path $Script:Dirs.Logs "events.csv"
$Script:OuiFile        = Join-Path $Script:Dirs.Database "oui.txt"
$Script:ArpRawLog      = Join-Path $Script:Dirs.Capture "packet-live.log"
$Script:ArpErrorLog    = Join-Path $Script:Dirs.Capture "packet-error.log"
$Script:StatusFile     = Join-Path $BridgeDir "sentinel-status.json"
$Script:NmapRequest    = Join-Path $BridgeDir "nmap-request.json"
$Script:FirewallLog    = Join-Path $env:SystemRoot "System32\LogFiles\Firewall\pfirewall.log"

# ============================================================
# SETTINGS
# ============================================================

$Script:Settings = [ordered]@{
    PollMilliseconds          = 1500
    ScheduleEnabled           = $true
    ScanIntervalMinutes       = 5
    ScanOnStart               = $true
    StartMonitoringOnLaunch   = $false
    ResolveNames              = $true
    EnableDeepCapture         = $true
    EnableFirewallLogging     = $true
    DetectionWindowSeconds    = 30
    MediumUniquePorts         = 12
    HighUniquePorts           = 30
    RepeatedPortAttempts      = 35
    IcmpBurstThreshold        = 20
    ArpWindowSeconds          = 10
    ArpSweepTargets           = 18
    AlertCooldownSeconds      = 20
    BalloonNotifications      = $true
    MaximumAlertsInGui        = 1000
    ShowVirtualAdapters       = $false
    SelectedInterfaceIndex    = 0
    OfflineAfterMinutes       = 15
    PingTimeoutMilliseconds   = 180
    UseNmapDiscovery          = $false
    FirstRunCompleted         = $false
}

function Save-Settings {
    try {
        $Script:Settings |
            ConvertTo-Json -Depth 8 |
            Set-Content $Script:SettingsFile -Encoding UTF8
    } catch {
    }
}

function Load-Settings {
    if (-not (Test-Path $Script:SettingsFile)) {
        Save-Settings
        return
    }

    try {
        $loaded = Get-Content $Script:SettingsFile -Raw | ConvertFrom-Json

        foreach ($p in $loaded.PSObject.Properties) {
            if ($Script:Settings.Contains($p.Name)) {
                $Script:Settings[$p.Name] = $p.Value
            }
        }
    } catch {
    }
}

Load-Settings

# ============================================================
# STATE
# ============================================================

$Script:IsAdmin = $false
$Script:Running = $false
$Script:ScanInProgress = $false
$Script:LastScan = $null
$Script:NextScan = $null

$Script:Adapters = @()
$Script:SelectedAdapter = $null
$Script:LocalIP = ""
$Script:PrefixLength = 24
$Script:GatewayIP = ""

$Script:DeviceState = @{}
$Script:KnownDevices = @()
$Script:TrustedDevicesData = @()
$Script:OuiDb = @{}
$Script:OuiLoaded = $false

$Script:Traffic = @{}
$Script:PacketTraffic = @{}
$Script:ArpActivity = @{}
$Script:LastAlert = @{}

$Script:FirewallOffset = 0
$Script:FirewallInitialized = $false
$Script:FirewallFields = @(
    "date","time","action","protocol","src-ip","dst-ip","src-port","dst-port",
    "size","tcpflags","tcpsyn","tcpack","tcpwin","icmptype","icmpcode","info","path"
)

$Script:TsharkProcess = $null
$Script:TsharkPath = $null
$Script:NmapPath = $null
$Script:CaptureOffset = 0
$Script:CapturePackets = 0
$Script:CapturePacketsLast = 0
$Script:CaptureRate = 0
$Script:CaptureLastRateTime = Get-Date
$Script:CaptureLastError = ""

$Script:LastStatusWrite = [datetime]::MinValue

# ============================================================
# GUI COLLECTIONS
# ============================================================

$Script:Devices = [System.Collections.ObjectModel.ObservableCollection[object]]::new()
$Script:Alerts = [System.Collections.ObjectModel.ObservableCollection[object]]::new()
$Script:History = [System.Collections.ObjectModel.ObservableCollection[object]]::new()

# ============================================================
# HELPERS
# ============================================================

function Test-IsAdministrator {
    try {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

$Script:IsAdmin = Test-IsAdministrator

function Write-JsonAtomic {
    param(
        [Parameter(Mandatory)]$Object,
        [Parameter(Mandatory)][string]$Path
    )

    try {
        $temp = "$Path.tmp"
        $Object | ConvertTo-Json -Depth 12 | Set-Content $temp -Encoding UTF8
        Move-Item $temp $Path -Force
    } catch {
    }
}

function Load-JsonArray {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return @()
    }

    try {
        $x = Get-Content $Path -Raw | ConvertFrom-Json
        if ($null -eq $x) {
            return @()
        }
        return @($x)
    } catch {
        return @()
    }
}

$Script:KnownDevices = Load-JsonArray $Script:KnownFile
$Script:TrustedDevicesData = Load-JsonArray $Script:TrustedFile

function Save-KnownDevices {
    try {
        @($Script:KnownDevices) |
            ConvertTo-Json -Depth 8 |
            Set-Content $Script:KnownFile -Encoding UTF8
    } catch {
    }
}

function Save-TrustedDevices {
    try {
        @($Script:TrustedDevicesData) |
            ConvertTo-Json -Depth 8 |
            Set-Content $Script:TrustedFile -Encoding UTF8
    } catch {
    }
}

function Test-IPv4 {
    param([string]$IP)

    $parsed = $null

    if ([System.Net.IPAddress]::TryParse($IP, [ref]$parsed)) {
        return (
            $parsed.AddressFamily -eq
            [System.Net.Sockets.AddressFamily]::InterNetwork
        )
    }

    return $false
}

function Normalize-Mac {
    param([string]$Mac)

    if (-not $Mac) {
        return ""
    }

    return $Mac.ToUpper().Replace("-", ":")
}

function Get-DeviceKey {
    param(
        [string]$IP,
        [string]$Mac
    )

    $m = Normalize-Mac $Mac

    if (
        $m -and
        $m -ne "00:00:00:00:00:00" -and
        $m -ne "FF:FF:FF:FF:FF:FF"
    ) {
        return $m
    }

    return $IP
}

function Test-IsMulticastOrSpecial {
    param([string]$IP)

    if (-not (Test-IPv4 $IP)) {
        return $true
    }

    $p = $IP.Split(".")
    $first = [int]$p[0]

    if ($IP -eq "0.0.0.0") { return $true }
    if ($IP -eq "255.255.255.255") { return $true }
    if ($first -eq 127) { return $true }
    if ($first -ge 224) { return $true }

    return $false
}

function Get-SubnetBounds {
    param(
        [string]$IP,
        [int]$PrefixLength
    )

    if (-not (Test-IPv4 $IP)) {
        return $null
    }

    $oct = $IP.Split(".") | ForEach-Object { [int]$_ }

    # Dla sieci szerszych niz /24 Sentinel celowo ogranicza discovery do lokalnego /24.
    if ($PrefixLength -lt 24) {
        return [pscustomobject]@{
            FirstHost = "$($oct[0]).$($oct[1]).$($oct[2]).1"
            LastHost = "$($oct[0]).$($oct[1]).$($oct[2]).254"
            Network = "$($oct[0]).$($oct[1]).$($oct[2]).0"
            Broadcast = "$($oct[0]).$($oct[1]).$($oct[2]).255"
            Scope = "$($oct[0]).$($oct[1]).$($oct[2]).0/24"
            Capped = $true
        }
    }

    $hostBits = 32 - $PrefixLength
    $blockSize = [int][math]::Pow(2, $hostBits)
    if ($blockSize -lt 1) { $blockSize = 1 }
    if ($blockSize -gt 256) { $blockSize = 256 }

    $last = $oct[3]
    $start = [math]::Floor($last / $blockSize) * $blockSize
    $end = $start + $blockSize - 1

    if ($PrefixLength -eq 32) {
        $firstHost = $last
        $lastHost = $last
    } elseif ($PrefixLength -eq 31) {
        $firstHost = $start
        $lastHost = $end
    } else {
        $firstHost = $start + 1
        $lastHost = $end - 1
    }

    return [pscustomobject]@{
        FirstHost = "$($oct[0]).$($oct[1]).$($oct[2]).$firstHost"
        LastHost = "$($oct[0]).$($oct[1]).$($oct[2]).$lastHost"
        Network = "$($oct[0]).$($oct[1]).$($oct[2]).$start"
        Broadcast = "$($oct[0]).$($oct[1]).$($oct[2]).$end"
        Scope = "$($oct[0]).$($oct[1]).$($oct[2]).$start/$PrefixLength"
        Capped = $false
    }
}

function Test-IsBroadcastAddress {
    param([string]$IP)

    if (-not $Script:LocalIP) {
        return $false
    }

    $bounds = Get-SubnetBounds $Script:LocalIP $Script:PrefixLength

    if (-not $bounds) {
        return $false
    }

    return ($IP -eq $bounds.Broadcast)
}

function Get-ScanTargets {
    if (-not $Script:LocalIP) {
        return @()
    }

    $bounds = Get-SubnetBounds $Script:LocalIP $Script:PrefixLength

    if (-not $bounds) {
        return @()
    }

    $first = $bounds.FirstHost.Split(".") | ForEach-Object { [int]$_ }
    $last = $bounds.LastHost.Split(".") | ForEach-Object { [int]$_ }

    $targets = @()

    for ($i = $first[3]; $i -le $last[3]; $i++) {
        $ip = "$($first[0]).$($first[1]).$($first[2]).$i"

        if ($ip -ne $Script:LocalIP) {
            $targets += $ip
        }
    }

    return $targets
}

function Write-HistoryEvent {
    param(
        [string]$Key,
        [string]$IP,
        [string]$Event,
        [string]$Details = ""
    )

    $record = [pscustomobject]@{
        Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Key = $Key
        IP = $IP
        Event = $Event
        Details = $Details
    }

    try {
        ($record | ConvertTo-Json -Compress) |
            Add-Content $Script:HistoryFile -Encoding UTF8
    } catch {
    }

    try {
        $Script:History.Insert(0, $record)

        while ($Script:History.Count -gt 500) {
            $Script:History.RemoveAt($Script:History.Count - 1)
        }
    } catch {
    }
}

function Load-RecentHistory {
    $Script:History.Clear()

    if (-not (Test-Path $Script:HistoryFile)) {
        return
    }

    try {
        $lines = Get-Content $Script:HistoryFile -Tail 300

        foreach ($line in ($lines | Select-Object -Last 300)) {
            try {
                $x = $line | ConvertFrom-Json
                $Script:History.Insert(0, $x)
            } catch {
            }
        }
    } catch {
    }
}

# ============================================================
# NOTIFICATIONS
# ============================================================

$Script:NotifyIcon = New-Object System.Windows.Forms.NotifyIcon
$Script:NotifyIcon.Icon = [System.Drawing.SystemIcons]::Shield
$Script:NotifyIcon.Text = "Prestige Tech Network Sentinel"
$Script:NotifyIcon.Visible = $true

function Show-SentinelNotification {
    param(
        [string]$Title,
        [string]$Message
    )

    if (-not $Script:Settings.BalloonNotifications) {
        return
    }

    try {
        $Script:NotifyIcon.BalloonTipTitle = $Title
        $Script:NotifyIcon.BalloonTipText = $Message
        $Script:NotifyIcon.BalloonTipIcon = "Warning"
        $Script:NotifyIcon.ShowBalloonTip(4500)
    } catch {
    }
}

# ============================================================
# ALERTS
# ============================================================

function Write-EventRecord {
    param($Event)

    try {
        ($Event | ConvertTo-Json -Compress -Depth 8) |
            Add-Content $Script:EventsJson -Encoding UTF8
    } catch {
    }

    try {
        if (-not (Test-Path $Script:EventsCsv)) {
            $Event |
                Export-Csv $Script:EventsCsv -NoTypeInformation -Encoding UTF8
        } else {
            $Event |
                Export-Csv $Script:EventsCsv -NoTypeInformation -Append -Encoding UTF8
        }
    } catch {
    }
}

function Add-Alert {
    param(
        [string]$Severity,
        [string]$Category,
        [string]$SourceIP,
        [string]$SourceMac = "",
        [string]$Type,
        [string]$Protocol = "",
        [string]$Ports = "",
        [int]$Attempts = 0,
        [int]$Score = 0,
        [double]$Confidence = 0.50,
        [string]$Note = ""
    )

    $evt = [pscustomobject]@{
        Time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Severity = $Severity
        Category = $Category
        SourceIP = $SourceIP
        SourceMac = Normalize-Mac $SourceMac
        Type = $Type
        Protocol = $Protocol
        Ports = $Ports
        Attempts = $Attempts
        Score = $Score
        Confidence = "{0:P0}" -f $Confidence
        Note = $Note
    }

    try {
        $Script:Alerts.Insert(0, $evt)

        while ($Script:Alerts.Count -gt $Script:Settings.MaximumAlertsInGui) {
            $Script:Alerts.RemoveAt($Script:Alerts.Count - 1)
        }
    } catch {
    }

    Write-EventRecord $evt

    if ($Category -eq "THREAT" -and ($Severity -eq "HIGH" -or $Severity -eq "CRITICAL")) {
        Show-SentinelNotification "Network Sentinel" "$Type | $SourceIP"
    }

    Update-UIStatus
}

# ============================================================
# ADAPTERS
# ============================================================

function Test-VirtualAdapter {
    param($Adapter)

    $text = "$($Adapter.Name) $($Adapter.InterfaceDescription)"

    return (
        $text -match "VirtualBox|VMware|Hyper-V|vEthernet|TAP|TUN|VPN|Npcap Loopback|Loopback|WSL|Docker|Hamachi|ZeroTier|Tailscale"
    )
}

function Get-MonitorableAdapters {
    $result = @()

    try {
        $configs = Get-NetIPConfiguration |
            Where-Object {
                $_.IPv4Address -and
                $_.NetAdapter.Status -eq "Up"
            }

        foreach ($cfg in $configs) {
            $adapter = Get-NetAdapter -InterfaceIndex $cfg.InterfaceIndex -ErrorAction SilentlyContinue

            if (-not $adapter) {
                continue
            }

            $virtual = Test-VirtualAdapter $adapter

            if ($virtual -and -not $Script:Settings.ShowVirtualAdapters) {
                continue
            }

            $ipv4 = @($cfg.IPv4Address | Select-Object -First 1)

            if (-not $ipv4) {
                continue
            }

            $gateway = ""

            if ($cfg.IPv4DefaultGateway) {
                $gateway = $cfg.IPv4DefaultGateway.NextHop
            }

            $result += [pscustomobject]@{
                InterfaceIndex = $cfg.InterfaceIndex
                Name = $adapter.Name
                Description = $adapter.InterfaceDescription
                IP = $ipv4.IPAddress
                Prefix = $ipv4.PrefixLength
                Gateway = $gateway
                Mac = Normalize-Mac $adapter.MacAddress
                Guid = $adapter.InterfaceGuid
                Virtual = $virtual
                Display = "$($adapter.Name) | $($ipv4.IPAddress)/$($ipv4.PrefixLength)"
            }
        }
    } catch {
    }

    return @($result)
}

function Refresh-Adapters {
    $Script:Adapters = @(Get-MonitorableAdapters)

    if ($Script:AdapterCombo) {
        $Script:AdapterCombo.ItemsSource = $null
        $Script:AdapterCombo.ItemsSource = $Script:Adapters
        $Script:AdapterCombo.DisplayMemberPath = "Display"

        $targetIndex = -1

        if ([int]$Script:Settings.SelectedInterfaceIndex -gt 0) {
            for ($i = 0; $i -lt $Script:Adapters.Count; $i++) {
                if ($Script:Adapters[$i].InterfaceIndex -eq [int]$Script:Settings.SelectedInterfaceIndex) {
                    $targetIndex = $i
                    break
                }
            }
        }

        if ($targetIndex -lt 0 -and $Script:Adapters.Count -gt 0) {
            # Preferuj adapter z brama domyslna
            for ($i = 0; $i -lt $Script:Adapters.Count; $i++) {
                if ($Script:Adapters[$i].Gateway) {
                    $targetIndex = $i
                    break
                }
            }

            if ($targetIndex -lt 0) {
                $targetIndex = 0
            }
        }

        if ($targetIndex -ge 0) {
            $Script:AdapterCombo.SelectedIndex = $targetIndex
        }
    }
}

function Set-SelectedAdapter {
    param($Adapter)

    if (-not $Adapter) {
        return
    }

    $changed = (
        -not $Script:SelectedAdapter -or
        $Script:SelectedAdapter.InterfaceIndex -ne $Adapter.InterfaceIndex
    )

    $Script:SelectedAdapter = $Adapter
    $Script:LocalIP = $Adapter.IP
    $Script:PrefixLength = [int]$Adapter.Prefix
    $Script:GatewayIP = $Adapter.Gateway

    $Script:Settings.SelectedInterfaceIndex = [int]$Adapter.InterfaceIndex
    Save-Settings

    if ($changed) {
        Stop-DeepCapture
        $Script:FirewallInitialized = $false
        $Script:DeviceState.Clear()
        Refresh-DeviceGrid

        if ($Script:Running -and $Script:Settings.EnableDeepCapture) {
            Start-DeepCapture | Out-Null
        }

        if ($Script:Running) {
            Invoke-DiscoveryScan
        }
    }

    Update-UIStatus
}

# ============================================================
# OUI / VENDOR
# ============================================================

$Script:BuiltInOui = @{
    "00:15:5D" = "Microsoft Hyper-V"
    "00:0C:29" = "VMware"
    "00:50:56" = "VMware"
    "08:00:27" = "Oracle VirtualBox"
    "B8:27:EB" = "Raspberry Pi Foundation"
    "DC:A6:32" = "Raspberry Pi Trading"
    "E4:5F:01" = "Raspberry Pi Trading"
    "18:FE:34" = "Espressif"
    "24:0A:C4" = "Espressif"
    "30:AE:A4" = "Espressif"
    "84:F3:EB" = "Espressif"
    "A4:CF:12" = "Espressif"
}

function Import-OuiDatabase {
    if ($Script:OuiLoaded) {
        return
    }

    $Script:OuiDb = @{}

    foreach ($k in $Script:BuiltInOui.Keys) {
        $Script:OuiDb[$k] = $Script:BuiltInOui[$k]
    }

    if (Test-Path $Script:OuiFile) {
        try {
            foreach ($line in Get-Content $Script:OuiFile -ErrorAction SilentlyContinue) {
                if ($line -match '^([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})-([0-9A-Fa-f]{2})\s+\(hex\)\s+(.+)$') {
                    $prefix = "$($Matches[1]):$($Matches[2]):$($Matches[3])".ToUpper()
                    $vendor = $Matches[4].Trim()

                    if (-not $Script:OuiDb.ContainsKey($prefix)) {
                        $Script:OuiDb[$prefix] = $vendor
                    }
                }
            }
        } catch {
        }
    }

    $Script:OuiLoaded = $true
}

function Update-OuiDatabase {
    try {
        $url = "https://standards-oui.ieee.org/oui/oui.txt"

        if ($Script:TxtEngineMessage) {
            $Script:TxtEngineMessage.Text = "Pobieranie bazy IEEE OUI..."
        }

        Invoke-WebRequest -Uri $url -OutFile $Script:OuiFile -UseBasicParsing -TimeoutSec 30

        $Script:OuiLoaded = $false
        Import-OuiDatabase

        if ($Script:TxtEngineMessage) {
            $Script:TxtEngineMessage.Text = "Baza OUI zaktualizowana. Wpisow: $($Script:OuiDb.Count)"
        }

        Invoke-DiscoveryScan
    } catch {
        if ($Script:TxtEngineMessage) {
            $Script:TxtEngineMessage.Text = "Nie udalo sie pobrac OUI: $($_.Exception.Message)"
        }
    }
}

function Get-VendorFromMac {
    param([string]$Mac)

    $m = Normalize-Mac $Mac

    if (-not $m -or $m.Length -lt 8) {
        return "Nieznany"
    }

    if ($m -eq "FF:FF:FF:FF:FF:FF") {
        return "Broadcast"
    }

    try {
        $first = [Convert]::ToInt32($m.Substring(0,2), 16)

        if (($first -band 2) -ne 0) {
            return "Prywatny / randomizowany MAC"
        }
    } catch {
    }

    Import-OuiDatabase

    $prefix = $m.Substring(0,8)

    if ($Script:OuiDb.ContainsKey($prefix)) {
        return $Script:OuiDb[$prefix]
    }

    return "Nieznany producent"
}

# ============================================================
# NAME / TYPE IDENTIFICATION
# ============================================================

function Resolve-HostNameSafe {
    param([string]$IP)

    if (-not $Script:Settings.ResolveNames) {
        return ""
    }

    if ($IP -eq $Script:LocalIP) {
        return $env:COMPUTERNAME
    }

    try {
        $r = Resolve-DnsName -Name $IP -Type PTR -QuickTimeout -ErrorAction SilentlyContinue |
            Select-Object -First 1

        if ($r -and $r.NameHost) {
            return $r.NameHost.TrimEnd(".")
        }
    } catch {
    }

    return ""
}

function Get-DeviceTypeGuess {
    param(
        [string]$Vendor,
        [string]$HostName,
        [string]$Role
    )

    if ($Role -eq "THIS_PC") {
        return [pscustomobject]@{ Type = "Komputer Windows"; Confidence = 100 }
    }

    if ($Role -eq "GATEWAY") {
        return [pscustomobject]@{ Type = "Router / Brama"; Confidence = 100 }
    }

    $text = "$Vendor $HostName".ToLower()

    if ($text -match "printer|hewlett|hp inc|brother|epson|canon|xerox|lexmark") {
        return [pscustomobject]@{ Type = "Drukarka"; Confidence = 85 }
    }

    if ($text -match "raspberry") {
        return [pscustomobject]@{ Type = "Raspberry Pi"; Confidence = 95 }
    }

    if ($text -match "espressif|tuya|shelly|sonoff|iot") {
        return [pscustomobject]@{ Type = "IoT"; Confidence = 85 }
    }

    if ($text -match "roku|chromecast|androidtv|bravia|webos|television") {
        return [pscustomobject]@{ Type = "TV / Multimedia"; Confidence = 80 }
    }

    if ($text -match "iphone|ipad|apple") {
        return [pscustomobject]@{ Type = "Telefon / Tablet"; Confidence = 70 }
    }

    if ($text -match "samsung|xiaomi|oneplus|oppo|vivo|motorola|huawei|honor|realme") {
        return [pscustomobject]@{ Type = "Telefon / Urzadzenie mobilne"; Confidence = 65 }
    }

    if ($text -match "intel|realtek|dell|lenovo|asus|acer|micro-star|gigabyte") {
        return [pscustomobject]@{ Type = "Komputer / Laptop"; Confidence = 60 }
    }

    if ($text -match "tp-link|mikrotik|ubiquiti|netgear|zyxel|d-link|tenda") {
        return [pscustomobject]@{ Type = "Sprzet sieciowy"; Confidence = 80 }
    }

    if ($text -match "vmware|virtualbox|hyper-v|parallels") {
        return [pscustomobject]@{ Type = "Maszyna wirtualna"; Confidence = 95 }
    }

    return [pscustomobject]@{ Type = "Nieznane"; Confidence = 30 }
}

function Get-KnownRecord {
    param([string]$Key)

    foreach ($x in @($Script:KnownDevices)) {
        if ($x.Key -eq $Key) {
            return $x
        }
    }

    return $null
}

function Get-TrustedRecord {
    param([string]$Key)

    foreach ($x in @($Script:TrustedDevicesData)) {
        if ($x.Key -eq $Key) {
            return $x
        }
    }

    return $null
}

function Add-KnownRecord {
    param($Device)

    if (Get-KnownRecord $Device.Key) {
        return
    }

    $Script:KnownDevices += [pscustomobject]@{
        Key = $Device.Key
        IP = $Device.IP
        MAC = $Device.MAC
        Name = $Device.Name
        Vendor = $Device.Vendor
        Type = $Device.Type
        Added = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }

    Save-KnownDevices
}

# ============================================================
# DEVICE STATE
# ============================================================

function New-OrUpdateDevice {
    param(
        [string]$IP,
        [string]$MAC,
        [string]$Role = "DEVICE",
        [string]$Status = "ONLINE",
        [string]$Name = "",
        [string]$Source = "Discovery"
    )

    if (-not (Test-IPv4 $IP)) {
        return
    }

    if (Test-IsMulticastOrSpecial $IP) {
        return
    }

    if (Test-IsBroadcastAddress $IP) {
        return
    }

    $macNorm = Normalize-Mac $MAC

    if ($macNorm -eq "FF:FF:FF:FF:FF:FF") {
        return
    }

    $key = Get-DeviceKey $IP $macNorm
    $vendor = Get-VendorFromMac $macNorm

    if (-not $Name) {
        if ($Role -eq "THIS_PC") {
            $Name = $env:COMPUTERNAME
        } elseif ($Role -eq "GATEWAY") {
            $Name = "Router / Brama"
        } else {
            $Name = Resolve-HostNameSafe $IP
        }
    }

    if (-not $Name) {
        $Name = "Nieznane urzadzenie"
    }

    $guess = Get-DeviceTypeGuess $vendor $Name $Role
    $known = $null -ne (Get-KnownRecord $key)
    $trusted = $null -ne (Get-TrustedRecord $key)

    $now = Get-Date
    $firstSeen = $now
    $previousStatus = ""

    if ($Script:DeviceState.ContainsKey($key)) {
        $old = $Script:DeviceState[$key]
        $firstSeen = $old.FirstSeen
        $previousStatus = $old.Status

        if ($old.IP -ne $IP) {
            Write-HistoryEvent $key $IP "Zmiana IP" "$($old.IP) -> $IP"
        }
    }

    $record = [pscustomobject]@{
        Key = $key
        Role = $Role
        RoleLabel = $(if ($Role -eq "THIS_PC") { "TEN KOMPUTER" }
            elseif ($Role -eq "GATEWAY") { "ROUTER / BRAMA" }
            else { "URZADZENIE" })
        Name = $Name
        IP = $IP
        MAC = $macNorm
        Vendor = $vendor
        Type = $guess.Type
        TypeConfidence = "$($guess.Confidence)%"
        Status = $Status
        Known = $known
        Trusted = $trusted
        New = (-not $known -and $Role -eq "DEVICE")
        FirstSeen = $firstSeen
        LastSeen = $now
        Interface = $(if ($Script:SelectedAdapter) { $Script:SelectedAdapter.Name } else { "" })
        Source = $Source
    }

    $Script:DeviceState[$key] = $record

    if (-not $previousStatus) {
        Write-HistoryEvent $key $IP "Pierwsze wykrycie" "$Name | $vendor | $($guess.Type)"

        if ($record.New) {
            Add-Alert `
                -Severity "INFO" `
                -Category "DEVICE" `
                -SourceIP $IP `
                -SourceMac $macNorm `
                -Type "Nowe urzadzenie w sieci" `
                -Protocol "LAN" `
                -Score 0 `
                -Confidence 0.90 `
                -Note "$Name | $vendor | $($guess.Type)"

            Show-SentinelNotification "Nowe urzadzenie" "$Name | $IP"
        }
    } elseif ($previousStatus -ne $Status) {
        Write-HistoryEvent $key $IP "Zmiana statusu" "$previousStatus -> $Status"
    }
}

function Mark-StaleDevicesOffline {
    $cutoff = (Get-Date).AddMinutes(-1 * [int]$Script:Settings.OfflineAfterMinutes)

    foreach ($key in @($Script:DeviceState.Keys)) {
        $d = $Script:DeviceState[$key]

        if ($d.Role -eq "THIS_PC") {
            continue
        }

        if ($d.LastSeen -lt $cutoff -and $d.Status -ne "OFFLINE") {
            $d.Status = "OFFLINE"
            Write-HistoryEvent $key $d.IP "Offline" "Brak wykrycia przez $($Script:Settings.OfflineAfterMinutes) min"
        }
    }
}

function Refresh-DeviceGrid {
    if (-not $Script:Devices) {
        return
    }

    Mark-StaleDevicesOffline

    $Script:Devices.Clear()

    $ordered = @(
        $Script:DeviceState.Values |
            Sort-Object `
                @{Expression = {
                    if ($_.Role -eq "THIS_PC") { 0 }
                    elseif ($_.Role -eq "GATEWAY") { 1 }
                    else { 2 }
                }},
                @{Expression = { if ($_.Status -eq "ONLINE") { 0 } else { 1 } }},
                IP
    )

    foreach ($d in $ordered) {
        $Script:Devices.Add($d)
    }

    Update-UIStatus
}

function Add-CurrentDeviceToKnown {
    $d = $Script:DevicesGrid.SelectedItem

    if (-not $d) {
        return
    }

    Add-KnownRecord $d

    if ($Script:DeviceState.ContainsKey($d.Key)) {
        $Script:DeviceState[$d.Key].Known = $true
        $Script:DeviceState[$d.Key].New = $false
    }

    Write-HistoryEvent $d.Key $d.IP "Dodano do znanych" $d.Name
    Refresh-DeviceGrid
}

function Add-CurrentDeviceToTrusted {
    $d = $Script:DevicesGrid.SelectedItem

    if (-not $d) {
        return
    }

    if (-not (Get-TrustedRecord $d.Key)) {
        $Script:TrustedDevicesData += [pscustomobject]@{
            Key = $d.Key
            IP = $d.IP
            MAC = $d.MAC
            Name = $d.Name
            Added = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        }

        Save-TrustedDevices
    }

    if ($Script:DeviceState.ContainsKey($d.Key)) {
        $Script:DeviceState[$d.Key].Trusted = $true
    }

    Write-HistoryEvent $d.Key $d.IP "Dodano do zaufanych" $d.Name
    Refresh-DeviceGrid
}

function Remove-CurrentDeviceTrust {
    $d = $Script:DevicesGrid.SelectedItem

    if (-not $d) {
        return
    }

    $Script:TrustedDevicesData = @(
        $Script:TrustedDevicesData |
            Where-Object { $_.Key -ne $d.Key }
    )

    Save-TrustedDevices

    if ($Script:DeviceState.ContainsKey($d.Key)) {
        $Script:DeviceState[$d.Key].Trusted = $false
    }

    Write-HistoryEvent $d.Key $d.IP "Usunieto z zaufanych" $d.Name
    Refresh-DeviceGrid
}

# ============================================================
# LOCAL / GATEWAY IDENTIFICATION
# ============================================================

function Refresh-LocalAndGateway {
    if (-not $Script:SelectedAdapter) {
        return
    }

    New-OrUpdateDevice `
        -IP $Script:LocalIP `
        -MAC $Script:SelectedAdapter.Mac `
        -Role "THIS_PC" `
        -Status "ONLINE" `
        -Name $env:COMPUTERNAME `
        -Source "Local"

    if ($Script:GatewayIP) {
        $gatewayMac = ""

        try {
            $n = Get-NetNeighbor `
                -InterfaceIndex $Script:SelectedAdapter.InterfaceIndex `
                -IPAddress $Script:GatewayIP `
                -ErrorAction SilentlyContinue |
                Select-Object -First 1

            if ($n) {
                $gatewayMac = $n.LinkLayerAddress
            }
        } catch {
        }

        New-OrUpdateDevice `
            -IP $Script:GatewayIP `
            -MAC $gatewayMac `
            -Role "GATEWAY" `
            -Status "ONLINE" `
            -Name "Router / Brama" `
            -Source "Gateway"
    }
}

# ============================================================
# ACTIVE DISCOVERY
# ============================================================

function Invoke-FastPingSweep {
    param([string[]]$Targets)

    $jobs = New-Object System.Collections.Generic.List[object]

    foreach ($ip in $Targets) {
        try {
            $ping = New-Object System.Net.NetworkInformation.Ping
            $task = $ping.SendPingAsync($ip, [int]$Script:Settings.PingTimeoutMilliseconds)

            $jobs.Add([pscustomobject]@{
                IP = $ip
                Ping = $ping
                Task = $task
            })
        } catch {
        }
    }

    if ($jobs.Count -eq 0) {
        return @()
    }

    try {
        $tasks = [System.Threading.Tasks.Task[]]@($jobs | ForEach-Object { $_.Task })
        [void][System.Threading.Tasks.Task]::WaitAll($tasks, 2500)
    } catch {
    }

    $alive = @()

    foreach ($job in $jobs) {
        try {
            if ($job.Task.IsCompleted -and $job.Task.Result.Status -eq "Success") {
                $alive += $job.IP
            }
        } catch {
        }

        try {
            $job.Ping.Dispose()
        } catch {
        }
    }

    return @($alive | Sort-Object -Unique)
}

function Find-Nmap {
    $cmd = Get-Command nmap.exe -ErrorAction SilentlyContinue

    if ($cmd) {
        return $cmd.Source
    }

    $paths = @(
        "$env:ProgramFiles\Nmap\nmap.exe",
        "${env:ProgramFiles(x86)}\Nmap\nmap.exe"
    )

    foreach ($p in $paths) {
        if (Test-Path $p) {
            return $p
        }
    }

    return $null
}

function Invoke-NmapDiscovery {
    param([string]$Scope)

    $nmap = Find-Nmap

    if (-not $nmap) {
        return @()
    }

    $found = @()

    try {
        $output = & $nmap -sn -n $Scope --max-retries 1 2>$null

        foreach ($line in $output) {
            if ($line -match '^Nmap scan report for ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)$') {
                $found += $Matches[1]
            }
        }
    } catch {
    }

    return @($found | Sort-Object -Unique)
}

function Invoke-DiscoveryScan {
    if ($Script:ScanInProgress) {
        return
    }

    if (-not $Script:SelectedAdapter) {
        return
    }

    $Script:ScanInProgress = $true
    Update-UIStatus

    try {
        Refresh-LocalAndGateway

        $targets = @(Get-ScanTargets)
        $alive = @(Invoke-FastPingSweep $targets)

        $bounds = Get-SubnetBounds $Script:LocalIP $Script:PrefixLength

        if (
            $Script:Settings.UseNmapDiscovery -and
            $bounds -and
            (Find-Nmap)
        ) {
            $nmapAlive = @(Invoke-NmapDiscovery $bounds.Scope)
            $alive = @($alive + $nmapAlive | Sort-Object -Unique)
        }

        # Ping uzupelnia cache ARP / neighbor.
        Start-Sleep -Milliseconds 150

        $neighbors = @()

        try {
            $neighbors = @(
                Get-NetNeighbor `
                    -InterfaceIndex $Script:SelectedAdapter.InterfaceIndex `
                    -AddressFamily IPv4 `
                    -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.State -notin @("Unreachable","Incomplete") -and
                        $_.IPAddress -ne $Script:LocalIP -and
                        -not (Test-IsMulticastOrSpecial $_.IPAddress) -and
                        -not (Test-IsBroadcastAddress $_.IPAddress) -and
                        (Normalize-Mac $_.LinkLayerAddress) -ne "FF:FF:FF:FF:FF:FF"
                    }
            )
        } catch {
        }

        $ips = @($alive)

        foreach ($n in $neighbors) {
            $ips += $n.IPAddress
        }

        if ($Script:GatewayIP) {
            $ips += $Script:GatewayIP
        }

        $ips = @($ips | Sort-Object -Unique)

        foreach ($ip in $ips) {
            if ($ip -eq $Script:LocalIP) {
                continue
            }

            if (Test-IsBroadcastAddress $ip) {
                continue
            }

            $neighbor = $neighbors |
                Where-Object { $_.IPAddress -eq $ip } |
                Select-Object -First 1

            $mac = ""

            if ($neighbor) {
                $mac = $neighbor.LinkLayerAddress
            }

            $role = "DEVICE"

            if ($ip -eq $Script:GatewayIP) {
                $role = "GATEWAY"
            }

            New-OrUpdateDevice `
                -IP $ip `
                -MAC $mac `
                -Role $role `
                -Status "ONLINE" `
                -Source "Active discovery"
        }

        $Script:LastScan = Get-Date

        if ($Script:Settings.ScheduleEnabled) {
            $Script:NextScan = $Script:LastScan.AddMinutes([int]$Script:Settings.ScanIntervalMinutes)
        } else {
            $Script:NextScan = $null
        }

        Write-HistoryEvent "SYSTEM" $Script:LocalIP "Skan sieci" "$($ips.Count) hostow wykrytych"

        Refresh-DeviceGrid
    } finally {
        $Script:ScanInProgress = $false
        Update-UIStatus
    }
}

# ============================================================
# FIREWALL LOGGING
# ============================================================

function Enable-FirewallLogging {
    if (-not $Script:IsAdmin) {
        return $false
    }

    try {
        Set-NetFirewallProfile `
            -Name Domain,Private,Public `
            -LogBlocked True `
            -LogAllowed False `
            -LogMaxSizeKilobytes 32767 `
            -LogFileName $Script:FirewallLog `
            -ErrorAction Stop

        return $true
    } catch {
        return $false
    }
}

function Test-FirewallLogging {
    try {
        $profiles = @(Get-NetFirewallProfile -ErrorAction Stop)

        if ($profiles.Count -eq 0) {
            return $false
        }

        return ($profiles | Where-Object { $_.LogBlocked -eq $true }).Count -gt 0
    } catch {
        return $false
    }
}

# ============================================================
# FIREWALL PARSER / SCAN DETECTION
# ============================================================

function Convert-FirewallLine {
    param([string]$Line)

    if (-not $Line) {
        return $null
    }

    if ($Line.StartsWith("#Fields:")) {
        $Script:FirewallFields = $Line.Substring(8).Trim() -split "\s+"
        return $null
    }

    if ($Line.StartsWith("#")) {
        return $null
    }

    $parts = $Line.Trim() -split "\s+"

    if ($parts.Count -lt 8) {
        return $null
    }

    $hash = @{}

    for ($i = 0; $i -lt $Script:FirewallFields.Count; $i++) {
        if ($i -lt $parts.Count) {
            $hash[$Script:FirewallFields[$i]] = $parts[$i]
        }
    }

    try {
        $time = [datetime]::ParseExact(
            "$($hash['date']) $($hash['time'])",
            "yyyy-MM-dd HH:mm:ss",
            [Globalization.CultureInfo]::InvariantCulture
        )
    } catch {
        $time = Get-Date
    }

    return [pscustomobject]@{
        Time = $time
        Action = $hash["action"]
        Protocol = $hash["protocol"]
        SourceIP = $hash["src-ip"]
        DestinationIP = $hash["dst-ip"]
        SourcePort = $hash["src-port"]
        DestinationPort = $hash["dst-port"]
        TcpFlags = $hash["tcpflags"]
    }
}

function Initialize-FirewallReader {
    if (-not (Test-Path $Script:FirewallLog)) {
        return
    }

    try {
        $header = Get-Content $Script:FirewallLog -TotalCount 30 -ErrorAction SilentlyContinue

        foreach ($line in $header) {
            if ($line.StartsWith("#Fields:")) {
                $Script:FirewallFields = $line.Substring(8).Trim() -split "\s+"
            }
        }

        $Script:FirewallOffset = (Get-Item $Script:FirewallLog).Length
        $Script:FirewallInitialized = $true
    } catch {
    }
}

function Read-NewFirewallRecords {
    if (-not (Test-Path $Script:FirewallLog)) {
        return
    }

    if (-not $Script:FirewallInitialized) {
        Initialize-FirewallReader
        return
    }

    try {
        $fileInfo = Get-Item $Script:FirewallLog

        if ($fileInfo.Length -lt $Script:FirewallOffset) {
            $Script:FirewallOffset = 0
        }

        if ($fileInfo.Length -eq $Script:FirewallOffset) {
            return
        }

        $fs = [System.IO.File]::Open(
            $Script:FirewallLog,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite
        )

        [void]$fs.Seek($Script:FirewallOffset, [System.IO.SeekOrigin]::Begin)
        $reader = New-Object System.IO.StreamReader($fs)

        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()
            $record = Convert-FirewallLine $line

            if ($record) {
                Add-TrafficRecord $record
            }
        }

        $reader.Close()
        $fs.Close()

        $Script:FirewallOffset = (Get-Item $Script:FirewallLog).Length
    } catch {
    }
}

function Add-TrafficRecord {
    param($Record)

    $src = $Record.SourceIP

    if (-not (Test-IPv4 $src)) {
        return
    }

    if ($src -eq $Script:LocalIP) {
        return
    }

    if (Test-IsMulticastOrSpecial $src) {
        return
    }

    if (-not $Script:Traffic.ContainsKey($src)) {
        $Script:Traffic[$src] = @()
    }

    $Script:Traffic[$src] += [pscustomobject]@{
        Time = $Record.Time
        Protocol = $Record.Protocol
        DestinationPort = $Record.DestinationPort
        Action = $Record.Action
        TcpFlags = $Record.TcpFlags
    }

    Evaluate-TrafficSource $src
}

function Evaluate-TrafficSource {
    param([string]$IP)

    $cutoff = (Get-Date).AddSeconds(-1 * [int]$Script:Settings.DetectionWindowSeconds)

    $recent = @(
        $Script:Traffic[$IP] |
            Where-Object { $_.Time -ge $cutoff }
    )

    $Script:Traffic[$IP] = $recent

    if ($recent.Count -eq 0) {
        return
    }

    $ports = @(
        $recent |
            Where-Object {
                $_.DestinationPort -and
                $_.DestinationPort -ne "-"
            } |
            ForEach-Object { $_.DestinationPort } |
            Sort-Object -Unique
    )

    $tcp = @($recent | Where-Object { $_.Protocol -eq "TCP" })
    $udp = @($recent | Where-Object { $_.Protocol -eq "UDP" })
    $icmp = @($recent | Where-Object { $_.Protocol -eq "ICMP" })

    $uniquePortCount = $ports.Count
    $attempts = $recent.Count

    $severity = $null
    $type = $null
    $confidence = 0.60

    if ($tcp.Count -gt 0 -and $uniquePortCount -ge [int]$Script:Settings.HighUniquePorts) {
        $severity = "HIGH"
        $type = "TCP port sweep"
        $confidence = 0.94
    } elseif ($tcp.Count -gt 0 -and $uniquePortCount -ge [int]$Script:Settings.MediumUniquePorts) {
        $severity = "MEDIUM"
        $type = "Podejrzane skanowanie TCP"
        $confidence = 0.85
    } elseif ($udp.Count -gt 0 -and $uniquePortCount -ge [int]$Script:Settings.MediumUniquePorts) {
        $severity = "MEDIUM"
        $type = "UDP port sweep"
        $confidence = 0.84
    } elseif ($icmp.Count -ge [int]$Script:Settings.IcmpBurstThreshold) {
        $severity = "MEDIUM"
        $type = "ICMP burst / sweep"
        $confidence = 0.76
    } elseif ($attempts -ge [int]$Script:Settings.RepeatedPortAttempts -and $uniquePortCount -le 3) {
        $severity = "MEDIUM"
        $type = "Powtarzane proby polaczenia"
        $confidence = 0.72
    }

    if (-not $type) {
        return
    }

    $key = "$IP|$type"

    if ($Script:LastAlert.ContainsKey($key)) {
        $age = (Get-Date) - $Script:LastAlert[$key]

        if ($age.TotalSeconds -lt [int]$Script:Settings.AlertCooldownSeconds) {
            return
        }
    }

    $Script:LastAlert[$key] = Get-Date

    $score = [Math]::Min(
        100,
        [int](($uniquePortCount * 2) + ($attempts / 2))
    )

    $portText = ($ports | Select-Object -First 25) -join ","

    if ($ports.Count -gt 25) {
        $portText += ",..."
    }

    Add-Alert `
        -Severity $severity `
        -Category "THREAT" `
        -SourceIP $IP `
        -Type $type `
        -Protocol (@($recent.Protocol | Sort-Object -Unique) -join ",") `
        -Ports $portText `
        -Attempts $attempts `
        -Score $score `
        -Confidence $confidence `
        -Note "Wzorzec ruchu charakterystyczny dla rekonesansu lub automatycznych prob."
}

# ============================================================
# ENGINE STATUS
# ============================================================

function Find-Tshark {
    $cmd = Get-Command tshark.exe -ErrorAction SilentlyContinue

    if ($cmd) {
        return $cmd.Source
    }

    $paths = @(
        "$env:ProgramFiles\Wireshark\tshark.exe",
        "${env:ProgramFiles(x86)}\Wireshark\tshark.exe"
    )

    foreach ($p in $paths) {
        if (Test-Path $p) {
            return $p
        }
    }

    return $null
}

function Get-NpcapStatus {
    $service = $null

    try {
        $service = Get-Service -Name npcap -ErrorAction SilentlyContinue
    } catch {
    }

    $dllPresent = (
        (Test-Path "$env:WINDIR\System32\Npcap\wpcap.dll") -or
        (Test-Path "$env:WINDIR\System32\Npcap\Packet.dll")
    )

    $installed = ($null -ne $service) -or $dllPresent

    $running = $false

    if ($service) {
        $running = ($service.Status -eq "Running")
    }

    return [pscustomobject]@{
        Installed = $installed
        Running = $running
        Service = $(if ($service) { $service.Status.ToString() } else { "BRAK" })
    }
}

function Get-EngineStatus {
    $npcap = Get-NpcapStatus
    $tshark = Find-Tshark
    $nmap = Find-Nmap
    $firewall = Test-FirewallLogging

    return [pscustomobject]@{
        NpcapInstalled = $npcap.Installed
        NpcapRunning = $npcap.Running
        NpcapService = $npcap.Service
        TShark = $tshark
        Nmap = $nmap
        FirewallLogging = $firewall
        Admin = $Script:IsAdmin
    }
}

# ============================================================
# DEEP PACKET CAPTURE
# ============================================================

function Start-DeepCapture {
    if (-not $Script:Settings.EnableDeepCapture) {
        return $false
    }

    if (-not $Script:IsAdmin) {
        $Script:CaptureLastError = "Deep Capture wymaga uruchomienia jako administrator."
        return $false
    }

    if ($Script:TsharkProcess) {
        try {
            if (-not $Script:TsharkProcess.HasExited) {
                return $true
            }
        } catch {
        }
    }

    $Script:TsharkPath = Find-Tshark

    if (-not $Script:TsharkPath) {
        $Script:CaptureLastError = "Brak TShark / Wireshark."
        return $false
    }

    $npcap = Get-NpcapStatus

    if (-not $npcap.Installed) {
        $Script:CaptureLastError = "Brak Npcap."
        return $false
    }

    if (-not $Script:SelectedAdapter) {
        $Script:CaptureLastError = "Nie wybrano interfejsu."
        return $false
    }

    try {
        Remove-Item $Script:ArpRawLog -Force -ErrorAction SilentlyContinue
        Remove-Item $Script:ArpErrorLog -Force -ErrorAction SilentlyContinue

        $guid = $Script:SelectedAdapter.Guid.ToString()
        $device = "\Device\NPF_{$guid}"

        $arguments = @(
            "-i", $device,
            "-l",
            "-n",
            "-f", "arp or tcp or udp or icmp",
            "-T", "fields",
            "-e", "frame.time_epoch",
            "-e", "eth.src",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "tcp.srcport",
            "-e", "tcp.dstport",
            "-e", "tcp.flags.syn",
            "-e", "tcp.flags.ack",
            "-e", "udp.srcport",
            "-e", "udp.dstport",
            "-e", "icmp.type",
            "-e", "arp.src.proto_ipv4",
            "-e", "arp.dst.proto_ipv4",
            "-E", "separator=|"
        )

        $Script:TsharkProcess = Start-Process `
            -FilePath $Script:TsharkPath `
            -ArgumentList $arguments `
            -PassThru `
            -WindowStyle Hidden `
            -RedirectStandardOutput $Script:ArpRawLog `
            -RedirectStandardError $Script:ArpErrorLog

        Start-Sleep -Milliseconds 500

        if ($Script:TsharkProcess.HasExited) {
            $Script:CaptureLastError = "TShark zakonczyl sie od razu. Sprawdz Npcap i interfejs."
            $Script:TsharkProcess = $null
            return $false
        }

        $Script:CaptureOffset = 0
        $Script:CapturePackets = 0
        $Script:CapturePacketsLast = 0
        $Script:CaptureLastRateTime = Get-Date
        $Script:CaptureLastError = ""

        return $true
    } catch {
        $Script:CaptureLastError = $_.Exception.Message
        $Script:TsharkProcess = $null
        return $false
    }
}

function Stop-DeepCapture {
    if (-not $Script:TsharkProcess) {
        return
    }

    try {
        if (-not $Script:TsharkProcess.HasExited) {
            $Script:TsharkProcess.Kill()
        }
    } catch {
    }

    $Script:TsharkProcess = $null
    $Script:CaptureRate = 0
}

function Add-PacketTraffic {
    param(
        [string]$SourceIP,
        [string]$Protocol,
        [string]$DestinationPort,
        [datetime]$Time
    )

    if (-not (Test-IPv4 $SourceIP)) {
        return
    }

    if ($SourceIP -eq $Script:LocalIP) {
        return
    }

    if (-not $Script:PacketTraffic.ContainsKey($SourceIP)) {
        $Script:PacketTraffic[$SourceIP] = @()
    }

    $Script:PacketTraffic[$SourceIP] += [pscustomobject]@{
        Time = $Time
        Protocol = $Protocol
        DestinationPort = $DestinationPort
        Action = "CAPTURE"
        TcpFlags = ""
    }

    # Uzywa tego samego silnika heurystyk.
    if (-not $Script:Traffic.ContainsKey($SourceIP)) {
        $Script:Traffic[$SourceIP] = @()
    }

    $Script:Traffic[$SourceIP] += [pscustomobject]@{
        Time = $Time
        Protocol = $Protocol
        DestinationPort = $DestinationPort
        Action = "CAPTURE"
        TcpFlags = ""
    }

    Evaluate-TrafficSource $SourceIP
}

function Evaluate-ArpSource {
    param([string]$IP)

    if (-not $Script:ArpActivity.ContainsKey($IP)) {
        return
    }

    $cut = (Get-Date).AddSeconds(-1 * [int]$Script:Settings.ArpWindowSeconds)

    $recent = @(
        $Script:ArpActivity[$IP] |
            Where-Object { $_.Time -ge $cut }
    )

    $Script:ArpActivity[$IP] = $recent

    $targets = @(
        $recent.Target |
            Where-Object { $_ } |
            Sort-Object -Unique
    )

    if ($targets.Count -lt [int]$Script:Settings.ArpSweepTargets) {
        return
    }

    $key = "$IP|ARP"

    if ($Script:LastAlert.ContainsKey($key)) {
        if (((Get-Date) - $Script:LastAlert[$key]).TotalSeconds -lt [int]$Script:Settings.AlertCooldownSeconds) {
            return
        }
    }

    $Script:LastAlert[$key] = Get-Date
    $mac = ($recent | Select-Object -First 1).Mac

    Add-Alert `
        -Severity "HIGH" `
        -Category "THREAT" `
        -SourceIP $IP `
        -SourceMac $mac `
        -Type "ARP sweep" `
        -Protocol "ARP" `
        -Attempts $recent.Count `
        -Score 90 `
        -Confidence 0.96 `
        -Note "$($targets.Count) roznych celow ARP w krotkim czasie."
}

function Read-DeepCapture {
    if (-not (Test-Path $Script:ArpRawLog)) {
        return
    }

    try {
        $info = Get-Item $Script:ArpRawLog

        if ($info.Length -lt $Script:CaptureOffset) {
            $Script:CaptureOffset = 0
        }

        if ($info.Length -eq $Script:CaptureOffset) {
            return
        }

        $fs = [System.IO.File]::Open(
            $Script:ArpRawLog,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite
        )

        [void]$fs.Seek($Script:CaptureOffset, [System.IO.SeekOrigin]::Begin)
        $reader = New-Object System.IO.StreamReader($fs)

        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()

            if (-not $line) {
                continue
            }

            $p = $line -split "\|", -1

            if ($p.Count -lt 13) {
                continue
            }

            $Script:CapturePackets++

            $ethSrc = Normalize-Mac $p[1]
            $ipSrc = $p[2]
            $ipDst = $p[3]
            $tcpDst = $p[5]
            $tcpSyn = $p[6]
            $tcpAck = $p[7]
            $udpDst = $p[9]
            $icmpType = $p[10]
            $arpSrc = $p[11]
            $arpDst = $p[12]

            $time = Get-Date

            if ($arpSrc -and $arpDst) {
                if ($arpSrc -ne $Script:LocalIP) {
                    if (-not $Script:ArpActivity.ContainsKey($arpSrc)) {
                        $Script:ArpActivity[$arpSrc] = @()
                    }

                    $Script:ArpActivity[$arpSrc] += [pscustomobject]@{
                        Time = $time
                        Mac = $ethSrc
                        Target = $arpDst
                    }

                    Evaluate-ArpSource $arpSrc
                }
            }

            if ($ipSrc -and $ipSrc -ne $Script:LocalIP) {
                if ($tcpDst) {
                    Add-PacketTraffic $ipSrc "TCP" $tcpDst $time
                } elseif ($udpDst) {
                    Add-PacketTraffic $ipSrc "UDP" $udpDst $time
                } elseif ($icmpType) {
                    Add-PacketTraffic $ipSrc "ICMP" "" $time
                }
            }
        }

        $reader.Close()
        $fs.Close()

        $Script:CaptureOffset = (Get-Item $Script:ArpRawLog).Length

        $elapsed = ((Get-Date) - $Script:CaptureLastRateTime).TotalSeconds

        if ($elapsed -ge 2) {
            $delta = $Script:CapturePackets - $Script:CapturePacketsLast
            $Script:CaptureRate = [math]::Round($delta / $elapsed, 1)
            $Script:CapturePacketsLast = $Script:CapturePackets
            $Script:CaptureLastRateTime = Get-Date
        }
    } catch {
    }
}

# ============================================================
# FIREWALL BLOCK
# ============================================================

function Test-SafeToBlock {
    param([string]$IP)

    if (-not (Test-IPv4 $IP)) {
        return $false
    }

    if ($IP -eq $Script:LocalIP) {
        return $false
    }

    if ($IP -eq $Script:GatewayIP) {
        return $false
    }

    if ($IP.StartsWith("127.")) {
        return $false
    }

    return $true
}

function Block-IP {
    param([string]$IP)

    if (-not $Script:IsAdmin) {
        [System.Windows.MessageBox]::Show(
            "Blokowanie wymaga trybu administratora.",
            "Network Sentinel"
        ) | Out-Null
        return
    }

    if (-not (Test-SafeToBlock $IP)) {
        [System.Windows.MessageBox]::Show(
            "Tego adresu Sentinel nie pozwala zablokowac.",
            "Network Sentinel"
        ) | Out-Null
        return
    }

    try {
        $inName = "Prestige Sentinel BLOCK IN $IP"
        $outName = "Prestige Sentinel BLOCK OUT $IP"

        if (-not (Get-NetFirewallRule -DisplayName $inName -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule `
                -DisplayName $inName `
                -Direction Inbound `
                -Action Block `
                -RemoteAddress $IP `
                -Profile Any `
                -Description "Prestige Tech Network Sentinel" |
                Out-Null
        }

        if (-not (Get-NetFirewallRule -DisplayName $outName -ErrorAction SilentlyContinue)) {
            New-NetFirewallRule `
                -DisplayName $outName `
                -Direction Outbound `
                -Action Block `
                -RemoteAddress $IP `
                -Profile Any `
                -Description "Prestige Tech Network Sentinel" |
                Out-Null
        }

        Add-Alert `
            -Severity "INFO" `
            -Category "SYSTEM" `
            -SourceIP $IP `
            -Type "Adres zablokowany" `
            -Protocol "FIREWALL" `
            -Confidence 1.0 `
            -Note "Inbound + outbound"
    } catch {
        [System.Windows.MessageBox]::Show(
            $_.Exception.Message,
            "Blad blokowania"
        ) | Out-Null
    }
}

function Unblock-IP {
    param([string]$IP)

    if (-not $Script:IsAdmin) {
        return
    }

    try {
        Get-NetFirewallRule `
            -DisplayName "Prestige Sentinel BLOCK IN $IP" `
            -ErrorAction SilentlyContinue |
            Remove-NetFirewallRule -ErrorAction SilentlyContinue

        Get-NetFirewallRule `
            -DisplayName "Prestige Sentinel BLOCK OUT $IP" `
            -ErrorAction SilentlyContinue |
            Remove-NetFirewallRule -ErrorAction SilentlyContinue

        Add-Alert `
            -Severity "INFO" `
            -Category "SYSTEM" `
            -SourceIP $IP `
            -Type "Adres odblokowany" `
            -Protocol "FIREWALL" `
            -Confidence 1.0
    } catch {
    }
}

# ============================================================
# NMAP BRIDGE
# ============================================================

function Send-SelectedToNmap {
    $d = $Script:DevicesGrid.SelectedItem

    if (-not $d) {
        return
    }

    $request = [pscustomobject]@{
        type = "nmap_target"
        target = $d.IP
        requestedBy = $Script:ModuleId
        timestamp = (Get-Date).ToString("o")
        requestId = [guid]::NewGuid().ToString()
    }

    Write-JsonAtomic $request $Script:NmapRequest

    Add-Alert `
        -Severity "INFO" `
        -Category "SYSTEM" `
        -SourceIP $d.IP `
        -Type "Przekazano host do Nmap" `
        -Protocol "BRIDGE" `
        -Confidence 1.0 `
        -Note $Script:NmapRequest
}

# ============================================================
# REPORT
# ============================================================

function Export-HtmlReport {
    $path = Join-Path $Script:Dirs.Reports (
        "Network-Sentinel-Report-" +
        (Get-Date -Format "yyyyMMdd-HHmmss") +
        ".html"
    )

    $engine = Get-EngineStatus

    $devicesHtml =
        @($Script:Devices) |
        Select-Object `
            RoleLabel,Name,IP,MAC,Vendor,Type,TypeConfidence,Status,Known,Trusted,New,FirstSeen,LastSeen |
        ConvertTo-Html -Fragment

    $alertsHtml =
        @($Script:Alerts) |
        Select-Object `
            Time,Severity,Category,SourceIP,SourceMac,Type,Protocol,Ports,Attempts,Score,Confidence,Note |
        ConvertTo-Html -Fragment

    $html = @"
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Prestige Tech Network Sentinel</title>
<style>
body{font-family:Segoe UI,Arial;background:#08101d;color:#e7edf7;margin:30px}
h1{color:#f5b700} h2{margin-top:30px}
.card{background:#111b2d;border:1px solid #25344d;border-radius:12px;padding:18px;margin:12px 0}
table{border-collapse:collapse;width:100%;background:#0e1727}
th{background:#17243a;color:#f5b700}
td,th{border:1px solid #25344d;padding:7px;text-align:left}
.good{color:#31c48d}.warn{color:#f5b700}.bad{color:#ff6b6b}
</style>
</head>
<body>
<h1>PRESTIGE TECH | NETWORK SENTINEL</h1>

<div class="card">
<b>Wersja:</b> $($Script:Version)<br>
<b>Raport:</b> $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")<br>
<b>Interfejs:</b> $($Script:SelectedAdapter.Name)<br>
<b>Siec:</b> $($Script:LocalIP)/$($Script:PrefixLength)<br>
<b>Gateway:</b> $($Script:GatewayIP)<br>
<b>Admin:</b> $($engine.Admin)<br>
<b>Npcap:</b> $($engine.NpcapInstalled) / running $($engine.NpcapRunning)<br>
<b>TShark:</b> $($engine.TShark)<br>
<b>Nmap:</b> $($engine.Nmap)<br>
<b>Firewall logging:</b> $($engine.FirewallLogging)<br>
<b>Capture packets:</b> $($Script:CapturePackets)<br>
</div>

<h2>Urzadzenia</h2>
$devicesHtml

<h2>Alerty</h2>
$alertsHtml

</body>
</html>
"@

    $html | Set-Content $path -Encoding UTF8
    Start-Process $path
}

# ============================================================
# AUTOSTART
# ============================================================

function Register-UserAutostart {
    if (-not $PSCommandPath) {
        return
    }

    try {
        $runPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
        $cmd = "powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File `"$PSCommandPath`""

        New-ItemProperty `
            -Path $runPath `
            -Name "PrestigeTechNetworkSentinel" `
            -Value $cmd `
            -PropertyType String `
            -Force |
            Out-Null

        [System.Windows.MessageBox]::Show(
            "Dodano zwykly autostart dla aktualnego uzytkownika.",
            "Network Sentinel"
        ) | Out-Null
    } catch {
        [System.Windows.MessageBox]::Show(
            $_.Exception.Message,
            "Autostart"
        ) | Out-Null
    }
}

function Register-AdminAutostartTask {
    if (-not $Script:IsAdmin) {
        [System.Windows.MessageBox]::Show(
            "Pelny autostart ADMIN wymaga uruchomienia Sentinela jako administrator.",
            "Network Sentinel"
        ) | Out-Null
        return
    }

    if (-not $PSCommandPath) {
        return
    }

    try {
        $action = New-ScheduledTaskAction `
            -Execute "powershell.exe" `
            -Argument "-NoProfile -STA -ExecutionPolicy Bypass -File `"$PSCommandPath`""

        $trigger = New-ScheduledTaskTrigger -AtLogOn

        $principal = New-ScheduledTaskPrincipal `
            -UserId $env:USERNAME `
            -LogonType Interactive `
            -RunLevel Highest

        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries

        Register-ScheduledTask `
            -TaskName "Prestige Tech Network Sentinel" `
            -Action $action `
            -Trigger $trigger `
            -Principal $principal `
            -Settings $settings `
            -Force |
            Out-Null

        [System.Windows.MessageBox]::Show(
            "Dodano autostart ADMIN w Harmonogramie zadan Windows.",
            "Network Sentinel"
        ) | Out-Null
    } catch {
        [System.Windows.MessageBox]::Show(
            $_.Exception.Message,
            "Autostart ADMIN"
        ) | Out-Null
    }
}

# ============================================================
# ADMIN RESTART
# ============================================================

function Restart-AsAdministrator {
    if ($Script:IsAdmin) {
        return
    }

    $arguments = @(
        "-NoProfile",
        "-STA",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`""
    )

    if ($DashboardRoot) {
        $arguments += @("-DashboardRoot", "`"$DashboardRoot`"")
    }

    if ($BridgeDir) {
        $arguments += @("-BridgeDir", "`"$BridgeDir`"")
    }

    Start-Process powershell.exe -Verb RunAs -ArgumentList $arguments
    $Script:Window.Close()
}

# ============================================================
# DASHBOARD STATUS
# ============================================================

function Write-DashboardStatus {
    $threats = @(
        $Script:Alerts |
            Where-Object {
                $_.Category -eq "THREAT" -and
                $_.Severity -in @("MEDIUM","HIGH","CRITICAL")
            }
    ).Count

    $newDevices = @(
        $Script:DeviceState.Values |
            Where-Object { $_.New -eq $true -and $_.Status -eq "ONLINE" }
    ).Count

    $online = @(
        $Script:DeviceState.Values |
            Where-Object { $_.Status -eq "ONLINE" }
    ).Count

    $captureActive = $false

    if ($Script:TsharkProcess) {
        try {
            $captureActive = -not $Script:TsharkProcess.HasExited
        } catch {
        }
    }

    $status = [pscustomobject]@{
        module = $Script:ModuleId
        version = $Script:Version
        running = $Script:Running
        admin = $Script:IsAdmin
        timestamp = (Get-Date).ToString("o")
        interface = $(if ($Script:SelectedAdapter) { $Script:SelectedAdapter.Name } else { "" })
        ip = $Script:LocalIP
        gateway = $Script:GatewayIP
        onlineDevices = $online
        newDevices = $newDevices
        threats = $threats
        alertCount = $Script:Alerts.Count
        lastScan = $(if ($Script:LastScan) { $Script:LastScan.ToString("o") } else { $null })
        nextScan = $(if ($Script:NextScan) { $Script:NextScan.ToString("o") } else { $null })
        deepCapture = $captureActive
        capturePackets = $Script:CapturePackets
        captureRate = $Script:CaptureRate
        bridgeVersion = 2
    }

    Write-JsonAtomic $status $Script:StatusFile
}

# ============================================================
# MONITORING
# ============================================================

function Start-Monitoring {
    if ($Script:Running) {
        return
    }

    if (-not $Script:SelectedAdapter) {
        [System.Windows.MessageBox]::Show(
            "Najpierw wybierz interfejs sieciowy.",
            "Network Sentinel"
        ) | Out-Null
        return
    }

    $Script:Running = $true

    if ($Script:IsAdmin -and $Script:Settings.EnableFirewallLogging) {
        Enable-FirewallLogging | Out-Null
    }

    Initialize-FirewallReader
    Refresh-LocalAndGateway

    if ($Script:IsAdmin -and $Script:Settings.EnableDeepCapture) {
        Start-DeepCapture | Out-Null
    }

    if ($Script:Settings.ScanOnStart) {
        Invoke-DiscoveryScan
    }

    if ($Script:Settings.ScheduleEnabled) {
        if (-not $Script:LastScan) {
            $Script:NextScan = (Get-Date)
        } else {
            $Script:NextScan = $Script:LastScan.AddMinutes([int]$Script:Settings.ScanIntervalMinutes)
        }
    }

    Add-Alert `
        -Severity "INFO" `
        -Category "SYSTEM" `
        -SourceIP $Script:LocalIP `
        -Type "Monitoring uruchomiony" `
        -Protocol "SYSTEM" `
        -Confidence 1.0

    Update-UIStatus
}

function Stop-Monitoring {
    if (-not $Script:Running) {
        return
    }

    $Script:Running = $false
    $Script:NextScan = $null

    Stop-DeepCapture

    Add-Alert `
        -Severity "INFO" `
        -Category "SYSTEM" `
        -SourceIP $Script:LocalIP `
        -Type "Monitoring zatrzymany" `
        -Protocol "SYSTEM" `
        -Confidence 1.0

    Update-UIStatus
    Write-DashboardStatus
}

function Poll-Sentinel {
    if ($Script:Running) {
        Read-NewFirewallRecords
        Read-DeepCapture

        if (
            $Script:Settings.ScheduleEnabled -and
            $Script:NextScan -and
            (Get-Date) -ge $Script:NextScan -and
            -not $Script:ScanInProgress
        ) {
            Invoke-DiscoveryScan
        }
    }

    if (((Get-Date) - $Script:LastStatusWrite).TotalSeconds -ge 3) {
        Write-DashboardStatus
        $Script:LastStatusWrite = Get-Date
    }

    Update-UIStatus
}

# ============================================================
# FIRST RUN
# ============================================================

function Show-FirstRunInfo {
    if ($Script:Settings.FirstRunCompleted) {
        return
    }

    $msg = @"
NETWORK SENTINEL v2

1. Wybierz prawdziwy interfejs Wi-Fi lub Ethernet.
2. Dla pelnych funkcji kliknij "Uruchom jako ADMIN".
3. Zakladka SILNIK pokazuje Npcap, TShark, Nmap i Firewall.
4. Kliknij ROZPOCZNIJ MONITORING.
5. Kliknij SKANUJ TERAZ, jesli chcesz od razu odswiezyc LAN.
6. Harmonogram aktywnego skanu ustawisz w USTAWIENIACH.
7. TEN KOMPUTER i ROUTER / BRAMA sa oznaczane osobno.
8. Broadcast i wirtualne interfejsy sa domyslnie filtrowane.
"@

    [System.Windows.MessageBox]::Show(
        $msg,
        "Pierwsze uruchomienie"
    ) | Out-Null

    $Script:Settings.FirstRunCompleted = $true
    Save-Settings
}

# ============================================================
# GUI XAML
# ============================================================

[xml]$xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Prestige Tech - Network Sentinel"
    Width="1550"
    Height="930"
    MinWidth="1250"
    MinHeight="760"
    Background="#070D17"
    Foreground="#E8EEF7"
    WindowStartupLocation="CenterScreen">

<Window.Resources>

    <Style x:Key="MainButton" TargetType="Button">
        <Setter Property="Foreground" Value="#F8FAFC"/>
        <Setter Property="Background" Value="#142037"/>
        <Setter Property="BorderBrush" Value="#2A3B59"/>
        <Setter Property="BorderThickness" Value="1"/>
        <Setter Property="Padding" Value="15,9"/>
        <Setter Property="Margin" Value="4"/>
        <Setter Property="Cursor" Value="Hand"/>
        <Setter Property="FontWeight" Value="SemiBold"/>
        <Setter Property="Template">
            <Setter.Value>
                <ControlTemplate TargetType="Button">
                    <Border
                        Background="{TemplateBinding Background}"
                        BorderBrush="{TemplateBinding BorderBrush}"
                        BorderThickness="{TemplateBinding BorderThickness}"
                        CornerRadius="8">
                        <ContentPresenter
                            HorizontalAlignment="Center"
                            VerticalAlignment="Center"/>
                    </Border>
                </ControlTemplate>
            </Setter.Value>
        </Setter>
    </Style>

    <Style x:Key="PrimaryButton" TargetType="Button" BasedOn="{StaticResource MainButton}">
        <Setter Property="Background" Value="#0C6B51"/>
        <Setter Property="BorderBrush" Value="#15A879"/>
        <Setter Property="FontSize" Value="15"/>
        <Setter Property="Padding" Value="22,11"/>
    </Style>

    <Style x:Key="DangerButton" TargetType="Button" BasedOn="{StaticResource MainButton}">
        <Setter Property="Background" Value="#74242A"/>
        <Setter Property="BorderBrush" Value="#A63E46"/>
    </Style>

    <Style TargetType="DataGrid">
        <Setter Property="Background" Value="#0B1423"/>
        <Setter Property="Foreground" Value="#E8EEF7"/>
        <Setter Property="BorderBrush" Value="#263650"/>
        <Setter Property="GridLinesVisibility" Value="Horizontal"/>
        <Setter Property="HorizontalGridLinesBrush" Value="#1F2E45"/>
        <Setter Property="RowBackground" Value="#0B1423"/>
        <Setter Property="AlternatingRowBackground" Value="#101B2D"/>
        <Setter Property="HeadersVisibility" Value="Column"/>
        <Setter Property="CanUserAddRows" Value="False"/>
        <Setter Property="IsReadOnly" Value="True"/>
        <Setter Property="SelectionMode" Value="Single"/>
        <Setter Property="AutoGenerateColumns" Value="False"/>
        <Setter Property="RowHeight" Value="30"/>
    </Style>

    <Style TargetType="DataGridColumnHeader">
        <Setter Property="Background" Value="#17243A"/>
        <Setter Property="Foreground" Value="#F5B700"/>
        <Setter Property="FontWeight" Value="SemiBold"/>
        <Setter Property="Padding" Value="8"/>
    </Style>

    <Style TargetType="TabItem">
        <Setter Property="Foreground" Value="#D6DFEC"/>
        <Setter Property="Background" Value="#101A2A"/>
        <Setter Property="Padding" Value="18,9"/>
        <Setter Property="Margin" Value="2"/>
        <Setter Property="FontWeight" Value="SemiBold"/>
    </Style>

    <Style TargetType="ComboBox">
        <Setter Property="Background" Value="#111C2F"/>
        <Setter Property="Foreground" Value="#F1F5F9"/>
        <Setter Property="BorderBrush" Value="#31435F"/>
        <Setter Property="Padding" Value="8,5"/>
        <Setter Property="Margin" Value="4"/>
    </Style>

    <Style TargetType="CheckBox">
        <Setter Property="Foreground" Value="#E8EEF7"/>
        <Setter Property="Margin" Value="4,7"/>
    </Style>

    <Style TargetType="TextBox">
        <Setter Property="Background" Value="#0C1626"/>
        <Setter Property="Foreground" Value="#F8FAFC"/>
        <Setter Property="BorderBrush" Value="#31435F"/>
        <Setter Property="Padding" Value="7"/>
    </Style>

</Window.Resources>

<Grid Margin="18">

<Grid.RowDefinitions>
    <RowDefinition Height="Auto"/>
    <RowDefinition Height="Auto"/>
    <RowDefinition Height="Auto"/>
    <RowDefinition Height="*"/>
    <RowDefinition Height="Auto"/>
</Grid.RowDefinitions>

<!-- HEADER -->
<Grid Grid.Row="0">
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="*"/>
    <ColumnDefinition Width="Auto"/>
</Grid.ColumnDefinitions>

<StackPanel>
    <TextBlock
        Text="PRESTIGE TECH"
        Foreground="#F5B700"
        FontSize="13"
        FontWeight="Bold"/>

    <TextBlock
        Text="NETWORK SENTINEL"
        FontSize="30"
        FontWeight="Bold"
        Margin="0,2,0,0"/>

    <TextBlock
        Name="TxtNetworkSummary"
        Foreground="#9DB0C9"
        Margin="0,4,0,0"/>
</StackPanel>

<StackPanel Grid.Column="1" Orientation="Horizontal" VerticalAlignment="Center">
    <StackPanel Margin="0,0,12,0">
        <TextBlock Text="MONITOROWANY INTERFEJS" Foreground="#8194AE" FontSize="11"/>
        <ComboBox Name="AdapterCombo" Width="320"/>
    </StackPanel>

    <TextBlock
        Name="TxtAdminHeader"
        VerticalAlignment="Center"
        Margin="8"/>

    <Button
        Name="BtnAdmin"
        Content="URUCHOM JAKO ADMIN"
        Style="{StaticResource MainButton}"/>
</StackPanel>
</Grid>

<!-- CONTROL BAR -->
<Grid Grid.Row="1" Margin="0,16,0,12">
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="Auto"/>
    <ColumnDefinition Width="Auto"/>
    <ColumnDefinition Width="Auto"/>
    <ColumnDefinition Width="*"/>
    <ColumnDefinition Width="Auto"/>
</Grid.ColumnDefinitions>

<Button
    Grid.Column="0"
    Name="BtnStart"
    Content="ROZPOCZNIJ MONITORING"
    Style="{StaticResource PrimaryButton}"
    Width="230"/>

<Button
    Grid.Column="1"
    Name="BtnStop"
    Content="ZATRZYMAJ"
    Style="{StaticResource DangerButton}"
    Width="120"/>

<Button
    Grid.Column="2"
    Name="BtnScan"
    Content="SKANUJ SIEC TERAZ"
    Style="{StaticResource MainButton}"
    Width="175"/>

<TextBlock
    Grid.Column="3"
    Name="TxtModeMessage"
    VerticalAlignment="Center"
    Foreground="#9DB0C9"
    Margin="14,0"/>

<TextBlock
    Grid.Column="4"
    Name="TxtUptime"
    VerticalAlignment="Center"
    Foreground="#9DB0C9"/>
</Grid>

<!-- CARDS -->
<Grid Grid.Row="2" Margin="0,0,0,14">
<Grid.ColumnDefinitions>
    <ColumnDefinition/>
    <ColumnDefinition/>
    <ColumnDefinition/>
    <ColumnDefinition/>
    <ColumnDefinition/>
    <ColumnDefinition/>
</Grid.ColumnDefinitions>

<Border Grid.Column="0" Background="#101A2A" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Margin="4" Padding="15">
<StackPanel>
    <TextBlock Text="STATUS" Foreground="#84A0C2"/>
    <TextBlock Name="TxtStatus" Text="NIEAKTYWNY" FontSize="20" FontWeight="Bold"/>
</StackPanel>
</Border>

<Border Grid.Column="1" Background="#101A2A" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Margin="4" Padding="15">
<StackPanel>
    <TextBlock Text="ONLINE" Foreground="#84A0C2"/>
    <TextBlock Name="TxtOnline" Text="0" FontSize="20" FontWeight="Bold"/>
</StackPanel>
</Border>

<Border Grid.Column="2" Background="#101A2A" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Margin="4" Padding="15">
<StackPanel>
    <TextBlock Text="NOWE" Foreground="#84A0C2"/>
    <TextBlock Name="TxtNew" Text="0" FontSize="20" FontWeight="Bold" Foreground="#F5B700"/>
</StackPanel>
</Border>

<Border Grid.Column="3" Background="#101A2A" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Margin="4" Padding="15">
<StackPanel>
    <TextBlock Text="ZAGROZENIA" Foreground="#84A0C2"/>
    <TextBlock Name="TxtThreats" Text="0" FontSize="20" FontWeight="Bold" Foreground="#FF6B6B"/>
</StackPanel>
</Border>

<Border Grid.Column="4" Background="#101A2A" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Margin="4" Padding="15">
<StackPanel>
    <TextBlock Text="OSTATNI SKAN" Foreground="#84A0C2"/>
    <TextBlock Name="TxtLastScan" Text="BRAK" FontSize="16" FontWeight="Bold"/>
</StackPanel>
</Border>

<Border Grid.Column="5" Background="#101A2A" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Margin="4" Padding="15">
<StackPanel>
    <TextBlock Text="DEEP CAPTURE" Foreground="#84A0C2"/>
    <TextBlock Name="TxtCapture" Text="OFF" FontSize="16" FontWeight="Bold"/>
    <TextBlock Name="TxtPps" Text="0 pak/s" Foreground="#9DB0C9" FontSize="11"/>
</StackPanel>
</Border>
</Grid>

<!-- TABS -->
<TabControl
    Grid.Row="3"
    Name="MainTabs"
    Background="#070D17"
    BorderBrush="#263650">

<!-- OVERVIEW -->
<TabItem Header="PULPIT">
<Grid Margin="8">
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="1.15*"/>
    <ColumnDefinition Width="0.85*"/>
</Grid.ColumnDefinitions>

<StackPanel Grid.Column="0" Margin="6">

<Border Background="#0E1828" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Padding="18" Margin="0,0,0,12">
<StackPanel>
    <TextBlock Text="TOPOLOGIA I IDENTYFIKACJA" Foreground="#F5B700" FontWeight="Bold" FontSize="14"/>
    <TextBlock Name="TxtTopology" FontFamily="Consolas" FontSize="15" Margin="0,12,0,0" TextWrapping="Wrap"/>
</StackPanel>
</Border>

<Border Background="#0E1828" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Padding="18">
<StackPanel>
    <TextBlock Text="HARMONOGRAM" Foreground="#F5B700" FontWeight="Bold" FontSize="14"/>
    <TextBlock Name="TxtScheduleSummary" Margin="0,10,0,0" Foreground="#D6DFEC"/>
    <TextBlock Name="TxtNextScan" Margin="0,6,0,0" Foreground="#9DB0C9"/>
</StackPanel>
</Border>

</StackPanel>

<StackPanel Grid.Column="1" Margin="6">

<Border Background="#0E1828" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Padding="18" Margin="0,0,0,12">
<StackPanel>
    <TextBlock Text="TRYB PRACY" Foreground="#F5B700" FontWeight="Bold" FontSize="14"/>
    <TextBlock Name="TxtModeLarge" FontSize="18" FontWeight="Bold" Margin="0,10,0,0"/>
    <TextBlock Name="TxtModeDetails" TextWrapping="Wrap" Foreground="#AFC0D6" Margin="0,8,0,0"/>
</StackPanel>
</Border>

<Border Background="#0E1828" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Padding="18">
<StackPanel>
    <TextBlock Text="OSTATNIE ZDARZENIE" Foreground="#F5B700" FontWeight="Bold" FontSize="14"/>
    <TextBlock Name="TxtLastEvent" TextWrapping="Wrap" Margin="0,10,0,0"/>
</StackPanel>
</Border>

</StackPanel>
</Grid>
</TabItem>

<!-- DEVICES -->
<TabItem Header="URZADZENIA">
<Grid Margin="8">
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="*"/>
    <ColumnDefinition Width="350"/>
</Grid.ColumnDefinitions>

<DataGrid Name="DevicesGrid" Grid.Column="0">
<DataGrid.Columns>
    <DataGridTextColumn Header="ROLA" Binding="{Binding RoleLabel}" Width="125"/>
    <DataGridTextColumn Header="NAZWA" Binding="{Binding Name}" Width="190"/>
    <DataGridTextColumn Header="IP" Binding="{Binding IP}" Width="120"/>
    <DataGridTextColumn Header="MAC" Binding="{Binding MAC}" Width="145"/>
    <DataGridTextColumn Header="PRODUCENT" Binding="{Binding Vendor}" Width="210"/>
    <DataGridTextColumn Header="TYP" Binding="{Binding Type}" Width="180"/>
    <DataGridTextColumn Header="PEWNOSC" Binding="{Binding TypeConfidence}" Width="80"/>
    <DataGridTextColumn Header="STATUS" Binding="{Binding Status}" Width="85"/>
    <DataGridCheckBoxColumn Header="ZNANE" Binding="{Binding Known}" Width="65"/>
    <DataGridCheckBoxColumn Header="TRUST" Binding="{Binding Trusted}" Width="65"/>
    <DataGridCheckBoxColumn Header="NOWE" Binding="{Binding New}" Width="65"/>
    <DataGridTextColumn Header="OSTATNIO" Binding="{Binding LastSeen}" Width="150"/>
</DataGrid.Columns>
</DataGrid>

<Border Grid.Column="1" Background="#0E1828" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Padding="16" Margin="12,0,0,0">
<StackPanel>
    <TextBlock Text="SZCZEGOLY URZADZENIA" Foreground="#F5B700" FontWeight="Bold" FontSize="14"/>
    <TextBlock Name="TxtDetailRole" FontSize="17" FontWeight="Bold" Margin="0,12,0,0"/>
    <TextBlock Name="TxtDetailName" FontSize="21" FontWeight="Bold" Margin="0,3,0,12"/>
    <TextBlock Name="TxtDetailIP" Margin="0,3"/>
    <TextBlock Name="TxtDetailMAC" Margin="0,3"/>
    <TextBlock Name="TxtDetailVendor" TextWrapping="Wrap" Margin="0,3"/>
    <TextBlock Name="TxtDetailType" TextWrapping="Wrap" Margin="0,3"/>
    <TextBlock Name="TxtDetailStatus" Margin="0,3"/>
    <TextBlock Name="TxtDetailFirst" Margin="0,3"/>
    <TextBlock Name="TxtDetailLast" Margin="0,3"/>

    <Separator Margin="0,12"/>

    <Button Name="BtnKnown" Content="OZNACZ JAKO ZNANE" Style="{StaticResource MainButton}"/>
    <Button Name="BtnTrust" Content="DODAJ DO ZAUFANYCH" Style="{StaticResource MainButton}"/>
    <Button Name="BtnUntrust" Content="USUN Z ZAUFANYCH" Style="{StaticResource MainButton}"/>
    <Button Name="BtnNmap" Content="WYSLIJ DO NMAP" Style="{StaticResource MainButton}" Background="#1D4ED8"/>
    <Button Name="BtnBlock" Content="BLOKUJ IP" Style="{StaticResource DangerButton}"/>
    <Button Name="BtnUnblock" Content="ODBLOKUJ IP" Style="{StaticResource MainButton}"/>
</StackPanel>
</Border>

</Grid>
</TabItem>

<!-- ALERTS -->
<TabItem Header="ALERTY">
<Grid Margin="8">
<DataGrid Name="AlertsGrid">
<DataGrid.Columns>
    <DataGridTextColumn Header="CZAS" Binding="{Binding Time}" Width="145"/>
    <DataGridTextColumn Header="KAT." Binding="{Binding Category}" Width="85"/>
    <DataGridTextColumn Header="POZIOM" Binding="{Binding Severity}" Width="85"/>
    <DataGridTextColumn Header="ZRODLO" Binding="{Binding SourceIP}" Width="120"/>
    <DataGridTextColumn Header="MAC" Binding="{Binding SourceMac}" Width="145"/>
    <DataGridTextColumn Header="TYP" Binding="{Binding Type}" Width="210"/>
    <DataGridTextColumn Header="PROTO" Binding="{Binding Protocol}" Width="80"/>
    <DataGridTextColumn Header="PORTY" Binding="{Binding Ports}" Width="*"/>
    <DataGridTextColumn Header="PROBY" Binding="{Binding Attempts}" Width="65"/>
    <DataGridTextColumn Header="SCORE" Binding="{Binding Score}" Width="65"/>
    <DataGridTextColumn Header="PEWNOSC" Binding="{Binding Confidence}" Width="80"/>
</DataGrid.Columns>
</DataGrid>
</Grid>
</TabItem>

<!-- HISTORY -->
<TabItem Header="HISTORIA">
<Grid Margin="8">
<DataGrid Name="HistoryGrid">
<DataGrid.Columns>
    <DataGridTextColumn Header="CZAS" Binding="{Binding Time}" Width="155"/>
    <DataGridTextColumn Header="IP" Binding="{Binding IP}" Width="120"/>
    <DataGridTextColumn Header="ZDARZENIE" Binding="{Binding Event}" Width="220"/>
    <DataGridTextColumn Header="SZCZEGOLY" Binding="{Binding Details}" Width="*"/>
</DataGrid.Columns>
</DataGrid>
</Grid>
</TabItem>

<!-- ENGINE -->
<TabItem Header="SILNIK">
<Grid Margin="14">
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="1.1*"/>
    <ColumnDefinition Width="0.9*"/>
</Grid.ColumnDefinitions>

<StackPanel Grid.Column="0" Margin="4">

<TextBlock Text="STAN SILNIKA" Foreground="#F5B700" FontWeight="Bold" FontSize="16"/>

<Border Background="#0E1828" BorderBrush="#263650" BorderThickness="1" CornerRadius="10" Padding="18" Margin="0,12,0,8">
<Grid>
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="190"/>
    <ColumnDefinition Width="*"/>
</Grid.ColumnDefinitions>
<Grid.RowDefinitions>
    <RowDefinition Height="Auto"/>
    <RowDefinition Height="Auto"/>
    <RowDefinition Height="Auto"/>
    <RowDefinition Height="Auto"/>
    <RowDefinition Height="Auto"/>
    <RowDefinition Height="Auto"/>
</Grid.RowDefinitions>

<TextBlock Grid.Row="0" Text="Administrator"/>
<TextBlock Grid.Row="0" Grid.Column="1" Name="TxtEngineAdmin" FontWeight="Bold"/>

<TextBlock Grid.Row="1" Text="Npcap"/>
<TextBlock Grid.Row="1" Grid.Column="1" Name="TxtEngineNpcap" FontWeight="Bold"/>

<TextBlock Grid.Row="2" Text="TShark"/>
<TextBlock Grid.Row="2" Grid.Column="1" Name="TxtEngineTshark" FontWeight="Bold"/>

<TextBlock Grid.Row="3" Text="Nmap"/>
<TextBlock Grid.Row="3" Grid.Column="1" Name="TxtEngineNmap" FontWeight="Bold"/>

<TextBlock Grid.Row="4" Text="Firewall logging"/>
<TextBlock Grid.Row="4" Grid.Column="1" Name="TxtEngineFirewall" FontWeight="Bold"/>

<TextBlock Grid.Row="5" Text="Packet capture"/>
<TextBlock Grid.Row="5" Grid.Column="1" Name="TxtEngineCapture" FontWeight="Bold"/>

</Grid>
</Border>

<WrapPanel>
    <Button Name="BtnEngineRefresh" Content="ODSWIEZ STAN" Style="{StaticResource MainButton}"/>
    <Button Name="BtnEnableFirewall" Content="WLACZ FIREWALL LOG" Style="{StaticResource MainButton}"/>
    <Button Name="BtnCaptureRestart" Content="RESTART CAPTURE" Style="{StaticResource MainButton}"/>
</WrapPanel>

<TextBlock Name="TxtEngineMessage" Foreground="#AFC0D6" TextWrapping="Wrap" Margin="4,12"/>

</StackPanel>

<StackPanel Grid.Column="1" Margin="18,4,4,4">

<TextBlock Text="ZALEZNOSCI" Foreground="#F5B700" FontWeight="Bold" FontSize="16"/>

<TextBlock
    Text="Pelny tryb monitoringu pakietow wymaga Npcap oraz TShark. Nmap jest opcjonalny i moze pomoc w aktywnym discovery."
    TextWrapping="Wrap"
    Foreground="#AFC0D6"
    Margin="0,12,0,12"/>

<Button Name="BtnNpcapWeb" Content="OTWORZ POBIERANIE NPCAP" Style="{StaticResource MainButton}"/>
<Button Name="BtnWiresharkWeb" Content="OTWORZ POBIERANIE WIRESHARK" Style="{StaticResource MainButton}"/>
<Button Name="BtnNmapWeb" Content="OTWORZ POBIERANIE NMAP" Style="{StaticResource MainButton}"/>
<Button Name="BtnOuiUpdate" Content="AKTUALIZUJ BAZE PRODUCENTOW IEEE OUI" Style="{StaticResource MainButton}"/>
<Button Name="BtnDataFolder" Content="OTWORZ FOLDER DANYCH SENTINELA" Style="{StaticResource MainButton}"/>

</StackPanel>
</Grid>
</TabItem>

<!-- SETTINGS -->
<TabItem Header="USTAWIENIA">
<Grid Margin="14">
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="1*"/>
    <ColumnDefinition Width="1*"/>
</Grid.ColumnDefinitions>

<StackPanel Grid.Column="0" Margin="5">
<TextBlock Text="SKANOWANIE I MONITORING" Foreground="#F5B700" FontWeight="Bold" FontSize="16"/>

<CheckBox Name="ChkSchedule" Content="Automatyczne aktywne odswiezanie urzadzen"/>
<StackPanel Orientation="Horizontal">
    <TextBlock Text="Skanuj co:" VerticalAlignment="Center" Width="100"/>
    <ComboBox Name="CmbInterval" Width="160">
        <ComboBoxItem Content="1 minuta" Tag="1"/>
        <ComboBoxItem Content="5 minut" Tag="5"/>
        <ComboBoxItem Content="10 minut" Tag="10"/>
        <ComboBoxItem Content="15 minut" Tag="15"/>
        <ComboBoxItem Content="30 minut" Tag="30"/>
        <ComboBoxItem Content="60 minut" Tag="60"/>
    </ComboBox>
</StackPanel>

<CheckBox Name="ChkScanOnStart" Content="Skanuj siec po rozpoczeciu monitoringu"/>
<CheckBox Name="ChkResolveNames" Content="Rozpoznawaj nazwy hostow przez reverse DNS"/>
<CheckBox Name="ChkDeepCapture" Content="Wlacz Deep Capture przez TShark + Npcap"/>
<CheckBox Name="ChkFirewallLog" Content="Wlacz logowanie zablokowanych polaczen Windows Firewall"/>
<CheckBox Name="ChkNmapDiscovery" Content="Uzywaj dodatkowo Nmap do discovery, jesli jest zainstalowany"/>
<CheckBox Name="ChkVirtual" Content="Pokazuj wirtualne interfejsy sieciowe"/>

<Button Name="BtnSaveSettings" Content="ZAPISZ USTAWIENIA" Style="{StaticResource PrimaryButton}" Width="220" Margin="4,15,4,4"/>
</StackPanel>

<StackPanel Grid.Column="1" Margin="25,5,5,5">
<TextBlock Text="AUTOSTART I RAPORTY" Foreground="#F5B700" FontWeight="Bold" FontSize="16"/>

<TextBlock
    Text="Zwykly autostart nie podnosi uprawnien. Pelny autostart ADMIN tworzy zadanie Windows Task Scheduler z najwyzszymi uprawnieniami."
    TextWrapping="Wrap"
    Foreground="#AFC0D6"
    Margin="0,12,0,12"/>

<Button Name="BtnAutoUser" Content="AUTOSTART ZWYKLY" Style="{StaticResource MainButton}"/>
<Button Name="BtnAutoAdmin" Content="AUTOSTART PELNY ADMIN" Style="{StaticResource MainButton}"/>
<Button Name="BtnReport" Content="GENERUJ RAPORT HTML" Style="{StaticResource MainButton}"/>
<Button Name="BtnClearAlerts" Content="WYCZYSC WIDOK ALERTOW" Style="{StaticResource MainButton}"/>
</StackPanel>
</Grid>
</TabItem>

</TabControl>

<!-- FOOTER -->
<Grid Grid.Row="4" Margin="0,10,0,0">
<Grid.ColumnDefinitions>
    <ColumnDefinition Width="*"/>
    <ColumnDefinition Width="Auto"/>
</Grid.ColumnDefinitions>

<TextBlock
    Name="TxtFooter"
    Foreground="#71839B"
    VerticalAlignment="Center"/>

<TextBlock
    Grid.Column="1"
    Text="Prestige Tech | Network Sentinel v2.0"
    Foreground="#71839B"
    VerticalAlignment="Center"/>
</Grid>

</Grid>
</Window>
"@

$reader = New-Object System.Xml.XmlNodeReader $xaml
$Script:Window = [Windows.Markup.XamlReader]::Load($reader)

# ============================================================
# GUI REFERENCES
# ============================================================

$Script:AdapterCombo = $Script:Window.FindName("AdapterCombo")
$Script:DevicesGrid = $Script:Window.FindName("DevicesGrid")
$Script:AlertsGrid = $Script:Window.FindName("AlertsGrid")
$Script:HistoryGrid = $Script:Window.FindName("HistoryGrid")

$Script:TxtNetworkSummary = $Script:Window.FindName("TxtNetworkSummary")
$Script:TxtAdminHeader = $Script:Window.FindName("TxtAdminHeader")
$Script:TxtModeMessage = $Script:Window.FindName("TxtModeMessage")
$Script:TxtUptime = $Script:Window.FindName("TxtUptime")

$Script:TxtStatus = $Script:Window.FindName("TxtStatus")
$Script:TxtOnline = $Script:Window.FindName("TxtOnline")
$Script:TxtNew = $Script:Window.FindName("TxtNew")
$Script:TxtThreats = $Script:Window.FindName("TxtThreats")
$Script:TxtLastScan = $Script:Window.FindName("TxtLastScan")
$Script:TxtCapture = $Script:Window.FindName("TxtCapture")
$Script:TxtPps = $Script:Window.FindName("TxtPps")

$Script:TxtTopology = $Script:Window.FindName("TxtTopology")
$Script:TxtScheduleSummary = $Script:Window.FindName("TxtScheduleSummary")
$Script:TxtNextScan = $Script:Window.FindName("TxtNextScan")
$Script:TxtModeLarge = $Script:Window.FindName("TxtModeLarge")
$Script:TxtModeDetails = $Script:Window.FindName("TxtModeDetails")
$Script:TxtLastEvent = $Script:Window.FindName("TxtLastEvent")

$Script:TxtDetailRole = $Script:Window.FindName("TxtDetailRole")
$Script:TxtDetailName = $Script:Window.FindName("TxtDetailName")
$Script:TxtDetailIP = $Script:Window.FindName("TxtDetailIP")
$Script:TxtDetailMAC = $Script:Window.FindName("TxtDetailMAC")
$Script:TxtDetailVendor = $Script:Window.FindName("TxtDetailVendor")
$Script:TxtDetailType = $Script:Window.FindName("TxtDetailType")
$Script:TxtDetailStatus = $Script:Window.FindName("TxtDetailStatus")
$Script:TxtDetailFirst = $Script:Window.FindName("TxtDetailFirst")
$Script:TxtDetailLast = $Script:Window.FindName("TxtDetailLast")

$Script:TxtEngineAdmin = $Script:Window.FindName("TxtEngineAdmin")
$Script:TxtEngineNpcap = $Script:Window.FindName("TxtEngineNpcap")
$Script:TxtEngineTshark = $Script:Window.FindName("TxtEngineTshark")
$Script:TxtEngineNmap = $Script:Window.FindName("TxtEngineNmap")
$Script:TxtEngineFirewall = $Script:Window.FindName("TxtEngineFirewall")
$Script:TxtEngineCapture = $Script:Window.FindName("TxtEngineCapture")
$Script:TxtEngineMessage = $Script:Window.FindName("TxtEngineMessage")

$Script:ChkSchedule = $Script:Window.FindName("ChkSchedule")
$Script:CmbInterval = $Script:Window.FindName("CmbInterval")
$Script:ChkScanOnStart = $Script:Window.FindName("ChkScanOnStart")
$Script:ChkResolveNames = $Script:Window.FindName("ChkResolveNames")
$Script:ChkDeepCapture = $Script:Window.FindName("ChkDeepCapture")
$Script:ChkFirewallLog = $Script:Window.FindName("ChkFirewallLog")
$Script:ChkNmapDiscovery = $Script:Window.FindName("ChkNmapDiscovery")
$Script:ChkVirtual = $Script:Window.FindName("ChkVirtual")

$Script:TxtFooter = $Script:Window.FindName("TxtFooter")

$Script:DevicesGrid.ItemsSource = $Script:Devices
$Script:AlertsGrid.ItemsSource = $Script:Alerts
$Script:HistoryGrid.ItemsSource = $Script:History

# ============================================================
# GUI FUNCTIONS
# ============================================================

function Get-Brush {
    param([string]$Hex)

    return [Windows.Media.BrushConverter]::new().ConvertFromString($Hex)
}

function Refresh-EngineStatusUI {
    $engine = Get-EngineStatus

    $Script:TxtEngineAdmin.Text = $(if ($engine.Admin) { "OK | ADMIN" } else { "OGRANICZONY | BRAK ADMIN" })

    $Script:TxtEngineAdmin.Foreground = Get-Brush $(if ($engine.Admin) { "#31C48D" } else { "#F5B700" })

    $Script:TxtEngineNpcap.Text = $(if ($engine.NpcapInstalled) {
            "ZAINSTALOWANY | usluga: $($engine.NpcapService)"
        } else {
            "BRAK"
        })

    $Script:TxtEngineNpcap.Foreground = Get-Brush $(if ($engine.NpcapInstalled) { "#31C48D" } else { "#FF6B6B" })

    $Script:TxtEngineTshark.Text = $(if ($engine.TShark) { "OK | $($engine.TShark)" } else { "BRAK" })

    $Script:TxtEngineTshark.Foreground = Get-Brush $(if ($engine.TShark) { "#31C48D" } else { "#F5B700" })

    $Script:TxtEngineNmap.Text = $(if ($engine.Nmap) { "OK | $($engine.Nmap)" } else { "BRAK | opcjonalny" })

    $Script:TxtEngineNmap.Foreground = Get-Brush $(if ($engine.Nmap) { "#31C48D" } else { "#9DB0C9" })

    $Script:TxtEngineFirewall.Text = $(if ($engine.FirewallLogging) { "WLACZONE" } else { "WYLACZONE" })

    $Script:TxtEngineFirewall.Foreground = Get-Brush $(if ($engine.FirewallLogging) { "#31C48D" } else { "#F5B700" })

    $captureActive = $false

    if ($Script:TsharkProcess) {
        try {
            $captureActive = -not $Script:TsharkProcess.HasExited
        } catch {
        }
    }

    if ($captureActive) {
        $Script:TxtEngineCapture.Text = "ACTIVE | $($Script:CaptureRate) pak/s"
        $Script:TxtEngineCapture.Foreground = Get-Brush "#31C48D"
    } else {
        $reason = $Script:CaptureLastError

        if (-not $reason) {
            $reason = "NIEAKTYWNY"
        }

        $Script:TxtEngineCapture.Text = $reason
        $Script:TxtEngineCapture.Foreground = Get-Brush "#F5B700"
    }
}

function Update-DeviceDetails {
    $d = $Script:DevicesGrid.SelectedItem

    if (-not $d) {
        $Script:TxtDetailRole.Text = ""
        $Script:TxtDetailName.Text = "Wybierz urzadzenie"
        $Script:TxtDetailIP.Text = ""
        $Script:TxtDetailMAC.Text = ""
        $Script:TxtDetailVendor.Text = ""
        $Script:TxtDetailType.Text = ""
        $Script:TxtDetailStatus.Text = ""
        $Script:TxtDetailFirst.Text = ""
        $Script:TxtDetailLast.Text = ""
        return
    }

    $Script:TxtDetailRole.Text = $d.RoleLabel
    $Script:TxtDetailName.Text = $d.Name
    $Script:TxtDetailIP.Text = "IP: $($d.IP)"
    $Script:TxtDetailMAC.Text = "MAC: $($d.MAC)"
    $Script:TxtDetailVendor.Text = "Producent: $($d.Vendor)"
    $Script:TxtDetailType.Text = "Typ: $($d.Type) | pewnosc $($d.TypeConfidence)"
    $Script:TxtDetailStatus.Text = "Status: $($d.Status) | Znane: $($d.Known) | Zaufane: $($d.Trusted)"
    $Script:TxtDetailFirst.Text = "Pierwszy raz: $($d.FirstSeen)"
    $Script:TxtDetailLast.Text = "Ostatnio: $($d.LastSeen)"
}

function Build-TopologyText {
    $local = $Script:DeviceState.Values |
        Where-Object { $_.Role -eq "THIS_PC" } |
        Select-Object -First 1

    $gw = $Script:DeviceState.Values |
        Where-Object { $_.Role -eq "GATEWAY" } |
        Select-Object -First 1

    $others = @(
        $Script:DeviceState.Values |
            Where-Object {
                $_.Role -eq "DEVICE" -and
                $_.Status -eq "ONLINE"
            } |
            Sort-Object IP
    )

    $lines = New-Object System.Collections.Generic.List[string]

    $lines.Add("INTERNET")
    $lines.Add("   |")

    if ($gw) {
        $lines.Add("ROUTER / BRAMA  $($gw.IP)  $($gw.Vendor)")
    } else {
        $lines.Add("ROUTER / BRAMA  niewykryty")
    }

    $lines.Add("   |")

    if ($local) {
        $lines.Add("TEN KOMPUTER    $($local.IP)  $($local.Name)")
    } else {
        $lines.Add("TEN KOMPUTER    $($Script:LocalIP)")
    }

    if ($others.Count -gt 0) {
        $lines.Add("   |")
        $lines.Add("POZOSTALE URZADZENIA ONLINE:")

        foreach ($d in ($others | Select-Object -First 12)) {
            $flag = ""

            if ($d.New) { $flag = " [NOWE]" }
            elseif ($d.Trusted) { $flag = " [ZAUFANE]" }

            $lines.Add("   $($d.IP)  $($d.Name)  $($d.Type)$flag")
        }

        if ($others.Count -gt 12) {
            $lines.Add("   + $($others.Count - 12) kolejnych")
        }
    }

    return ($lines -join "`r`n")
}

function Update-UIStatus {
    $online = @(
        $Script:DeviceState.Values |
            Where-Object { $_.Status -eq "ONLINE" }
    ).Count

    $new = @(
        $Script:DeviceState.Values |
            Where-Object {
                $_.Status -eq "ONLINE" -and
                $_.New -eq $true
            }
    ).Count

    $threats = @(
        $Script:Alerts |
            Where-Object {
                $_.Category -eq "THREAT" -and
                $_.Severity -in @("MEDIUM","HIGH","CRITICAL")
            }
    ).Count

    if ($Script:Running) {
        $Script:TxtStatus.Text = "MONITORING"
        $Script:TxtStatus.Foreground = Get-Brush "#31C48D"
    } else {
        $Script:TxtStatus.Text = "NIEAKTYWNY"
        $Script:TxtStatus.Foreground = Get-Brush "#FF6B6B"
    }

    $Script:TxtOnline.Text = $online.ToString()
    $Script:TxtNew.Text = $new.ToString()
    $Script:TxtThreats.Text = $threats.ToString()

    if ($Script:LastScan) {
        $Script:TxtLastScan.Text = $Script:LastScan.ToString("HH:mm:ss")
    } else {
        $Script:TxtLastScan.Text = "BRAK"
    }

    $captureActive = $false

    if ($Script:TsharkProcess) {
        try {
            $captureActive = -not $Script:TsharkProcess.HasExited
        } catch {
        }
    }

    if ($captureActive) {
        $Script:TxtCapture.Text = "ACTIVE"
        $Script:TxtCapture.Foreground = Get-Brush "#31C48D"
    } elseif ($Script:Settings.EnableDeepCapture) {
        $Script:TxtCapture.Text = "READY / OFF"
        $Script:TxtCapture.Foreground = Get-Brush "#F5B700"
    } else {
        $Script:TxtCapture.Text = "WYLACZONY"
        $Script:TxtCapture.Foreground = Get-Brush "#9DB0C9"
    }

    $Script:TxtPps.Text = "$($Script:CaptureRate) pak/s"

    if ($Script:IsAdmin) {
        $Script:TxtAdminHeader.Text = "ADMIN: TAK"
        $Script:TxtAdminHeader.Foreground = Get-Brush "#31C48D"
        $Script:TxtModeLarge.Text = "TRYB PELNY"
        $Script:TxtModeLarge.Foreground = Get-Brush "#31C48D"
        $Script:TxtModeDetails.Text = "Firewall, blokowanie IP i Deep Capture sa dostepne. Packet capture wymaga dodatkowo Npcap i TShark."
    } else {
        $Script:TxtAdminHeader.Text = "ADMIN: NIE"
        $Script:TxtAdminHeader.Foreground = Get-Brush "#F5B700"
        $Script:TxtModeLarge.Text = "TRYB OGRANICZONY"
        $Script:TxtModeLarge.Foreground = Get-Brush "#F5B700"
        $Script:TxtModeDetails.Text = "Discovery urzadzen dziala. Pelne logowanie Firewall, blokowanie IP i przechwytywanie pakietow wymagaja uruchomienia jako administrator."
    }

    if ($Script:SelectedAdapter) {
        $bounds = Get-SubnetBounds $Script:LocalIP $Script:PrefixLength

        $scopeText = ""

        if ($bounds) {
            $scopeText = $bounds.Scope

            if ($bounds.Capped) {
                $scopeText += " | discovery ograniczone do lokalnego /24"
            }
        }

        $Script:TxtNetworkSummary.Text =
            "$($Script:SelectedAdapter.Name) | $($Script:LocalIP)/$($Script:PrefixLength) | Gateway $($Script:GatewayIP) | Zakres $scopeText"
    } else {
        $Script:TxtNetworkSummary.Text = "Brak wybranego interfejsu."
    }

    if ($Script:ScanInProgress) {
        $Script:TxtModeMessage.Text = "Skanowanie sieci..."
    } elseif ($Script:Running) {
        $Script:TxtModeMessage.Text = "Monitoring aktywny"
    } else {
        $Script:TxtModeMessage.Text = "Monitoring zatrzymany"
    }

    $uptime = (Get-Date) - $Script:StartedAt
    $Script:TxtUptime.Text = "Czas aplikacji: {0:hh\:mm\:ss}" -f $uptime

    if ($Script:Settings.ScheduleEnabled) {
        $Script:TxtScheduleSummary.Text =
            "Automatyczny skan: co $($Script:Settings.ScanIntervalMinutes) min"

        if ($Script:NextScan) {
            $Script:TxtNextScan.Text =
                "Nastepny skan: $($Script:NextScan.ToString('HH:mm:ss'))"
        } else {
            $Script:TxtNextScan.Text = "Nastepny skan: po uruchomieniu monitoringu"
        }
    } else {
        $Script:TxtScheduleSummary.Text = "Automatyczny skan: WYLACZONY"
        $Script:TxtNextScan.Text = "Skan uruchamiasz recznie."
    }

    $Script:TxtTopology.Text = Build-TopologyText

    if ($Script:Alerts.Count -gt 0) {
        $a = $Script:Alerts[0]
        $Script:TxtLastEvent.Text =
            "$($a.Time) | $($a.Type) | $($a.SourceIP) | $($a.Note)"
    } else {
        $Script:TxtLastEvent.Text = "Brak zdarzen."
    }

    $Script:TxtFooter.Text =
        "Dane: $($Script:DataRoot) | Pakiety capture: $($Script:CapturePackets)"

    Refresh-EngineStatusUI
}

function Load-SettingsIntoUI {
    $Script:ChkSchedule.IsChecked = [bool]$Script:Settings.ScheduleEnabled
    $Script:ChkScanOnStart.IsChecked = [bool]$Script:Settings.ScanOnStart
    $Script:ChkResolveNames.IsChecked = [bool]$Script:Settings.ResolveNames
    $Script:ChkDeepCapture.IsChecked = [bool]$Script:Settings.EnableDeepCapture
    $Script:ChkFirewallLog.IsChecked = [bool]$Script:Settings.EnableFirewallLogging
    $Script:ChkNmapDiscovery.IsChecked = [bool]$Script:Settings.UseNmapDiscovery
    $Script:ChkVirtual.IsChecked = [bool]$Script:Settings.ShowVirtualAdapters

    $desired = [int]$Script:Settings.ScanIntervalMinutes

    for ($i = 0; $i -lt $Script:CmbInterval.Items.Count; $i++) {
        $item = $Script:CmbInterval.Items[$i]

        if ([int]$item.Tag -eq $desired) {
            $Script:CmbInterval.SelectedIndex = $i
            break
        }
    }

    if ($Script:CmbInterval.SelectedIndex -lt 0) {
        $Script:CmbInterval.SelectedIndex = 1
    }
}

function Save-SettingsFromUI {
    $Script:Settings.ScheduleEnabled = [bool]$Script:ChkSchedule.IsChecked
    $Script:Settings.ScanOnStart = [bool]$Script:ChkScanOnStart.IsChecked
    $Script:Settings.ResolveNames = [bool]$Script:ChkResolveNames.IsChecked
    $Script:Settings.EnableDeepCapture = [bool]$Script:ChkDeepCapture.IsChecked
    $Script:Settings.EnableFirewallLogging = [bool]$Script:ChkFirewallLog.IsChecked
    $Script:Settings.UseNmapDiscovery = [bool]$Script:ChkNmapDiscovery.IsChecked
    $Script:Settings.ShowVirtualAdapters = [bool]$Script:ChkVirtual.IsChecked

    if ($Script:CmbInterval.SelectedItem) {
        $Script:Settings.ScanIntervalMinutes = [int]$Script:CmbInterval.SelectedItem.Tag
    }

    Save-Settings

    if ($Script:Settings.ScheduleEnabled -and $Script:Running) {
        $Script:NextScan = (Get-Date).AddMinutes([int]$Script:Settings.ScanIntervalMinutes)
    } else {
        $Script:NextScan = $null
    }

    Refresh-Adapters

    if (-not $Script:Settings.EnableDeepCapture) {
        Stop-DeepCapture
    } elseif ($Script:Running -and $Script:IsAdmin) {
        Start-DeepCapture | Out-Null
    }

    Update-UIStatus
}

# ============================================================
# GUI EVENTS
# ============================================================

$Script:AdapterCombo.Add_SelectionChanged({
    if ($Script:AdapterCombo.SelectedItem) {
        Set-SelectedAdapter $Script:AdapterCombo.SelectedItem
    }
})

$Script:DevicesGrid.Add_SelectionChanged({
    Update-DeviceDetails
})

$Script:Window.FindName("BtnAdmin").Add_Click({
    Restart-AsAdministrator
})

$Script:Window.FindName("BtnStart").Add_Click({
    Start-Monitoring
})

$Script:Window.FindName("BtnStop").Add_Click({
    Stop-Monitoring
})

$Script:Window.FindName("BtnScan").Add_Click({
    Invoke-DiscoveryScan
})

$Script:Window.FindName("BtnKnown").Add_Click({
    Add-CurrentDeviceToKnown
})

$Script:Window.FindName("BtnTrust").Add_Click({
    Add-CurrentDeviceToTrusted
})

$Script:Window.FindName("BtnUntrust").Add_Click({
    Remove-CurrentDeviceTrust
})

$Script:Window.FindName("BtnNmap").Add_Click({
    Send-SelectedToNmap
})

$Script:Window.FindName("BtnBlock").Add_Click({
    $d = $Script:DevicesGrid.SelectedItem

    if ($d) {
        $r = [System.Windows.MessageBox]::Show(
            "Zablokowac ruch IN i OUT dla $($d.IP)?",
            "Network Sentinel",
            "YesNo",
            "Warning"
        )

        if ($r -eq "Yes") {
            Block-IP $d.IP
        }
    }
})

$Script:Window.FindName("BtnUnblock").Add_Click({
    $d = $Script:DevicesGrid.SelectedItem

    if ($d) {
        Unblock-IP $d.IP
    }
})

$Script:Window.FindName("BtnEngineRefresh").Add_Click({
    Refresh-EngineStatusUI
})

$Script:Window.FindName("BtnEnableFirewall").Add_Click({
    if (-not $Script:IsAdmin) {
        [System.Windows.MessageBox]::Show(
            "Uruchom Sentinel jako administrator.",
            "Network Sentinel"
        ) | Out-Null
    } else {
        if (Enable-FirewallLogging) {
            $Script:TxtEngineMessage.Text = "Logowanie Windows Firewall wlaczone."
        } else {
            $Script:TxtEngineMessage.Text = "Nie udalo sie wlaczyc logowania Firewall."
        }

        Refresh-EngineStatusUI
    }
})

$Script:Window.FindName("BtnCaptureRestart").Add_Click({
    Stop-DeepCapture

    if (Start-DeepCapture) {
        $Script:TxtEngineMessage.Text = "Deep Capture uruchomiony."
    } else {
        $Script:TxtEngineMessage.Text = "Deep Capture nie wystartowal: $($Script:CaptureLastError)"
    }

    Refresh-EngineStatusUI
})

$Script:Window.FindName("BtnNpcapWeb").Add_Click({
    Start-Process "https://npcap.com/#download"
})

$Script:Window.FindName("BtnWiresharkWeb").Add_Click({
    Start-Process "https://www.wireshark.org/download.html"
})

$Script:Window.FindName("BtnNmapWeb").Add_Click({
    Start-Process "https://nmap.org/download.html#windows"
})

$Script:Window.FindName("BtnOuiUpdate").Add_Click({
    Update-OuiDatabase
})

$Script:Window.FindName("BtnDataFolder").Add_Click({
    Start-Process explorer.exe $Script:DataRoot
})

$Script:Window.FindName("BtnSaveSettings").Add_Click({
    Save-SettingsFromUI

    [System.Windows.MessageBox]::Show(
        "Ustawienia zapisane.",
        "Network Sentinel"
    ) | Out-Null
})

$Script:Window.FindName("BtnAutoUser").Add_Click({
    Register-UserAutostart
})

$Script:Window.FindName("BtnAutoAdmin").Add_Click({
    Register-AdminAutostartTask
})

$Script:Window.FindName("BtnReport").Add_Click({
    Export-HtmlReport
})

$Script:Window.FindName("BtnClearAlerts").Add_Click({
    $Script:Alerts.Clear()
    Update-UIStatus
})

# ============================================================
# TIMER
# ============================================================

$Script:Timer = New-Object Windows.Threading.DispatcherTimer
$Script:Timer.Interval = [TimeSpan]::FromMilliseconds([int]$Script:Settings.PollMilliseconds)
$Script:Timer.Add_Tick({
    Poll-Sentinel
})
$Script:Timer.Start()

# ============================================================
# WINDOW EVENTS
# ============================================================

$Script:Window.Add_Loaded({
    Load-RecentHistory
    Load-SettingsIntoUI
    Import-OuiDatabase
    Refresh-Adapters

    if ($Script:AdapterCombo.SelectedItem) {
        Set-SelectedAdapter $Script:AdapterCombo.SelectedItem
    }

    Refresh-LocalAndGateway
    Refresh-DeviceGrid
    Refresh-EngineStatusUI
    Show-FirstRunInfo

    if (-not $NoAutoStart -and $Script:Settings.StartMonitoringOnLaunch) {
        Start-Monitoring
    }

    Write-DashboardStatus
    Update-UIStatus
})

$Script:Window.Add_Closed({
    Stop-DeepCapture
    $Script:Running = $false
    Write-DashboardStatus

    try {
        $Script:NotifyIcon.Visible = $false
        $Script:NotifyIcon.Dispose()
    } catch {
    }
})

# ============================================================
# START
# ============================================================

[void]$Script:Window.ShowDialog()
