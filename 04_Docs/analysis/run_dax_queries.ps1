# Generic runner: executes the DAX queries in a JSON file {name: dax} against the OPEN Power BI Desktop model.
param([string]$ProjectFolder = "D:\Ai Projects\Power BI", [string]$QueriesFile, [string]$OutFile)
$ErrorActionPreference = "Stop"
$ProjectFolder = $ProjectFolder.Trim().Trim('"').TrimEnd('\')
$bin = Join-Path (Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop).InstallLocation "bin"
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin "Microsoft.PowerBI.AdomdClient.dll"))
$engine = Get-Process msmdsrv -ErrorAction Stop | Sort-Object StartTime -Descending | Select-Object -First 1
$port = (Get-NetTCPConnection -OwningProcess $engine.Id -State Listen | Select-Object -First 1).LocalPort
$Q = Get-Content $QueriesFile -Raw -Encoding UTF8 | ConvertFrom-Json
$Res = [ordered]@{ port = $port; queries = [ordered]@{}; errors = @() }
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$port")
$conn.Open()
foreach ($prop in $Q.PSObject.Properties) {
    try {
        $cmd = $conn.CreateCommand(); $cmd.CommandText = $prop.Value
        $rd = $cmd.ExecuteReader()
        $names = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $names += $rd.GetName($i) }
        $rows = @()
        while ($rd.Read()) { $row = @(); for ($i = 0; $i -lt $rd.FieldCount; $i++) { $x = $rd.GetValue($i); if ($x -is [DBNull]) { $x = $null }; $row += ,$x }; $rows += ,$row }
        $rd.Close()
        $Res.queries[$prop.Name] = [ordered]@{ columns = $names; rows = $rows }
    } catch { $Res.queries[$prop.Name] = [ordered]@{ error = $_.Exception.Message }; $Res.errors += "$($prop.Name) : $($_.Exception.Message)" }
}
$conn.Close()
$Res | ConvertTo-Json -Depth 10 -Compress | Set-Content -Path $OutFile -Encoding UTF8
"queries=$($Res.queries.Count) errors=$($Res.errors.Count)"; $Res.errors
