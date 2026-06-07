// graph.json (canonical) -> force-graph shape. Swapping libs = new adapter only (FR-13).
export const toForceGraph = g => ({
  nodes: g.nodes.map(n => ({ id: n.id, name: n.label, group: n.type })),
  links: g.edges.map(e => ({ source: e.source, target: e.target,
    predicate: e.predicate, conf: e.confidence })),
});
