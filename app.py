import streamlit as st
import os
import subprocess
import time
import datetime
from io import BytesIO
import tempfile

# App Configuration
st.set_page_config(
    page_title="PDF Compressor Pro",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded"
)

def check_ghostscript_installed():
    """Check if Ghostscript is available on the system"""
    try:
        subprocess.run(["gs", "--version"], 
                      check=True,
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# Time-based restriction
def is_restricted_time():
    now = datetime.datetime.now()
    restricted_time = datetime.time(0, 21)  # 12:21 AM
    return now.time() == restricted_time

# Compression Functions
def compress_pdf_gs(input_pdf, output_pdf, quality='screen'):
    """Compress PDF using Ghostscript"""
    qualities = {
        'screen': 'Low quality, smallest size',
        'ebook': 'Medium quality',
        'printer': 'High quality',
        'prepress': 'Highest quality'
    }
    
    if quality not in qualities:
        raise ValueError(f"Invalid quality. Choose from: {list(qualities.keys())}")

    command = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dOptimize=true",
        f"-sOutputFile={output_pdf}",
        input_pdf
    ]

    try:
        result = subprocess.run(command, check=True, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode().strip()
        raise RuntimeError(f"Ghostscript compression failed: {error_msg}")

# Streamlit UI
st.title("📄 PDF Compression Tool")
st.caption("Reduce PDF file size while maintaining good quality")

# Check for Ghostscript first
if not check_ghostscript_installed():
    st.error("""
    ## Ghostscript not found!
    
    This app requires Ghostscript to be installed:
    
    **Linux/WSL:**  
    `sudo apt-get install ghostscript`  
    
    **Windows:**  
    Download from [ghostscript.com](https://www.ghostscript.com)
    
    **MacOS:**  
    `brew install ghostscript`
    """)
    st.stop()

if is_restricted_time():
    st.error("⚠️ Uploads are temporarily restricted at this time (12:21 AM). Please try again later.")
    st.stop()

with st.expander("ℹ️ How to use"):
    st.write("""
    1. Upload your PDF file
    2. Select compression level
    3. Click 'Compress PDF'
    4. Download your compressed file
    """)
    st.write("Higher compression = smaller files but lower quality")

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file:
    # Check file size limit (50MB)
    if uploaded_file.size > 50 * 1024 * 1024:
        st.error("File too large! Maximum size is 50MB")
        st.stop()
    
    col1, col2 = st.columns([1, 2])
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
        st.write("")
        st.write("")
        if st.button("🚀 Compress PDF", type="primary"):
            with st.spinner("Compressing PDF... Please wait"):
                # Create temporary files
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    input_path = tmp_input.name

                output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

                try:
                    # Get original size
                    original_size = os.path.getsize(input_path)
                    
                    # Start compression
                    start_time = time.time()
                    quality = quality_map[compression_type]
                    compress_pdf_gs(input_path, output_path, quality)

                    # Get compressed size
                    new_size = os.path.getsize(output_path)
                    ratio = (1 - (new_size / original_size)) * 100
                    time_taken = time.time() - start_time

                    # Display results
                    st.success("🎉 Compression successful!")
                    
                    cols = st.columns(3)
                    cols[0].metric("Original Size", f"{original_size/1024:.1f} KB")
                    cols[1].metric("Compressed Size", f"{new_size/1024:.1f} KB")
                    cols[2].metric("Reduction", f"{ratio:.1f}%")
                    
                    st.progress(min(int(ratio), 100))
                    st.caption(f"Processing time: {time_taken:.2f} seconds")

                    # Download button
                    with open(output_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Compressed PDF",
                            f.read(),
                            file_name=f"compressed_{uploaded_file.name}",
                            mime="application/pdf",
                            use_container_width=True
                        )

                except Exception as e:
                    st.error(f"❌ Error during compression: {str(e)}")
                finally:
                    # Clean up temporary files
                    if os.path.exists(input_path):
                        os.remove(input_path)
                    if os.path.exists(output_path):
                        os.remove(output_path)