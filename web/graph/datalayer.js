// Shared data layer (FR-13): filtering/time-slicing happens HERE, renderers stay dumb.
const RANK = { low: 0, medium: 1, high: 2 };

export function cmpQuarter(a, b) {
  const [ya, qa] = a.split("-Q").map(Number), [yb, qb] = b.split("-Q").map(Number);
  return (ya - yb) || (qa - qb);
}

function inWindow(e, asOf) {
  const from = e.valid_from ?? e.as_of;
  if (from == null) return true;
  if (cmpQuarter(asOf, from) < 0) return false;
  return e.valid_to == null || cmpQuarter(asOf, e.valid_to) <= 0;
}

export function filterGraph(g, { predicates = null, minConfidence = "medium", asOf = null } = {}) {
  const edges = g.edges.filter(e =>
    (!predicates || predicates.includes(e.predicate)) &&
    RANK[e.confidence] >= RANK[minConfidence] &&
    (!asOf || inWindow(e, asOf)));
  const keep = new Set(edges.flatMap(e => [e.source, e.target]));
  return { nodes: g.nodes.filter(n => keep.has(n.id)), edges };
}
