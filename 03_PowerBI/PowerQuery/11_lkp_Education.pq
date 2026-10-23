// lkp_Education  (Staging, do not load)
// Code -> label mapping table Lkp_Education from HR_Lookups.xlsx.
let
    Source   = fnGetLookup("Lkp_Education"),
    Typed    = Table.TransformColumnTypes(Source, {{"EducationCode", Int64.Type}, {"EducationLevel", type text}, {"SortOrder", Int64.Type}}),
    Buffered = Table.Buffer(Typed)
in
    Buffered
