"""
Optimizer program with multiple message interactions.
Includes system prompt, measures client time and estimates server processing time.
"""

import argparse
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from litellm import OpenAI

# Load environment variables
load_dotenv()

# Constants
BASE_URL = "http://localhost:8004/v1"  # Local vLLM server TODO
# BASE_URL = "https://ai-green.yasdb.com/compatible-mode/v1"
MODEL_NAME = "/ssd_data/models/Qwen3-30B-A3B-Instruct-2507-FP8"
# MODEL_NAME = "deepseek-v4-flash"
DEFAULT_TIMEOUT = 300

# Parse command line arguments
parser = argparse.ArgumentParser(description="Optimizer program")
parser.add_argument("--output", "--output-file", type=str, default=None,
                    help="Output file path (default: ./data/{sql_stem}_proposals.json)")
parser.add_argument("--sql", type=str, required=True,
                    help="Path to SQL file (required)")
parser.add_argument("--stat", type=str, default=None,
                    help="Path to metadata/statistics file")
parser.add_argument("--explain", type=str, default=None,
                    help="Path to EXPLAIN output file")
parser.add_argument("--dataset", type=str, default=None,
                    # choices=["TPCDS", "IMDB", ],
                    help="Dataset to use for statistics (TPCDS, IMDB). "
                         "If not specified, uses default")
args = parser.parse_args()

def read_file(filepath):
    """Read file content, return empty string if file not found."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"[WARNING] File not found: {filepath}")
        return ""
    except Exception as e:
        print(f"[ERROR] Failed to read file {filepath}: {e}")
        return ""

OUTPUT_FILE = args.output or str(Path("./data") / f"{Path(args.sql).stem}_proposals.json")
SQL_CONTENT = read_file(args.sql)
META_STAT_CONTENT = read_file(args.stat) if args.stat else ""
EXPLAIN_CONTENT = read_file(args.explain) if args.explain else ""
PROPOSAL_COUNT = 20


TEMPLATE_CONTENT = """
```json
[
  {
    "proposal_id": 1,
    "strategy_overview": "修正行数估计偏差，调整连接顺序并强制哈希连接，解决大表嵌套循环性能瓶颈",
    "core_optimization_points": [
      "校正orders表行数估计，修正优化器对驱动表规模的误判",
      "调整连接顺序为customer→orders→order_item，将小结果集customer作为驱动表",
      "强制customer与orders使用HashJoin，替代原低效的NestLoop",
      "提升order_item表并行度至4，加速大表扫描"
    ],
    "hint_combination": "/*+ Rows(orders *0.1) Leading( (customer orders order_item) ) HashJoin(customer orders) HashJoin(customer orders order_item) Parallel(order_item 4) */",
    "expected_performance_benefit": "预计降低执行耗时50%-70%，核心收益来自消除嵌套循环对大表的千万次循环扫描，同时并行加速大表扫描"
  },
  {
    "proposal_id": 2,
    "strategy_overview": "优化索引扫描路径，使用覆盖索引实现仅索引扫描，减少回表IO开销",
    "core_optimization_points": [
      "强制orders表使用idx_orders_cust_date索引进行仅索引扫描",
      "保持原连接顺序，强制使用MergeJoin复用索引排序结果",
      "调整random_page_cost为1.1，匹配SSD存储的随机读性能"
    ],
    "hint_combination": "/*+ IndexOnlyScan(orders idx_orders_cust_date) MergeJoin(customer orders) Set(random_page_cost 1.1) */",
    "expected_performance_benefit": "预计降低执行耗时30%-40%，核心收益来自避免orders表的回表IO，合并连接复用索引排序"
  }
]
```
"""

PROMPTS = [
f"""
# PostgreSQL 查询优化策略生成提示词
## 角色与任务定义
### 角色定位
你是PostgreSQL数据库内核与查询优化顶级专家，精通优化器代价模型、执行计划生成机制、pg_hint_plan插件全量语法与深层原理，擅长结合元数据、统计信息与执行计划分析，生成可落地的高性能查询优化方案。

