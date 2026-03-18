# ST-Weather-Watcher

SillyTavern 实时天气同步插件。基于高德 API 实现，适用于国内直连环境。
本来想用wttr但是必须开魔法，而且配置端口太麻烦了（

## 功能介绍
- 自动抓取高德天气实况，无需梯子。
- 支持 Docker 容器化部署及本地/安卓环境运行。
- 自动写入 SillyTavern 变量，支持 {{getvar::weather}}。
- 个人基础配额 5000 次/日（目前免费是5000,后续会不会调整不清楚）。

## 获取 API Key
1. 访问 [高德开放平台](https://lbs.amap.com/) 注册。
2. 开发者认证时可跳过企业认证，完成个人实名核验。
3. 应用管理 -> 我的应用 -> 添加 Key，选择 "Web服务"。
4. 获取Key，并在项目附带的 Excel 中查询城市的 adcode。

## 部署

### 1. Docker
```bash
git clone https://github.com/P0lar1zzZ/ST-Weather-Watcher.git
cd ST-Weather-Watcher
# 为.env填写内部参数
docker build -t st-weather .
docker run -d \
  --name st-weather \
  -v /填入你的酒馆绝对路径，到SillyTavern为止/public:/app/public \
  --env-file .env \
  st-weather
```

### 2. Android (Termux)

*请注意，你需要开启魔法。*

```bash
curl -sSL https://raw.githubusercontent.com/P0lar1zzZ/ST-Weather-Watcher/main/install_weather.sh | bash -s -- "替换为你的APIkey" "替换为你的城市代码"
```

## 使用
1. 将 weather.js 内容复制粘贴添加至酒馆助手全局脚本（需要酒馆助手）。
2. 在角色提示词中调用变量 {{getvar::weather}}。

