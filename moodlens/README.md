# MoodLens

A privacy-conscious mood-aware music recommender built with Python and Streamlit.

## Features
- Browser-side facial landmark/blendshape processing with MediaPipe Tasks Vision.
- User-controlled “Match my mood” and “Shift my mood” playlist goals.
- Mood/energy/genre ranking using a built-in demo catalogue.
- Optional Spotify track search and playlist creation with OAuth.

## Important privacy note
Do **not** replace the custom camera component with `st.camera_input()`: that widget sends the captured image to the Streamlit server. This project runs camera processing in the browser and sends only numerical blendshape scores when the user presses **Use expression scores**. The component loads MediaPipe code and its model from external CDNs. No captured image/video is sent to those endpoints by this code. The app does not write camera images to disk.

Facial expressions do not reliably reveal someone's true feelings. MoodLens uses them only as optional cues, and the user can override the result.

## Setup

### 1. Create a virtual environment

Windows PowerShell:
```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run without Spotify
```bash
streamlit run app.py
```
The demo catalogue works without API credentials.

### 3. Configure Spotify
1. Create an app in the Spotify Developer Dashboard.
2. Add `http://localhost:8501` as a Redirect URI in the app settings.
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
4. Add your Client ID and Client Secret. Never commit the real secrets file.

Example:
```toml
SPOTIFY_CLIENT_ID = "..."
SPOTIFY_CLIENT_SECRET = "..."
SPOTIFY_REDIRECT_URI = "http://localhost:8501"
```

Restart Streamlit after editing secrets. Track search uses app credentials. Saving a playlist requires user authorization. The Spotify app must have access to the relevant Web API features, and Spotify may impose account/app-mode restrictions.

## How to use
1. Run the app and open the local URL.
2. Toggle **Enable camera**.
3. Press **Start camera** inside the camera panel and allow permission.
4. Wait for face detection, then press **Use expression scores**.
5. Select or override the expression cue.
6. Choose **Match my mood** or **Shift my mood** in the sidebar.
7. Press **Generate my playlist**.
8. Follow Spotify links, or connect Spotify to save a private playlist.

## Limitations
- The expression-to-mood mapping is a transparent heuristic, not a validated emotion classifier.
- The starter catalogue is illustrative; replace it with a licensed or otherwise permitted catalogue.
- Spotify API permissions and available endpoints may vary. Playback is handled by Spotify, not streamed by this app.
- Use HTTPS when hosting the app publicly. Camera access generally requires a secure context (localhost is allowed during development).
