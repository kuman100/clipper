import streamlit as st
import os
import time
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Clipper Pro", page_icon="🎬", layout="wide")

# --- FUNGSI UTAMA ---
def get_video_info(url):
    # Opsi ringan hanya untuk ambil judul
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        return None

def process_video(url, start_str, end_str, resolution, format_type):
    # 1. Konversi Waktu
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
        return None, "⚠️ Waktu Selesai harus lebih besar!"

    filename = f"clip_{int(time.time())}.mp4"
    
    # 2. Konfigurasi yt-dlp (MODE AMAN)
    ydl_opts = {
        'outtmpl': filename,
        'download_ranges': download_range_func(None, [(start_sec, end_sec)]),
        'force_keyframes_at_cuts': False, # Cepat & Ringan
        'quiet': False, # Nyalakan log biar kelihatan kalau error
        'verbose': True, # Debugging mode
        'nocheckcertificate': True,
        # Header palsu biar YouTube tidak curiga
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
    }

    # 3. Logika Format (PENTING UNTUK MENGHINDARI ERROR FFMPEG)
    if format_type == "Video (MP4)":
        if resolution == "1080":
            # 1080p sering bikin crash di cloud gratisan, hati-hati
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            # Pilih format yang SUDAH jadi satu (tidak perlu merge ffmpeg berat)
            # Ini trik agar tidak kena error "exited with code 1"
            ydl_opts['format'] = f'best[ext=mp4][height<={resolution}]'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
        filename = f"clip_{int(time.time())}.mp3"

    # Hapus lokasi ffmpeg manual (biarkan sistem Linux mendeteksi sendiri)
    # Kita hapus blok if os.name == 'nt' agar bersih di Cloud.

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename, "Success"
    except Exception as e:
        return None, str(e)

# --- UI HEADER ---
st.title("✂️ YouTube Clipper (Safe Mode)")
st.caption("Tips: Jika error, coba turunkan resolusi ke 360p atau 480p.")

# --- INPUT ---
url = st.text_input("Link YouTube:", placeholder="https://...")
col1, col2 = st.columns(2)
start_time = col1.text_input("Mulai", "00:00")
end_time = col2.text_input("Selesai", "00:30")
fmt = st.selectbox("Format", ["Video (MP4)", "Audio Only (MP3)"])
res = st.selectbox("Resolusi (Pilih rendah jika error)", ["360", "480", "720", "1080"], index=2, disabled="Audio" in fmt)

if st.button("🚀 Potong Video", type="primary"):
    if not url:
        st.error("Link kosong!")
    else:
        with st.spinner("Sedang memproses..."):
            file_result, msg = process_video(url, start_time, end_time, res, fmt)
            
            if file_result and os.path.exists(file_result):
                st.success("✅ Berhasil!")
                if "mp4" in file_result:
                    st.video(file_result)
                else:
                    st.audio(file_result)
                
                with open(file_result, "rb") as f:
                    st.download_button("⬇️ Download", f, file_name=file_result)
            else:
                st.error(f"Gagal: {msg}")
                st.warning("⚠️ Tips Perbaikan: Coba pilih resolusi '360' atau '480'. Resolusi tinggi sering gagal di server gratis.")