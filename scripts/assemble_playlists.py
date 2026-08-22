#!/usr/bin/env python3
"""总装两级播放列表（v2 排序版）。

curated（推荐精选）：
  - 入选：华语频道 / 知名品牌频道
  - 组间：华语→新闻→影视→体育→纪录→少儿→音乐→综合
  - 组内：频道按 知名度/影响力（FAME 分级表）降序，再按最佳源质量
  - 同一频道多个源相邻放置（播放器合并为多线路），源按 分辨率+连接速度+稳定性 降序，最多保留 4 条
full（全量可播）：
  - 按国家分组；组内同样按频道知名度与源质量排序，同频道源相邻
输入：PLAYLIST_FILE（原始 m3u）+ probe_results.jsonl（探测结果，含 status/ms/retried）
"""
import json, re, collections, os

SRC = os.environ.get("PLAYLIST_FILE", "index.m3u")
PROBE = "probe_results.jsonl"
OUT_PICK = "推荐精选·实测可播.m3u"
OUT_ALL = "全量可播·按国家.m3u"
HEADER = ('#EXTM3U x-tvg-url="'
          'https://raw.githubusercontent.com/quanquanluo0309-lang/epg/output/guide.xml.gz,'
          'https://live.fanmingming.cn/e.xml"\n')

# ---------------- 知名度/影响力分级表（分数越高越靠前） ----------------
# regex: 正则片段；names: 字面子串（自动转义）。首个命中的 tier 生效。
FAME_TIERS = [
    # T1 全球一线新闻 / 华语一线
    (1000,
     ["CCTV-?1\\b", "CCTV-?13", "Phoenix (Chinese|InfoNews|TV)", "France ?24", "Aljazeera"],
     ["BBC News", "BBC World", "CNN", "Al Jazeera", "Sky News", "Deutsche Welle", "DW News", "Euronews",
      "NHK World", "CGTN", "Bloomberg", "Reuters", "TRT World", "CNBC",
      "凤凰卫视", "TVB", "翡翠台", "Jade", "明珠台", "Pearl", "CCTV新闻"]),
    # T2 重要新闻/财经/国家级/华语二线
    (900,
     ["CCTV-?[24]\\b", "i24", "RT News"],
     ["Fox News", "MSNBC", "ABC News", "CBS News", "NBC News", "CTV News", "CBC News", "Al Arabiya",
      "Sky News Arabia", "Channel NewsAsia", "CNA", "Arirang", "YTN", "WION", "India Today", "NDTV",
      "Times Now", "Republic TV", "News18", "Zee News", "ARY News", "Geo News", "GB News", "Africanews",
      "TV5 Monde", "BFM TV", "LCI", "ANC", "GMA News",
      "中天新闻", "东森新闻", "TVBS", "RTHK", "公视", "PTS", "民视", "台视", "中视", "华视",
      "东方卫视", "湖南卫视", "浙江卫视", "江苏卫视", "北京卫视", "广东卫视", "深圳卫视", "ViuTV", "香港开电视", "澳亚卫视"]),
    # 各国旗舰综合台 / 其余卫视
    (800,
     [r"\bARD\b", r"\bZDF\b", "La 1\\b", r"\bITV\b", r"\bNHK\b", r"\bKBS\b", r"\bMBC\b", r"\bSBS\b",
      r"\bRTL\b", "Canal\\+", "SAT\\.1", "CCTV", "卫视"],
     ["Das Erste", "TF1", "France 2", "Rai 1", "Rai 2", "RTVE", "BBC One", "BBC Two", "Channel 4",
      "Globo", "Televisa", "Antena 3", "Telecinco", "ProSieben", "América TV", "Caracol", "TV Azteca",
      "Doordarshan", "DD National", "Rede Record", "SBT", "RTP1", "SIC", "TV2 Norway", "SVT1", "DR1",
      "YLE", "ORF", "SRF", "RTS Un", "Seven Network", "Nine Network"]),
    # 知名垂类品牌（影视/体育/纪录/少儿/音乐）
    (700,
     [r"\bAMC\b", r"\bFX\b", r"\bMTV\b", "Sony (TV|Entertainment|Movies)", "Star (Plus|Movies|Sports)",
      "Nat ?Geo", r"\bTNT\b", r"\bTLC\b", r"\bE!\b", r"\bVH1\b"],
     ["HBO", "Cinemax", "Showtime", "Starz", "Paramount", "Universal", "Warner", "USA Network", "Syfy",
      "Bravo", "Comedy Central", "AXN", "TCM", "Movistar",
      "ESPN", "Sky Sports", "Fox Sports", "beIN", "Eurosport", "NBC Sports", "TNT Sports", "DAZN",
      "Star Sports", "TSN", "Sportsnet", "Setanta", "SuperSport", "Red Bull TV",
      "National Geographic", "Discovery", "Animal Planet", "History", "BBC Earth", "Smithsonian",
      "Curiosity", "Travel Channel", "DMAX",
      "Disney", "Cartoon Network", "Nickelodeon", "Nick Jr", "Boomerang", "PBS Kids", "CBeebies",
      "Baby TV", "Toonami", "Trace", "CMT", "Fuse", "4Music", "Music Choice"]),
]
# 字面量加 ASCII 词边界，防止 "TVB" 误命中 "CCTVBilliards"/"TVBRICS" 这类无分隔字符串
def _lit(n):
    return r"(?<![A-Za-z0-9])" + re.escape(n) + r"(?![A-Za-z0-9])"
