#!/usr/bin/env python3
"""全量探测 IPTV 播放列表可播率。
两段式：HLS master -> variant 二级验证；尊重条目自带 UA/Referrer；失败类重试一轮。
输出 JSONL + 汇总。"""
import subprocess, json, re, sys, time, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

PLAYLIST = os.environ.get("PLAYLIST_FILE", "index.m3u")
OUT = "probe_results.jsonl"
SUMMARY = "probe_summary.json"
DEFAULT_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
WORKERS = 60

def parse(path):
    entries = []; extinf = None; vlcopt = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line.startswith("#EXTINF"):
            extinf = line; vlcopt = {}
        elif line.startswith("#EXTVLCOPT:"):
            k, _, v = line[len("#EXTVLCOPT:"):].partition("=")
            vlcopt[k.strip()] = v.strip()
        elif line and not line.startswith("#") and extinf is not None:
            attrs = dict(re.findall(r'([a-zA-Z0-9-]+)="([^"]*)"', extinf))
            entries.append({
                "idx": len(entries),
                "tvg_id": attrs.get("tvg-id", ""),
                "group": attrs.get("group-title", ""),
                "title": extinf.rpartition(",")[2].strip(),
                "url": line,
                "ua": attrs.get("http-user-agent") or vlcopt.get("http-user-agent") or DEFAULT_UA,
                "ref": attrs.get("http-referrer") or vlcopt.get("http-referrer") or "",
            })
            extinf = None
    return entries

def fetch(url, ua, ref, tmax, maxbytes=262143):
    M = "#-#META#-#"  # 不能以 @ 开头：curl -w 会把 @xxx 当作格式文件路径
    cmd = ["curl", "-skL", "--max-time", str(tmax), "--range", "0-%d" % maxbytes,
           "-A", ua, "-w", M + "%{http_code}#-#%{url_effective}"]
    if ref:
        cmd += ["-e", ref]
    cmd += ["--", url]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=tmax + 8)
    except subprocess.TimeoutExpired:
        return None, "000", url, 28
    out = p.stdout
    i = out.rfind(M.encode())
    if i < 0:
        return out, "000", url, p.returncode
    meta = out[i + len(M):].decode("utf-8", "replace").split("#-#")
    return out[:i], (meta[0] if meta else "000"), (meta[1] if len(meta) > 1 else url), p.returncode

CURL_ERR = {5: "proxy-dns", 6: "dns-fail", 7: "conn-refused", 16: "http2-err", 18: "partial-file",
            26: "local-read-err", 28: "timeout", 35: "tls-fail", 52: "empty-reply", 56: "recv-fail", 60: "tls-cert", 92: "http2-err"}

def verdict(body, code, eff, e, rc=0, tmax_variant=10):
    if body is None or code == "000":
        if rc == 28:
            return "timeout", "connect/transfer-timeout"
        return "dead", CURL_ERR.get(rc, "curl-exit-%s" % rc)
    c = int(code) if code.isdigit() else 0
    if c >= 400:
        return "dead", "http-%d" % c
    b = body.lstrip()[:16]
    if body.lstrip().startswith(b"#EXTM3U"):
        text = body.decode("utf-8", "replace")
        if "#EXT-X-" in text and "#EXTINF" in text:
            return "ok", "media-manifest"
        # 无 EXT-X 标签的"清单"要么是 master（含 EXT-X-STREAM-INF，上面已排除），
        # 要么是套壳跳转文件（#EXTM3U+#EXTINF+真实地址）——播放器 HLS 解析会报 MALFORMED，
        # 必须解析内层真实地址并验证，总装时用真实地址替换壳地址
        inner = next((l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")), None)
        if not inner:
            return "dead", "empty-manifest"
        inner_abs = urljoin(eff, inner)
        vb, vc, _veff, _vrc = fetch(inner_abs, e["ua"], e["ref"], tmax_variant)
        if vb is not None and vb.lstrip().startswith(b"#EXTM3U") and b"#EXT-X-" in vb:
            if "#EXT-X-STREAM-INF" in text:
                return "ok", "master+variant"
            return "ok", "nested-resolved:" + inner_abs
        if vb is not None and (vb.lstrip().startswith(b"\x47") or vb[4:8] == b"ftyp"):
            return "ok", "nested-raw:" + inner_abs
        return "variant-fail", "variant-http-%s" % vc
    if b.startswith(b"\x47") or b[4:8] == b"ftyp" or b.startswith(b"FLV"):
        return "ok", "raw-stream"
    if b.startswith(b"<") :
        return "dead", "html/xml-body"
    if len(body) > 100000:
        return "ok", "large-binary"
    return "dead", "unrecognized-body"

def probe(e, tmax=12):
    t0 = time.time()
    if not e["url"].lower().startswith(("http://", "https://")):
        return {**e, "status": "skip", "detail": "non-http-proto", "code": "", "ms": 0}
    body, code, eff, rc = fetch(e["url"], e["ua"], e["ref"], tmax)
    st, detail = verdict(body, code, eff, e, rc)
    return {**e, "status": st, "detail": detail, "code": code, "ms": int((time.time() - t0) * 1000)}

def run(entries, tmax, tag):
    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(probe, e, tmax): e for e in entries}
        for f in as_completed(futs):
            results.append(f.result())
            done += 1
            if tag == "pass1" and done == 300:
                ok300 = sum(1 for r in results if r["status"] == "ok")
                if ok300 == 0:
                    print("FATAL: 前300条全部失败，疑似环境/脚本问题，中止", flush=True)
                    ex.shutdown(wait=False, cancel_futures=True)
                    sys.exit(2)
            if done % 500 == 0:
                ok = sum(1 for r in results if r["status"] == "ok")
                print(f"[{tag}] {done}/{len(entries)} ok={ok}", flush=True)
    return results

def main():
    entries = parse(PLAYLIST)
    print(f"共解析 {len(entries)} 条", flush=True)
    r1 = run(entries, 12, "pass1")
    # 重试：timeout / variant-fail / 5xx / 429（403/404/410 视为确定性死链不重试）
    retry_pool = [r for r in r1 if r["status"] in ("timeout", "variant-fail")
                  or (r["status"] == "dead" and r["detail"].startswith("http-5"))
                  or r["detail"] in ("http-429", "recv-fail", "dns-fail", "empty-reply")]
    keep = {r["idx"]: r for r in r1}
    print(f"pass1 完成，重试 {len(retry_pool)} 条", flush=True)
    r2 = run([{k: r[k] for k in ("idx", "tvg_id", "group", "title", "url", "ua", "ref")} for r in retry_pool], 15, "pass2")
    for r in r2:
        old = keep[r["idx"]]
        if r["status"] == "ok" or old["status"] != "ok":
            r["retried"] = True
            keep[r["idx"]] = r
    final = [keep[i] for i in sorted(keep)]
    with open(OUT, "w", encoding="utf-8") as f:
        for r in final:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    stats = {}
    for r in final:
        stats[r["status"]] = stats.get(r["status"], 0) + 1
    by_status_detail = {}
    for r in final:
        if r["status"] != "ok":
            k = r["detail"].split("-")[0] + ":" + r["detail"]
            by_status_detail[r["detail"]] = by_status_detail.get(r["detail"], 0) + 1
    summary = {"total": len(final), "stats": stats,
               "dead_details": dict(sorted(by_status_detail.items(), key=lambda x: -x[1])[:15])}
    json.dump(summary, open(SUMMARY, "w"), ensure_ascii=False, indent=1)
    print("SUMMARY:", json.dumps(summary, ensure_ascii=False), flush=True)

if __name__ == "__main__":
    main()
