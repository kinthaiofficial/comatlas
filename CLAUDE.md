# CLAUDE.md — ComAtlas 维护规则（NVIDIA 产业链知识图谱 / Wiki）

> 项目：**ComAtlas** ·  仓库：`kinthaiofficial/ComAtlas` ·  公开站点：`https://comatlas.kinthai.ai`（GitHub Pages）
> 你（Claude Code）是这个仓库的**维护 Agent**。本文件是你的操作规则与约束。
> 黄金法则：**Markdown 知识库(`content/`)是唯一真相来源；无来源的关系永不入图；schema 是封闭集合，不得擅自扩展。**
> 本项目呈现来源可追溯的公开事实，**不输出投资建议**。

---

## 1. 你负责什么

每次运行(手动或定时)，按顺序：
1. 处理 `raw/` 中**新增/变更**的来源（增量，不重复处理旧文件）。
2. 用三腿管线抽取实体与关系，归一化、共识打分、grounding 校验。
3. 更新 `content/` 下的 Markdown 实体页(frontmatter + 正文)。
4. 通过 `lint_frontmatter.py`；有违例必须修复或将该边降级，不得跳过。
5. 提交并推送（触发自动重建发布）。

**不要**：自行发明实体类型或关系谓词；写入无来源的边；把 low 置信边设为 `publish: true`；重分发受版权保护的大段原文（只存事实 + 短引用 + 回链）。

---

## 2. 仓库结构（你常用的）
- `ontology/entity_types.yml`、`ontology/predicates.yml` — 封闭集合，**只读约束**（人类才能改）。
- `ontology/alias_map.yml` — 实体消解；可在发现新别名时**追加**(需人类复核新增项)。
- `raw/` — 原始资料投放区（你消费）。
- `content/` — Markdown 实体页（唯一真相，你写这里）。
- `scripts/` — 采集/抽取/建图/校验脚本。
- `eval/gold_triples.json` — 验收 gold 集（勿改，仅用于测试）。

---

## 3. 本体（封闭集合，必须遵守）

**实体类型（8 个）**：`Company` `Product` `Chip` `Fab` `DataCenter` `Technology` `Person` `Segment`

**关系谓词（8 个活跃）**：`SUPPLIES` `CUSTOMER_OF` `COMPETES_WITH` `MANUFACTURED_BY` `OWNS_STAKE_IN` `SUBSIDIARY_OF` `PARTNER_WITH` `IN_SEGMENT`

> **`HEADQUARTERED_IN` 已保留/停用**（决策 G9）：本体中无 `Place` 实体类型，该谓词的 target 无法解析；总部信息改用实体页标量字段 `hq:` 记录（见 §4）。是否新增 `Place` 类型留给人类本体决策。

**谓词函数型约束**（决策 G12）：
- `SUBSIDIARY_OF`：对同一主语**函数型**——同一公司只有一个直接母公司；同主语不同宾语构成冲突，进复核队列。
- `MANUFACTURED_BY`：仅当主语类型为 **`Chip`** 时函数型（一款芯片通常单一代工）；主语为 `Company` 或 `Product` 时允许多个 target，不构成冲突。

**domain/range 由 `lint_frontmatter.py` 强制**：每条 relation 写入前管线会过 ontology 的 domain/range 守卫，违规边直接**丢弃**（不写入 frontmatter，不进复核队列；如需保留应先扩展本体）。

抽取时若遇到无法归入上述集合的实体/关系：**不要新增类别**，记入 `low` 置信并写入复核队列说明，交人类决定是否扩展本体。

---

## 4. 实体页 frontmatter（Schema v2，写入格式，严格）

