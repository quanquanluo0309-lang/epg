# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 17241,
 "stats": {
  "ok": 11428,
  "timeout": 1136,
  "variant-fail": 491,
  "dead": 4159,
  "skip": 27
 },
 "dead_details": {
  "connect/transfer-timeout": 1136,
  "http-403": 1010,
  "http-404": 987,
  "dns-fail": 423,
  "http-429": 403,
  "unrecognized-body": 343,
  "html/xml-body": 297,
  "conn-refused": 248,
  "variant-http-429": 178,
  "variant-http-404": 115,
  "tls-fail": 100,
  "variant-http-000": 99,
  "http-400": 53,
  "http-500": 51,
  "variant-http-200": 47
 }
}```

更新时间：2026-09-28 10:55 UTC
