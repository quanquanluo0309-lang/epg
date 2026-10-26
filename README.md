# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 17870,
 "stats": {
  "ok": 11800,
  "dead": 4287,
  "variant-fail": 483,
  "timeout": 1273,
  "skip": 27
 },
 "dead_details": {
  "connect/transfer-timeout": 1273,
  "http-404": 1058,
  "http-403": 979,
  "dns-fail": 489,
  "http-429": 457,
  "unrecognized-body": 311,
  "html/xml-body": 267,
  "conn-refused": 245,
  "variant-http-429": 202,
  "tls-fail": 154,
  "variant-http-000": 103,
  "variant-http-404": 102,
  "http-400": 67,
  "http-500": 63,
  "variant-http-200": 44
 }
}```

更新时间：2026-10-26 10:07 UTC
