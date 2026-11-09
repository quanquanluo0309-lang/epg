# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 17980,
 "stats": {
  "ok": 11834,
  "timeout": 1207,
  "dead": 4435,
  "variant-fail": 472,
  "skip": 32
 },
 "dead_details": {
  "connect/transfer-timeout": 1207,
  "http-404": 1082,
  "http-403": 946,
  "dns-fail": 672,
  "http-429": 552,
  "conn-refused": 281,
  "html/xml-body": 264,
  "unrecognized-body": 255,
  "variant-http-429": 189,
  "variant-http-000": 103,
  "variant-http-404": 97,
  "tls-fail": 89,
  "http-400": 63,
  "http-500": 53,
  "variant-http-200": 49
 }
}```

更新时间：2026-11-09 12:51 UTC
