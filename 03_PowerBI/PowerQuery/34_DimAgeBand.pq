// DimAgeBand  (Load)
// Band dimension from the band lookup. AgeBandKey = SortOrder -> use it for "Sort by column" on AgeBand.
let
    Source  = lkp_AgeBand,
    Renamed = Table.RenameColumns(Source, {{"BandKey", "AgeBandKey"}, {"Band", "AgeBand"}, {"Min", "MinAge"}, {"Max", "MaxAge"}}),
    Final   = Table.SelectColumns(Renamed, {"AgeBandKey", "AgeBand", "MinAge", "MaxAge"}),
    Typed   = Table.TransformColumnTypes(Final, {{"AgeBandKey", Int64.Type}, {"AgeBand", type text}, {"MinAge", Int64.Type}, {"MaxAge", Int64.Type}})
in
    Typed
