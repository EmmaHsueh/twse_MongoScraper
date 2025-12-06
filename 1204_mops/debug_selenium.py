"""
Debug Selenium - 查看 MOPS 網頁結構
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# 設定 Chrome（顯示瀏覽器）
options = Options()
# options.add_argument('--headless')  # 不使用無頭模式，顯示瀏覽器
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    print("訪問 MOPS 資產負債表頁面...")
    url = 'https://mops.twse.com.tw/mops/web/t163sb05'
    driver.get(url)

    print(f"當前 URL: {driver.current_url}")
    print(f"頁面標題: {driver.title}")

    # 等待頁面載入
    time.sleep(5)

    # 儲存頁面截圖
    driver.save_screenshot('mops_page.png')
    print("已儲存截圖: mops_page.png")

    # 儲存頁面 HTML
    with open('mops_page.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print("已儲存 HTML: mops_page.html")

    # 查找所有 input 元素
    inputs = driver.find_elements('tag name', 'input')
    print(f"\n找到 {len(inputs)} 個 input 元素:")
    for i, inp in enumerate(inputs[:10], 1):  # 只顯示前 10 個
        print(f"  {i}. type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}")

    # 查找所有 select 元素
    selects = driver.find_elements('tag name', 'select')
    print(f"\n找到 {len(selects)} 個 select 元素:")
    for i, sel in enumerate(selects, 1):
        print(f"  {i}. name={sel.get_attribute('name')}, id={sel.get_attribute('id')}")

    print("\n請檢查:")
    print("  1. mops_page.png - 查看頁面截圖")
    print("  2. mops_page.html - 查看完整 HTML")
    print("\n瀏覽器將在 30 秒後自動關閉...")
    time.sleep(30)

except Exception as e:
    print(f"錯誤: {e}")

finally:
    driver.quit()
    print("瀏覽器已關閉")
