#!/usr/bin/env python3
"""Search, inspect and acquire local media. No raw extractor JSON is persisted."""
import argparse
import contextlib
import datetime as dt
import fcntl
import html
import http.client
import http.cookiejar
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import warnings
from pathlib import Path

from common import ROOT, CONFIG, local_env
import download as ledger
from media_support import bili_search, yt_dlp_readonly as guard

FORMATS = {
    "audio": "bestaudio[protocol^=http]/best[protocol^=http]",
    "video": "bestvideo[height<=1080][protocol^=http]+bestaudio[protocol^=http]/best[height<=1080][protocol^=http]",
}


class MediaError(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason
        super().__init__(reason)


def clean(value, limit=240):
    return " ".join("".join(c if c.isprintable() else " " for c in str(value or "")).split())[:limit]


def remote_url(value):
    try:
        u = urllib.parse.urlsplit(value)
        if u.scheme not in {"https", "http"} or not u.hostname or u.username or u.password:
            raise ValueError()
        if u.hostname in {"localhost", "localhost.localdomain"} or u.hostname.endswith(".local"):
            raise ValueError()
        try:
            address = ipaddress.ip_address(u.hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError()
        return value
    except (ValueError, TypeError):
        raise MediaError("BLOCKED_INPUT", "public_http_url_required") from None


def public_url(value):
    """Receipts retain public page identifiers, never CDN tokens or signed URLs."""
    try:
        remote_url(value)
        u = urllib.parse.urlsplit(value)
        query = [(k, v) for k, v in urllib.parse.parse_qsl(u.query)
                 if k in {"v", "p"} and re.fullmatch(r"[\w-]{1,64}", v)]
        return urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, urllib.parse.urlencode(query), ""))
    except MediaError:
        return ""


def summary(info):
    return {
        "id": clean(info.get("id"), 80), "title": clean(info.get("title")),
        "uploader": clean(info.get("uploader")), "duration": info.get("duration"),
        "webpage_url": public_url(info.get("webpage_url") or info.get("url") or ""),
        "license": clean(info.get("license")) or "unknown",
        "extractor": clean(info.get("extractor_key") or info.get("extractor")),
    }


def classify_stderr(stderr):
    detail = stderr.casefold()
    if re.search(r"operation not permitted|permission denied|sandbox|approval required", detail):
        return MediaError("BLOCKED_ENV", "local_execution_denied")
    if re.search(r"cookies?[^\n]*(no longer valid|expired|rotated)|sign in|log ?in required|http error (401|403|412|429)|not a bot", detail):
        return MediaError("BLOCKED_ACCESS", "authentication_or_platform_restriction")
    if "requested format is not available" in detail:
        return MediaError("BLOCKED_FORMAT", "requested_http_format_unavailable")
    if re.search(r"getaddrinfo|name resolution|resolve|connection|timed out|ssl", detail):
        return MediaError("RETRY_REQUIRED", "transport_unresolved")
    return MediaError("RETRY_REQUIRED", "extractor_failed")


@contextlib.contextmanager
def session(args):
    selected = args.cookies or os.environ.get("SVC_LAB_COOKIE_FILE")
    if args.public:
        selected = None
    elif not selected and (ROOT / "all_cookies.txt").exists():
        selected = ROOT / "all_cookies.txt"
    if selected:
        with guard.private_cookie_snapshot(Path(selected).expanduser(), repo_root=ROOT) as snapshot:
            yield snapshot
    else:
        yield None


