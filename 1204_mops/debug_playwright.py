"""
Debug Playwright - 詳細查看 MOPS 網頁結構
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_mops():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 顯示瀏覽器
        page = await browser.new_page()

        print("訪問 MOPS 資產負債表頁面...")
        url = 'https://mops.twse.com.tw/mops/web/t163sb05'
        await page.goto(url, wait_until='networkidle')

        print(f"當前 URL: {page.url}")
        print(f"頁面標題: {await page.title()}")

        # 等待頁面完全載入
        await asyncio.sleep(5)

        # 儲存截圖
        await page.screenshot(path='mops_playwright.png', full_page=True)
        print("已儲存截圖: mops_playwright.png")

        # 儲存 HTML
        content = await page.content()
        with open('mops_playwright.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("已儲存 HTML: mops_playwright.html")

        # 查找所有 input 元素
        inputs = await page.locator('input').all()
        print(f"\n找到 {len(inputs)} 個 input 元素:")
        for i, inp in enumerate(inputs[:15], 1):  # 只顯示前 15 個
            name = await inp.get_attribute('name')
            id_attr = await inp.get_attribute('id')
            type_attr = await inp.get_attribute('type')
            placeholder = await inp.get_attribute('placeholder')
            print(f"  {i}. type={type_attr}, name={name}, id={id_attr}, placeholder={placeholder}")

        # 查找所有 select 元素
        selects = await page.locator('select').all()
        print(f"\n找到 {len(selects)} 個 select 元素:")
        for i, sel in enumerate(selects, 1):
            name = await sel.get_attribute('name')
            id_attr = await sel.get_attribute('id')
            print(f"  {i}. name={name}, id={id_attr}")

        # 查找所有 button 元素
        buttons = await page.locator('button').all()
        print(f"\n找到 {len(buttons)} 個 button 元素:")
        for i, btn in enumerate(buttons[:10], 1):
            text = await btn.text_content()
            print(f"  {i}. text={text}")

        print("\n瀏覽器將在 60 秒後自動關閉...")
        print("請查看:")
        print("  1. mops_playwright.png - 頁面截圖")
        print("  2. mops_playwright.html - HTML 原始碼")
        await asyncio.sleep(60)

        await browser.close()
        print("瀏覽器已關閉")


if __name__ == '__main__':
    asyncio.run(debug_mops())
