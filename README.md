# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 17994,
 "stats": {
  "ok": 11911,
  "dead": 4381,
  "variant-fail": 447,
  "timeout": 1224,
  "skip": 31
 },
 "dead_details": {
  "http-403": 1228,
  "connect/transfer-timeout": 1224,
  "http-404": 1058,
  "http-429": 468,
  "dns-fail": 461,
  "html/xml-body": 260,
  "conn-refused": 249,
  "unrecognized-body": 212,
  "variant-http-429": 186,
  "tls-fail": 118,
  "variant-http-404": 99,
  "variant-http-000": 99,
  "http-400": 66,
  "http-500": 62,
  "http-502": 35
 }
}```

更新时间：2026-11-23 14:24 UTC
