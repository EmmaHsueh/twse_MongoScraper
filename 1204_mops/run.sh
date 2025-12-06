#!/bin/bash
# MOPS 資產負債表爬蟲執行腳本

echo "======================================"
echo "  MOPS 資產負債表爬蟲系統"
echo "======================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 找不到 Python3，請先安裝 Python"
    exit 1
fi

echo "[1/6] 檢查 Python 版本..."
python3 --version

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo ""
    echo "[2/6] 建立虛擬環境..."
    python3 -m venv venv
    echo "✓ 虛擬環境建立完成"
else
    echo ""
    echo "[2/6] ✓ 虛擬環境已存在"
fi

# 啟動虛擬環境
echo ""
echo "[3/6] 啟動虛擬環境..."
source venv/bin/activate
echo "✓ 已進入虛擬環境: $(which python3)"

# 安裝依賴
echo ""
echo "[4/6] 檢查並安裝依賴套件..."
pip install -q -r requirements.txt
echo "✓ 套件安裝完成"

# 檢查 .env
echo ""
echo "[5/6] 檢查設定檔..."
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 檔案不存在，複製範例檔案..."
    cp .env.example .env
    echo "📝 請編輯 .env 檔案設定 MongoDB 連接資訊"
    echo "   然後重新執行此腳本"
    exit 1
else
    echo "✓ .env 檔案存在"
fi

# 執行程式
echo ""
echo "[6/6] 🚀 啟動爬蟲..."
echo "======================================"
echo ""
python3 main.py

echo ""
echo "======================================"
echo "  ✅ 爬蟲執行完成"
echo "======================================"
