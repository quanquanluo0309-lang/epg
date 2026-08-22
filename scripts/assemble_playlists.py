#!/usr/bin/env python3
"""总装两级播放列表（v3 多源聚合版）。

输入：PLAYLIST_FILE（默认 pool.m3u，由 aggregate_sources.py 生成，条目含 x-src/x-trust/x-region）
     + probe_results.jsonl（探测结果）
curated（推荐精选）：
  组序：央视→卫视地方→香港→台湾→国际新闻→影视→体育→纪录→少儿→音乐→综合精选
  组内：FAME 影响力分级降序 → 同级按最佳线路质量
  同频道多源（跨上游合并）：相邻放置、显示名统一、按 分辨率+连接速度+稳定性+来源信任分 降序，≤5 条
full（全量可播）：按国家/地区分组，同样排序
频道识别：tvg-id 基名优先；无 ID 或跨源时用归一化名（去空格连字符/画质词/CCTV 规则/别名表）合并，
         合并时继承 iptv-org 式 tvg-id 以挂接 EPG。
"""
import json, re, collections, os

SRC = os.environ.get("PLAYLIST_FILE", "pool.m3u")
PROBE = "probe_results.jsonl"
OUT_PICK = "推荐精选·实测可播.m3u"
OUT_ALL = "全量可播·按国家.m3u"
HEADER = ('#EXTM3U x-tvg-url="'
          'https://raw.githubusercontent.com/quanquanluo0309-lang/epg/output/guide.xml.gz,'
          'https://live.fanmingming.cn/e.xml"\n')

# ---------------- 知名度/影响力分级表（分数越高越靠前） ----------------
FAME_TIERS = [
    (1000,
     ["CCTV-?1\\b", "CCTV-?13", "Phoenix (Chinese|InfoNews|TV)", "France ?24", "Aljazeera"],
     ["BBC News", "BBC World", "CNN", "Al Jazeera", "Sky News", "Deutsche Welle", "DW News", "DW", "Euronews",
      "NHK World", "CGTN", "Bloomberg", "Reuters", "TRT World", "CNBC",
      "凤凰卫视", "鳳凰衛視", "凤凰中文", "凤凰资讯", "now新聞", "TVB", "翡翠台", "Jade", "明珠台", "Pearl", "CCTV新闻"]),
    (900,
     ["CCTV-?[24]\\b", "i24", "RT News"],
     ["Fox News", "MSNBC", "ABC News", "CBS News", "NBC News", "CTV News", "CBC News", "Al Arabiya",
      "Sky News Arabia", "Channel NewsAsia", "CNA", "Arirang", "YTN", "WION", "India Today", "NDTV",
      "Times Now", "Republic TV", "News18", "Zee News", "ARY News", "Geo News", "GB News", "Africanews",
      "TV5 Monde", "TV5Monde", "BFM TV", "LCI", "ANC", "GMA News",
      "中天新闻", "中天新聞", "东森新闻", "東森新聞", "三立新闻", "三立新聞", "TVBS", "RTHK", "港台电视", "港台電視", "公视", "公視", "PTS", "民视", "民視", "台视", "台視", "中视", "中視", "华视", "華視",
      "东方卫视", "湖南卫视", "浙江卫视", "江苏卫视", "北京卫视", "广东卫视", "深圳卫视",
      "ViuTV", "香港开电视", "HOY", "now新闻", "澳亚卫视", "澳视"]),
    (800,
     [r"\bARD\b", r"\bZDF\b", "La 1\\b", r"\bITV\b", r"\bNHK\b", r"\bKBS\b", r"\bMBC\b", r"\bSBS\b",
      r"\bRTL\b", "Canal\\+", "SAT\\.1", "CCTV", "卫视", "衛視"],
     ["Das Erste", "TF1", "France 2", "Rai 1", "Rai 2", "RTVE", "BBC One", "BBC Two", "Channel 4",
      "Globo", "Televisa", "Antena 3", "Telecinco", "ProSieben", "América TV", "Caracol", "TV Azteca",
      "Doordarshan", "DD National", "Rede Record", "SBT", "RTP1", "SIC", "TV2 Norway", "SVT1", "DR1",
      "YLE", "ORF", "SRF", "RTS Un", "Seven Network", "Nine Network",
      "纬来", "八大", "东森", "三立", "年代", "非凡", "民视第一台"]),
    (700,
     [r"\bAMC\b", r"\bFX\b", r"\bMTV\b", "Sony (TV|Entertainment|Movies)", "Star (Plus|Movies|Sports)",
      "Nat ?Geo", r"\bTNT\b", r"\bTLC\b", r"\bE!\b", r"\bVH1\b"],
     ["HBO", "Cinemax", "Showtime", "Starz", "Paramount", "Universal", "Warner", "USA Network", "Syfy",
      "Bravo", "Comedy Central", "AXN", "TCM", "Movistar",
      "ESPN", "Sky Sports", "Fox Sports", "beIN", "Eurosport", "NBC Sports", "TNT Sports", "DAZN",
      "Star Sports", "TSN", "Sportsnet", "Setanta", "SuperSport", "Red Bull TV", "五星体育", "广东体育",
      "National Geographic", "Discovery", "Animal Planet", "History", "BBC Earth", "Smithsonian",
      "Curiosity", "Travel Channel", "DMAX", "求索", "纪实",
      "Disney", "Cartoon Network", "Nickelodeon", "Nick Jr", "Boomerang", "PBS Kids", "CBeebies",
      "Baby TV", "Toonami", "金鹰卡通", "卡酷", "Trace", "CMT", "Fuse", "4Music", "Music Choice"]),
]
def _lit(n):
    return r"(?<![A-Za-z0-9])" + re.escape(n) + r"(?![A-Za-z0-9])"