### 核心任务
基于输入的**SPJ（Select-Project-Join）类型分析查询SQL**、数据库元数据与统计信息、PostgreSQL `EXPLAIN`/`EXPLAIN ANALYZE` 执行结果，生成 **{PROPOSAL_COUNT}** 个差异化的查询优化策略。每个策略以 `pg_hint_plan` 标准Hint组合的形式呈现，核心目标是显著降低查询执行耗时、提升执行性能。

### 输入信息说明
你将收到三类核心输入：
1. **查询SQL**：标准SPJ类型SQL语句，包含多表连接、过滤条件与列投影；表可能使用别名。
2. **元数据与统计信息**：包含相关表的结构、索引定义、约束信息，以及`pg_class`、`pg_stats`中的统计数据。
3. **EXPLAIN执行结果**：该SQL在PostgreSQL中执行`EXPLAIN`或`EXPLAIN ANALYZE`的完整输出。

### 工作流程要求
1. 逐层拆解执行计划，定位当前计划的性能瓶颈与不合理决策；
2. 结合元数据与统计信息，自主计算过滤选择性、中间结果集规模，校验优化器估计准确性，识别估计偏差；
3. 基于PostgreSQL优化器内核原理与优化规则，设计差异化优化方案，每组方案对应一套可执行的pg_hint_plan Hint组合；
4. 严格按照指定JSON格式输出，保证Hint语法合规、逻辑自洽，可直接嵌入SQL验证效果。

---

## 输入信息
### 查询SQL
{SQL_CONTENT}

### 元数据与统计信息
{META_STAT_CONTENT}

### EXPLAIN执行结果
{EXPLAIN_CONTENT}

---

## 专业知识体系一：pg_hint_plan 完整语法与使用规范
pg_hint_plan是PostgreSQL官方兼容的执行计划强制引导插件，通过SQL首部的`/*+ ... */`注释块传递Hint指令，强制优化器选择指定的执行路径。所有Hint必须严格遵循官方语法规范，表名必须与SQL中的别名完全一致（无别名则使用原表名），多个Hint之间用空格分隔，全量语法**不支持`*`通配符**。

### 1. 连接顺序控制 Hint（Leading）
用于强制指定多表连接的整体顺序与连接树结构，是控制中间结果集规模的核心手段。仅支持两种合法写法，禁止混合使用。

#### 1.1 左深树写法（扁平列表）
**正确语法**：`Leading( (表1 表2 表3 ... 表N) )`
- 单一层级括号，内部按顺序列出所有参与连接的表；
- 执行逻辑：表1与表2先执行连接，连接结果依次与表3、表4…表N连接，形成左深连接树；
- 表1为最外层驱动表，越靠前的表越先参与连接。
- 示例：`Leading( (customer orders order_item) )`

#### 1.2 灌木树写法（严格嵌套）
**正确语法**：`Leading( (左元素 右元素) )`
- 每个括号内**必须且只能包含2个元素**，元素可以是具体表名，也可以是另一个嵌套括号；
- 执行逻辑：先计算括号内两个元素的连接，再作为整体参与外层连接；
- 适用于需要先将某几张表聚合成子结果，再与其他表连接的场景。
- 示例：`Leading( (customer (orders order_item)) )`：orders与order_item先连接，结果再与customer连接。

#### 强制禁令（违者必触发语法错误）
- ❌ 禁止嵌套括号中出现超过2个元素，如`Leading( (a b (c d)) )`（外层括号有3个元素，违反嵌套语法规则）
- ❌ 禁止单表使用Leading，如`Leading( (t1) )`
- ❌ 禁止外连接场景下反转内外表顺序，违反SQL语义的Hint会被静默忽略

---

### 2. 连接方法控制 Hints
用于强制指定或禁止某组表之间的连接算法，**必须指定至少2个具体表名，禁止使用`*`通配符**。

#### 2.1 肯定式连接Hint（强制使用指定算法）
| Hint语法 | 作用 |
|---------|------|
| `HashJoin(表1 表2 [表3...])` | 强制指定表组之间使用哈希连接 |
| `NestLoop(表1 表2 [表3...])` | 强制指定表组之间使用嵌套循环连接 |
| `MergeJoin(表1 表2 [表3...])` | 强制指定表组之间使用合并连接 |

