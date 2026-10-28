
import os
import random
from io import BytesIO

import cv2
import numpy as np
import streamlit as st
from PIL import Image

# Spotify is optional. The app still works with demo songs if it is not
# installed or if Spotify credentials have not been configured.
try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    from spotipy.cache_handler import CacheHandler

    SPOTIFY_AVAILABLE = True
except ImportError:
    SPOTIFY_AVAILABLE = False


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="MoodLens | Music for your mood",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: linear-gradient(145deg, #101525 0%, #171b30 55%, #202440 100%);
        color: #F1FAEE;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #F1FAEE !important;
    }

    .hero {
        padding: 2rem 0 1rem 0;
    }

    .hero-kicker {
        color: #A8DADC;
        text-transform: uppercase;
        letter-spacing: 3px;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(2.7rem, 6vw, 4.8rem);
        font-weight: 700;
        line-height: 1.05;
        color: #F1FAEE;
        margin: 0.5rem 0;
    }

    .hero-title span {
        color: #E63946;
    }

    .hero-subtitle {
        color: #B8C3D9;
        font-size: 1.08rem;
        max-width: 700px;
        line-height: 1.7;
    }

    .section-label {
        color: #A8DADC;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .song-card {
        background: rgba(255, 255, 255, 0.055);
        border: 1px solid rgba(168, 218, 220, 0.18);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .song-title {
        color: #F1FAEE;
        font-weight: 700;
        font-size: 1rem;
    }

    .song-artist {
        color: #B8C3D9;
        font-size: 0.88rem;
        margin-top: 0.25rem;
    }

    .song-meta {
        color: #A8DADC;
        font-size: 0.78rem;
        margin-top: 0.65rem;
    }

    div.stButton > button[kind="primary"] {
        background: #E63946;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        padding: 0.7rem 1rem;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #C92D3A;
        color: white;
    }

    [data-testid="stSidebar"] {
        background: #111625;
    }

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.04);
        padding: 1rem;
        border-radius: 12px;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        color: #B8C3D9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# MOOD SETTINGS
# ---------------------------------------------------------

MOOD_TARGETS = {
    "Match my mood": {
        "happy": ("happy", 0.82),
        "sad": ("sad", 0.28),
        "angry": ("energized", 0.78),
        "surprised": ("energized", 0.82),
        "neutral": ("focused", 0.42),
        "calm": ("calm", 0.32),
    },
    "Shift my mood": {
        "happy": ("calm", 0.38),
        "sad": ("happy", 0.75),
        "angry": ("calm", 0.25),
        "surprised": ("focused", 0.45),
        "neutral": ("happy", 0.72),
        "calm": ("energized", 0.76),
    },
}

MOOD_EMOJIS = {
    "happy": "😊",
    "sad": "🌧️",
    "angry": "🔥",
    "surprised": "⚡",
    "neutral": "🌙",
    "calm": "🌿",
    "energized": "⚡",
    "focused": "🎯",
}

MOOD_DESCRIPTIONS = {
    "happy": "Keep the good energy going.",
    "sad": "Music for a quieter moment.",
    "angry": "Channel that energy into music.",
    "surprised": "Follow the unexpected energy.",
    "neutral": "Find your rhythm and focus.",
    "calm": "Slow things down and breathe.",
    "energized": "Turn up the energy.",
    "focused": "Settle into a focused flow.",
}


# ---------------------------------------------------------
# DEMO SONG CATALOGUE
# ---------------------------------------------------------

