import streamlit as st
import re
import time
import json
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from pytube import YouTube

# Add caching to improve performance
@st.cache_data(ttl=3600)

# Set page configuration
st.set_page_config(
    page_title="Telugu Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4a148c;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #7b1fa2;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e1bee7;
        padding: 10px 20px;
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #7b1fa2;
        color: white;
    }
    .result-area {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #ddd;
        margin-top: 20px;
    }
    footer {
        text-align: center;
        margin-top: 40px;
        color: #666;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Function to translate text safely with caching
@st.cache_data(ttl=3600)
def safe_translate(text, src='auto', dest='te'):
    if not text.strip():
        return {'text': '', 'src': src, 'dest': dest}
        
    try:
        # Use a direct HTTP request approach to Google Translate API
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": src if src != 'auto' else 'auto',
            "tl": dest,
            "dt": "t",
            "q": text
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        # Add retry mechanism
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    translated_text = ''.join([sentence[0] for sentence in result[0] if sentence and len(sentence) > 0])
                    detected_lang = result[2] if src == 'auto' and len(result) > 2 else src
                    return {
                        'text': translated_text,
                        'src': detected_lang,
                        'dest': dest
                    }
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    retry_count += 1
                    time.sleep(2 * retry_count)  # Exponential backoff
                else:
                    st.error(f"Translation API error: {response.status_code}")
                    return {
                        'text': f"[Translation error: API returned status code {response.status_code}]",
                        'src': src,
                        'dest': dest
                    }
            except requests.exceptions.Timeout:
                retry_count += 1
                time.sleep(2 * retry_count)  # Exponential backoff
            except Exception as e:
                st.error(f"Request error: {str(e)}")
                break
                
        # Fallback message if all retries failed
        if retry_count >= max_retries:
            return {
                'text': "[Translation temporarily unavailable. Please try again later.]",
                'src': src,
                'dest': dest
            }
                
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return {
            'text': f"[Translation error: {str(e)}]",
            'src': src,
            'dest': dest
        }

# Header
st.markdown('<h1 class="main-header">Telugu Translator</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem;">Translate any text or YouTube video to Telugu</p>', unsafe_allow_html=True)

# Create tabs
tab1, tab2 = st.tabs(["Text Translation", "YouTube Translation"])

# Text Translation Tab
with tab1:
    st.markdown('<h2 class="sub-header">Text Translation</h2>', unsafe_allow_html=True)
    
    # Source language selection
    source_language = st.selectbox(
        "Source Language:",
        ["auto", "en", "ta", "hi", "ml", "kn"],
        format_func=lambda x: {
            "auto": "Auto Detect", 
            "en": "English", 
            "ta": "Tamil", 
            "hi": "Hindi", 
            "ml": "Malayalam", 
            "kn": "Kannada"
        }.get(x, x)
    )
    
    # Text input
    source_text = st.text_area("Enter Text:", height=200, placeholder="Enter text to translate to Telugu...")
    
    # Translation button
    if st.button("Translate to Telugu", key="translate_text_btn"):
        if not source_text.strip():
            st.error("Please enter text to translate.")
        else:
            with st.spinner("Translating..."):
                try:
                    # For large texts, split into chunks to avoid translation limits
                    chunk_size = 1000
                    chunks = [source_text[i:i+chunk_size] for i in range(0, len(source_text), chunk_size)]
                    
                    translated_chunks = []
                    detected_language = None
                    
                    for chunk in chunks:
                        # Add delay between chunks to avoid rate limiting
                        if len(translated_chunks) > 0:
                            time.sleep(1)
                        
                        result = safe_translate(
                            chunk, 
                            src=source_language if source_language != "auto" else 'auto', 
                            dest='te'
                        )
                        
                        # Get detected language from first chunk
                        if detected_language is None and source_language == "auto":
                            detected_language = result['src']
                            
                        translated_chunks.append(result['text'])
                    
                    translated_text = ''.join(translated_chunks)
                    
                    # Display results
                    st.markdown('<div class="result-area">', unsafe_allow_html=True)
                    st.subheader(f"Original Text ({detected_language if source_language == 'auto' else source_language})")
                    st.write(source_text)
                    
                    st.subheader("Telugu Translation")
                    st.write(translated_text)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Translation error: {str(e)}")

# YouTube Translation Tab
with tab2:
    st.markdown('<h2 class="sub-header">YouTube Video Translation</h2>', unsafe_allow_html=True)
    
    # YouTube URL input
    youtube_url = st.text_input("YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")
    
    # Video language selection
    video_language = st.selectbox(
        "Video Language:",
        ["auto", "en", "ta", "hi", "ml", "kn"],
        format_func=lambda x: {
            "auto": "Auto Detect", 
            "en": "English", 
            "ta": "Tamil", 
            "hi": "Hindi", 
            "ml": "Malayalam", 
            "kn": "Kannada"
        }.get(x, x)
    )
    
    # Extract YouTube video ID
    def extract_youtube_id(url):
        pattern = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    # Translation button
    if st.button("Translate to Telugu", key="translate_video_btn"):
        if not youtube_url.strip():
            st.error("Please enter a YouTube URL.")
        else:
            # Validate YouTube URL
            video_id = extract_youtube_id(youtube_url)
            if not video_id:
                st.error("Please enter a valid YouTube URL.")
            else:
                with st.spinner("Fetching video transcript and translating..."):
                    try:
                        # Display video
                        st.video(f"https://www.youtube.com/watch?v={video_id}")
                        
                        # Get video transcript
                        try:
                            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                            
                            # Try to get transcript in specified language or auto-generated
                            if video_language != "auto":
                                try:
                                    transcript = transcript_list.find_transcript([video_language])
                                except:
                                    # Fallback to auto-generated
                                    transcript = transcript_list.find_generated_transcript(['en'])
                            else:
                                # Try to get any available transcript
                                try:
                                    transcript = transcript_list.find_transcript(['en'])
                                except:
                                    transcript = list(transcript_list)[0]
                            
                            transcript_data = transcript.fetch()
                            
                            # Extract text from transcript
                            original_transcript = ' '.join([item['text'] for item in transcript_data])
                            detected_language = transcript.language_code
                            
                        except (TranscriptsDisabled, NoTranscriptFound):
                            # If no transcript available, try to get video title and description
                            try:
                                yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
                                original_transcript = f"Title: {yt.title}\n\nDescription: {yt.description}"
                                detected_language = 'auto'
                            except Exception as e:
                                st.error(f"Failed to get video information: {str(e)}")
                                st.stop()
                        
                        # Translate transcript to Telugu
                        chunk_size = 1000
                        chunks = [original_transcript[i:i+chunk_size] for i in range(0, len(original_transcript), chunk_size)]
                        
                        translated_chunks = []
                        
                        for chunk in chunks:
                            # Add delay between chunks to avoid rate limiting
                            if len(translated_chunks) > 0:
                                time.sleep(1)
                                
                            result = safe_translate(chunk, dest='te')
                            translated_chunks.append(result['text'])
                        
                        translated_text = ''.join(translated_chunks)
                        
                        # Display results
                        st.markdown('<div class="result-area">', unsafe_allow_html=True)
                        st.subheader(f"Original Transcript ({detected_language})")
                        st.write(original_transcript)
                        
                        st.subheader("Telugu Translation")
                        st.write(translated_text)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Translation error: {str(e)}")

# Footer
st.markdown('<footer>© 2025 Telugu Translator | Translate any text or YouTube video to Telugu</footer>', unsafe_allow_html=True)
