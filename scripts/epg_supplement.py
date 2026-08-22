#!/usr/bin/env python3
"""EPG 补覆盖（两种模式）。

--mode mjh：直并 i.mjh.nz 现成 EPG，双通道输出 epg_extra_mjh.xml：
    ① 原生通道：频道/节目原样并入（id=mjh 原生 hash，天然匹配 BuddyChew 系 FAST 条目的 tvg-id）
    ② 重映射通道：凡 grabber 映射表（sites/i.mjh.nz/*.channels.xml 的 site_id="Svc/region#id" ↔ xmltv_id）
       中存在 iptv-org id 且主抓取尚未覆盖者，改写 id 后并入（挂接 iptv-org 系条目）
--mode fallback：对比目标 channels/*.xml 与已产出 guide_part*.xml 的覆盖，
    为仍缺失且存在备选站点（非 i.mjh.nz）的频道生成 channels_fallback.xml 供二次抓取。
需要 cwd 下有 grabber/（iptv-org/epg 浅克隆）。
"""
import argparse, glob, re, subprocess, sys, collections
from xml.sax.saxutils import quoteattr

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
# 原生直并的服务/地区（BuddyChew 系列表对应的核心地区）
NATIVE_SERVICES = ["PlutoTV/us", "PlutoTV/ca", "PlutoTV/gb", "PlutoTV/de", "PlutoTV/fr",
                   "PlutoTV/it", "PlutoTV/es", "PlutoTV/mx", "PlutoTV/br",
                   "SamsungTVPlus/us", "Plex/us", "Roku/all"]

def fetch(url, timeout=180):
    for _ in range(2):
        p = subprocess.run(["curl", "-skL", "--max-time", str(timeout), "-A", UA, "--", url],
                           capture_output=True)
        if p.returncode == 0 and p.stdout:
            return p.stdout.decode("utf-8", "replace")
    return None

def programme_covered_ids(patterns=("guide_part*.xml", "out_channels_part*.xml", "out_fallback*.xml")):
    if isinstance(patterns, str):
        patterns = (patterns,)
    ids = set()
    for pattern in patterns:
        for f in glob.glob(pattern):
            for line in open(f, encoding="utf-8", errors="replace"):
                m = re.search(r'<programme[^>]*channel="([^"]+)"', line)
                if m:
                    ids.add(m.group(1))
    return ids

def load_mjh_mapping():
    """{(service_path, mjh_id): xmltv_id}，并返回映射中出现的 service_path 集合"""
    mapping = {}
    paths = set()
    for f in glob.glob("grabber/sites/i.mjh.nz/*.channels.xml"):
        for m in re.finditer(r'<channel\s+([^>]*?)>', open(f, encoding="utf-8", errors="replace").read()):
            a = dict(re.findall(r'([a-zA-Z_]+)="([^"]*)"', m.group(1)))
            sid = a.get("site_id", "")
            xid = a.get("xmltv_id", "")
            if "#" not in sid:
                continue
            svc, mid = sid.split("#", 1)
            paths.add(svc)
            if xid:
                mapping[(svc, mid)] = xid
    return mapping, paths

def mode_mjh(out_path):
    mapping, mapped_paths = load_mjh_mapping()
    covered = programme_covered_ids()
    services = sorted(set(NATIVE_SERVICES) | mapped_paths)
    n_native = n_remap = 0
    with open(out_path, "w", encoding="utf-8") as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n')
        for svc in services:
            text = fetch(f"https://i.mjh.nz/{svc}.xml")
            if not text or "<tv" not in text:
                print(f"[mjh] {svc}: 下载失败/非XML，跳过", flush=True)
                continue
            body = re.findall(r"<(?:channel|programme)[\s\S]*?</(?:channel|programme)>", text)
            native = svc in NATIVE_SERVICES
            for node in body:
                idm = re.search(r'(?:id|channel)="([^"]+)"', node)
                if not idm:
                    continue
                mid = idm.group(1)
                if native:
                    out.write(node + "\n")
                    n_native += 1
                xid = mapping.get((svc, mid))
                if xid and xid not in covered:
                    remapped = node.replace(f'id="{mid}"', f'id="{xid}"').replace(
                        f'channel="{mid}"', f'channel="{xid}"')
                    out.write(remapped + "\n")
                    n_remap += 1
            print(f"[mjh] {svc}: 节点 {len(body)}", flush=True)
        out.write("</tv>\n")
    print(f"mjh 直并完成: 原生节点 {n_native}, 重映射节点 {n_remap} -> {out_path}", flush=True)

def mode_fallback(out_path):
    # 目标
    target_site = {}
    for f in sorted(glob.glob("channels/channels_part*.xml")):
        for line in open(f, encoding="utf-8", errors="replace"):
            m = re.search(r'site="([^"]+)".*?xmltv_id="([^"]+)"', line)
            if m:
                target_site[m.group(2)] = m.group(1)
    covered = programme_covered_ids() | programme_covered_ids("epg_extra_*.xml")
    missing = {t: s for t, s in target_site.items() if t not in covered}
    # 备选站点索引
    idx = collections.defaultdict(list)
    for f in glob.glob("grabber/sites/*/*.channels.xml"):
        for m in re.finditer(r"<channel\s+([^>]*?)>([^<]*)</channel>",
                             open(f, encoding="utf-8", errors="replace").read()):
            a = dict(re.findall(r'([a-zA-Z_]+)="([^"]*)"', m.group(1)))
            if a.get("xmltv_id"):
                idx[a["xmltv_id"]].append({"site": a.get("site", ""), "site_id": a.get("site_id", ""),
                                           "lang": a.get("lang", "en"), "name": m.group(2)})
    rows = []
    for t, primary in sorted(missing.items()):
        cands = [c for c in idx.get(t, []) if c["site"] not in (primary, "i.mjh.nz")]
        if not cands:
            continue
        e = sorted(cands, key=lambda c: c["site"])[0]
        rows.append(f'  <channel site={quoteattr(e["site"])} lang={quoteattr(e["lang"] or "en")} '
                    f'xmltv_id={quoteattr(t)} site_id={quoteattr(e["site_id"])}>{e["name"]}</channel>')
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<channels>\n' + "\n".join(rows) + "\n</channels>\n")
    print(f"fallback 清单: 缺失 {len(missing)}, 可回退 {len(rows)} -> {out_path}", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mjh", "fallback"], required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.mode == "mjh":
        mode_mjh(a.out or "epg_extra_mjh.xml")
    else:
        mode_fallback(a.out or "channels_fallback.xml")
