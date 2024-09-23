# Sample Code for a Generative AI Agent
This repository contains sample code demonstrating a generative AI agent that integrates various functionalities such as stock price retrieval, weather forecasting, book information retrieval, Wikipedia information extraction, and natural language chat. Each function showcases how to interact with external APIs (e.g., Stooq for stock prices, OpenWeather for weather data, CiNii Books for book information, and Wikipedia for general knowledge) and process responses in a structured manner using Python and Streamlit for the interface.

## Features:
- **Stock Price Retrieval:** Fetches real-time stock prices for a specified company between two dates using the Stooq data source.
- **Weather Forecast:** Retrieves current weather data for any location using the OpenWeather API by providing latitude and longitude.
- **Book Information Retrieval:** Allows users to search for books by keywords and retrieve related book information, such as title, author, and a link to the book's details, using the CiNii Books OpenSearch API.
- **Wikipedia Information Retrieval:** Fetches introductory information from Japanese Wikipedia based on a given keyword using the MediaWiki API.
- **Chat Functionality:** A simple natural language interaction for general chat responses, including integration with various tools like stock prices, weather information, and book searches.
- **ReAct-based Question Answering** (`react.ipynb`): Demonstrates how to use the ReAct (Reasoning + Acting) framework to answer user questions by combining tools like stock price retrieval, calculation, and general knowledge. This notebook shows how ReAct integrates reasoning through intermediate steps and tool usage to provide structured, accurate answers.

## Environment Setup
> conda create -n agent python=3.11  
> conda activate agent  

> pip install notebook ipython  
> pip install python-dotenv pandas_datareader openai  
> pip install streamlit  

> pip install langchain langchain_community yfinance gtts langchain-openai duckduckgo-search  
> pip install google-search-results numexprpyowm langchain-google-genai langgraph  
  

## API Key
Create a .env file and add the following code:
> OPENAI_API_KEY=xxxxxxxx    

**Running the Agent**

To run the agent as a Streamlit app:

> conda activate agent    
> streamlit run agent.py  

**Running ReAct Notebook**

To run the ReAct example in react.ipynb, open the notebook in Jupyter or any notebook interface:

> jupyter notebook react.ipynb  
