// DimTrainingBand  (Load)
// Band dimension from the band lookup. TrainingBandKey = SortOrder -> use it for "Sort by column" on TrainingBand.
let
    Source  = lkp_TrainingBand,
    Renamed = Table.RenameColumns(Source, {{"BandKey", "TrainingBandKey"}, {"Band", "TrainingBand"}, {"Min", "MinTrainings"}, {"Max", "MaxTrainings"}}),
    Final   = Table.SelectColumns(Renamed, {"TrainingBandKey", "TrainingBand", "MinTrainings", "MaxTrainings"}),
    Typed   = Table.TransformColumnTypes(Final, {{"TrainingBandKey", Int64.Type}, {"TrainingBand", type text}, {"MinTrainings", Int64.Type}, {"MaxTrainings", Int64.Type}})
in
    Typed
