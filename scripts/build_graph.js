#!/usr/bin/env node
// content/entities frontmatter -> library-agnostic graph.json (FR-12).
// Red line #3: low-confidence edges are never published.
import fs from "node:fs";
import path from "node:path";
import { parse as parseYaml } from "yaml";

/** Parse YAML frontmatter from a markdown string. Returns the data object. */
function readFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  try {
    return parseYaml(match[1]) ?? {};
  } catch {
    return {};
  }
}

export function buildGraph(pages) {
  const published = new Map(
    pages.filter((p) => p.publish === true).map((p) => [p.id, p])
  );
  const nodes = [...published.values()].map((p) => ({
    id: p.id,
    type: p.type,
    label: p.label ?? p.id,
    confidence: p.confidence,
  }));
  const edges = [];
  for (const p of published.values()) {
    for (const r of p.relations ?? []) {
      if (!["medium", "high"].includes(r.confidence) || !published.has(r.target)) continue;
      edges.push({
        source: p.id,
        target: r.target,
        predicate: r.predicate,
        as_of: r.as_of != null ? String(r.as_of) : null,
        valid_from: r.valid_from ?? null,
        valid_to: r.valid_to ?? null,
        confidence: r.confidence,
        source_ref: r.source,
      });
    }
  }
  return { nodes, edges };
}

const isMain =
  process.argv[1] &&
  path.resolve(process.argv[1]) === new URL(import.meta.url).pathname;

if (isMain) {
  const root = path.resolve(new URL(".", import.meta.url).pathname, "..");
  const dir = path.join(root, "content/entities");
  let pages = [];
  if (fs.existsSync(dir)) {
    pages = fs
      .readdirSync(dir)
      .filter((f) => f.endsWith(".md"))
      .map((f) => readFrontmatter(fs.readFileSync(path.join(dir, f), "utf8")));
  }
  const out = process.argv[2] ?? path.join(root, "public/graph/graph.json");
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const g = buildGraph(pages);
  fs.writeFileSync(out, JSON.stringify(g, null, 2));
  console.log(
    `graph.json: ${g.nodes.length} nodes, ${g.edges.length} edges -> ${out}`
  );
}
