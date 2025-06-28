"""シンプルなStrands Agents + Gradio + MCP チャット"""

import os
import logging
import gradio as gr
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from dotenv import load_dotenv

# ログ設定
logging.basicConfig(level=logging.INFO)
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

def chat(message, history):
    """MCPツール付きチャット関数"""
    try:
        logger.info(f"チャット: {message}")
        with mcp_client:
            tools = mcp_client.list_tools_sync()
            agent = Agent(model=bedrock_model, tools=tools)
            response = agent(message)
            return str(response)
    except Exception as e:
        logger.error(f"エラー: {e}")
        return f"エラー: {str(e)}"

# Gradioインターフェース
interface = gr.ChatInterface(
    fn=chat,
    title="Simple MCP Chat",
    examples=["AWS Lambda とは？", "EC2 の料金は？", "こんにちは"]
)

if __name__ == "__main__":
    interface.launch(server_name="0.0.0.0", server_port=7862)