import { config } from "dotenv";

// Load .env file
config();

export interface EnvConfig {
  mongoUri: string;
  mongoDbName: string;
  revenueCollection: string;
  basicInfoCollection: string;
  stockPriceCollection: string;
  port: number;
}

const defaultMongoUri = process.env.MONGO_URI || "mongodb://localhost:27017";
const defaultDbName = process.env.MONGO_DB_NAME || "mops";

export const env: EnvConfig = {
  mongoUri: defaultMongoUri,
  mongoDbName: defaultDbName,
  revenueCollection: process.env.MONGO_REVENUE_COLLECTION || "每月營收",
  basicInfoCollection: process.env.MONGO_BASIC_COLLECTION || "公司基本資料",
  stockPriceCollection: process.env.MONGO_STOCK_PRICE_COLLECTION || "歷史股價",
  port: Number(process.env.PORT || 4000),
};
