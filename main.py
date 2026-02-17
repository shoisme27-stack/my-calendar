import requests
import datetime
import json
import os
from lunarcalendar import Converter, Lunar

# 設定年份 (抓取今年和明年)
current_year = datetime.datetime.now().year
years = [current_year, current_year + 1]

# 定義 ICS 檔案標頭
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//My Custom Holiday Calendar//CN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:大陸休假 & 節日", 
    "X-WR-TIMEZONE:Asia/Shanghai",
]

# --- 輔助函式：產生 ICS 事件區塊 ---
def create_event(date_str, summary):
    # 日期格式 YYYY-MM-DD
    dt_start = date_str.replace("-", "")
    dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    dt_end_obj = dt_obj + datetime.timedelta(days=1)
    dt_end = dt_end_obj.strftime("%Y%m%d")
    
    return [
        "BEGIN:VEVENT",
        f"DTSTART;VALUE=DATE:{dt_start}",
        f"DTEND;VALUE=DATE:{dt_end}",
        f"SUMMARY:{summary}",
        "TRANSP:TRANSPARENT",
        "UID:" + dt_start + "_" + summary + "@mycalendar",
        "END:VEVENT"
    ]

# --- 第一部分：處理政府發布的休假與補班 ---
for year in years:
    url = f"https://natescarlet.github.io/holiday-cn/release/{year}.json"
    try:
        print(f"Fetching holiday data for {year}...")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for day in data['days']:
                date_str = day['date']
                is_off = day['isOffDay']
                
                # 只有休假和補班，沒有鬧鐘文字
                summary = "🔴 休假" if is_off else "⚫ 補班"
                ics_content.extend(create_event(date_str, summary))
    except Exception as e:
        print(f"Note: Official data for {year} might not be ready yet. ({e})")

# --- 第二部分：處理您指定的特殊節日 ---
for year in years:
    # 1. 固定公曆節日
    fixed_festivals = {
        "02-14": "💖 情人節",
        "12-25": "🎄 聖誕節"
    }
    
    for date_suffix, name in fixed_festivals.items():
        date_str = f"{year}-{date_suffix}"
        ics_content.extend(create_event(date_str, name))

    # 2. 農曆節日：七夕 (農曆七月初七)
    try:
        lunar_date = Lunar(year, 7, 7, leep=False)
        solar_date = Converter.LunarToSolar(lunar_date)
        
        if solar_date:
            qixi_date_str = f"{solar_date.year}-{solar_date.month:02d}-{solar_date.day:02d}"
            ics_content.extend(create_event(qixi_date_str, "🎋 七夕"))
            
    except Exception as e:
        print(f"Error calculating Qixi for {year}: {e}")

ics_content.append("END:VCALENDAR")

# 寫入檔案
with open("calendar.ics", "w", encoding="utf-8") as f:
    f.write("\n".join(ics_content))

print("Done! calendar.ics generated.")
