# ST-Weather-Watcher

SillyTavern 实时天气同步插件。基于高德 API 实现，适用于国内直连环境。
本来想用wttr但是必须开魔法，而且配置端口太麻烦了（
以及感谢Gemini无私的帮助。

## 功能介绍
- 自动抓取高德天气实况，无需梯子。
- 支持 Docker 容器化部署及本地/安卓环境运行。
- 自动写入 SillyTavern 变量，支持 {{getvar::weather}}。
- 个人基础配额 5000 次/日（目前免费是5000,后续会不会调整不清楚）。
- **永久记忆服务器**（`server.py`）：为 Claude 手机 App MCP 接口提供 `remember` / `recall` 工具。

## 获取 API Key
1. 访问 [高德开放平台](https://lbs.amap.com/) 注册。
2. 开发者认证时可跳过企业认证，完成个人实名核验。
3. 应用管理 -> 我的应用 -> 添加 Key，选择 "Web服务"。
4. 获取Key，并在项目附带的 Excel 中查询城市的 adcode。

## 部署

### 1. Docker

*不推荐，该方式是为酒馆同样部署在docker内的用户准备的，有需要可以自己折腾。*

```bash
git clone https://github.com/P0lar1zzZ/ST-Weather-Watcher.git
cd ST-Weather-Watcher
# 为.env填写内部参数
docker build -t st-weather .
docker run -d \
  --name st-weather \
  -v /填入你的酒馆绝对路径，到SillyTavern为止/public:/app/public \
  --env-file .env \
  st-weather
```

### 2. Android (Termux)

如果你是用一键式脚本部署的酒馆，请先退出脚本，回到~$

*请注意，你需要开启魔法。*

然后你需要复制粘贴这段代码——如果你输错了，可以退出重进，复制粘贴从头再来一次。

友情提示：你不需要删除引号。

```bash
curl -sSL https://raw.githubusercontent.com/P0lar1zzZ/ST-Weather-Watcher/main/install_weather.sh | bash -s -- "替换为你的APIkey" "替换为你的城市代码"
```

## 使用
1. 将 weather.js 内容复制粘贴添加至酒馆助手全局脚本（需要酒馆助手）。
2. 在角色提示词中调用变量 {{getvar::weather}}。

---

## 永久记忆服务器（MCP）

`server.py` 是一个轻量 HTTP 服务器，为 Claude 手机 App 的 MCP 接口提供两个工具：

| 工具 | 作用 |
|------|------|
| `remember` | 将内容存入永久记忆；相似内容（相似度 ≥ 阈值）自动合并，避免重复 |
| `recall` | 按关键词检索记忆，按相关度排序返回，每次调用均返回 3 步处理详情 |

### 启动记忆服务器

```bash
# 本地直接运行
python server.py

# Docker（覆盖默认 CMD）
docker run -d \
  --name st-memory \
  -p 8080:8080 \
  -v $(pwd)/memories.json:/app/memories.json \
  --env-file .env \
  st-weather \
  python server.py
```

### MCP 接口说明

```
# 获取工具列表（供 App 自动发现注册）
GET http://<host>:8080/tools

# 调用工具
POST http://<host>:8080/tools/call
Content-Type: application/json

# 存储记忆
{ "name": "remember", "parameters": { "content": "用户喜欢简洁的回答", "category": "偏好" } }

# 检索记忆
{ "name": "recall", "parameters": { "query": "用户偏好", "limit": 5 } }
```

### 记忆合并策略

记忆以 JSON 文件持久存储（`memories.json`）。新增记忆时：
1. 与已有记忆逐条计算相似度。
2. 若最高相似度 ≥ `MERGE_THRESHOLD`（默认 0.75），则**合并**到已有条目（追加新增词语），避免重复膨胀。
3. 相似度低于阈值则**新增**条目。

每次工具调用的响应均包含 **3 步处理详情**（扫描 → 合并/新增 → 持久化），方便在 App 侧观察完整执行过程。

### .env 配置项

```ini
# 记忆数据文件路径
MEMORIES_FILE=memories.json
# 记忆服务器监听端口
MEMORY_PORT=8080
# 合并相似度阈值（0~1）
MERGE_THRESHOLD=0.75
```

