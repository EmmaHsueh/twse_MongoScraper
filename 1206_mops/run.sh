#!/bin/bash

# MOPS 爬蟲啟動腳本
# 自動啟動虛擬環境並執行程式

echo "啟動 MOPS 爬蟲..."
echo "===================="

# 啟動虛擬環境
source venv/bin/activate

# 執行爬蟲程式
python mops_scraper.py

# 結束後保持虛擬環境啟動狀態
echo ""
echo "程式執行完畢"
echo "虛擬環境仍在啟動中，輸入 'deactivate' 可退出"
