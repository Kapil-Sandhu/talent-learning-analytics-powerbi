# Step 4 - live check against the model OPEN in Power BI Desktop.
#  1. finds the local Analysis Services engine (msmdsrv) of the open Power BI Desktop
#  2. optional -Refresh: full refresh of every table (runs all Power Query code inside Power BI)
#  3. dumps the live model metadata (tables, columns, relationships) as Power BI really holds it
#  4. runs DAX test queries (row counts, QA_Checks, orphan keys, filter direction, totals per dimension)
# Output: 03_PowerBI\validation\step4_live_results.json
param([string]$ProjectFolder = "D:\Ai Projects\Power BI", [switch]$Refresh)
$ErrorActionPreference = "Stop"
$ProjectFolder = $ProjectFolder.Trim().Trim('"').TrimEnd('\')
$out = Join-Path $ProjectFolder "03_PowerBI\validation\step4_live_results.json"
$bin = Join-Path (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop).InstallLocation "bin"
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Tabular.dll"))
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.AdomdClient.dll"))

$R = [ordered]@{ port = $null; database = $null; refresh = $null; refreshSeconds = $null; tables = @(); relationships = @(); queries = [ordered]@{}; errors = @() }

$ms = Get-Process msmdsrv -ErrorAction Stop | Sort-Object StartTime -Descending | Select-Object -First 1
$R.port = (Get-NetTCPConnection -OwningProcess $ms.Id -State Listen | Select-Object -First 1).LocalPort
$srv = New-Object Microsoft.AnalysisServices.Tabular.Server
$srv.Connect("Data Source=localhost:$($R.port)")
$db = $srv.Databases[0]
$R.database = $db.Name
$m = $db.Model

if ($Refresh) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    try {
        $m.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
        $res = $m.SaveChanges()
        $R.refresh = "OK"
    } catch {
        $ex = $_.Exception; $msg = ""
        while ($ex) { $msg += $ex.Message + " | "; $ex = $ex.InnerException }
        $R.refresh = "FAILED: $msg"
        $m.UndoLocalChanges()
    }
    $R.refreshSeconds = [Math]::Round($sw.Elapsed.TotalSeconds, 1)
    $m.Sync()
}

foreach ($t in $m.Tables) {
    $cols = @()
    foreach ($c in $t.Columns) {
        if ("$($c.Type)" -eq "RowNumber") { continue }
        $cols += [ordered]@{ name = $c.Name; dataType = "$($c.DataType)"; isHidden = $c.IsHidden; isKey = $c.IsKey;
                             summarizeBy = "$($c.SummarizeBy)"; formatString = $c.FormatString;
                             sortByColumn = $(if ($c.SortByColumn) { $c.SortByColumn.Name } else { $null }) }
    }
    $R.tables += [ordered]@{ name = $t.Name; isHidden = $t.IsHidden; columns = $cols }
}
foreach ($rel in $m.Relationships) {
    $R.relationships += [ordered]@{ from = "$($rel.FromTable.Name).$($rel.FromColumn.Name)"; to = "$($rel.ToTable.Name).$($rel.ToColumn.Name)";
        fromCardinality = "$($rel.FromCardinality)"; toCardinality = "$($rel.ToCardinality)"; crossFilter = "$($rel.CrossFilteringBehavior)"; active = $rel.IsActive }
}

# ---------------- DAX test queries
$dims = @(
  @("DimDepartment","DepartmentKey","Department"), @("DimJobRole","JobRoleKey","JobRole"),
  @("DimEducation","EducationKey","EducationLevel"), @("DimJobSatisfaction","JobSatisfactionKey","JobSatisfaction"),
  @("DimAgeBand","AgeBandKey","AgeBand"), @("DimTenureBand","TenureBandKey","TenureBand"),
  @("DimIncomeBand","IncomeBandKey","IncomeBand"), @("DimTrainingBand","TrainingBandKey","TrainingBand"),
  @("DimEmployee","EmployeeID","EmployeeStatus"))
