import json
import os
from datetime import datetime
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 設定學期第一週的開始日期（這個日期可以根據你的學校行事曆調整）
semester_start_date = datetime(2024, 8, 30)  # 假設學期從 8 月 30 日開始

# 計算今天是第幾週
today = datetime.today()
days_since_start = (today - semester_start_date).days
current_week = days_since_start // 7 + 2  # 計算週數

print(f"現在是第 {current_week} 週")

# 從環境變數中讀取帳號和密碼
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

# 使用 webdriver_manager 自動設置 ChromeDriver
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()

# 啟用無頭模式和其他參數
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920x1080')

# 初始化 WebDriver
driver = webdriver.Chrome(service=service, options=options)

# 設置隱性等待時間
driver.implicitly_wait(40)

# 開啟目標網站
driver.get("https://app.1campus.net/")

# 找到按鈕並點擊
button = driver.find_element(By.CLASS_NAME, "btn-square")
button.click()
print("按鈕已點擊")

# 設置顯性等待
wait = WebDriverWait(driver, 60)

# 找到並填寫帳號
email_field = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
email_field.send_keys(username)
email_field.send_keys(Keys.RETURN)
print("帳號已輸入")

# 找到並填寫密碼
password_field = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
password_field.send_keys(password)
password_field.send_keys(Keys.RETURN)
print("密碼已輸入")

# 找到並點擊指定的課表圖片
timetable_img = wait.until(EC.element_to_be_clickable((By.XPATH, "//img[@src='https://campus-lite.web.app/icons/tschool/timetable.png' and @alt='學生課表']")))
timetable_img.click()
print("課表圖片已點擊")

# 等待新分頁打開
wait.until(lambda driver: len(driver.window_handles) > 1)

# 記錄當前分頁的句柄
original_window = driver.current_window_handle

# 切換到新分頁
driver.switch_to.window(driver.window_handles[-1])
print("已切換到新分頁")

# 等待頁面加載完成
time.sleep(40)  # 根據實際情況調整等待時間

# 查找特定的封包
timetable_data = None
for request in driver.requests:
    if request.response and "https://asia-east1-campus-lite.cloudfunctions.net/tschool/timetable" in request.url:
        timetable_data = request.response.body.decode('utf-8')
        break

if timetable_data:
    # 將課表數據轉換為 JSON 格式
    timetable_data = json.loads(timetable_data)
    
    # 過濾出下一週的課程內容
    next_week = current_week + 1
    next_week_schedule = []

    for entry in timetable_data:
        week_str = entry.get('週次', '').strip()
        day = entry.get('星期', '').strip()
        if week_str.isdigit() and int(week_str) == next_week and day != '':
            next_week_schedule.append(entry)

    # 初始化嵌套列表結構
    schedule_list = [[[], []] for _ in range(7)]  # 7天，每天兩個時段

    # 將資料存入對應的列表位置
    for entry in next_week_schedule:
        day = int(entry.get('星期', 0)) - 1  # 星期一對應索引0
        periods = entry.get('節次', '').split(',')
        for period in periods:
            period = period.strip()
            if '1' in period或 '2' in period或 '3' in period或 '4' in period:
                if not schedule_list[day][0]:
                    schedule_list[day][0].append(1)
            elif '5' in period或 '6' in period或 '7' in period或 '8' in period:
                if not schedule_list[day][1]:
                    schedule_list[day][1].append(1)
else:
    print("未找到課表封包")

# 切換回原本的分頁
driver.switch_to.window(original_window)
print("已切換回原本的分頁")

# 找到並點擊學習週曆圖片
calendar_img = wait.until(EC.element_to_be_clickable((By.XPATH, "//img[@src='https://campus-lite.web.app/icons/tschool/calendar.png' and @alt='學習週曆']")))
calendar_img.click()
print("學習週曆圖片已點擊")

# 等待新分頁打開
wait.until(lambda driver: len(driver.window_handles) > 2)

# 切換到新分頁
driver.switch_to.window(driver.window_handles[-1])
print("已切換到學習週曆的新分頁")

# 找到並點擊「待填下週」的標籤
next_week_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='tabs tabs-boxed']/a[text()='待填下週']")))
next_week_tab.click()
print("已點擊「待填下週」標籤")

# 找到並點擊「週曆填報」按鈕
report_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-sm btn-neutral' and .//span[text()='週曆填報']]")))
report_button.click()
print("已點擊「週曆填報」按鈕")

time.sleep(20)

# 遍歷選擇地點
select_elements = driver.find_elements(By.XPATH, "//div[@class='p-4 space-y-4']//select")
for i, select_element in enumerate(select_elements):
    day_index = i // 2
    period_index = i % 2
    # 根據 schedule_list 的內容選擇地點
    if schedule_list[day_index][period_index]:
        location = "吉林基地"
    else:
        location = "在家中"
    
    for option in select_element.find_elements(By.TAG_NAME, 'option'):
        if option.get_attribute('value') == location:
            option.click()
            break

# 點擊「回報計劃」按鈕
report_plan_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-neutral' and .//span[text()='回報計劃']]")))
report_plan_button.click()
print("已點擊「回報計劃」按鈕")

time.sleep(10)

# 關閉瀏覽器
driver.quit()