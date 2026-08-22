import glob, gzip, os
parts = sorted(glob.glob("out_channels_part*.xml")) + sorted(glob.glob("out_fallback*.xml")) + sorted(glob.glob("epg_extra_*.xml"))
assert parts, "no grabbed output found"
n_ch = n_pr = 0
with open("guide.xml", "w", encoding="utf-8") as out:
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n')
    for p in parts:
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                s = line.strip()
                if s.startswith("<?xml") or s.startswith("<tv") or s.startswith("</tv"):
                    continue
                out.write(line if line.endswith("\n") else line + "\n")
                n_ch += s.count("<channel "); n_pr += s.count("<programme ")
    out.write("</tv>\n")
with open("guide.xml", "rb") as fi, gzip.open("guide.xml.gz", "wb") as fo:
    while True:
        b = fi.read(1 << 20)
        if not b: break
        fo.write(b)
print(f"merged {len(parts)} parts: channel={n_ch} programme={n_pr} gz={os.path.getsize('guide.xml.gz')//1048576}MB")