DEMO_SONGS = [
    {
        "title": "Good as Hell",
        "artist": "Lizzo",
        "genre": "Pop",
        "mood": "happy",
        "energy": 0.84,
        "url": "https://open.spotify.com/search/Good%20as%20Hell%20Lizzo",
    },
    {
        "title": "Levitating",
        "artist": "Dua Lipa",
        "genre": "Pop",
        "mood": "happy",
        "energy": 0.82,
        "url": "https://open.spotify.com/search/Levitating%20Dua%20Lipa",
    },
    {
        "title": "Walking on Sunshine",
        "artist": "Katrina and the Waves",
        "genre": "Pop",
        "mood": "happy",
        "energy": 0.88,
        "url": "https://open.spotify.com/search/Walking%20on%20Sunshine",
    },
    {
        "title": "Sunflower",
        "artist": "Post Malone, Swae Lee",
        "genre": "Pop",
        "mood": "calm",
        "energy": 0.48,
        "url": "https://open.spotify.com/search/Sunflower%20Post%20Malone",
    },
    {
        "title": "Someone Like You",
        "artist": "Adele",
        "genre": "Pop",
        "mood": "sad",
        "energy": 0.25,
        "url": "https://open.spotify.com/search/Someone%20Like%20You%20Adele",
    },
    {
        "title": "The Night We Met",
        "artist": "Lord Huron",
        "genre": "Indie",
        "mood": "sad",
        "energy": 0.22,
        "url": "https://open.spotify.com/search/The%20Night%20We%20Met",
    },
    {
        "title": "when the party's over",
        "artist": "Billie Eilish",
        "genre": "Alternative",
        "mood": "sad",
        "energy": 0.18,
        "url": "https://open.spotify.com/search/when%20the%20party%27s%20over",
    },
    {
        "title": "Numb",
        "artist": "Linkin Park",
        "genre": "Rock",
        "mood": "energized",
        "energy": 0.82,
        "url": "https://open.spotify.com/search/Numb%20Linkin%20Park",
    },
    {
        "title": "Believer",
        "artist": "Imagine Dragons",
        "genre": "Rock",
        "mood": "energized",
        "energy": 0.87,
        "url": "https://open.spotify.com/search/Believer%20Imagine%20Dragons",
    },
    {
        "title": "Seven Nation Army",
        "artist": "The White Stripes",
        "genre": "Rock",
        "mood": "energized",
        "energy": 0.76,
        "url": "https://open.spotify.com/search/Seven%20Nation%20Army",
    },
    {
        "title": "Weightless",
        "artist": "Marconi Union",
        "genre": "Ambient",
        "mood": "calm",
        "energy": 0.12,
        "url": "https://open.spotify.com/search/Weightless%20Marconi%20Union",
    },
    {
        "title": "Clair de Lune",
        "artist": "Claude Debussy",
        "genre": "Classical",
        "mood": "calm",
        "energy": 0.15,
        "url": "https://open.spotify.com/search/Clair%20de%20Lune%20Debussy",
    },
    {
        "title": "River Flows in You",
        "artist": "Yiruma",
        "genre": "Classical",
        "mood": "calm",
        "energy": 0.24,
        "url": "https://open.spotify.com/search/River%20Flows%20in%20You%20Yiruma",
    },
    {
        "title": "Experience",
        "artist": "Ludovico Einaudi",
        "genre": "Classical",
        "mood": "focused",
        "energy": 0.43,
        "url": "https://open.spotify.com/search/Experience%20Ludovico%20Einaudi",
    },
    {
        "title": "Time",
        "artist": "Hans Zimmer",
        "genre": "Soundtrack",
        "mood": "focused",
        "energy": 0.45,
        "url": "https://open.spotify.com/search/Time%20Hans%20Zimmer",
    },
    {
        "title": "Intro",
        "artist": "The xx",
        "genre": "Indie",
        "mood": "focused",
        "energy": 0.38,
        "url": "https://open.spotify.com/search/Intro%20The%20xx",
    },
    {
        "title": "Blinding Lights",
        "artist": "The Weeknd",
        "genre": "Pop",
        "mood": "energized",
        "energy": 0.80,
        "url": "https://open.spotify.com/search/Blinding%20Lights%20The%20Weeknd",
    },
    {
        "title": "As It Was",
        "artist": "Harry Styles",
        "genre": "Pop",
        "mood": "happy",
        "energy": 0.73,
        "url": "https://open.spotify.com/search/As%20It%20Was%20Harry%20Styles",
    },
    {
        "title": "Ocean Eyes",
        "artist": "Billie Eilish",
        "genre": "Alternative",
        "mood": "calm",
        "energy": 0.30,
        "url": "https://open.spotify.com/search/Ocean%20Eyes%20Billie%20Eilish",
    },
    {
        "title": "Do I Wanna Know?",
        "artist": "Arctic Monkeys",
        "genre": "Rock",
        "mood": "focused",
        "energy": 0.55,
        "url": "https://open.spotify.com/search/Do%20I%20Wanna%20Know%20Arctic%20Monkeys",
    },
    {
        "title": "Shake It Off",
        "artist": "Taylor Swift",
        "genre": "Pop",
        "mood": "happy",
        "energy": 0.86,
        "url": "https://open.spotify.com/search/Shake%20It%20Off%20Taylor%20Swift",
    },
    {
        "title": "Fix You",
        "artist": "Coldplay",
        "genre": "Alternative",
        "mood": "sad",
        "energy": 0.32,
        "url": "https://open.spotify.com/search/Fix%20You%20Coldplay",
    },
    {
        "title": "Lose Yourself",
        "artist": "Eminem",
        "genre": "Hip-Hop",
        "mood": "energized",
        "energy": 0.90,
        "url": "https://open.spotify.com/search/Lose%20Yourself%20Eminem",
    },
    {
        "title": "Nocturne Op. 9 No. 2",
        "artist": "Frédéric Chopin",
        "genre": "Classical",
        "mood": "calm",
        "energy": 0.20,
        "url": "https://open.spotify.com/search/Chopin%20Nocturne%20Op%209%20No%202",
    },
    {
        "title": "Electric Feel",
        "artist": "MGMT",
        "genre": "Indie",
        "mood": "happy",
        "energy": 0.77,
        "url": "https://open.spotify.com/search/Electric%20Feel%20MGMT",
    },
]


