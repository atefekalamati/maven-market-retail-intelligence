# Parse a TMDL folder with the Tabular Object Model shipped in Power BI Desktop
# and print a JSON summary of the deserialized model.
#
# Usage (Windows PowerShell 5.1):
#   powershell -NoProfile -File tests/tmdl_parse.ps1 dashboard/MavenMarket.SemanticModel/definition
param(
    [Parameter(Mandatory = $true)][string]$DefinitionPath,
    [string]$DesktopBin = 'C:\Program Files\Microsoft Power BI Desktop\bin'
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
[void][Reflection.Assembly]::LoadFrom((Join-Path $DesktopBin 'Microsoft.PowerBI.Tabular.dll'))

$resolved = (Resolve-Path $DefinitionPath).Path
$database = [Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder($resolved)
$model = $database.Model

$tables = foreach ($table in $model.Tables) {
    [ordered]@{
        name         = $table.Name
        dataCategory = $table.DataCategory
        columns      = @($table.Columns | Where-Object { $_.Type -ne 'RowNumber' } | ForEach-Object {
            [ordered]@{
                name         = $_.Name
                dataType     = $_.DataType.ToString()
                isHidden     = $_.IsHidden
                isKey        = $_.IsKey
                sortByColumn = if ($_.SortByColumn) { $_.SortByColumn.Name } else { $null }
            }
        })
        measures     = @($table.Measures | ForEach-Object {
            [ordered]@{
                name          = $_.Name
                expression    = $_.Expression
                formatString  = $_.FormatString
                displayFolder = $_.DisplayFolder
            }
        })
        partitions   = @($table.Partitions | ForEach-Object { $_.SourceType.ToString() })
    }
}

$relationships = foreach ($relationship in $model.Relationships) {
    [ordered]@{
        fromTable          = $relationship.FromTable.Name
        fromColumn         = $relationship.FromColumn.Name
        toTable            = $relationship.ToTable.Name
        toColumn           = $relationship.ToColumn.Name
        isActive           = $relationship.IsActive
        fromCardinality    = $relationship.FromCardinality.ToString()
        toCardinality      = $relationship.ToCardinality.ToString()
        crossFilteringBehavior = $relationship.CrossFilteringBehavior.ToString()
    }
}

$annotations = @{}
foreach ($annotation in $model.Annotations) { $annotations[$annotation.Name] = $annotation.Value }

$summary = [ordered]@{
    compatibilityLevel       = $database.CompatibilityLevel
    culture                  = $model.Culture
    maxParallelismPerRefresh = $model.MaxParallelismPerRefresh
    discourageImplicitMeasures = $model.DiscourageImplicitMeasures
    annotations              = $annotations
    expressions              = @($model.Expressions | ForEach-Object { [ordered]@{ name = $_.Name; expression = $_.Expression } })
    tables                   = @($tables)
    relationships            = @($relationships)
}
$summary | ConvertTo-Json -Depth 8 -Compress
