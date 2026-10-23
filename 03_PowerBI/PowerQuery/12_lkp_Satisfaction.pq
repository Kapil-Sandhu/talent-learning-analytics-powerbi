// lkp_Satisfaction  (Staging, do not load)
// Code -> label mapping table Lkp_Satisfaction from HR_Lookups.xlsx.
let
    Source   = fnGetLookup("Lkp_Satisfaction"),
    Typed    = Table.TransformColumnTypes(Source, {{"RatingCode", Int64.Type}, {"RatingLabel", type text}, {"SortOrder", Int64.Type}}),
    Buffered = Table.Buffer(Typed)
in
    Buffered
