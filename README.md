# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 17451,
 "stats": {
  "ok": 11539,
  "timeout": 1180,
  "variant-fail": 488,
  "dead": 4217,
  "skip": 27
 },
 "dead_details": {
  "connect/transfer-timeout": 1180,
  "http-404": 1089,
  "http-403": 1017,
  "dns-fail": 447,
  "http-429": 385,
  "unrecognized-body": 306,
  "html/xml-body": 292,
  "conn-refused": 248,
  "variant-http-429": 188,
  "variant-http-404": 108,
  "variant-http-000": 105,
  "tls-fail": 100,
  "http-400": 57,
  "variant-http-200": 54,
  "http-500": 52
 }
}```

更新时间：2026-10-05 11:30 UTC
