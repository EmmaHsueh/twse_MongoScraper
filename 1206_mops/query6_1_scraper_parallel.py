#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOPS 網站爬蟲 - 查詢 query6_1 頁面資料（多進程並行版本）
針對 https://mops.twse.com.tw/mops/#/web/query6_1
使用 3 個並行進程爬取公司特定年月的資料
"""

import time
import json
import logging
import random
from datetime import datetime
from multiprocessing import Process, Queue, Manager
from query6_1_scraper import Query61Scraper, generate_year_month_list
from mongodb_helper import MongoDBHelper


def setup_logger(process_id):
    """
    為每個進程設定 logger
    """
    logger = logging.getLogger(f'process_{process_id}')
    logger.setLevel(logging.INFO)

    # 檔案處理器（每個進程獨立的 log 檔）
    fh = logging.FileHandler(f'query6_1_scraper_p{process_id}.log', encoding='utf-8')
    fh.setLevel(logging.INFO)

    # 格式設定
    formatter = logging.Formatter('%(asctime)s - [P%(process)d] - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    return logger


def worker_process(process_id, task_queue, result_queue, year_month_list, stop_event):
    """
    工作進程：從隊列中取得公司代號並爬取資料

    Args:
        process_id: 進程編號
        task_queue: 任務隊列（公司代號）
        result_queue: 結果隊列（統計資訊）
        year_month_list: 年月列表
        stop_event: 停止事件
    """
    logger = setup_logger(process_id)
    logger.info(f"進程 {process_id} 啟動")

    # 初始化爬蟲和 MongoDB（每個進程獨立）
    scraper = Query61Scraper(headless=True)
    mongo_helper = MongoDBHelper()

    try:
        # 開啟網頁
        logger.info(f"進程 {process_id} 正在開啟 MOPS 網站...")
        scraper.driver.get(scraper.url)
        time.sleep(1.5)

        # 統計變數
        process_success_count = 0
        process_fail_count = 0

        # 取得公司代號
        while not stop_event.is_set():
            try:
                # 非阻塞式取得任務（timeout=1秒）
                task = task_queue.get(timeout=1)

                if task is None:  # 結束信號
                    logger.info(f"進程 {process_id} 收到結束信號")
                    break

                company_code, year, month = task

                logger.info(f"進程 {process_id} 開始處理: {company_code} - {year}年{month}月")

                # 爬取資料
                data = scraper.scrape_company_data(company_code, year, month)

                if data:
                    # 存入 MongoDB
                    if scraper.save_to_mongodb(mongo_helper, data):
                        process_success_count += 1
                        result_queue.put(('success', company_code, year, month))
                    else:
                        process_fail_count += 1
                        result_queue.put(('fail', company_code, year, month))
                else:
                    process_fail_count += 1
                    result_queue.put(('fail', company_code, year, month))

                # 隨機延遲（每個進程獨立）
                delay = random.uniform(0.3, 0.8)  # 稍微增加延遲以保持穩定
                time.sleep(delay)

            except Exception as e:
                if not stop_event.is_set():
                    logger.error(f"進程 {process_id} 發生錯誤: {e}")
                    continue
                else:
                    break

        logger.info(f"進程 {process_id} 完成，成功: {process_success_count}，失敗: {process_fail_count}")

    except KeyboardInterrupt:
        logger.info(f"進程 {process_id} 被中斷")
    finally:
        scraper.close()
        mongo_helper.close()
        logger.info(f"進程 {process_id} 關閉")


def main():
    """主程式"""
    # 設定主日誌（確保立即寫入）
    file_handler = logging.FileHandler('query6_1_scraper_main.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - [MAIN] - %(levelname)s - %(message)s'))

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - [MAIN] - %(levelname)s - %(message)s'))

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, stream_handler]
    )
    main_logger = logging.getLogger('main')

    # 強制立即 flush
    for handler in main_logger.handlers:
        handler.flush()

    print("\n" + "="*60)
    print("MOPS Query6_1 爬蟲程式 - 多進程並行版本")
    print("="*60 + "\n")

    main_logger.info("="*60)
    main_logger.info("程式啟動 - 多進程並行爬蟲")
    main_logger.info("="*60)

    # 連接 MongoDB（主進程）
    print("正在連接 MongoDB...")
    mongo_helper = MongoDBHelper()

    # 顯示選單
    print("\n請選擇爬取模式：")
    print("1. 完整爬取（所有上市上櫃公司）")
    print("2. 部分爬取（指定索引範圍）")
    print("3. 個別爬取（輸入特定公司代號）")

    choice = input("\n請輸入選項 (1/2/3): ").strip()

    # 根據選擇決定要爬取的公司代號
    all_codes = []

    if choice == "1":
        # 完整爬取
        print("\n正在取得所有公司代號...")
        sii_codes = mongo_helper.get_all_company_codes("sii")  # 上市
        otc_codes = mongo_helper.get_all_company_codes("otc")  # 上櫃
        all_codes = sii_codes + otc_codes
        print(f"\n總共需要爬取 {len(all_codes)} 家公司")
        print(f"  - 上市: {len(sii_codes)} 家")
        print(f"  - 上櫃: {len(otc_codes)} 家")

    elif choice == "2":
        # 部分爬取
        print("\n正在取得所有公司代號...")
        sii_codes = mongo_helper.get_all_company_codes("sii")
        otc_codes = mongo_helper.get_all_company_codes("otc")
        all_available_codes = sii_codes + otc_codes

        print(f"\n可用公司總數: {len(all_available_codes)}")
        print(f"  - 上市: {len(sii_codes)} 家")
        print(f"  - 上櫃: {len(otc_codes)} 家")

        # 讓使用者選擇範圍
        while True:
            try:
                start_idx = int(input(f"\n請輸入起始索引 (0-{len(all_available_codes)-1}): "))
                end_idx = int(input(f"請輸入結束索引 (0-{len(all_available_codes)-1}): "))

                if 0 <= start_idx < len(all_available_codes) and 0 <= end_idx < len(all_available_codes) and start_idx <= end_idx:
                    all_codes = all_available_codes[start_idx:end_idx+1]
                    print(f"\n將爬取 {len(all_codes)} 家公司（索引 {start_idx} 到 {end_idx}）")
                    print(f"公司代號: {', '.join(all_codes[:10])}{'...' if len(all_codes) > 10 else ''}")
                    break
                else:
                    print("✗ 索引範圍無效，請重新輸入")
            except ValueError:
                print("✗ 請輸入有效的數字")

    elif choice == "3":
        # 個別爬取
        print("\n請輸入要爬取的公司代號")
        codes_input = input("多個代號請用逗號分隔 (例如: 2330,1101,2317): ").strip()
        all_codes = [code.strip() for code in codes_input.split(",") if code.strip()]

        if all_codes:
            print(f"\n將爬取 {len(all_codes)} 家公司: {', '.join(all_codes)}")
        else:
            print("✗ 沒有輸入有效的公司代號")
            mongo_helper.close()
            return

    else:
        print("✗ 無效的選項")
        mongo_helper.close()
        return

    # 確認是否繼續
    confirm = input("\n確定要開始爬取嗎? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消爬取")
        mongo_helper.close()
        return

    # 設定爬取時間範圍
    start_year, start_month = 101, 1  # 根據用戶修改
    end_year, end_month = 114, 11

    year_month_list = generate_year_month_list(start_year, start_month, end_year, end_month)

    print(f"\n爬取時間範圍: 民國 {start_year} 年 {start_month} 月 到 {end_year} 年 {end_month} 月")
    print(f"總共 {len(year_month_list)} 個月份")
    main_logger.info(f"爬取時間範圍: {start_year}/{start_month} - {end_year}/{end_month}，共 {len(year_month_list)} 個月份")

    # 設定並行進程數
    num_processes = 4
    print(f"\n使用 {num_processes} 個並行進程")
    main_logger.info(f"使用 {num_processes} 個並行進程")

    # 關閉主進程的 MongoDB 連接
    mongo_helper.close()

    # 創建任務隊列和結果隊列
    manager = Manager()
    task_queue = manager.Queue()
    result_queue = manager.Queue()
    stop_event = manager.Event()

    # 將所有任務放入隊列
    total_tasks = 0
    for year, month in year_month_list:
        for company_code in all_codes:
            task_queue.put((company_code, year, month))
            total_tasks += 1

    print(f"\n總任務數: {total_tasks}")
    main_logger.info(f"總任務數: {total_tasks}")

    # 添加結束信號
    for _ in range(num_processes):
        task_queue.put(None)

    # 啟動工作進程
    processes = []
    for i in range(num_processes):
        p = Process(target=worker_process, args=(i+1, task_queue, result_queue, year_month_list, stop_event))
        p.start()
        processes.append(p)
        print(f"進程 {i+1} 已啟動")

    # 監控進度
    completed_tasks = 0
    success_count = 0
    fail_count = 0

    start_time = time.time()

    try:
        while completed_tasks < total_tasks:
            try:
                result = result_queue.get(timeout=1)
                status, company_code, year, month = result

                completed_tasks += 1
                if status == 'success':
                    success_count += 1
                else:
                    fail_count += 1

                # 每 10 筆顯示一次進度
                if completed_tasks % 10 == 0 or completed_tasks == total_tasks:
                    elapsed = time.time() - start_time
                    progress = (completed_tasks / total_tasks) * 100
                    print(f"\r進度: {completed_tasks}/{total_tasks} ({progress:.1f}%) | 成功: {success_count} | 失敗: {fail_count} | 耗時: {elapsed:.0f}秒", end='')

            except:
                # 檢查所有進程是否還活著
                all_dead = all(not p.is_alive() for p in processes)
                if all_dead:
                    break

        print("\n")  # 換行

        # 等待所有進程結束
        for p in processes:
            p.join(timeout=5)

        # 顯示最終統計
        elapsed_time = time.time() - start_time
        print("\n" + "="*80)
        print("爬取完成")
        print("="*80)
        print(f"總任務數: {total_tasks}")
        print(f"成功: {success_count}")
        print(f"失敗: {fail_count}")
        print(f"總耗時: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分鐘)")
        print(f"平均速度: {total_tasks/elapsed_time:.2f} 筆/秒")
        print("="*80)

        main_logger.info("="*60)
        main_logger.info("爬取完成")
        main_logger.info(f"總任務數: {total_tasks}，成功: {success_count}，失敗: {fail_count}")
        main_logger.info(f"總耗時: {elapsed_time:.2f} 秒")
        main_logger.info("="*60)

    except KeyboardInterrupt:
        print("\n\n使用者中斷程式")
        main_logger.info("使用者中斷程式")
        stop_event.set()

        # 終止所有進程
        for p in processes:
            p.terminate()
            p.join(timeout=2)

    print("\n程式結束")


if __name__ == "__main__":
    main()