# ---------------------------------------------------------
# SPOTIFY CONFIGURATION
# ---------------------------------------------------------

def get_spotify_credentials():
    """Read Spotify credentials from Streamlit secrets or environment."""
    try:
        client_id = st.secrets.get("SPOTIFY_CLIENT_ID", "")
        client_secret = st.secrets.get("SPOTIFY_CLIENT_SECRET", "")
        redirect_uri = st.secrets.get("SPOTIFY_REDIRECT_URI", "")
    except Exception:
        client_id = ""
        client_secret = ""
        redirect_uri = ""

    client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET", "")
    redirect_uri = (
        redirect_uri
        or os.getenv("SPOTIFY_REDIRECT_URI", "")
        or "http://localhost:8501"
    )

    return client_id, client_secret, redirect_uri


class SessionTokenCache(CacheHandler):
    """Keep the Spotify OAuth token in this Streamlit session."""

    def get_cached_token(self):
        return st.session_state.get("spotify_token_info")

    def save_token_to_cache(self, token_info):
        st.session_state["spotify_token_info"] = token_info


def get_spotify_auth_manager():
    if not SPOTIFY_AVAILABLE:
        return None

    client_id, client_secret, redirect_uri = get_spotify_credentials()

    if not client_id or not client_secret:
        return None

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="playlist-modify-private playlist-modify-public",
        cache_handler=SessionTokenCache(),
        open_browser=False,
        show_dialog=True,
    )


def get_spotify_client():
    """Return an authenticated Spotify client, or None if unavailable."""
    if not SPOTIFY_AVAILABLE:
        return None

    auth_manager = get_spotify_auth_manager()
    if auth_manager is None:
        return None

    try:
        token_info = st.session_state.get("spotify_token_info")
        if token_info and auth_manager.is_token_expired(token_info):
            token_info = auth_manager.refresh_access_token(
                token_info["refresh_token"]
            )
            st.session_state["spotify_token_info"] = token_info

        if token_info:
            return spotipy.Spotify(auth_manager=auth_manager)

    except Exception as exc:
        st.session_state["spotify_error"] = str(exc)

    return None