def connect_ipv4(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """Per-connection IPv4, matching cc-media's YouTube default; no OS changes."""
    last = None
    for family, kind, proto, _, sockaddr in socket.getaddrinfo(*address, socket.AF_INET, socket.SOCK_STREAM):
        sock = socket.socket(family, kind, proto)
        try:
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            return sock
        except OSError as error:
            last = error
            sock.close()
    raise last or OSError("IPv4 resolution returned no addresses")


class IPv4HTTPConnection(http.client.HTTPConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = connect_ipv4


class IPv4HTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = connect_ipv4


class IPv4HTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, request):
        return self.do_open(IPv4HTTPConnection, request)


class IPv4HTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
        return self.do_open(IPv4HTTPSConnection, request, context=self._context)


def opener_for(snapshot, *, ipv4=False):
    handlers = [IPv4HTTPHandler(), IPv4HTTPSHandler()] if ipv4 else []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # malformed cookie rows can contain secrets
        if snapshot:
            handlers.append(urllib.request.HTTPCookieProcessor(bili_search.load_cookie_jar(snapshot)))
    opener = urllib.request.build_opener(*handlers)
    opener.addheaders = [("User-Agent", bili_search.UA)]
    return opener


def extract(target, snapshot, *, flat=False, kind="audio"):
    command = ["yt-dlp", "--ignore-config", "--no-config-locations", "--no-plugin-dirs",
               "--no-remote-components", "--no-cache-dir", "--skip-download", "--no-playlist",
               "--no-progress", "--socket-timeout", "15", "--retries", "0",
               "--extractor-retries", "0", "--dump-single-json"]
    command += ["--cookies", str(snapshot)] if snapshot else ["--no-cookies"]
    command += guard._youtube_defaults([target])
    command += ["--flat-playlist"] if flat else ["--playlist-end", "1", "-f", FORMATS[kind]]
    result = subprocess.run([*command, "--", target], capture_output=True, text=True,
                            errors="replace", timeout=100, env=local_env(offline=False))
    if result.returncode:
        raise classify_stderr(result.stderr)
    try:
        info = json.loads(result.stdout)
        if not isinstance(info, dict):
            raise ValueError()
        if not flat and (info.get("entries") is not None or info.get("is_live")):
            raise MediaError("BLOCKED_INPUT", "playlists_and_live_streams_not_acquired")
        return info
    except (ValueError, TypeError):
        raise MediaError("RETRY_REQUIRED", "invalid_extractor_response") from None


def search(args, snapshot):
    if args.platform == "youtube":
        info = extract(f"ytsearch{args.limit}:{args.query}", snapshot, flat=True)
        return [summary(row) for row in info.get("entries", []) if isinstance(row, dict)]
    opener = opener_for(snapshot)
    opener.addheaders = [("User-Agent", bili_search.UA), ("Referer", "https://www.bilibili.com/")]
    rows = bili_search.search(args.query, args.limit, opener=opener)
    results = []
    for row in rows:
        bvid = row.get("bvid", "")
        if not re.fullmatch(r"BV[0-9A-Za-z]{10}", bvid):
            continue
        results.append({"id": bvid, "title": clean(html.unescape(re.sub("<[^>]+>", "", row["title"]))),
                        "uploader": clean(row["author"]), "duration": clean(row["duration"]),
                        "webpage_url": f"https://www.bilibili.com/video/{bvid}/", "license": "unknown"})
    return results


def selected_streams(info):
    streams = info.get("requested_formats") or [info]
    if not 1 <= len(streams) <= 2:
        raise MediaError("BLOCKED_FORMAT", "one_or_two_streams_required")
    for stream in streams:
        remote_url(stream.get("url", ""))
        if stream.get("protocol") not in {"http", "https"} or stream.get("fragments"):
            raise MediaError("BLOCKED_FORMAT", "fragmented_stream_requires_separate_budget_adapter")
        if stream.get("has_drm"):
            raise MediaError("BLOCKED_FORMAT", "drm_stream")
    return streams


def stream_headers(stream):
    # Do not copy raw Cookie/Authorization across hosts; CookieJar handles domain scope.
    return {k: str(v) for k, v in stream.get("http_headers", {}).items()
            if k.lower() in {"user-agent", "referer", "origin", "accept", "accept-language"}}


def inspect_size(opener, stream, cap):
    # An extractor's exact filesize is sufficient; filesize_approx is never trusted.
    # Some CDNs reject HEAD although the media GET itself is allowed.
    declared = stream.get("filesize")
    if type(declared) is int and declared > 0:
        if declared > cap:
            raise MediaError("BLOCKED_SIZE", "single_file_limit_exceeded")
        return declared
    headers = {**stream_headers(stream), "Accept-Encoding": "identity"}
    request = urllib.request.Request(stream["url"], headers=headers, method="HEAD")
    with opener.open(request, timeout=20) as response:
        remote_url(response.geturl())
        raw = response.headers.get("Content-Length", "")
        if not raw.isdigit() or int(raw) <= 0:
            raise MediaError("BLOCKED_SIZE", "exact_content_length_required")
        size = int(raw)
        if size > cap:
            raise MediaError("BLOCKED_SIZE", "single_file_limit_exceeded")
        return size


def copy_bounded(response, output, size, row):
    """Read at most the reserved bytes, never an extra chunk past the boundary."""
    length = response.headers.get("Content-Length", "")
    if length != str(size) or response.headers.get("Content-Encoding", "identity") != "identity":
        raise MediaError("BLOCKED_SIZE", "get_headers_differ_from_preflight")
    while row["transferred_bytes"] < size:
        chunk = response.read(min(1024 * 1024, size - row["transferred_bytes"]))
        if not chunk:
            raise MediaError("FAILED_DOWNLOAD", "incomplete_body")
        output.write(chunk)
        row["transferred_bytes"] += len(chunk)


def run_directory(run_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise MediaError("BLOCKED_INPUT", "invalid_run_id")
    path = ROOT / "work/acquisition" / run_id
    if not path.resolve().is_relative_to(ROOT.resolve()) or path.exists():
        raise MediaError("BLOCKED_INPUT", "run_path_exists_or_outside_repository")
    return path


def append_rows(rows):
    with ledger.LEDGER.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def transfer(info, args, snapshot, event):
    directory = run_directory(args.run_id)
    streams = selected_streams(info)
    opener = opener_for(snapshot, ipv4=info.get("extractor_key") == "Youtube")
    sizes = [inspect_size(opener, stream, args.max_bytes) for stream in streams]
    receipt = summary(info)
    page = receipt["webpage_url"] or public_url(args.url)
    rows = []
    for index, (stream, size) in enumerate(zip(streams, sizes)):
        ext = stream.get("ext", "bin")
        if not re.fullmatch(r"[A-Za-z0-9]{1,8}", ext):
            ext = "bin"
        path = directory / f"stream-{index}.{ext}"
        rows.append({"kind": "media", "dest": str(path.relative_to(ROOT)), "url": page,
                     "evidence": page, "purpose": args.purpose, "license": receipt["license"],
                     "size_bytes": size, "format_id": clean(stream.get("format_id"), 80),
                     "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                     "status": "NOT_STARTED", "transferred_bytes": 0, "budget_bytes": 0})
    (ROOT / ".cache").mkdir(exist_ok=True)
    with (ROOT / ".cache/download.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        held = ledger.reservations()
        if ledger.charged(ledger.records()) + sum(held.values()) + sum(sizes) > CONFIG["total_download_limit_bytes"]:
            raise MediaError("BLOCKED_SIZE", "cumulative_download_limit_exceeded")
        if shutil.disk_usage(ROOT).free < sum(sizes) * 3 + CONFIG["minimum_free_disk_bytes"]:
            raise MediaError("BLOCKED_ENV", "insufficient_free_disk")
        directory.mkdir(parents=True, exist_ok=False)
        reservation = "media-" + event["id"]
        held[reservation] = sum(sizes)
        ledger.save_reservations(held)
        failure = None
        try:
            for stream, row in zip(streams, rows):
                path = ROOT / row["dest"]
                partial = path.with_name(path.name + ".part")
                row.update(status="FAILED", budget_bytes=row["size_bytes"], partial_path=str(partial.relative_to(ROOT)))
                request = urllib.request.Request(stream["url"], headers={**stream_headers(stream), "Accept-Encoding": "identity"})
                with opener.open(request, timeout=30) as response, partial.open("xb") as output:
                    remote_url(response.geturl())
                    copy_bounded(response, output, row["size_bytes"], row)
                row["sha256"] = ledger.hash_file(partial)
                partial.rename(path)
                row["status"] = "DOWNLOADED"
        except Exception as error:
            failure = error
        # BaseException/kill retains reservation and .part for conservative accounting.
        append_rows(rows)
        held.pop(reservation)
        ledger.save_reservations(held)
        ledger.render()
        event["downloads"] = rows
        if failure:
            raise failure
    return directory, rows, receipt


def finish_media(directory, rows, args):
    output = directory / ("audio.wav" if args.kind == "audio" else "video.mkv")
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n"]
    for row in rows:
        command += ["-protocol_whitelist", "file,pipe,crypto", "-i", str(ROOT / row["dest"])]
    if args.kind == "audio":
        # Keep channel count/sample rate; normalization belongs to preprocessing.
        command += ["-map", "0:a:0", "-vn", "-c:a", "pcm_s16le"]
    else:
        command += ["-map", "0:v:0", "-map", "1:a:0" if len(rows) == 2 else "0:a:0", "-c", "copy"]
    result = subprocess.run([*command, str(output)], capture_output=True, timeout=600, env=local_env())
    if result.returncode:
        raise MediaError("FAILED_POSTPROCESS", "ffmpeg_failed_raw_streams_retained")
    probe = subprocess.run(["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe,crypto", "-show_entries", "format=duration,size:stream=codec_type,codec_name,sample_rate,channels,width,height",
                            "-of", "json", str(output)], capture_output=True, text=True, timeout=30)
    if probe.returncode:
        raise MediaError("FAILED_POSTPROCESS", "ffprobe_failed")
    result_info = {"path": str(output.relative_to(ROOT)), "sha256": ledger.hash_file(output),
                   "size_bytes": output.stat().st_size, "probe": json.loads(probe.stdout)}
    if args.role != "reference":
        if args.kind != "audio":
            raise MediaError("BLOCKED_INPUT", "target_source_roles_require_audio")
        destination = ROOT / "data" / args.role / f"{args.run_id}.wav"
        if not destination.parent.resolve().is_relative_to(ROOT.resolve()):
            raise MediaError("BLOCKED_INPUT", "data_path_outside_repository")
        with output.open("rb") as source, destination.open("xb") as target:
            shutil.copyfileobj(source, target)
        result_info["data_path"] = str(destination.relative_to(ROOT))
    return result_info


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    auth = parser.add_mutually_exclusive_group()
    auth.add_argument("--cookies", help="Existing user-maintained Netscape jar; consumed read-only")
    auth.add_argument("--public", action="store_true", help="Do not read any cookie jar")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    search_p = sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--platform", choices=["youtube", "bilibili"], default="youtube")
    search_p.add_argument("--limit", type=int, choices=range(1, 21), default=5)
    for name in ("probe", "download"):
        child = sub.add_parser(name)
        child.add_argument("url")
        child.add_argument("--kind", choices=["audio", "video"], default="audio")
        if name == "download":
            child.add_argument("--run-id", required=True)
            child.add_argument("--role", choices=["target", "source", "reference"], default="reference")
            child.add_argument("--purpose", required=True)
            child.add_argument("--max-bytes", type=int, default=500_000_000,
                               help="Per-stream cap; default 500 MB, maximum 5 GB")
    return parser.parse_args(argv)


def doctor():
    results = {}
    for tool in ("yt-dlp", "ffmpeg", "ffprobe"):
        executable = shutil.which(tool)
        if not executable:
            results[tool] = {"available": False}
        else:
            result = subprocess.run([executable, "--version" if tool == "yt-dlp" else "-version"], capture_output=True, text=True, timeout=15)
            results[tool] = {"available": result.returncode == 0, "version": clean(result.stdout.splitlines()[0])}
    return results


def main(argv=None):
    args = parse_args(argv)
    start = time.monotonic()
    event = {"id": dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"), "command": args.command,
             "status": "PASS", "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        if args.command == "doctor":
            event["tools"] = doctor()
            if not all(tool["available"] for tool in event["tools"].values()):
                raise MediaError("BLOCKED_ENV", "required_tool_missing")
        else:
            if args.command in {"probe", "download"}:
                remote_url(args.url)
                event["url"] = public_url(args.url)
                event.update(kind=args.kind, format_selector=FORMATS[args.kind])
            if args.command == "download":
                event["parameters"] = {k: getattr(args, k) for k in ("run_id", "role", "purpose", "max_bytes")}
                event["tools"] = doctor()
                if not 0 < args.max_bytes <= CONFIG["single_file_limit_bytes"]:
                    raise MediaError("BLOCKED_INPUT", "invalid_max_bytes")
                run_directory(args.run_id)
                if args.role != "reference" and args.kind != "audio":
                    raise MediaError("BLOCKED_INPUT", "target_source_roles_require_audio")
                if args.role != "reference" and (ROOT / "data" / args.role / f"{args.run_id}.wav").exists():
                    raise MediaError("BLOCKED_INPUT", "data_destination_exists")
            with session(args) as snapshot:
                event["cookie_mode"] = "private_snapshot" if snapshot else "public"
                if args.command == "search":
                    event.update(platform=args.platform, query=args.query, results=search(args, snapshot))
                    if not event["results"]:
                        event["status"] = "EMPTY"
                else:
                    info = extract(args.url, snapshot, kind=args.kind)
                    event["media"] = summary(info)
                    if args.command == "probe":
                        event["streams"] = [{k: s.get(k) for k in ("format_id", "ext", "protocol", "filesize", "filesize_approx", "acodec", "vcodec", "height")}
                                            for s in selected_streams(info)]
                    else:
                        directory, rows, receipt = transfer(info, args, snapshot, event)
                        event["output"] = finish_media(directory, rows, args)
                        (directory / "receipt.json").write_text(json.dumps({**event, "media": receipt}, ensure_ascii=False, indent=2) + "\n")
    except MediaError as error:
        event.update(status=error.status, reason=error.reason)
    except guard.CookieGuardError:
        event.update(status="BLOCKED_COOKIE", reason="readonly_cookie_guard_failed")
    except bili_search.ApiResponseError as error:
        event.update(status="BLOCKED_ACCESS", reason=f"bilibili_{error.stage}_code_{error.code}")
    except bili_search.SearchRequestError as error:
        event.update(status="BLOCKED_ENV" if error.permission_denied else "RETRY_REQUIRED",
                     reason=f"bilibili_{error.stage}_http_{error.http_status}")
    except urllib.error.HTTPError as error:
        event.update(status="BLOCKED_ACCESS" if error.code in {401, 403, 412, 429} else "RETRY_REQUIRED", reason=f"http_{error.code}")
        error.close()
    except (urllib.error.URLError, TimeoutError, subprocess.TimeoutExpired):
        event.update(status="RETRY_REQUIRED", reason="transport_or_process_timeout")
    except (FileNotFoundError, PermissionError):
        event.update(status="BLOCKED_ENV", reason="tool_or_path_unavailable")
    except KeyboardInterrupt:
        event.update(status="INTERRUPTED", reason="check_retained_download_reservations")
    except Exception as error:
        # Never persist raw exceptions, info JSON, signed URLs, headers or cookie rows.
        event.update(status="FAILED", reason=type(error).__name__)
    event["elapsed_seconds"] = round(time.monotonic() - start, 3)
    folder = ROOT / "reports/evidence/media-events"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / (event["id"] + ".json")).open("x") as handle:
        json.dump(event, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    if event["status"] not in {"PASS", "EMPTY"}:
        errors = ROOT / "logs/media"
        errors.mkdir(parents=True, exist_ok=True)
        with (errors / (event["id"] + ".json")).open("x") as handle:
            json.dump(event, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(json.dumps(event, ensure_ascii=False, indent=2))
    return 0 if event["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