```yaml
---
type: Company              # ∈ 实体封闭集
id: nvidia                 # = 文件名，^[a-z0-9][a-z0-9-]*$，小写、稳定、全局唯一
label: NVIDIA              # 显示名（新增 v2）
aliases: [NVIDIA Corporation, 英伟达, NVDA]
ticker: NVDA               # 可选
hq: "Santa Clara, California, US"   # 可选标量（G9：替代 HEADQUARTERED_IN 谓词）
confidence: high           # high | medium | low
authority: official        # official | inferred
publish: true              # 发布闸门（新增 v2）：low 置信页面必须 false（lint 强制）
last_updated: 2026-06-07   # 字符串形式（非 YAML 日期）
summary_by: claude         # 可选（M2.5）：页面含机器生成简介块时标注，对读者透明
sources: [nvda-10k-2026-02-25]
relations:
  - predicate: MANUFACTURED_BY   # ∈ 谓词封闭集（含 domain/range 守卫）
    target: tsmc                 # 必须解析到已存在的实体 id（经 alias_map）
    as_of: 2026-Q1               # 日历季度（G5：统一用日历季，不用 NVIDIA 财季）
    valid_from: 2020-Q1          # 可选
    valid_to: null               # 可选
    source: nvda-10k-2026-02-25  # 必须，且必须解析到 content/sources/ 下的来源页
    corroborates: []             # 可选：其他印证来源 id 列表（新增 v2）
    quote: "…such as … TSMC …"   # 可选（M2.5）：≤15 词年报短引；lint 强制 ≤15 词（红线 #5）
    confidence: high
    extractors: [claude, xbrl]   # ∈ {claude, minimax, glirel, xbrl, human, wikidata}
                                 # human = 人工核实/金种子；绝不把人工标注改写为 LLM 抽取器
facts:                           # 新增 v2：XBRL 数值事实列表
  - metric: revenue
    value: 215938000000
    unit: USD
    period: FY2026               # 财务事实保留财期标签（FY2026 / Q1FY2027 等）
    source: nvda-10k-2026-02-25
    confidence: high
    extractors: [xbrl]
---
（英文正文结构（M2.5）：`<!-- SUMMARY:BEGIN/END -->`（机器生成简介，受管） → 手写区（保留） → `<!-- AUTO-RELATIONS:BEGIN/END -->`（关系/事实表，受管，含 ≤15 词"依据"短引）。两个受管块由 update_content.py 重写，块外手写内容保留）
```

**硬性规则**：`type` ∈ 实体集；`predicate` ∈ 谓词集；每条 relation 必须有 `source`、`as_of`、`confidence`、`extractors`；`target` 必须能解析到一个实体 id（先过 `alias_map`）；`source` 必须解析到 `content/sources/` 下的来源页。

**来源页** (`content/sources/<id>.md`) 格式：
```yaml
---
id: nvda-10k-2026-02-25
kind: sec-filing          # sec-filing | transcript | news | wikidata
title: "NVIDIA FY2026 Form 10-K"
url: https://www.sec.gov/Archives/edgar/data/...
date: 2026-02-25
accession: "0001045810-26-000123"
publish: true
---
```

---

## 5. 抽取与共识（核心流程）

### 5.1 M2 实际运行（已上线）

**管线 = Claude 锚 + MiniMax 第二票 + XBRL/Wikidata 结构腿**（共识投票 + grounding + 锚门 + 复核队列）。

- **锚 = Claude**：headless `claude -p`（订阅；Actions 用 `CLAUDE_CODE_OAUTH_TOKEN`，**不用** API key）。**本地手动重算应用会话内 Claude 直接抽（不 shell `claude -p` 子进程——会与本会话抢订阅配额、自相限速）**，CI 隔离 runner 才用 `claude -p`。`extractors:[claude]`。
- **第二票 = MiniMax M3**：`api.minimaxi.com/v1`，强制 `record_triples` tool_call。仅投票不当锚；越界/无效三元组丢弃；**逐块容错**（422 敏感内容/限速跳过该块）。`extractors:[minimax]`。
- **XBRL 腿**：`edgartools` 财务事实 → 直接采信 high。`extractors:[xbrl]`。
- **Wikidata 腿**：WDQS SPARQL（P355 子公司 / P1830 持股）→ 结构边；**印证现有实体**（subject+target 都已存在才入图，不引入新节点）；WDQS 故障容错跳过。`extractors:[wikidata]`。
- **grounding = MiniMax M3**：rapidfuzz 证据存在性 + M3 蕴含判定（用供应链语义措辞、给原文上下文窗口）。
- **锚门（关键）**：MiniMax/GLiREL 是票不是锚——无锚抽取器 `{claude,human,xbrl,wikidata}` 支持的边**绝不入图**，进 `review_queue.md`（kind=weak-only）。
- **human / 结构边权威**：带 `human` 的人工 gold 与 XBRL/Wikidata 边**绕过 grounding**，不被 flaky 判定误降。
- **函数型冲突（G12）→ review_queue（kind=conflict）**：不发布、不自动仲裁（GLiREL 未启用，冲突交人工）。
- **打分（`consensus.score`）**：结构边→high；grounding 失败→low；否则 ≥2 抽取器且 ≥2 来源→high，≥1→medium。

