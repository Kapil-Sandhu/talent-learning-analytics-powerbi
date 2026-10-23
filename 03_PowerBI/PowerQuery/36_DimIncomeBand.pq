// DimIncomeBand  (Load)
// Band dimension from the band lookup. IncomeBandKey = SortOrder -> use it for "Sort by column" on IncomeBand.
let
    Source  = lkp_IncomeBand,
    Renamed = Table.RenameColumns(Source, {{"BandKey", "IncomeBandKey"}, {"Band", "IncomeBand"}, {"Min", "MinIncome"}, {"Max", "MaxIncome"}}),
    Final   = Table.SelectColumns(Renamed, {"IncomeBandKey", "IncomeBand", "MinIncome", "MaxIncome"}),
    Typed   = Table.TransformColumnTypes(Final, {{"IncomeBandKey", Int64.Type}, {"IncomeBand", type text}, {"MinIncome", Int64.Type}, {"MaxIncome", Int64.Type}})
in
    Typed
