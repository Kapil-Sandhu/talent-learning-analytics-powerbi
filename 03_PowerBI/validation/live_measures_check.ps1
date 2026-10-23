# Step 5 - live check of the DAX measures in the model OPEN in Power BI Desktop.
#  * reads every measure as Power BI holds it (expression, format, folder, description) + its engine State / ErrorMessage
#  * runs DAX test queries: all measures at total level, by 15 groupings, per employee, empty selection,
#    KEEPFILTERS behaviour, slicer + company baseline, and a negative control that MUST fail
# Output: 03_PowerBI\validation\step5_live_results.json
param([string]$ProjectFolder = "D:\Ai Projects\Power BI")
$ErrorActionPreference = "Stop"
$ProjectFolder = $ProjectFolder.Trim().Trim('"').TrimEnd('\')
$out = Join-Path $ProjectFolder "03_PowerBI\validation\step5_live_results.json"
$specFile = Join-Path $ProjectFolder "03_PowerBI\model\measures.json"
$bin = Join-Path (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop).InstallLocation "bin"
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.Tabular.dll"))
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.AdomdClient.dll"))
$spec = Get-Content $specFile -Raw -Encoding UTF8 | ConvertFrom-Json
$names = @($spec | ForEach-Object { $_.name })

$Res = [ordered]@{ port = $null; measures = @(); queries = [ordered]@{}; errors = @() }
$engine = Get-Process msmdsrv -ErrorAction Stop | Sort-Object StartTime -Descending | Select-Object -First 1
$Res.port = (Get-NetTCPConnection -OwningProcess $engine.Id -State Listen | Select-Object -First 1).LocalPort
$srv = New-Object Microsoft.AnalysisServices.Tabular.Server
$srv.Connect("Data Source=localhost:$($Res.port)")
$db = $srv.Databases[0]
foreach ($tbl in $db.Model.Tables) {
    foreach ($ms in $tbl.Measures) {
        $Res.measures += [ordered]@{ name = $ms.Name; table = $tbl.Name; expression = $ms.Expression; formatString = $ms.FormatString;
            displayFolder = $ms.DisplayFolder; description = $ms.Description; state = "$($ms.State)"; errorMessage = $ms.ErrorMessage }
    }
}

$all = ($names | ForEach-Object { "`"$_`", [$_]" }) -join ", "
$Q = [ordered]@{}
$Q["total"] = "EVALUATE ROW($all)"
$groups = [ordered]@{ dept = "DimDepartment[Department]"; role = "DimJobRole[JobRole]"; edu = "DimEducation[EducationLevel]";
  jobsat = "DimJobSatisfaction[JobSatisfaction]"; age = "DimAgeBand[AgeBand]"; tenure = "DimTenureBand[TenureBand]";
  income = "DimIncomeBand[IncomeBand]"; training = "DimTrainingBand[TrainingBand]"; overtime = "DimEmployee[OverTime]";
  gender = "DimEmployee[Gender]"; marital = "DimEmployee[MaritalStatus]"; travel = "DimEmployee[BusinessTravel]";
  wlb = "DimEmployee[WorkLifeBalance]"; status = "DimEmployee[EmployeeStatus]"; employee = "DimEmployee[EmployeeID]";
  dept_x_overtime = "DimDepartment[Department], DimEmployee[OverTime]" }
foreach ($g in $groups.Keys) { $Q["by_$g"] = "EVALUATE SUMMARIZECOLUMNS($($groups[$g]), $all)" }
$Q["empty_selection"] = "EVALUATE CALCULATETABLE(ROW($all), DimDepartment[Department] = `"__no_such_department__`")"
$Q["keepfilters_overtime_col"] = "EVALUATE SUMMARIZECOLUMNS(FactEmployee[OverTimeFlag], `"HC`", [Headcount], `"AR_OT`", [Attrition Rate - Overtime], `"AR_NoOT`", [Attrition Rate - No Overtime], `"OT_Emp`", [Overtime Employees])"
$Q["keepfilters_training_col"] = "EVALUATE SUMMARIZECOLUMNS(FactEmployee[TrainingTimesLastYear], `"HC`", [Headcount], `"NoTrain`", [Employees with No Training], `"High`", [% High Training (5-6)])"
$Q["slicer_sales"] = "EVALUATE CALCULATETABLE(ROW(`"Rate`", [Attrition Rate], `"Company`", [Company Attrition Rate], `"Vs`", [Attrition vs Company (pts)], `"HC`", [Headcount]), DimDepartment[Department] = `"Sales`")"
$Q["negative_control_must_fail"] = "DEFINE MEASURE _Measures[BrokenOnPurpose] = SUM ( FactEmployee[NoSuchColumn] ) EVALUATE ROW(`"x`", [BrokenOnPurpose])"

$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$($Res.port);Catalog=$($db.Name)")
$conn.Open()
foreach ($k in $Q.Keys) {
    try {
        $cmd = $conn.CreateCommand(); $cmd.CommandText = $Q[$k]
        $rd = $cmd.ExecuteReader()
        $cols = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $cols += $rd.GetName($i) }
        $rows = @()
        while ($rd.Read()) { $row = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $v = $rd.GetValue($i); if ($v -is [DBNull]) { $v = $null }; $row += ,$v }; $rows += ,$row }
        $rd.Close()
        $Res.queries[$k] = [ordered]@{ columns = $cols; rows = $rows }
    } catch {
        $Res.queries[$k] = [ordered]@{ error = $_.Exception.Message }
        if ($k -ne "negative_control_must_fail") { $Res.errors += "$k : $($_.Exception.Message)" }
    }
}
$conn.Close(); $srv.Disconnect()
$Res | ConvertTo-Json -Depth 10 -Compress | Set-Content -Path $out -Encoding UTF8
"port=$($Res.port) measures=$($Res.measures.Count) notReady=$(@($Res.measures | Where-Object { $_.state -ne 'Ready' }).Count) queries=$($Res.queries.Count) errors=$($Res.errors.Count)"
$Res.errors
