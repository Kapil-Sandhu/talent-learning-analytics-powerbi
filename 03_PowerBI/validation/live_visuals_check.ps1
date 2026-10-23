# Step 6 - runs, inside the OPEN Power BI model, the query behind every card / chart / slicer / matrix / table
# listed in 03_PowerBI\report\report_spec.json. Output: 03_PowerBI\validation\step6_live_values.json
param([string]$ProjectFolder = "D:\Ai Projects\Power BI")
$ErrorActionPreference = "Stop"
$ProjectFolder = $ProjectFolder.Trim().Trim('"').TrimEnd('\')
$out = Join-Path $ProjectFolder "03_PowerBI\validation\step6_live_values.json"
$spec = Get-Content (Join-Path $ProjectFolder "03_PowerBI\report\report_spec.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$bin = Join-Path (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop).InstallLocation "bin"
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.AdomdClient.dll"))
$engine = Get-Process msmdsrv -ErrorAction Stop | Sort-Object StartTime -Descending | Select-Object -First 1
$port = (Get-NetTCPConnection -OwningProcess $engine.Id -State Listen | Select-Object -First 1).LocalPort
function ColRef($c) { $t, $p = $c.Split('.', 2); return "'$t'[$p]" }
function MeaList($ms) { return (($ms | ForEach-Object { "`"$_`", [$_]" }) -join ", ") }
$Q = [ordered]@{}
foreach ($pg in $spec.pages) {
    foreach ($v in $pg.visuals) {
        $k = "$($pg.id)|$($v.key)"
        switch ($v.type) {
            "textbox" { }
            "actionButton" { }
            "card"    { $Q[$k] = "EVALUATE ROW(`"v`", [$($v.measures[0])])" }
            "slicer"  { $Q[$k] = "EVALUATE VALUES($(ColRef $v.columns[0]))" }
            default   {
                $cols = ($v.columns | ForEach-Object { ColRef $_ }) -join ", "
                $parts = @()
                if ($v.measures -and $v.measures.Count -gt 0) { $parts += (MeaList $v.measures) }
                foreach ($a in @($v.aggs)) { if ($a) { $fn = @{ Sum = "SUM"; Avg = "AVERAGE" }[$a.func]; $parts += "`"$($a.alias)`", $fn($(ColRef $a.col))" } }
                if ($parts.Count -gt 0) { $Q[$k] = "EVALUATE SUMMARIZECOLUMNS($cols, $($parts -join ', '))" }
                else { $Q[$k] = "EVALUATE SUMMARIZECOLUMNS($cols)" }
            }
        }
    }
}
$Q["slicer_test_sales"] = "EVALUATE CALCULATETABLE(ROW($(MeaList @('Headcount','Leavers','Attrition Rate','Avg Tenure (Years)','Training per Employee','Overtime %'))), 'DimDepartment'[Department] = `"Sales`")"
$Res = [ordered]@{ port = $port; queries = [ordered]@{}; errors = @() }
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$port")
$conn.Open()
foreach ($k in $Q.Keys) {
    try {
        $cmd = $conn.CreateCommand(); $cmd.CommandText = $Q[$k]
        $rd = $cmd.ExecuteReader()
        $names = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $names += $rd.GetName($i) }
        $rows = @()
        while ($rd.Read()) { $row = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $x = $rd.GetValue($i); if ($x -is [DBNull]) { $x = $null }; $row += ,$x }; $rows += ,$row }
        $rd.Close()
        $Res.queries[$k] = [ordered]@{ dax = $Q[$k]; columns = $names; rows = $rows }
    } catch { $Res.queries[$k] = [ordered]@{ dax = $Q[$k]; error = $_.Exception.Message }; $Res.errors += "$k : $($_.Exception.Message)" }
}
$conn.Close()
$Res | ConvertTo-Json -Depth 10 -Compress | Set-Content -Path $out -Encoding UTF8
"queries=$($Res.queries.Count) errors=$($Res.errors.Count)"; $Res.errors
