# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 17709,
 "stats": {
  "dead": 6685,
  "timeout": 1189,
  "ok": 9351,
  "variant-fail": 457,
  "skip": 27
 },
 "dead_details": {
  "http-403": 3021,
  "http-404": 1311,
  "connect/transfer-timeout": 1189,
  "http-429": 489,
  "dns-fail": 445,
  "unrecognized-body": 312,
  "conn-refused": 273,
  "html/xml-body": 264,
  "variant-http-429": 186,
  "http-503": 175,
  "tls-fail": 101,
  "variant-http-404": 99,
  "variant-http-000": 82,
  "variant-http-200": 61,
  "http-500": 52
 }
}```

更新时间：2026-10-12 11:58 UTC
