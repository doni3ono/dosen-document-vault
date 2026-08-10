import streamlit as st
from supabase import create_client

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import os


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Dosen Document Vault",
    page_icon="📚",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SECRET_KEY = st.secrets["SUPABASE_SECRET_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = st.secrets["GOOGLE_REDIRECT_URI"]

GOOGLE_DRIVE_FOLDER_ID = st.secrets["GOOGLE_DRIVE_FOLDER_ID"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


# =========================================================
# GOOGLE OAUTH
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]


def create_google_flow():

    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                GOOGLE_REDIRECT_URI
            ]
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    return flow


# =========================================================
# SESSION
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "google_credentials" not in st.session_state:
    st.session_state.google_credentials = None


# =========================================================
# APP LOGIN
# =========================================================

if not st.session_state.logged_in:

    st.title("📚 Dosen Document Vault")

    st.caption(
        "Secure Academic Document Management System"
    )

    st.subheader("🔐 Login")

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "Masuk",
        type="primary"
    ):

        if password == APP_PASSWORD:

            st.session_state.logged_in = True
            st.rerun()

        else:

            st.error(
                "Password salah."
            )

    st.stop()


# =========================================================
# GOOGLE CALLBACK
# =========================================================

if "code" in st.query_params:

    try:
        code = st.query_params.get("code")

        flow = create_google_flow()

        # Penting: gunakan authorization_response lengkap
        authorization_response = (
            GOOGLE_REDIRECT_URI
            + "?code="
            + code
        )

        flow.fetch_token(
            authorization_response=authorization_response
        )

        credentials = flow.credentials

        st.session_state.google_credentials = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }

        # Bersihkan parameter OAuth setelah credential tersimpan
        st.query_params.clear()

        st.rerun()

    except Exception as e:

        st.error(
            f"Google OAuth callback gagal: {e}"
        )

        st.stop()


# =========================================================
# HEADER
# =========================================================

st.title("📚 Dosen Document Vault")

st.caption(
    "Google Drive + Supabase Document Management"
)

st.markdown("---")


# =========================================================
# SIDEBAR
# =========================================================

menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Dashboard",
        "☁️ Google Drive",
        "📚 Data Supabase"
    ]
)

if st.sidebar.button("🚪 Logout"):

    st.session_state.logged_in = False
    st.session_state.google_credentials = None

    st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    st.subheader("Dashboard")

    try:

        response = (
            supabase
            .table("documents")
            .select("*")
            .execute()
        )

        total = len(response.data)

    except Exception:

        total = 0

    col1, col2 = st.columns(2)

    col1.metric(
        "📄 Dokumen",
        total
    )

    if st.session_state.google_credentials:

        col2.metric(
            "☁️ Google Drive",
            "Terhubung"
        )

    else:

        col2.metric(
            "☁️ Google Drive",
            "Belum terhubung"
        )


# =========================================================
# GOOGLE DRIVE
# =========================================================

elif menu == "☁️ Google Drive":

    st.subheader(
        "☁️ Koneksi Google Drive"
    )

    if not st.session_state.google_credentials:

        st.warning(
            "Google Drive belum terhubung."
        )

        flow = create_google_flow()

        authorization_url, state = flow.authorization_url(
    access_type="offline",
    include_granted_scopes="true",
    prompt="consent"
)
        )

        st.link_button(
            "🔗 Hubungkan Google Drive",
            authorization_url,
            type="primary"
        )

    else:

        st.success(
            "✅ Google Drive sudah terhubung."
        )

        credentials = Credentials(
            **st.session_state.google_credentials
        )

        try:

            drive_service = build(
                "drive",
                "v3",
                credentials=credentials
            )

            about = (
                drive_service
                .about()
                .get(
                    fields="user"
                )
                .execute()
            )

            user = about.get(
                "user",
                {}
            )

            st.write(
                "Google Drive account:"
            )

            st.write(
                f"**{user.get('emailAddress', '')}**"
            )

            st.markdown("---")

            st.subheader(
                "📁 Folder Dosen Document Vault"
            )

            try:

                folder = (
                    drive_service
                    .files()
                    .get(
                        fileId=GOOGLE_DRIVE_FOLDER_ID,
                        fields="id,name,mimeType"
                    )
                    .execute()
                )

                st.success(
                    f"Folder ditemukan: "
                    f"**{folder['name']}**"
                )

                st.write(
                    "✅ Aplikasi memiliki akses "
                    "ke folder Google Drive."
                )

            except Exception as e:

                st.warning(
                    "Google Drive sudah terhubung, "
                    "tetapi folder yang dibuat manual "
                    "belum dapat diakses."
                )

                st.caption(
                    "Ini bisa terjadi karena kita "
                    "menggunakan scope drive.file."
                )

                st.code(str(e))

        except Exception as e:

            st.error(
                f"Koneksi Google Drive gagal: {e}"
            )


# =========================================================
# SUPABASE
# =========================================================

elif menu == "📚 Data Supabase":

    st.subheader(
        "📚 Metadata Supabase"
    )

    try:

        response = (
            supabase
            .table("documents")
            .select("*")
            .execute()
        )

        data = response.data

        if data:

            st.dataframe(
                data,
                use_container_width=True
            )

        else:

            st.info(
                "Belum ada metadata dokumen."
            )

    except Exception as e:

        st.error(
            f"Gagal mengambil data: {e}"
        )
