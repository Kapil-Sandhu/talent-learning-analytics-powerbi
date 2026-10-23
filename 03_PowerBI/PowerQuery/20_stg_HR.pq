// stg_HR  (Staging, do not load)
// Cleaned, enriched employee table that all dimension and fact tables are built from.
let
    Source = src_HR,

    // 1. Drop 3 constant columns (EmployeeCount = 1, Over18 = "Y", StandardHours = 80)
    //    and 3 rate columns whose meaning the dataset does not document.
    RemovedColumns = Table.RemoveColumns(Source,
        {"EmployeeCount", "Over18", "StandardHours", "DailyRate", "HourlyRate", "MonthlyRate"}),

    // 2. EmployeeNumber is unique (validated in Step 2) -> primary key
    RenamedKey = Table.RenameColumns(RemovedColumns, {{"EmployeeNumber", "EmployeeID"}}),

    // 3. Trim all text columns (defensive cleaning)
    TrimmedText = Table.TransformColumns(RenamedKey, {
        {"Attrition", Text.Trim, type text}, {"BusinessTravel", Text.Trim, type text},
        {"Department", Text.Trim, type text}, {"EducationField", Text.Trim, type text},
        {"Gender", Text.Trim, type text}, {"JobRole", Text.Trim, type text},
        {"MaritalStatus", Text.Trim, type text}, {"OverTime", Text.Trim, type text}}),

    // 4. Numeric flags for DAX measures, and a readable status
    AddAttritionFlag = Table.AddColumn(TrimmedText, "AttritionFlag", each if [Attrition] = "Yes" then 1 else 0, Int64.Type),
    AddOverTimeFlag  = Table.AddColumn(AddAttritionFlag, "OverTimeFlag", each if [OverTime] = "Yes" then 1 else 0, Int64.Type),
    AddStatus        = Table.AddColumn(AddOverTimeFlag, "EmployeeStatus", each if [AttritionFlag] = 1 then "Left" else "Active", type text),

    // 5. Band keys from the band lookup tables (fnBandKey errors if a value fits no band)
    AddAgeBandKey      = Table.AddColumn(AddStatus, "AgeBandKey", each fnBandKey([Age], lkp_AgeBand), Int64.Type),
    AddTenureBandKey   = Table.AddColumn(AddAgeBandKey, "TenureBandKey", each fnBandKey([YearsAtCompany], lkp_TenureBand), Int64.Type),
    AddIncomeBandKey   = Table.AddColumn(AddTenureBandKey, "IncomeBandKey", each fnBandKey([MonthlyIncome], lkp_IncomeBand), Int64.Type),
    AddTrainingBandKey = Table.AddColumn(AddIncomeBandKey, "TrainingBandKey", each fnBandKey([TrainingTimesLastYear], lkp_TrainingBand), Int64.Type),

    // 6. Code -> label merges (Merge Queries, left outer join)
    MergeEnv   = Table.NestedJoin(AddTrainingBandKey, {"EnvironmentSatisfaction"}, lkp_Satisfaction, {"RatingCode"}, "EnvLkp", JoinKind.LeftOuter),
    ExpandEnv  = Table.ExpandTableColumn(MergeEnv, "EnvLkp", {"RatingLabel"}, {"EnvironmentSatisfactionLabel"}),
    MergeRel   = Table.NestedJoin(ExpandEnv, {"RelationshipSatisfaction"}, lkp_Satisfaction, {"RatingCode"}, "RelLkp", JoinKind.LeftOuter),
    ExpandRel  = Table.ExpandTableColumn(MergeRel, "RelLkp", {"RatingLabel"}, {"RelationshipSatisfactionLabel"}),
    MergeInv   = Table.NestedJoin(ExpandRel, {"JobInvolvement"}, lkp_Satisfaction, {"RatingCode"}, "InvLkp", JoinKind.LeftOuter),
    ExpandInv  = Table.ExpandTableColumn(MergeInv, "InvLkp", {"RatingLabel"}, {"JobInvolvementLabel"}),
    MergeWLB   = Table.NestedJoin(ExpandInv, {"WorkLifeBalance"}, lkp_WorkLifeBalance, {"WLBCode"}, "WLBLkp", JoinKind.LeftOuter),
    ExpandWLB  = Table.ExpandTableColumn(MergeWLB, "WLBLkp", {"WLBLabel"}, {"WorkLifeBalanceLabel"}),
    MergePerf  = Table.NestedJoin(ExpandWLB, {"PerformanceRating"}, lkp_PerformanceRating, {"PerformanceCode"}, "PerfLkp", JoinKind.LeftOuter),
    ExpandPerf = Table.ExpandTableColumn(MergePerf, "PerfLkp", {"PerformanceLabel"}, {"PerformanceRatingLabel"}),
    MergeTrav  = Table.NestedJoin(ExpandPerf, {"BusinessTravel"}, lkp_BusinessTravel, {"BusinessTravelCode"}, "TravLkp", JoinKind.LeftOuter),
    ExpandTrav = Table.ExpandTableColumn(MergeTrav, "TravLkp", {"BusinessTravelLabel", "SortOrder"}, {"BusinessTravelLabel", "BusinessTravelSort"}),

    // 7. Types for the merged columns, then restore employee order (merges do not guarantee order)
    TypedLabels = Table.TransformColumnTypes(ExpandTrav, {
        {"EnvironmentSatisfactionLabel", type text}, {"RelationshipSatisfactionLabel", type text},
        {"JobInvolvementLabel", type text}, {"WorkLifeBalanceLabel", type text},
        {"PerformanceRatingLabel", type text}, {"BusinessTravelLabel", type text}, {"BusinessTravelSort", Int64.Type}}),
    Sorted = Table.Sort(TypedLabels, {{"EmployeeID", Order.Ascending}})
in
    Sorted
