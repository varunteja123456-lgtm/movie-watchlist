import streamlit as st
import requests
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
TMDB_API_KEY = "1e08f4e7f84d8985db9da59d7d71e8e8"

# YOUR FORM DETAILS (Already filled in for you!)
FORM_ID = "1FAIpQLSd6QgvqLpdr8lpCRInZ7KJDT3Eiw25RfqAMkzhn1bdUJHmWhw"
ENTRY_NAME = "entry.619367303" 
ENTRY_YEAR = "entry.918552721"
ENTRY_TYPE = "entry.1234985263"
ENTRY_RATE = "entry.1608048686"

st.set_page_config(page_title="Movie Tracker", layout="wide")

# --- CONNECT TO GOOGLE SHEETS (For Viewing) ---
conn = st.connection("gsheets", type=GSheetsConnection)

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
                    # Submit to Google Form
                    form_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
                    payload = {
                        ENTRY_NAME: title,
                        ENTRY_YEAR: year,
                        ENTRY_TYPE: item.get('media_type', 'N/A'),
                        ENTRY_RATE: item.get('vote_average', 0)
                    }
                    try:
                        requests.post(form_url, data=payload)
                        st.success(f"Added {title}! It will appear in your list shortly.")
                    except Exception as e:
                        st.error(f"Failed to add: {e}")

elif menu == "View My Watchlist":
    st.header("📋 My Entries")
    # Make sure your Streamlit Secrets still has your Google Sheet URL
    df = conn.read()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Your list is currently empty.")