FAME_COMPILED = [(s, re.compile("|".join(rx + [_lit(n) for n in names]), re.I))
                 for s, rx, names in FAME_TIERS]

RES_RE = re.compile(r"\b(2160|1440|1080|720|576|480|360|240)p?\b")
CJK = re.compile(r"[一-鿿]")
NEWS = re.compile(r"BBC News|CNN|Al Jazeera|Aljazeera|\bDW\b|France ?24|Sky News|Bloomberg|CNBC|NHK World|Channel NewsAsia|\bCNA\b|TRT World|Euronews|ABC News|CBS News|NBC News|Fox News|CGTN|Arirang|i24|WION|Africanews|Deutsche Welle|TV5 ?Monde|Rai News|GB News|Times Now|India Today|NDTV|Al Arabiya|MSNBC|Reuters|凤凰|Phoenix", re.I)
SPORT = re.compile(r"ESPN|DAZN|beIN|Eurosport|Red Bull TV|Sky Sports|Sport|Racing|Fight|NBA|NFL|MLB|Tennis|Golf", re.I)
KIDS = re.compile(r"Nick|Cartoon|Disney|Boomerang|Baby|Kids|Duck TV|CBeebies|少儿|卡通", re.I)
MUSIC = re.compile(r"MTV|Vevo|Music|Hits|Clubbing|Stingray|NRJ|Trace ", re.I)
MOVIE = re.compile(r"HBO|AMC|Paramount|Cinema|Cine\b|Movies?|Film|Hollywood|Showtime|Cinemax|剧场|电影", re.I)
DOCU = re.compile(r"Discovery|Nat ?Geo|National Geographic|History|Animal Planet|Documentar|Arte|Smithsonian|Love Nature|纪实|纪录", re.I)
BRAND_EXTRA = re.compile(r"TVB|翡翠|RTHK|民视|公视|中天|TVBS|三立|東森|东森|华视|台视|CCTV|Comedy Central|Rakuten|Pluto|CBS|Univision|Telemundo|ZDF|ARD|TF1|Canal|BBC|ITV|Channel [45]\b|RTL|Antena", re.I)

STRIP_TITLE = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]\s*$")

def fame_of(text):
    for score, rx in FAME_COMPILED:
        if rx.search(text):
            return score
    return 0

def res_pts(title):
    m = RES_RE.search(title)
    if not m:
        return 22
    return {2160: 50, 1440: 42, 1080: 40, 720: 30, 576: 18, 480: 15, 360: 8, 240: 4}[int(m.group(1))]

def speed_pts(ms):
    if ms < 1200: return 25
    if ms < 2500: return 20
    if ms < 5000: return 12
    if ms < 8000: return 6
    return 2

def channel_key(tvg_id, title):
    base = tvg_id.split("@")[0]
    if base:
        return "id:" + base
    t = title
    while True:
        t2 = STRIP_TITLE.sub("", t)
        if t2 == t: break
        t = t2
    return "t:" + re.sub(r"\s+", " ", t).strip().lower()

def cc_of(tvg_id):
    base = tvg_id.split("@")[0]
    return base.rsplit(".", 1)[-1].lower() if "." in base else ""

def cat_of(title, group):
    g = group.split(";")[0]
    if NEWS.search(title) or g == "News": return "📰 新闻"
    if SPORT.search(title) or g == "Sports": return "⚽ 体育"
    if KIDS.search(title) or g == "Kids": return "🧒 少儿"
    if MOVIE.search(title) or g in ("Movies", "Series"): return "🎬 影视剧"
    if DOCU.search(title) or g in ("Documentary", "Science", "Education"): return "🌍 纪录知识"
    if MUSIC.search(title) or g == "Music": return "🎵 音乐"
    return "✨ 综合娱乐"

def set_group(extinf, group):
    if 'group-title="' in extinf:
        return re.sub(r'group-title="[^"]*"', 'group-title="%s"' % group, extinf, count=1)
    return extinf.replace("#EXTINF:-1", '#EXTINF:-1 group-title="%s"' % group, 1)

def canon_title(title):
    # 去掉 (1080p)/[Not 24/7] 等尾部标注——mytv-android 按「频道名完全相同」合并多线路，
    # 同频道各源必须统一显示名才能启用线路切换
    t = title
    while True:
        t2 = STRIP_TITLE.sub("", t)
        if t2 == t:
            break
        t = t2
    return re.sub(r"\s+", " ", t).strip() or title