#### 2.2 否定式连接Hint（禁止使用指定算法）
| Hint语法 | 作用 |
|---------|------|
| `NoHashJoin(表1 表2 [表3...])` | 禁止指定表组之间使用哈希连接 |
| `NoNestLoop(表1 表2 [表3...])` | 禁止指定表组之间使用嵌套循环连接 |
| `NoMergeJoin(表1 表2 [表3...])` | 禁止指定表组之间使用合并连接 |

#### 强制禁令（违者必触发语法/冲突错误）
- ❌ 禁止使用通配符，如`NoNestLoop(*)`（语法错误，必须指定具体表）
- ❌ 禁止同一组表同时指定多个肯定式连接Hint，如同时写`HashJoin(a b) NestLoop(a b)`（触发连接方法冲突错误）
- ❌ 禁止单表使用连接方法Hint，如`HashJoin(t1)`
- ❌ 禁止指定不存在的表名或别名

---

### 3. 扫描方法控制 Hints
用于强制指定或禁止单表的扫描路径，作用对象为单个表，可选择性指定具体索引名。

#### 3.1 肯定式扫描Hint
| Hint语法 | 作用 |
|---------|------|
| `SeqScan(表名)` | 强制对指定表使用顺序扫描 |
| `IndexScan(表名 [索引名])` | 强制使用指定索引进行索引扫描；不指定索引则由优化器选最优索引 |
| `IndexOnlyScan(表名 [索引名])` | 强制使用仅索引扫描（覆盖索引扫描，无需回表） |
| `BitmapScan(表名 [索引名])` | 强制使用位图扫描 |

#### 3.2 否定式扫描Hint
| Hint语法 | 作用 |
|---------|------|
| `NoSeqScan(表名)` | 禁止指定表使用顺序扫描 |
| `NoIndexScan(表名)` | 禁止指定表使用所有普通索引扫描 |
| `NoIndexOnlyScan(表名)` | 禁止指定表使用仅索引扫描 |
| `NoBitmapScan(表名)` | 禁止指定表使用位图扫描 |

#### 强制禁令（违者必触发语法/冲突错误）
- ❌ 禁止同一表同时指定多个肯定式扫描Hint，如同时写`SeqScan(t1) IndexScan(t1)`（触发扫描方法冲突错误）
- ❌ 禁止指定不存在的索引名，对应Hint会被静默忽略
- ❌ 禁止使用`BitmapAnd`、`BitmapOr`等非官方扫描Hint关键字

---

### 4. 行数估计校正 Hint（Rows）
用于修正多表连接后中间结果集的行数估计偏差，是解决统计信息失准导致错误计划的核心手段。
**核心约束：必须指定至少2个表，仅作用于表组连接后的结果集，禁止作用于单表**。

#### 正确语法
- 强制指定行数：`Rows(表1 表2 [表3...] #目标行数)`
- 按系数修正：`Rows(表1 表2 [表3...] *修正系数)`（原估计行数 × 系数）
- 偏移量修正：`Rows(表1 表2 [表3...] +偏移量)` / `Rows(表1 表2 [表3...] -偏移量)`

#### 说明与示例
- 表列表中的表必须是连接树中真实存在的连接组合，顺序无要求；
- 修正系数 = 实际行数 / 优化器估计行数，用于抵消统计信息偏差；
- 示例：`Rows(customer orders *0.1)`：将customer与orders连接后的估计行数乘以0.1。

#### 强制禁令（违者必触发语法错误）
- ❌ 禁止单表使用Rows Hint，如`Rows(item #1000)`（语法错误，必须至少2个表）
- ❌ 禁止表列表与实际连接树不匹配，对应Hint会被静默忽略

---

### 5. 连接行为控制 Hints
仅支持官方提供的连接行为Hint，禁止使用任何未列出的非官方关键字。

#### 5.1 Memoize 缓存控制
用于控制嵌套循环连接内表的结果缓存，仅作用于指定的连接表对，**必须指定至少2个表**。
| Hint语法 | 作用 |
|---------|------|
| `Memoize(外表 内表)` | 对指定嵌套循环连接启用Memoize缓存，重复外表值时复用内表查询结果 |
| `NoMemoize(外表 内表)` | 对指定嵌套循环连接禁用Memoize缓存 |
- 示例：`Memoize(customer orders)`：在customer驱动orders的嵌套循环中启用Memoize

