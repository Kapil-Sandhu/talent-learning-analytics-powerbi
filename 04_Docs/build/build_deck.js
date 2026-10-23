// Step 8 - build the 5-slide deck 05_Presentation/Talent_Learning_Deck.pptx from 05_Presentation/deck_content.json
// (written by build_docs.py, where every number is logged with its source). Nothing numeric is typed here.
// Run from the project root:  node 04_Docs/build/build_deck.js <path to the pptx skill's scripts/apply_theme.js>
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = process.cwd();
const C = JSON.parse(fs.readFileSync(path.join(ROOT, "05_Presentation", "deck_content.json"), "utf8"));
const OUT = path.join(ROOT, "05_Presentation", "Talent_Learning_Deck.pptx");
const APPLY_THEME = process.argv[2];

const THEME = {
  name: "Talent Analytics",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1E2A44", lt1: "FFFFFF", dk2: "5B6B82", lt2: "F2F5FA",
    accent1: "118DFF", accent2: "E4572E", accent3: "0B5CAD", accent4: "9AA7BA", accent5: "D7E8FF", accent6: "2BB673",
    hlink: "118DFF", folHlink: "0B5CAD",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.33 x 7.5 in
pres.title = "Talent & Learning Analytics - summary";
pres.author = "Kapil Sandhu";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const S = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "DARK_TITLE",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.2, w: 12.1, h: 1.7, fontSize: 40, bold: true, color: S.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "DARK",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.45, w: 12.1, h: 1.0, fontSize: 36, bold: true, color: S.background1, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "LIGHT",
  background: { color: HEX.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.4, w: 12.1, h: 0.9, fontSize: 36, bold: true, color: S.text1, align: "left", valign: "top", margin: 0 }, text: "" } },
    { text: { text: "Talent & Learning Analytics Dashboard", options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: S.text2, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: HEX.dk2, align: "right" },
});

function circleNum(slide, n, x, y, d, fill, color, name) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill }, objectName: name + " circle" });
  slide.addText(String(n), { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: 16, bold: true, color, margin: 0, isTextBox: true, objectName: name + " number" });
}

// ---------------------------------------------------------------- 1. title / problem
{
  const T = C.title;
  pres.addSection({ title: "Problem" });
  const s = pres.addSlide({ masterName: "DARK_TITLE", sectionTitle: "Problem" });
  s.addText(T.kicker, { x: 0.6, y: 0.6, w: 12, h: 0.45, fontSize: 18, bold: true, color: S.accent1, margin: 0, isTextBox: true, objectName: "kicker" });
  s.addText(T.headline, { placeholder: "title" });
  T.stats.forEach(([v, lab], i) => {
    const x = 0.6 + i * 4.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.25, w: 3.7, h: 2.1, rectRadius: 0.12, fill: { color: "2A3A5C" }, line: { color: "2A3A5C" }, objectName: `stat ${i + 1} card` });
    s.addText(v, { x: x + 0.3, y: 3.45, w: 3.1, h: 1.15, fontSize: 60, bold: true, color: i === 2 ? S.accent2 : S.background1, margin: 0, isTextBox: true, objectName: `stat ${i + 1} value` });
    s.addText(lab, { x: x + 0.3, y: 4.6, w: 3.1, h: 0.5, fontSize: 18, color: S.accent5, margin: 0, isTextBox: true, objectName: `stat ${i + 1} label` });
  });
  s.addText(T.sub, { x: 0.6, y: 6.3, w: 12.1, h: 0.5, fontSize: 14, color: S.accent4, margin: 0, isTextBox: true, objectName: "subtitle" });
  s.addNotes(T.notes);
}

// ---------------------------------------------------------------- 2. data & approach
{
  const T = C.data;
  pres.addSection({ title: "Approach" });
  const s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Approach" });
  s.addText(T.title, { placeholder: "title" });
  const n = T.steps.length, w = 2.2, gap = (12.1 - n * w) / (n - 1);
  T.steps.forEach(([head, body], i) => {
    const x = 0.6 + i * (w + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w, h: 2.15, rectRadius: 0.12, fill: { color: HEX.lt2 }, line: { color: HEX.lt2 }, objectName: `step ${i + 1} card` });
    circleNum(s, i + 1, x + 0.25, 1.85, 0.55, HEX.accent1, HEX.lt1, `step ${i + 1}`);
    s.addText(head, { x: x + 0.25, y: 2.55, w: w - 0.45, h: 0.45, fontSize: 18, bold: true, color: S.text1, margin: 0, isTextBox: true, objectName: `step ${i + 1} head` });
    s.addText(body, { x: x + 0.25, y: 3.0, w: w - 0.45, h: 0.65, fontSize: 14, color: S.text2, margin: 0, valign: "top", isTextBox: true, objectName: `step ${i + 1} body` });
    if (i < n - 1) s.addShape(pres.shapes.CHEVRON, { x: x + w + gap / 2 - 0.08, y: 2.55, w: 0.16, h: 0.32, fill: { color: HEX.accent4 }, line: { color: HEX.accent4 }, objectName: `arrow ${i + 1}` });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 4.25, w: 12.1, h: 2.1, rectRadius: 0.12, fill: { color: HEX.accent5 }, line: { color: HEX.accent5 }, objectName: "validation card" });
  s.addText(T.callout[0], { x: 1.0, y: 4.55, w: 3.2, h: 1.5, fontSize: 66, bold: true, color: S.accent3, margin: 0, valign: "middle", isTextBox: true, objectName: "checks value" });
  s.addText([
    { text: T.callout[1], options: { fontSize: 22, bold: true, color: S.text1, breakLine: true } },
    { text: T.callout_sub, options: { fontSize: 16, color: S.text2 } },
  ], { x: 4.3, y: 4.6, w: 8.1, h: 1.45, margin: 0, valign: "middle", paraSpaceAfter: 6, isTextBox: true, objectName: "checks text" });
  s.addNotes(T.notes);
}

