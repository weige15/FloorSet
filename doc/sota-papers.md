# State-of-the-Art Papers Overlapping `doc/prompt.md`

Search date: 2026-06-14.

Scope: papers were ranked by objective overlap with the FloorSet optimizer prompt:
hard-feasible rectangle floorplanning first, then lower HPWL, smaller bounding-box
area, fewer placement-constraint violations, and bounded runtime. I prioritized
recent floorplanning or macro-placement work that addresses constraints,
legalization, data-driven initialization, or large-scale SoC/IP layouts.

Search notes: I used web/arXiv search and a Semantic Scholar metadata search. The
Semantic Scholar API was rate-limited after returning partial candidate tables,
but it confirmed recent candidates around constrained SoC floorplanning, RL chip
placement, and macro-placement constraints.

## Top 5

### 1. PARSAC: Fast, Human-quality Floorplanning for Modern SoCs with Complex Design Constraints

- Authors/year: Hesham Mostafa, Uday Mallappa, Mikhail Galkin, Mariano Phielipp,
  Somdeb Majumdar, 2024.
- Source: <https://arxiv.org/abs/2405.05495>
- Objective overlap: strongest direct match. It targets SoC floorplanning with
  hard placement constraints, while still optimizing wirelength and area.
- Why it matters here: the paper argues that simply adding hard constraints as
  annealing penalties often produces illegal or weak solutions. Its
  constraints-aware simulated annealing approach aligns with the FloorSet prompt's
  feasibility-first rule.
- Implementation takeaway: encode preplaced/fixed/boundary constraints in
  constructive placement and move generation, not just in the proxy score. Keep
  a best-legal candidate and use multi-start or parallelizable search only after
  legality is robust.

### 2. Physics-Guided Geometric Diffusion for Macro Placement Generation

- Authors/year: Jongho Yoon, Jinsung Jeon, Seokhyeong Kang, 2026.
- Source: <https://arxiv.org/abs/2605.16451>
- Objective overlap: highly relevant to data-driven macro placement, with
  explicit attention to topology, geometry, physical validity, wirelength, and
  scalability.
- Why it matters here: MacroDiff+ combines heterogeneous GNN connectivity
  encoding with Transformer-based geometric context and physics-guided sampling.
  The paper reports improved wirelength over state-of-the-art baselines on
  ISPD2005 MMS and better stability on larger designs.
- Implementation takeaway: if an ML initializer is added later, use it to produce
  candidate centers/orders/aspect hints, then pass every output through the
  deterministic legalizer and hard-constraint preflight.

### 3. Chip Placement with Diffusion Models

- Authors/year: Vint Lee, Minh Nguyen, Leena Elzeiny, Chun Deng, Pieter Abbeel,
  John Wawrzynek, 2024; revised 2025.
- Source: <https://arxiv.org/abs/2407.12282>
- Objective overlap: data-driven macro placement aimed at high-quality layouts
  without slow per-design reinforcement learning.
- Why it matters here: the paper trains diffusion models for zero-shot placement
  and uses guided sampling instead of sequential RL. Its emphasis on synthetic
  pretraining and transfer to unseen circuits matches the optional FloorSet ML
  initializer direction.
- Implementation takeaway: a learned initializer should be advisory, not
  authoritative. The contest solver should still own dimension planning,
  legalization, overlap repair, and immutable geometry preservation.

### 4. Hier-RTLMP: A Hierarchical Automatic Macro Placer for Large-scale Complex IP Blocks

- Authors/year: Andrew B. Kahng, Ravi Varadarajan, Zhiang Wang, 2023.
- Source: <https://arxiv.org/abs/2304.11761>
- Objective overlap: large-scale automatic macro floorplanning for complex IP
  blocks, using hierarchy and dataflow to improve QoR.
- Why it matters here: FloorSet cases can have up to 120 active blocks and
  include cluster/grouping structure. Hier-RTLMP shows that hierarchical
  decomposition and dataflow-aware placement remain competitive and practical
  even when pure peripheral placement breaks down.
- Implementation takeaway: treat clusters and strongly connected subgraphs as
  placement units when possible. Use connectivity-driven ordering before local
  search, especially for large cases where random or pure shelf packing wastes
  area and HPWL.

### 5. Floorplanning of VLSI by Mixed-Variable Optimization

- Authors/year: Jian Sun, Huabin Cheng, Jian Wu, Zhanyang Zhu, Yu Chen, 2024.
- Source: <https://arxiv.org/abs/2401.15317>
- Objective overlap: direct VLSI floorplanning optimization of wirelength and
  area, including fixed-outline and non-fixed-outline variants.
- Why it matters here: the paper frames floorplanning as a mixed-variable problem:
  discrete variables for orientation/order and continuous variables for
  coordinates. It reports improvements over B*-tree floorplanning baselines on
  GSRC benchmarks.
- Implementation takeaway: split the FloorSet solver into discrete construction
  decisions and continuous/legal refinement. This supports the prompt's proposed
  architecture: dimension planning, constructive initialization, compaction, and
  bounded local repair.

## Nearby Papers Not Selected for the Top 5

- A graph placement methodology for fast chip design / AlphaChip, Nature 2021:
  important historical data-driven RL floorplanning work, but less directly
  actionable for this solver because of reproducibility debate, fixed-canvas macro
  placement assumptions, and weaker fit to FloorSet hard/soft constraints.
  Source: <https://www.nature.com/articles/s41586-021-03544-w>
- An Updated Assessment of Reinforcement Learning for Macro Placement, 2023/2026:
  valuable for benchmarking discipline and strong SA baselines; more evaluation
  and critique than primary optimizer design. Source:
  <https://arxiv.org/abs/2302.11014>
- DREAMPlaceFPGA-MP, 2023: strong constraint/legalization ideas for FPGA macro
  placement, especially region and cascade constraints, but less direct because
  FloorSet is SoC floorplanning rather than FPGA site placement. Source:
  <https://arxiv.org/abs/2311.08582>
- Effective Analog ICs Floorplanning with Relational Graph Neural Networks and
  Reinforcement Learning, 2024: useful for graph encoders plus RL under positional
  constraints, but analog-circuit-specific. Source:
  <https://arxiv.org/abs/2411.15212>

## Cross-Paper Implications for `iccad2026contest/my_optimizer.py`

1. Feasibility should be structural. Recent constrained floorplanning work
   supports the prompt's plan to build exact immutable geometry handling,
   obstacle-aware construction, and legality-preserving local moves before score
   tuning.
2. ML should initialize, not replace, legalization. Diffusion and RL methods are
   relevant, but hidden-case contest robustness needs deterministic repair and
   evaluator-parity hard checks.
3. Hierarchy and grouping are first-class signals. Clustering, dataflow, and
   grouped macro units should influence seed order and constructive layout.
4. Separate discrete and continuous work. Use discrete choices for order, macro
   grouping, boundary intent, and MIB compatibility; use continuous compaction or
   local coordinate repair to reduce bbox area and HPWL.
5. Benchmark against strong classical baselines. The literature cautions that
   learning-based placement claims can be brittle; the immediate FloorSet path
   should compare against deterministic fallback, template B*-tree behavior, and
   constrained-SA-style local search before investing in model weights.
