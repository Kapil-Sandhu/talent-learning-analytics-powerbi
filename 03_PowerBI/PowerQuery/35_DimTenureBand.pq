// DimTenureBand  (Load)
// Band dimension from the band lookup. TenureBandKey = SortOrder -> use it for "Sort by column" on TenureBand.
let
    Source  = lkp_TenureBand,
    Renamed = Table.RenameColumns(Source, {{"BandKey", "TenureBandKey"}, {"Band", "TenureBand"}, {"Min", "MinYears"}, {"Max", "MaxYears"}}),
    Final   = Table.SelectColumns(Renamed, {"TenureBandKey", "TenureBand", "MinYears", "MaxYears"}),
    Typed   = Table.TransformColumnTypes(Final, {{"TenureBandKey", Int64.Type}, {"TenureBand", type text}, {"MinYears", Int64.Type}, {"MaxYears", Int64.Type}})
in
    Typed
