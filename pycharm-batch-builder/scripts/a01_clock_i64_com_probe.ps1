# Diagnose whether LabVIEW ActiveX preserves exact I64 values.
# This uses ONLY outputs/A01/native_clock_v2/Sim_Clock.vi. It never saves the VI.
# Does not certify native behavior unless exact I64 input read-back is proven.
param(
    [string]$ViPath = (Join-Path $PSScriptRoot "..\outputs\A01\native_clock_v2\Sim_Clock.vi")
)

$ErrorActionPreference = "Stop"
$vi = $null
$lv = $null
$rows = @()
$state = "NOT_RUN"
$details = ""
$before = @(Get-Process -Name "LabVIEW" -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
$reportPath = Join-Path $PSScriptRoot "..\outputs\A01\evidence\sim_clock_com_precision_probe.json"

try {
    if (-not $before.Count) {
        throw "LabVIEW must be running already. This probe must not start LabVIEW."
    }
    $full = [System.IO.Path]::GetFullPath($ViPath)
    $root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\outputs\A01"))
    if (-not $full.StartsWith($root + [System.IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing a VI outside the A01 scratch output folder"
    }
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
        throw "Missing native Sim_Clock VI: $full"
    }
    $lv = New-Object -ComObject "LabVIEW.Application"
    $after = @(Get-Process -Name "LabVIEW" -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
    if (@($after | Where-Object { $before -notcontains $_ }).Count -ne 0) {
        throw "ActiveX started an additional LabVIEW process; refusing further activity. Close any new automation instance manually if needed."
    }
    $vi = $lv.GetVIReference($full)

    $vectors = @(
        @{ test_id = "A01-CLK-005"; current = "9223372036854775806"; advance = "2"; next = "9223372036854775806"; valid = $false },
        @{ test_id = "A01-CLK-008"; current = "9223372036854775805"; advance = "2"; next = "9223372036854775807"; valid = $true }
    )
    foreach ($tc in $vectors) {
        # A literal Int64 is passed as a COM argument (not via Fract/Exp String To Number).
        $current = [long]::Parse($tc.current, [System.Globalization.CultureInfo]::InvariantCulture)
        $advance = [long]::Parse($tc.advance, [System.Globalization.CultureInfo]::InvariantCulture)
        $vi.SetControlValue("current_ms", $current)
        $vi.SetControlValue("advance_ms", $advance)
        $currentRead = $vi.GetControlValue("current_ms")
        $advanceRead = $vi.GetControlValue("advance_ms")
        $currentType = if ($null -ne $currentRead) { $currentRead.GetType().FullName } else { "null" }
        $advanceType = if ($null -ne $advanceRead) { $advanceRead.GetType().FullName } else { "null" }
        $precise = ($currentRead -is [long]) -and ($advanceRead -is [long]) -and
                   ($currentRead -eq $current) -and ($advanceRead -eq $advance)
        if (-not $precise) {
            $rows += @{
                test_id = $tc.test_id
                status = "BLOCKED_INPUT_PRECISION"
                expected_current = $tc.current
                readback_current = [string]$currentRead
                readback_type = $currentType
                readback_advance_type = $advanceType
            }
            continue
        }
        $vi.Run($true)
        $next = $vi.GetControlValue("next_ms")
        $valid = $vi.GetControlValue("valid")
        $pass = ($next -is [long]) -and ($valid -is [bool]) -and
                ($next.ToString([System.Globalization.CultureInfo]::InvariantCulture) -eq $tc.next) -and
                ($valid -eq $tc.valid)
        $rows += @{
            test_id = $tc.test_id
            status = $(if ($pass) { "PASS" } else { "FAIL" })
            expected_next = $tc.next
            actual_next = [string]$next
            actual_next_type = $(if ($null -ne $next) { $next.GetType().FullName } else { "null" })
            expected_valid = $tc.valid
            actual_valid = $valid
            input_readback_exact = $precise
        }
    }
    $state = if (@($rows | Where-Object { $_.status -ne "PASS" }).Count -eq 0) { "PASS" } else { "NOT_VERIFIED" }
} catch {
    $state = "ERROR"
    $details = $_.Exception.Message
} finally {
    if ($null -ne $vi) { try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($vi) } catch {} }
    if ($null -ne $lv) { try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($lv) } catch {} }
    $summary = @{
        component = "Sim_Clock.vi"
        backend = "ActiveX/COM (strict typed Int64 probe)"
        status = $state
        results = $rows
        error = $details
        note = "Only exact System.Int64 input readback allows a test to count as PASS."
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $reportPath) | Out-Null
    $summary | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $reportPath -Encoding UTF8
    $summary | ConvertTo-Json -Depth 8
}
if ($state -ne "PASS") { exit 2 }
