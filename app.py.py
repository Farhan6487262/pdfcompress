import streamlit as st
import os
import subprocess
import time
import datetime
from io import BytesIO
import tempfile

# App Configuration
st.set_page_config(page_title="PDF Compressor", page_icon="📄")

# Time-based restriction
def is_restricted_time():
    now = datetime.datetime.now()
    restricted_time = datetime.time(0, 21)  # 12:21 AM
    return now.time() == restricted_time

# Compression Functions
def compress_pdf_gs(input_pdf, output_pdf, quality='screen'):
    """Compress PDF using Ghostscript"""
    qualities = ['screen', 'ebook', 'printer', 'prepress']
    if quality not in qualities:
        raise ValueError(f"Invalid quality. Choose from: {qualities}")

    command = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_pdf}",
        input_pdf
    ]

    try:
        subprocess.run(command, check=True, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ghostscript failed: {e.stderr.decode()}")

# Streamlit UI
st.title("📄 PDF Compression Tool")

if is_restricted_time():
    st.error("⚠️ Uploads are temporarily restricted at this time (12:21 AM). Please try again later.")
    st.stop()

uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file:
    col1, col2 = st.columns(2)
    with col1:
        compression_type = st.radio(
            "Compression Level",
            ('Less (recommended)', 'Extreme'),
            index=0
        )
    with col2:
        st.write("")
        st.write("")
        compress_btn = st.button("Compress PDF")

    if compress_btn:
        with st.spinner("Compressing PDF..."):
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
                tmp_input.write(uploaded_file.getvalue())
                input_path = tmp_input.name

            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

            try:
                # Get original size
                original_size = os.path.getsize(input_path) / (1024 * 1024)  # in MB

                # Start compression
                start_time = time.time()
                quality = "ebook" if "Less" in compression_type else "screen"
                compress_pdf_gs(input_path, output_path, quality)

                # Get compressed size
                new_size = os.path.getsize(output_path) / (1024 * 1024)
                ratio = (1 - (new_size / original_size)) * 100
                time_taken = time.time() - start_time

                # Display results
                st.success("Compression successful!")
                st.metric("Original Size", f"{original_size:.2f} MB")
                st.metric("Compressed Size", f"{new_size:.2f} MB", 
                         delta=f"{ratio:.1f}% reduction")
                st.caption(f"Processing time: {time_taken:.1f} seconds")

                # Download button
                with open(output_path, "rb") as f:
                    st.download_button(
                        "Download Compressed PDF",
                        f.read(),
                        file_name=f"compressed_{uploaded_file.name}",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Error during compression: {str(e)}")
            finally:
                # Clean up temporary files
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)