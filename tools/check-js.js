// Saca el <script> de index.html y lo pasa por node --check (parseo) sin ejecutarlo.
const fs = require("fs");
const p = "C:/Users/PC/DeskBox/Apps/CODE/IG Info extractor Code/ig-vault-apk/src/assets/index.html";
const h = fs.readFileSync(p, "utf8");
const m = [...h.matchAll(/<script>([\s\S]*?)<\/script>/g)];
if (!m.length) { console.log("NO HAY SCRIPT"); process.exit(1); }
let js = m.map(x => x[1]).join("\n;\n");
fs.writeFileSync("C:/Users/PC/AppData/Local/Temp/opencode/app.js", js);
console.log("script bytes:", js.length);