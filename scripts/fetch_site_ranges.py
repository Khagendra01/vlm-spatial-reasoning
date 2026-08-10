"""
Ultra-fast targeted SITE media fetch, v3 — multipart byteranges.

Phase A: parse central directories (tails + CD regions) -> locate needed
         entries, report total bytes.
Phase B: per zip, fetch needed entry ranges in MULTIPART byteranges
         (~200 ranges per request -> ~200 requests total, rate-limit safe),
         parse parts, decompress, write to media root.

Handles: ZIP64, HTTP 429 (retry with backoff), size validation.
"""
import os, sys, json, subprocess, time, struct, zlib, re
from pathlib import Path

os.chdir("/home/ubuntu/vlm-spatial-reasoning")

NEEDED = Path("results/site/needed_media.txt")
MEDIA_ROOT = Path("data/site_media")
WORK = Path("/tmp/opencode/site_partial")
BASE_URL = "https://huggingface.co/datasets/franky-veteran/SITE-Bench/resolve/main/data_chunked_{:02d}.zip"
TAIL_BYTES = 8 * 1024 * 1024
GROUP = 200
MAX_TRIES = 6


def curl_out(url, out, args):
    for attempt in range(MAX_TRIES):
        r = subprocess.run(["curl", "-sL", "--connect-timeout", "15",
                            "--max-time", "600", "--retry", "3",
                            "--retry-all-errors", "--retry-delay", "2"]
                           + args + ["-o", str(out), "-D", str(out) + ".hdr",
                                     url],
                           check=False, capture_output=True)
        hdr = Path(str(out) + ".hdr")
        code = ""
        if hdr.exists():
            for line in hdr.read_text(errors="replace").splitlines():
                m = re.match(r"^HTTP/\S+\s+(\d+)", line)
                if m:
                    code = m.group(1)
        if code == "429":
            wait = 10 * (attempt + 1)
            print(f"    429 -> waiting {wait}s", flush=True)
            time.sleep(wait)
            continue
        if out.exists() and out.stat().st_size > 0:
            return True
        time.sleep(3 * (attempt + 1))
    return False


def read_eocd(data):
    idx = data.rfind(b"\x50\x4b\x05\x06")
    if idx < 0:
        return None
    cd_size = struct.unpack_from("<I", data, idx + 12)[0]
    cd_offset = struct.unpack_from("<I", data, idx + 16)[0]
    n_entries = struct.unpack_from("<H", data, idx + 10)[0]
    if cd_offset != 0xFFFFFFFF:
        return cd_offset, cd_size, n_entries
    loc = data.rfind(b"\x50\x4b\x06\x07", 0, idx)
    if loc < 0:
        return None
    z64 = loc - 56
    if z64 >= 0 and data[z64:z64 + 4] == b"\x50\x4b\x06\x06":
        n_entries = struct.unpack_from("<Q", data, z64 + 32)[0]
        cd_size = struct.unpack_from("<Q", data, z64 + 40)[0]
        cd_offset = struct.unpack_from("<Q", data, z64 + 48)[0]
        return cd_offset, cd_size, n_entries
    return None


def parse_cd(data, cd_offset, cd_size):
    entries = {}
    pos, end = cd_offset, cd_offset + cd_size
    while pos + 46 <= end and data[pos:pos + 4] == b"\x50\x4b\x01\x02":
        method = struct.unpack_from("<H", data, pos + 10)[0]
        csize = struct.unpack_from("<I", data, pos + 20)[0]
        nlen = struct.unpack_from("<H", data, pos + 28)[0]
        elen = struct.unpack_from("<H", data, pos + 30)[0]
        clen = struct.unpack_from("<H", data, pos + 32)[0]
        name = data[pos + 46: pos + 46 + nlen].decode("utf-8", "replace")
        lho = struct.unpack_from("<I", data, pos + 42)[0]
        if csize == 0xFFFFFFFF or lho == 0xFFFFFFFF:
            extra = data[pos + 46 + nlen: pos + 46 + nlen + elen]
            epos = 0
            while epos + 4 <= len(extra):
                tag, sz = struct.unpack_from("<HH", extra, epos)
                if tag == 0x0001:
                    body = extra[epos + 4: epos + 4 + sz]
                    k = 0
                    if lho == 0xFFFFFFFF and k + 8 <= len(body):
                        lho = struct.unpack_from("<Q", body, k)[0]; k += 8
                    if csize == 0xFFFFFFFF and k + 8 <= len(body):
                        csize = struct.unpack_from("<Q", body, k)[0]; k += 8
                    break
                epos += 4 + sz
        entries[name] = {"lho": lho, "csize": csize, "method": method}
        pos += 46 + nlen + elen + clen
    return entries