#### 强制禁令（违者必触发语法错误）
- ❌ 禁止单表使用Memoize/NoMemoize，如`NoMemoize(inventory)`（语法错误，必须至少2个表）

#### 5.2 明确禁止使用的非官方行为Hint
以下关键字**不存在于pg_hint_plan官方语法中，绝对禁止使用**，使用会触发“无法识别的Hint关键字”错误：
- `Materialize` / `NoMaterialize`
- `NoExpand`
- `BitmapAnd` / `BitmapOr`

---

### 6. 并行执行控制 Hint
仅支持单表并行度设置Hint，**不存在其他并行相关关键字**。
**正确语法**：`Parallel(表名 并行Worker数量)`
- 强制指定指定表扫描时的并行工作进程数量；
- 若需禁用某表的并行扫描，设置并行数量为0即可，无需单独的NoParallel关键字。
- 示例：
  - `Parallel(order_item 4)`：order_item表扫描启用4个并行Worker
  - `Parallel(order_item 0)`：禁用order_item表的并行扫描

#### 强制禁令（违者必触发语法错误）
以下并行相关关键字**不存在于官方语法中，绝对禁止使用**：
- `NoParallel`
- `ParallelAppend`
- `NoParallelAppend`

---

### 7. 规划器参数设置 Hint（Set）
通过Set Hint临时调整优化器/执行器参数，仅对当前查询生效，不修改全局配置，语法完全兼容PostgreSQL原生参数。
**正确语法**：`Set(参数名 参数值)`
**常用可调参数分类**：
1. 路径开关类：`enable_nestloop`、`enable_hashjoin`、`enable_mergejoin`、`enable_seqscan`、`enable_indexscan`
2. 代价模型类：`seq_page_cost`、`random_page_cost`、`cpu_tuple_cost`、`effective_cache_size`
3. 并行控制类：`max_parallel_workers_per_gather`、`parallel_setup_cost`、`parallel_tuple_cost`
4. 内存配置类：`work_mem`、`maintenance_work_mem`
- 示例：`Set(random_page_cost 1.1)`、`Set(work_mem '128MB')`

---

### 8. 通用语法规则与强制禁令
为彻底避免语法错误、冲突错误与Hint静默失效，生成策略时必须严格遵守以下规则：
1. **表名一致性**：所有Hint中的表名必须与SQL中使用的别名完全一致，无别名时使用原表名；
2. **禁止冲突Hint**：同一作用域（同表/同表组）只能指定一个肯定式扫描/连接Hint，禁止同时指定多个互斥的肯定式Hint；
3. **关键字白名单制**：仅可使用上述章节明确列出的官方Hint关键字，禁止使用任何未提及的自定义关键字；
4. **语义合法性**：Hint不能违反SQL语义（如反转外连接内外表），否则会被优化器静默忽略；
5. **无通配符支持**：所有连接类、行为类Hint都必须指定具体表名，禁止使用`*`作为通配符；
6. **嵌套严格性**：Leading的灌木树写法中，每个括号必须恰好包含2个元素，禁止多元素混合嵌套。

---

## 专业知识体系二：PostgreSQL 优化器内核原理
PostgreSQL采用**基于代价的优化器（CBO）**，核心逻辑是枚举所有可行执行路径，通过代价模型计算每条路径的预估总开销，最终选择代价最低的执行计划。

### 1. 代价模型核心机制
代价以「顺序读取一个磁盘页」为基准单位，核心代价参数：
- `seq_page_cost`：顺序读取1个磁盘页的代价，默认1.0
- `random_page_cost`：随机读取1个磁盘页的代价，默认4.0（SSD环境通常下调至1.1~2.0）
- `cpu_tuple_cost`：处理1个数据元组的CPU代价，默认0.01
- `cpu_index_tuple_cost`：处理1个索引元组的CPU代价，默认0.005
- `cpu_operator_cost`：执行1次基础运算的CPU代价，默认0.0025

