import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Dosen Document Vault",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Dosen Document Vault")
st.caption("Simpan, kelola, dan temukan dokumen dosen dengan cepat.")

os.makedirs("documents", exist_ok=True)
os.makedirs("data", exist_ok=True)

metadata_file = "data/documents.csv"

if not os.path.exists(metadata_file):
    df = pd.DataFrame(columns=[
        "id",
        "judul",
        "kategori",
        "tahun",
        "kata_kunci",
        "nama_file",
        "tanggal_upload"
    ])
    df.to_csv(metadata_file, index=False)

st.success("Dosen Document Vault siap digunakan.")
