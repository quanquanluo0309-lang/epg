# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 17840,
 "stats": {
  "ok": 11989,
  "dead": 4195,
  "variant-fail": 472,
  "timeout": 1157,
  "skip": 27
 },
 "dead_details": {
  "connect/transfer-timeout": 1157,
  "http-404": 1093,
  "http-403": 936,
  "dns-fail": 463,
  "http-429": 439,
  "unrecognized-body": 298,
  "conn-refused": 266,
  "html/xml-body": 257,
  "variant-http-429": 189,
  "tls-fail": 112,
  "variant-http-000": 101,
  "variant-http-404": 100,
  "http-400": 62,
  "http-500": 62,
  "variant-http-200": 56
 }
}```

更新时间：2026-10-19 09:55 UTC
