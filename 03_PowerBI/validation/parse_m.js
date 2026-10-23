// Syntax-checks every .pq file with Microsoft's official Power Query parser.
const PQP = require("@microsoft/powerquery-parser");
const fs = require("fs"), path = require("path");
(async () => {
  const dir = process.argv[2]; const out = [];
  for (const f of fs.readdirSync(dir).filter(x => x.endsWith(".pq")).sort()) {
    const text = fs.readFileSync(path.join(dir, f), "utf8");
    const task = await PQP.TaskUtils.tryLexParse(PQP.DefaultSettings, text);
    let ok = PQP.TaskUtils.isParseStageOk(task), msg = "";
    if (!ok) { const e = task.error; msg = (e && (e.message || (e.innerError && e.innerError.message))) || JSON.stringify(e).slice(0, 300); }
    out.push({ file: f, ok, msg });
  }
  console.log(JSON.stringify(out));
})();