总代价 = IO代价 + CPU代价，优化器以总代价最低为目标选择路径。

### 2. 连接顺序搜索算法
1. **动态规划算法**：当连接表数量 ≤ `geqo_threshold`（默认12）时启用，穷举所有合法连接顺序与连接树结构，保证找到全局最优解；计算量随表数量指数级增长。
2. **遗传算法（GEQO）**：当连接表数量超过阈值时启用，通过启发式搜索在庞大解空间中寻找近似最优解，存在错过最优计划的可能。

连接顺序优化的核心目标：让中间结果集随连接步骤尽可能缓慢增长，避免早期连接产生超大中间结果。

### 3. 三类连接方法的代价模型与适用场景
| 连接方法 | 核心逻辑 | 代价构成 | 最优适用场景 |
|---------|---------|---------|-------------|
| 嵌套循环连接（NestLoop） | 外表逐行遍历，内表每次按连接键查找匹配行 | 外表扫描代价 + 外表行数 × 内表单次查找代价 | 外表行数小（千级以内），内表连接键有高效索引；带LIMIT的查询可提前终止 |
| 哈希连接（Hash Join） | 以小表构建哈希表，大表逐行探测匹配 | 两表扫描代价 + 哈希构建CPU代价 + 哈希探测CPU代价 | 等值连接，两表数据量大，无合适索引；结果集规模大的场景 |
| 合并连接（Merge Join） | 两表按连接键排序后，双指针归并匹配 | 两表扫描代价 + 排序代价（无索引时） + 归并CPU代价 | 连接键已有索引（天然有序）；查询本身需按连接键排序；支持非等值连接 |

### 4. 扫描路径的选择逻辑
1. **顺序扫描（Seq Scan）**：全表逐页顺序读取，代价与表大小正相关。
   - 适用场景：小表、过滤选择性差（返回>20%行）、无可用索引
2. **索引扫描（Index Scan）**：先遍历索引定位匹配行TID，再回表读取完整数据。
   - 代价构成：索引扫描IO（随机读为主） + 回表IO + CPU处理代价
   - 适用场景：过滤选择性高（返回<5%行），有匹配索引
3. **仅索引扫描（Index Only Scan）**：索引包含所有查询所需列，无需回表，依赖可见性映射（VM）判断行可见性。
   - 代价远低于普通索引扫描，是覆盖索引场景的最优选择
4. **位图扫描（Bitmap Scan）**：先构建满足条件的行位图，再批量顺序回表读取，减少随机IO。
   - 适用场景：中等选择性（5%-20%）、多索引组合过滤（Bitmap And/Or）

### 5. 并行查询规划机制
PostgreSQL支持并行顺序扫描、并行索引扫描、并行哈希连接、并行聚合等。
- 触发条件：表大小超过`min_parallel_table_scan_size`（默认8MB），且估算代价显著高于并行启动开销
- 并行度计算：基于表大小自动计算，受`max_parallel_workers_per_gather`上限约束
- 开销构成：进程启动开销、数据分发开销；小表并行会得不偿失

---

## 专业知识体系三：EXPLAIN 执行计划分析方法论
### 1. 核心字段解读
#### 估计类字段（EXPLAIN 输出）
- `Node Type`：节点类型（Seq Scan、Hash Join、Nested Loop等）
- `Startup Cost`：节点输出第一行数据的预估代价
- `Total Cost`：节点执行完成的总预估代价
- `Plan Rows`：节点输出的预估行数
- `Plan Width`：每行输出的预估字节宽度

#### 实际执行字段（EXPLAIN ANALYZE 输出）
- `Actual Startup Time`：实际启动时间（单位：毫秒）
- `Actual Total Time`：节点实际总执行时间
- `Actual Rows`：节点实际输出行数
- `Actual Loops`：节点执行的循环次数
- `Rows Removed by Filter`：过滤条件剔除的行数
- `Sort Method`：排序算法与内存/磁盘状态（External Merge表示磁盘排序）
- `Hash Buckets / Hash Batches`：哈希表桶数与批次数（批次>1表示磁盘溢出）
- `Workers Planned / Workers Launched`：计划与实际启动的并行工作者数量

