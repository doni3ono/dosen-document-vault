import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import mimetypes

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Dosen Document Vault",
    page_icon="📚",
    layout="wide"
)

# =========================================================
# SECRETS
# =========================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SECRET_KEY = st.secrets["SUPABASE_SECRET_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

BUCKET_NAME = "documents"

# =========================================================
# SUPABASE CONNECTION
# =========================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)

# =========================================================
# SESSION
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =========================================================
# LOGIN
# =========================================================

if not st.session_state.logged_in:

    st.title("📚 Dosen Document Vault")
    st.caption("Secure Academic Document Management System")

    st.markdown("---")

    st.subheader("🔐 Login")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "Masuk",
        type="primary",
        use_container_width=True
    ):

        if password == APP_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()

        else:
            st.error("Password salah.")

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📚 Document Vault")

menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Dashboard",
        "📤 Upload Dokumen",
        "🔎 Cari Dokumen",
        "📚 Semua Dokumen"
    ]
)

st.sidebar.markdown("---")

if st.sidebar.button("🚪 Logout"):

    st.session_state.logged_in = False
    st.rerun()

# =========================================================
# HEADER
# =========================================================

st.title("📚 Dosen Document Vault")
st.caption("Academic Document Management with Supabase")

st.markdown("---")

# =========================================================
# FUNCTIONS
# =========================================================

def get_documents():

    try:

        response = (
            supabase
            .table("documents")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return response.data

    except Exception as e:

        st.error(
            f"Gagal mengambil data dokumen: {e}"
        )

        return []


def download_document(storage_path):

    try:

        return (
            supabase.storage
            .from_(BUCKET_NAME)
            .download(storage_path)
        )

    except Exception as e:

        st.error(
            f"Gagal mengambil file: {e}"
        )

        return None

# =========================================================
# DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    documents = get_documents()

    total_documents = len(documents)

    categories = {
        doc.get("kategori")
        for doc in documents
        if doc.get("kategori")
    }

    years = {
        doc.get("tahun")
        for doc in documents
        if doc.get("tahun")
    }

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "📄 Total Dokumen",
        total_documents
    )

    col2.metric(
        "📁 Kategori",
        len(categories)
    )

    col3.metric(
        "📅 Tahun",
        len(years)
    )

    st.markdown("---")

    if total_documents == 0:

        st.info(
            "Belum ada dokumen. "
            "Gunakan menu Upload Dokumen."
        )

    else:

        st.subheader("Dokumen Terbaru")

        for doc in documents[:5]:

            st.write(
                f"📄 **{doc.get('judul', '-')}** "
                f"— {doc.get('kategori', '-')} "
                f"({doc.get('tahun', '-')})"
            )

# =========================================================
# UPLOAD
# =========================================================

elif menu == "📤 Upload Dokumen":

    st.subheader("📤 Upload Dokumen Baru")

    with st.form("upload_form"):

        judul = st.text_input(
            "Judul Dokumen *",
            placeholder="Contoh: Surat Tugas Seminar Penilaian"
        )

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
            min_value=1990,
            max_value=2100,
            value=datetime.now().year
        )

        kata_kunci = st.text_input(
            "Kata Kunci",
            placeholder="Contoh: MAPPI, BKD, penelitian"
        )

        uploaded_file = st.file_uploader(
            "Pilih Dokumen *",
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

        submit = st.form_submit_button(
            "💾 Simpan Dokumen",
            type="primary",
            use_container_width=True
        )

    if submit:

        if not judul:

            st.warning(
                "Judul dokumen harus diisi."
            )

        elif uploaded_file is None:

            st.warning(
                "Silakan pilih dokumen."
            )

        else:

            try:

                file_id = str(uuid.uuid4())

                safe_name = (
                    uploaded_file.name
                    .replace(" ", "_")
                )

                storage_path = (
                    f"{datetime.now().year}/"
                    f"{file_id}_{safe_name}"
                )

                file_bytes = uploaded_file.getvalue()

                content_type = (
                    uploaded_file.type
                    or mimetypes.guess_type(
                        uploaded_file.name
                    )[0]
                    or "application/octet-stream"
                )

                # Upload file to Supabase Storage
                supabase.storage.from_(
                    BUCKET_NAME
                ).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={
                        "content-type": content_type,
                        "upsert": "false"
                    }
                )

                # Save metadata
                metadata = {
                    "judul": judul,
                    "kategori": kategori,
                    "tahun": int(tahun),
                    "kata_kunci": kata_kunci,
                    "nama_file": uploaded_file.name,
                    "storage_path": storage_path
                }

                supabase.table(
                    "documents"
                ).insert(
                    metadata
                ).execute()

                st.success(
                    "✅ Dokumen berhasil disimpan."
                )

                st.balloons()

            except Exception as e:

                st.error(
                    f"Gagal menyimpan dokumen: {e}"
                )

