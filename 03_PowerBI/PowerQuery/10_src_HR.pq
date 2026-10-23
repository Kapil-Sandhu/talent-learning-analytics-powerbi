// src_HR  (Staging, do not load)
// Reads the raw CSV. Encoding 65001 = UTF-8, which also removes the BOM in front of the first header ("Age").
// Every one of the 35 columns gets an explicit data type (no automatic type detection).
let
    Folder   = if Text.EndsWith(ProjectFolder, "\") then ProjectFolder else ProjectFolder & "\",   // works with or without trailing \
    Source   = Csv.Document(
                   File.Contents(Folder & "01_Data\raw\WA_Fn-UseC_-HR-Employee-Attrition.csv"),
                   [Delimiter = ",", Columns = 35, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {
                   {"Age", Int64.Type}, {"Attrition", type text}, {"BusinessTravel", type text},
                   {"DailyRate", Int64.Type}, {"Department", type text}, {"DistanceFromHome", Int64.Type},
                   {"Education", Int64.Type}, {"EducationField", type text}, {"EmployeeCount", Int64.Type},
                   {"EmployeeNumber", Int64.Type}, {"EnvironmentSatisfaction", Int64.Type}, {"Gender", type text},
                   {"HourlyRate", Int64.Type}, {"JobInvolvement", Int64.Type}, {"JobLevel", Int64.Type},
                   {"JobRole", type text}, {"JobSatisfaction", Int64.Type}, {"MaritalStatus", type text},
                   {"MonthlyIncome", Int64.Type}, {"MonthlyRate", Int64.Type}, {"NumCompaniesWorked", Int64.Type},
                   {"Over18", type text}, {"OverTime", type text}, {"PercentSalaryHike", Int64.Type},
                   {"PerformanceRating", Int64.Type}, {"RelationshipSatisfaction", Int64.Type},
                   {"StandardHours", Int64.Type}, {"StockOptionLevel", Int64.Type}, {"TotalWorkingYears", Int64.Type},
                   {"TrainingTimesLastYear", Int64.Type}, {"WorkLifeBalance", Int64.Type}, {"YearsAtCompany", Int64.Type},
                   {"YearsInCurrentRole", Int64.Type}, {"YearsSinceLastPromotion", Int64.Type},
                   {"YearsWithCurrManager", Int64.Type}}, "en-US")
in
    Typed
