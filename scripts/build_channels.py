#!/usr/bin/env python3
"""每周由最新探测结果重建 EPG 定向抓取清单：可播 ∩ 有 grabber 的频道 → channels/channels_part{1..4}.xml。
需要当前目录存在 probe_results.jsonl 和 grabber/（iptv-org/epg 浅克隆）。"""
import json, re, glob, collections
from xml.sax.saxutils import escape, quoteattr

idx = collections.defaultdict(list)
pat = re.compile(r"<channel\s+([^>]*?)>([^<]*)</channel>")
attr = re.compile(r'([a-zA-Z_]+)="([^"]*)"')
for f in glob.glob("grabber/sites/*/*.channels.xml"):
    try:
        text = open(f, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    for m in pat.finditer(text):
        a = dict(attr.findall(m.group(1)))
        if a.get("xmltv_id"):
            idx[a["xmltv_id"]].append({"site": a.get("site", ""), "site_id": a.get("site_id", ""),
                                       "lang": a.get("lang", ""), "name": m.group(2)})
base_map = collections.defaultdict(list)
for xid in idx:
    base_map[xid.split("@")[0]].append(xid)

ok_ids = set()
for l in open("probe_results.jsonl"):
    r = json.loads(l)
    if r["status"] == "ok" and r.get("tvg_id"):
        ok_ids.add(r["tvg_id"])

LANG_PREF = {"zh": 0, "en": 1}
rows = []
for pid in sorted(ok_ids):
    if pid in idx:
        cands = idx[pid]
    elif pid.split("@")[0] in base_map:
        cands = [c for x in base_map[pid.split("@")[0]] for c in idx[x]]
    else:
        continue
    e = sorted(cands, key=lambda c: (LANG_PREF.get(c["lang"], 2), c["site"]))[0]
    rows.append(f'  <channel site={quoteattr(e["site"])} lang={quoteattr(e["lang"] or "en")} '
                f'xmltv_id={quoteattr(pid)} site_id={quoteattr(e["site_id"])}>{escape(e["name"])}</channel>')

N = 4
size = (len(rows) + N - 1) // N
for i in range(N):
    part = rows[i * size:(i + 1) * size]
    with open(f"channels/channels_part{i + 1}.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n' + "\n".join(part) + "\n</channels>\n")
print(f"EPG 目标重建: {len(rows)} 频道 -> 4 parts")
