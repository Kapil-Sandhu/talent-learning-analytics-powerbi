// lkp_IncomeBand  (Staging, do not load)
// Band table Lkp_IncomeBand from HR_Lookups.xlsx, renamed to the generic columns used by fnBandKey:
// Band (label), Min, Max (inclusive bounds), BandKey (= SortOrder).
let
    Source   = fnGetLookup("Lkp_IncomeBand"),
    Typed    = Table.TransformColumnTypes(Source, {{"IncomeBand", type text}, {"MinIncome", Int64.Type}, {"MaxIncome", Int64.Type}, {"SortOrder", Int64.Type}}),
    Renamed  = Table.RenameColumns(Typed, {{"IncomeBand", "Band"}, {"MinIncome", "Min"}, {"MaxIncome", "Max"}, {"SortOrder", "BandKey"}}),
    Buffered = Table.Buffer(Renamed)
in
    Buffered
