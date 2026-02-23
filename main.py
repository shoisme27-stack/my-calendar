import requests
import datetime
import json

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
    
    uid = f"v6_{dt_start}_{event_type}@mycustomcal.com"
    
    return [
        "BEGIN:VEVENT",
        f"DTSTART;VALUE=DATE:{dt_start}",
        f"DTEND;VALUE=DATE:{dt_end}",
        f"SUMMARY:{summary}",
        "TRANSP:TRANSPARENT",
        f"UID:{uid}",
        "END:VEVENT"
    ]

# --- 十年免維護農曆對照表 (2024-2036) ---
lunar_festivals = {
    "2024": {"chuxi": "2024-02-09", "duanwu": "2024-06-10", "zhongqiu": "2024-09-17", "qixi": "2024-08-10"},
    "2025": {"chuxi": "2025-01-28", "duanwu": "2025-05-31", "zhongqiu": "2025-10-06", "qixi": "2025-08-29"},
    "2026": {"chuxi": "2026-02-16", "duanwu": "2026-06-19", "zhongqiu": "2026-09-25", "qixi": "2026-08-19"},
    "2027": {"chuxi": "2027-02-05", "duanwu": "2027-06-09", "zhongqiu": "2027-09-15", "qixi": "2027-08-08"},
    "2028": {"chuxi": "2028-01-25", "duanwu": "2028-05-28", "zhongqiu": "2028-10-03", "qixi": "2028-08-26"},
    "2029": {"chuxi": "2029-02-12", "duanwu": "2029-06-16", "zhongqiu": "2029-09-22", "qixi": "2029-08-16"},
    "2030": {"chuxi": "2030-02-02", "duanwu": "2030-06-05", "zhongqiu": "2030-09-12", "qixi": "2030-08-05"},
    "2031": {"chuxi": "2031-01-22", "duanwu": "2031-06-24", "zhongqiu": "2031-10-01", "qixi": "2031-08-24"},
    "2032": {"chuxi": "2032-02-10", "duanwu": "2032-06-12", "zhongqiu": "2032-09-19", "qixi": "2032-08-12"},
    "2033": {"chuxi": "2033-01-30", "duanwu": "2033-06-01", "zhongqiu": "2033-09-08", "qixi": "2033-08-01"},
    "2034": {"chuxi": "2034-02-18", "duanwu": "2034-06-20", "zhongqiu": "2034-09-27", "qixi": "2034-08-20"},
    "2035": {"chuxi": "2035-02-07", "duanwu": "2035-06-10", "zhongqiu": "2035-09-16", "qixi": "2035-08-10"},
    "2036": {"chuxi": "2036-01-27", "duanwu": "2036-05-29", "zhongqiu": "2036-10-04", "qixi": "2036-07-29"}
}

# 清明節對照表 (2024-2036)
qm_dates = {
    "2024": "04-04", "2025": "04-04", "2026": "04-05", "2027": "04-05", "2028": "04-04",
    "2029": "04-04", "2030": "04-05", "2031": "04-05", "2032": "04-04", "2033": "04-04",
    "2034": "04-05", "2035": "04-05", "2036": "04-04"
}

exact_holidays = {}
for y in years:
    ys = str(y)
    # 1. 固定公曆節日
    exact_holidays[f"{ys}-01-01"] = "🎆 元旦"
    exact_holidays[f"{ys}-05-01"] = "👷 五一"
    exact_holidays[f"{ys}-10-01"] = "🇨🇳 十一"
    
    # 2. 清明節
    if ys in qm_dates:
        exact_holidays[f"{ys}-{qm_dates[ys]}"] = "🍃 清明"
        
    # 3. 農曆節日
    if ys in lunar_festivals:
        exact_holidays[lunar_festivals[ys]["chuxi"]] = "🏮 除夕"
        exact_holidays[lunar_festivals[ys]["duanwu"]] = "🐉 端午"
        exact_holidays[lunar_festivals[ys]["zhongqiu"]] = "🌕 中秋"

# --- 處理政府休假/補班 ---
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
                # 只有官方認定是休假的日子，才會配對標籤
                summary = exact_holidays.get(date_str, "🥳 放假！")
                ics_content.extend(create_event(date_str, summary, "OFF"))
            else:
                ics_content.extend(create_event(date_str, "💀 補班", "WORK"))

# --- 加入額外自訂節日 (不放假) ---
for year in years:
    ys = str(year)
    ics_content.extend(create_event(f"{ys}-02-14", "💖 情人節", "FEST"))
    ics_content.extend(create_event(f"{ys}-12-25", "🎄 聖誕節", "FEST"))

    # 加入七夕
    if ys in lunar_festivals:
        ics_content.extend(create_event(lunar_festivals[ys]["qixi"], "🎋 七夕", "QIXI"))

ics_content.append("END:VCALENDAR")

with open("calendar.ics", "w", encoding="utf-8") as f:
    f.write("\n".join(ics_content))

print("10年免維護完美版日曆產生完畢！")
