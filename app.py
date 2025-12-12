import streamlit as st
import os
import time
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Clipper Pro Local",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS CUSTOM (Biar Tampilan Ganteng) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    .success-box {
        padding: 20px;
        background-color: #d4edda;
        color: #155724;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
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
        'force_keyframes_at_cuts': False, # True = Lambat tapi presisi, False = Cepat
        'quiet': True,
        'ffmpeg_location': os.getcwd() # Pastikan baca ffmpeg.exe di folder yang sama
    }

    # Pengaturan Format Khusus
    if format_type == "Video (MP4)":
        # Download video sesuai resolusi
        ydl_opts['format'] = f'best[ext=mp4][height<={resolution}]/best[ext=mp4]'
    else:
        # Download Audio Saja
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Koreksi nama file untuk MP3 (kadang yt-dlp otomatis rename)
        if format_type == "Audio Only (MP3)" and not os.path.exists(filename):
            filename = filename.replace(".mp3", "") + ".mp3"
            
        return filename, "Success"
    except Exception as e:
        return None, str(e)

# --- UI HEADER ---
st.title("🎬 YouTube Clipper Pro (Local)")
st.markdown("Potong video YouTube dengan cepat, simpan di laptop, tanpa internet lemot.")
st.divider()

# --- SESSION STATE (Agar data tidak hilang saat klik tombol) ---
if 'video_info' not in st.session_state:
    st.session_state.video_info = None

# --- KOLOM INPUT URL ---
col_url, col_btn = st.columns([4, 1])
with col_url:
    url_input = st.text_input("Tempel Link YouTube di sini:", placeholder="https://youtube.com/watch?v=...")

with col_btn:
    st.write("") # Spacer
    st.write("") # Spacer
    if st.button("🔍 Cek Video"):
        if not url_input:
            st.toast("Masukkan link dulu!", icon="❌")
        else:
            with st.spinner("Sedang mengambil data video..."):
                info = get_video_info(url_input)
                if info:
                    st.session_state.video_info = info
                    st.toast("Video ditemukan!", icon="✅")
                else:
                    st.error("Video tidak ditemukan atau Link salah.")

st.divider()

# --- TAMPILAN DASHBOARD UTAMA ---
if st.session_state.video_info:
    info = st.session_state.video_info
    
    # Layout 2 Kolom: Kiri (Preview) - Kanan (Kontrol)
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        st.image(info['thumbnail'], use_container_width=True)
        st.subheader(info['title'])
        st.caption(f"Channel: {info['uploader']} | Durasi Asli: {format_seconds(info['duration'])}")
        
        # Fitur Preview Video Asli
        with st.expander("🎥 Putar Video Asli (Untuk cek menit)"):
            st.video(url_input)

    with col_right:
        st.markdown("### ✂️ Pengaturan Potongan")
        
        c1, c2 = st.columns(2)
        with c1:
            start_time = st.text_input("⏱️ Mulai (Menit:Detik)", "00:00", help="Contoh: 01:20 atau 80")
        with c2:
            end_time = st.text_input("⏱️ Selesai (Menit:Detik)", "00:30", help="Contoh: 02:00 atau 120")
            
        c3, c4 = st.columns(2)
        with c3:
            fmt = st.selectbox("📂 Format Output", ["Video (MP4)", "Audio Only (MP3)"])
        with c4:
            res = st.selectbox("📺 Kualitas Video", ["360", "480", "720", "1080"], index=2, disabled=(fmt=="Audio Only (MP3)"))

        st.write("")
        st.write("")
        
        # TOMBOL EKSEKUSI
        if st.button("🚀 PROSES KLIP SEKARANG", type="primary"):
            with st.status("Sedang memproses...", expanded=True) as status:
                st.write("🔄 Menghubungkan ke YouTube...")
                time.sleep(1)
                st.write("⬇️ Sedang mendownload & memotong...")
                
                file_result, msg = process_video(url_input, start_time, end_time, res, fmt)
                
                if file_result and os.path.exists(file_result):
                    status.update(label="Selesai!", state="complete", expanded=False)
                    
                    st.balloons()
                    st.success(f"✅ Berhasil! File tersimpan: `{file_result}`")
                    
                    # Tampilkan Hasil
                    if fmt == "Video (MP4)":
                        st.video(file_result)
                    else:
                        st.audio(file_result)
                        
                    # Tombol Download
                    with open(file_result, "rb") as f:
                        btn = st.download_button(
                            label="⬇️ Simpan ke Laptop",
                            data=f,
                            file_name=f"clip_hasil.{'mp4' if 'Video' in fmt else 'mp3'}",
                            mime=f"application/{'mp4' if 'Video' in fmt else 'mp3'}"
                        )
                else:
                    status.update(label="Gagal", state="error")
                    st.error(f"Terjadi Kesalahan: {msg}")

else:
    st.info("👆 Masukkan link di atas dan klik 'Cek Video' untuk memulai.")