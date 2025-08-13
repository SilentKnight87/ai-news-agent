export interface CacheConfig {
  searchArticles: { ttl: 300 };      // 5 minutes
  latestArticles: { ttl: 600 };      // 10 minutes  
  articleStats: { ttl: 3600 };       // 1 hour
  digests: { ttl: 3600 };            // 1 hour
  sources: { ttl: 86400 };           // 24 hours
}

export class CacheManager {
  constructor(private kv: KVNamespace) {}
  
  generateKey(operation: string, params: any): string {
    return `${operation}:${JSON.stringify(params)}`;
  }
  
  async get<T>(key: string): Promise<T | null> {
    const value = await this.kv.get(key, "json");
    return value as T;
  }
  
  async set(key: string, value: any, ttlSeconds: number): Promise<void> {
    await this.kv.put(key, JSON.stringify(value), {
      expirationTtl: ttlSeconds
    });
  }
  
  async invalidatePattern(pattern: string): Promise<void> {
    // List all keys matching pattern and delete
    const list = await this.kv.list({ prefix: pattern });
    for (const key of list.keys) {
      await this.kv.delete(key.name);
    }
  }
}

// Cache configuration constants
export const CACHE_CONFIG: CacheConfig = {
  searchArticles: { ttl: 300 },      // 5 minutes
  latestArticles: { ttl: 600 },      // 10 minutes  
  articleStats: { ttl: 3600 },       // 1 hour
  digests: { ttl: 3600 },            // 1 hour
  sources: { ttl: 86400 },           // 24 hours
};