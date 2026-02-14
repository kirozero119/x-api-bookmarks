# x-api-bookmarks

X API（従量課金 / Pay-Per-Use）で、自分の **ブックマーク** と **いいね** を取得するスクリプト。

2026年2月に正式ローンチされた Pay-Per-Use モデルを使い、**$5（約750円）から**ブックマーク・いいねのAPI取得が可能になりました。

📝 **解説記事**: [【2026年2月】X APIが従量課金に！$5で自分のブックマーク・いいねをAPI取得してみた](https://qiita.com/YOUR_USERNAME/items/ARTICLE_ID)

## できること

- OAuth 2.0 PKCE 認証によるアクセストークンの自動取得
- 自分のブックマーク一覧の取得
- 自分のいいね一覧の取得

## 事前準備

### 1. Developer Console でアプリを作成

https://console.x.com にアクセスしてアプリを作成します。

### 2. 認証設定

アプリの認証設定で以下を設定:

| 項目 | 値 |
|---|---|
| アプリの権限 | 読む |
| アプリの種類 | ウェブアプリ、自動化アプリまたはボット |
| コールバックURI | `http://localhost:3000/callback` |
| ウェブサイトURL | `https://example.com` |

### 3. クレジット購入

Console の Billing から最低 $5 を購入してください。

## セットアップ

```bash
git clone https://github.com/YOUR_USERNAME/x-api-bookmarks.git
cd x-api-bookmarks

# 依存パッケージのインストール
uv sync

# 環境変数の設定
cp .env.example .env
```

`.env` を編集して、OAuth 2.0 の **Client ID** と **Client Secret** を記入:

```
X_CLIENT_ID=あなたのClient ID
X_CLIENT_SECRET=あなたのClient Secret
```

> ⚠️ **API Key / API Key Secret ではなく、OAuth 2.0 のセクションにある Client ID / Client Secret を使用してください。**

## 実行

```bash
uv run python src/x_api_test.py
```

ブラウザが自動で開きます。X にログインして「アプリを認証」をクリックすると、自動でテストが実行されます。

## 実行結果の例

```
✅ アクセストークン取得成功!
   スコープ: offline.access bookmark.read like.read users.read tweet.read

✅ ブックマーク取得成功! (5 件)
   [1] AIエージェントがWebサイトと構造化された方法でやり取りするための...
   [2] これおもしろい "Hono on Node.js 最速レスポンス選手権"...

✅ いいね取得成功! (5 件)
   [1] ClaudeのSkillsが教えてくれたことは...
```

## 料金目安

| 操作 | 単価 | $5 でできる回数 |
|---|---|---|
| ポスト読み取り (GET) | $0.005/件 | 1,000件 |
| ポスト作成 (POST) | $0.01/件 | 500件 |

同日内の同一リソースへの重複リクエストは課金されません。

## トラブルシューティング

| エラー | 原因と対策 |
|---|---|
| `401 Unauthorized` | Client ID/Secret が間違っている。OAuth 2.0 の値を使っているか確認 |
| `402 CreditsDepleted` | クレジット未購入。Console の Billing から $5 を購入 |
| `429 Too Many Requests` | レートリミット超過。数分待って再試行 |
| ブラウザで「問題が発生しました」 | コールバック URI が `http://localhost:3000/callback` と一致しているか確認 |

## ライセンス

MIT
