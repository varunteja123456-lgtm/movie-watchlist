import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd

# --- 1. CONFIGURATION (Edit these two) ---
TMDB_API_KEY = "1e08f4e7f84d8985db9da59d7d71e8e8" 
OMDB_API_KEY = "28f7ec5e"

st.set_page_config(page_title="Movie Tracker", layout="wide")

# --- 2. CLOUD DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. UI SETUP ---
st.title("🎬 Global Movie Tracker")
menu = st.sidebar.radio("Menu", ["Add Movie", "View My Watchlist"])

if menu == "Add Movie":
    query = st.text_input("Search Movie/Series name:")
    
    if query:
        # Search TMDB for results
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
        response = requests.get(url).json()
        results = response.get('results', [])
        
        if results:
            for item in results[:5]:
                title = item.get('title') or item.get('name')
                year = item.get('release_date', item.get('first_air_date', '????'))[:4]
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{title}** ({year})")
                with col2:
                    if st.button("Add to List", key=item['id']):
                        # This creates the data to send to Google Sheets
                        new_entry = pd.DataFrame([{
                            "Name": title,
                            "Year": year,
                            "Type": item.get('media_type'),
                            "Rating": item.get('vote_average')
                        }])
                        # Logic to update Google Sheet will go here once we link it
                        st.success(f"Added {title}!")
        else:
            st.error("No results found.")

elif menu == "View My Watchlist":
    st.header("📋 My Entries")
    try:
        data = conn.read()
        st.dataframe(data)
    except:
        st.info("Your list is currently empty.")