def get_spotify_search_client():
    """Create a client-credentials client for searching Spotify."""
    if not SPOTIFY_AVAILABLE:
        return None

    client_id, client_secret, _ = get_spotify_credentials()
    if not client_id or not client_secret:
        return None

    try:
        from spotipy.oauth2 import SpotifyClientCredentials

        return spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
            )
        )
    except Exception:
        return None


def spotify_search_songs(target_mood, target_energy, genre, limit):
    """Search Spotify for tracks using the target mood and selected genre."""
    client = get_spotify_search_client()
    if client is None:
        return []

    mood_terms = {
        "happy": "feel good upbeat",
        "sad": "sad emotional",
        "calm": "calm relaxing",
        "energized": "high energy upbeat",
        "focused": "focus instrumental",
    }

    genre_query = "" if genre == "All genres" else f" genre:{genre.lower()}"
    query = f"{mood_terms.get(target_mood, target_mood)}{genre_query}"

    try:
        results = client.search(
            q=query,
            type="track",
            limit=min(50, max(limit * 3, 15)),
            market="AE",
        )

        tracks = results.get("tracks", {}).get("items", [])
        songs = []
        seen_ids = set()

        for track in tracks:
            if not track or track["id"] in seen_ids:
                continue

            seen_ids.add(track["id"])
            artists = ", ".join(
                artist["name"] for artist in track.get("artists", [])
            )
            images = track.get("album", {}).get("images", [])
            image_url = images[0]["url"] if images else None

            songs.append(
                {
                    "title": track.get("name", "Unknown track"),
                    "artist": artists or "Unknown artist",
                    "genre": genre if genre != "All genres" else "Spotify",
                    "mood": target_mood,
                    "energy": target_energy,
                    "url": track.get("external_urls", {}).get(
                        "spotify", "https://open.spotify.com/"
                    ),
                    "spotify_id": track["id"],
                    "image": image_url,
                    "source": "Spotify",
                }
            )

            if len(songs) >= limit:
                break

        return songs

    except Exception as exc:
        st.session_state["spotify_search_error"] = str(exc)
        return []


# ---------------------------------------------------------
# FACIAL-EXPRESSION RECOGNITION
# ---------------------------------------------------------

@st.cache_resource
def get_deepface():
    """Load DeepFace once per Streamlit process."""
    from deepface import DeepFace
    return DeepFace


def analyze_captured_face(uploaded_photo):
    """
    Run pretrained facial-expression analysis on a captured photo.

    Returns:
        detected: dominant model label
        scores: emotion scores returned by DeepFace
    """
    image_bytes = uploaded_photo.getvalue()

    rgb_image = np.array(
        Image.open(BytesIO(image_bytes)).convert("RGB")
    )
    bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)

    deepface = get_deepface()

    results = deepface.analyze(
        img_path=bgr_image,
        actions=["emotion"],
        enforce_detection=True,
        detector_backend="opencv",
    )

    analysis = results[0] if isinstance(results, list) else results

    scores = analysis.get("emotion", {})
    detected = analysis.get("dominant_emotion", "neutral").lower()

    # Map DeepFace labels to the expression names used in this app.
    if detected == "surprise":
        detected = "surprised"

    scores = {
        str(name): float(value)
        for name, value in scores.items()
    }

    return detected, scores


# ---------------------------------------------------------
# PLAYLIST GENERATION
# ---------------------------------------------------------

