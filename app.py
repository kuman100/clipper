import streamlit as st
import os
import time
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Clipper Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS CUSTOM ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI UTAMA ---

def format_seconds(seconds):
    """Mengubah detik ke format MM:SS"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def get_video_info(url):
    """Mengambil data video tanpa download"""
    ydl_opts = {'quiet': True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        return None

def process_video(url, start_str, end_str, resolution, format_type):
    # 1. Parsing Waktu
    def to_seconds(t_str):
        try:
            parts = list(map(int, t_str.split(':')))
            if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
            if len(parts) == 2: return parts[0]*60 + parts[1]
            if len(parts) == 1: return parts[0]
            return 0
        except: return 0

    start_sec = to_seconds(start_str)
    end_sec = to_seconds(end_str)
    
    if start_sec >= end_sec:
        return None, "⚠️ Waktu Selesai harus lebih besar dari Waktu Mulai!"

    # 2. Setup Filename
    ext = "mp4" if format_type == "Video (MP4)" else "mp3"
    filename = f"clip_{int(time.time())}.{ext}"
    
    # 3. Konfigurasi yt-dlp
    ydl_opts = {
        'outtmpl': filename,
        'download_ranges': download_range_func(None, [(start_sec, end_sec)]),
        'force_keyframes_at_cuts': False, 
        'quiet': True,
        'nocheckcertificate': True,
    }

    # --- LOGIKA CERDAS FFMPEG ---
    # Jika di Windows (Local) dan ada file ffmpeg.exe, pakai itu.
    # Jika di Cloud (Linux), biarkan kosong (dia akan cari di sistem /usr/bin/ffmpeg).
    if os.name == 'nt' and os.path.exists("ffmpeg.exe"):
        ydl_opts['ffmpeg_location'] = "ffmpeg.exe"

    # Pengaturan Format
    if format_type == "Video (MP4)":
        ydl_opts['format'] = f'best[ext=mp4][height<={resolution}]/best[ext=mp4]'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Koreksi nama file untuk MP3
        if format_type == "Audio Only (MP3)" and not os.path.exists(filename):
            filename = filename.replace(".mp3", "") + ".mp3"
            
        return filename, "Success"
    except Exception as e:
        return None, str(e)

# --- UI HEADER ---
st.title("🎬 YouTube Clipper Pro")
st.markdown("Potong video YouTube dengan cepat & mudah.")
st.divider()

if 'video_info' not in st.session_state:
    st.session_state.video_info = None

# --- KOLOM INPUT URL ---
col_url, col_btn = st.columns([4, 1])
with col_url:
    url_input = st.text_input("Tempel Link YouTube:", placeholder="https://youtube.com/...")

with col_btn:
    st.write("")
    st.write("")
    if st.button("🔍 Cek Video"):
        if not url_input:
            st.toast("Masukkan link dulu!", icon="❌")
        else:
            with st.spinner("Sedang mengambil data..."):
                info = get_video_info(url_input)
                if info:
                    st.session_state.video_info = info
                    st.toast("Video ditemukan!", icon="✅")
                else:
                    st.error("Gagal memuat video.")

st.divider()

# --- DASHBOARD UTAMA ---
if st.session_state.video_info:
    info = st.session_state.video_info
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Menghapus parameter use_container_width agar tidak warning
        st.image(info['thumbnail']) 
        st.subheader(info['title'])
        st.caption(f"Durasi: {format_seconds(info['duration'])}")
        
        with st.expander("🎥 Preview Video Asli"):
            st.video(url_input)

    with col_right:
        st.markdown("### ✂️ Pengaturan Potongan")
        
        c1, c2 = st.columns(2)
        with c1:
            start_time = st.text_input("⏱️ Mulai (MM:SS)", "00:00")
        with c2:
            end_time = st.text_input("⏱️ Selesai (MM:SS)", "00:30")
            
        c3, c4 = st.columns(2)
        with c3:
            fmt = st.selectbox("📂 Format", ["Video (MP4)", "Audio Only (MP3)"])
        with c4:
            res = st.selectbox("📺 Resolusi", ["360", "480", "720", "1080"], index=2, disabled=(fmt=="Audio Only (MP3)"))

        st.write("")
        
        if st.button("🚀 PROSES KLIP", type="primary"):
            with st.status("Sedang memproses...", expanded=True) as status:
                st.write("⬇️ Mendownload & Memotong...")
                
                file_result, msg = process_video(url_input, start_time, end_time, res, fmt)
                
                if file_result and os.path.exists(file_result):
                    status.update(label="Selesai!", state="complete", expanded=False)
                    st.balloons()
                    st.success("✅ Berhasil!")
                    
                    if fmt == "Video (MP4)":
                        st.video(file_result)
                    else:
                        st.audio(file_result)
                        
                    with open(file_result, "rb") as f:
                        st.download_button(
                            label="⬇️ Download File",
                            data=f,
                            file_name=f"clip_hasil.{'mp4' if 'Video' in fmt else 'mp3'}",
                            mime=f"application/{'mp4' if 'Video' in fmt else 'mp3'}"
                        )
                else:
                    status.update(label="Gagal", state="error")
                    st.error(f"Error: {msg}")

else:
    st.info("👆 Masukkan link di atas untuk memulai.")