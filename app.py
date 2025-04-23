import streamlit as st
import os
import subprocess
import time
import datetime
from io import BytesIO
import tempfile
import platform

# App Configuration
st.set_page_config(
    page_title="PDF Compressor Pro",
    page_icon="📄",
    layout="centered"
)

def get_ghostscript_path():
    """Find Ghostscript executable path across different systems"""
    try:
        # Try default 'gs' first
        subprocess.run(["gs", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "gs"
    except:
        # Common Ghostscript paths
        paths = {
            'Windows': [
                r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
                r"C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe"
            ],
            'Linux': ["/usr/bin/gs"],
            'Darwin': ["/usr/local/bin/gs"]
        }
        
        for path_pattern in paths.get(platform.system(), []):
            if platform.system() == 'Windows':
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    return matches[0]
            else:
                if os.path.exists(path_pattern):
                    return path_pattern
        
        return None

# Time-based restriction
def is_restricted_time():
    now = datetime.datetime.now()
    return now.time() == datetime.time(0, 21)  # 12:21 AM

# Compression Functions
def compress_pdf_gs(input_pdf, output_pdf, quality='screen'):
    """Compress PDF using Ghostscript"""
    qualities = ['screen', 'ebook', 'printer', 'prepress']
    if quality not in qualities:
        raise ValueError(f"Invalid quality. Choose from: {qualities}")

    gs_path = get_ghostscript_path()
    if not gs_path:
        raise RuntimeError("Ghostscript not found. Please install it first.")

    command = [
        gs_path,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        f"-sOutputFile={output_pdf}",
        input_pdf
    ]

    try:
        result = subprocess.run(command, check=True, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode().strip()
        raise RuntimeError(f"Ghostscript failed: {error_msg}")

# Streamlit UI
st.title("📄 PDF Compression Tool")

# Ghostscript check
gs_path = get_ghostscript_path()
if not gs_path:
    st.error("""
    ## Ghostscript not found!
    
    Please install Ghostscript:
    
    **Windows:**
    1. Download from [ghostscript.com](https://www.ghostscript.com)
    2. Run the installer
    3. Add to PATH or restart your computer
    
    **Mac/Linux:**
    ```bash
    # Mac
    brew install ghostscript
    
    # Linux
    sudo apt-get install ghostscript
    ```
    """)
    st.stop()

if is_restricted_time():
    st.error("⚠️ Uploads restricted at 12:21 AM. Try again later.")
    st.stop()

uploaded_file = st.file_uploader("Upload PDF file", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        compression_type = st.radio(
            "Compression Level",
            ('Medium (recommended)', 'High', 'Maximum'),
            index=0
        )
    
    quality_map = {
        'Medium (recommended)': 'ebook',
        'High': 'printer',
        'Maximum': 'screen'
    }
    
    with col2:
        if st.button("🚀 Compress PDF", type="primary"):
            with st.spinner("Compressing..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    input_path = tmp_input.name

                output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

                try:
                    # Compression
                    start_time = time.time()
                    quality = quality_map[compression_type]
                    compress_pdf_gs(input_path, output_path, quality)

                    # Results
                    original_size = os.path.getsize(input_path)
                    new_size = os.path.getsize(output_path)
                    ratio = (1 - (new_size / original_size)) * 100
                    
                    # Display
                    st.success(f"✅ Reduced from {original_size/1024:.1f}KB to {new_size/1024:.1f}KB ({ratio:.1f}%)")
                    
                    # Download
                    with open(output_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Compressed PDF",
                            f.read(),
                            file_name=f"compressed_{uploaded_file.name}",
                            mime="application/pdf"
                        )

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    # Cleanup
                    for path in [input_path, output_path]:
                        if os.path.exists(path):
                            os.remove(path)

# Debug info (hidden by default)
with st.expander("Debug Info", expanded=False):
    st.write(f"OS: {platform.system()}")
    st.write(f"Ghostscript path: {gs_path}")
    st.write(f"Python PATH: {os.environ.get('PATH', '').split(os.pathsep)}")