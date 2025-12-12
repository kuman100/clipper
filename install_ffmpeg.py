import os
import zipfile
import urllib.request
import shutil

# URL Download FFmpeg Windows
URL = "https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip"
ZIP_NAME = "ffmpeg_temp.zip"

print("⬇️  Sedang mendownload FFmpeg (Sekitar 30MB)... Tunggu ya.")

try:
    # 1. Download
    urllib.request.urlretrieve(URL, ZIP_NAME)
    print("📦 Sedang mengekstrak...")

    # 2. Ekstrak
    with zipfile.ZipFile(ZIP_NAME, 'r') as zip_ref:
        # Cari file ffmpeg.exe di dalam subfolder zip
        ffmpeg_file = None
        for file in zip_ref.namelist():
            if file.endswith("bin/ffmpeg.exe"):
                ffmpeg_file = file
                break
        
        if ffmpeg_file:
            with open("ffmpeg.exe", "wb") as f_out:
                with zip_ref.open(ffmpeg_file) as f_in:
                    shutil.copyfileobj(f_in, f_out)
            print("✅ BERHASIL! File 'ffmpeg.exe' sudah ada.")
        else:
            print("❌ Gagal menemukan ffmpeg.exe di dalam zip.")

    # 3. Bersih-bersih
    os.remove(ZIP_NAME)

except Exception as e:
    print(f"❌ Error: {e}")
    print("Coba download manual di: https://www.gyan.dev/ffmpeg/builds/")

input("\nTekan Enter untuk keluar...")