# =========================================================
# SEARCH
# =========================================================

elif menu == "🔎 Cari Dokumen":

    st.subheader("🔎 Cari Dokumen")

    documents = get_documents()

    keyword = st.text_input(
        "Cari dokumen",
        placeholder="Contoh: MAPPI, BKD, penelitian rumah"
    )

    kategori_filter = st.selectbox(
        "Kategori",
        [
            "Semua",
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

    if keyword:

        keyword_lower = keyword.lower()

        results = []

        for doc in documents:

            searchable = (
                str(doc.get("judul", ""))
                + " "
                + str(doc.get("kategori", ""))
                + " "
                + str(doc.get("kata_kunci", ""))
                + " "
                + str(doc.get("tahun", ""))
                + " "
                + str(doc.get("nama_file", ""))
            ).lower()

            if keyword_lower in searchable:

                results.append(doc)

    else:

        results = documents

    if kategori_filter != "Semua":

        results = [
            doc for doc in results
            if doc.get("kategori") == kategori_filter
        ]

    st.write(
        f"**Ditemukan {len(results)} dokumen**"
    )

    if not results:

        st.info(
            "Dokumen tidak ditemukan."
        )

    for doc in results:

        with st.expander(
            f"📄 {doc.get('judul', '-')}"
        ):

            st.write(
                "**Kategori:**",
                doc.get("kategori", "-")
            )

            st.write(
                "**Tahun:**",
                doc.get("tahun", "-")
            )

            st.write(
                "**Kata Kunci:**",
                doc.get("kata_kunci", "-")
            )

            st.write(
                "**Nama File:**",
                doc.get("nama_file", "-")
            )

            if st.button(
                "Siapkan Download",
                key=f"prepare_{doc['id']}"
            ):

                file_data = download_document(
                    doc["storage_path"]
                )

                if file_data:

                    st.download_button(
                        "⬇️ Download Dokumen",
                        data=file_data,
                        file_name=doc["nama_file"],
                        key=f"download_{doc['id']}"
                    )

# =========================================================
# ALL DOCUMENTS
# =========================================================

elif menu == "📚 Semua Dokumen":

    st.subheader("📚 Semua Dokumen")

    documents = get_documents()

    if not documents:

        st.info(
            "Belum ada dokumen."
        )

    else:

        st.write(
            f"Total: **{len(documents)} dokumen**"
        )

        for doc in documents:

            with st.expander(
                f"📄 {doc.get('judul', '-')} "
                f"({doc.get('tahun', '-')})"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        "**Kategori:**",
                        doc.get("kategori", "-")
                    )

                    st.write(
                        "**Tahun:**",
                        doc.get("tahun", "-")
                    )

                with col2:

                    st.write(
                        "**Kata Kunci:**",
                        doc.get("kata_kunci", "-")
                    )

                    st.write(
                        "**Nama File:**",
                        doc.get("nama_file", "-")
                    )

                if st.button(
                    "Siapkan Download",
                    key=f"all_prepare_{doc['id']}"
                ):

                    file_data = download_document(
                        doc["storage_path"]
                    )

                    if file_data:

                        st.download_button(
                            "⬇️ Download Dokumen",
                            data=file_data,
                            file_name=doc["nama_file"],
                            key=f"all_download_{doc['id']}"
                        )
