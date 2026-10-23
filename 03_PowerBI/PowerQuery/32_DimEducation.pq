// DimEducation  (Load)
// All 5 education levels from the lookup table. EducationKey = the dataset's education code (1-5).
let
    Source  = lkp_Education,
    Renamed = Table.RenameColumns(Source, {{"EducationCode", "EducationKey"}}),
    Final   = Table.SelectColumns(Renamed, {"EducationKey", "EducationLevel"}),
    Typed   = Table.TransformColumnTypes(Final, {{"EducationKey", Int64.Type}, {"EducationLevel", type text}})
in
    Typed
