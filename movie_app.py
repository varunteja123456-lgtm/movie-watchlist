import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd

# --- CONFIGURATION ---
TMDB_API_KEY = "1e08f4e7f84d8985db9da59d7d71e8e8" 
OMDB_API_KEY = "28f7ec5e"

st.set_page_config(page_title="Movie Tracker", layout="wide")

# --- CONNECT TO GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🎬 Global Movie Tracker")
menu = st.sidebar.radio("Menu", ["Add Movie", "View My Watchlist"])

# Try to load existing data
try:
    df = conn.read()
except Exception:
    df = pd.DataFrame(columns=["Name", "Year", "Type", "Rating"])

if menu == "Add Movie":
    query = st.text_input("Search Movie/Series name:")
    
    if query:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
        try:
            response = requests.get(url)
            results = response.json().get('results', [])
            
            if results:
                for item in results[:5]:
                    title = item.get('title') or item.get('name')
                    year = item.get('release_date', item.get('first_air_date', '????'))[:4]
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{title}** ({year})")
                    with col2:
                        if st.button("Add to List", key=f"btn_{item['id']}"):
                            new_row = pd.DataFrame([{
                                "Name": title,
                                "Year": year,
                                "Type": item.get('media_type', 'N/A'),
                                "Rating": item.get('vote_average', 0)
                            }])
                            updated_df = pd.concat([df, new_row], ignore_index=True)
                            conn.update(data=updated_df)
                            st.success(f"Added {title}!")
                            st.rerun()
            else:
                st.error("No results found.")
        except Exception as e:
            st.error(f"Error: {e}")

elif menu == "View My Watchlist":
    st.header("📋 My Entries")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Your list is currently empty.")
