# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a hybrid Next.js/Express application for crawling and querying Taiwan stock market data from MOPS (Market Observation Post System). The project includes:
- Monthly revenue crawler (TypeScript and Python versions)
- Express API for historical stock price and revenue queries
- Next.js frontend (currently boilerplate)
- MongoDB storage for stock data

## Development Commands

### Install Dependencies
```bash
npm install
```

### Next.js Development
```bash
npm run dev      # Start Next.js dev server on port 3000
npm run build    # Build Next.js production bundle
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Backend Scripts

#### Monthly Revenue Crawler (TypeScript)
```bash
# Default: fetch previous month for all markets (上市/上櫃/興櫃)
npm run crawler:revenue

# Custom year/month/markets
npm run crawler:revenue -- --year=2024 --month=11 --markets=sii,otc,rotc
```

**Note**: The TypeScript crawler imports from `src/crawler/mopsRevenueCrawler.ts` which is currently **missing**. The script will fail until this file is created.

#### Monthly Revenue Crawler (Python)
```bash
# Install Python dependencies first
pip install requests beautifulsoup4 pymongo

# Default: fetch previous month for all markets
python python/fetch_monthly_revenue.py

# Custom parameters
python python/fetch_monthly_revenue.py --year 2024 --month 11 --markets sii,otc,rotc --mongo-uri "mongodb://localhost:27017" --mongo-db TW_Stock
```

#### API Server
```bash
npm run api      # Start Express server (default port 4000)
```

API endpoints:
- `GET /api/revenue?stock_id=2330` - Query monthly revenue data (中文欄位)
- `GET /api/stock-price?stock_id=2330&start=2024-01-01&end=2024-02-01` - Query historical stock prices
- `GET /health` - Health check

## Architecture

### Database Schema (MongoDB)

**Database Name**:
- TypeScript: `mops` (default)
- Python: `TW_Stock` (default)

**Collections**:
1. `每月營收` - Monthly revenue records
   - Unique key: `{stockId, year, month, market}`
   - Fields use Chinese labels: `公司代號`, `公司名稱`, `營業收入`, `去年同月營收`, `營收年增率(%)`, `本年累計營收`, `去年累計營收`, `累計年增率(%)`

2. `公司基本資料` - Company basic info
   - Used to validate which companies have revenue data
   - Field: `stock_id`

3. `歷史股價` - Historical stock prices
   - Fields: `stock_id`, `date`, `open`, `high`, `low`, `close`, `volume`

### Market Types
- `sii` - 上市 (Listed)
- `otc` - 上櫃 (OTC)
- `rotc` - 興櫃 (Emerging)

### Configuration (src/config/env.ts)

Environment variables:
- `MONGO_URI` - MongoDB connection string (default: `mongodb://localhost:27017`)
- `MONGO_DB_NAME` - Database name (default: `mops`)
- `MONGO_REVENUE_COLLECTION` - Revenue collection (default: `每月營收`)
- `MONGO_BASIC_COLLECTION` - Company collection (default: `公司基本資料`)
- `MONGO_STOCK_PRICE_COLLECTION` - Stock price collection (default: `歷史股價`)
- `PORT` - API server port (default: `4000`)

### Core Modules

#### Database Layer
- `src/db/mongo.ts` - MongoDB connection singleton
  - `getDb()` - Get database instance
  - `getCollection<T>(name)` - Get typed collection
  - `closeDb()` - Close connection

#### Types
- `src/types/mops.ts` - TypeScript interfaces
  - `MarketType` - Market enum
  - `MonthlyRevenueRecord` - Revenue data structure (English fields)
  - `MopsChineseRecord` - Revenue data with Chinese field names (used in DB)
  - `StockPrice` - Stock price structure

#### Crawler Workflow (Both TS and Python versions)
1. Build POST request to `https://mops.twse.com.tw/mops/web/ajax_t21sc04_ifrs`
   - Convert Gregorian year to Minguo (ROC) calendar: `year - 1911`
   - Parameters: `TYPEK` (market), `year` (Minguo), `month`

2. Parse HTML table using cheerio (TS) or BeautifulSoup (Python)
   - Headers resolved by keyword matching (e.g., "公司代號", "營業收入", "年增率")
   - Extract numeric values (remove commas)

3. Upsert to MongoDB `每月營收` collection
   - Unique constraint: `{stockId, year, month, market}`
   - Store with Chinese field names for API compatibility

4. Validate against `公司基本資料` collection
   - Report missing companies (in basic info but no revenue data)

#### API Server (src/api/server.ts)
- Express server with CORS enabled
- Zod validation for query parameters
- Returns standardized format: `{Result: [...], Status: {Code, Message}}`
- Aggregation pipeline for stock prices to rename fields to Chinese labels

### Known Issues

1. **Missing Crawler Implementation**: `src/scripts/fetchMonthlyRevenue.ts` imports from `src/crawler/mopsRevenueCrawler.ts` which doesn't exist. This file needs to be created with:
   - `fetchAndSaveMonthlyRevenue(year, month, markets)` function
   - `describeMarket(market)` function
   - Implementation similar to `python/fetch_monthly_revenue.py`

2. **Date Format Conversion**: MOPS uses Minguo calendar (year - 1911). Always convert before making requests.

3. **Table Header Parsing**: Crawler relies on keyword matching in Chinese headers. If MOPS changes table structure, update keyword arrays in parser logic.

4. **Empty Collections**: If `公司基本資料` is empty, missing company validation is skipped. Populate company list before running comparisons.

## Frontend Structure

- `app/page.tsx` - Next.js App Router homepage (currently default template)
- `app/layout.tsx` - Root layout
- `app/globals.css` - Tailwind CSS styles
- Tailwind v4 with @tailwindcss/postcss

Frontend is mostly boilerplate - actual functionality is in backend scripts and API.