def rank_songs(songs, target_mood, target_energy, genre):
    """Rank songs by mood match, energy proximity and genre preference."""
    ranked = []

    mood_equivalents = {
        "happy": {"happy"},
        "sad": {"sad"},
        "calm": {"calm"},
        "energized": {"energized", "happy"},
        "focused": {"focused", "calm"},
    }

    desired_moods = mood_equivalents.get(target_mood, {target_mood})

    for song in songs:
        mood_score = 1.0 if song.get("mood") in desired_moods else 0.35
        energy_score = 1.0 - abs(
            float(song.get("energy", 0.5)) - target_energy
        )
        genre_score = (
            1.0
            if genre == "All genres"
            or song.get("genre", "").lower() == genre.lower()
            else 0.35
        )

        total_score = (
            0.55 * mood_score
            + 0.30 * energy_score
            + 0.15 * genre_score
        )

        ranked.append((total_score, song))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [song for _, song in ranked]


def generate_playlist(target_mood, target_energy, genre, playlist_size):
    """
    Prefer live Spotify search results where available.
    Fall back to the built-in demo catalogue.
    """
    spotify_songs = spotify_search_songs(
        target_mood=target_mood,
        target_energy=target_energy,
        genre=genre,
        limit=playlist_size,
    )

    if spotify_songs:
        return rank_songs(
            spotify_songs,
            target_mood,
            target_energy,
            genre,
        )[:playlist_size], "Spotify search"

    catalogue = [
        dict(song, source="Demo catalogue")
        for song in DEMO_SONGS
        if genre == "All genres" or song["genre"].lower() == genre.lower()
    ]

    ranked = rank_songs(
        catalogue,
        target_mood,
        target_energy,
        genre,
    )

    return ranked[:playlist_size], "Demo catalogue"


# ---------------------------------------------------------
# SPOTIFY PLAYLIST SAVING
# ---------------------------------------------------------

def save_spotify_playlist(songs, playlist_name):
    """Create a Spotify playlist from available Spotify track IDs."""
    client = get_spotify_client()

    if client is None:
        raise RuntimeError(
            "Connect your Spotify account first. Spotify credentials "
            "and a completed authorization are required."
        )

    track_ids = [
        song.get("spotify_id")
        for song in songs
        if song.get("spotify_id")
    ]

    if not track_ids:
        raise RuntimeError(
            "These songs are demo search links rather than Spotify track "
            "results. Generate a playlist while Spotify search is available."
        )

    user = client.current_user()
    user_id = user["id"]

    playlist = client.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=False,
        description="A MoodLens playlist inspired by my selected mood.",
    )

    client.playlist_add_items(
        playlist_id=playlist["id"],
        items=track_ids,
    )

    return playlist.get("external_urls", {}).get(
        "spotify", "https://open.spotify.com/"
    )


# ---------------------------------------------------------
# SESSION STATE INITIALIZATION
# ---------------------------------------------------------

