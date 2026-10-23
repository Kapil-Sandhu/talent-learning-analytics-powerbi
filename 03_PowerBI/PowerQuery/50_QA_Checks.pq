// QA_Checks  (Load, then hide it in Report view)
// Runs every time you refresh. Every row must show Result = "PASS".
// Expected values come from the validated Step 2 profiling (01_Data / 02_Excel_Profiling).
let
    Fact = FactEmployee,
    Emp  = DimEmployee,
    DroppedColumns = {"EmployeeCount", "Over18", "StandardHours", "DailyRate", "HourlyRate", "MonthlyRate"},

    // helpers
    OrphanCount = (FactKeys as list, DimKeys as list) as number =>
        List.Count(List.Difference(List.Distinct(FactKeys), DimKeys)),
    RowsWithNull = (t as table) as number =>
        Table.RowCount(Table.SelectRows(t, each List.Contains(Record.FieldValues(_), null))),
    DuplicateKeys = (Keys as list) as number =>
        List.Count(Keys) - List.Count(List.Distinct(Keys)),

    Checks = {
        // row and column counts
        {"FactEmployee rows", Table.RowCount(Fact), 1470},
        {"DimEmployee rows", Table.RowCount(Emp), 1470},
        {"FactEmployee columns", Table.ColumnCount(Fact), 28},
        {"DimEmployee columns", Table.ColumnCount(Emp), 20},
        {"DimDepartment rows", Table.RowCount(DimDepartment), 3},
        {"DimJobRole rows", Table.RowCount(DimJobRole), 9},
        {"DimEducation rows", Table.RowCount(DimEducation), 5},
        {"DimJobSatisfaction rows", Table.RowCount(DimJobSatisfaction), 4},
        {"DimAgeBand rows", Table.RowCount(DimAgeBand), 5},
        {"DimTenureBand rows", Table.RowCount(DimTenureBand), 4},
        {"DimIncomeBand rows", Table.RowCount(DimIncomeBand), 5},
        {"DimTrainingBand rows", Table.RowCount(DimTrainingBand), 4},
        // keys
        {"Duplicate EmployeeID in FactEmployee", DuplicateKeys(Fact[EmployeeID]), 0},
        {"Duplicate EmployeeID in DimEmployee", DuplicateKeys(Emp[EmployeeID]), 0},
        {"Duplicate DepartmentKey in DimDepartment", DuplicateKeys(DimDepartment[DepartmentKey]), 0},
        {"Duplicate JobRoleKey in DimJobRole", DuplicateKeys(DimJobRole[JobRoleKey]), 0},
        // completeness
        {"Rows with a null in FactEmployee", RowsWithNull(Fact), 0},
        {"Rows with a null in DimEmployee", RowsWithNull(Emp), 0},
        // referential integrity (every fact key exists in its dimension)
        {"Orphan EmployeeID (Fact -> DimEmployee)", OrphanCount(Fact[EmployeeID], Emp[EmployeeID]), 0},
        {"Orphan DepartmentKey", OrphanCount(Fact[DepartmentKey], DimDepartment[DepartmentKey]), 0},
        {"Orphan JobRoleKey", OrphanCount(Fact[JobRoleKey], DimJobRole[JobRoleKey]), 0},
        {"Orphan EducationKey", OrphanCount(Fact[EducationKey], DimEducation[EducationKey]), 0},
        {"Orphan JobSatisfactionKey", OrphanCount(Fact[JobSatisfactionKey], DimJobSatisfaction[JobSatisfactionKey]), 0},
        {"Orphan AgeBandKey", OrphanCount(Fact[AgeBandKey], DimAgeBand[AgeBandKey]), 0},
        {"Orphan TenureBandKey", OrphanCount(Fact[TenureBandKey], DimTenureBand[TenureBandKey]), 0},
        {"Orphan IncomeBandKey", OrphanCount(Fact[IncomeBandKey], DimIncomeBand[IncomeBandKey]), 0},
        {"Orphan TrainingBandKey", OrphanCount(Fact[TrainingBandKey], DimTrainingBand[TrainingBandKey]), 0},
        // control totals (must equal Step 2)
        {"Sum AttritionFlag (leavers)", List.Sum(Fact[AttritionFlag]), 237},
        {"Sum OverTimeFlag", List.Sum(Fact[OverTimeFlag]), 416},
        {"Sum TrainingTimesLastYear", List.Sum(Fact[TrainingTimesLastYear]), 4115},
        {"Sum MonthlyIncome", List.Sum(Fact[MonthlyIncome]), 9559309},
        {"Sum YearsAtCompany", List.Sum(Fact[YearsAtCompany]), 10302},
        {"Sum JobSatisfactionScore", List.Sum(Fact[JobSatisfactionScore]), 4011},
        {"Employees with Status = Left", Table.RowCount(Table.SelectRows(Emp, each [EmployeeStatus] = "Left")), 237},
        // cleaning
        {"Dropped columns still present in stg_HR", List.Count(List.Intersect({Table.ColumnNames(stg_HR), DroppedColumns})), 0}
    },

    AsTable   = Table.FromRows(Checks, type table [Check = text, Actual = number, Expected = number]),
    AddNo     = Table.AddIndexColumn(AsTable, "CheckNo", 1, 1, Int64.Type),
    AddResult = Table.AddColumn(AddNo, "Result", each if [Actual] = [Expected] then "PASS" else "FAIL", type text),
    Final     = Table.ReorderColumns(AddResult, {"CheckNo", "Check", "Actual", "Expected", "Result"})
in
    Final
