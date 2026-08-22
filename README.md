# Personal EPG builder

每日自动抓取 3,254 个实测可播频道的电视节目单（XMLTV），频道 ID 与 iptv-org 播放列表完全一致。

- 订阅地址（每日 06:00 北京时间更新）：`https://raw.githubusercontent.com/quanquanluo0309-lang/epg/output/guide.xml.gz`
- 数据来源：[iptv-org/epg](https://github.com/iptv-org/epg) 官方 grabber，按自选频道清单（channels/）定向抓取
- 手动触发：Actions → build-epg → Run workflow
