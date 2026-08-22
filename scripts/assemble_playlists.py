#!/usr/bin/env python3
"""基于探测结果总装两级播放列表：推荐精选 + 全量可播。保留原始 EXTINF/指令行不变，仅重排与改写分组。"""
import json, re, collections, os

SRC = os.environ.get("PLAYLIST_FILE", "index.m3u")
PROBE = "probe_results.jsonl"
OUT_PICK = "推荐精选·实测可播.m3u"
OUT_ALL = "全量可播·按国家.m3u"
HEADER = ('#EXTM3U x-tvg-url="'
          'https://raw.githubusercontent.com/quanquanluo0309-lang/epg/output/guide.xml.gz,'
          'https://live.fanmingming.cn/e.xml"\n')

# ---------- 解析原始文件为 block（与探测脚本同序） ----------
blocks = []  # {idx, extinf, extra[], url}
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

RES_RE = re.compile(r"\b(2160|1440|1080|720|576|480|360|240)p?\b")
CJK = re.compile(r"[一-鿿]")
NEWS = re.compile(r"BBC News|CNN|Al Jazeera|Aljazeera|\bDW\b|France 24|France24|Sky News|Bloomberg|CNBC|NHK World|Channel NewsAsia|\bCNA\b|TRT World|Euronews|ABC News|CBS News|NBC News|Fox News|CGTN|Arirang|i24|WION|Africanews|Deutsche Welle|TV5 ?Monde|Rai News|GB News|Times Now|India Today|NDTV|Al Arabiya|凤凰|Phoenix", re.I)
SPORT = re.compile(r"ESPN|DAZN|beIN|Eurosport|Red Bull TV|Sport|Racing|Fight|NBA|NFL|MLB|Tennis|Golf", re.I)
KIDS = re.compile(r"Nick|Cartoon|Disney|Boomerang|Baby|Kids|Duck TV|CBeebies|少儿|卡通", re.I)
MUSIC = re.compile(r"MTV|Vevo|Music|Hits|Clubbing|Stingray|NRJ|Trace ", re.I)
MOVIE = re.compile(r"HBO|AMC|Paramount|Cinema|Cine\b|Movies?|Film|Hollywood|剧场|电影", re.I)
DOCU = re.compile(r"Discovery|Nat ?Geo|National Geographic|History|Animal Planet|Documentar|Arte|Smithsonian|Love Nature|纪实|纪录", re.I)
BRAND = re.compile("|".join([NEWS.pattern, SPORT.pattern, KIDS.pattern, MUSIC.pattern.rstrip(), MOVIE.pattern, DOCU.pattern,
                    r"TVB|翡翠|RTHK|民视|公视|中天|TVBS|三立|東森|东森|华视|台视|CCTV|Comedy Central|Pluto|Rakuten|CBS|Univision|Telemundo|Antena 3|ZDF|ARD|TF1|Canal|BBC One|BBC Two|ITV|Channel 4|Channel 5"]), re.I)

def cc_of(tvg_id):
    base = tvg_id.split("@")[0]
    return base.rsplit(".", 1)[-1].lower() if "." in base else ""

def res_score(title):
    m = RES_RE.search(title)
    return int(m.group(1)) if m else 0

def cat_of(b, title, group):
    g = group.split(";")[0]
    if NEWS.search(title) or g == "News": return "📰 新闻"
    if SPORT.search(title) or g == "Sports": return "⚽ 体育"
    if KIDS.search(title) or g == "Kids": return "🧒 少儿"
    if MOVIE.search(title) or g in ("Movies", "Series"): return "🎬 影视剧"
    if DOCU.search(title) or g in ("Documentary", "Science", "Education"): return "🌍 纪录知识"
    if MUSIC.search(title) or g == "Music": return "🎵 音乐"
    return "✨ 综合娱乐"

def attrs_of(extinf):
    return dict(re.findall(r'([a-zA-Z0-9-]+)="([^"]*)"', extinf))

def set_group(extinf, group):
    if 'group-title="' in extinf:
        return re.sub(r'group-title="[^"]*"', 'group-title="%s"' % group, extinf, count=1)
    return extinf.replace("#EXTINF:-1", '#EXTINF:-1 group-title="%s"' % group, 1)

ok_blocks = []
for b in blocks:
    r = probe.get(b["idx"])
    if r and r["status"] == "ok":
        a = attrs_of(b["extinf"])
        title = b["extinf"].rpartition(",")[2].strip()
        b["tvg_id"] = a.get("tvg-id", "")
        b["title"] = title
        b["cc"] = cc_of(b["tvg_id"])
        b["res"] = res_score(title)
        b["group0"] = a.get("group-title", "")
        ok_blocks.append(b)

# ---------- 推荐精选 ----------
pick = []
for b in ok_blocks:
    zh = b["cc"] in ("cn", "hk", "tw", "mo") or CJK.search(b["title"])
    if zh or BRAND.search(b["title"]):
        b["zh"] = bool(zh)
        pick.append(b)
# 按 tvg_id 基名去重：保留分辨率最高的一条；无 ID 的按标题去重
best = {}
for b in pick:
    key = b["tvg_id"].split("@")[0] or ("T:" + b["title"].lower())
    if key not in best or b["res"] > best[key]["res"]:
        best[key] = b
pick = list(best.values())
for b in pick:
    b["cat"] = "🇨🇳 华语频道" if b["zh"] else cat_of(b, b["title"], b["group0"])
CAT_ORDER = ["🇨🇳 华语频道", "📰 新闻", "🎬 影视剧", "⚽ 体育", "🌍 纪录知识", "🧒 少儿", "🎵 音乐", "✨ 综合娱乐"]
pick.sort(key=lambda b: (CAT_ORDER.index(b["cat"]), -b["res"], b["title"].lower()))

with open(OUT_PICK, "w", encoding="utf-8") as f:
    f.write(HEADER)
    for b in pick:
        f.write(set_group(b["extinf"], b["cat"]) + "\n")
        for x in b["extra"]:
            f.write(x + "\n")
        f.write(b["url"] + "\n")

# ---------- 全量可播（按国家分组） ----------
def all_group(b):
    if b["cc"]:
        return b["cc"].upper()
    return (b["group0"].split(";")[0] or "其他")
for b in ok_blocks:
    b["gg"] = all_group(b)
order = collections.Counter(b["gg"] for b in ok_blocks)
ok_blocks.sort(key=lambda b: (-order[b["gg"]], b["gg"], -b["res"], b["title"].lower()))
with open(OUT_ALL, "w", encoding="utf-8") as f:
    f.write(HEADER)
    for b in ok_blocks:
        f.write(set_group(b["extinf"], b["gg"]) + "\n")
        for x in b["extra"]:
            f.write(x + "\n")
        f.write(b["url"] + "\n")

cats = collections.Counter(b["cat"] for b in pick)
print("推荐精选:", len(pick), "条 |", dict(sorted(cats.items(), key=lambda x: CAT_ORDER.index(x[0]))))
print("全量可播:", len(ok_blocks), "条 | 分组数:", len(order))
