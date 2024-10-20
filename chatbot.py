import streamlit as st
import pandas as pd
import os
from pandasai import Agent
import matplotlib.pyplot as plt
import requests
from translatepy import Translator
from gtts import gTTS
import mysql.connector
from mysql.connector import Error

# Function to check internet connectivity
def check_connectivity():
    url = "http://www.google.com"
    timeout = 5
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

# Set the PANDASAI_API_KEY environment variable directly in the code
os.environ['PANDASAI_API_KEY'] = '$2a$10$pTODw4eDi3lLS7hAj79hjutd5ekmCrlRel1TuZzFf2o7ULlLPN0g'

# Function for pandas ai to query a DataFrame
def chat_with_csv(df, prompt):
    try:
        agent = Agent(dfs=[df])
        result = agent.chat(prompt)
        return result
    except Exception as e:
        return f"An error occurred: {e}"

# Function to translate text to the specified language
def translate_text(text, target_language):
    translator = Translator()
    translated_text = translator.translate(text, target_language)
    return translated_text.result

# Function to generate speech from text using gTTS
def generate_speech(text, lang):
    tts = gTTS(text=text, lang=lang)
    audio_path = "response.mp3"
    tts.save(audio_path)
    return audio_path

# Function to fetch data from MySQL database
def fetch_data_from_mysql(host, database, user, password, query):
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        if connection.is_connected():
            df = pd.read_sql(query, connection)
            return df
    except Error as e:
        return f"Error while connecting to MySQL: {e}"
    finally:
        if (connection.is_connected()):
            connection.close()

# Initialize session state for chat history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

st.set_page_config(layout='wide')
st.title("🦊QueryBot")

# Check connectivity status
connectivity_status = check_connectivity()

# Display a warning message based on connectivity status
if connectivity_status is False:
    st.warning("⚠️ You are currently offline. Please check your internet connection.")
else:
    st.success("✅ You are connected to the internet.")

# Add a help icon with an expander
with st.expander("❓ About 🦊QueryBot"):
    st.markdown("""
    🦊QueryBot is a versatile tool designed to help you interact with your CSV files using natural language queries. 
    You can perform the following operations:
    - **Data Summarization**: Ask for summaries of your data, such as average values, total counts, or unique entries.
    - **Data Visualization**: Generate visualizations of your data over a specified time period.
    - **Custom Queries**: Ask custom questions related to the data in your CSV file and get specific answers.
    
    **How to use**:
    1. **Upload a CSV File**: Use the file uploader to upload your CSV file.
    2. **Visualize Data**: Select a column and visualize its data over a specified time period.
    3. **Ask Questions**: Enter your query in the text area and get responses about your data.
    
    We hope 🦊QueryBot enhances your data analysis experience!
    """)

# Add an option to choose data source (CSV or MySQL)
data_source = st.selectbox('Select Data Source', ['CSV File', 'MySQL Database'])

def visualize_data(df, column_to_plot):
    # Assuming 'value' is the column in your dataframe that contains the data you want to visualize
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Process the selected column to get 12 data points (for simplicity, taking a random sample)
    monthly_data = df[column_to_plot].sample(12, random_state=1)  # Replace with your actual processing logic

    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(months, monthly_data, marker='o')
    plt.xlabel('Month')
    plt.ylabel(column_to_plot)
    plt.title('Monthly Data')
    st.pyplot(plt)

if data_source == 'CSV File':
    # Add help text to file uploader
    input_csv = st.file_uploader("Upload your csv file (Ensure it's a csv file)", type=['csv'])

    if input_csv is not None:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.success("CSV file uploaded successfully")
            data = pd.read_csv(input_csv)
            st.dataframe(data)

            # Let the user select a column to visualize
            column_to_plot = st.selectbox('Select a column to visualize', data.columns)

            # Add an option to visualize the data over a time period of 5 years and months
            if st.button("Visualize Time Series"):
                visualize_data(data, column_to_plot)

        with col2:
            st.info("Chat with your CSV")

            input_text = st.text_area("Enter your query")
            language_options = {
                'English': 'en',
                'Spanish': 'es',
                'French': 'fr',
                'German': 'de',
                'Hindi': 'hi',
                'Chinese': 'zh',
                'Telugu': 'te',
                'Tamil': 'ta'
            }
            target_language = st.selectbox('Select language for response', list(language_options.keys()))

            if st.button("Ask"):
                if input_text:
                    st.info("Your query: " + input_text)
                    with st.spinner('Processing your query...'):
                        result = chat_with_csv(data, input_text)
                    
                    result_str = str(result)

                    translated_result = translate_text(result_str, language_options[target_language])
                    
                    audio_path = generate_speech(translated_result, language_options[target_language])
                    
                    st.success(translated_result)

                    # Play the audio file directly in the app
                    audio_file = open(audio_path, "rb")
                    st.audio(audio_file, format='audio/mp3')

                    # Add user query to session state chat history
                    st.session_state['chat_history'].append(("You", input_text))
                    st.session_state['chat_history'].append(("Bot", translated_result))

elif data_source == 'MySQL Database':
    st.info("Enter MySQL Database Connection Details")

    host = st.text_input("Host")
    database = st.text_input("Database")
    user = st.text_input("User")
    password = st.text_input("Password", type='password')
    query = st.text_area("SQL Query")

    if st.button("Connect and Fetch Data"):
        with st.spinner('Connecting to MySQL Database and fetching data...'):
            data = fetch_data_from_mysql(host, database, user, password, query)
        
        if isinstance(data, pd.DataFrame):
            st.success("Data fetched successfully from MySQL database")
            st.dataframe(data)

            col1, col2 = st.columns([1, 1])

            with col1:
                # Let the user select a column to visualize
                column_to_plot = st.selectbox('Select a column to visualize', data.columns)

                # Add an option to visualize the data over a time period of 5 years and months
                if st.button("Visualize Time Series"):
                    visualize_data(data, column_to_plot)

            with col2:
                st.info("Chat with your MySQL Data")

                input_text = st.text_area("Enter your query")
                language_options = {
                    'English': 'en',
                    'Spanish': 'es',
                    'French': 'fr',
                    'German': 'de',
                    'Hindi': 'hi',
                    'Chinese': 'zh',
                    'Telugu': 'te',
                    'Tamil': 'ta'
                }
                target_language = st.selectbox('Select language for response', list(language_options.keys()))

                if st.button("Ask"):
                    if input_text:
                        st.info("Your query: " + input_text)
                        with st.spinner('Processing your query...'):
                            result = chat_with_csv(data, input_text)
                        
                        result_str = str(result)

                        translated_result = translate_text(result_str, language_options[target_language])
                        
                        audio_path = generate_speech(translated_result, language_options[target_language])
                        
                        st.success(translated_result)

                        # Play the audio file directly in the app
                        audio_file = open(audio_path, "rb")
                        st.audio(audio_file, format='audio/mp3')

                        # Add user query to session state chat history
                        st.session_state['chat_history'].append(("You", input_text))
                        st.session_state['chat_history'].append(("Bot", translated_result))

# Display the chat history in the sidebar
st.sidebar.header("Chat History")
for role, text in st.session_state['chat_history']:
    st.sidebar.write(f"{role}: {text}")