### 2. 逐层分析框架
1. **自底向上拆解**：从最内层扫描节点开始，逐层向上分析连接、排序等上层节点；
2. **行数偏差校验**：对比每个节点`Plan Rows`与`Actual Rows`，偏差>10倍为严重偏差，是计划失准的核心原因；
3. **瓶颈节点定位**：找到实际执行时间占比最高的节点，作为优化核心目标；
4. **连接合理性判断**：检查连接顺序是否导致中间结果过早膨胀，连接方法是否匹配数据规模与索引条件；
5. **扫描效率判断**：检查是否命中最优扫描方式，是否存在不必要的回表开销；
6. **并行效率判断**：检查并行度是否匹配数据规模，是否存在并行不足或过度并行。

### 3. 常见性能瓶颈识别
1. **错误嵌套循环**：外表实际行数远大于估计值，导致内表被循环扫描成千上万次，耗时指数级增长；
2. **大表全表扫描**：大表过滤性高但未命中索引，产生大量顺序IO；
3. **排序/哈希磁盘溢出**：`work_mem`不足，大排序、大哈希落到磁盘，性能骤降；
4. **中间结果膨胀**：连接顺序错误，早期连接产生超大中间结果，后续操作开销剧增；
5. **并行度不足**：大表扫描、大连接未启用并行，或并行worker数量过少。

---

## 专业知识体系四：元数据与统计信息利用指南
统计信息是优化器代价计算的基础，统计信息失准是错误执行计划的首要原因。你必须充分利用统计信息自主估算真实数据规模，校验优化器决策的合理性。

### 1. 核心元数据字段
1. **表元数据（pg_class）**
   - `reltuples`：表的预估总行数（由ANALYZE更新）
   - `relpages`：表占用的磁盘页数（每页8KB）
   - `relallvisible`：全可见页数量，决定Index Only Scan的可行性
2. **索引元数据**
   - 索引字段与顺序、索引类型（B树、哈希、GIN等）、是否唯一/部分索引
   - 索引区分度：唯一值比例越高，索引效率越高
3. **约束信息**：主键、唯一约束、外键、非空约束，可用于推导连接结果集与过滤效果。

### 2. 统计信息核心指标（pg_stats）
- `n_distinct`：列的唯一值数量；正值为绝对值，负值为行数的倒数比例
- `null_frac`：列中空值的占比
- `most_common_vals (MCV)`：最常见值列表
- `most_common_freqs (MCF)`：对应最常见值的出现频率
- `histogram_bounds`：非最常见值的分布直方图，用于范围查询估算
- `avg_width`：列的平均字节宽度

### 3. 选择性与结果集估算方法
1. **等值查询选择性**
   - 过滤值在MCV中：选择性 = 对应MCF的频率值
   - 过滤值不在MCV中：选择性 = (1 - sum(MCF) - null_frac) / (n_distinct - MCV数量)
2. **范围查询选择性**：基于直方图边界，计算查询范围覆盖的区间比例，乘以对应数据占比
3. **多条件组合选择性**：假设条件独立，选择性 = 各条件选择性的乘积
4. **连接结果集估算**：等值连接结果行数 ≈ 左表行数 × 右表行数 / max(左连接列n_distinct, 右连接列n_distinct)

### 4. 应用原则
1. 用统计信息自主计算真实选择性与结果集大小，对比优化器估计值，定位估计偏差；
2. 基于真实中间结果集规模，设计更优的连接顺序与连接方法；
3. 估计偏差严重时，通过`Rows` Hint直接校正优化器估计。

---

## 查询策略生成核心原则与优化规则
### 总纲：性能优化核心逻辑
1. **减少数据量**：尽早过滤数据，最小化中间结果集，是所有优化的第一原则；
2. **降低IO开销**：优先使用索引、覆盖索引，减少随机IO与全表扫描IO；
3. **算法匹配场景**：为数据规模与访问模式选择最合适的连接、扫描算法；
4. **并行换取时间**：对大负载操作合理提升并行度，用CPU资源降低执行耗时；
5. **修正估计偏差**：统计信息失准时，通过Hint校正估计或强制最优路径。

