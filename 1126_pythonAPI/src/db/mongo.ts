import { MongoClient, Db, Collection } from "mongodb";
import { env } from "../config/env";

let client: MongoClient | null = null;
let dbInstance: Db | null = null;

export async function getDb(): Promise<Db> {
  if (dbInstance) return dbInstance;

  client = new MongoClient(env.mongoUri);
  await client.connect();
  dbInstance = client.db(env.mongoDbName);
  return dbInstance;
}

export async function getCollection<T = unknown>(name: string): Promise<Collection<T>> {
  const db = await getDb();
  return db.collection<T>(name);
}

export async function closeDb(): Promise<void> {
  if (client) {
    await client.close();
    client = null;
    dbInstance = null;
  }
}
