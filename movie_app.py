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
ENTRY_POSTER = "entry.1676316582"
ENTRY_YEAR = "entry.918552721"
ENTRY_TYPE = "entry.1234985263"
ENTRY_GENRE = "entry.2057116315"
ENTRY_TMDB_RATE = "entry.1608048686"
ENTRY_IMDB_RATE = "entry.958964522"
ENTRY_DURATION = "entry.1982271493"
ENTRY_TRUST = "entry.1829770777"
ENTRY_INTEREST = "entry.191577536"
ENTRY_WEIGHT = "entry.496039702"

st.set_page_config(page_title="Cinema Archive Pro", layout="wide")
st.title("🎬 My Cinema Archive")

menu = st.sidebar.radio("Menu", ["Add New Content", "View My Library"])

if menu == "Add New Content":
    query = st.text_input("Search Movie or TV Series:")
    if query:
        search_url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
        try:
            results = requests.get(search_url).json().get('results', [])
            
            for item in results[:5]:
                m_type = item.get('media_type', 'movie')
                if m_type not in ['movie', 'tv']: continue
                m_id = item['id']
                
                # 1. Fetch TMDB Data & Poster
                details = requests.get(f"https://api.themoviedb.org/3/{m_type}/{m_id}?api_key={TMDB_API_KEY}").json()
                title = details.get('title') or details.get('name')
                year = details.get('release_date', details.get('first_air_date', '????'))[:4]
                genres = ", ".join([g['name'] for g in details.get('genres', [])])
                poster_path = details.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""

                # 2. Fetch IMDB Rating (Triple-Check)
                imdb_rate = "N/A"
                try:
                    omdb_type = "series" if m_type == "tv" else "movie"
                    o_url = f"http://www.omdbapi.com/?t={title}&y={year}&type={omdb_type}&apikey={OMDB_API_KEY}"
                    o_res = requests.get(o_url).json()
                    imdb_rate = o_res.get('imdbRating', 'N/A')
                except: pass

                # 3. Deep Scan Duration
                total_mins = 0
                if m_type == "tv":
                    with st.spinner(f"Scanning episodes for {title}..."):
                        for season in details.get('seasons', []):
                            s_num = season.get('season_number')
                            if s_num == 0: continue
                            s_data = requests.get(f"https://api.themoviedb.org/3/tv/{m_id}/season/{s_num}?api_key={TMDB_API_KEY}").json()
                            for ep in s_data.get('episodes', []):
                                total_mins += ep.get('runtime', 0)
                else:
                    total_mins = details.get('runtime', 0)
                
                h, m = total_mins // 60, total_mins % 60
                dur_str = f"{h}h {m}m" if h > 0 else f"{total_mins}m"

                # --- UI DISPLAY & CURATION ---
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1.5])
                with col1:
                    if poster_url: st.image(poster_url)
                with col2:
                    st.subheader(f"{title} ({year})")
                    st.caption(f"🎭 {genres} | ⭐ IMDB: {imdb_rate} | ⏳ {dur_str}")
                with col3:
                    trust_val = st.slider("Trust Rating (2-5):", 2.0, 5.0, 4.0, 0.5, key=f"t_{m_id}")
                    interest_val = st.select_slider("Interest:", options=["Low", "Medium", "High"], value="High", key=f"i_{m_id}")
                    weight_map = {"High": 3, "Medium": 2, "Low": 1}
                    
                    if st.button("Add to Archive", key=f"btn_{m_id}"):
                        form_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse"
                        payload = {
                            ENTRY_NAME: title, ENTRY_POSTER: poster_url, ENTRY_YEAR: year,
                            ENTRY_TYPE: m_type, ENTRY_GENRE: genres, ENTRY_TMDB_RATE: details.get('vote_average', 0),
                            ENTRY_IMDB_RATE: imdb_rate, ENTRY_DURATION: dur_str,
                            ENTRY_TRUST: trust_val, ENTRY_INTEREST: interest_val,
                            ENTRY_WEIGHT: weight_map[interest_val]
                        }
                        requests.post(form_url, data=payload)
                        st.success(f"Archived {title}!")
        except Exception as e:
            st.error(f"Error: {e}")

elif menu == "View My Library":
    st.header("📋 My Watchlist")
    try:
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(f"{sheet_url}&cb={int(time.time())}")
        
        # --- SMART SORT LOGIC ---
        # Adjust these column names if your Google Sheet headers differ exactly
        # The code will attempt to find the interest/trust columns to sort
        sort_candidates = [col for col in df.columns if 'Weight' in col or 'Trust' in col]
        if len(sort_candidates) >= 2:
            # Assumes Weight is first priority, Trust is second
            df = df.sort_values(by=sort_candidates, ascending=[False, False])

        view = st.radio("View Mode", ["Gallery", "Table"], horizontal=True)
        if view == "Gallery":
            cols = st.columns(4)
            # Find the poster column dynamically
            poster_col = next((c for c in df.columns if 'Poster' in c or 'Image' in c), None)
            name_col = next((c for c in df.columns if 'Name' in c or 'Title' in c), "Name")

            for idx, row in df.reset_index().iterrows():
                with cols[idx % 4]:
                    if poster_col and pd.notna(row[poster_col]): st.image(row[poster_col])
                    st.write(f"**{row.get(name_col)}**")
                    st.caption(f"⭐ {row.get('Trust Rating', row.get('test9', 'N/A'))}")
        else:
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Sheet Error: {e}")
