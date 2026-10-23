# Step 6 - opens every report page in the running Power BI Desktop (via Windows UI Automation: selects the page tab,
# no other clicks or typing) and records what the page shows: all accessible text (visual titles, values, error
# messages) and any dialogs. Output: 03_PowerBI\validation\step6_ui_pages.json
param([string]$ProjectFolder = "D:\Ai Projects\Power BI", [int]$WaitSeconds = 25)
$ErrorActionPreference = "Stop"
$ProjectFolder = $ProjectFolder.Trim().Trim('"').TrimEnd('\')
$spec = Get-Content (Join-Path $ProjectFolder "03_PowerBI\report\report_spec.json") -Raw -Encoding UTF8 | ConvertFrom-Json
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [System.Windows.Automation.AutomationElement]
$TS = [System.Windows.Automation.TreeScope]
$p = Get-Process PBIDesktop | Where-Object { $_.MainWindowTitle -like '*Talent*' } | Select-Object -First 1
$win = $AE::RootElement.FindFirst($TS::Children, (New-Object System.Windows.Automation.PropertyCondition($AE::ProcessIdProperty, $p.Id)))
function AllText($el) {
    $list = New-Object System.Collections.Generic.List[string]
    foreach ($e in $el.FindAll($TS::Descendants, [System.Windows.Automation.Condition]::TrueCondition)) {
        try { $n = $e.Current.Name; if ($n) { $list.Add($n) }; $h = $e.Current.HelpText; if ($h) { $list.Add($h) } } catch {}
    }
    return @($list | Select-Object -Unique)
}
function Dialogs($el) {
    $c = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, [System.Windows.Automation.ControlType]::Window)
    return @($el.FindAll($TS::Descendants, $c) | ForEach-Object { $_.Current.Name })
}
$U = [ordered]@{ window = $win.Current.Name; dialogs = @(Dialogs $win); pages = [ordered]@{} }
foreach ($pg in $spec.pages) {
    $cond = New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty, $pg.name)
    $cands = @($win.FindAll($TS::Descendants, $cond))
    $selected = $false; $how = ""
    foreach ($c in $cands) {
        if ($selected) { break }
        foreach ($pat in @([System.Windows.Automation.SelectionItemPattern]::Pattern, [System.Windows.Automation.InvokePattern]::Pattern)) {
            $o = $null
            if ($c.TryGetCurrentPattern($pat, [ref]$o)) {
                try { if ($pat -eq [System.Windows.Automation.SelectionItemPattern]::Pattern) { $o.Select() } else { $o.Invoke() }; $selected = $true; $how = "$($c.Current.ControlType.ProgrammaticName) via $($pat.ProgrammaticName)"; break } catch {}
            }
        }
    }
    Start-Sleep -Seconds $WaitSeconds
    $U.pages[$pg.name] = [ordered]@{ selected = $selected; how = $how; candidates = $cands.Count; texts = @(AllText $win); dialogs = @(Dialogs $win) }
    "$($pg.name): selected=$selected ($how) texts=$($U.pages[$pg.name].texts.Count)"
}
$first = $spec.pages[0].name
$c0 = @($win.FindAll($TS::Descendants, (New-Object System.Windows.Automation.PropertyCondition($AE::NameProperty, $first))))
foreach ($c in $c0) { $o = $null; if ($c.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$o)) { try { $o.Select(); break } catch {} } }
$U.dialogs = @(Dialogs $win)
$U | ConvertTo-Json -Depth 6 | Set-Content -Path (Join-Path $ProjectFolder "03_PowerBI\validation\step6_ui_pages.json") -Encoding UTF8
"dialogs: $($U.dialogs -join ' | ')"
