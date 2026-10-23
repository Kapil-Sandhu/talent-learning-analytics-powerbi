// lkp_PerformanceRating  (Staging, do not load)
// Code -> label mapping table Lkp_PerformanceRating from HR_Lookups.xlsx.
let
    Source   = fnGetLookup("Lkp_PerformanceRating"),
    Typed    = Table.TransformColumnTypes(Source, {{"PerformanceCode", Int64.Type}, {"PerformanceLabel", type text}, {"SortOrder", Int64.Type}}),
    Buffered = Table.Buffer(Typed)
in
    Buffered
