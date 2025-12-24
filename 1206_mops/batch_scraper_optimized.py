#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime
from mops_scraper import MOPSScraper
from mongodb_helper import MongoDBHelper
import pandas as pd
import re


class OptimizedBatchScraper:
    def __init__(self, mongodb_uri="mongodb://localhost:27017/", headless=True):
        """
        初始化優化版批次爬蟲

        Args:
            mongodb_uri: MongoDB 連線字串
            headless: 是否使用無頭模式
        """
        self.scraper = MOPSScraper(headless=headless)
        self.db_helper = MongoDBHelper(mongodb_uri)

    def parse_all_companies_from_table(self, html_content, year, season):
        """
        從表格中解析所有公司的資料

        Args:
            html_content: HTML 內容
            year: 年度
            season: 季別

        Returns:
            list: 包含所有公司資料的字典列表
        """
        try:
            # 使用 pandas 讀取所有表格
            tables = pd.read_html(html_content)

            if not tables:
                print(f"  ✗ 未找到表格")
                return []

            print(f"  找到 {len(tables)} 個表格")

            all_records = []

            # 通常主要的資料在第一個或第二個表格
            for table_idx, df in enumerate(tables):
                print(f"\n  分析表格 {table_idx + 1}, 維度: {df.shape}")

                # 檢查是否有公司代號欄位
                # 可能的欄位名稱: "公司代號", "代號", "stock_code" 等
                code_column = None
                for col in df.columns:
                    col_str = str(col).strip()
                    if any(keyword in col_str for keyword in ["公司代號", "公司代碼", "股票代號"]):
                        code_column = col
                        print(f"  ✓ 找到公司代號欄位: {code_column}")
                        break

                if code_column is None:
                    print(f"  ⊙ 表格 {table_idx + 1} 沒有公司代號欄位,跳過")
                    continue

                # 逐列處理
                for idx, row in df.iterrows():
                    try:
                        # 取得公司代號
                        company_code = str(row[code_column]).strip()

                        # 過濾無效的代號
                        if not company_code or company_code == 'nan' or len(company_code) < 4:
                            continue

                        # 清理公司代號 (只保留數字)
                        company_code = re.sub(r'[^0-9]', '', company_code)

                        if not company_code:
                            continue

                        # 檢查公司是否存在於基本資料
                        if not self.db_helper.company_exists(company_code):
                            print(f"    ⊙ {company_code} 不在「公司基本資料」中,跳過")
                            continue

                        # 建立記錄
                        record = {
                            "公司代號": company_code,
                            "年度": year,
                            "季別": season,
                            "爬取時間": datetime.now()
                        }

                        # 將每一欄的資料加入記錄
                        for col_name, value in row.items():
                            clean_col_name = str(col_name).strip()

                            # 跳過公司代號欄位 (已處理)
                            if clean_col_name == code_column:
                                continue

                            # 處理數值
                            if pd.notna(value):
                                # 嘗試轉換為數值
                                try:
                                    # 移除逗號和其他格式字元
                                    if isinstance(value, str):
                                        clean_value = value.replace(',', '').replace('$', '').strip()
                                        if clean_value:
                                            record[clean_col_name] = float(clean_value)
                                        else:
                                            record[clean_col_name] = value
                                    else:
                                        record[clean_col_name] = value
                                except:
                                    record[clean_col_name] = value

                        all_records.append(record)

                    except Exception as e:
                        print(f"    ✗ 處理第 {idx} 列失敗: {e}")
                        continue

            print(f"\n  ✓ 總共解析出 {len(all_records)} 筆有效資料")
            return all_records

        except Exception as e:
            print(f"  ✗ 解析表格失敗: {e}")
            import traceback
            traceback.print_exc()
            return []

    def scrape_and_save_batch(self, market_type, year, season):
        """
        一次爬取並儲存某市場、年度、季別的所有公司資料

        Args:
            market_type: 市場類型 ("sii", "otc")
            year: 年度
            season: 季別

        Returns:
            int: 成功儲存的筆數
        """
        market_names = {"sii": "上市", "otc": "上櫃", "rotc": "興櫃"}
        market_name = market_names.get(market_type, market_type)

        print(f"\n{'='*60}")
        print(f"爬取 {market_name} {year}Q{season}")
        print(f"{'='*60}")

        try:
            # 執行查詢
            print("正在查詢...")
            result_url = self.scraper.scrape_data(market_type, year, season)

            if not result_url:
                print("✗ 查詢失敗")
                return 0

            # 等待頁面完全載入
            time.sleep(3)

            # 取得頁面內容
            html_content = self.scraper.driver.page_source

            # 解析所有公司資料
            print("\n解析表格資料...")
            all_records = self.parse_all_companies_from_table(html_content, year, season)

            if not all_records:
                print("✗ 未解析到任何資料")
                return 0

            # 過濾已存在的資料
            print("\n檢查重複資料...")
            new_records = []
            skip_count = 0

            for record in all_records:
                company_code = record["公司代號"]
                if self.db_helper.balance_sheet_exists(company_code, year, season):
                    skip_count += 1
                else:
                    new_records.append(record)

            print(f"  已存在: {skip_count} 筆")
            print(f"  需新增: {len(new_records)} 筆")

            # 批次儲存到 MongoDB
            if new_records:
                print("\n儲存到 MongoDB...")
                success_count = self.db_helper.insert_balance_sheets_batch(new_records)
                print(f"✓ 成功儲存 {success_count}/{len(new_records)} 筆")
                return success_count
            else:
                print("⊙ 所有資料已存在,無需新增")
                return 0

        except Exception as e:
            print(f"\n✗ 爬取失敗: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def scrape_all_history_optimized(self, market_types=["sii", "otc"], start_year=100, end_year=113):
        """
        按年度+季別批次爬取

        Args:
            market_types: 市場類型列表
            start_year: 起始年度
            end_year: 結束年度
        """
        print("\n" + "="*60)
        print("優化版批次爬蟲 - 按市場別+年度+季別爬取")
        print("="*60)

        market_names = {"sii": "上市", "otc": "上櫃", "rotc": "興櫃"}

        total_success = 0
        total_requests = 0

        for market_type in market_types:
            market_name = market_names.get(market_type, market_type)

            print(f"\n\n{'#'*60}")
            print(f"# {market_name}公司")
            print(f"{'#'*60}")

            for year in range(start_year, end_year + 1):
                for season in range(1, 5):
                    total_requests += 1

                    print(f"\n[請求 {total_requests}] {market_name} {year}Q{season}")

                    # 一次爬取該市場+年度+季別的所有公司
                    success_count = self.scrape_and_save_batch(market_type, year, season)
                    total_success += success_count

                    # 避免請求過於頻繁
                    print("\n休息 5 秒...")
                    time.sleep(5)

        # 顯示總結
        print(f"\n\n{'='*60}")
        print("爬取完成!")
        print(f"{'='*60}")
        print(f"總請求次數: {total_requests}")
        print(f"成功儲存: {total_success} 筆")
        print(f"{'='*60}\n")

    def close(self):
        """關閉連線"""
        self.scraper.close()
        self.db_helper.close()


def main():
    """主程式"""
    print("\n優化版批次爬蟲 - 按市場別+年度+季別批次處理")
    print("="*60)

    scraper = OptimizedBatchScraper(
        mongodb_uri="mongodb://localhost:27017/",
        headless=True
    )

    try:
        # 顯示資料庫狀態
        stats = scraper.db_helper.get_statistics()
        print(f"\n目前資料庫狀態:")
        print(f"  公司總數: {stats['公司總數']}")
        print(f"  上市公司: {stats['上市公司數']}")
        print(f"  上櫃公司: {stats['上櫃公司數']}")
        print(f"  資產負債表: {stats['資產負債表筆數']} 筆")

        print("\n請選擇執行模式:")
        print("1. 完整爬取 (100-113 年,上市+上櫃)")
        print("2. 測試模式 (只爬 113Q3, 上市)")
        print("3. 自訂範圍")

        choice = input("\n請輸入選項 (1/2/3): ").strip()

        if choice == "1":
            # 完整爬取
            scraper.scrape_all_history_optimized(
                market_types=["sii", "otc"],
                start_year=86,
                end_year=99
            )
        elif choice == "2":
            # 測試模式
            print("\n測試模式: 113Q3 上市公司")
            scraper.scrape_and_save_batch("sii", 113, 3)
        elif choice == "3":
            # 自訂範圍
            print("\n自訂爬取範圍:")
            market_input = input("市場別 (sii=上市, otc=上櫃, 多個用逗號分隔): ").strip()
            markets = [m.strip() for m in market_input.split(",")]

            start = int(input("起始年度 (例如:110): "))
            end = int(input("結束年度 (例如:113): "))

            scraper.scrape_all_history_optimized(
                market_types=markets,
                start_year=start,
                end_year=end
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
        scraper.close()
        print("\n程式結束")


if __name__ == "__main__":
    main()