def parse_multipart(body, boundary):
    """Parse multipart/byteranges -> {start_offset: bytes}."""
    parts = {}
    for chunk in body.split(b"--" + boundary.encode()):
        if b"Content-Range:" not in chunk:
            continue
        cr = re.search(rb"bytes\s+(\d+)-(\d+)/", chunk)
        if not cr:
            continue
        start, end = int(cr.group(1)), int(cr.group(2))
        data = chunk.split(b"\r\n\r\n", 1)[1]
        if data.endswith(b"\r\n"):
            data = data[:-2]
        parts[start] = data
    return parts


def main():
    needed = set(p for p in NEEDED.read_text().splitlines() if p)
    WORK.mkdir(parents=True, exist_ok=True)
    print(f"Needed: {len(needed)}", flush=True)

    # ── Phase A ──
    t0 = time.time()
    loc = {}
    for i in range(1, 16):
        tail = WORK / f"tail_{i:02d}.bin"
        curl_out(BASE_URL.format(i), tail, ["-r", f"-{TAIL_BYTES}"])
        data = tail.read_bytes()
        eocd = read_eocd(data)
        if eocd is None:
            print(f"zip {i:02d}: no EOCD", flush=True)
            continue
        cd_offset, cd_size, n_entries = eocd
        if cd_offset + cd_size > len(data):
            curl_out(BASE_URL.format(i), WORK / f"cd_{i:02d}.bin",
                     ["-r", f"{cd_offset}-{cd_offset + cd_size - 1}"])
            data = (WORK / f"cd_{i:02d}.bin").read_bytes()
            cd_offset = 0
        entries = parse_cd(data, cd_offset, cd_size)
        hits = {n: e for n, e in entries.items() if n in needed}
        for n, e in hits.items():
            loc[(i, n)] = e
        print(f"  zip {i:02d}: {len(hits)} hits ({time.time()-t0:.0f}s)", flush=True)

    total = sum(e["csize"] for e in loc.values())
    print(f"Located {len(loc)}/{len(needed)}; total compressed {total/1e9:.2f}GB; "
          f"phase A {time.time()-t0:.0f}s", flush=True)

    # ── Phase B: single-range per file (overshoot covers local header) ──
    by_zip = {}
    for (z, n), e in loc.items():
        by_zip.setdefault(z, []).append((n, e))
    t0 = time.time()
    done = 0
    import concurrent.futures as cf

    def fetch_one(z, url, n, e):
        name_len = len(n.encode("utf-8"))
        a = e["lho"]
        b = a + 30 + name_len + 256 + e["csize"] - 1  # overshoot for extra field
        out = WORK / f"f_{z}_{abs(hash(n)) % 1000000:06d}.bin"
        if not curl_out(url, out, ["-r", f"{a}-{b}"]):
            return n, None
        data = out.read_bytes()
        out.unlink()
        Path(str(out) + ".hdr").unlink(missing_ok=True)
        if len(data) < 30 or data[:4] != b"\x50\x4b\x03\x04":
            return n, None
        nlen = struct.unpack_from("<H", data, 26)[0]
        elen = struct.unpack_from("<H", data, 28)[0]
        body = data[30 + nlen + elen: 30 + nlen + elen + e["csize"]]
        if len(body) != e["csize"]:
            return n, None
        try:
            if e["method"] == 8:
                payload = zlib.decompress(body, -15)
            elif e["method"] == 0:
                payload = body
            else:
                return n, None
        except Exception:
            return n, None
        out2 = MEDIA_ROOT / n
        out2.parent.mkdir(parents=True, exist_ok=True)
        out2.write_bytes(payload)
        return n, payload

    for z, items in sorted(by_zip.items()):
        url = BASE_URL.format(z)
        ok = 0
        with cf.ThreadPoolExecutor(max_workers=24) as ex:
            futs = {ex.submit(fetch_one, z, url, n, e): n for n, e in items}
            for fut in cf.as_completed(futs):
                n, payload = fut.result()
                if payload is not None:
                    ok += 1
        done += len(items)
        print(f"  zip {z:02d}: extracted {ok}/{len(items)} "
              f"(total {done}/{len(loc)}, {time.time()-t0:.0f}s)", flush=True)

    present = sum(1 for p in needed if (MEDIA_ROOT / p).exists())
    print(f"Media present: {present}/{len(needed)} in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
