// lkp_TenureBand  (Staging, do not load)
// Band table Lkp_TenureBand from HR_Lookups.xlsx, renamed to the generic columns used by fnBandKey:
// Band (label), Min, Max (inclusive bounds), BandKey (= SortOrder).
let
    Source   = fnGetLookup("Lkp_TenureBand"),
    Typed    = Table.TransformColumnTypes(Source, {{"TenureBand", type text}, {"MinYears", Int64.Type}, {"MaxYears", Int64.Type}, {"SortOrder", Int64.Type}}),
    Renamed  = Table.RenameColumns(Typed, {{"TenureBand", "Band"}, {"MinYears", "Min"}, {"MaxYears", "Max"}, {"SortOrder", "BandKey"}}),
    Buffered = Table.Buffer(Renamed)
in
    Buffered