FAME_COMPILED = [(s, re.compile("|".join(rx + [_lit(n) for n in names]), re.I))
                 for s, rx, names in FAME_TIERS]

RES_RE = re.compile(r"\b(2160|1440|1080|720|576|480|360|240)p?\b")
CJK = re.compile(r"[一-鿿]")
NEWS = re.compile(r"BBC News|CNN|Al Jazeera|Aljazeera|\bDW\b|France ?24|Sky News|Bloomberg|CNBC|NHK World|Channel NewsAsia|\bCNA\b|TRT World|Euronews|ABC News|CBS News|NBC News|Fox News|CGTN|Arirang|i24|WION|Africanews|Deutsche Welle|TV5 ?Monde|Rai News|GB News|Times Now|India Today|NDTV|Al Arabiya|MSNBC|Reuters", re.I)
SPORT = re.compile(r"ESPN|DAZN|beIN|Eurosport|Red Bull TV|Sky Sports|Sport|Racing|Fight|NBA|NFL|MLB|Tennis|Golf|体育", re.I)
KIDS = re.compile(r"Nick|Cartoon|Disney|Boomerang|Baby|Kids|Duck TV|CBeebies|少儿|卡通|亲子", re.I)
MUSIC = re.compile(r"MTV|Vevo|Music|Hits|Clubbing|Stingray|NRJ|Trace |音乐", re.I)
MOVIE = re.compile(r"HBO|AMC|Paramount|Cinema|Cine\b|Movies?|Film|Hollywood|Showtime|Cinemax|剧场|电影|影视|戏剧", re.I)
DOCU = re.compile(r"Discovery|Nat ?Geo|National Geographic|History|Animal Planet|Documentar|Arte|Smithsonian|Love Nature|纪实|纪录|求索", re.I)
BRAND_EXTRA = re.compile(r"TVB|翡翠|RTHK|民视|公视|中天|TVBS|三立|東森|东森|华视|台视|CCTV|Comedy Central|Rakuten|Pluto|CBS|Univision|Telemundo|ZDF|ARD|TF1|BBC|ITV|Channel [45]\b|RTL|Antena", re.I)
HK_RE = re.compile(r"TVB|翡翠|明珠|Jade|Pearl|ViuTV|Viu TV|开电视|開電視|HOY|RTHK|港台电视|now|凤凰|鳳凰|Phoenix|香港", re.I)
TW_RE = re.compile(r"民视|民視|公视|公視|PTS|台视|台視|中视|中視|华视|華視|TVBS|三立|东森|東森|中天|纬来|緯來|八大|年代|非凡|寰宇|镜新闻|鏡新聞|台湾|台灣", re.I)
CCTV_RE = re.compile(r"CCTV|CGTN|央视|央視|中央电视台", re.I)

