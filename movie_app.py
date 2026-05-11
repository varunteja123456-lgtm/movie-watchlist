import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
TMDB_API_KEY = "1e08f4e7f84d8985db9da59d7d71e8e8"
FORM_ID = "1FAIpQLSd6QgvqLpdr8lpCRInZ7KJDT3Eiw25RfqAMkzhn1bdUJHmWhw"
# These are your form entry IDs
ENTRY_NAME = "entry.619367303" 
ENTRY_YEAR = "entry.918552721"
ENTRY_TYPE = "entry.1234985263"
ENTRY_RATE = "entry.1608048686"

st.set_page_config(page_title="Movie Tracker", layout="wide")

st.title("🎬 Global Movie Tracker")
menu = st.sidebar.radio("Menu", ["Add Movie", "View My Watchlist"])

if menu == "Add Movie":
    query = st.text_input("Search Movie/Series name:")
    if query:
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
        results = requests.get(url).json().get('results', [])
        for item in results[:5]:
            title = item.get('title') or item.get('name')
            year = item.get('release_date', item.get('first_air_date', '????'))[:4]
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{title}** ({year})")
            with col2:
                if st.button("Add to List", key=f"btn_{item['id']}"):
                    form_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
                    payload = {ENTRY_NAME: title, ENTRY_YEAR: year, ENTRY_TYPE: item.get('media_type'), ENTRY_RATE: item.get('vote_average')}
                    requests.post(form_url, data=payload)
                    st.success(f"Added {title}! (Wait 5 seconds and refresh Watchlist)")

elif menu == "View My Watchlist":
    st.header("📋 My Entries")
    try:
        import time
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # This trick forces Google to bypass the cache
        refresh_url = f"{sheet_url}&t={int(time.time())}"
        df = pd.read_csv(refresh_url)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("The list is empty. Add a movie first!")
    except Exception as e:
        st.error(f"Error reading watchlist: {e}")
