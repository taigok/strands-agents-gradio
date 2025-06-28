"""基本的なMCPツールの実装"""

import math
import re
from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource


# MCPサーバーの初期化
mcp = FastMCP("Basic Tools Server")


@mcp.tool()
def calculate(expression: str) -> str:
    """安全な数式計算を実行します

    Args:
        expression: 計算する数式 (例: "2 + 3 * 4", "sqrt(16)", "sin(pi/2)")

    Returns:
        計算結果の文字列
    """
    try:
        # 安全な関数のみを許可
        safe_dict = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }

        # 危険な文字列をチェック
        dangerous_patterns = [
            r"__.*__",
            r"import",
            r"exec",
            r"eval",
            r"open",
            r"file",
            r"input",
            r"raw_input",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return f"エラー: 危険な操作が検出されました: {pattern}"

        result = eval(expression, safe_dict, {})
        return f"{expression} = {result}"

    except Exception as e:
        return f"計算エラー: {str(e)}"


@mcp.tool()
def get_current_time(timezone_name: str = "Asia/Tokyo") -> str:
    """現在の日時を取得します

    Args:
        timezone_name: タイムゾーン名 (デフォルト: Asia/Tokyo)

    Returns:
        現在の日時の文字列
    """
    try:
        import zoneinfo

        tz = zoneinfo.ZoneInfo(timezone_name)
        now = datetime.now(tz)
        return f"現在時刻 ({timezone_name}): {now.strftime('%Y年%m月%d日 %H:%M:%S %Z')}"
    except Exception:
        # フォールバック: UTC
        now = datetime.now(timezone.utc)
        return f"現在時刻 (UTC): {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"


@mcp.tool()
def process_text(text: str, operation: str = "count_words") -> str:
    """テキスト処理操作を実行します

    Args:
        text: 処理するテキスト
        operation: 実行する操作 ("count_words", "count_chars", "to_upper", "to_lower", "reverse")

    Returns:
        処理結果の文字列
    """
    try:
        if operation == "count_words":
            word_count = len(text.split())
            return f"単語数: {word_count}"

        elif operation == "count_chars":
            char_count = len(text)
            char_count_no_spaces = len(text.replace(" ", ""))
            return f"文字数: {char_count} (スペース含む), {char_count_no_spaces} (スペース除く)"

        elif operation == "to_upper":
            return text.upper()

        elif operation == "to_lower":
            return text.lower()

        elif operation == "reverse":
            return text[::-1]

        else:
            return f"未対応の操作: {operation}. 対応操作: count_words, count_chars, to_upper, to_lower, reverse"

    except Exception as e:
        return f"テキスト処理エラー: {str(e)}"


@mcp.tool()
async def fetch_url_content(url: str, max_length: int = 2000) -> str:
    """URLからコンテンツを取得します

    Args:
        url: 取得するURL
        max_length: 最大文字数 (デフォルト: 2000)

    Returns:
        取得したコンテンツの文字列
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            content = response.text
            if len(content) > max_length:
                content = content[:max_length] + "..."

            return f"URL: {url}\n状態: {response.status_code}\n内容:\n{content}"

    except Exception as e:
        return f"URL取得エラー: {str(e)}"


@mcp.resource("mcp://tools/help")
async def get_tools_help() -> Resource:
    """利用可能なツールのヘルプ情報を提供します"""
    help_content = """
# 利用可能なMCPツール

## 計算ツール
- **calculate(expression)**: 安全な数式計算
  - 例: calculate("2 + 3 * 4")
  - 例: calculate("sqrt(16)")

## 日時ツール
- **get_current_time(timezone_name)**: 現在時刻取得
  - 例: get_current_time("Asia/Tokyo")
  - 例: get_current_time("UTC")

## テキスト処理ツール
- **process_text(text, operation)**: テキスト処理
  - count_words: 単語数カウント
  - count_chars: 文字数カウント
  - to_upper: 大文字変換
  - to_lower: 小文字変換
  - reverse: 文字列反転

## ウェブツール
- **fetch_url_content(url, max_length)**: URL内容取得
  - 例: fetch_url_content("https://example.com")
"""

    return Resource(
        uri="mcp://tools/help",
        name="Tools Help",
        description="利用可能なツールのヘルプ情報",
        mimeType="text/markdown",
        text=help_content,
    )


if __name__ == "__main__":
    # MCPサーバーとして実行
    mcp.run()
