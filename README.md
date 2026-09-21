# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 17171,
 "stats": {
  "ok": 11543,
  "timeout": 1152,
  "variant-fail": 493,
  "dead": 3956,
  "skip": 27
 },
 "dead_details": {
  "connect/transfer-timeout": 1152,
  "http-404": 970,
  "http-403": 930,
  "dns-fail": 426,
  "http-429": 383,
  "html/xml-body": 295,
  "unrecognized-body": 273,
  "conn-refused": 223,
  "variant-http-429": 189,
  "variant-http-404": 111,
  "variant-http-000": 99,
  "http-502": 78,
  "tls-fail": 75,
  "http-400": 54,
  "http-503": 52
 }
}```

更新时间：2026-09-21 09:59 UTC
