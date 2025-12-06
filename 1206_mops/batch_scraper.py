#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次爬取上市櫃公司歷史資產負債表資料
支援 MongoDB 儲存、去重、斷點續傳
"""

import time
from datetime import datetime
from mops_scraper import MOPSScraper
from mongodb_helper import MongoDBHelper
import pandas as pd


class BatchBalanceSheetScraper:
    def __init__(self, mongodb_uri="mongodb://localhost:27017/", headless=True):
        """
        初始化批次爬蟲

        Args:
            mongodb_uri: MongoDB 連線字串
            headless: 是否使用無頭模式
        """
        self.scraper = MOPSScraper(headless=headless)
        self.db_helper = MongoDBHelper(mongodb_uri)

    def parse_balance_sheet_table(self, html_content, company_code, year, season):
        """
        解析資產負債表 HTML 表格

        Args:
            html_content: HTML 內容
            company_code: 公司代號
            year: 年度
            season: 季別

        Returns:
            list: 解析後的資料列表
        """
        try:
            # 使用 pandas 讀取所有表格
            tables = pd.read_html(html_content)

            if not tables:
                print(f"  ✗ 未找到表格")
                return []

            # 通常第一個表格是主要的資產負債表
            main_table = tables[0]

            # 轉換為字典列表
            records = []
            for _, row in main_table.iterrows():
                record = {
                    "公司代號": company_code,
                    "年度": year,
                    "季別": season,
                    "爬取時間": datetime.now()
                }

                # 將每一列的資料加入記錄
                for col_name, value in row.items():
                    # 清理欄位名稱
                    clean_col_name = str(col_name).strip()
                    record[clean_col_name] = value

                records.append(record)

            print(f"  ✓ 解析出 {len(records)} 筆資料")
            return records

        except Exception as e:
            print(f"  ✗ 解析表格失敗: {e}")
            return []

    def scrape_and_save_one(self, market_type, company_code, year, season):
        """
        爬取並儲存單一公司的資產負債表

        Args:
            market_type: 市場類型
            company_code: 公司代號
            year: 年度
            season: 季別

        Returns:
            bool: 是否成功
        """
        try:
            # 檢查是否已存在
            if self.db_helper.balance_sheet_exists(company_code, year, season):
                print(f"  ⊙ {company_code} {year}Q{season} 資料已存在,跳過")
                return True

            # 執行爬蟲
            result_url = self.scraper.scrape_data(market_type, year, season)

            if not result_url:
                return False

            # 等待頁面載入
            time.sleep(2)

            # 取得頁面內容
            html_content = self.scraper.driver.page_source

            # 解析表格
            records = self.parse_balance_sheet_table(html_content, company_code, year, season)

            if records:
                # 儲存到 MongoDB
                success_count = self.db_helper.insert_balance_sheets_batch(records)
                print(f"  ✓ 成功儲存 {success_count} 筆資料")
                return success_count > 0
            else:
                return False

        except Exception as e:
            print(f"  ✗ 爬取失敗: {e}")
            return False

    def scrape_all_history(self, market_types=["sii", "otc"], start_year=100, end_year=113):
        """
        爬取所有上市櫃公司的歷史資料

        Args:
            market_types: 市場類型列表
            start_year: 起始年度 (民國)
            end_year: 結束年度 (民國)
        """
        print("\n" + "="*60)
        print("批次爬取上市櫃公司資產負債表")
        print("="*60)

        market_names = {"sii": "上市", "otc": "上櫃", "rotc": "興櫃", "pub": "公開發行"}

        for market_type in market_types:
            market_name = market_names.get(market_type, market_type)
            print(f"\n\n【{market_name}公司】")
            print("-" * 60)

            # 從 MongoDB 取得該市場的所有公司代號
            company_codes = self.db_helper.get_all_company_codes(market_type)

            if not company_codes:
                print(f"⚠ 未找到{market_name}公司資料,請先建立「公司基本資料」")
                continue

            print(f"共 {len(company_codes)} 家公司")
            print(f"爬取期間: {start_year} - {end_year} 年")
            print(f"總共需爬取: {len(company_codes) * (end_year - start_year + 1) * 4} 筆")

            # 統計資料
            total_count = 0
            success_count = 0
            skip_count = 0
            fail_count = 0

            # 逐一爬取每家公司
            for idx, company_code in enumerate(company_codes, 1):
                print(f"\n[{idx}/{len(company_codes)}] 公司代號: {company_code}")

                # 檢查公司是否存在於基本資料
                if not self.db_helper.company_exists(company_code):
                    print(f"  ⚠ {company_code} 不在「公司基本資料」中,跳過")
                    skip_count += 1
                    continue

                # 爬取所有年度和季度
                for year in range(start_year, end_year + 1):
                    for season in range(1, 5):
                        total_count += 1

                        print(f"  爬取 {year}Q{season}...", end=" ")

                        # 檢查是否已存在
                        if self.db_helper.balance_sheet_exists(company_code, year, season):
                            print("已存在,跳過")
                            skip_count += 1
                            continue

                        # 執行爬蟲
                        if self.scrape_and_save_one(market_type, company_code, year, season):
                            success_count += 1
                        else:
                            fail_count += 1

                        # 避免請求過於頻繁
                        time.sleep(3)

                # 每爬完一家公司,休息較長時間
                if idx < len(company_codes):
                    print(f"\n  休息 10 秒...")
                    time.sleep(10)

            # 顯示統計
            print(f"\n\n{'='*60}")
            print(f"【{market_name}】爬取完成")
            print(f"{'='*60}")
            print(f"總共處理: {total_count} 筆")
            print(f"成功爬取: {success_count} 筆")
            print(f"已存在跳過: {skip_count} 筆")
            print(f"失敗: {fail_count} 筆")
            print(f"{'='*60}\n")

    def scrape_missing_data(self, market_types=["sii", "otc"], start_year=100, end_year=113):
        """
        只爬取缺少的資料 (更高效)

        Args:
            market_types: 市場類型列表
            start_year: 起始年度
            end_year: 結束年度
        """
        print("\n" + "="*60)
        print("智慧補缺 - 只爬取缺少的資料")
        print("="*60)

        market_names = {"sii": "上市", "otc": "上櫃", "rotc": "興櫃", "pub": "公開發行"}

        for market_type in market_types:
            market_name = market_names.get(market_type, market_type)
            print(f"\n【{market_name}公司】")

            company_codes = self.db_helper.get_all_company_codes(market_type)

            if not company_codes:
                print(f"⚠ 未找到{market_name}公司資料")
                continue

            print(f"檢查 {len(company_codes)} 家公司的缺漏資料...")

            # 收集所有缺少的資料
            all_missing = []
            for company_code in company_codes:
                if not self.db_helper.company_exists(company_code):
                    continue

                missing = self.db_helper.get_missing_data(company_code, start_year, end_year)
                for year, season in missing:
                    all_missing.append((market_type, company_code, year, season))

            print(f"\n找到 {len(all_missing)} 筆缺少的資料")

            if not all_missing:
                print("✓ 資料完整,無需補爬")
                continue

            # 爬取缺少的資料
            success_count = 0
            for idx, (mt, code, year, season) in enumerate(all_missing, 1):
                print(f"\n[{idx}/{len(all_missing)}] {code} {year}Q{season}")

                if self.scrape_and_save_one(mt, code, year, season):
                    success_count += 1

                time.sleep(3)

            print(f"\n✓ 補爬完成: {success_count}/{len(all_missing)}")

    def close(self):
        """關閉連線"""
        self.scraper.close()
        self.db_helper.close()


def main():
    """主程式"""
    print("\n上市櫃公司資產負債表批次爬蟲")
    print("="*60)

    # 建立爬蟲實例
    batch_scraper = BatchBalanceSheetScraper(
        mongodb_uri="mongodb://localhost:27017/",
        headless=True  # 背景執行
    )

    try:
        # 顯示資料庫統計
        stats = batch_scraper.db_helper.get_statistics()
        print(f"\n目前資料庫狀態:")
        print(f"  公司總數: {stats['公司總數']}")
        print(f"  上市公司: {stats['上市公司數']}")
        print(f"  上櫃公司: {stats['上櫃公司數']}")
        print(f"  資產負債表: {stats['資產負債表筆數']} 筆")

        # 選擇模式
        print("\n請選擇執行模式:")
        print("1. 完整爬取 (爬取所有歷史資料,自動跳過已存在)")
        print("2. 智慧補缺 (只爬取缺少的資料,最高效)")
        print("3. 測試模式 (只爬取少量資料測試)")

        choice = input("\n請輸入選項 (1/2/3): ").strip()

        if choice == "1":
            # 完整爬取
            batch_scraper.scrape_all_history(
                market_types=["sii", "otc"],
                start_year=100,
                end_year=113
            )
        elif choice == "2":
            # 智慧補缺
            batch_scraper.scrape_missing_data(
                market_types=["sii", "otc"],
                start_year=100,
                end_year=113
            )
        elif choice == "3":
            # 測試模式 - 只爬取最近一年
            print("\n測試模式: 爬取 113 年資料")
            batch_scraper.scrape_all_history(
                market_types=["sii"],
                start_year=113,
                end_year=113
            )
        else:
            print("無效的選項")

    except KeyboardInterrupt:
        print("\n\n⚠ 使用者中斷執行")
    except Exception as e:
        print(f"\n✗ 執行失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        batch_scraper.close()
        print("\n程式結束")


if __name__ == "__main__":
    main()
