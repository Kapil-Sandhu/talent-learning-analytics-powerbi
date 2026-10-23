# Step 4 - offline check: parse the TMDL folder with Microsoft's own TMDL serializer (shipped with Power BI Desktop)
# and dump what it understood (tables, columns, properties, relationships) to JSON for comparison with the design.
param([string]$ProjectFolder = "D:\Ai Projects\Power BI")
$ErrorActionPreference = "Stop"
$ProjectFolder = $ProjectFolder.Trim().Trim('"').TrimEnd('\')
$def = Join-Path $ProjectFolder "03_PowerBI\Talent_Learning_Dashboard.SemanticModel\definition"
$out = Join-Path $ProjectFolder "03_PowerBI\validation\step4_tmdl_offline.json"
$bin = Join-Path (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop).InstallLocation "bin"
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Tabular.dll"))
$result = [ordered]@{ ok = $false; error = $null; tables = @(); relationships = @(); expressions = @() }
try {
    $db = [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($def)
    $m = $db.Model
    foreach ($t in $m.Tables) {
        $cols = @()
        foreach ($c in $t.Columns) {
            if ($c.Type -eq "RowNumber") { continue }
            $cols += [ordered]@{ name = $c.Name; dataType = "$($c.DataType)"; isHidden = $c.IsHidden; isKey = $c.IsKey;
                                 summarizeBy = "$($c.SummarizeBy)"; formatString = $c.FormatString;
                                 sortByColumn = $(if ($c.SortByColumn) { $c.SortByColumn.Name } else { $null }) }
        }
        $parts = @(); foreach ($p in $t.Partitions) { $parts += [ordered]@{ name = $p.Name; kind = "$($p.SourceType)"; mode = "$($p.Mode)" } }
        $result.tables += [ordered]@{ name = $t.Name; isHidden = $t.IsHidden; description = $t.Description; columns = $cols; partitions = $parts }
    }
    foreach ($r in $m.Relationships) {
        $result.relationships += [ordered]@{ from = "$($r.FromTable.Name).$($r.FromColumn.Name)"; to = "$($r.ToTable.Name).$($r.ToColumn.Name)";
            fromCardinality = "$($r.FromCardinality)"; toCardinality = "$($r.ToCardinality)";
            crossFilter = "$($r.CrossFilteringBehavior)"; active = $r.IsActive }
    }
    foreach ($e in $m.Expressions) { $result.expressions += [ordered]@{ name = $e.Name; kind = "$($e.Kind)" } }
    $result.measures = @()
    foreach ($t in $m.Tables) {
        foreach ($x in $t.Measures) {
            $result.measures += [ordered]@{ name = $x.Name; table = $t.Name; expression = $x.Expression; formatString = $x.FormatString;
                                            displayFolder = $x.DisplayFolder; description = $x.Description }
        }
    }
    $result.compatibilityLevel = $db.CompatibilityLevel
    $result.ok = $true
} catch {
    $ex = $_.Exception; $msg = ""
    while ($ex) { $msg += $ex.GetType().Name + ": " + $ex.Message + " | "; $ex = $ex.InnerException }
    $result.error = $msg
}
$result | ConvertTo-Json -Depth 8 | Set-Content -Path $out -Encoding UTF8
"ok=$($result.ok) tables=$($result.tables.Count) relationships=$($result.relationships.Count) expressions=$($result.expressions.Count) measures=$($result.measures.Count)"
if ($result.error) { "ERROR: $($result.error)" }
