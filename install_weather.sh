#!/bin/bash

# 1. 直接获取用户在命令行填的参数
USER_KEY=$1
USER_CITY=${2:-330100} # 如果没填城市，默认杭州

# 2. 自动安装环境 (静默模式，不跳出一堆字)
echo "正在为您配置环境，请稍候..."
pkg update -y && pkg upgrade -y > /dev/null 2>&1
pkg install python git -y > /dev/null 2>&1
pip install requests python-dotenv > /dev/null 2>&1

# 3. 自动处理项目文件夹
if [ ! -d "ST-Weather-Watcher" ]; then
    git clone https://github.com/P0lar1zzZ/ST-Weather-Watcher.git > /dev/null 2>&1
fi
cd ST-Weather-Watcher

# 4. 自动寻找酒馆并写入 .env (完全不需要用户填路径)
ST_PATH=$(find $HOME -maxdepth 3 -type d -name "SillyTavern" 2>/dev/null | head -n 1)
ST_PUBLIC="${ST_PATH:-$HOME/SillyTavern}/public"

cat <<EOF > .env
AMAP_KEY=$USER_KEY
CITY_CODE=$USER_CITY
INTERVAL=3600
ST_PUBLIC_PATH=$ST_PUBLIC
EOF

# 5. 直接启动进程 (并在后台保持运行)
echo "✅ 配置成功！正在启动天气同步..."
nohup python main.py > weather.log 2>&1 &

echo "------------------------------------------"
echo "🎉 大功告成！气象站已在后台开始工作。"
echo "📍 天气文件已指向: $ST_PUBLIC/weather.txt"
echo "💡 提示：您可以直接关掉这个窗口去玩酒馆了。"
echo "------------------------------------------"

