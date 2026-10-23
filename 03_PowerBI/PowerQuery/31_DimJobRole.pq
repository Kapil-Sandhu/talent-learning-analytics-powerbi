// DimJobRole  (Load)
// One row per distinct JobRole found in the data; surrogate key JobRoleKey = 1..n in alphabetical order.
let
    Source   = stg_HR,
    Selected = Table.SelectColumns(Source, {"JobRole"}),
    Distinct = Table.Distinct(Selected),
    Sorted   = Table.Sort(Distinct, {{"JobRole", Order.Ascending}}),
    AddKey   = Table.AddIndexColumn(Sorted, "JobRoleKey", 1, 1, Int64.Type),
    Final    = Table.SelectColumns(AddKey, {"JobRoleKey", "JobRole"}),
    Typed    = Table.TransformColumnTypes(Final, {{"JobRoleKey", Int64.Type}, {"JobRole", type text}})
in
    Typed