DEFAULT_STATE = {
    "detected_expression": None,
    "emotion_scores": {},
    "chosen_expression": "neutral",
    "last_playlist": [],
    "last_target": None,
    "last_mode": None,
    "last_auto_expression": None,
    "_last_detected_expression": None,
    "spotify_token_info": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------

with st.sidebar:
    st.markdown("## 🎧 MoodLens")
    st.caption("Music that meets you where you are.")

    st.divider()

    st.markdown("### Playlist preferences")

    mode = st.radio(
        "What do you want music to do?",
        ["Match my mood", "Shift my mood"],
        index=0,
        help=(
            "Match my mood finds music aligned with your selected expression. "
            "Shift my mood aims for a different musical direction."
        ),
    )

    genre = st.selectbox(
        "Preferred genre",
        [
            "All genres",
            "Pop",
            "Rock",
            "Indie",
            "Classical",
            "Ambient",
            "Alternative",
            "Hip-Hop",
            "Soundtrack",
        ],
    )

    playlist_size = st.slider(
        "Number of songs",
        min_value=5,
        max_value=20,
        value=10,
        step=5,
    )

    st.divider()

    st.markdown("### Spotify")
    client_id, client_secret, redirect_uri = get_spotify_credentials()

    if not SPOTIFY_AVAILABLE:
        st.warning(
            "Spotipy is not installed. The demo catalogue will still work."
        )
    elif not client_id or not client_secret:
        st.info(
            "Add your Spotify API credentials to enable Spotify search "
            "and playlist saving."
        )
    else:
        auth_manager = get_spotify_auth_manager()

        if auth_manager is not None:
            spotify_client = get_spotify_client()

            if spotify_client is not None:
                st.success("Spotify account connected.")
            else:
                try:
                    authorization_url = auth_manager.get_authorize_url()
                    st.link_button(
                        "Connect Spotify",
                        authorization_url,
                        use_container_width=True,
                    )
                    st.caption(
                        "After authorizing, return to this app. "
                        "The redirect URI must match your Spotify dashboard."
                    )
                except Exception as exc:
                    st.error(f"Could not start Spotify authorization: {exc}")

    st.divider()
    st.caption("MoodLens uses expression predictions as optional cues.")


# ---------------------------------------------------------
# HANDLE SPOTIFY OAUTH CALLBACK
# ---------------------------------------------------------

if SPOTIFY_AVAILABLE:
    try:
        authorization_code = st.query_params.get("code")

        if authorization_code and not st.session_state.get(
            "spotify_token_info"
        ):
            auth_manager = get_spotify_auth_manager()

            if auth_manager is not None:
                token_info = auth_manager.get_access_token(
                    authorization_code,
                    check_cache=False,
                )
                st.session_state["spotify_token_info"] = token_info
                st.query_params.clear()
                st.rerun()

    except Exception as exc:
        st.warning(
            "Spotify authorization could not be completed. "
            "Check the redirect URI and try connecting again."
        )
        st.caption(f"Technical details: {exc}")


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">Your expression. Your soundtrack.</div>
        <div class="hero-title">Meet your mood.<br><span>Find your music.</span></div>
        <div class="hero-subtitle">
            MoodLens uses a pretrained facial-expression model to suggest
            a musical direction. You stay in control of the mood and the
            music you choose.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ---------------------------------------------------------
# MAIN INTERFACE
# ---------------------------------------------------------

left, right = st.columns([1.05, 0.95], gap="large")


with left:
    st.markdown(
        '<div class="section-label">01 / Read your expression</div>',
        unsafe_allow_html=True,
    )
    st.subheader("A moment for your mood")

    st.write(
        "Take a photo to get a facial-expression prediction, "
        "or skip the camera and choose an expression yourself."
    )

    camera_photo = st.camera_input(
        "Take a picture",
        key="moodlens_camera",
        resolution="720p",
    )

    analyze_clicked = st.button(
        "Analyze my expression",
        type="primary",
        use_container_width=True,
    )

    st.caption(
        "The captured photo is sent to the Streamlit server for analysis. "
        "This app does not explicitly save the photo to a file or database. "
        "Avoid capturing sensitive images."
    )

    if analyze_clicked:
        if camera_photo is None:
            st.warning("Take a picture first.")
        else:
            st.session_state.pop("detected_expression", None)
            st.session_state.pop("emotion_scores", None)
            st.session_state["last_auto_expression"] = None

            try:
                with st.spinner(
                    "Loading the model and analyzing your expression..."
                ):
                    detected, emotion_scores = analyze_captured_face(
                        camera_photo
                    )

                st.session_state["detected_expression"] = detected
                st.session_state["emotion_scores"] = emotion_scores
                st.session_state["_last_detected_expression"] = None

                st.success("Expression analysis complete.")

            except Exception as exc:
                st.error(
                    "Could not analyze this photo. Make sure your face "
                    "is clearly visible, then try again."
                )
                st.caption(f"Technical details: {exc}")


with right:
    st.markdown(
        '<div class="section-label">02 / Your playlist</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Choose your direction")

    detected = st.session_state.get("detected_expression")
    scores = st.session_state.get("emotion_scores", {})

    if detected:
        st.success(
            f"{MOOD_EMOJIS.get(detected, '🎧')} "
            f"Predicted expression: **{detected.title()}**"
        )
    else:
        st.info(
            "No expression analyzed yet. You can still choose an expression "
            "below and generate a playlist."
        )

    if scores:
        with st.expander("View model scores"):
            st.caption(
                "These are model scores, not reliable measurements of "
                "someone's actual feelings or mental state."
            )

            sorted_scores = sorted(
                scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            for label, value in sorted_scores:
                st.write(f"**{label.title()}** · {value:.1f}")
                st.progress(
                    max(0.0, min(1.0, value / 100.0))
                )

    # DeepFace uses "surprise", "fear" and "disgust" labels.
    # The current playlist interface supports six expression choices.
    expression_for_playlist = {
        "surprise": "surprised",
        "fear": "surprised",
        "disgust": "angry",
    }.get(detected, detected)

    mood_options = [
        "happy",
        "sad",
        "angry",
        "surprised",
        "neutral",
        "calm",
    ]

    if expression_for_playlist in mood_options:
        if (
            st.session_state.get("_last_detected_expression")
            != detected
        ):
            st.session_state["chosen_expression"] = expression_for_playlist
            st.session_state["_last_detected_expression"] = detected

    if st.session_state.get("chosen_expression") not in mood_options:
        st.session_state["chosen_expression"] = "neutral"

    chosen_expression = st.selectbox(
        "Expression cue (you can change this)",
        options=mood_options,
        key="chosen_expression",
        format_func=lambda mood: (
            f"{MOOD_EMOJIS.get(mood, '🎧')} {mood.title()}"
        ),
        help=(
            "Facial-expression models can be wrong. Select the expression "
            "or mood you want the playlist to use."
        ),
    )

    target_mood, target_energy = MOOD_TARGETS[mode][chosen_expression]

    st.markdown(
        f"""
        <div class="song-card">
            <div class="section-label">Playlist direction</div>
            <h3>{MOOD_EMOJIS.get(target_mood, '🎧')} {target_mood.title()}</h3>
            <div class="song-artist">
                {MOOD_DESCRIPTIONS.get(target_mood, '')}
            </div>
            <div class="song-meta">Target energy: {target_energy:.2f} / 1.00</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    generate = st.button(
        "✨ Generate my playlist",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------
# AUTOMATIC GENERATION AFTER A NEW EXPRESSION
# ---------------------------------------------------------

auto_generate = (
    detected is not None
    and st.session_state.get("last_auto_expression") != detected
)

if generate or auto_generate:
    expression_for_playlist = (
        {
            "surprise": "surprised",
            "fear": "surprised",
            "disgust": "angry",
        }.get(detected, detected)
        if auto_generate
        else chosen_expression
    )

    # Record the expression before generating to avoid repeated
    # automatic generation on every Streamlit rerun.
    if auto_generate:
        st.session_state["last_auto_expression"] = detected

    target_mood, target_energy = MOOD_TARGETS[mode][
        expression_for_playlist
    ]

    with st.spinner("Finding songs for your playlist..."):
        playlist, playlist_source = generate_playlist(
            target_mood=target_mood,
            target_energy=target_energy,
            genre=genre,
            playlist_size=playlist_size,
        )

    st.session_state["last_playlist"] = playlist
    st.session_state["last_target"] = target_mood
    st.session_state["last_mode"] = mode
    st.session_state["last_expression"] = expression_for_playlist
    st.session_state["last_playlist_source"] = playlist_source

    if not playlist:
        st.warning(
            "No songs were found for these preferences. "
            "Try selecting All genres."
        )


# ---------------------------------------------------------
# DISPLAY GENERATED PLAYLIST
# ---------------------------------------------------------

playlist = st.session_state.get("last_playlist", [])

if playlist:
    st.divider()

    st.markdown(
        '<div class="section-label">03 / Your soundtrack</div>',
        unsafe_allow_html=True,
    )

    playlist_target = st.session_state.get("last_target", "happy")
    playlist_mode = st.session_state.get("last_mode", mode)
    playlist_source = st.session_state.get(
        "last_playlist_source", "Demo catalogue"
    )

    st.header(
        f"{MOOD_EMOJIS.get(playlist_target, '🎧')} "
        f"Your {playlist_target.title()} Playlist"
    )

    st.caption(
        f"Mode: {playlist_mode} · "
        f"Songs: {len(playlist)} · "
        f"Source: {playlist_source}"
    )

    metric_columns = st.columns(3)

    with metric_columns[0]:
        st.metric("Tracks", len(playlist))

    with metric_columns[1]:
        st.metric("Target mood", playlist_target.title())

    with metric_columns[2]:
        st.metric(
            "Target energy",
            f"{MOOD_TARGETS[playlist_mode][st.session_state.get('last_expression', 'neutral')][1]:.2f}",
        )

    for index, song in enumerate(playlist, start=1):
        with st.container():
            image_column, details_column = st.columns(
                [0.18, 0.82],
                vertical_alignment="center",
            )

            with image_column:
                if song.get("image"):
                    st.image(song["image"], use_container_width=True)
                else:
                    st.markdown(
                        f"<div style='font-size:2.3rem; text-align:center;'>"
                        f"{MOOD_EMOJIS.get(song.get('mood'), '🎵')}</div>",
                        unsafe_allow_html=True,
                    )

            with details_column:
                st.markdown(
                    f"""
                    <div class="song-card">
                        <div class="song-title">
                            {index:02d}. {song.get('title', 'Unknown track')}
                        </div>
                        <div class="song-artist">
                            {song.get('artist', 'Unknown artist')}
                        </div>
                        <div class="song-meta">
                            {song.get('genre', 'Music')} ·
                            {song.get('mood', 'mixed').title()} ·
                            Energy {float(song.get('energy', 0.5)):.2f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if song.get("url"):
                    st.link_button(
                        "Listen on Spotify",
                        song["url"],
                        key=f"listen_{index}_{song.get('spotify_id', 'demo')}",
                    )

    st.divider()

    # -----------------------------------------------------
    # SAVE PLAYLIST TO SPOTIFY
    # -----------------------------------------------------

    st.subheader("Save this playlist to Spotify")

    spotify_client = get_spotify_client() if SPOTIFY_AVAILABLE else None

    if spotify_client is None:
        st.info(
            "To save a playlist, configure Spotify API credentials in "
            "Streamlit secrets and connect your Spotify account."
        )
    else:
        playlist_name = st.text_input(
            "Playlist name",
            value=f"MoodLens - {playlist_target.title()}",
            key="spotify_playlist_name",
        )

        if st.button(
            "Save playlist to my Spotify account",
            type="primary",
            key="save_spotify_playlist",
        ):
            if not playlist_name.strip():
                st.warning("Enter a playlist name first.")
            else:
                try:
                    with st.spinner("Saving your Spotify playlist..."):
                        playlist_url = save_spotify_playlist(
                            playlist,
                            playlist_name.strip(),
                        )

                    st.success("Playlist saved to Spotify!")
                    st.link_button(
                        "Open your Spotify playlist",
                        playlist_url,
                    )

                except Exception as exc:
                    st.error("Could not save this playlist.")
                    st.caption(f"Technical details: {exc}")

else:
    st.divider()
    st.markdown(
        """
        <div style="text-align:center; padding:2rem 0; color:#B8C3D9;">
            <div style="font-size:2.5rem;">🎶</div>
            <h3>Your soundtrack is waiting</h3>
            <p>Choose an expression and generate a playlist to get started.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    "MoodLens is a music-discovery prototype. Facial-expression "
    "recognition is imperfect and can be affected by lighting, pose "
    "and individual differences. A predicted facial expression does not "
    "establish how someone actually feels. You can always choose your "
    "own expression cue instead."
)
