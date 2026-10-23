// DimDepartment  (Load)
// One row per distinct Department found in the data; surrogate key DepartmentKey = 1..n in alphabetical order.
let
    Source   = stg_HR,
    Selected = Table.SelectColumns(Source, {"Department"}),
    Distinct = Table.Distinct(Selected),
    Sorted   = Table.Sort(Distinct, {{"Department", Order.Ascending}}),
    AddKey   = Table.AddIndexColumn(Sorted, "DepartmentKey", 1, 1, Int64.Type),
    Final    = Table.SelectColumns(AddKey, {"DepartmentKey", "Department"}),
    Typed    = Table.TransformColumnTypes(Final, {{"DepartmentKey", Int64.Type}, {"Department", type text}})
in
    Typed
