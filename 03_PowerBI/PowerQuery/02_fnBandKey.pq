// fnBandKey  (Function, do not load)
// Returns the BandKey of the single band where Min <= Value <= Max.
// Raises an error if the value falls in no band or in more than one band (so bad band tables never load silently).
(Value as nullable number, Bands as table) as nullable number =>
let
    Matches = Table.SelectRows(Bands, each [Min] <= Value and Value <= [Max]),
    Count   = Table.RowCount(Matches),
    Key     = if Value = null then null
              else if Count = 1 then Matches{0}[BandKey]
              else error Error.Record("Band lookup failed",
                         "Value " & Number.ToText(Value) & " matches " & Number.ToText(Count) & " bands")
in
    Key
