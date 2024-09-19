import os
import json
import requests
from dotenv import load_dotenv
import pandas_datareader.data as web 
import openai
from openai import OpenAI
import streamlit as st

# Set the OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

model_name = 'gpt-4o-mini-2024-07-18'  # 'gpt-4o-2024-08-06'

# DataReaderでstooqから株価情報を取得する関数を定義（開始日～終了日）
def get_stock_price(code, date_from, date_to):
    # 日本用のコードに変換
    code = code + '.JP'
    # stooqからデータ取得
    df = web.DataReader(code, data_source='stooq', start=date_from, end=date_to)
    # 日付と株価の終値を返す ※日付形式がおかしくなるのでorient='table'を利用
    return df['Close'].to_json(orient='table')

def get_stock_price_range(arguments):
    res = get_stock_price(
        code=arguments.get('code'),
        date_from=arguments.get('date_from'),
        date_to=arguments.get('date_to')
    )
    return res

# 天気情報を取得する関数を定義
def get_info(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true"
    }
    response = requests.get(url, params=parameters)

    if response.status_code == 200:
        data = response.json()
        return json.dumps(data["current_weather"])
    else:
        return None

def get_weather_by_location(arguments):
    res = get_info(
        latitude=arguments.get('latitude'),
        longitude=arguments.get('longitude')
    )
    return res

# 使用するツールのリスト
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price_range",
            "description": "証券コードと2つの日付を渡すと指定の会社のその2つの日付の間の株価の終値を返します",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "証券コード",
                    },
                    "date_from": {
                        "type": "string",
                        "description": "株価を知りたい日付の開始日",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "株価を知りたい日付の終了日",
                    },
                },
                "required": ["code", "date_from", "date_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_by_location",
            "description": "緯度と経度の情報から現在と将来の天気を取得",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "string",
                        "description": "緯度",
                    },
                    "longitude": {
                        "type": "string",
                        "description": "経度",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        },
    }
]

def llm_agent(user_input, chat_history):

    client = OpenAI()

    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use the supplied tools to assist the user if needed."},
        {"role": "user", "content": user_input}
    ]

    # ChatGPT API呼び出し
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice='auto'
    )

    # Add user input to chat history
    st.session_state.chat_history.append(f"# You: \n{user_input}")
    
    # ツール呼び出しの結果があるか確認
    tool_calls = getattr(response.choices[0].message, 'tool_calls', None)

    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if function_name == 'get_stock_price_range':
                function_response = get_stock_price_range(arguments)
            elif function_name == 'get_weather_by_location':
                function_response = get_weather_by_location(arguments)
            else:
                raise NotImplementedError(f"Unknown function: {function_name}")

            second_response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {'role': 'system', 'content': "You are a helpful assistant."},
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "tool_call_id": tool_call.id, "content": ""},
                    {'role': 'function', 'name': function_name, 'content': str(function_response)},
                ]
            )
            # ツール応答をchat_historyに追加
            chat_history.append(f"# Bot: \n{second_response.choices[0].message.content}")
    else:
        # 通常の応答をchat_historyに追加
        chat_history.append(f"# Bot:\n {response.choices[0].message.content}")

# Build Streamlit UI
st.title("Simple Chat Bot")

# Maintain chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Get user input
user_input = st.text_input("Input:", key="input_text")

# Add Send button and reset input
if st.button("Send"):
    if user_input:
        # Run the agent and update chat history
        llm_agent(user_input, st.session_state.chat_history)
      
# Display chat history
st.write("Chat History:")
for message in st.session_state.chat_history:
    st.write(message)
