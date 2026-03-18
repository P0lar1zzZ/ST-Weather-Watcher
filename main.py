import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# 加载配置
load_dotenv()

API_KEY = os.getenv("AMAP_KEY")
CITY_CODE = os.getenv("CITY_CODE", "330100") 

# --- 🛠️ 兼容性路径修复 ---
# 1. 优先读取 install_weather.sh 写入的路径
# 2. 如果没有，则使用原本的 Docker 路径 /app/public
# 3. 如果前两者都不可写，最后保底写在当前文件夹
env_path = os.getenv("ST_PUBLIC_PATH")
if env_path and os.path.exists(os.path.dirname(env_path)):
    FILE_PATH = os.path.join(env_path, "weather.txt")
elif os.path.exists("/app/public"):
    FILE_PATH = "/app/public/weather.txt"
else:
    FILE_PATH = "weather.txt"

print(f"📍 天气文件同步路径: {FILE_PATH}")

def fetch_weather():
    if not API_KEY:
        print("❌ 错误：未检测到 AMAP_KEY，请检查 .env 文件！")
        return

    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "key": API_KEY,
        "city": CITY_CODE,
        "extensions": "base",
        "output": "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "1" and data.get("lives"):
            live = data["lives"][0]
            weather_str = f"{live['city']} {live['weather']} {live['temperature']}°C 湿度:{live['humidity']}%"
            
            # 确保目录存在并写入
            os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
            with open(FILE_PATH, "w", encoding="utf-8") as f:
                f.write(weather_str)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 高德同步成功: {weather_str}")
        else:
            print(f"❌ 高德接口报错: {data.get('info')}")
            
    except Exception as e:
        print(f"💥 网络请求失败: {e}")

if __name__ == "__main__":
    interval = int(os.getenv("INTERVAL", "3600"))
    print(f"🚀 高德气象站已启动，更新频率: {interval}s")
    
    fetch_weather() # 启动即同步
    
    while True:
        time.sleep(interval)
        fetch_weather()
