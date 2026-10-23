// lkp_WorkLifeBalance  (Staging, do not load)
// Code -> label mapping table Lkp_WorkLifeBalance from HR_Lookups.xlsx.
let
    Source   = fnGetLookup("Lkp_WorkLifeBalance"),
    Typed    = Table.TransformColumnTypes(Source, {{"WLBCode", Int64.Type}, {"WLBLabel", type text}, {"SortOrder", Int64.Type}}),
    Buffered = Table.Buffer(Typed)
in
    Buffered
