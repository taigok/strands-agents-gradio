"""Strands Agents + Gradio + MCP統合チャットアプリケーション"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Tuple

import gradio as gr
from strands import Agent

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPChatApp:
    """MCPサーバ統合チャットアプリケーション"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.agent = None
        self.mcp_servers = {}
        self._initialize_agent()

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # .envファイルから設定を読み込み
            import os
            from dotenv import load_dotenv

            load_dotenv()

            # アプリ設定を環境変数で上書き
            if "app_settings" not in config:
                config["app_settings"] = {}

            config["app_settings"].update(
                {
                    "title": os.getenv("APP_TITLE", "Strands Agents Chat"),
                    "description": os.getenv(
                        "APP_DESCRIPTION", "MCPサーバ統合チャット"
                    ),
                    "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "4000")),
                    "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.7")),
                }
            )

            return config

        except Exception as e:
            logger.error(f"設定ファイル読み込みエラー: {e}")
            # フォールバック設定も.envから読み込み
            import os
            from dotenv import load_dotenv

            load_dotenv()

            return {
                "mcpServers": {},
                "user_servers": [],
                "app_settings": {
                    "title": os.getenv("APP_TITLE", "Strands Agents Chat"),
                    "description": os.getenv(
                        "APP_DESCRIPTION", "MCPサーバ統合チャット"
                    ),
                    "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "4000")),
                    "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.7")),
                },
            }

    def _save_config(self):
        """設定ファイルを保存"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"設定ファイル保存エラー: {e}")

    def _initialize_agent(self):
        """Strands Agentを初期化"""
        try:
            # 環境変数から設定を読み込み
            import os
            from dotenv import load_dotenv

            load_dotenv()

            # AWS Bedrock設定を取得
            aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            aws_region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
            model_id = os.getenv(
                "BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"
            )
            temperature = float(os.getenv("MODEL_TEMPERATURE", "0.7"))

            if not aws_access_key or not aws_secret_key:
                logger.warning(
                    "AWS認証情報が設定されていません。.envファイルを確認してください。"
                )
                logger.info(
                    "AWS_ACCESS_KEY_ID と AWS_SECRET_ACCESS_KEY を設定してください。"
                )

            # BedrockModelを作成
            from strands.models import BedrockModel

            bedrock_model = BedrockModel(
                model_id=model_id, region_name=aws_region, temperature=temperature
            )

            # 内蔵MCPツールを作成
            tools = self._create_builtin_tools()

            # ステータス表示用の状態管理
            self.current_status = {"message": "", "tool_name": "", "thinking": False}

            # ストリーミング用のステータス管理
            self.stream_status_queue = []

            # Strands Agentイベント監視用コールバック（ストリーミング対応）
            def status_callback(**kwargs):
                try:
                    # ツール使用イベント
                    if "current_tool_use" in kwargs:
                        tool_info = kwargs["current_tool_use"]
                        tool_name = tool_info.get("name", "unknown")
                        self.current_status["tool_name"] = tool_name
                        self.current_status["message"] = f"🔧 ツール使用中: {tool_name}"
                        # ストリーミング用にキューに追加
                        self.stream_status_queue.append(
                            f"🔧 ツール「{tool_name}」を実行中..."
                        )
                        logger.info(f"🔧 Tool実行: {tool_name}")

                    # 思考プロセスイベント
                    elif "reasoning" in kwargs:
                        self.current_status["thinking"] = True
                        self.current_status["message"] = "🤔 思考中..."
                        self.stream_status_queue.append("🤔 AIが思考しています...")
                        logger.info("🤔 Agent思考中")

                    elif "reasoningText" in kwargs:
                        reasoning_text = (
                            kwargs["reasoningText"][:50] + "..."
                            if len(kwargs["reasoningText"]) > 50
                            else kwargs["reasoningText"]
                        )
                        self.current_status["message"] = f"🤔 思考中: {reasoning_text}"
                        self.stream_status_queue.append(f"🤔 思考: {reasoning_text}")
                        logger.info(f"🤔 Reasoning: {reasoning_text}")

                    # テキスト生成イベント
                    elif "data" in kwargs:
                        self.current_status["message"] = "✍️ 応答生成中..."
                        self.current_status["thinking"] = False
                        self.stream_status_queue.append("✍️ 応答を生成しています...")

                    # 完了イベント
                    elif "complete" in kwargs and kwargs["complete"]:
                        self.current_status["message"] = ""
                        self.current_status["thinking"] = False
                        logger.info("✅ Agent応答完了")

                except Exception as e:
                    logger.debug(f"Status callback処理エラー: {e}")

            # Strands Agentを作成（ステータス監視コールバック付き）
            self.agent = Agent(
                model=bedrock_model, tools=tools, callback_handler=status_callback
            )

            # 外部MCPサーバとの統合を試行
            self._setup_mcp_integration()

            logger.info("Strands Agent初期化完了")
            logger.info(f"リージョン: {aws_region}")
            logger.info(f"モデル: {model_id}")
            logger.info(f"温度: {temperature}")
            logger.info(f"内蔵ツール数: {len(tools)}")

        except Exception as e:
            logger.error(f"Agent初期化エラー: {e}")
            logger.error("AWS認証情報またはBedrock設定を確認してください。")
            self.agent = None

    def _create_builtin_tools(self):
        """内蔵MCPツールを作成"""
        from datetime import datetime, timezone
        import math
        import re
        from strands import tool

        @tool
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

        @tool
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

        @tool
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

        return [calculate, get_current_time, process_text]

    def _setup_mcp_integration(self):
        """MCPサーバとの統合設定"""
        try:
            # Strands AgentsのMCP機能を使用
            mcp_servers = self.config.get("mcpServers", {})

            for server_name, server_config in mcp_servers.items():
                try:
                    logger.info(f"MCPサーバ '{server_name}' の統合を試行中...")
                    # 実際のMCPサーバ統合はStrands Agentsのドキュメントに従って実装
                    # ここでは基本的な設定のみ
                    self.mcp_servers[server_name] = server_config

                except Exception as e:
                    logger.warning(f"MCPサーバ '{server_name}' の統合に失敗: {e}")

        except Exception as e:
            logger.error(f"MCP統合設定エラー: {e}")

    def chat_stream(self, message: str, _history: List[Tuple[str, str]]):
        """ストリーミングチャット処理（リアルタイムステータス表示付き）"""
        import time
        import threading

        try:
            start_time = time.time()
            logger.info(f"🚀 チャット開始: {message[:50]}...")

            # Strands Agentを使用してメッセージを処理
            if self.agent is None:
                yield "エラー: Agentが初期化されていません。"
                return

            # ステータスリセット
            self.current_status = {"message": "", "tool_name": "", "thinking": False}
            self.stream_status_queue = []

            # 処理開始ステータス表示
            yield "🚀 処理を開始しています..."
            time.sleep(0.3)

            # Agent呼び出し前
            pre_agent_time = time.time()
            logger.info(f"⏱️ Agent呼び出し前: {pre_agent_time - start_time:.2f}秒経過")

            # 思考中ステータス表示
            yield "🤔 AIが思考中です..."
            time.sleep(0.3)

            # Agent処理を別スレッドで実行してコールバックイベントを監視
            agent_response = None
            agent_error = None

            def run_agent():
                nonlocal agent_response, agent_error
                try:
                    agent_response = self.agent(message)
                except Exception as e:
                    agent_error = e

            # Agent実行開始
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.start()

            # ステータス監視とストリーミング表示
            last_status = ""
            while agent_thread.is_alive():
                # 新しいステータスがあれば表示
                if self.stream_status_queue:
                    status = self.stream_status_queue.pop(0)
                    if status != last_status:
                        yield status
                        last_status = status
                        time.sleep(0.5)
                else:
                    time.sleep(0.1)  # 短い間隔でチェック

            # Agent完了を待つ
            agent_thread.join()

            # エラーチェック
            if agent_error:
                raise agent_error

            # Agent呼び出し後
            post_agent_time = time.time()
            logger.info(f"⏱️ Agent応答完了: {post_agent_time - pre_agent_time:.2f}秒")

            # レスポンスが文字列でない場合の処理
            if not isinstance(agent_response, str):
                agent_response = str(agent_response)

            # 使用されたツール情報
            tool_info = ""
            if self.current_status["tool_name"]:
                tool_info = f"\n\n🔧 使用ツール: {self.current_status['tool_name']}"

            # 最終応答をストリーミング風に表示
            final_response = agent_response + tool_info

            # 応答生成中表示
            yield "✍️ 応答を生成中..."
            time.sleep(0.2)

            # 最終応答を少しずつ表示（ストリーミング風）
            current_text = ""
            for char in final_response:
                current_text += char
                if len(current_text) % 15 == 0:  # 15文字ごとに更新
                    yield current_text
                    time.sleep(0.03)  # 短い間隔

            # 最終的な完全な応答
            yield final_response

            # 総処理時間
            total_time = time.time() - start_time
            logger.info(f"✅ チャット完了: 総時間 {total_time:.2f}秒")

        except Exception as e:
            logger.error(f"チャット処理エラー: {e}")
            yield f"申し訳ございません。エラーが発生しました: {str(e)}"
        finally:
            # ステータスクリア
            self.current_status = {"message": "", "tool_name": "", "thinking": False}
            self.stream_status_queue = []

    async def chat_async(self, message: str, _history: List[Tuple[str, str]]) -> str:
        """非同期チャット処理（後方互換性のため保持）"""
        import time

        try:
            start_time = time.time()
            logger.info(f"🚀 チャット開始: {message[:50]}...")

            # Strands Agentを使用してメッセージを処理
            if self.agent is None:
                return "エラー: Agentが初期化されていません。"

            # ステータスリセット
            self.current_status = {"message": "", "tool_name": "", "thinking": False}

            # Agent呼び出し前
            pre_agent_time = time.time()
            logger.info(f"⏱️ Agent呼び出し前: {pre_agent_time - start_time:.2f}秒経過")

            # Agent処理（コールバックによりステータス更新）
            response = self.agent(message)

            # Agent呼び出し後
            post_agent_time = time.time()
            logger.info(f"⏱️ Agent応答完了: {post_agent_time - pre_agent_time:.2f}秒")

            # レスポンスが文字列でない場合の処理
            if not isinstance(response, str):
                response = str(response)

            # 実際に使用されたツール情報をステータスから取得
            if self.current_status["tool_name"]:
                tool_info = f"\n\n🔧 使用ツール: {self.current_status['tool_name']}"
                response = response + tool_info

            # 総処理時間
            total_time = time.time() - start_time
            logger.info(f"✅ チャット完了: 総時間 {total_time:.2f}秒")

            return response

        except Exception as e:
            logger.error(f"チャット処理エラー: {e}")
            return f"申し訳ございません。エラーが発生しました: {str(e)}"
        finally:
            # ステータスクリア
            self.current_status = {"message": "", "tool_name": "", "thinking": False}

    def chat(self, message: str, history: List[Tuple[str, str]]) -> str:
        """同期チャット処理（Gradio用）"""
        try:
            # 非同期関数を同期的に実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(self.chat_async(message, history))
                return response
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"同期チャット処理エラー: {e}")
            return f"申し訳ございません。エラーが発生しました: {str(e)}"

    def add_mcp_server(
        self, name: str, command: str, args_str: str, env_str: str
    ) -> str:
        """新しいMCPサーバを追加"""
        try:
            # 引数と環境変数をパース
            args = args_str.split() if args_str.strip() else []
            env = {}
            if env_str.strip():
                for line in env_str.strip().split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env[key.strip()] = value.strip()

            # 新しいサーバ設定
            server_config = {"command": command.strip(), "args": args, "env": env}

            # 設定に追加
            self.config["mcpServers"][name] = server_config
            self.config["user_servers"].append(name)
            self._save_config()

            # MCPサーバの再初期化を試行
            self._setup_mcp_integration()

            return f"MCPサーバ '{name}' を追加しました。"

        except Exception as e:
            logger.error(f"MCPサーバ追加エラー: {e}")
            return f"MCPサーバの追加に失敗しました: {str(e)}"

    def remove_mcp_server(self, name: str) -> str:
        """MCPサーバを削除"""
        try:
            if name in self.config["mcpServers"]:
                del self.config["mcpServers"][name]
                if name in self.config["user_servers"]:
                    self.config["user_servers"].remove(name)
                self._save_config()
                return f"MCPサーバ '{name}' を削除しました。"
            else:
                return f"MCPサーバ '{name}' が見つかりません。"

        except Exception as e:
            logger.error(f"MCPサーバ削除エラー: {e}")
            return f"MCPサーバの削除に失敗しました: {str(e)}"

    def get_server_list(self) -> str:
        """設定済みMCPサーバのリストを取得"""
        try:
            servers = list(self.config["mcpServers"].keys())
            if not servers:
                return "設定されているMCPサーバはありません。"

            result = "設定済みMCPサーバ:\n"
            for i, server in enumerate(servers, 1):
                server_config = self.config["mcpServers"][server]
                result += f"{i}. {server}\n"
                result += f"   コマンド: {server_config.get('command', 'N/A')}\n"
                if server_config.get("args"):
                    result += f"   引数: {' '.join(server_config['args'])}\n"
                result += "\n"

            return result

        except Exception as e:
            logger.error(f"サーバリスト取得エラー: {e}")
            return f"サーバリストの取得に失敗しました: {str(e)}"

    def get_model_info(self) -> str:
        """モデル情報を取得"""
        try:
            if self.agent is None:
                return (
                    "❌ Agent未初期化\n\nAWS認証情報を.envファイルに設定してください:\n"
                    "AWS_ACCESS_KEY_ID=your_key\n"
                    "AWS_SECRET_ACCESS_KEY=your_secret\n"
                    "AWS_DEFAULT_REGION=us-west-2"
                )

            model_info = "✅ 使用中のモデル情報:\n"
            if hasattr(self.agent, "model"):
                model = self.agent.model
                model_info += "プロバイダー: AWS Bedrock\n"
                model_info += f"モデル: {type(model).__name__}\n"
                if hasattr(model, "model_id"):
                    model_info += f"モデルID: {model.model_id}\n"
                if hasattr(model, "region"):
                    model_info += f"リージョン: {model.region}\n"
                else:
                    import os

                    region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
                    model_info += f"リージョン: {region}\n"
            else:
                model_info += "モデル詳細情報が利用できません"

            return model_info

        except Exception as e:
            return f"モデル情報取得エラー: {str(e)}"

    def create_interface(self) -> gr.Blocks:
        """Gradioインターフェースを作成"""
        app_settings = self.config.get("app_settings", {})
        title = app_settings.get("title", "Strands Agents Chat")
        description = app_settings.get("description", "MCPサーバ統合チャット")

        with gr.Blocks(title=title) as interface:
            gr.Markdown(f"# {title}")
            gr.Markdown(description)

            with gr.Tabs():
                # チャットタブ
                with gr.Tab("💬 チャット"):
                    gr.Markdown(
                        "### 🤖 AIアシスタント（リアルタイムステータス表示付き）"
                    )
                    gr.Markdown(
                        "何でもお聞きください。計算、テキスト処理、時刻確認など様々なツールが利用できます。"
                    )
                    gr.Markdown(
                        "**📱 ステータス表示機能**: チャット中にAIの思考プロセスやツール使用状況がリアルタイムで表示されます。"
                    )

                    # ストリーミングチャットインターフェース
                    gr.ChatInterface(
                        fn=self.chat_stream,
                        title="AIアシスタント（ストリーミング版）",
                        description="リアルタイムでAIの状態を確認しながらチャットできます",
                        examples=[
                            "2 + 3 * 4 を計算して",
                            "現在の時刻を教えて",
                            "「Hello World」の文字数を数えて",
                            "こんにちは、今日は何ができますか？",
                        ],
                        # ストリーミング有効化
                        show_progress="full",
                        multimodal=False,
                    )

                # MCPサーバ管理タブ
                with gr.Tab("⚙️ MCPサーバ管理"):
                    gr.Markdown("## MCPサーバの追加")

                    with gr.Row():
                        with gr.Column():
                            server_name = gr.Textbox(
                                label="サーバ名", placeholder="my-custom-server"
                            )
                            server_command = gr.Textbox(
                                label="コマンド", placeholder="uvx"
                            )
                            server_args = gr.Textbox(
                                label="引数 (スペース区切り)",
                                placeholder="my-mcp-server@latest",
                            )
                            server_env = gr.Textbox(
                                label="環境変数 (KEY=VALUE形式、1行ずつ)",
                                placeholder="LOG_LEVEL=INFO\nAPI_KEY=your_key",
                                lines=3,
                            )

                        with gr.Column():
                            add_btn = gr.Button("➕ サーバ追加", variant="primary")
                            add_result = gr.Textbox(
                                label="結果", interactive=False, lines=3
                            )

                    gr.Markdown("## 設定済みサーバ")

                    with gr.Row():
                        refresh_btn = gr.Button("🔄 リスト更新")
                        remove_name = gr.Textbox(
                            label="削除するサーバ名",
                            placeholder="削除したいサーバ名を入力",
                        )
                        remove_btn = gr.Button("🗑️ サーバ削除", variant="stop")

                    server_list = gr.Textbox(
                        label="サーバリスト",
                        interactive=False,
                        lines=10,
                        value=self.get_server_list(),
                    )

                    remove_result = gr.Textbox(
                        label="削除結果", interactive=False, lines=2
                    )

                    # イベントハンドラ
                    add_btn.click(
                        fn=self.add_mcp_server,
                        inputs=[server_name, server_command, server_args, server_env],
                        outputs=add_result,
                    )

                    remove_btn.click(
                        fn=self.remove_mcp_server,
                        inputs=remove_name,
                        outputs=remove_result,
                    )

                    refresh_btn.click(fn=self.get_server_list, outputs=server_list)

                # 情報タブ
                with gr.Tab("ℹ️ 情報"):
                    gr.Markdown("## システム情報")

                    model_info_btn = gr.Button("🔄 モデル情報更新")
                    model_info_display = gr.Textbox(
                        label="モデル情報",
                        interactive=False,
                        lines=6,
                        value=self.get_model_info(),
                    )

                    gr.Markdown("## 利用可能なMCPツール")
                    gr.Markdown("""
### 基本ツール
- **計算機**: 数式計算 (例: `2 + 3 * 4 を計算して`)
- **時刻取得**: 現在時刻表示 (例: `現在の時刻を教えて`)
- **テキスト処理**: 文字数カウント、大小文字変換など (例: `「Hello」の文字数を数えて`)
- **URL取得**: ウェブページ内容取得

### 使い方
チャットで「○○を計算して」「時刻を教えて」などと話しかけてください。
""")

                    model_info_btn.click(
                        fn=self.get_model_info, outputs=model_info_display
                    )

        return interface


def main():
    """メイン実行関数"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    app = MCPChatApp()
    interface = app.create_interface()

    # .envから設定を取得
    port = int(os.getenv("APP_PORT", "7860"))

    # アプリケーションを起動
    interface.launch(
        server_name="0.0.0.0", server_port=port, share=False, show_error=True
    )


if __name__ == "__main__":
    main()
