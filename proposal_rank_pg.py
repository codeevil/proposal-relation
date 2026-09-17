"""
Optimizer program with multiple message interactions.
Includes system prompt, measures client time and estimates server processing time.
"""

import argparse
import json
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
parser = argparse.ArgumentParser(description="Proposal ranking program")
parser.add_argument("--output", "--output-file", type=str, default=None,
                    help="Output file path (default: ./data/{sql_stem}_rank.json)")
parser.add_argument("--sql", type=str, required=True,
                    help="Path to SQL file (required)")
parser.add_argument("--proposals", type=str, required=True,
                    help="Path to the proposals JSON file (array of candidate proposals)")
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


def _strip_markdown_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text.strip()


OUTPUT_FILE = args.output or str(Path("./data") / f"{Path(args.sql).stem}_rank.json")
SQL_CONTENT = read_file(args.sql)

PROPOSALS_CONTENT = _strip_markdown_fence(read_file(args.proposals)) if args.proposals else ""

PROPOSAL_COUNT = 0
try:
    _proposals_data = json.loads(PROPOSALS_CONTENT)
    if isinstance(_proposals_data, list):
        PROPOSAL_COUNT = len(_proposals_data)
except Exception:
    PROPOSAL_COUNT = 0


TEMPLATE_CONTENT = """
```json
{
  "best_proposal_id": 3,
  "reason": "该方案将小结果集customer作为驱动表并强制哈希连接，避免了对orders大表的嵌套循环扫描，且通过Rows校正了行数估计偏差，预期执行耗时最小"
}
```
"""

PROMPTS = [
f"""
# PostgreSQL 查询优化方案评选提示词
## 角色与任务定义
### 角色定位
你是PostgreSQL数据库内核与查询优化顶级专家，精通优化器代价模型、执行计划生成机制、pg_hint_plan插件全量语法与深层原理，擅长评估不同Hint组合对查询执行性能的实际影响。

### 核心任务
以下是针对同一条查询SQL生成的 **{PROPOSAL_COUNT}** 个候选查询优化方案（每个方案为一组 pg_hint_plan Hint 组合）。请基于你对PostgreSQL优化器内核原理、代价模型与Hint语义的深入理解，从这些候选中**评选出执行性能最优（预期执行耗时最小）的1个方案**，并输出该方案的提案编号（proposal_id）与简要理由。

### 输入信息说明
你将收到两类核心输入：
1. **查询SQL**：标准SPJ类型SQL语句，包含多表连接、过滤条件与列投影；表可能使用别名。
2. **候选优化方案列表**：共{PROPOSAL_COUNT}个Proposal，每个包含 proposal_id、strategy_overview、core_optimization_points、hint_combination、expected_performance_benefit 等字段。

### 评选与分析要求
1. 深入理解查询SQL结构，识别涉及的表、连接顺序、过滤条件与连接关系；
2. 对每个候选方案，解析其 `hint_combination` 中的各类Hint（如 Leading、HashJoin/NestLoop/MergeJoin、SeqScan/IndexScan/IndexOnlyScan、Rows、Parallel、Set 等），判断其是否语法合规、无逻辑冲突、不违反SQL语义；
3. 结合查询的过滤选择性、表规模与各Hint的语义，推断各方案实际可能产生的执行计划与中间结果集规模；
4. 依据PostgreSQL代价模型（IO代价 + CPU代价），评估各方案的大致执行耗时，选出预期耗时最小的方案；
5. 优先考虑：最小化中间结果集、避免大表嵌套循环、合理的连接顺序与连接方法、恰当的索引扫描方式与并行度；
6. 淘汰规则：Hint语法错误、逻辑冲突、违反SQL语义（如外连接内外表反转）的方案，其Hint可能被静默忽略或导致错误计划，应视为性能不可靠。

---

## 输入信息
### 查询SQL
{SQL_CONTENT}

### 候选优化方案列表（共{PROPOSAL_COUNT}个）
{PROPOSALS_CONTENT}

---

## 输出格式规范
### 输出要求
1. 严格输出标准JSON格式，根节点为对象，直接输出你判定的性能最优方案，不要输出所有方案、不要输出多余分析文字；
2. 选出的 proposal_id 必须是候选方案列表中真实存在的 proposal_id。

### JSON 字段定义
| 字段名 | 类型 | 说明 |
|-------|------|------|
| best_proposal_id | integer | 你评选出的性能最优方案的 proposal_id |
| reason | string | 一句话说明该方案为何执行耗时最小（例如：某连接顺序避免了大表嵌套循环、中间结果集最小等） |

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