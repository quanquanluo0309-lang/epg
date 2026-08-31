# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 18284,
 "stats": {
  "ok": 12169,
  "dead": 4255,
  "variant-fail": 496,
  "timeout": 1339,
  "skip": 25
 },
 "dead_details": {
  "connect/transfer-timeout": 1339,
  "http-403": 993,
  "http-404": 913,
  "http-429": 531,
  "dns-fail": 472,
  "html/xml-body": 321,
  "unrecognized-body": 300,
  "conn-refused": 232,
  "variant-http-429": 189,
  "variant-http-404": 137,
  "variant-http-000": 99,
  "tls-fail": 82,
  "http-400": 75,
  "http-502": 53,
  "http-500": 53
 }
}```

更新时间：2026-08-31 10:54 UTC
