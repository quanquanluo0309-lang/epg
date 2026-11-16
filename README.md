# 实测可播播放列表

每周一北京时间 12:00 自动刷新：聚合 12 个上游源（全球/FAST/国内/港/台）→ URL 去重 → 逐条实测可播性 → 跨源频道合并与影响力排序 → 生成下列两份列表。

- 推荐精选(curated.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/curated.m3u`
- 全量可播(full.m3u)：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/lists/full.m3u`

最近一次探测结果：
```json
{
 "total": 18098,
 "stats": {
  "ok": 12126,
  "dead": 4361,
  "variant-fail": 488,
  "timeout": 1090,
  "skip": 33
 },
 "dead_details": {
  "connect/transfer-timeout": 1090,
  "http-404": 1088,
  "http-403": 894,
  "http-429": 549,
  "dns-fail": 483,
  "conn-refused": 389,
  "html/xml-body": 281,
  "unrecognized-body": 246,
  "variant-http-429": 231,
  "variant-http-404": 98,
  "variant-http-000": 93,
  "tls-fail": 87,
  "http-400": 61,
  "http-500": 57,
  "http-502": 48
 }
}```

更新时间：2026-11-16 12:44 UTC
