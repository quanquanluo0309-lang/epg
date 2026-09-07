# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 18673,
 "stats": {
  "ok": 12480,
  "dead": 4384,
  "variant-fail": 516,
  "timeout": 1268,
  "skip": 25
 },
 "dead_details": {
  "connect/transfer-timeout": 1268,
  "http-403": 1048,
  "http-404": 1014,
  "http-429": 531,
  "dns-fail": 463,
  "html/xml-body": 301,
  "unrecognized-body": 276,
  "conn-refused": 215,
  "variant-http-429": 214,
  "variant-http-404": 137,
  "variant-http-000": 103,
  "tls-fail": 89,
  "http-502": 71,
  "http-500": 67,
  "http-400": 65
 }
}```

更新时间：2026-09-07 09:19 UTC
