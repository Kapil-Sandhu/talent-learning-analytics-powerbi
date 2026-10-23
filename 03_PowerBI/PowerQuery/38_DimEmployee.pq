// DimEmployee  (Load)
// One row per employee with descriptive attributes used for slicing and the drill-through page.
// Each rating label has a matching *Sort column (the original code) for "Sort by column".
let
    Source  = stg_HR,
    Final   = Table.SelectColumns(Source, {
                  "EmployeeID", "EmployeeStatus", "Gender", "MaritalStatus", "EducationField",
                  "BusinessTravelLabel", "BusinessTravelSort", "OverTime", "JobLevel", "StockOptionLevel",
                  "EnvironmentSatisfactionLabel", "EnvironmentSatisfaction",
                  "RelationshipSatisfactionLabel", "RelationshipSatisfaction",
                  "JobInvolvementLabel", "JobInvolvement",
                  "WorkLifeBalanceLabel", "WorkLifeBalance",
                  "PerformanceRatingLabel", "PerformanceRating"}),
    // Rename in two steps: codes -> *Sort first, then labels -> the plain name (avoids a name clash)
    RenamedCodes  = Table.RenameColumns(Final, {
                  {"EnvironmentSatisfaction", "EnvironmentSatisfactionSort"},
                  {"RelationshipSatisfaction", "RelationshipSatisfactionSort"},
                  {"JobInvolvement", "JobInvolvementSort"},
                  {"WorkLifeBalance", "WorkLifeBalanceSort"},
                  {"PerformanceRating", "PerformanceRatingSort"}}),
    Renamed = Table.RenameColumns(RenamedCodes, {
                  {"BusinessTravelLabel", "BusinessTravel"},
                  {"EnvironmentSatisfactionLabel", "EnvironmentSatisfaction"},
                  {"RelationshipSatisfactionLabel", "RelationshipSatisfaction"},
                  {"JobInvolvementLabel", "JobInvolvement"},
                  {"WorkLifeBalanceLabel", "WorkLifeBalance"},
                  {"PerformanceRatingLabel", "PerformanceRating"}}),
    Typed   = Table.TransformColumnTypes(Renamed, {
                  {"EmployeeID", Int64.Type}, {"EmployeeStatus", type text}, {"Gender", type text},
                  {"MaritalStatus", type text}, {"EducationField", type text}, {"BusinessTravel", type text},
                  {"BusinessTravelSort", Int64.Type}, {"OverTime", type text}, {"JobLevel", Int64.Type},
                  {"StockOptionLevel", Int64.Type}, {"EnvironmentSatisfaction", type text},
                  {"EnvironmentSatisfactionSort", Int64.Type}, {"RelationshipSatisfaction", type text},
                  {"RelationshipSatisfactionSort", Int64.Type}, {"JobInvolvement", type text},
                  {"JobInvolvementSort", Int64.Type}, {"WorkLifeBalance", type text},
                  {"WorkLifeBalanceSort", Int64.Type}, {"PerformanceRating", type text},
                  {"PerformanceRatingSort", Int64.Type}})
in
    Typed
