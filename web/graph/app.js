import { filterGraph } from "./datalayer.js";
import { toForceGraph } from "./adapters/forcegraph.js";

const COLORS = { Company: "#4f8df7", Fab: "#f7a14f", Product: "#6fd08c", Chip: "#d06fb8",
  Segment: "#c9c9c9", Technology: "#9b6fd0", Person: "#f7d24f", DataCenter: "#6fc9d0" };

const raw = await (await fetch("./graph.json")).json();
const preds = [...new Set(raw.edges.map(e => e.predicate))].sort();
const panel = document.getElementById("preds");
panel.innerHTML = preds.map(p =>
  `<label><input type="checkbox" value="${p}" checked> ${p}</label>`).join("<br>");

const fg = ForceGraph()(document.getElementById("graph"))
  .nodeColor(n => COLORS[n.group] ?? "#999").nodeLabel(n => `${n.name} (${n.group})`)
  .linkLabel(l => `${l.predicate} [${l.conf}]`)
  .linkLineDash(l => (l.conf === "medium" ? [4, 4] : null))   // unverified = dashed
  .onNodeClick(n => { location.href = `/entities/${n.id}`; });

function redraw() {
  const checked = [...panel.querySelectorAll("input:checked")].map(i => i.value);
  const minConf = document.getElementById("conf").value;
  fg.graphData(toForceGraph(filterGraph(raw, { predicates: checked, minConfidence: minConf })));
}
document.getElementById("panel").addEventListener("change", redraw);
redraw();