def set_title(extinf, new_title):
    head, _, _ = extinf.rpartition(",")
    return head + "," + new_title

# ---------------- 解析 + 探测结果合并 ----------------
blocks = []
extinf = None; extra = []
for line in open(SRC, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n").rstrip("\r")
    if line.startswith("#EXTINF"):
        extinf = line; extra = []
    elif line.startswith("#") and extinf is not None and line.strip():
        extra.append(line)
    elif line.strip() and not line.startswith("#") and extinf is not None:
        blocks.append({"idx": len(blocks), "extinf": extinf, "extra": extra, "url": line.strip()})
        extinf = None; extra = []

probe = {}
for l in open(PROBE):
    r = json.loads(l); probe[r["idx"]] = r

ok = []
for b in blocks:
    r = probe.get(b["idx"])
    if not (r and r["status"] == "ok"):
        continue
    attrs = dict(re.findall(r'([a-zA-Z0-9-]+)="([^"]*)"', b["extinf"]))
    title = b["extinf"].rpartition(",")[2].strip()
    b["tvg_id"] = attrs.get("tvg-id", "")
    b["title"] = title
    b["cc"] = cc_of(b["tvg_id"])
    b["group0"] = attrs.get("group-title", "")
    b["key"] = channel_key(b["tvg_id"], title)
    b["fame"] = fame_of(title)  # 只对人类可读标题匹配；tvg-id 无分隔符易误命中
    b["q"] = res_pts(title) + speed_pts(r.get("ms", 9999)) - (6 if r.get("retried") else 0)
    ok.append(b)

# 按频道聚合；源按质量降序，最多 4 条
channels = collections.defaultdict(list)
for b in ok:
    channels[b["key"]].append(b)
for k in channels:
    channels[k].sort(key=lambda b: -b["q"])
    channels[k] = channels[k][:4]

def ch_fame(entries): return max(e["fame"] for e in entries)
def ch_best(entries): return entries[0]["q"]
def ch_name(entries): return min(e["title"] for e in entries)

# ---------------- curated ----------------
def is_zh(e): return e["cc"] in ("cn", "hk", "tw", "mo") or bool(CJK.search(e["title"]))
def selected(entries):
    e = entries[0]
    return is_zh(e) or ch_fame(entries) > 0 or BRAND_EXTRA.search(e["title"]) or NEWS.search(e["title"]) \
        or SPORT.search(e["title"]) or KIDS.search(e["title"]) or MUSIC.search(e["title"]) \
        or MOVIE.search(e["title"]) or DOCU.search(e["title"])

CAT_ORDER = ["🇨🇳 华语频道", "📰 新闻", "🎬 影视剧", "⚽ 体育", "🌍 纪录知识", "🧒 少儿", "🎵 音乐", "✨ 综合娱乐"]
picked = []
for k, entries in channels.items():
    if not selected(entries):
        continue
    e = entries[0]
    cat = "🇨🇳 华语频道" if is_zh(e) else cat_of(e["title"], e["group0"])
    picked.append((cat, -ch_fame(entries), -ch_best(entries), ch_name(entries), entries))
picked.sort(key=lambda t: (CAT_ORDER.index(t[0]), t[1], t[2], t[3]))

with open(OUT_PICK, "w", encoding="utf-8") as f:
    f.write(HEADER)
    for cat, _, _, _, entries in picked:
        canon = canon_title(entries[0]["title"])
        for b in entries:
            f.write(set_title(set_group(b["extinf"], cat), canon) + "\n")
            for x in b["extra"]:
                f.write(x + "\n")
            f.write(b["url"] + "\n")

# ---------------- full（按国家） ----------------
def country_group(e):
    return e["cc"].upper() if e["cc"] else (e["group0"].split(";")[0] or "其他")

full = []
for k, entries in channels.items():
    e = entries[0]
    full.append((country_group(e), -ch_fame(entries), -ch_best(entries), ch_name(entries), entries))
size = collections.Counter(t[0] for t in full)
full.sort(key=lambda t: (-size[t[0]], t[0], t[1], t[2], t[3]))

n_full = 0
with open(OUT_ALL, "w", encoding="utf-8") as f:
    f.write(HEADER)
    for g, _, _, _, entries in full:
        canon = canon_title(entries[0]["title"])
        for b in entries:
            f.write(set_title(set_group(b["extinf"], g), canon) + "\n")
            for x in b["extra"]:
                f.write(x + "\n")
            f.write(b["url"] + "\n")
            n_full += 1

n_pick = sum(len(t[4]) for t in picked)
cats = collections.Counter(t[0] for t in picked)
print(f"curated: {len(picked)} 频道 / {n_pick} 源 | {dict(sorted(cats.items(), key=lambda x: CAT_ORDER.index(x[0])))}")
print(f"full: {len(full)} 频道 / {n_full} 源 | 分组 {len(size)}")
