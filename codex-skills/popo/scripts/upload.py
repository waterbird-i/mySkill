 #!/usr/bin/env python3
"""One-shot upload to pop platform via /works/upload (api subdomain).

Creates a work, its first version, uploads all files, and publishes — all in
a single multipart/form-data request. Supports both first-time deployments
and re-deployments (via --previous-slug).

Auth: automatically reads the local UUAP ugate token from
~/.config/uuap/.eac_ugate_token_<username>. Falls back to --token if provided.

Usage:
  python upload.py --title <title> --slug <slug> --base <dir> [--entry <path>]

Examples:
  python upload.py --title "My App" --slug my-app --base ./dist
  python upload.py --title "My App" --slug my-app --previous-slug my-app --base ./dist
"""

import argparse
import json
import mimetypes
import os
import ssl
import sys
import urllib.request
import uuid
from pathlib import Path

DEFAULT_API_BASE = "https://api.pop.baidu-int.com"
DEFAULT_API_HOST = "api.pop.baidu-int.com"
DEFAULT_GLOBS = ["**/*"]


def get_ugate_token():
    """Read the local UUAP ugate token file. Returns (token, username) or (None, None)."""
    uuap_dir = Path.home() / ".config" / "uuap"
    if not uuap_dir.exists():
        return None
    for f in uuap_dir.glob(".eac_ugate_token_*"):
        try:
            data = json.loads(f.read_text())
            return data.get("token")
        except (json.JSONDecodeError, OSError):
            continue
    return None


def collect_files(base_dir, globs, excludes):
    """Collect files matching any glob, excluding hidden files and excludes."""
    matched = set()
    for pattern in globs:
        for p in base_dir.glob(pattern):
            if p.is_file():
                rel = p.relative_to(base_dir)
                if any(part.startswith(".") for part in rel.parts):
                    continue
                matched.add(rel)

    if excludes:
        filtered = set()
        for rel in matched:
            if not any(rel.match(pat) for pat in excludes):
                filtered.add(rel)
        return sorted(filtered)
    return sorted(matched)


def build_multipart(fields, files):
    """Build a multipart/form-data body. Returns (body_bytes, content_type)."""
    boundary = f"----pop{uuid.uuid4().hex}"
    crlf = b"\r\n"
    parts = []

    for name, value in fields.items():
        parts.append(f"--{boundary}".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"'.encode()
        )
        parts.append(b"")
        parts.append(str(value).encode())

    for rel_path, data in files:
        mime = mimetypes.guess_type(rel_path)[0] or "application/octet-stream"
        parts.append(f"--{boundary}".encode())
        parts.append(
            (
                f'Content-Disposition: form-data; name="files"; '
                f'filename="{rel_path}"'
            ).encode()
        )
        parts.append(f"Content-Type: {mime}".encode())
        parts.append(b"")
        parts.append(data)

    parts.append(f"--{boundary}--".encode())
    parts.append(b"")

    body = crlf.join(parts)
    return body, f"multipart/form-data; boundary={boundary}"


def main():
    """Parse command arguments and upload files to the pop platform."""
    parser = argparse.ArgumentParser(
        description="One-shot deploy to pop via /works/upload (api subdomain)"
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--previous-slug", default=None,
                        help="Set to slug for re-deploy, or a different slug to archive old work")
    parser.add_argument("--token", default=None,
                        help="Override token. If not provided, reads local ugate token automatically.")
    parser.add_argument("--base", default=".")
    parser.add_argument("--entry", default="index.html",
                        help="Entry path relative to --base")
    parser.add_argument("--glob", action="append", dest="globs")
    parser.add_argument("--exclude", action="append", dest="excludes")
    parser.add_argument("--visibility", default="private")
    parser.add_argument("--source", default="comate")
    parser.add_argument("--type", dest="work_type", default="website")
    parser.add_argument("--artifact-kind", default="static_site")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument(
        "--api-host",
        default=DEFAULT_API_HOST,
        help=(
            "Host header to send. Must start with 'api.' so isApiRequest() "
            "matches. Default 'api.localhost' for local pnpm dev."
        ),
    )
    args = parser.parse_args()

    # Resolve token: --token > local ugate token
    token = args.token
    token_header = "x-access-token"
    if not token:
        token = get_ugate_token()
        token_header = "x-ugate-token"
    if not token:
        print("Error: no token provided and no local ugate token found in ~/.config/uuap/",
              file=sys.stderr)
        sys.exit(1)

    base_dir = Path(args.base).resolve()
    if not base_dir.exists():
        print(f'Error: base directory "{args.base}" does not exist',
              file=sys.stderr)
        sys.exit(1)

    files_rel = collect_files(
        base_dir, args.globs or DEFAULT_GLOBS, args.excludes or []
    )
    if not files_rel:
        print("No files matched the given glob patterns.", file=sys.stderr)
        sys.exit(1)

    entry_norm = args.entry.replace("\\", "/")
    if not any(str(f).replace("\\", "/") == entry_norm for f in files_rel):
        print(
            f'Error: entry "{entry_norm}" not found in collected files',
            file=sys.stderr,
        )
        sys.exit(1)

    file_payload = []
    total_size = 0
    for rel in files_rel:
        rel_str = str(rel).replace("\\", "/")
        data = (base_dir / rel).read_bytes()
        total_size += len(data)
        file_payload.append((rel_str, data))

    print(
        f"Uploading {len(file_payload)} file(s), {total_size} bytes "
        f"to {args.api_base}/works/upload (Host: {args.api_host}) ..."
    )

    fields = {
        "title": args.title,
        "slug": args.slug,
        "visibility": args.visibility,
        "source": args.source,
        "type": args.work_type,
        "artifactKind": args.artifact_kind,
        "entryPath": entry_norm,
    }
    if args.previous_slug:
        fields["previousSlug"] = args.previous_slug

    body, content_type = build_multipart(fields, file_payload)

    req = urllib.request.Request(
        f"{args.api_base}/works/upload",
        data=body,
        method="POST",
        headers={
            "Content-Type": content_type,
            token_header: token,
        },
    )
    # urllib drops a regular "Host" header; use add_unredirected_header so it
    # actually goes on the wire. The api subdomain check inspects this value.
    req.add_unredirected_header("Host", args.api_host)

    ctx = ssl.create_default_context()
    # Disable SSL verification: internal network uses self-signed certificates
    # that are not in the system CA bundle. Safe for intranet-only traffic.
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        if isinstance(e, urllib.error.HTTPError):
            body_text = e.read().decode("utf-8", errors="replace")
            print(f"HTTP {e.code}: {body_text}", file=sys.stderr)
            sys.exit(1)
        # Network error — retry once
        print("Network error, retrying...", file=sys.stderr)
        req2 = urllib.request.Request(
            f"{args.api_base}/works/upload",
            data=body,
            method="POST",
            headers={
                "Content-Type": content_type,
                token_header: token,
            },
        )
        req2.add_unredirected_header("Host", args.api_host)
        try:
            with urllib.request.urlopen(req2, context=ctx) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e2:
            body_text = e2.read().decode("utf-8", errors="replace")
            print(f"HTTP {e2.code}: {body_text}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e2:
            print(f"Network error: {e2.reason}", file=sys.stderr)
            sys.exit(1)

    print(json.dumps(payload, ensure_ascii=False))
    if not payload.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
