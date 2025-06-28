"""超シンプルなStrands Agents + Gradio チャット"""

import os
import logging
import gradio as gr
from strands import Agent
from strands.models import BedrockModel
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

# Agent作成
agent = Agent(model=bedrock_model)

def chat(message, history):
    """シンプルなチャット関数"""
    try:
        logger.info(f"チャット開始: {message}")
        response = agent(message)
        logger.info(f"チャット完了")
        return str(response)
    except Exception as e:
        logger.error(f"エラー: {e}")
        return f"エラーが発生しました: {str(e)}"

# Gradioインターフェース
interface = gr.ChatInterface(
    fn=chat,
    title="Simple Strands Chat",
    examples=["こんにちは", "今日の天気は？", "数学の問題を出して"]
)

if __name__ == "__main__":
    interface.launch(server_name="0.0.0.0", server_port=7862)