#!/usr/bin/env python3
"""多源聚合：按 sources.json 下载全部上游播放列表 → 统一解析 → URL 级去重 → 输出合并池。

输出：
  pool.m3u    合并后的待测全量（每条 EXTINF 注入 x-src / x-trust / x-region 属性，供总装读取）
  pool_stats.json  各源下载/解析/去重统计
用法：cd 工作目录 && python3 scripts/aggregate_sources.py [sources.json 路径，默认 ./sources.json]
"""
import json, re, subprocess, sys, collections

CFG = sys.argv[1] if len(sys.argv) > 1 else "sources.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

def fetch(url, timeout=300, retries=2):
    for i in range(retries + 1):
        p = subprocess.run(["curl", "-skL", "--max-time", str(timeout), "-A", UA, "--", url],
                           capture_output=True)
        if p.returncode == 0 and p.stdout:
            return p.stdout.decode("utf-8", "replace")
        print(f"    [retry {i+1}] curl exit={p.returncode} {url[:80]}", flush=True)
    return None

def parse_m3u(text):
    entries = []
    extinf = None; extra = []
    for line in text.splitlines():
        line = line.rstrip("\r")
        if line.startswith("#EXTINF"):
            extinf = line; extra = []
        elif line.startswith("#") and extinf is not None and line.strip():
            if not line.startswith("#EXTM3U"):
                extra.append(line)
        elif line.strip() and not line.startswith("#") and extinf is not None:
            entries.append({"extinf": extinf, "extra": extra, "url": line.strip()})
            extinf = None; extra = []
    return entries

def inject_attrs(extinf, src, trust, region):
    # 在 #EXTINF:-1 之后注入来源属性；已有同名属性时不重复
    tag = f' x-src="{src}" x-trust="{trust}" x-region="{region}"'
    m = re.match(r"(#EXTINF:[^\s,]*)", extinf)
    head = m.group(1) if m else "#EXTINF:-1"
    return extinf.replace(head, head + tag, 1)

def main():
    sources = json.load(open(CFG, encoding="utf-8"))
    seen_urls = set()
    stats = []
    n_out = 0
    with open("pool.m3u", "w", encoding="utf-8") as out:
        out.write("#EXTM3U\n")
        for s in sources:
            if not s.get("enabled", True):
                stats.append({"name": s["name"], "skipped": True}); continue
            text = None
            for u in s["urls"]:            # 多个 URL 互为镜像，取第一个成功的
                text = fetch(u)
                if text and "#EXTINF" in text:
                    break
                text = None
            if text is None:
                stats.append({"name": s["name"], "ok": False, "error": "download-failed"})
                print(f"[FAIL] {s['name']}", flush=True)
                continue
            entries = parse_m3u(text)
            dup = 0; added = 0
            for e in entries:
                key = e["url"].strip().lower()
                if key in seen_urls:
                    dup += 1; continue
                seen_urls.add(key)
                out.write(inject_attrs(e["extinf"], s["name"], s.get("trust", 5),
                                       s.get("region", "global")) + "\n")
                for x in e["extra"]:
                    out.write(x + "\n")
                out.write(e["url"] + "\n")
                added += 1
            n_out += added
            stats.append({"name": s["name"], "ok": True, "entries": len(entries),
                          "added": added, "dup_skipped": dup})
            print(f"[OK] {s['name']}: {len(entries)} 条, 新增 {added}, 去重 {dup}", flush=True)
    json.dump({"total_unique": n_out, "sources": stats},
              open("pool_stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"合并池: {n_out} 条唯一 URL / {len(sources)} 个源", flush=True)

if __name__ == "__main__":
    main()