STRIP_TITLE = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]\s*$")
QUAL_WORDS = re.compile(r"(高清|超清|超高清|蓝光|藍光|标清|標清|\b(hd|fhd|uhd|sd|4k|8k|50fps)\b)", re.I)

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

def canon_title(title):
    t = title
    while True:
        t2 = STRIP_TITLE.sub("", t)
        if t2 == t:
            break
        t = t2
    return re.sub(r"\s+", " ", t).strip() or title

ALIAS = {  # 归一化名 → 统一键（小写无空格态）
    "翡翠台": "tvbjade", "tvbjade": "tvbjade",
    "明珠台": "tvbpearl", "tvbpearl": "tvbpearl",
    "凤凰卫视中文台": "凤凰中文", "凤凰中文台": "凤凰中文", "凤凰中文": "凤凰中文",
    "凤凰卫视资讯台": "凤凰资讯", "凤凰资讯台": "凤凰资讯", "凤凰资讯": "凤凰资讯",
    "凤凰卫视香港台": "凤凰香港", "凤凰香港台": "凤凰香港",
}
FW = str.maketrans("ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９－　",
                   "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789- ")

def norm_name(title):
    t = canon_title(title).translate(FW)
    t = QUAL_WORDS.sub("", t)
    t = re.sub(r"[\s\-_\.·]+", "", t).lower()
    t = re.sub(r"(4k|8k|fhd|uhd|50fps|高清|超清|超高清|蓝光|标清)+$", "", t)
    m = re.match(r"^cctv(\d+\+?)", t)      # CCTV1综合 / CCTV-1 / cctv1hd → cctv1
    if m:
        return "cctv" + m.group(1)
    return ALIAS.get(t, t)

def channel_key(tvg_id, title):
    base = tvg_id.split("@")[0]
    if base and "." in base:               # iptv-org 式 Name.cc 才作强键
        return "id:" + base
    n = norm_name(title)
    return ("n:" + n) if n else ("t:" + title.lower())

def cc_of(tvg_id):
    base = tvg_id.split("@")[0]
    return base.rsplit(".", 1)[-1].lower() if "." in base else ""

def set_group(extinf, group):
    if 'group-title="' in extinf:
        return re.sub(r'group-title="[^"]*"', 'group-title="%s"' % group, extinf, count=1)
    return extinf.replace("#EXTINF:-1", '#EXTINF:-1 group-title="%s"' % group, 1)

def set_title(extinf, new_title):
    head, _, _ = extinf.rpartition(",")
    return head + "," + new_title

# ---------------- 解析 + 探测合并 ----------------
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
    b["srcname"] = attrs.get("x-src", "?")
    b["trust"] = int(attrs.get("x-trust", "5"))
    b["region"] = attrs.get("x-region", "global")
    b["key"] = channel_key(b["tvg_id"], title)
    b["fame"] = fame_of(title)
    b["q"] = res_pts(title) + speed_pts(r.get("ms", 9999)) - (6 if r.get("retried") else 0) + b["trust"] * 3
    ok.append(b)

# 二次合并：无 ID 条目与有 ID 条目若归一化名相同则并为一个频道（继承 ID 键）
name_to_idkey = {}
for b in ok:
    if b["key"].startswith("id:"):
        name_to_idkey.setdefault(norm_name(b["title"]), b["key"])
for b in ok:
    if b["key"].startswith("n:"):
        idk = name_to_idkey.get(b["key"][2:])
        if idk:
            b["key"] = idk

MAX_LINES_PICK = 8   # 精选：每频道最多保留 8 条跨源线路（用户要求多线路可选）
MAX_LINES_FULL = 5
channels = collections.defaultdict(list)
for b in ok:
    channels[b["key"]].append(b)
for k in channels:
    channels[k].sort(key=lambda b: -b["q"])
    channels[k] = channels[k][:MAX_LINES_PICK]

def ch_fame(es): return max(e["fame"] for e in es)
def ch_best(es): return es[0]["q"]
def ch_name(es): return min(e["title"] for e in es)
def ch_tvgid(es):
    for e in es:
        if e["tvg_id"] and "." in e["tvg_id"].split("@")[0]:
            return e["tvg_id"]
    return es[0]["tvg_id"]

def is_zh(es):
    return any(e["cc"] in ("cn", "hk", "tw", "mo") or e["region"] in ("cn", "hk", "tw", "mo")
               or CJK.search(e["title"]) for e in es)

