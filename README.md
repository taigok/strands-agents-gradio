# Strands Agents + Gradio チャットアプリケーション

Strands Agents SDK、Gradio、Model Context Protocol (MCP) を統合したインテリジェントなチャットインターフェースです。

## ✨ 特徴

- 🤖 **Strands Agents**: AWS Bedrock (Claude) を使用したAIチャット
- 🎨 **Gradio UI**: 美しく使いやすいWebインターフェース
- 🔧 **MCP統合**: Model Context Protocol サーバとの動的統合
- ⚙️ **管理機能**: MCPサーバの追加・削除をWebUIで操作
- 🛠️ **内蔵ツール**: 計算機、テキスト処理、時刻取得、URL取得

## 🚀 クイックスタート

### 1. 環境設定

```bash
# リポジトリをクローン
git clone <repository-url>
cd strands-agents-gradio

# 依存関係をインストール
uv sync
```

### 2. AWS認証情報の設定

`.env` ファイルを編集して、AWS認証情報を設定：

```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-west-2
```

### 3. AWS Bedrock設定

1. **IAMユーザー作成**: Bedrockアクセス権限を持つIAMユーザーを作成
2. **モデルアクセス**: AWS Bedrockコンソールでクロードモデルのアクセスを有効化
3. **リージョン確認**: `us-west-2` リージョンを使用（変更可能）

### 4. アプリケーション起動

```bash
uv run python main.py
```

ブラウザで http://localhost:7860 にアクセス

## 📱 使用方法

### チャット機能

以下のような質問でAIとチャットできます：

- `2 + 3 * 4 を計算して` → 数式計算
- `現在の時刻を教えて` → 現在時刻表示
- `「Hello World」の文字数を数えて` → テキスト処理
- `https://example.com の内容を教えて` → URL内容取得

### MCPサーバ管理

1. **⚙️ MCPサーバ管理** タブを開く
2. 新しいサーバを追加：
   - サーバ名、コマンド、引数、環境変数を入力
   - 例: AWS Documentation MCP Server
3. 設定済みサーバの表示・削除

### システム情報

**ℹ️ 情報** タブで以下を確認：
- 使用中のモデル情報
- 利用可能なMCPツール
- システム状態

## 🛠️ 内蔵MCPツール

| ツール | 機能 | 使用例 |
|--------|------|--------|
| **計算機** | 安全な数式計算 | `sqrt(16) + 2 * 3 を計算して` |
| **時刻取得** | 現在時刻表示（JST対応） | `現在の時刻を教えて` |
| **テキスト処理** | 文字数、大小文字変換等 | `「Hello」を大文字にして` |
| **URL取得** | ウェブページ内容取得 | `https://example.com の内容を要約して` |

## 📁 プロジェクト構成

```
strands-agents-gradio/
├── main.py              # メインアプリケーション
├── mcp_tools.py         # 内蔵MCPツール
├── config.json          # MCP設定ファイル
├── .env                 # 環境変数（要設定）
├── pyproject.toml       # プロジェクト設定
└── README.md           # このファイル
```

## 🔧 開発コマンド

```bash
# アプリケーション実行
uv run python main.py

# コード品質チェック
uv run ruff check
uv run ruff format

# 依存関係追加
uv add <package-name>

# MCPツール単体テスト
uv run python mcp_tools.py
```

## 🌐 外部MCPサーバの追加例

### AWS Documentation MCP Server

```
サーバ名: aws-docs
コマンド: uvx
引数: awslabs.aws-documentation-mcp-server@latest
環境変数: 
FASTMCP_LOG_LEVEL=INFO
AWS_DOCUMENTATION_PARTITION=aws
```

### その他のMCPサーバ

- [MCP Servers GitHub](https://github.com/modelcontextprotocol/servers)
- [Gradio MCP Examples](https://huggingface.co/spaces)

## ⚠️ トラブルシューティング

### "Unable to locate credentials"

```bash
# .envファイルを確認
cat .env

# AWS認証情報が正しく設定されているか確認
aws configure list  # AWS CLIがある場合
```

### Bedrockアクセスエラー

1. AWS Bedrockコンソールでモデルアクセスを確認
2. IAMユーザーのポリシーを確認
3. リージョンが正しく設定されているか確認

### MCPサーバ接続エラー

1. **ℹ️ 情報** タブでモデル情報を確認
2. サーバ設定（コマンド、引数）を確認
3. ログでエラー詳細を確認

## 🔗 関連リンク

- [Strands Agents](https://strandsagents.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Gradio](https://gradio.app/)
- [AWS Bedrock](https://aws.amazon.com/bedrock/)

## 📄 ライセンス

このプロジェクトはパブリックドメインです。自由に使用・改変してください。
