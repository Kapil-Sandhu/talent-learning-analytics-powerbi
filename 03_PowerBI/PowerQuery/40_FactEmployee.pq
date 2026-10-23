// FactEmployee  (Load)
// Grain: one row per employee (point-in-time snapshot). Holds foreign keys + numeric columns for DAX.
let
    Source = stg_HR,

    // Surrogate keys for the data-driven dimensions
    MergeDept  = Table.NestedJoin(Source, {"Department"}, DimDepartment, {"Department"}, "DeptDim", JoinKind.LeftOuter),
    ExpandDept = Table.ExpandTableColumn(MergeDept, "DeptDim", {"DepartmentKey"}, {"DepartmentKey"}),
    MergeRole  = Table.NestedJoin(ExpandDept, {"JobRole"}, DimJobRole, {"JobRole"}, "RoleDim", JoinKind.LeftOuter),
    ExpandRole = Table.ExpandTableColumn(MergeRole, "RoleDim", {"JobRoleKey"}, {"JobRoleKey"}),

    // Keys that equal the source codes, plus "Score" copies of the ratings for averages
    AddEducationKey = Table.AddColumn(ExpandRole, "EducationKey", each [Education], Int64.Type),
    AddJobSatKey    = Table.AddColumn(AddEducationKey, "JobSatisfactionKey", each [JobSatisfaction], Int64.Type),
    Renamed = Table.RenameColumns(AddJobSatKey, {
                  {"JobSatisfaction", "JobSatisfactionScore"},
                  {"EnvironmentSatisfaction", "EnvironmentSatisfactionScore"},
                  {"RelationshipSatisfaction", "RelationshipSatisfactionScore"},
                  {"JobInvolvement", "JobInvolvementScore"},
                  {"WorkLifeBalance", "WorkLifeBalanceScore"},
                  {"PerformanceRating", "PerformanceRatingScore"}}),

    Final = Table.SelectColumns(Renamed, {
                  "EmployeeID", "DepartmentKey", "JobRoleKey", "EducationKey", "JobSatisfactionKey",
                  "AgeBandKey", "TenureBandKey", "IncomeBandKey", "TrainingBandKey",
                  "AttritionFlag", "OverTimeFlag", "Age", "MonthlyIncome", "PercentSalaryHike",
                  "DistanceFromHome", "NumCompaniesWorked", "TotalWorkingYears", "YearsAtCompany",
                  "YearsInCurrentRole", "YearsSinceLastPromotion", "YearsWithCurrManager",
                  "TrainingTimesLastYear", "JobSatisfactionScore", "EnvironmentSatisfactionScore",
                  "RelationshipSatisfactionScore", "JobInvolvementScore", "WorkLifeBalanceScore",
                  "PerformanceRatingScore"}),
    Typed = Table.TransformColumnTypes(Final, {
                  {"EmployeeID", Int64.Type}, {"DepartmentKey", Int64.Type}, {"JobRoleKey", Int64.Type},
                  {"EducationKey", Int64.Type}, {"JobSatisfactionKey", Int64.Type}, {"AgeBandKey", Int64.Type},
                  {"TenureBandKey", Int64.Type}, {"IncomeBandKey", Int64.Type}, {"TrainingBandKey", Int64.Type},
                  {"AttritionFlag", Int64.Type}, {"OverTimeFlag", Int64.Type}, {"Age", Int64.Type},
                  {"MonthlyIncome", Int64.Type}, {"PercentSalaryHike", Int64.Type}, {"DistanceFromHome", Int64.Type},
                  {"NumCompaniesWorked", Int64.Type}, {"TotalWorkingYears", Int64.Type}, {"YearsAtCompany", Int64.Type},
                  {"YearsInCurrentRole", Int64.Type}, {"YearsSinceLastPromotion", Int64.Type},
                  {"YearsWithCurrManager", Int64.Type}, {"TrainingTimesLastYear", Int64.Type},
                  {"JobSatisfactionScore", Int64.Type}, {"EnvironmentSatisfactionScore", Int64.Type},
                  {"RelationshipSatisfactionScore", Int64.Type}, {"JobInvolvementScore", Int64.Type},
                  {"WorkLifeBalanceScore", Int64.Type}, {"PerformanceRatingScore", Int64.Type}}),
    Sorted = Table.Sort(Typed, {{"EmployeeID", Order.Ascending}})
in
    Sorted
