"""シンプルなStrands Agents + Gradio + MCP チャット"""

import logging
import os
import queue
import threading

import gradio as gr
from dotenv import load_dotenv
from gradio import ChatMessage
from mcp import StdioServerParameters, stdio_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# デフォルトのシステムプロンプト
DEFAULT_SYSTEM_PROMPT = (
    "あなたはAWSのドキュメントに精通した技術アシスタントです。"
    "ユーザーの質問に対して、MCPツールを使用してAWSの公式ドキュメントから正確な情報を検索し、"
    "わかりやすく簡潔に回答してください。"
    "回答には具体例やベストプラクティスを含めると良いでしょう。"
    "技術的な内容は正確に、しかし初心者にも理解しやすいように説明してください。"
)

# gr.NO_RELOAD を使用して、リロード時に再実行されないようにする
if gr.NO_RELOAD:
    # 環境変数読み込み
    load_dotenv()

    # AWS設定
    aws_region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    temperature = 0.1

    # システムプロンプトを環境変数から取得（オプション）
    system_prompt_override = os.getenv("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)

    logger.info("🚀 初期化: モデルとMCPクライアントをロード中...")

    # モデル作成
    bedrock_model = BedrockModel(
        model_id=model_id, region_name=aws_region, temperature=temperature
    )

    # MCP クライアント作成
    mcp_client = MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="uvx", args=["awslabs.aws-documentation-mcp-server@latest"]
            )
        )
    )

    logger.info("✅ 初期化完了: モデルとMCPクライアントがロードされました")


