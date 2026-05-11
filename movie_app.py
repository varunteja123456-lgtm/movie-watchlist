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

# Try to load existing data from the Google Sheet
try:
    df = conn.read()
except Exception:
    # If the sheet is totally empty, create the structure
    df = pd.DataFrame(columns=["Name", "Year", "Type", "Rating"])

if menu == "Add Movie":
    query = st.text_input("Search Movie/Series name:")
    
    if query:
        # Search TMDB for results
        url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={query}"
        try:
            results = requests.get(url).json().get('results', [])
            
            if results:
                st.write("### Search Results:")
                for item in results[:5]:
                    title = item.get('title') or item.get('name')
                    year = item.get('release_date', item.get('first_air_date', '????'))[:4]
                    media_type = item.get('media_type', 'N/A')
                    rating = item.get('vote_average', 0)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{title}** ({year}) - {media_type.capitalize()}")
                    with col2:
                        if st.button("Add to List", key=f"btn_{item['id']}"):
                            # Create new row
                            new_row = pd.DataFrame([{
                                "Name": title,
                                "Year": year,
                                "Type": media_type,
                                "Rating": rating
                            }])
                            
                            # Combine old data with new row
                            updated_df = pd.concat([df, new_row], ignore_index=True)
                            
                            # Save back to Google Sheets
                            conn.update(data=updated_df)
                            st.success(f"Successfully saved '{title}'!")
                            st.rerun() # Refresh to update the internal data
            else:
                st.error("No results found.")
        except Exception as e:
            st.error(f"Search failed. Please check your keys or connection.")

elif menu == "View My Watchlist":
    st.header("📋 My Entries")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Your list is currently empty. Go to 'Add Movie' to start!")
