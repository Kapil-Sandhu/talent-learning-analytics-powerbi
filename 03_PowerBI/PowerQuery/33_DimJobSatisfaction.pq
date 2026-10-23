// DimJobSatisfaction  (Load)
// Job satisfaction scale 1-4 (Low ... Very High). Job satisfaction is a key attrition driver,
// so it gets its own dimension; the other ratings are attributes of DimEmployee.
let
    Source  = lkp_Satisfaction,
    Renamed = Table.RenameColumns(Source, {{"RatingCode", "JobSatisfactionKey"}, {"RatingLabel", "JobSatisfaction"}}),
    Final   = Table.SelectColumns(Renamed, {"JobSatisfactionKey", "JobSatisfaction"}),
    Typed   = Table.TransformColumnTypes(Final, {{"JobSatisfactionKey", Int64.Type}, {"JobSatisfaction", type text}})
in
    Typed
