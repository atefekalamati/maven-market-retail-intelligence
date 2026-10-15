# Bridge to the Analysis Services engine of an open Power BI Desktop report.
#
# Finds the msmdsrv.exe instance that belongs to the Power BI Desktop window
# whose title contains -WindowTitle, then either refreshes the model (TOM) or
# runs DAX queries (ADOMD.NET) and writes the results as JSON.
#
# Usage (Windows PowerShell 5.1):
#   powershell -NoProfile -File scripts/power_bi_desktop_engine.ps1 -Action port
#   powershell -NoProfile -File scripts/power_bi_desktop_engine.ps1 -Action refresh
#   powershell -NoProfile -File scripts/power_bi_desktop_engine.ps1 -Action query `
#       -RequestPath queries.json -ResultPath results.json
#
# queries.json: [{"id": "...", "dax": "EVALUATE ..."}, ...]
# results.json: [{"id": "...", "columns": [...], "rows": [[...], ...], "error": null}, ...]
param(
    [Parameter(Mandatory = $true)][ValidateSet('port', 'refresh', 'query')][string]$Action,
    [string]$WindowTitle = 'MavenMarket',
    [string]$RequestPath,
    [string]$ResultPath,
    [string]$DesktopBin = 'C:\Program Files\Microsoft Power BI Desktop\bin'
)

$ErrorActionPreference = 'Stop'

function Get-EnginePort {
    $desktop = @(Get-Process PBIDesktop -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -like "*$WindowTitle*" })
    if ($desktop.Count -ne 1) {
        throw "Expected one Power BI Desktop window titled '*$WindowTitle*', found $($desktop.Count)."
    }
    $engine = Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe' AND ParentProcessId=$($desktop[0].Id)"
    if (-not $engine) { throw "No msmdsrv.exe found for Power BI Desktop process $($desktop[0].Id)." }
    if ($engine.CommandLine -notmatch '-s\s+"([^"]+)"') { throw 'Could not read the engine data folder.' }
    $portFile = Join-Path $Matches[1] 'msmdsrv.port.txt'
    $port = (Get-Content $portFile -Raw -Encoding Unicode).Trim()
    if ($port -notmatch '^\d+$') { throw "Unexpected port value '$port' in $portFile." }
    return [int]$port
}

$port = Get-EnginePort
$connectionString = "Data Source=localhost:$port"

switch ($Action) {
    'port' {
        $port
    }
    'refresh' {
        [void][Reflection.Assembly]::LoadFrom((Join-Path $DesktopBin 'Microsoft.PowerBI.Tabular.dll'))
        $server = New-Object Microsoft.AnalysisServices.Tabular.Server
        $server.Connect($connectionString)
        try {
            $database = $server.Databases[0]
            $database.Model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
            [void]$database.Model.SaveChanges()
            foreach ($table in $database.Model.Tables) {
                foreach ($partition in $table.Partitions) {
                    "{0}: {1}" -f $table.Name, $partition.State
                }
            }
        }
        finally {
            $server.Disconnect()
        }
    }
    'query' {
        [void][Reflection.Assembly]::LoadFrom((Join-Path $DesktopBin 'Microsoft.PowerBI.AdomdClient.dll'))
        $requests = Get-Content $RequestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $connection = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection $connectionString
        $connection.Open()
        $results = New-Object System.Collections.ArrayList
        try {
            foreach ($request in $requests) {
                $result = [ordered]@{ id = $request.id; columns = @(); rows = @(); error = $null }
                try {
                    $command = $connection.CreateCommand()
                    $command.CommandText = $request.dax
                    $reader = $command.ExecuteReader()
                    $columns = @(for ($i = 0; $i -lt $reader.FieldCount; $i++) { $reader.GetName($i) })
                    $rows = New-Object System.Collections.ArrayList
                    while ($reader.Read()) {
                        $row = @(for ($i = 0; $i -lt $reader.FieldCount; $i++) {
                            $value = $reader.GetValue($i)
                            if ($null -eq $value -or $value -is [System.DBNull]) { $null }
                            elseif ($value -is [decimal] -or $value -is [double] -or $value -is [long] -or $value -is [int]) {
                                $value.ToString([Globalization.CultureInfo]::InvariantCulture)
                            }
                            else { [string]$value }
                        })
                        [void]$rows.Add($row)
                    }
                    $reader.Close()
                    $result.columns = $columns
                    $result.rows = $rows.ToArray()
                }
                catch {
                    $result.error = $_.Exception.Message
                }
                [void]$results.Add($result)
            }
        }
        finally {
            $connection.Close()
        }
        $json = ConvertTo-Json -InputObject $results.ToArray() -Depth 6 -Compress
        [IO.File]::WriteAllText($ResultPath, $json, (New-Object Text.UTF8Encoding $false))
    }
}
