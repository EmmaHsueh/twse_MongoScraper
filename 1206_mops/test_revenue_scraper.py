#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試每月營收爬蟲
"""

from monthly_revenue_scraper import MonthlyRevenueScraper


def test_single_request():
    """測試單一請求"""
    print("="*60)
    print("測試每月營收爬蟲 - 單一請求測試")
    print("="*60)

    scraper = MonthlyRevenueScraper()

    try:
        # 測試 1: 民國 91 年 1 月 (無分國內外)
        print("\n【測試 1】民國 91 年 1 月上市公司營收 (無分國內外)")
        success = scraper.scrape_single_month(
            market_type="sii",
            year=91,
            month=1,
            data_type=None,
            delay=1
        )
        print(f"結果: 成功儲存 {success} 筆資料")

        # 測試 2: 民國 100 年 1 月國內 (有分國內外)
        print("\n【測試 2】民國 100 年 1 月上市公司營收 - 國內")
        success = scraper.scrape_single_month(
            market_type="sii",
            year=100,
            month=1,
            data_type="0",  # 國內
            delay=1
        )
        print(f"結果: 成功儲存 {success} 筆資料")

        # 測試 3: 民國 100 年 1 月國外 (有分國內外)
        print("\n【測試 3】民國 100 年 1 月上市公司營收 - 國外")
        success = scraper.scrape_single_month(
            market_type="sii",
            year=100,
            month=1,
            data_type="1",  # 國外
            delay=1
        )
        print(f"結果: 成功儲存 {success} 筆資料")

        # 顯示統計
        print("\n" + "="*60)
        print("資料庫統計:")
        stats = scraper.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print("="*60)

    except Exception as e:
        print(f"\n測試失敗: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    test_single_request()