### 1. 连接顺序优化规则
1. 小结果集优先：将过滤后行数最少的表置于连接最外层，作为驱动表；
2. 控制中间结果膨胀：每一步连接后结果集增长越平缓越好，避免早期连接产生超大中间结果；
3. 遵守语义约束：内连接可自由调整顺序，左/右/全外连接的内外表不可反转；
4. 多表连接策略：表数量较多时，优先将关联紧密、结果集小的表聚合成组，再与大表连接。

### 2. 连接方法优化规则
#### 优先选择嵌套循环
- 驱动表过滤后行数 ≤ 1000行
- 内表连接键上有唯一索引或高选择性索引
- 查询带有LIMIT，可提前终止循环

#### 优先选择哈希连接
- 两表连接结果集大（万级以上）
- 连接为等值连接
- 内表无合适索引，或索引扫描代价高于全表扫描
- 优化器错误选择嵌套循环且实际耗时极高时，强制改为哈希连接

#### 优先选择合并连接
- 连接键上已有有序索引，数据天然排序
- 查询本身需要按连接键排序，可复用排序结果
- 非等值连接（>、<、between）场景，哈希连接不支持

### 3. 扫描路径优化规则
1. 过滤选择性 ≤ 5%、返回行数少时，优先使用索引扫描；
2. 查询所需列全部包含在索引中、表可见性映射良好时，优先使用仅索引扫描；
3. 表体积小（<10MB）、过滤选择性差（返回>20%行）时，优先使用顺序扫描；
4. 中等选择性、多索引组合过滤场景，优先使用位图扫描。

### 4. 并行执行优化规则
1. 启用前提：单表扫描或单步连接的执行代价显著高于并行启动开销；
2. 并行度设置：表大小每1~2GB对应1个并行worker，上限不超过服务器物理CPU核心数；
3. 禁止并行场景：小表扫描、小结果集连接、嵌套循环内表扫描，并行开销大于收益。

### 5. 估计偏差校正规则
1. 实际行数与估计行数偏差超过10倍时，必须通过`Rows` Hint校正；
2. 优先校正最内层扫描节点的行数偏差，逐层向上修正中间结果估计；
3. 优先使用乘法系数校正，严重偏差时直接强制指定行数。

### 6. 策略优先级与差异化要求
1. 优先级：校正估计偏差 > 优化连接顺序 > 调整连接/扫描方法 > 提升并行度 > 调整代价参数；
2. 生成的{PROPOSAL_COUNT}个策略必须差异化，分别从不同维度切入优化，避免同质化；
3. 策略按预期收益从高到低排序，第一个为最优方案。

---

## 输出格式规范
### 输出要求
1. 严格输出标准JSON格式，根节点为数组，包含恰好 **{PROPOSAL_COUNT}** 个查询策略对象；
2. 所有Hint必须符合pg_hint_plan语法规范，表名与SQL别名一致，可直接嵌入SQL执行；
3. 策略按预期性能收益从高到低排序。

### JSON 字段定义
| 字段名 | 类型 | 说明 |
|-------|------|------|
| proposal_id | integer | 策略编号，从1开始递增 |
| strategy_overview | string | 策略整体优化思路的一句话概述 |
| core_optimization_points | array[string] | 具体优化点列表，逐条说明调整的执行计划要素 |
| hint_combination | string | 完整的pg_hint_plan Hint组合，格式为`/*+ hint1 hint2 ... */` |
| expected_performance_benefit | string | 预期性能收益描述，说明优化逻辑依据与大致耗时降幅 |

### 输出示例
{TEMPLATE_CONTENT}

