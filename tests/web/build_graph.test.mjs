import { test } from "node:test";
import assert from "node:assert/strict";
import { buildGraph } from "../../scripts/build_graph.js";

const pages = [
  { id: "nvidia", type: "Company", label: "NVIDIA", publish: true, confidence: "high",
    relations: [
      { predicate: "MANUFACTURED_BY", target: "tsmc", as_of: "2026-Q1", confidence: "high", source: "s1" },
      { predicate: "PARTNER_WITH", target: "ghost", as_of: "2026-Q1", confidence: "high", source: "s1" },
      { predicate: "COMPETES_WITH", target: "amd", as_of: "2026-Q1", confidence: "low", source: "s1" },
      { predicate: "SUPPLIES_TO", target: "amd", as_of: "2026-Q1", confidence: undefined, source: "s2" },
      { predicate: "LICENSES_TO", target: "amd", as_of: "2026-Q1", confidence: "Low", source: "s3" }]},
  { id: "tsmc", type: "Fab", label: "TSMC", publish: true, confidence: "high", relations: [] },
  { id: "amd", type: "Company", label: "AMD", publish: true, confidence: "medium", relations: [] },
  { id: "secret", type: "Company", label: "S", publish: false, confidence: "low", relations: [] }];

test("only published nodes; low edges and dangling targets dropped", () => {
  const g = buildGraph(pages);
  assert.deepEqual(g.nodes.map(n => n.id).sort(), ["amd", "nvidia", "tsmc"]);
  assert.equal(g.edges.length, 1);                       // red line #3 + dangling 'ghost'
  assert.deepEqual(g.edges[0], { source: "nvidia", target: "tsmc", predicate: "MANUFACTURED_BY",
    as_of: "2026-Q1", valid_from: null, valid_to: null, confidence: "high", source_ref: "s1" });
});

test("confidence undefined is dropped", () => {
  const g = buildGraph(pages);
  const found = g.edges.some(e => e.predicate === "SUPPLIES_TO");
  assert.equal(found, false);
});

test("confidence 'Low' (wrong case) is dropped", () => {
  const g = buildGraph(pages);
  const found = g.edges.some(e => e.predicate === "LICENSES_TO");
  assert.equal(found, false);
});
