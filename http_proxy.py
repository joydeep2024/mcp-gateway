import sys
from urllib.parse import urljoin

from flask import Flask, request, Response
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ==== CONFIGURATION ====
# Change this to the server you want to forward to
TARGET_BASE = os.getenv("TARGET_BASE")


def print_http_request(req):
    """Pretty-print the incoming HTTP request."""
    print("\n" + "=" * 80)
    print(">>> Incoming Request")
    print(f"{req.method} {req.full_path or req.path} HTTP/1.1")
    for header, value in req.headers.items():
        print(f"{header}: {value}")
    body = req.get_data()
    if body:
        print("\n--- Request Body ---")
        try:
            print(body.decode("utf-8"))
        except UnicodeDecodeError:
            # Fallback for non-text bodies
            print(body)
    else:
        print("\n(no request body)")
    print("=" * 80 + "\n", flush=True)


def print_http_response(resp):
    """Pretty-print the HTTP response from the target."""
    print("\n" + "-" * 80)
    print("<<< Response From Target")
    print(f"HTTP/1.1 {resp.status_code} {resp.reason}")
    for header, value in resp.headers.items():
        print(f"{header}: {value}")
    body = resp.content
    if body:
        print("\n--- Response Body ---")
        # Be careful with binary content
        content_type = resp.headers.get("Content-Type", "")
        if "text" in content_type or "json" in content_type or "xml" in content_type:
            try:
                print(body.decode("utf-8"))
            except UnicodeDecodeError:
                print(body)
        else:
            # For non-text, just show length
            print(f"[{len(body)} bytes]")
    else:
        print("\n(no response body)")
    print("-" * 80 + "\n", flush=True)


def filter_headers(headers):
    """
    Remove or adjust hop-by-hop headers that should not be forwarded.
    """
    excluded = {
        "Host",
        "Content-Length",
        "Transfer-Encoding",
        "Connection",
        "Keep-Alive",
        "Proxy-Authenticate",
        "Proxy-Authorization",
        "Upgrade",
        "Accept-Encoding",  # let requests handle it
    }
    return {k: v for k, v in headers.items() if k not in excluded}


ALL_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]


@app.route("/", defaults={"path": ""}, methods=ALL_METHODS)
@app.route("/<path:path>", methods=ALL_METHODS)
def proxy(path):
    # Log the incoming request
    print_http_request(request)

    # Build target URL
    target_url = urljoin(TARGET_BASE.rstrip("/") + "/", path)

    # Forward headers & body
    headers = filter_headers(request.headers)
    data = request.get_data()  # raw body
    params = request.args  # query parameters

    # Make the request to the target
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=params,
            data=data,
            cookies=request.cookies,
            allow_redirects=False,
            stream=True,
        )
    except requests.RequestException as e:
        # If the upstream is not reachable or errors out
        print(f"Error contacting target: {e}", file=sys.stderr, flush=True)
        return Response(
            "Error contacting target server.\n", status=502, mimetype="text/plain"
        )

    # Log the response from the target
    print_http_response(resp)

    # Build response to caller
    response_headers = filter_headers(resp.headers)
    # Flask Response requires a list of header tuples
    return Response(
        resp.content,
        status=resp.status_code,
        headers=list(response_headers.items()),
    )


if __name__ == "__main__":
    # Example: python proxy.py 5000
    port = 8080
    print(f"Starting proxy on http://0.0.0.0:{port} -> {TARGET_BASE}")
    app.run(host="0.0.0.0", port=port, debug=False)
