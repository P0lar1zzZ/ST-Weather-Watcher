"""
MCP 兼容永久记忆服务器
为 Claude 手机 App MCP 接口提供 remember / recall 工具
"""

import json
import os
import re
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from http.server import BaseHTTPRequestHandler, HTTPServer

# ── 配置 ──────────────────────────────────────────────
MEMORIES_FILE = os.getenv("MEMORIES_FILE", "memories.json")
PORT = int(os.getenv("MEMORY_PORT", "8080"))
# 相似度阈值：超过此值则视为重复记忆并合并
MERGE_THRESHOLD = float(os.getenv("MERGE_THRESHOLD", "0.75"))
# 检索评分权重（词元重叠 vs 序列相似度）
_TOKEN_OVERLAP_WEIGHT = 0.6
_SEQ_SIMILARITY_WEIGHT = 0.4

# ── 工具定义（注册表）─────────────────────────────────
TOOLS = [
    {
        "name": "remember",
        "description": "将重要信息存入永久记忆，相似内容会自动合并去重。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "需要记住的内容"
                },
                "category": {
                    "type": "string",
                    "description": "记忆分类（可选），如：偏好、事实、任务等"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "recall",
        "description": "根据关键词从永久记忆中检索相关信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "检索关键词或描述"
                },
                "limit": {
                    "type": "integer",
                    "description": "最多返回条数（默认 5）"
                }
            },
            "required": ["query"]
        }
    }
]

# ── 记忆持久化 ─────────────────────────────────────────

def load_memories() -> list:
    if not os.path.exists(MEMORIES_FILE):
        return []
    try:
        with open(MEMORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        print(f"⚠️  {MEMORIES_FILE} 格式损坏，已重置为空记忆库")
        return []


def save_memories(memories: list) -> None:
    with open(MEMORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

# ── 相似度计算（用于合并判断）─────────────────────────

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _tokenize(text: str) -> set:
    return set(re.findall(r"[\w\u4e00-\u9fff]+", text.lower()))

# ── 工具实现 ──────────────────────────────────────────

def tool_remember(content: str, category: str = "") -> dict:
    """存储记忆，相似度超过阈值时自动合并。"""
    memories = load_memories()
    steps = []

    # Step 1: 查找相似记忆
    similar_idx = None
    best_score = 0.0
    for i, mem in enumerate(memories):
        score = _similarity(content, mem["content"])
        if score > best_score:
            best_score = score
            similar_idx = i

    steps.append(f"[1/3] 扫描已有 {len(memories)} 条记忆，最高相似度: {best_score:.2%}")

    # Step 2: 合并或新增
    if similar_idx is not None and best_score >= MERGE_THRESHOLD:
        old = memories[similar_idx]["content"]
        # 合并：保留旧内容，追加新增部分
        old_tokens = _tokenize(old)
        new_tokens = _tokenize(content)
        added = new_tokens - old_tokens
        if added:
            merged = old + "；" + content
            memories[similar_idx]["content"] = merged
            memories[similar_idx]["updated_at"] = datetime.now().isoformat()
            memories[similar_idx]["merge_count"] = memories[similar_idx].get("merge_count", 0) + 1
            action = f"[2/3] 相似度 {best_score:.2%} ≥ 阈值 {MERGE_THRESHOLD:.0%}，已与第 {similar_idx+1} 条记忆合并"
        else:
            action = f"[2/3] 内容完全重复（相似度 {best_score:.2%}），跳过存储"
    else:
        entry = {
            "id": str(uuid.uuid4()),
            "content": content,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "merge_count": 0
        }
        memories.append(entry)
        action = f"[2/3] 未找到相似记忆（最高相似度 {best_score:.2%}），新增第 {len(memories)} 条"

    steps.append(action)

    # Step 3: 持久化
    save_memories(memories)
    steps.append(f"[3/3] 已保存，当前共 {len(memories)} 条记忆")

    return {
        "content": [
            {"type": "text", "text": "\n".join(steps)}
        ]
    }


def tool_recall(query: str, limit: int = 5) -> dict:
    """检索记忆，按相关度排序后返回。"""
    memories = load_memories()
    steps = []

    # Step 1: 关键词分词
    q_tokens = _tokenize(query)
    steps.append(f"[1/3] 已分词 {len(q_tokens)} 个关键词，共 {len(memories)} 条记忆待检索")

    # Step 2: 评分
    scored = []
    for mem in memories:
        m_tokens = _tokenize(mem["content"])
        overlap = len(q_tokens & m_tokens)
        seq_score = _similarity(query, mem["content"])
        score = overlap * _TOKEN_OVERLAP_WEIGHT + seq_score * _SEQ_SIMILARITY_WEIGHT
        if score > 0:
            scored.append((score, mem))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]
    steps.append(f"[2/3] 命中 {len(scored)} 条，取前 {len(top)} 条结果")

    # Step 3: 格式化输出
    if top:
        lines = []
        for rank, (score, mem) in enumerate(top, 1):
            ts = mem.get("updated_at", mem.get("created_at", ""))[:10]
            cat = f"[{mem['category']}] " if mem.get("category") else ""
            lines.append(f"{rank}. {cat}{mem['content']}  （相关度 {score:.2f}，{ts}）")
        result_text = "\n".join(lines)
    else:
        result_text = "未找到相关记忆。"

    steps.append(f"[3/3] 检索完成")

    return {
        "content": [
            {"type": "text", "text": "\n".join(steps)},
            {"type": "text", "text": result_text}
        ]
    }

# ── HTTP 请求处理 ─────────────────────────────────────

class MCPHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # 覆盖默认日志，保持简洁
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw)

    # GET /tools — 列出所有工具（供 MCP 客户端发现）
    def do_GET(self):
        if self.path.rstrip("/") in ("/tools", ""):
            self._send_json({"tools": TOOLS})
        else:
            self._send_json({"error": "Not found"}, 404)

    # POST /tools/call — 执行工具
    def do_POST(self):
        if self.path.rstrip("/") != "/tools/call":
            self._send_json({"error": "Not found"}, 404)
            return

        try:
            body = self._read_body()
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json({"error": f"Invalid JSON: {e}"}, 400)
            return

        name = body.get("name")
        params = body.get("parameters") or body.get("arguments") or {}

        if name == "remember":
            content = params.get("content", "").strip()
            if not content:
                self._send_json({"error": "参数 content 不能为空"}, 400)
                return
            result = tool_remember(content, params.get("category", ""))
            self._send_json(result)

        elif name == "recall":
            query = params.get("query", "").strip()
            if not query:
                self._send_json({"error": "参数 query 不能为空"}, 400)
                return
            try:
                limit = int(params.get("limit", 5))
            except (TypeError, ValueError):
                self._send_json({"error": "参数 limit 必须为整数"}, 400)
                return
            result = tool_recall(query, limit)
            self._send_json(result)

        else:
            self._send_json({"error": f"未知工具: {name}"}, 400)

# ── 入口 ─────────────────────────────────────────────

if __name__ == "__main__":
    print(f"🧠 记忆服务器已启动，端口: {PORT}")
    print(f"📁 记忆文件: {os.path.abspath(MEMORIES_FILE)}")
    print(f"🔗 工具列表: http://0.0.0.0:{PORT}/tools")
    print(f"🔗 工具调用: POST http://0.0.0.0:{PORT}/tools/call")
    print(f"🔀 合并阈值: {MERGE_THRESHOLD:.0%}")
    httpd = HTTPServer(("0.0.0.0", PORT), MCPHandler)
    httpd.serve_forever()
