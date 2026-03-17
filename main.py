import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# 加载配置
load_dotenv()

API_KEY = os.getenv("AMAP_KEY")
# 🌟 注意：这里填的是 adcode（如 330100 代表杭州）
CITY_CODE = os.getenv("CITY_CODE", "330100") 
FILE_PATH = "/app/public/weather.txt"

def fetch_weather():
    if not API_KEY:
        print("❌ 错误：未检测到 AMAP_KEY，请检查 .env 文件！")
        return

    # 🌟 完全对齐你截图里的高德官方参数
    url = "https://restapi.amap.com/v3/weather/weatherInfo"
    params = {
        "key": API_KEY,
        "city": CITY_CODE,      # 传入 adcode
        "extensions": "base",   # 实况天气
        "output": "JSON"        # 返回 JSON 格式
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # 文档说：status 为 1 成功，0 失败
        if data.get("status") == "1" and data.get("lives"):
            live = data["lives"][0]
            # 拼接你喜欢的格式
            weather_str = f"{live['city']} {live['weather']} {live['temperature']}°C 湿度:{live['humidity']}%"
            
            # 写入酒馆目录
            os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
            with open(FILE_PATH, "w", encoding="utf-8") as f:
                f.write(weather_str)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 高德同步成功: {weather_str}")
        else:
            # 打印官方给出的错误原因（info 字段）
            print(f"❌ 高德接口报错: {data.get('info')}")
            
    except Exception as e:
        print(f"💥 网络请求失败 (请确认 M4 是否能直连高德): {e}")

if __name__ == "__main__":
    interval = int(os.getenv("INTERVAL", "3600"))
    print(f"🚀 高德气象站已启动，更新频率: {interval}s")
    
    fetch_weather() # 启动即同步
    
    while True:
        time.sleep(interval)
        fetch_weather()
