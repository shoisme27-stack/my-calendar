import requests
import datetime
import json
import os
from lunarcalendar import Converter, Lunar

# 取得目前年份
current_year = datetime.datetime.now().year
# 抓取 去年、今年、明年，確保跨年數據完整
years = [current_year - 1, current_year, current_year + 1]

# 定義 ICS 檔案標頭
ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//My Custom Calendar//CN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:大陸休假 & 節日", 
    "X-WR-TIMEZONE:Asia/Shanghai",
]

# --- 輔助函式：產生 ICS 事件區塊 ---
def create_event(date_str, summary, event_type):
    # 日期格式 YYYY-MM-DD
    dt_start = date_str.replace("-", "")
    dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    dt_end_obj = dt_obj + datetime.timedelta(days=1)
    dt_end = dt_end_obj.strftime("%Y%m%d")
    
    # 使用 日期+類型 製作唯一 ID，避免七夕或節日消失
    uid = f"{dt_start}_{event_type}@mycustomcal"
    
    return [
        "BEGIN:VEVENT",
        f"DTSTART;VALUE=DATE:{dt_start}",
        f"DTEND;VALUE=DATE:{dt_end}",
        f"SUMMARY:{summary}",
        "TRANSP:TRANSPARENT",
        f"UID:{uid}",
        "END:VEVENT"
    ]

# --- 第一部分：處理政府發布的休假與補班 ---
for year in years:
    # 雙源備援
    urls = [
        f"https://natescarlet.github.io/holiday-cn/release/{year}.json",
        f"https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json"
    ]
    
    data = None
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                break
        except:
            continue
            
    if data:
        for day in data['days']:
            date_str = day['date']
            is_off = day['isOffDay']
            # 更新圖標：休假用雀躍派對臉，補班用骷髏頭
            if is_off:
                summary = "🥳 放假啦！"
                e_type = "HOLIDAY"
            else:
                summary = "💀 慘遭補班"
                e_type = "WORK"
            ics_content.extend(create_event(date_str, summary, e_type))

# --- 第二部分：處理您指定的特殊節日 ---
for year in years:
    # 1. 固定公曆節日
    fixed_festivals = {
        "02-14": "💖 情人節",
        "12-25": "🎄 聖誕節"
    }
    for date_suffix, name in fixed_festivals.items():
        ics_content.extend(create_event(f"{year}-{date_suffix}", name, "FESTIVAL"))

    # 2. 農曆節日：七夕 (農曆七月初七)
    try:
        # 這裡加強了轉換逻辑，確保能正確抓到每一年的七夕
        lunar_date = Lunar(year, 7, 7)
        solar_date = Converter.LunarToSolar(lunar_date)
        if solar_date:
            qixi_str = f"{solar_date.year}-{solar_date.month:02d}-{solar_date.day:02d}"
            ics_content.extend(create_event(qixi_str, "🎋 七夕", "LUNAR"))
            print(f"Success: {year} Qixi is on {qixi_str}")
    except Exception as e:
        print(f"Error calculating Qixi for {year}: {e}")

ics_content.append("END:VCALENDAR")

# 寫入檔案
with open("calendar.ics", "w", encoding="utf-8") as f:
    f.write("\n".join(ics_content))

print("Update complete with 3-year data and new icons!")