def zh_group(es):
    text = " ".join({e["title"] for e in es})
    ccs = {e["cc"] for e in es} | {e["region"] for e in es}
    if CCTV_RE.search(text): return "🇨🇳 央视"
    if HK_RE.search(text) or "hk" in ccs: return "🇭🇰 香港"
    if TW_RE.search(text) or "tw" in ccs: return "🇹🇼 台湾"
    if "卫视" in text or "衛視" in text: return "🇨🇳 卫视"
    return "🇨🇳 地方·其他"

def cat_of(es):
    e = es[0]
    t = e["title"]; g = e["group0"].split(";")[0]
    if NEWS.search(t) or "news" in g.lower(): return "📰 国际新闻"
    if SPORT.search(t) or "sport" in g.lower(): return "⚽ 体育"
    if KIDS.search(t) or "kids" in g.lower() or "children" in g.lower(): return "🧒 少儿"
    if MOVIE.search(t) or "movie" in g.lower() or "series" in g.lower(): return "🎬 影视剧"
    if DOCU.search(t) or "documentar" in g.lower() or "science" in g.lower(): return "🌍 纪录知识"
    if MUSIC.search(t) or "music" in g.lower(): return "🎵 音乐"
    return "✨ 综合精选"

def selected(es):
    e = es[0]
    return is_zh(es) or ch_fame(es) > 0 or bool(BRAND_EXTRA.search(e["title"]))

CAT_ORDER = ["🇨🇳 央视", "🇨🇳 卫视", "🇭🇰 香港", "🇹🇼 台湾", "🇨🇳 地方·其他", "📰 国际新闻",
             "🎬 影视剧", "⚽ 体育", "🌍 纪录知识", "🧒 少儿", "🎵 音乐", "✨ 综合精选"]

picked = []
for k, es in channels.items():
    if not selected(es):
        continue
    cat = zh_group(es) if is_zh(es) else cat_of(es)
    picked.append((cat, -ch_fame(es), -ch_best(es), ch_name(es), es))
picked.sort(key=lambda t: (CAT_ORDER.index(t[0]), t[1], t[2], t[3]))

def write_channel(f, cat, es):
    canon = canon_title(es[0]["title"])
    tid = ch_tvgid(es)
    for b in es:
        line = set_title(set_group(b["extinf"], cat), canon)
        if tid and tid != b["tvg_id"]:
            if 'tvg-id="' in line:
                line = re.sub(r'tvg-id="[^"]*"', 'tvg-id="%s"' % tid, line, count=1)
            else:
                line = line.replace("#EXTINF:-1", '#EXTINF:-1 tvg-id="%s"' % tid, 1)
        f.write(line + "\n")
        for x in b["extra"]:
            f.write(x + "\n")
        f.write(b["url"] + "\n")

with open(OUT_PICK, "w", encoding="utf-8") as f:
    f.write(HEADER)
    for cat, _, _, _, es in picked:
        write_channel(f, cat, es)

# ---------------- full（按国家/地区） ----------------
REGION_NAME = {"cn": "CN", "hk": "HK", "tw": "TW", "mo": "MO", "fast": "FAST免费平台"}
def country_group(es):
    e = es[0]
    if e["cc"]:
        return e["cc"].upper()
    if e["region"] in REGION_NAME:
        return REGION_NAME[e["region"]]
    if CJK.search(e["title"]):
        return "华语·未标区"
    return "其他"

full = []
for k, es in channels.items():
    full.append((country_group(es), -ch_fame(es), -ch_best(es), ch_name(es), es))
size = collections.Counter(t[0] for t in full)
full.sort(key=lambda t: (-size[t[0]], t[0], t[1], t[2], t[3]))

n_full = 0
with open(OUT_ALL, "w", encoding="utf-8") as f:
    f.write(HEADER)
    for g, _, _, _, es in full:
        es = es[:MAX_LINES_FULL]
        write_channel(f, g, es)
        n_full += len(es)

n_pick = sum(len(t[4]) for t in picked)
cats = collections.Counter(t[0] for t in picked)
print(f"curated: {len(picked)} 频道 / {n_pick} 源 | " +
      " ".join(f"{c}:{cats[c]}" for c in CAT_ORDER if cats.get(c)))
print(f"full: {len(full)} 频道 / {n_full} 源 | 分组 {len(size)}")
