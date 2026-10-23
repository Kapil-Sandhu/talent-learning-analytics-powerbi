// fnGetLookup  (Function, do not load)
// Returns one Excel TABLE (by its table name, e.g. "Lkp_Education") from 01_Data\lookups\HR_Lookups.xlsx.
(TableName as text) as table =>
let
    Folder   = if Text.EndsWith(ProjectFolder, "\") then ProjectFolder else ProjectFolder & "\",   // works with or without trailing \
    Source   = Excel.Workbook(File.Contents(Folder & "01_Data\lookups\HR_Lookups.xlsx"), true, true),
    Selected = Table.SelectRows(Source, each [Kind] = "Table" and [Name] = TableName),
    Result   = if Table.RowCount(Selected) = 1
               then Selected{0}[Data]
               else error Error.Record("Lookup not found", "Table '" & TableName & "' was not found in HR_Lookups.xlsx")
in
    Result
