"""シンプルなStrands Agents + Gradio + MCP チャット"""

import os
import logging
import threading
import time
import gradio as gr
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from dotenv import load_dotenv

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# gr.NO_RELOAD を使用して、リロード時に再実行されないようにする
if gr.NO_RELOAD:
    # 環境変数読み込み
    load_dotenv()
    
    # AWS設定
    aws_region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    temperature = 0.1
    
    logger.info("🚀 初期化: モデルとMCPクライアントをロード中...")
    
    # モデル作成
    bedrock_model = BedrockModel(
        model_id=model_id, 
        region_name=aws_region, 
        temperature=temperature
    )
    
    # MCP クライアント作成
    mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    ))
    
    logger.info("✅ 初期化完了: モデルとMCPクライアントがロードされました")

def chat_stream(message, _history):
    """ストリーミングチャット関数（ステータス表示付き）"""
    status_log = []
    current_status = ""
    tools = []  # ツール情報を保持
    
    try:
        logger.info(f"🚀 チャット開始: {message}")
        
        # コールバックハンドラーでログ表示
        def debug_callback(**kwargs):
            nonlocal current_status
            if "current_tool_use" in kwargs:
                tool_info = kwargs["current_tool_use"]
                tool_name = tool_info.get("name", "unknown")
                status = f"🔧 ツール使用: {tool_name}"
                status_log.append(status)
                current_status = status
                logger.info(status)
            elif "reasoning" in kwargs:
                status = "🤔 思考中..."
                status_log.append(status)
                current_status = status
                logger.info(status)
            elif "reasoningText" in kwargs:
                reasoning_full = kwargs["reasoningText"]
                reasoning_preview = reasoning_full[:100] + "..." if len(reasoning_full) > 100 else reasoning_full
                status = f"🤔 思考: {reasoning_preview}"
                status_log.append(status)
                current_status = status
                logger.info(f"🤔 Reasoning: {reasoning_full}")  # 完全版をログに
            elif "reasoningComplete" in kwargs:
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
        
        with mcp_client:
            # ツール取得
            yield "📊 MCPツールを取得中..."
            tools = mcp_client.list_tools_sync()
            
            # ツール一覧をログ出力（正しい属性アクセス方法）
            tool_names = []
            tool_details = []
            for tool in tools:
                tool_name = "unknown"
                tool_desc = "説明なし"
                
                # MCPAgentToolオブジェクトの正しい属性アクセス
                if hasattr(tool, 'mcp_tool'):
                    tool_name = tool.mcp_tool.name
                    tool_desc = tool.mcp_tool.description or "説明なし"
                elif hasattr(tool, 'tool_name'):
                    # 代替: tool_nameプロパティを使用
                    tool_name = tool.tool_name
                    tool_desc = getattr(tool, 'description', '説明なし')
                elif hasattr(tool, '_tool'):
                    tool_name = getattr(tool._tool, 'name', 'unknown')
                    tool_desc = getattr(tool._tool, 'description', '説明なし')
                elif hasattr(tool, 'tool'):
                    tool_name = getattr(tool.tool, 'name', 'unknown')
                    tool_desc = getattr(tool.tool, 'description', '説明なし')
                elif hasattr(tool, 'name'):
                    tool_name = tool.name
                    tool_desc = getattr(tool, 'description', '説明なし')
                
                tool_names.append(tool_name)
                tool_details.append((tool_name, tool_desc))
            
            tool_status = f"📊 利用可能ツール数: {len(tools)} ({', '.join(tool_names)})"
            status_log.append(tool_status)
            logger.info(tool_status)
            
            # 各ツールの詳細もログ出力
            for tool_name, tool_desc in tool_details:
                logger.info(f"🔧 ツール: {tool_name} - {tool_desc[:100]}...")
            
            # ツール詳細を画面にも表示（簡潔版）
            tool_display = f"{tool_status}\n\n"
            
            # ツール名のみ簡潔に表示
            tool_display += "**📋 利用可能ツール:**\n"
            for tool_name, tool_desc in tool_details:
                tool_display += f"• **{tool_name}**\n"
            
            # 詳細情報へのリンク
            tool_display += "\n💡 詳細情報は応答後のログセクションで確認できます。"
            
            yield tool_display
            
            # Agent作成
            yield "🤖 Agentを初期化中..."
            agent = Agent(model=bedrock_model, tools=tools, callback_handler=debug_callback)
            
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
            yield "🚀 Agent処理開始..."
            agent_thread = threading.Thread(target=run_agent)
            agent_thread.start()
            
            # ステータス監視
            last_status = ""
            while agent_thread.is_alive():
                if current_status and current_status != last_status:
                    yield current_status
                    last_status = current_status
                time.sleep(0.1)
            
            # Agent完了を待つ
            agent_thread.join()
            
            if agent_error:
                raise agent_error
            
            # 最終応答
            final_response = str(agent_response)
            
            # 処理ログとツール情報を表示
            log_section = ""
            if status_log:
                # "✍️ 応答生成中..." を除外して表示
                filtered_log = [log for log in status_log if not log.startswith("✍️")]
                if filtered_log:
                    log_section = "\n\n---\n**処理ログ:**\n" + "\n".join(filtered_log)
            
            # ツール詳細情報を追加（正しい属性アクセス方法）
            if tools:
                tool_details_section = "\n\n---\n**利用可能なMCPツール:**\n"
                
                # ツール名のみ簡潔に表示
                tool_names_list = []
                tool_full_details = []
                
                for tool in tools:
                    tool_name = "unknown"
                    tool_desc = "説明なし"
                    
                    # MCPAgentToolオブジェクトの正しい属性アクセス
                    if hasattr(tool, 'mcp_tool'):
                        tool_name = tool.mcp_tool.name
                        tool_desc = tool.mcp_tool.description or "説明なし"
                    elif hasattr(tool, 'tool_name'):
                        # 代替: tool_nameプロパティを使用
                        tool_name = tool.tool_name
                        tool_desc = getattr(tool, 'description', '説明なし')
                    elif hasattr(tool, '_tool'):
                        tool_name = getattr(tool._tool, 'name', 'unknown')
                        tool_desc = getattr(tool._tool, 'description', '説明なし')
                    elif hasattr(tool, 'tool'):
                        tool_name = getattr(tool.tool, 'name', 'unknown')
                        tool_desc = getattr(tool.tool, 'description', '説明なし')
                    elif hasattr(tool, 'name'):
                        tool_name = tool.name
                        tool_desc = getattr(tool, 'description', '説明なし')
                    
                    tool_names_list.append(tool_name)
                    tool_full_details.append((tool_name, tool_desc))
                
                # ツール名のみ表示
                tool_details_section += f"**使用ツール:** {', '.join(tool_names_list)}\n\n"
                
                # 詳細は別セクションで表示
                tool_details_section += "**詳細情報:**\n"
                for tool_name, tool_desc in tool_full_details:
                    # 説明文を適切な長さに制限
                    desc_preview = tool_desc[:150] + "..." if len(tool_desc) > 150 else tool_desc
                    tool_details_section += f"• **{tool_name}**: {desc_preview}\n"
                
                log_section += tool_details_section
            
            logger.info("🏁 チャット処理完了")
            yield final_response + log_section
            
    except Exception as e:
        error_msg = f"❌ エラー: {str(e)}"
        logger.error(error_msg)
        yield error_msg

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
                logger.info(f"利用可能属性: {[attr for attr in dir(tool) if not attr.startswith('_')]}")
                
                # MCPAgentToolオブジェクトの正しい属性アクセス
                if hasattr(tool, 'mcp_tool'):
                    tool_name = tool.mcp_tool.name
                    tool_desc = tool.mcp_tool.description or "説明なし"
                    logger.info(f"✅ mcp_tool 属性経由: {tool_name}")
                elif hasattr(tool, 'tool_name'):
                    # 代替: tool_nameプロパティを使用
                    tool_name = tool.tool_name
                    tool_desc = getattr(tool, 'description', '説明なし')
                    logger.info(f"✅ tool_name プロパティ経由: {tool_name}")
                else:
                    # さらに詳細な調査
                    logger.info(f"🔍 すべての属性: {dir(tool)}")
                    
                    # プライベート属性も含めて調査
                    for attr in dir(tool):
                        if 'tool' in attr.lower() or 'mcp' in attr.lower():
                            try:
                                attr_value = getattr(tool, attr)
                                logger.info(f"🔍 {attr}: {type(attr_value)} = {attr_value}")
                                
                                # 内部オブジェクトの name と description を確認
                                if hasattr(attr_value, 'name'):
                                    tool_name = attr_value.name
                                    logger.info(f"✅ {attr}.name: {tool_name}")
                                if hasattr(attr_value, 'description'):
                                    tool_desc = attr_value.description or "説明なし"
                                    logger.info(f"✅ {attr}.description: {tool_desc[:50]}...")
                            except Exception as e:
                                logger.info(f"❌ {attr} アクセスエラー: {e}")
                    
                    # フォールバック
                    if tool_name == "unknown":
                        tool_name = f"MCP_Tool_{i+1}"
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
with gr.Blocks(title="Simple MCP Chat with Debug", css="footer{display:none !important}") as interface:
    gr.Markdown("# Simple MCP Chat with Debug")
    gr.Markdown("Strands Agents + AWS Documentation MCP Server")
    
    # ツール情報を初期表示
    gr.Markdown(get_initial_tools_info())
    
    # チャットインターフェース
    gr.ChatInterface(
        fn=chat_stream,
        examples=[
            "AWS Lambda とは？",
            "EC2 の料金は？", 
            "S3バケットの設定方法を教えて",
            "DynamoDBのパフォーマンス最適化について",
            "VPCとセキュリティグループの違いは？",
            "CloudFormationテンプレートの例を見せて"
        ]
    )

if __name__ == "__main__":
    # 開発時は `gradio main.py` で実行してホットリロードを有効化
    # 本番環境では `python main.py` で実行
    interface.launch(server_name="0.0.0.0", server_port=7862, show_api=False)