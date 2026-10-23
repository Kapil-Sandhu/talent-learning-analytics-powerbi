# Step 3 runtime test: executes every Power Query (.pq) file in the REAL Power Query engine (Excel),
# loads the 11 output queries to sheets and saves the result for comparison with the Python mirror.
# Usage:  powershell -ExecutionPolicy Bypass -File run_m_in_excel.ps1 "D:\Ai Projects\Power BI"
param([string]$ProjectFolder = "D:\Ai Projects\Power BI")
# Pass the folder WITHOUT a trailing backslash (a trailing \ before a closing quote breaks Windows quoting)
$ProjectFolder = $ProjectFolder.Trim().Trim('"')
if (-not $ProjectFolder.EndsWith('\')) { $ProjectFolder += '\' }

$ErrorActionPreference = "Stop"
$pqDir   = Join-Path $ProjectFolder "03_PowerBI\PowerQuery"
$outFile = Join-Path $ProjectFolder "03_PowerBI\validation\excel_engine_run.xlsx"
$logFile = Join-Path $ProjectFolder "03_PowerBI\validation\excel_engine_run_log.txt"
$loadList = @("DimDepartment","DimJobRole","DimEducation","DimJobSatisfaction","DimAgeBand","DimTenureBand",
              "DimIncomeBand","DimTrainingBand","DimEmployee","FactEmployee","QA_Checks")
$log = New-Object System.Collections.Generic.List[string]
function Log($m) { $script:log.Add($m); Write-Output $m }

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
try {
    $wb = $xl.Workbooks.Add()
    # 1) add every query (name = file name without the number prefix)
    foreach ($f in Get-ChildItem $pqDir -Filter *.pq | Sort-Object Name) {
        $name = ($f.BaseName -replace '^\d+_', '')
        $m = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8)
        # the parameter's default value must point at THIS machine's project folder
        if ($name -eq "ProjectFolder") {
            $m = '"' + $ProjectFolder + '" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]'
        }
        [void]$wb.Queries.Add($name, $m)
        if ($name -eq "ProjectFolder") { Log "ADDED   $name  =  $m" } else { Log "ADDED   $name" }
    }
    # 2) load the output queries to their own sheets and refresh each one
    foreach ($q in $loadList) {
        $ws = $wb.Worksheets.Add()
        $ws.Name = $q.Substring(0, [Math]::Min(31, $q.Length))
        $conn = "OLEDB;Provider=Microsoft.Mashup.OleDb.1;Data Source=`$Workbook`$;Location=$q;Extended Properties=`"`""
        $lo = $ws.ListObjects.Add(0, $conn, $null, 1, $ws.Range("A1"))
        $lo.QueryTable.CommandType = 2
        $lo.QueryTable.CommandText = "SELECT * FROM [$q]"
        $lo.QueryTable.BackgroundQuery = $false
        $sw = [Diagnostics.Stopwatch]::StartNew()
        try {
            [void]$lo.QueryTable.Refresh($false)
            Log ("LOADED  {0,-20} rows={1,-5} cols={2,-3} ({3} ms)" -f $q, $lo.ListRows.Count, $lo.ListColumns.Count, $sw.ElapsedMilliseconds)
        } catch {
            Log ("ERROR   {0,-20} {1}" -f $q, $_.Exception.Message)
        }
    }
    if (Test-Path $outFile) { Remove-Item $outFile }
    $wb.SaveAs($outFile, 51)
    Log "SAVED   $outFile"
    $wb.Close($false)
} catch {
    Log ("FATAL   " + $_.Exception.Message)
} finally {
    $xl.Quit()
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
    $log | Set-Content -Path $logFile -Encoding UTF8
}