$Q = [ordered]@{}
$Q["rowcounts"] = "EVALUATE ROW(" + ((@("DimDepartment","DimJobRole","DimEducation","DimJobSatisfaction","DimAgeBand","DimTenureBand","DimIncomeBand","DimTrainingBand","DimEmployee","FactEmployee","QA_Checks","_Measures") | ForEach-Object { "`"$_`", COUNTROWS('$_')" }) -join ", ") + ")"
$Q["qa_checks"] = "EVALUATE QA_Checks ORDER BY QA_Checks[CheckNo]"
$Q["orphans"] = "EVALUATE ROW(" + (($dims | ForEach-Object { "`"$($_[0])`", COUNTROWS(FILTER(FactEmployee, ISBLANK(RELATED($($_[0])[$($_[1])]))))" }) -join ", ") + ")"
$Q["direction"] = "EVALUATE ROW(`"DeptRowsWhenFactFiltered`", CALCULATE(COUNTROWS(DimDepartment), FactEmployee[AttritionFlag] = 1), `"EmployeeRowsWhenFactFiltered`", CALCULATE(COUNTROWS(DimEmployee), FactEmployee[AttritionFlag] = 1), `"FactRowsWhenDeptFiltered`", CALCULATE(COUNTROWS(FactEmployee), DimDepartment[Department] = `"Sales`"))"
foreach ($d in $dims) {
    $Q["by_$($d[0])"] = "EVALUATE SUMMARIZECOLUMNS($($d[0])[$($d[2])], `"Headcount`", COUNTROWS(FactEmployee), `"Leavers`", SUM(FactEmployee[AttritionFlag]), `"Trainings`", SUM(FactEmployee[TrainingTimesLastYear]))"
}
foreach ($c in @("OverTime","BusinessTravel","WorkLifeBalance","EnvironmentSatisfaction","PerformanceRating","Gender","MaritalStatus")) {
    $Q["by_DimEmployee_$c"] = "EVALUATE SUMMARIZECOLUMNS(DimEmployee[$c], `"Headcount`", COUNTROWS(FactEmployee), `"Leavers`", SUM(FactEmployee[AttritionFlag]))"
}
$Q["totals"] = "EVALUATE ROW(`"Headcount`", COUNTROWS(FactEmployee), `"Leavers`", SUM(FactEmployee[AttritionFlag]), `"Trainings`", SUM(FactEmployee[TrainingTimesLastYear]), `"Income`", SUM(FactEmployee[MonthlyIncome]), `"Tenure`", SUM(FactEmployee[YearsAtCompany]))"
$Q["two_dims"] = "EVALUATE SUMMARIZECOLUMNS(DimDepartment[Department], DimTenureBand[TenureBand], `"Headcount`", COUNTROWS(FactEmployee), `"Leavers`", SUM(FactEmployee[AttritionFlag]))"

$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$($R.port);Catalog=$($db.Name)")
$conn.Open()
foreach ($k in $Q.Keys) {
    try {
        $cmd = $conn.CreateCommand(); $cmd.CommandText = $Q[$k]
        $rd = $cmd.ExecuteReader()
        $names = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $names += $rd.GetName($i) }
        $rows = @()
        while ($rd.Read()) { $row = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $v = $rd.GetValue($i); if ($v -is [DBNull]) { $v = $null }; $row += ,$v }; $rows += ,$row }
        $rd.Close()
        $R.queries[$k] = [ordered]@{ dax = $Q[$k]; columns = $names; rows = $rows }
    } catch {
        $R.queries[$k] = [ordered]@{ dax = $Q[$k]; error = $_.Exception.Message }
        $R.errors += "$k : $($_.Exception.Message)"
    }
}
$conn.Close(); $srv.Disconnect()
$R | ConvertTo-Json -Depth 10 | Set-Content -Path $out -Encoding UTF8
"port=$($R.port) refresh=$($R.refresh) seconds=$($R.refreshSeconds) tables=$($R.tables.Count) rels=$($R.relationships.Count) queries=$($R.queries.Count) errors=$($R.errors.Count)"
$R.errors
