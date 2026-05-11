import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
TMDB_API_KEY = "1e08f4e7f84d8985db9da59d7d71e8e8"
OMDB_API_KEY = "28f7ec5e" 
FORM_ID = "1FAIpQLSd6QgvqLpdr8lpCRInZ7KJDT3Eiw25RfqAMkzhn1bdUJHmWhw"

# --- GOOGLE FORM ENTRY IDs (Mapped from your link) ---
ENTRY_NAME = "entry.619367303"
ENTRY_YEAR = "entry.918552721"
ENTRY_TYPE = "entry.1234985263"
ENTRY_GENRE = "entry.2057116315"      
ENTRY_TMDB_RATE = "entry.1608048686"
ENTRY_IMDB_RATE = "entry.958964522"  
ENTRY_DURATION = "entry.1982271493"   

st.set_page_config(page_title="Ultimate Movie Tracker", layout="wide")
st.title("🎬 Global Movie & Series Tracker")

menu = st.sidebar.radio("Menu", ["Add Movie", "View My Watchlist"])

if menu == "Add Movie":
    query = st.text_input("Search Movie or TV Series:")
    if query:
        search_url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
        try:
            results = requests.get(search_url).json().get('results', [])
            
            for item in results[:5]:
                m_type = item.get('media_type', 'movie')
                if m_type not in ['movie', 'tv']: continue
                m_id = item['id']
                
                # 1. Fetch TMDB Deep Data
                detail_url = f"https://api.themoviedb.org/3/{m_type}/{m_id}?api_key={TMDB_API_KEY}"
                details = requests.get(detail_url).json()
                
                title = details.get('title') or details.get('name')
                year = details.get('release_date', details.get('first_air_date', '????'))[:4]
                tmdb_rate = details.get('vote_average', 0)
                genres = ", ".join([g['name'] for g in details.get('genres', [])])
                
                # 2. Fetch IMDB Rating from OMDB
                imdb_rate = "N/A"
                try:
                    omdb_res = requests.get(f"http://www.omdbapi.com/?t={title}&y={year}&apikey={OMDB_API_KEY}").json()
                    imdb_rate = omdb_res.get('imdbRating', 'N/A')
                except: pass

                # 3. Deep Scan Duration Logic
                total_mins = 0
                if m_type == "tv":
                    with st.spinner(f"Deep scanning episodes for {title}..."):
                        for season in details.get('seasons', []):
                            s_num = season.get('season_number')
                            if s_num == 0: continue 
                            s_url = f"https://api.themoviedb.org/3/tv/{m_id}/season/{s_num}?api_key={TMDB_API_KEY}"
                            s_data = requests.get(s_url).json()
                            for ep in s_data.get('episodes', []):
                                total_mins += ep.get('runtime', 0)
                else:
                    total_mins = details.get('runtime', 0)

                # --- CUSTOM DURATION FORMATTING ---
                hours = total_mins // 60
                rem_mins = total_mins % 60

                if hours > 0:
                    h_text = f"{hours} hour" if hours == 1 else f"{hours} hours"
                    m_text = f"{rem_mins} minute" if rem_mins == 1 else f"{rem_mins} minutes"
                    duration = f"{h_text} {m_text}"
                else:
                    duration = f"{total_mins} minute" if total_mins == 1 else f"{total_mins} minutes"

                # 4. Display UI
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{title}** ({year})")
                    st.caption(f"🎭 {genres} | ⭐ TMDB: {tmdb_rate} | ⭐ IMDB: {imdb_rate} | ⏳ {duration}")
                
                with col2:
                    if st.button("Add to List", key=f"btn_{m_id}"):
                        form_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
                        payload = {
                            ENTRY_NAME: title, ENTRY_YEAR: year, ENTRY_TYPE: m_type,
                            ENTRY_GENRE: genres, ENTRY_TMDB_RATE: tmdb_rate,
                            ENTRY_IMDB_RATE: imdb_rate, ENTRY_DURATION: duration
                        }
                        r = requests.post(form_url, data=payload)
                        if r.status_code == 200:
                            st.success(f"Added {title}!")
                        else:
                            st.error(f"Error {r.status_code}. Check Form Privacy Settings.")
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")

elif menu == "View My Watchlist":
    st.header("📋 My Personal Watchlist")
    try:
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(f"{sheet_url}&cachebust={int(time.time())}")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load data. Check if your Sheet is 'Published to Web' as CSV. Error: {e}")
