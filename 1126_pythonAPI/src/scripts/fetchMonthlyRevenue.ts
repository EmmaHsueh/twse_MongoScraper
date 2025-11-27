import { closeDb } from "../db/mongo";
import { fetchAndSaveMonthlyRevenue, describeMarket } from "../crawler/mopsRevenueCrawler";
import { MarketType } from "../types/mops";

interface Args {
  year: number;
  month: number;
  markets: MarketType[];
}

function parseArgs(): Args {
  const now = new Date();
  now.setMonth(now.getMonth() - 1); // default: previous month data is most stable

  let year = now.getFullYear();
  let month = now.getMonth() + 1; // JS month is zero-based
  let markets: MarketType[] = ["sii", "otc", "rotc"];

  process.argv.slice(2).forEach((arg) => {
    const [key, value] = arg.split("=");
    if (key === "--year" && value) year = Number(value);
    if (key === "--month" && value) month = Number(value);
    if (key === "--markets" && value) {
      markets = value.split(",").map((v) => v.trim()) as MarketType[];
    }
  });

  return { year, month, markets };
}

async function main() {
  const { year, month, markets } = parseArgs();
  console.log(`Fetching monthly revenue for ${year}-${String(month).padStart(2, "0")} markets: ${markets.join(", ")}`);

  try {
    const result = await fetchAndSaveMonthlyRevenue(year, month, markets);
    console.log("Saved records:", result.total);
    console.log(
      "Per market:",
      Object.entries(result.perMarket)
        .map(([k, v]) => `${describeMarket(k as MarketType)}:${v}`)
        .join(", ")
    );

    if (result.missing.length) {
      console.warn(`Companies missing revenue data (${result.missing.length}):`, result.missing.join(", "));
    } else {
      console.log("All companies in 公司基本資料 have revenue data for this month.");
    }
  } catch (err) {
    console.error("Crawler failed", err);
    process.exitCode = 1;
  } finally {
    await closeDb();
  }
}

main();