"""
]


def get_server_time_ms(response, response_headers: dict) -> float | None:
    """从响应头或响应对象中提取服务端计算时间(毫秒)"""
    server_time_ms = None

    # 常见的服务端时间头字段 (按优先级)
    header_names = [
        'x-envoy-upstream-service-time',  # Envoy 代理上报的服务端时间
        'req-cost-time',  # 请求处理时间
        'x-process-time-ms',
        'x-response-time-ms',
        'x-latency-ms',
        'process-time-ms',
        'response-time-ms',
        'latency',
        'server-timing',
    ]

    # 从响应头中获取
    for header_name in header_names:
        if header_name in response_headers:
            header_value = response_headers[header_name]
            try:
                server_time_ms = float(header_value)
                break
            except (ValueError, TypeError):
                pass

    # 如果 header 中没有，尝试从响应对象的其他属性获取
    if server_time_ms is None:
        model_extra = getattr(response, 'model_extra', None)
        if model_extra:
            server_time_ms = (model_extra.get('response_ms') or
                            model_extra.get('latency') or
                            model_extra.get('server_time_ms'))

    # 尝试从 litellm 的其他属性获取
    if server_time_ms is None:
        if hasattr(response, 'response_ms'):
            server_time_ms = response.response_ms
        elif hasattr(response, 'extra_data') and response.extra_data:
            server_time_ms = response.extra_data.get('response_ms') or response.extra_data.get('latency')

    return server_time_ms


def main():
    """Initialize LLM client and interact with multiple messages."""

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") #TODO
    # api_key = "sk-24Mf5wY2RvofQHgknlCakLhQgd2ZSP1it14GvhxF9WWvqW6T"
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment")
        return

    # 创建响应头存储变量
    response_headers = {}

    # 使用 httpx transport 来拦截响应头
    class HeaderCaptureTransport(httpx.HTTPTransport):
        def handle_request(self, request):
            response = super().handle_request(request)
            # 存储响应头供后续使用
            response_headers.update(dict(response.headers))
            return response

    # Initialize client with custom http client that disables proxy
    http_client = httpx.Client(
        trust_env=False,
        timeout=DEFAULT_TIMEOUT,
        transport=HeaderCaptureTransport(),
    )

    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
        http_client=http_client,
    )

    print(f"[INFO] Client initialized successfully")
    print(f"[INFO] Base URL: {BASE_URL}")
    print(f"[INFO] Model: {MODEL_NAME}")
    print(f"[INFO] Output file: {OUTPUT_FILE}")
    # print(f"=" * 60)

    # Initialize messages with system prompt
    # messages = [
    #     {"role": "system", "content": SYSTEM_PROMPT}
    # ]
    messages = []

    # Process each prompt
    for i, prompt in enumerate(PROMPTS):
        print(f"\n[INFO] Prompt#{i+1} prompt length: {len(prompt)})")
        # print(f"------\n {prompt} \n")

        # Record client start time (before sending request)
        client_start_time = time.time()

        # Add user message to conversation
        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                timeout=DEFAULT_TIMEOUT,
            )

            # Calculate client-side time
            client_end_time = time.time()
            client_elapsed = client_end_time - client_start_time

            # Extract server time from response headers
            server_time_ms = get_server_time_ms(response, response_headers)

            # Extract response content
            assistant_message = response.choices[0].message.content

            # Estimate server processing time
            if hasattr(response, "usage") and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens

                # Rough estimate: Assuming ~50 tokens/sec generation rate for 30B model
                estimated_server_time = completion_tokens / 50.0 if completion_tokens > 0 else 0
            else:
                prompt_tokens = completion_tokens = total_tokens = 0
                estimated_server_time = 0

            # Add assistant response to messages for context
            messages.append({"role": "assistant", "content": assistant_message})

            # Write assistant_message to output file
            try:
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    f.write(assistant_message)
                print(f"[INFO] Output written to: {OUTPUT_FILE}")
            except Exception as e:
                print(f"[ERROR] Failed to write output file: {e}")

            print(f"[INFO] Client time: {client_elapsed * 1000:.1f} ms")
            if server_time_ms is not None:
                print(f"[INFO] Server computation time: {server_time_ms:.1f} ms")
            else:
                print(f"[INFO] Server computation time: ~{estimated_server_time * 1000:.1f} ms (estimated)")

            if total_tokens > 0:
                print(f"[INFO] Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")

        except Exception as e:
            print(f"[ERROR] Failed to get response: {e}")

    print(f"\n{'=' * 60}")
    print(f"[INFO] All prompts processed successfully!")


if __name__ == "__main__":
    main()