### 5.2 共识规则（M2 生效后）
1. **先归一化**：所有抽取输出映射到规范实体 id（过 `alias_map`）+ 规范谓词，**再**比对一致性。
2. **分层**：结构化事实(XBRL/Wikidata)→ 高权威直接采信；叙述关系 → 投票。
3. **默认 2 票、分歧升级**：默认 Claude + MiniMax；二者不一致才调 GLiREL 仲裁。
4. **置信度** = 抽取器一致度 + 独立来源印证数：
   - `high`：≥2 抽取器一致 **且** ≥2 独立来源 / 或来自结构化权威源。
   - `medium`：单来源或仅 1 票，但 grounding 通过。
   - `low`：冲突 / grounding 失败 / 仅弱模型支持。
5. **小模型不对称**：GLiREL/REBEL **赞成加分，沉默不否决**——绝不因弱模型漏抽而删除已被强模型支持的边。
6. **Grounding 校验**：每条新边校验"引用句是否真支持该边"；失败 → 降为 `low`。

参考（共识打分，伪代码）：
```python
def score_edge(edge, votes, sources):
    if edge.from_structured:           # XBRL / Wikidata
        return "high"
    agree = normalize_and_count_agreement(votes)   # 归一后统计一致抽取器数
    corro = count_independent_sources(sources)
    if not grounding_ok(edge):
        return "low"
    if agree >= 2 and corro >= 2:
        return "high"
    if agree >= 1:
        return "medium"
    return "low"
# 注意：弱模型缺席不降级；冲突(不同 target/predicate)才进 low + 复核队列
```

### 5.3 当前管线命令
```bash
export MINIMAX_API_KEY=...                    # 第二票 + grounding（ops/.env；Actions 用 Secret）
python scripts/fetch_sources.py               # EDGAR 增量采集
python scripts/extract_consensus.py           # 锚+二票+结构腿 → 共识/grounding/锚门 → content/ + review_queue.md
python scripts/lint_frontmatter.py            # schema/来源/红线强制（exit 1 → 修复后才能提交）
node scripts/build_graph.js                   # frontmatter → public/graph/graph.json
npx quartz build                              # Quartz 渲染发布
```
- **自动维护**：`.github/workflows/maintain.yml`（手动 `workflow_dispatch`；需 `CLAUDE_CODE_OAUTH_TOKEN` + `MINIMAX_API_KEY` Secret）。跑通后再加 `schedule:` cron。
- **本地重算存量**：会话内 Claude 抽取注入 + MiniMax 腿，见 `scripts/_recompute_m2.py`（审计记录）。

---

## 6. graph.json 契约（建图）
`scripts/build_graph.js` 扫描所有 frontmatter，输出库无关数据；每条边带 `predicate / as_of / confidence / source_ref`。**不要**把可视化库特定字段写进 graph.json——库差异交给 `web/components/GraphView/adapters/`。

---

## 7. 发布闸门
- 仅 `publish: true` 的页面公开。
- `high` 可自动 `publish: true`；`medium` 可发布但正文标注"未核实"；**`low` 默认不发布**，进复核队列。
- 修改 `quartz.config.ts` 的 ExplicitPublish 行为前先与人类确认。

---

## 8. 复核队列
把 `low`/冲突边写入 `review_queue.md`，列出：实体、候选关系、各抽取器的分歧、来源句。人类只处理这里。**不要**自行决断冲突边的去留。

---

## 9. 提交规范
- 提交信息：`auto: <动作> <实体/来源范围>`（如 `auto: update NVIDIA supply edges from 10-Q 2026Q1`）。
- 一次提交对应一次连贯的更新；保持 diff 可读，便于人类回滚。

---

## 10. 维护节奏
- 定时任务(默认每日)：拉新来源 → 抽取共识 → 更新 → lint → 提交。
- 每次只处理增量；若来源未变更则跳过，不产生空提交。

---

## 11. 红线（任何时候不得违反）
1. 无 `source` 的关系**绝不**入图。
2. **绝不**新增本体类别（封闭集合）；越界项进复核队列。
3. **绝不**把 `low`/冲突边发布出去。
4. **绝不**编造来源、关系或数字；置信度必须诚实。
5. **绝不**重分发受版权保护的大段原文；只存事实 + 短引用(<15 词) + 回链。
6. **绝不**在站点输出投资建议或买卖结论。
7. **绝不**删除或改写根目录 `CNAME` 文件（内容 `comatlas.kinthai.ai`），否则自定义域名会断。
8. **溯源必须诚实**：人工核实或手工种子数据的 `extractors` 必须写 `[human]`，**绝不**改写为任何 LLM 抽取器名称（claude/minimax/glirel 等）。同理，LLM 抽取的边不得标注为 `human`。溯源造假是对图谱可信度的根本破坏。
