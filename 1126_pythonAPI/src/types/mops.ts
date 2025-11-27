export type MarketType = "sii" | "otc" | "rotc";

export interface MonthlyRevenueRecord {
  stockId: string;
  companyName: string;
  year: number; // Gregorian year
  month: number; // 1-12
  market: MarketType;
  revenue: number; // 營業收入
  revenueLastYear: number; // 去年同月
  revenueChangePercent: number; // 年增率或增減百分比
  cumulativeRevenue: number; // 本年累計
  cumulativeRevenueLastYear: number; // 去年累計
  cumulativeChangePercent: number; // 累計年增率
  raw?: Record<string, unknown>;
  createdAt: Date;
}

export interface StockPrice {
  stock_id: string;
  date: string; // YYYY-MM-DD
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
}

// 中文欄位對應版本（每月營收）
export interface MopsChineseRecord {
  stockId: string;
  year: number;
  month: number;
  market: MarketType;
  公司代號: string;
  公司名稱: string;
  營業收入: number;
  去年同月營收: number;
  營收年增率百分比: number;
  本年累計營收: number;
  去年累計營收: number;
  累計年增率百分比: number;
  createdAt: Date;
  raw?: Record<string, unknown>;
}