def chat_stream(message, history):
    """ストリーミングチャット関数（ステータス表示付き）"""
    status_log = []
    current_status = ""
    tools = []  # ツール情報を保持
    used_tools = []  # 使用されたツールを記録

    try:
        logger.info(f"🚀 チャット開始: {message}")

        # ユーザーメッセージを履歴に追加
        history.append(ChatMessage(role="user", content=message))
        yield history

        # キューを先に定義
        update_queue = queue.Queue()

        # コールバックハンドラーでログ表示
        def debug_callback(**kwargs):
            nonlocal current_status, history, used_tools, update_queue
            # すべてのkwargsをログ出力してデバッグ
            logger.info(f"🔍 Callback kwargs: {list(kwargs.keys())}")

            # event形式のコールバックを処理
            if "event" in kwargs:
                event_data = kwargs["event"]
                logger.info(
                    f"🔍 Event data: {type(event_data)} = {str(event_data)[:300]}..."
                )

                # ツール使用の開始を検出
                if isinstance(event_data, dict):
                    if "contentBlockStart" in event_data:
                        content_block = event_data.get("contentBlockStart", {}).get(
                            "start", {}
                        )
                        if "toolUse" in content_block:
                            tool_use = content_block["toolUse"]
                            tool_name = tool_use.get("name", "unknown")

                            history.append(
                                ChatMessage(
                                    role="assistant",
                                    content=f"🔧 ツール '{tool_name}' を実行中...",
                                    metadata={"title": f"🔧 ツール使用: {tool_name}"},
                                )
                            )
                            used_tools.append(tool_name)
                            logger.info(f"🔧 ツール使用開始: {tool_name}")
                            # キューに更新を追加
                            update_queue.put(("update", None))
                            return

            if "current_tool_use" in kwargs:
                tool_info = kwargs["current_tool_use"]
                tool_name = tool_info.get("name", "unknown")
                tool_input = tool_info.get("input", {})

                # ツール使用のメッセージを追加
                tool_message = f"ツール '{tool_name}' を使用しています..."
                if tool_input:
                    # 入力パラメータがある場合は表示（簡潔に）
                    input_preview = (
                        str(tool_input)[:100] + "..."
                        if len(str(tool_input)) > 100
                        else str(tool_input)
                    )
                    tool_message += f"\n入力: {input_preview}"

                history.append(
                    ChatMessage(
                        role="assistant",
                        content=tool_message,
                        metadata={"title": f"🔧 ツール使用: {tool_name}"},
                    )
                )
                used_tools.append(tool_name)
                # キューに更新を追加
                update_queue.put(("update", None))

                status = f"🔧 ツール使用: {tool_name}"
                status_log.append(status)
                current_status = status
                logger.info(status)
            elif "reasoning" in kwargs:
                history.append(
                    ChatMessage(
                        role="assistant",
                        content="思考中です...",
                        metadata={"title": "🤔 思考中"},
                    )
                )
                yield history

                status = "🤔 思考中..."
                status_log.append(status)
                current_status = status
                logger.info(status)
            elif "reasoningText" in kwargs:
                reasoning_full = kwargs["reasoningText"]
                reasoning_preview = (
                    reasoning_full[:200] + "..."
                    if len(reasoning_full) > 200
                    else reasoning_full
                )

                history.append(
                    ChatMessage(
                        role="assistant",
                        content=reasoning_preview,
                        metadata={"title": "🤔 思考内容"},
                    )
                )
                yield history

                status = f"🤔 思考: {reasoning_preview[:50]}..."
                status_log.append(status)
                current_status = status
                logger.info(f"🤔 Reasoning: {reasoning_full}")  # 完全版をログに
            elif "reasoningComplete" in kwargs:
                history.append(
                    ChatMessage(
                        role="assistant",
                        content="思考が完了しました。回答を準備中です。",
                        metadata={"title": "🤔 思考完了"},
                    )
                )
                yield history

                status = "🤔 思考完了"
                status_log.append(status)
                current_status = status
                logger.info(status)
            elif "data" in kwargs:
                status = "✍️ 応答生成中..."
                if status not in status_log:
                    status_log.append(status)
                    current_status = status
                    logger.info(status)
            elif "complete" in kwargs and kwargs["complete"]:
                status = "✅ 応答完了"
                status_log.append(status)
                current_status = ""  # ステータスをクリア
                logger.info(status)
            elif "tool_use" in kwargs:
                # 代替: tool_use キーをチェック
                tool_info = kwargs["tool_use"]
                tool_name = (
                    tool_info.get("name", "unknown")
                    if isinstance(tool_info, dict)
                    else str(tool_info)
                )

                history.append(
                    ChatMessage(
                        role="assistant",
                        content=f"ツール '{tool_name}' を使用中...",
                        metadata={"title": f"🔧 ツール: {tool_name}"},
                    )
                )
                used_tools.append(tool_name)
                # キューに更新を追加
                update_queue.put(("update", None))
                logger.info(f"🔧 ツール使用 (tool_use): {tool_name}")
            elif "tool_result" in kwargs:
                # ツール結果
                tool_result = kwargs["tool_result"]
                result_preview = (
                    str(tool_result)[:100] + "..."
                    if len(str(tool_result)) > 100
                    else str(tool_result)
                )

                history.append(
                    ChatMessage(
                        role="assistant",
                        content=f"ツール実行完了: {result_preview}",
                        metadata={"title": "✅ ツール実行完了"},
                    )
                )
                # キューに更新を追加
                update_queue.put(("update", None))
                logger.info(f"✅ ツール結果: {result_preview}")
            else:
                # その他のコールバック
                logger.info(f"🔍 その他のコールバック: {kwargs}")

        with mcp_client:
            # ツール取得メッセージ
            history.append(
                ChatMessage(
                    role="assistant",
                    content="MCPツールを取得中です...",
                    metadata={"title": "📊 ツール取得中"},
                )
            )
            yield history

            tools = mcp_client.list_tools_sync()

            # ツール一覧をログ出力（正しい属性アクセス方法）
            tool_names = []
            tool_details = []
            for tool in tools:
                tool_name = "unknown"
                tool_desc = "説明なし"

                # MCPAgentToolオブジェクトの正しい属性アクセス
                if hasattr(tool, "mcp_tool"):
                    tool_name = tool.mcp_tool.name
                    tool_desc = tool.mcp_tool.description or "説明なし"
                elif hasattr(tool, "tool_name"):
                    # 代替: tool_nameプロパティを使用
                    tool_name = tool.tool_name
                    tool_desc = getattr(tool, "description", "説明なし")
                elif hasattr(tool, "_tool"):
                    tool_name = getattr(tool._tool, "name", "unknown")
                    tool_desc = getattr(tool._tool, "description", "説明なし")
                elif hasattr(tool, "tool"):
                    tool_name = getattr(tool.tool, "name", "unknown")
                    tool_desc = getattr(tool.tool, "description", "説明なし")
                elif hasattr(tool, "name"):
                    tool_name = tool.name
                    tool_desc = getattr(tool, "description", "説明なし")

                tool_names.append(tool_name)
                tool_details.append((tool_name, tool_desc))

            tool_status = f"利用可能ツール数: {len(tools)}"
            status_log.append(tool_status)
            logger.info(tool_status)

            # 各ツールの詳細もログ出力
            for tool_name, tool_desc in tool_details:
                logger.info(f"🔧 ツール: {tool_name} - {tool_desc[:100]}...")

            # ツール詳細をChatMessageで表示
            tool_list = "\n".join([f"• {name}" for name in tool_names])
            history.append(
                ChatMessage(
                    role="assistant",
                    content=f"取得完了: {len(tools)}個のツールが利用可能です。\n\n{tool_list}",
                    metadata={"title": f"📊 ツール取得完了 ({len(tools)}個)"},
                )
            )
            yield history

            # Agent作成
            history.append(
                ChatMessage(
                    role="assistant",
                    content="Agentを初期化中です...",
                    metadata={"title": "🤖 Agent初期化"},
                )
            )
            yield history

            agent = Agent(
                model=bedrock_model,
                tools=tools,
                callback_handler=debug_callback,
                system_prompt=system_prompt_override,
            )

            # Agent処理を別スレッドで実行
            agent_response = None
            agent_error = None

            def run_agent():
                nonlocal agent_response, agent_error
                try:
                    agent_response = agent(message)
                except Exception as e:
                    agent_error = e

            # Agent実行開始
            history.append(
                ChatMessage(
                    role="assistant",
                    content="Agent処理を開始します...",
                    metadata={"title": "🚀 Agent処理開始"},
                )
            )
            yield history

            agent_thread = threading.Thread(target=run_agent)
            agent_thread.start()

            # ステータス監視とキューからの更新処理
            while agent_thread.is_alive():
                try:
                    # キューから更新を取得（タイムアウト付き）
                    update_type, _ = update_queue.get(timeout=0.1)
                    if update_type == "update":
                        yield history
                except queue.Empty:
                    pass

            # Agent完了を待つ
            agent_thread.join()

            if agent_error:
                # エラーメッセージ
                history.append(
                    ChatMessage(
                        role="assistant",
                        content=f"エラーが発生しました: {str(agent_error)}",
                        metadata={"title": "❌ エラー"},
                    )
                )
                yield history
                raise agent_error

            # 最終応答
            final_response = str(agent_response)

            # サマリー情報を追加
            summary_info = ""
            if used_tools:
                summary_info += (
                    f"\n\n**使用されたツール:** {', '.join(set(used_tools))}"
                )

            # 最終回答メッセージ
            history.append(
                ChatMessage(
                    role="assistant",
                    content=final_response + summary_info,
                    metadata={"title": "✅ 回答完了"},
                )
            )
            yield history

            logger.info("🏁 チャット処理完了")

    except Exception as e:
        error_msg = f"エラーが発生しました: {str(e)}"
        logger.error(error_msg)
        history.append(
            ChatMessage(
                role="assistant", content=error_msg, metadata={"title": "❌ エラー"}
            )
        )
        yield history


