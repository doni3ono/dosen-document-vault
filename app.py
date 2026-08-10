import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid
import mimetypes

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Dosen Document Vault",
    page_icon="📚",
    layout="wide"
)

# =====================================================
# SUPABASE CONNECTION
# =====================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SECRET_KEY = st.secrets["SUPABASE_SECRET_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)

BUCKET_NAME = "documents"


# =====================================================
# LOGIN
# =====================================================

def login():

    st.title("📚 Dosen Document Vault")
    st.caption("Secure Academic Document Management")

    st.markdown("---")

    st.subheader("🔐 Login")

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Masukkan password"
    )

    if st.button(
        "Masuk",
        type="primary",
        use_container_width=True
    ):

        if password == APP_PASSWORD:

            st.session_state["login"] = True
            st.rerun()

        else:

            st.error("Password salah.")


if "login" not in st.session_state:
    st.session_state["login"] = False


if not st.session_state["login"]:
    login()
    st.stop()


# =====================================================
# SIDEBAR
# =====================================================

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

    st.session_state["login"] = False
    st.rerun()


# =====================================================
# HEADER
# =====================================================

st.title("📚 Dosen Document Vault")

st.caption(
    "Secure Academic Document Management System"
)

st.markdown("---")


# =====================================================
# FUNCTION GET DOCUMENTS
# =====================================================

def get_documents():

    try:

        response = (
            supabase
            .table("documents")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        return response.data

    except Exception as e:

        st.error(
            f"Gagal mengambil data: {e}"
        )

        return []


# =====================================================
# DASHBOARD
# =====================================================

if menu == "🏠 Dashboard":

    st.subheader("Dashboard")

    documents = get_documents()

    total_documents = len(documents)

    categories = set()

    years = set()

    for doc in documents:

        if doc.get("kategori"):
            categories.add(
                doc["kategori"]
            )

        if doc.get("tahun"):
            years.add(
                doc["tahun"]
            )

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

    st.info(
        "Dokumen sekarang disimpan secara permanen "
        "di Supabase Storage."
    )


# =====================================================
# UPLOAD DOCUMENT
# =====================================================

elif menu == "📤 Upload Dokumen":

    st.subheader("📤 Upload Dokumen")

    with st.form("upload_form"):

        judul = st.text_input(
            "Judul Dokumen *",
            placeholder="Contoh: Surat Tugas Seminar Penilaian"
        )

        kategori = st.selectbox(
            "Kategori *",
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
            placeholder=(
                "Contoh: MAPPI, seminar, "
                "penilaian properti"
            )
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

                # ---------------------------------
                # Create unique storage filename
                # ---------------------------------

                file_id = str(uuid.uuid4())

                safe_name = (
                    uploaded_file.name
                    .replace(" ", "_")
                )

                storage_path = (
                    f"{datetime.now().year}/"
                    f"{file_id}_{safe_name}"
                )

                file_bytes = (
                    uploaded_file.getvalue()
                )

                content_type = (
                    uploaded_file.type
                    or mimetypes.guess_type(
                        uploaded_file.name
                    )[0]
                    or "application/octet-stream"
                )

                # ---------------------------------
                # Upload to Supabase Storage
                # ---------------------------------

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

                # ---------------------------------
                # Save metadata
                # ---------------------------------

                metadata = {

                    "judul": judul,

                    "kategori": kategori,

                    "tahun": int(tahun),

                    "kata_kunci": kata_kunci,

                    "nama_file":
                        uploaded_file.name,

                    "storage_path":
                        storage_path
                }

                supabase.table(
                    "documents"
                ).insert(
                    metadata
                ).execute()

                st.success(
                    "✅ Dokumen berhasil "
                    "disimpan permanen."
                )

                st.balloons()

            except Exception as e:

                st.error(
                    f"Gagal menyimpan dokumen: {e}"
                )


# =====================================================
# SEARCH
# =====================================================

elif menu == "🔎 Cari Dokumen":

    st.subheader("🔎 Cari Dokumen")

    documents = get_documents()

    keyword = st.text_input(
        "Cari",
        placeholder=(
            "Contoh: MAPPI, BKD, "
            "machine learning..."
        )
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
            ).lower()

            if keyword_lower in searchable:

                results.append(doc)

        st.write(
            f"**Ditemukan "
            f"{len(results)} dokumen**"
        )

        for doc in results:

            with st.expander(
                f"📄 {doc['judul']}"
            ):

                st.write(
                    "**Kategori:**",
                    doc.get("kategori")
                )

                st.write(
                    "**Tahun:**",
                    doc.get("tahun")
                )

                st.write(
                    "**Kata Kunci:**",
                    doc.get("kata_kunci")
                )

                st.write(
                    "**File:**",
                    doc.get("nama_file")
                )

                try:

                    file_data = (
                        supabase.storage
                        .from_(BUCKET_NAME)
                        .download(
                            doc["storage_path"]
                        )
                    )

                    st.download_button(
                        "⬇️ Download",
                        data=file_data,
                        file_name=doc[
                            "nama_file"
                        ],
                        key=(
                            f"download_"
                            f"{doc['id']}"
                        )
                    )

                except Exception:

                    st.warning(
                        "File tidak dapat "
                        "di-download."
                    )

    else:

        st.info(
            "Masukkan kata kunci "
            "untuk mencari dokumen."
        )


# =====================================================
# ALL DOCUMENTS
# =====================================================

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
                f"📄 {doc['judul']} "
                f"({doc.get('tahun', '-')})"
            ):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        "**Kategori:**",
                        doc.get("kategori")
                    )

                    st.write(
                        "**Tahun:**",
                        doc.get("tahun")
                    )

                with col2:

                    st.write(
                        "**Kata Kunci:**",
                        doc.get("kata_kunci")
                    )

                    st.write(
                        "**Nama File:**",
                        doc.get("nama_file")
                    )

                try:

                    file_data = (
                        supabase.storage
                        .from_(BUCKET_NAME)
                        .download(
                            doc["storage_path"]
                        )
                    )

                    st.download_button(
                        "⬇️ Download Dokumen",
                        data=file_data,
                        file_name=doc[
                            "nama_file"
                        ],
                        key=(
                            f"all_download_"
                            f"{doc['id']}"
                        )
                    )

                except Exception:

                    st.warning(
                        "File tidak dapat "
                        "di-download."
                    )
