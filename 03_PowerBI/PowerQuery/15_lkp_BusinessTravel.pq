// lkp_BusinessTravel  (Staging, do not load)
// Code -> label mapping table Lkp_BusinessTravel from HR_Lookups.xlsx.
let
    Source   = fnGetLookup("Lkp_BusinessTravel"),
    Typed    = Table.TransformColumnTypes(Source, {{"BusinessTravelCode", type text}, {"BusinessTravelLabel", type text}, {"SortOrder", Int64.Type}}),
    Buffered = Table.Buffer(Typed)
in
    Buffered
