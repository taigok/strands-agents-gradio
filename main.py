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

# 環境変数読み込み
load_dotenv()

# AWS設定
aws_region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
model_id = "anthropic.claude-3-haiku-20240307-v1:0"
temperature = 0.1

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

def chat_stream(message, _history):
    """ストリーミングチャット関数（ステータス表示付き）"""
    status_log = []
    current_status = ""
    
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
                reasoning = kwargs["reasoningText"][:100] + "..." if len(kwargs["reasoningText"]) > 100 else kwargs["reasoningText"]
                status = f"🤔 思考: {reasoning}"
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
                current_status = status
                logger.info(status)
        
        with mcp_client:
            # ツール取得
            yield "📊 MCPツールを取得中..."
            tools = mcp_client.list_tools_sync()
            tool_status = f"📊 利用可能ツール数: {len(tools)}"
            status_log.append(tool_status)
            logger.info(tool_status)
            yield tool_status
            
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
            if status_log:
                final_response += "\n\n---\n**処理ログ:**\n" + "\n".join(status_log)
            
            logger.info("🏁 チャット処理完了")
            yield final_response
            
    except Exception as e:
        error_msg = f"❌ エラー: {str(e)}"
        logger.error(error_msg)
        yield error_msg

# Gradioインターフェース
interface = gr.ChatInterface(
    fn=chat_stream,
    title="Simple MCP Chat with Debug",
    examples=["AWS Lambda とは？", "EC2 の料金は？", "こんにちは"]
)

if __name__ == "__main__":
    interface.launch(server_name="0.0.0.0", server_port=7862)