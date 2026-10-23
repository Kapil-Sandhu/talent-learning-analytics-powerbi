# Reads Power BI Desktop's open windows through Windows UI Automation (read-only, no clicks):
# which windows / dialogs are open and whether any warning or error text is shown.
param([string]$ProjectFolder = "D:\Ai Projects\Power BI", [string]$OutName = "step5_ui_check.json")
$ErrorActionPreference = "Stop"
$ProjectFolder = $ProjectFolder.Trim().Trim('"').TrimEnd('\')
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$A = [System.Windows.Automation.AutomationElement]
$procs = @(Get-Process PBIDesktop -ErrorAction SilentlyContinue)
$U = [ordered]@{ windows = @(); dialogs = @(); suspicious = @(); measures_table_visible = $false }
foreach ($p in $procs) {
    $cond = New-Object System.Windows.Automation.PropertyCondition($A::ProcessIdProperty, $p.Id)
    foreach ($w in $A::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children, $cond)) {
        $U.windows += $w.Current.Name
        $wc = New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty, [System.Windows.Automation.ControlType]::Window)
        foreach ($k in $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $wc)) { $U.dialogs += $k.Current.Name }
        $names = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition) |
                 ForEach-Object { $_.Current.Name } | Where-Object { $_ } | Select-Object -Unique
        $U.suspicious += @($names | Where-Object { $_ -match "issue|could not|couldn't|can't|cannot|error|failed|problem|warning|unable" })
        if (@($names | Where-Object { $_ -match "_Measures" }).Count -gt 0) { $U.measures_table_visible = $true }
    }
}
$U | ConvertTo-Json -Depth 5 | Set-Content -Path (Join-Path $ProjectFolder "03_PowerBI\validation\$OutName") -Encoding UTF8
"windows: $($U.windows -join ' | ')"; "dialogs: $($U.dialogs -join ' | ')"; "suspicious: $($U.suspicious -join ' | ')"; "_Measures visible: $($U.measures_table_visible)"
