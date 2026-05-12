import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
TMDB_API_KEY = "1e08f4e7f84d8985db9da59d7d71e8e8"
OMDB_API_KEY = "28f7ec5e" 
FORM_ID = "1FAIpQLSd6QgvqLpdr8lpCRInZ7KJDT3Eiw25RfqAMkzhn1bdUJHmWhw"

# --- GOOGLE FORM ENTRY IDs ---
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

st.set_page_config(page_title="Varun's Buffet", layout="wide")
st.title("🍽️ Varun’s Cinematic Buffet")

menu = st.sidebar.radio("Navigation", ["Add to Watchlist", "View My Watchlist"])

if menu == "Add to Watchlist":
    query = st.text_input("Search for a Cinema or Web Series:")
    if query:
        search_url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
        try:
            results = requests.get(search_url).json().get('results', [])
            
            for item in results[:5]:
                m_type_raw = item.get('media_type', 'movie')
                if m_type_raw not in ['movie', 'tv']: continue
                m_id = item['id']
                
                # LOCALIZE TYPE NAME
                display_type = "Web Series" if m_type_raw == "tv" else "Cinema"
                
                details = requests.get(f"https://api.themoviedb.org/3/{m_type_raw}/{m_id}?api_key={TMDB_API_KEY}").json()
                title = details.get('title') or details.get('name')
                year = details.get('release_date', details.get('first_air_date', '????'))[:4]
                genres = ", ".join([g['name'] for g in details.get('genres', [])])
                poster_path = details.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""

                # IMDB Search
                imdb_rate = "N/A"
                try:
                    omdb_type = "series" if m_type_raw == "tv" else "movie"
                    o_res = requests.get(f"http://www.omdbapi.com/?t={title}&y={year}&type={omdb_type}&apikey={OMDB_API_KEY}").json()
                    imdb_rate = o_res.get('imdbRating', 'N/A')
                except: pass

                # Duration & Episode Logic
                total_mins = 0
                ep_count = 0
                if m_type_raw == "tv":
                    ep_count = details.get('number_of_episodes', 0)
                    with st.spinner(f"Counting episodes for {title}..."):
                        for season in details.get('seasons', []):
                            if season.get('season_number') == 0: continue
                            s_data = requests.get(f"https://api.themoviedb.org/3/tv/{m_id}/season/{season.get('season_number')}?api_key={TMDB_API_KEY}").json()
                            for ep in s_data.get('episodes', []):
                                total_mins += ep.get('runtime', 0)
                else:
                    total_mins = details.get('runtime', 0)
                
                h, m = total_mins // 60, total_mins % 60
                dur_str = f"{h}h {m}m" if h > 0 else f"{total_mins}m"
                if m_type_raw == "tv":
                    dur_str += f" ({ep_count} Episodes)"

                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1.5])
                with col1:
                    if poster_url: st.image(poster_url)
                with col2:
                    st.subheader(f"{title} ({year})")
                    st.write(f"📺 **Type:** {display_type}")
                    st.write(f"🎭 **Genre:** {genres}")
                    st.write(f"⭐ **IMDB:** {imdb_rate} | ⏳ **Total:** {dur_str}")
                with col3:
                    st.write("**Personal Taste**")
                    trust_val = st.slider("Trust Rating (2-5):", 2.0, 5.0, 4.0, 0.5, key=f"t_{m_id}")
                    interest_val = st.select_slider("My Interest:", options=["Low", "Medium", "High"], value="High", key=f"i_{m_id}")
                    
                    if st.button("Add to Watchlist", key=f"btn_{m_id}"):
                        weight_map = {"High": 3, "Medium": 2, "Low": 1}
                        payload = {
                            ENTRY_NAME: title, ENTRY_POSTER: poster_url, ENTRY_YEAR: year,
                            ENTRY_TYPE: display_type, ENTRY_GENRE: genres, 
                            ENTRY_IMDB_RATE: imdb_rate, ENTRY_DURATION: dur_str,
                            ENTRY_TRUST: trust_val, ENTRY_INTEREST: interest_val,
                            ENTRY_WEIGHT: weight_map[interest_val]
                        }
                        requests.post(f"https://docs.google.com/forms/d/e/{FORM_ID}/formResponse", data=payload)
                        st.success(f"Added this {display_type} to your buffet!")
        except Exception as e:
            st.error(f"Error: {e}")

elif menu == "View My Watchlist":
    st.header("🍴 Your Selected Buffet")
    try:
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(f"{sheet_url}&cb={int(time.time())}")
        
        # Dynamic Column Detection
        w_col = next((c for c in df.columns if 'Weight' in c), None)
        t_col = next((c for c in df.columns if 'Trust' in c), None)
        
        if w_col and t_col:
            df = df.sort_values(by=[w_col, t_col], ascending=[False, False])

        view = st.radio("Display Mode:", ["Visual Gallery", "Data Sheet"], horizontal=True)
        
        if view == "Visual Gallery":
            cols = st.columns(4)
            for idx, row in df.reset_index().iterrows():
                with cols[idx % 4]:
                    poster_link = row.get('Poster URL', row.get('test2'))
                    if pd.notna(poster_link): st.image(poster_link)
                    
                    st.markdown(f"### {row.get('Name')}")
                    # DISPLAYING "WEB SERIES" OR "CINEMA" IN GALLERY
                    st.caption(f"📅 {row.get('Year')} • 🎬 {row.get('Type')}")
                    st.markdown(f"⭐ **IMDB:** {row.get('IMDB Rating')} | ⏳ {row.get('Duration')}")
                    
                    interest = row.get('Interest Level', 'N/A')
                    color = {"High": "green", "Medium": "orange", "Low": "gray"}.get(interest, "blue")
                    st.markdown(f":{color}[❤️ {interest} Interest] | ⭐ **Trust:** {row.get('Trust Rating')}")
                    st.write("---")
        else:
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading your buffet: {e}")
