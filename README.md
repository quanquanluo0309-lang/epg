# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 18081,
 "stats": {
  "ok": 11995,
  "timeout": 1193,
  "dead": 4386,
  "variant-fail": 475,
  "skip": 32
 },
 "dead_details": {
  "connect/transfer-timeout": 1193,
  "http-403": 1044,
  "http-404": 1037,
  "http-429": 527,
  "dns-fail": 486,
  "unrecognized-body": 342,
  "html/xml-body": 268,
  "conn-refused": 261,
  "variant-http-429": 191,
  "tls-fail": 104,
  "variant-http-000": 102,
  "variant-http-404": 98,
  "http-400": 63,
  "http-500": 53,
  "variant-http-200": 43
 }
}```

更新时间：2026-11-02 12:19 UTC
