// lkp_AgeBand  (Staging, do not load)
// Band table Lkp_AgeBand from HR_Lookups.xlsx, renamed to the generic columns used by fnBandKey:
// Band (label), Min, Max (inclusive bounds), BandKey (= SortOrder).
let
    Source   = fnGetLookup("Lkp_AgeBand"),
    Typed    = Table.TransformColumnTypes(Source, {{"AgeBand", type text}, {"MinAge", Int64.Type}, {"MaxAge", Int64.Type}, {"SortOrder", Int64.Type}}),
    Renamed  = Table.RenameColumns(Typed, {{"AgeBand", "Band"}, {"MinAge", "Min"}, {"MaxAge", "Max"}, {"SortOrder", "BandKey"}}),
    Buffered = Table.Buffer(Renamed)
in
    Buffered
