#!/bin/bash

# 获取参数
USER_KEY=$1
USER_CITY=${2:-330100}

echo "🔄 正在为您配置/更新同步站..."

# 1. 强行杀掉可能正在运行的旧进程（防止多开报错）
pkill -f "python main.py" > /dev/null 2>&1

# 2. 自动处理项目更新
if [ -d "ST-Weather-Watcher" ]; then
    cd ST-Weather-Watcher
    git pull > /dev/null 2>&1
else
    git clone https://github.com/P0lar1zzZ/ST-Weather-Watcher.git > /dev/null 2>&1
    cd ST-Weather-Watcher
fi

# 3. 寻找酒馆路径
ST_PATH=$(find $HOME -maxdepth 3 -type d -name "SillyTavern" 2>/dev/null | head -n 1)
ST_PUBLIC="${ST_PATH:-$HOME/SillyTavern}/public"

# 4. 覆盖写入新配置
cat <<EOF > .env
AMAP_KEY=$USER_KEY
CITY_CODE=$USER_CITY
INTERVAL=3600
ST_PUBLIC_PATH=$ST_PUBLIC
EOF

# 5. 启动并静默运行
nohup python main.py > weather.log 2>&1 &

echo "------------------------------------------"
echo "✅ 配置已更新并重新启动！"
echo "📍 城市代码: $USER_CITY"
echo "📖 如果酒馆里显示错误信息，请确认 Key 是否申请正确。"
echo "------------------------------------------"
