# Python開発テンプレート

このリポジトリは、Claude CodeとDevContainerを使用したPython開発環境のテンプレートです。

## 概要

このプロジェクトは、以下の特徴を持つモダンなPython開発環境を提供します：

- **DevContainer**: VS Codeで一貫した開発環境を構築
- **Claude Code**: AIペアプログラミングアシスタント統合
- **最新のPythonツール**: uv、ruff、pyrightを使用した高速で効率的な開発

## セットアップ

### 前提条件

- VS Code
- Docker Desktop
- Dev Containers拡張機能

### 使い方

1. このリポジトリをクローンまたはテンプレートとして使用
2. VS Codeでフォルダを開く
3. 「Reopen in Container」の通知をクリック（または、コマンドパレットから「Dev Containers: Reopen in Container」を実行）
4. コンテナのビルドが完了するまで待つ
5. ターミナルで `claude auth login` を実行してClaude Codeを認証

## 開発コマンド

コンテナ内で使用できる便利なエイリアス：

- `run` - メインのPythonスクリプトを実行
- `test` - すべてのテストを実行
- `lint` - コードの品質チェック
- `format` - コードの自動フォーマット
- `typecheck` - 型チェックを実行
- `cc` - Claude Codeコマンドのショートカット

## プロジェクト構成

```text
.
├── .devcontainer/       # DevContainer設定
│   ├── devcontainer.json
│   └── Dockerfile
├── .claude/            # Claude Code設定
│   └── settings.json
├── CLAUDE.md          # Claude Code用のプロジェクトガイド
└── README.md          # このファイル
```

## 使用技術

- **Python 3.13**: プログラミング言語
- **Node.js 20.x**: JavaScript実行環境（Claude Code用）
- **uv**: 高速なPythonパッケージマネージャー
- **ruff**: 高速なPythonリンター・フォーマッター
- **pyright**: 静的型チェッカー
- **pytest**: テストフレームワーク
- **Claude Code**: AIペアプログラミングツール

## カスタマイズ

### 依存関係の追加

```bash
uv add <パッケージ名>
```

### 新しいプロジェクトの開始

1. `main.py` を作成して、プロジェクトのエントリーポイントを定義
2. `pyproject.toml` を作成して、プロジェクトの設定と依存関係を管理
3. `tests/` ディレクトリにテストを追加

## ライセンス

このテンプレートはパブリックドメインです。自由に使用・改変してください。
