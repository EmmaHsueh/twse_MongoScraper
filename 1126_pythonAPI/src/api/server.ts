import express, { Request, Response, NextFunction } from "express";
import { z } from "zod";
import { env } from "../config/env";
import { getCollection, closeDb } from "../db/mongo";
import { StockPrice, MopsChineseRecord } from "../types/mops";

const app = express();
app.use(express.json());

// Simple CORS allow-all
app.use((req: Request, res: Response, next: NextFunction) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
  next();
});

// Revenue query (中文欄位版) - 適配 revenue_crawler.py 的資料格式
app.get("/api/revenue", async (req: Request, res: Response) => {
  const stockId = (req.query.stock_id as string) || "";
  if (!stockId) {
    return res.status(400).json({
      Status: { Code: 400, Message: "Missing stock_id parameter" },
      Result: [],
    });
  }

  try {
    const col = await getCollection<any>(env.revenueCollection);
    const result = await col
      .find({ 公司代號: stockId }, { projection: { _id: 0 } })
      .sort({ 資料年月: -1 })
      .toArray();

    return res.json({ Result: result, Status: { Code: 0, Message: "Success" } });
  } catch (err) {
    console.error("Query revenue failed", err);
    return res.status(500).json({
      Status: { Code: 500, Message: "Internal Server Error" },
      Result: [],
    });
  }
});

const querySchema = z.object({
  stock_id: z.string().min(1, "stock_id is required"),
  start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "start must be YYYY-MM-DD").optional(),
  end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "end must be YYYY-MM-DD").optional(),
});

// Stock price query
app.get("/api/stock-price", async (req: Request, res: Response) => {
  const parsed = querySchema.safeParse(req.query);
  if (!parsed.success) {
    return res.status(400).json({
      Result: [],
      Status: { Code: 400, Message: parsed.error.errors.map((e) => e.message).join("; ") },
    });
  }

  const { stock_id, start, end } = parsed.data;

  if (start && end && start > end) {
    return res.status(400).json({
      Result: [],
      Status: { Code: 400, Message: "start date must be <= end date" },
    });
  }

  try {
    const col = await getCollection<StockPrice>(env.stockPriceCollection);
    const match: Record<string, unknown> = { stock_id };
    if (start && end) {
      match.date = { $gte: start, $lte: end };
    }

    // aggregate to allow field renaming to Chinese labels
    const result = await col
      .aggregate([
        { $match: match },
        { $sort: { date: 1 } },
        {
          $project: {
            _id: 0,
            stock_id: 1,
            date: 1,
            開盤: "$open",
            最高: "$high",
            最低: "$low",
            收盤: "$close",
            成交量: "$volume",
          },
        },
      ])
      .toArray();

    return res.json({
      Result: result,
      Status: { Code: 0, Message: "Success" },
    });
  } catch (err) {
    console.error("Query stock price failed", err);
    return res.status(500).json({
      Result: [],
      Status: { Code: 500, Message: "Internal Server Error" },
    });
  }
});

app.get("/health", (_req, res) => res.json({ ok: true }));

const server = app.listen(env.port, () => {
  console.log(`API Server listening on http://localhost:${env.port}`);
  console.log(`Database: ${env.mongoDbName}, Collection: ${env.revenueCollection}`);
});

const shutdown = async () => {
  await closeDb();
  server.close(() => process.exit(0));
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
