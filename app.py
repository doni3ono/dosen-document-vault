import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

st.set_page_config(
    page_title="Dosen Document Vault",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Dosen Document Vault")
st.caption("Simpan, kelola, dan temukan dokumen dosen dengan cepat.")

# =========================
# Folder dan file metadata
# =========================
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

# =========================
# Menu sidebar
# =========================
menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Beranda",
        "📤 Upload Dokumen",
        "🔎 Cari Dokumen",
        "📚 Daftar Dokumen"
    ]
)

# =========================
# BERANDA
# =========================
if menu == "🏠 Beranda":

    df = pd.read_csv(metadata_file)

    st.subheader("Ringkasan Dokumen")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Dokumen", len(df))

    if len(df) > 0:
        col2.metric("Kategori", df["kategori"].nunique())
        col3.metric("Tahun", df["tahun"].nunique())
    else:
        col2.metric("Kategori", 0)
        col3.metric("Tahun", 0)

    st.info(
        "Gunakan menu Upload Dokumen untuk menambahkan arsip baru."
    )

# =========================
# UPLOAD DOKUMEN
# =========================
elif menu == "📤 Upload Dokumen":

    st.subheader("📤 Upload Dokumen Baru")

    judul = st.text_input("Judul Dokumen")

    kategori = st.selectbox(
        "Kategori",
        [
            "Pengajaran",
            "Penelitian",
            "Publikasi",
            "Kedinasan",
            "BKD & Kinerja",
            "Kerja Sama",
            "Seminar & PPL",
            "Arsip Pribadi",
            "Lainnya"
        ]
    )

    tahun = st.number_input(
        "Tahun",
        min_value=2000,
        max_value=2100,
        value=datetime.now().year
    )

    kata_kunci = st.text_input(
        "Kata Kunci",
        placeholder="contoh: MAPPI, penilaian, seminar"
    )

    uploaded_file = st.file_uploader(
        "Pilih File",
        type=[
            "pdf",
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            "csv",
            "txt",
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if st.button("💾 Simpan Dokumen"):

        if not judul:
            st.warning("Judul dokumen harus diisi.")

        elif uploaded_file is None:
            st.warning("Silakan pilih file terlebih dahulu.")

        else:

            doc_id = str(uuid.uuid4())[:8]
            nama_file_asli = uploaded_file.name
            nama_file_simpan = f"{doc_id}_{nama_file_asli}"

            path_file = os.path.join(
                "documents",
                nama_file_simpan
            )

            with open(path_file, "wb") as f:
                f.write(uploaded_file.getbuffer())

            df = pd.read_csv(metadata_file)

            data_baru = pd.DataFrame([{
                "id": doc_id,
                "judul": judul,
                "kategori": kategori,
                "tahun": int(tahun),
                "kata_kunci": kata_kunci,
                "nama_file": nama_file_simpan,
                "tanggal_upload": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }])

            df = pd.concat(
                [df, data_baru],
                ignore_index=True
            )

            df.to_csv(metadata_file, index=False)

            st.success("✅ Dokumen berhasil disimpan.")

# =========================
# CARI DOKUMEN
# =========================
elif menu == "🔎 Cari Dokumen":

    st.subheader("🔎 Cari Dokumen")

    df = pd.read_csv(metadata_file)

    if len(df) == 0:

        st.info("Belum ada dokumen yang disimpan.")

    else:

        pencarian = st.text_input(
            "Cari berdasarkan judul atau kata kunci",
            placeholder="contoh: MAPPI, BKD, penelitian rumah"
        )

        kategori_filter = st.selectbox(
            "Filter Kategori",
            ["Semua"] + sorted(df["kategori"].dropna().unique().tolist())
        )

        tahun_list = sorted(
            df["tahun"].dropna().astype(int).unique().tolist(),
            reverse=True
        )

        tahun_filter = st.selectbox(
            "Filter Tahun",
            ["Semua"] + tahun_list
        )

        hasil = df.copy()

        if pencarian:

            pencarian_lower = pencarian.lower()

            hasil = hasil[
                hasil["judul"].fillna("").str.lower().str.contains(
                    pencarian_lower,
                    regex=False
                )
                |
                hasil["kata_kunci"].fillna("").str.lower().str.contains(
                    pencarian_lower,
                    regex=False
                )
            ]

        if kategori_filter != "Semua":
            hasil = hasil[
                hasil["kategori"] == kategori_filter
            ]

        if tahun_filter != "Semua":
            hasil = hasil[
                hasil["tahun"].astype(int) == int(tahun_filter)
            ]

        st.write(f"**Ditemukan {len(hasil)} dokumen**")

        if len(hasil) == 0:

            st.warning("Dokumen tidak ditemukan.")

        else:

            for _, row in hasil.iterrows():

                with st.expander(
                    f"📄 {row['judul']} — {row['tahun']}"
                ):

                    st.write(
                        "**Kategori:**",
                        row["kategori"]
                    )

                    st.write(
                        "**Kata Kunci:**",
                        row["kata_kunci"]
                    )

                    st.write(
                        "**Tanggal Upload:**",
                        row["tanggal_upload"]
                    )

                    path_file = os.path.join(
                        "documents",
                        row["nama_file"]
                    )

                    if os.path.exists(path_file):

                        with open(path_file, "rb") as f:

                            st.download_button(
                                "⬇️ Download Dokumen",
                                data=f.read(),
                                file_name=row["nama_file"].split(
                                    "_",
                                    1
                                )[-1],
                                key=f"download_{row['id']}"
                            )

                    else:

                        st.error(
                            "File tidak ditemukan di penyimpanan."
                        )

# =========================
# DAFTAR DOKUMEN
# =========================
elif menu == "📚 Daftar Dokumen":

    st.subheader("📚 Daftar Dokumen")

    df = pd.read_csv(metadata_file)

    if len(df) == 0:

        st.info("Belum ada dokumen yang disimpan.")

    else:

        st.dataframe(
            df[
                [
                    "judul",
                    "kategori",
                    "tahun",
                    "kata_kunci",
                    "tanggal_upload"
                ]
            ],
            use_container_width=True
        )