// ---------------------------------------------------------------- 3. model
{
  const T = C.model;
  pres.addSection({ title: "Model" });
  const s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Model" });
  s.addText(T.title, { placeholder: "title" });
  const iw = 7.4, ih = iw * 869 / 1386;
  s.addImage({ path: path.join(ROOT, T.image), x: 0.6, y: 1.55, w: iw, h: ih, altText: "Star schema: FactEmployee in the centre, nine dimension tables around it", objectName: "star schema" });
  T.points.forEach(([head, body], i) => {
    const y = 1.6 + i * 1.3;
    circleNum(s, i + 1, 8.35, y + 0.05, 0.5, HEX.accent1, HEX.lt1, `point ${i + 1}`);
    s.addText(head, { x: 9.05, y, w: 3.7, h: 0.4, fontSize: 18, bold: true, color: S.text1, margin: 0, isTextBox: true, objectName: `point ${i + 1} head` });
    s.addText(body, { x: 9.05, y: y + 0.42, w: 3.7, h: 0.8, fontSize: 14, color: S.text2, margin: 0, valign: "top", isTextBox: true, objectName: `point ${i + 1} body` });
  });
  s.addNotes(T.notes);
}

// ---------------------------------------------------------------- 4. findings
{
  const T = C.findings;
  pres.addSection({ title: "Findings" });
  const s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Findings" });
  s.addText(T.title, { placeholder: "title" });
  const labels = T.chart.map(d => d.label);
  const isCo = T.chart.map(d => d.label === "Company");
  // two stacked series so the company bar can be grey: each category has exactly one non-zero value
  s.addChart(pres.charts.BAR, [
    { name: "Group", labels, values: T.chart.map((d, i) => isCo[i] ? 0 : d.value) },
    { name: "Company", labels, values: T.chart.map((d, i) => isCo[i] ? d.value : 0) },
  ], {
    x: 0.6, y: 1.5, w: 6.8, h: 4.75, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 45,
    chartColors: [HEX.accent1, HEX.accent4], catAxisOrientation: "maxMin",
    showValue: true, dataLabelPosition: "inEnd", dataLabelFormatCode: "0.0%;;;", dataLabelColor: "FFFFFF", dataLabelFontSize: 14, dataLabelFontBold: true,
    dataLabelFontFace: "+mn-lt",
    valAxisHidden: true, valAxisMinVal: 0, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    catAxisLabelColor: HEX.dk1, catAxisLabelFontSize: 14, catAxisLabelFontFace: "+mn-lt", catAxisLineShow: false,
    showLegend: false, showTitle: true, title: T.chart_title, titleFontSize: 16, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
    objectName: "attrition by group chart",
  });
  T.points.forEach(([v, text], i) => {
    const y = 1.55 + i * 1.55;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.7, y, w: 5.0, h: 1.35, rectRadius: 0.1, fill: { color: HEX.lt2 }, line: { color: HEX.lt2 }, objectName: `finding ${i + 1} card` });
    s.addText(v, { x: 7.9, y: y + 0.12, w: 2.15, h: 1.1, fontSize: 30, bold: true, color: i === 0 ? S.accent2 : S.accent3, margin: 0, valign: "middle", isTextBox: true, objectName: `finding ${i + 1} value` });
    s.addText(text, { x: 10.15, y: y + 0.1, w: 2.4, h: 1.15, fontSize: 14, color: S.text1, margin: 0, valign: "middle", isTextBox: true, objectName: `finding ${i + 1} text` });
  });
  s.addText(T.foot, { x: 0.6, y: 6.35, w: 12.1, h: 0.5, fontSize: 12, italic: true, color: S.text2, margin: 0, isTextBox: true, objectName: "footnote" });
  s.addNotes(T.notes);
}

// ---------------------------------------------------------------- 5. recommendations
{
  const T = C.recs;
  pres.addSection({ title: "Recommendations" });
  const s = pres.addSlide({ masterName: "DARK", sectionTitle: "Recommendations" });
  s.addText(T.title, { placeholder: "title" });
  T.cards.forEach(([head, body, track], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.5 + Math.floor(i / 2) * 2.3;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.95, h: 2.1, rectRadius: 0.12, fill: { color: "2A3A5C" }, line: { color: "2A3A5C" }, objectName: `action ${i + 1} card` });
    circleNum(s, i + 1, x + 0.25, y + 0.25, 0.55, HEX.accent1, HEX.lt1, `action ${i + 1}`);
    s.addText(head, { x: x + 1.0, y: y + 0.22, w: 4.75, h: 0.55, fontSize: 20, bold: true, color: S.background1, margin: 0, valign: "middle", isTextBox: true, objectName: `action ${i + 1} head` });
    s.addText(body, { x: x + 1.0, y: y + 0.8, w: 4.75, h: 0.75, fontSize: 14, color: S.accent5, margin: 0, valign: "top", isTextBox: true, objectName: `action ${i + 1} body` });
    s.addText(track, { x: x + 1.0, y: y + 1.55, w: 4.75, h: 0.4, fontSize: 13, bold: true, color: S.accent1, margin: 0, isTextBox: true, objectName: `action ${i + 1} track` });
  });
  s.addText(T.data_fix, { x: 0.6, y: 6.25, w: 12.1, h: 0.55, fontSize: 14, color: S.accent4, margin: 0, isTextBox: true, objectName: "data fix" });
  s.addNotes(T.notes);
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  if (APPLY_THEME) { const { applyTheme } = require(APPLY_THEME); await applyTheme(OUT, THEME); }
  console.log("wrote", OUT);
})();
