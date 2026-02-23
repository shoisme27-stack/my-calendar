import requests
import datetime
import json
import os
from lunarcalendar import Converter, Lunar

# 取得目前年份並涵蓋 去年、今年、明年
current_year = datetime.datetime.now().year
years = [current_year - 1, current_year, current_year + 1]

ics_content = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//My Smart Calendar//CN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:大陸休假 & 節日", 
    "X-WR-TIMEZONE:Asia/Shanghai",
]

def create_event(date_str, summary, event_type):
    dt_start = date_str.replace("-", "")
    dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    dt_end = (dt_obj + datetime.timedelta(days=1)).strftime("%Y%m%d")
    
    # 升級 UID 版本，確保手機強制刷新抓取最新圖標與名稱
    uid = f"v4_{dt_start}_{event_type}@mycustomcal.com"
    
    return [
        "BEGIN:VEVENT",
        f"DTSTART;VALUE=DATE:{dt_start}",
        f"DTEND;VALUE=DATE:{dt_end}",
        f"SUMMARY:{summary}",
        "TRANSP:TRANSPARENT",
        f"UID:{uid}",
        "END:VEVENT"
    ]

# --- 準備工作：預先計算每年的「核心節日正日子」 ---
exact_holidays = {}
for y in years:
    # 固定公曆節日
    exact_holidays[f"{y}-01-01"] = "🎆 元旦"
    exact_holidays[f"{y}-05-01"] = "👷 五一"
    exact_holidays[f"{y}-10-01"] = "🇨🇳 十一"
    
    # 清明節 (通常是 4/4 或 4/5，建立對照表確保穩定)
    qm_dates = {2024: "04-04", 2025: "04-04", 2026: "04-05", 2027: "04-05", 2028: "04-04"}
    if y in qm_dates:
        exact_holidays[f"{y}-{qm_dates[y]}"] = "🍃 清明"
    
    try:
        # 端午 (農曆五月初五)
        dw = Converter.LunarToSolar(Lunar(y, 5, 5))
        exact_holidays[f"{dw.year}-{dw.month:02d}-{dw.day:02d}"] = "🐉 端午"
        
        # 中秋 (農曆八月十五)
        zq = Converter.LunarToSolar(Lunar(y, 8, 15))
        exact_holidays[f"{zq.year}-{zq.month:02d}-{zq.day:02d}"] = "🌕 中秋"
        
        # 除夕 (農曆正月初一的「前一天」)
        sf = Converter.LunarToSolar(Lunar(y, 1, 1)) # 當年春節
        chuxi_date = datetime.date(sf.year, sf.month, sf.day) - datetime.timedelta(days=1)
        exact_holidays[chuxi_date.strftime("%Y-%m-%d")] = "🏮 除夕"
    except Exception as e:
        print(f"Error calculating lunar exact holidays for {y}: {e}")

# --- 1. 處理政府休假/補班 ---
for year in years:
    urls = [
        f"https://natescarlet.github.io/holiday-cn/release/{year}.json",
        f"https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json"
    ]
    data = None
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                break
        except: continue
            
    if data:
        for day in data['days']:
            date_str = day['date']
            is_off = day['isOffDay']
            
            if is_off:
                # 判斷這天是不是「正日子」
                if date_str in exact_holidays:
                    summary = exact_holidays[date_str] # 替換成：節日名 + 圖標
                else:
                    summary = "🥳 放假！" # 普通連假日子
                e_type = "OFF"
            else:
                summary = "💀 補班"
                e_type = "WORK"
                
            ics_content.extend(create_event(date_str, summary, e_type))

# --- 2. 加入額外的自訂不放假節日 ---
for year in years:
    # 情人節、聖誕節
    ics_content.extend(create_event(f"{year}-02-14", "💖 情人節", "FESTIVAL"))
    ics_content.extend(create_event(f"{year}-12-25", "🎄 聖誕節", "FESTIVAL"))

    # 農曆七夕
    try:
        qixi = Converter.LunarToSolar(Lunar(year, 7, 7))
        qixi_date = f"{qixi.year}-{qixi.month:02d}-{qixi.day:02d}"
        ics_content.extend(create_event(qixi_date, "🎋 七夕", "QIXI"))
    except: pass

ics_content.append("END:VCALENDAR")

with open("calendar.ics", "w", encoding="utf-8") as f:
    f.write("\n".join(ics_content))

print("完美版日曆產生完畢！")
