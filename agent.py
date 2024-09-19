import json
import requests
import pandas_datareader.data as web 
import xml.etree.ElementTree as ET
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

# 書籍情報を取得する関数を定義
def get_books(keyword):
    url = "https://ci.nii.ac.jp/books/opensearch/search"
    parameters = {
        "q": keyword
    }
    response = requests.get(url, params=parameters)

    if response.status_code == 200:
        try:
            # Parse the XML response
            root = ET.fromstring(response.content)
            
            # Extract book titles and other relevant information
            books = []
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title').text
                link = entry.find('{http://www.w3.org/2005/Atom}link').attrib['href']
                author = entry.find('{http://purl.org/dc/elements/1.1/}publisher').text if entry.find('{http://purl.org/dc/elements/1.1/}publisher') is not None else 'Unknown'
                
                books.append({
                    "title": title,
                    "link": link,
                    "author": author
                })
            
            return json.dumps(books, ensure_ascii=False)  # Ensure correct encoding for Japanese characters
        except ET.ParseError as e:
            st.error("Failed to parse XML. Error:")
            st.write(str(e))
            return None
    else:
        st.error(f"Error: {response.status_code}")
        st.write(response.text)
        return None

def get_books_by_keyword(arguments):
    res = get_books(
        keyword=arguments.get('keyword')
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_books_by_keyword",
            "description": "キーワードで書籍情報を検索し、関連する書籍情報を取得します",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "書籍情報を取得するための検索キーワード",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
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
            elif function_name == 'get_books_by_keyword':
                function_response = get_books_by_keyword(arguments)
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
st.title("Agent AI")

# Maintain chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Get user input (Move this part before the chat history display)
user_input = st.text_input("Input:", key="input_text")

# Add Send button and reset input
if st.button("Send"):
    if user_input:
        # Run the agent and update chat history
        llm_agent(user_input, st.session_state.chat_history)

# Display chat history after the input
st.write("Chat History:")
for message in st.session_state.chat_history:
    st.write(message)
