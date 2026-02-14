"""
X API ブックマーク・いいね取得テストスクリプト

使い方:
  1. cp .env.example .env
  2. .env に CLIENT_ID, CLIENT_SECRET を記入
  3. uv run python src/x_api_test.py
"""

import hashlib
import base64
import secrets
import urllib.parse
import webbrowser
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import requests
from dotenv import load_dotenv

# .env をプロジェクトルートから読み込む
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CLIENT_ID = os.getenv("X_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("X_CLIENT_SECRET", "")

REDIRECT_URI = "http://localhost:3000/callback"
SCOPES = "tweet.read users.read bookmark.read like.read offline.access"

# PKCE
code_verifier = secrets.token_urlsafe(64)[:128]
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()
state = secrets.token_urlsafe(32)

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    """ローカルサーバーでOAuthコールバックを受け取る"""

    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "✅ 認証成功！このページを閉じてターミナルに戻ってください。".encode()
            )
        else:
            error = params.get("error", ["unknown"])[0]
            desc = params.get("error_description", [""])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"❌ エラー: {error} - {desc}".encode())
            print(f"\n❌ 認証エラー: {error} - {desc}")

    def log_message(self, format, *args):
        pass


def step1_authorize():
    """ブラウザで認証ページを開き、コールバックで認証コードを受け取る"""
    print("=" * 60)
    print("Step 1: ブラウザで X の認証ページを開きます")
    print("=" * 60)

    auth_url = (
        f"https://x.com/i/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"scope={urllib.parse.quote(SCOPES)}&"
        f"state={state}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )

    print(f"\n以下のURLをブラウザで開いてください:\n")
    print(auth_url)
    print(f"\n自動でブラウザを開きます...")
    webbrowser.open(auth_url)

    print(f"\nコールバック待機中 (http://localhost:3000/callback) ...")
    server = HTTPServer(("localhost", 3000), CallbackHandler)
    server.handle_request()

    if not auth_code:
        print("❌ 認証コードを取得できませんでした。")
        sys.exit(1)

    print(f"✅ 認証コード取得成功!")
    return auth_code


def step2_get_token(code):
    """認証コードをアクセストークンに交換"""
    print("\n" + "=" * 60)
    print("Step 2: アクセストークンを取得します")
    print("=" * 60)

    resp = requests.post(
        "https://api.x.com/2/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if resp.status_code != 200:
        print(f"❌ トークン取得失敗: {resp.status_code}")
        print(resp.text)
        sys.exit(1)

    token_data = resp.json()
    access_token = token_data["access_token"]
    print(f"✅ アクセストークン取得成功!")
    print(f"   スコープ: {token_data.get('scope', 'N/A')}")
    print(f"   有効期限: {token_data.get('expires_in', 'N/A')} 秒")

    if "refresh_token" in token_data:
        print(f"   リフレッシュトークン: あり")

    return access_token


def step3_get_me(token):
    """自分のユーザー情報を取得"""
    print("\n" + "=" * 60)
    print("Step 3: 自分のユーザー情報を取得 (GET /2/users/me)")
    print("=" * 60)

    resp = requests.get(
        "https://api.x.com/2/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    print(f"\n   ステータスコード: {resp.status_code}")
    print_rate_limit(resp)

    if resp.status_code == 200:
        data = resp.json()
        user = data["data"]
        print(f"   ✅ ユーザー名: @{user['username']}")
        print(f"   ✅ 表示名: {user['name']}")
        print(f"   ✅ ユーザーID: {user['id']}")
        return user["id"]
    else:
        print(f"   ❌ エラー: {resp.text}")
        return None


def step4_test_bookmarks(token, user_id):
    """ブックマーク取得テスト"""
    print("\n" + "=" * 60)
    print(f"Step 4: ブックマーク取得テスト")
    print(f"   GET /2/users/{user_id}/bookmarks?max_results=5")
    print("=" * 60)

    resp = requests.get(
        f"https://api.x.com/2/users/{user_id}/bookmarks",
        params={
            "max_results": 5,
            "tweet.fields": "created_at,author_id,text",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    print(f"\n   ステータスコード: {resp.status_code}")
    print_rate_limit(resp)
    print_response(resp, "ブックマーク")


def step5_test_likes(token, user_id):
    """いいね取得テスト"""
    print("\n" + "=" * 60)
    print(f"Step 5: いいね取得テスト")
    print(f"   GET /2/users/{user_id}/liked_tweets?max_results=5")
    print("=" * 60)

    resp = requests.get(
        f"https://api.x.com/2/users/{user_id}/liked_tweets",
        params={
            "max_results": 5,
            "tweet.fields": "created_at,author_id,text",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    print(f"\n   ステータスコード: {resp.status_code}")
    print_rate_limit(resp)
    print_response(resp, "いいね")


def print_response(resp, label):
    """レスポンスを整形して表示"""
    if resp.status_code == 200:
        data = resp.json()
        posts = data.get("data", [])
        print(f"   ✅ {label}取得成功! ({len(posts)} 件)")
        for i, post in enumerate(posts, 1):
            text = post["text"][:80] + ("..." if len(post["text"]) > 80 else "")
            print(f"\n   [{i}] ID: {post['id']}")
            print(f"       {text}")
    elif resp.status_code == 429:
        print(f"   ❌ レートリミット (429) - PPUプランでの既知の問題の可能性あり")
        print(f"   レスポンス: {resp.text}")
    else:
        print(f"   ❌ エラー ({resp.status_code}): {resp.text}")


def print_rate_limit(resp):
    """レートリミットヘッダーを表示"""
    limit = resp.headers.get("x-rate-limit-limit", "N/A")
    remaining = resp.headers.get("x-rate-limit-remaining", "N/A")
    reset = resp.headers.get("x-rate-limit-reset", "N/A")
    print(f"   レートリミット: {remaining}/{limit} (リセット: {reset})")


def main():
    print()
    print("🔍 X API ブックマーク・いいね取得テスト")
    print("=" * 60)

    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ X_CLIENT_ID / X_CLIENT_SECRET が未設定です!")
        print()
        print("   1. cp .env.example .env")
        print("   2. .env を編集して値を入力")
        print("   3. 再実行")
        sys.exit(1)

    code = step1_authorize()
    token = step2_get_token(code)
    user_id = step3_get_me(token)

    if user_id:
        step4_test_bookmarks(token, user_id)
        step5_test_likes(token, user_id)

    print("\n" + "=" * 60)
    print("テスト完了!")
    print("=" * 60)


if __name__ == "__main__":
    main()
