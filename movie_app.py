import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
TMDB_API_KEY = "1e08f4e7f84d8985db9da59d7d71e8e8"
OMDB_API_KEY = "28f7ec5e" 
FORM_ID = "1FAIpQLSd6QgvqLpdr8lpCRInZ7KJDT3Eiw25RfqAMkzhn1bdUJHmWhw"

# --- GOOGLE FORM ENTRY IDs (Calibrated to your link) ---
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
        # Step 1: Search TMDB (The big database)
        search_url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
        try:
            results = requests.get(search_url).json().get('results', [])
            
            for item in results[:5]:
                m_type = item.get('media_type', 'movie')
                if m_type not in ['movie', 'tv']: continue
                m_id = item['id']
                
                # --- FETCH DEEP DATA FROM TMDB ---
                detail_url = f"https://api.themoviedb.org/3/{m_type}/{m_id}?api_key={TMDB_API_KEY}"
                details = requests.get(detail_url).json()
                
                title = details.get('title') or details.get('name')
                year = details.get('release_date', details.get('first_air_date', '????'))[:4]
                tmdb_rate = details.get('vote_average', 0)
                genres = ", ".join([g['name'] for g in details.get('genres', [])])
                
               # --- SUPER SEARCHER FOR IMDB ---
                imdb_rate = "N/A"
                try:
                    omdb_type = "series" if m_type == "tv" else "movie"
                    # Clean the title (remove everything after a colon or dash for better matching)
                    base_title = title.split(':')[0].split('-')[0].strip()
                    
                    # 1st Try: Original Title + Year
                    omdb_url = f"http://www.omdbapi.com/?t={title}&y={year}&type={omdb_type}&apikey={OMDB_API_KEY}"
                    res = requests.get(omdb_url).json()
                    
                    if res.get('Response') == 'True':
                        imdb_rate = res.get('imdbRating', 'N/A')
                    else:
                        # 2nd Try: Cleaned Title (No colons/subtitles)
                        omdb_url_clean = f"http://www.omdbapi.com/?t={base_title}&type={omdb_type}&apikey={OMDB_API_KEY}"
                        res_clean = requests.get(omdb_url_clean).json()
                        if res_clean.get('Response') == 'True':
                            imdb_rate = res_clean.get('imdbRating', 'N/A')
                        else:
                            # 3rd Try: Just Title (Broadest search)
                            omdb_url_broad = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
                            res_broad = requests.get(omdb_url_broad).json()
                            imdb_rate = res_broad.get('imdbRating', 'N/A')
                except:
                    imdb_rate = "N/A"

                # --- DEEP SCAN DURATION LOGIC ---
                total_mins = 0
                if m_type == "tv":
                    with st.spinner(f"Scanning all episodes for {title}..."):
                        for season in details.get('seasons', []):
                            s_num = season.get('season_number')
                            if s_num == 0: continue # Skip 'Specials'
                            s_url = f"https://api.themoviedb.org/3/tv/{m_id}/season/{s_num}?api_key={TMDB_API_KEY}"
                            s_data = requests.get(s_url).json()
                            for ep in s_data.get('episodes', []):
                                total_mins += ep.get('runtime', 0)
                else:
                    total_mins = details.get('runtime', 0)

                # --- FORMAT DURATION (Human Readable) ---
                hours = total_mins // 60
                rem_mins = total_mins % 60

                if hours > 0:
                    h_label = "hour" if hours == 1 else "hours"
                    m_label = "minute" if rem_mins == 1 else "minutes"
                    duration_str = f"{hours} {h_label} {rem_mins} {m_label}"
                else:
                    m_label = "minute" if total_mins == 1 else "minutes"
                    duration_str = f"{total_mins} {m_label}"

                # --- UI DISPLAY ---
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{title}** ({year})")
                    st.caption(f"🎭 {genres} | ⭐ TMDB: {tmdb_rate} | ⭐ IMDB: {imdb_rate} | ⏳ {duration_str}")
                
                with col2:
                    if st.button("Add to List", key=f"btn_{m_id}"):
                        form_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
                        payload = {
                            ENTRY_NAME: title, ENTRY_YEAR: year, ENTRY_TYPE: m_type,
                            ENTRY_GENRE: genres, ENTRY_TMDB_RATE: tmdb_rate,
                            ENTRY_IMDB_RATE: imdb_rate, ENTRY_DURATION: duration_str
                        }
                        # Send the data to Google Forms
                        r = requests.post(form_url, data=payload)
                        if r.status_code == 200:
                            st.success(f"Added {title}!")
                        else:
                            st.error(f"Error {r.status_code}. Make sure Form doesn't require login.")
                            
        except Exception as e:
            st.error(f"Something went wrong: {e}")

elif menu == "View My Watchlist":
    st.header("📋 My Watchlist")
    try:
        # Fetching the CSV from the 'Published' URL in Secrets
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # Force a refresh with a timestamp
        df = pd.read_csv(f"{sheet_url}&cachebuster={int(time.time())}")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load data. Ensure your Sheet is Published to Web as CSV. Error: {e}")