def get_initial_tools_info():
    """初期表示用のツール情報を取得"""
    try:
        with mcp_client:
            tools = mcp_client.list_tools_sync()

            info = f"🔧 **利用可能なMCPツール** ({len(tools)}個)\n\n"

            # MCPAgentToolから実際のツール情報を抽出（正しい属性アクセス方法）
            for i, tool in enumerate(tools):
                tool_name = "unknown"
                tool_desc = "説明なし"

                # 詳細デバッグ: MCPAgentToolの内部構造を調査
                logger.info(f"ツール {i}: {type(tool)}")
                logger.info(
                    f"利用可能属性: {[attr for attr in dir(tool) if not attr.startswith('_')]}"
                )

                # MCPAgentToolオブジェクトの正しい属性アクセス
                if hasattr(tool, "mcp_tool"):
                    tool_name = tool.mcp_tool.name
                    tool_desc = tool.mcp_tool.description or "説明なし"
                    logger.info(f"✅ mcp_tool 属性経由: {tool_name}")
                elif hasattr(tool, "tool_name"):
                    # 代替: tool_nameプロパティを使用
                    tool_name = tool.tool_name
                    tool_desc = getattr(tool, "description", "説明なし")
                    logger.info(f"✅ tool_name プロパティ経由: {tool_name}")
                else:
                    # さらに詳細な調査
                    logger.info(f"🔍 すべての属性: {dir(tool)}")

                    # プライベート属性も含めて調査
                    for attr in dir(tool):
                        if "tool" in attr.lower() or "mcp" in attr.lower():
                            try:
                                attr_value = getattr(tool, attr)
                                logger.info(
                                    f"🔍 {attr}: {type(attr_value)} = {attr_value}"
                                )

                                # 内部オブジェクトの name と description を確認
                                if hasattr(attr_value, "name"):
                                    tool_name = attr_value.name
                                    logger.info(f"✅ {attr}.name: {tool_name}")
                                if hasattr(attr_value, "description"):
                                    tool_desc = attr_value.description or "説明なし"
                                    logger.info(
                                        f"✅ {attr}.description: {tool_desc[:50]}..."
                                    )
                            except Exception as e:
                                logger.info(f"❌ {attr} アクセスエラー: {e}")

                    # フォールバック
                    if tool_name == "unknown":
                        tool_name = f"MCP_Tool_{i + 1}"
                        tool_desc = "MCP Tool"

                logger.info(f"🔧 最終ツール情報: {tool_name} - {tool_desc[:50]}...")
                info += f"• **{tool_name}**\n"

            return info
    except Exception as e:
        logger.error(f"MCPツール情報取得エラー: {e}")
        import traceback

        logger.error(f"スタックトレース: {traceback.format_exc()}")

        # フォールバック: 簡単な説明を表示
        return """🔧 **MCPツール利用可能** 

• **AWS Documentation Server**: AWS公式ドキュメント検索
• **詳細**: チャット時に動的に表示されます

⚠️ 初期ツール情報取得中にエラーが発生しましたが、チャット機能は正常に動作します。"""


# Gradioインターフェース
with gr.Blocks(
    title="Simple MCP Chat with Debug", css="footer{display:none !important}"
) as interface:
    gr.Markdown("# Simple MCP Chat with Debug")
    gr.Markdown("Strands Agents + AWS Documentation MCP Server")

    # ツール情報を初期表示
    gr.Markdown(get_initial_tools_info())

    # チャットインターフェース
    chatbot = gr.Chatbot(type="messages", height=500)
    gr.ChatInterface(
        fn=chat_stream,
        chatbot=chatbot,
        examples=[
            "AWS Lambda とは？",
            "EC2 の料金は？",
            "S3バケットの設定方法を教えて",
            "DynamoDBのパフォーマンス最適化について",
            "VPCとセキュリティグループの違いは？",
            "CloudFormationテンプレートの例を見せて",
        ],
    )

if __name__ == "__main__":
    # 開発時は `gradio main.py` で実行してホットリロードを有効化
    # 本番環境では `python main.py` で実行
    interface.launch(server_name="0.0.0.0", server_port=7862, show_api=False)
