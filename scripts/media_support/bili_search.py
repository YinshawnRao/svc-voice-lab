#!/usr/bin/env python3
"""Bilibili WBI search helpers adapted from cc-media.

Use scripts/media.py rather than invoking this module. The public entry point
passes a private cookie snapshot or an anonymous opener. Importing this module
does not inspect credentials; cookie jars are never saved by these helpers.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import http.client
import http.cookiejar
import json
import re
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
MIXIN_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]

EXIT_EMPTY = 1
EXIT_COOKIE_PRECHECK = 2
EXIT_API_ERROR = 3
EXIT_RESPONSE_INVALID = 4
EXIT_REQUEST_FAILED = 5


class BiliSearchError(Exception):
    """Base class for safe, classified remote-search failures."""


class ApiResponseError(BiliSearchError):
    def __init__(self, stage: str, code: int):
        super().__init__(f"{stage}:{code}")
        self.stage = stage
        self.code = code


class ResponseParseError(BiliSearchError):
    def __init__(self, stage: str):
        super().__init__(stage)
        self.stage = stage


class SearchRequestError(BiliSearchError):
    def __init__(self, stage: str, *, http_status: int | None = None,
                 permission_denied: bool = False):
        super().__init__(stage)
        self.stage = stage
        self.http_status = http_status
        self.permission_denied = permission_denied


def default_cookie_path(repo_root: Path | None = None) -> Path:
    root = REPO_ROOT if repo_root is None else Path(repo_root)
    return root / "all_cookies.txt"


def validate_cookie_jar(path: Path | str) -> Path:
    jar = Path(path).expanduser()
    if "=" in str(jar):
        raise ValueError(
            "cookie jar 路径不能包含 '='；命令行消费者可能把它误判为内联数据"
        )
    if not jar.is_file():
        raise ValueError(f"cookie jar 不存在: {jar}")
    mode = stat.S_IMODE(jar.stat().st_mode)
    if mode & 0o077:
        raise ValueError(
            "cookie jar 权限不符合要求；canonical 只允许用户本人维护，"
            "请由用户检查文件权限"
        )
    return jar


def load_cookie_jar(path: Path | str) -> http.cookiejar.MozillaCookieJar:
    jar_path = validate_cookie_jar(path)
    jar = http.cookiejar.MozillaCookieJar(str(jar_path))
    # stdlib MozillaCookieJar 原生识别 Netscape #HttpOnly_，并保留 HTTPOnly rest。
    jar.load(ignore_discard=True, ignore_expires=False)
    return jar


def build_opener(path: Path | str):
    jar = load_cookie_jar(path)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [
        ("User-Agent", UA),
        ("Referer", "https://www.bilibili.com/"),
    ]
    return opener


def get_json(url: str, opener, *, stage: str = "response"):
    try:
        with opener.open(url, timeout=20) as response:
            return json.load(response)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        # Never attach the response body to an error: API/edge responses can
        # contain account or anti-bot details that must not reach CLI output.
        # ``json`` may also raise a plain ValueError for oversized integer
        # tokens, so classify that as malformed remote data instead of
        # leaking a traceback and stopping the surrounding goal.
        raise ResponseParseError(stage) from None
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise SearchRequestError(stage, http_status=status) from None
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        http.client.HTTPException,
    ) as error:
        reason = error.reason if isinstance(error, urllib.error.URLError) else error
        denied = isinstance(reason, OSError) and reason.errno in (errno.EACCES, errno.EPERM)
        raise SearchRequestError(stage, permission_denied=denied) from None


def api_data(payload, *, stage: str) -> dict:
    if not isinstance(payload, dict):
        raise ResponseParseError(stage)
    code = payload.get("code")
    if isinstance(code, bool) or not isinstance(code, int):
        raise ResponseParseError(stage)
    if code != 0:
        # Bilibili's numeric business code is safe and useful for recovery;
        # its free-form message and the original payload are deliberately not
        # retained or printed.
        raise ApiResponseError(stage, code)
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ResponseParseError(stage)
    return data


def mixin_key(original: str) -> str:
    return "".join(original[index] for index in MIXIN_TAB)[:32]


def get_keys(opener) -> tuple[str, str]:
    nav = get_json(
        "https://api.bilibili.com/x/web-interface/nav",
        opener,
        stage="nav",
    )
    data = api_data(nav, stage="nav")
    wbi = data.get("wbi_img")
    if not isinstance(wbi, dict):
        raise ResponseParseError("nav")
    image_url = wbi.get("img_url")
    sub_url = wbi.get("sub_url")
    if not isinstance(image_url, str) or not isinstance(sub_url, str):
        raise ResponseParseError("nav")
    image_key = image_url.rsplit("/", 1)[-1].split(".", 1)[0]
    sub_key = sub_url.rsplit("/", 1)[-1].split(".", 1)[0]
    if not re.fullmatch(r"[0-9a-fA-F]{32}", image_key) or not re.fullmatch(
        r"[0-9a-fA-F]{32}", sub_key
    ):
        raise ResponseParseError("nav")
    return image_key, sub_key


def enc_wbi(params: dict, image_key: str, sub_key: str) -> dict:
    mixin = mixin_key(image_key + sub_key)
    signed = {**params, "wts": round(time.time())}
    signed = dict(sorted(signed.items()))
    signed = {
        key: "".join(char for char in str(value) if char not in "!'()*")
        for key, value in signed.items()
    }
    query = urllib.parse.urlencode(signed)
    signed["w_rid"] = hashlib.md5((query + mixin).encode()).hexdigest()
    return signed


def result_line(result: object) -> str:
    if not isinstance(result, dict):
        raise ResponseParseError("search")
    fields = {
        "bvid": result.get("bvid"),
        "duration": result.get("duration"),
        "author": result.get("author"),
        "title": result.get("title"),
    }
    if not all(isinstance(value, str) for value in fields.values()):
        raise ResponseParseError("search")
    fields["title"] = re.sub("<[^>]+>", "", fields["title"])
    for key, value in fields.items():
        # Collapse line breaks and remove control/ANSI characters so remote
        # fields cannot forge additional CLI status lines.
        printable = "".join(char if char.isprintable() else " " for char in value)
        fields[key] = " ".join(printable.split())
    return (
        f"{fields['bvid'][:64]} | {fields['duration'][:32]} | "
        f"{fields['author'][:160]} | {fields['title'][:240]}"
    )


def search(
    keyword: str,
    n: int = 8,
    *,
    cookie_path: Path | str | None = None,
    opener=None,
) -> list[dict]:
    if n <= 0:
        raise ValueError("result count must be positive")
    if opener is None:
        selected = default_cookie_path() if cookie_path is None else cookie_path
        opener = build_opener(selected)

    image_key, sub_key = get_keys(opener)
    params = enc_wbi(
        {"search_type": "video", "keyword": keyword, "page": 1},
        image_key,
        sub_key,
    )
    url = (
        "https://api.bilibili.com/x/web-interface/wbi/search/type?"
        + urllib.parse.urlencode(params)
    )
    payload = get_json(url, opener, stage="search")
    data = api_data(payload, stage="search")
    results = data.get("result")
    if not isinstance(results, list):
        raise ResponseParseError("search")
    # Only an actual empty list is an EMPTY result. Missing/null/malformed
    # result fields are response failures and must not be reported as no hits.
    if not results:
        return []
    selected_results = results[:n]
    for result in selected_results:
        result_line(result)  # validate without printing remote fields
    return selected_results

