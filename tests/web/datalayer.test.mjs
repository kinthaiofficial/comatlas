import { test } from "node:test";
import assert from "node:assert/strict";
import { filterGraph, cmpQuarter } from "../../web/graph/datalayer.js";
import { toForceGraph } from "../../web/graph/adapters/forcegraph.js";

const G = { nodes: [{ id: "a", type: "Company", label: "A" }, { id: "b", type: "Fab", label: "B" },
                    { id: "c", type: "Company", label: "C" }],
  edges: [
    { source: "a", target: "b", predicate: "MANUFACTURED_BY", as_of: "2026-Q1", valid_from: "2020-Q1", valid_to: null, confidence: "high" },
    { source: "a", target: "c", predicate: "COMPETES_WITH", as_of: "2026-Q1", valid_from: null, valid_to: "2024-Q4", confidence: "medium" }]};

test("quarter compare", () => {
  assert.ok(cmpQuarter("2025-Q4", "2026-Q1") < 0);
  assert.equal(cmpQuarter("2026-Q2", "2026-Q2"), 0);
});
test("predicate + confidence filter drops nodes with no edges", () => {
  const g = filterGraph(G, { predicates: ["MANUFACTURED_BY"], minConfidence: "high" });
  assert.deepEqual(g.nodes.map(n => n.id).sort(), ["a", "b"]);
});
test("asOf slices by validity window", () => {
  const g = filterGraph(G, { asOf: "2025-Q1" });
  assert.equal(g.edges.length, 1);    // a-c expired 2024-Q4; a-b valid since 2020-Q1
  assert.equal(g.edges[0].predicate, "MANUFACTURED_BY");
});
test("adapter shape", () => {
  const fg = toForceGraph(G);
  assert.deepEqual(Object.keys(fg), ["nodes", "links"]);
  assert.equal(fg.links[0].predicate, "MANUFACTURED_BY");
});
