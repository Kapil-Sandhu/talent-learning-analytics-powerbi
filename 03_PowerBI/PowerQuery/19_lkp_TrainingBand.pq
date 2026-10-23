// lkp_TrainingBand  (Staging, do not load)
// Band table Lkp_TrainingBand from HR_Lookups.xlsx, renamed to the generic columns used by fnBandKey:
// Band (label), Min, Max (inclusive bounds), BandKey (= SortOrder).
let
    Source   = fnGetLookup("Lkp_TrainingBand"),
    Typed    = Table.TransformColumnTypes(Source, {{"TrainingBand", type text}, {"MinTrainings", Int64.Type}, {"MaxTrainings", Int64.Type}, {"SortOrder", Int64.Type}}),
    Renamed  = Table.RenameColumns(Typed, {{"TrainingBand", "Band"}, {"MinTrainings", "Min"}, {"MaxTrainings", "Max"}, {"SortOrder", "BandKey"}}),
    Buffered = Table.Buffer(Renamed)
in
    Buffered
