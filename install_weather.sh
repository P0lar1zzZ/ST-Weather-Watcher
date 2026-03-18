#!/bin/bash

# 定义一个返回函数，方便重复调用
function configure_step() {
    clear
    echo "=========================================="
    echo "🌦️  高德天气助手 - 极简配置向导"
    echo "=========================================="
    
    # --- 步骤 1: 获取 Key ---
    while true; do
        echo ""
        echo "第一步：请输入您的高德 Key"
        echo "(输入 'q' 退出安装)"
        read -p "👉 Key: " user_key
        [[ "$user_key" == "q" ]] && exit 1
        
        # 简单校验
        if [ ${#user_key} -lt 10 ]; then
            echo "❌ 这个 Key 看起来太短了，请重新输入。"
            continue
        fi
        break
    done

    # --- 步骤 2: 获取 城市代码 ---
    while true; do
        echo ""
        echo "第二步：请输入城市代码 (adcode)"
        echo "(直接回车默认杭州: 330100，输入 'b' 返回上一步)"
        read -p "👉 代码: " user_adcode
        
        if [[ "$user_adcode" == "b" ]]; then
            configure_step # 递归调用，返回第一步
            return
        fi
        
        user_adcode=${user_adcode:-330100}
        break
    done

    # --- 步骤 3: 最终确认 ---
    echo ""
    echo "--------------------------"
    echo "确认信息："
    echo "Key: $user_key"
    echo "城市: $user_adcode"
    echo "--------------------------"
    read -p "确认无误开始安装吗？(y/n/b): " final
    case $final in
        y) ;;
        b) configure_step ;; # 返回
        *) echo "已取消"; exit 1 ;;
    esac

    # --- 写入文件 ---
    echo "写入配置中..."
    cat <<EOF > .env
AMAP_KEY=$user_key
CITY_CODE=$user_adcode
INTERVAL=3600
WEATHER_FILE=weather.txt
ST_PUBLIC_PATH=$HOME/SillyTavern/public
EOF
}

# 执行配置
configure_step

# 生成专属启动脚本 (weather_start.sh)
cat <<EOF > weather_start.sh
#!/bin/bash
while true; do
    python main.py
    echo "连接波动，5秒后自动重连..."
    sleep 5
done
EOF
chmod +x weather_start.sh

echo "✅ 配置完成！请输入 ./weather_start.sh 启动。"
