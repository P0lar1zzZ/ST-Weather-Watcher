/**
 * 🌦️ SillyTavern 实时天气同步脚本 这个要贴在酒馆助手全局脚本里并打开
 */
(async function() {
    async function updateWeather() {
        try {
            // 加上时间戳防止缓存，只在根目录下寻找 weather.txt
            const res = await fetch('/weather.txt?v=' + Date.now());
            if (!res.ok) return;

            const text = await res.text();
            const cleanText = text.trim();
            
            if (cleanText && window.SillyTavern && window.SillyTavern.executeSlashCommands) {
                // 自动赋值给酒馆变量 {{getvar::weather}}
                window.SillyTavern.executeSlashCommands(`/setvar name=weather value=${cleanText}`);
                console.log("🌦️ 气象站同步成功:", cleanText);
            }
        } catch (e) {
            // 默默失败，不打扰对话
        }
    }
    
    // 启动 2 秒后初次运行，之后每分钟更新一次
    setTimeout(updateWeather, 2000);
    setInterval(updateWeather, 60000);
})();
