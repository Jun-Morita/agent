# 必要なライブラリのインポート
import os
import requests
import argparse
import warnings
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults

# 警告メッセージを無効にする
warnings.filterwarnings("ignore")

# 環境変数の読み込み
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("APIキーが設定されていません。環境変数を確認してください。")

# GPTモデルの設定
model_name = 'gpt-4o-mini-2024-07-18'  # 使用するモデル名

# Wikipedia情報を取得する関数
def get_wikipedia_info(keyword):
    url = f"https://ja.wikipedia.org/w/api.php"
    parameters = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "titles": keyword
    }
    response = requests.get(url, params=parameters)

    if response.status_code == 200:
        data = response.json()
        pages = data["query"]["pages"]
        page_id = next(iter(pages))
        if page_id != "-1":
            return pages[page_id]["extract"]
        else:
            return "Wikipedia page not found for the keyword."
    else:
        return f"Error: {response.status_code}"

# Wikipedia検索ツール
def wikipedia_search(arguments):
    keyword = arguments
    return get_wikipedia_info(keyword)

# DuckDuckGo検索ツール
def duckduckgo_search(arguments):
    search_results = DuckDuckGoSearchResults().run(arguments)
    return search_results

# ツールリスト
tools = [
    Tool(
        name="WikipediaSearch",
        func=wikipedia_search,
        description="Useful for when you need to search Wikipedia."
    ),
    Tool(
        name="DuckDuckGo Search",
        func=duckduckgo_search,
        description="Use this tool to search for general information on the web via DuckDuckGo."
    ),
]

# GPT-4を使用する設定
llm = ChatOpenAI(temperature=0, model_name=model_name)

# エージェントを初期化
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True
)

# コマンドライン引数の設定
def main():
    parser = argparse.ArgumentParser(description="Run LangChain agent with a question")
    parser.add_argument("question", type=str, help="The question to ask the agent")
    args = parser.parse_args()

    # エージェントに質問を投げる
    agent.run(args.question)

if __name__ == "__main__":
    main()
