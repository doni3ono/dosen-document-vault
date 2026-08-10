import streamlit as st
from supabase import create_client

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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

GOOGLE_CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = st.secrets["GOOGLE_REDIRECT_URI"]

GOOGLE_DRIVE_FOLDER_ID = st.secrets.get(
    "GOOGLE_DRIVE_FOLDER_ID",
    ""
)

# =========================================================
# SUPABASE
# =========================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)

# =========================================================
# GOOGLE OAUTH CONFIG
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

    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI
    )


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "google_credentials" not in st.session_state:
    st.session_state.google_credentials = None


# =========================================================
# GOOGLE OAUTH CALLBACK
# IMPORTANT: handle callback BEFORE app login screen
# =========================================================

if "code" in st.query_params:

    try:

        code = st.query_params.get("code")

        flow = create_google_flow()

        flow.fetch_token(
            code=code
        )

        credentials = flow.credentials

        st.session_state.google_credentials = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }

        # OAuth callback means user was already using the app
        st.session_state.logged_in = True

        st.query_params.clear()

        st.rerun()

    except Exception as e:

        st.error(
            f"Google OAuth gagal: {e}"
        )

        st.stop()


# =========================================================
# LOGIN
# =========================================================

if not st.session_state.logged_in:

    st.title("📚 Dosen Document Vault")

    st.caption(
        "Secure Academic Document Management System"
    )

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

            st.error(
                "Password salah."
            )

    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "📚 Document Vault"
)

menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Dashboard",
        "☁️ Google Drive",
        "📚 Supabase"
    ]
)

st.sidebar.markdown("---")

if st.sidebar.button(
    "🚪 Logout"
):

    st.session_state.logged_in = False
    st.session_state.google_credentials = None

    st.rerun()


# =========================================================
# HEADER
# =========================================================

st.title(
    "📚 Dosen Document Vault"
)

st.caption(
    "Google Drive + Supabase"
)

st.markdown("---")


# =========================================================
# DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    st.subheader(
        "Dashboard"
    )

    try:

        response = (
            supabase
            .table("documents")
            .select("*")
            .execute()
        )

        total_documents = len(
            response.data
        )

    except Exception as e:

        total_documents = 0

        st.warning(
            f"Supabase belum dapat dibaca: {e}"
        )

    col1, col2 = st.columns(2)

    col1.metric(
        "📄 Dokumen",
        total_documents
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

    if not st.session_state.google_credentials:

        st.info(
            "Buka menu Google Drive untuk "
            "menghubungkan akun Google."
        )


# =========================================================
# GOOGLE DRIVE
# =========================================================

elif menu == "☁️ Google Drive":

    st.subheader(
        "☁️ Google Drive"
    )

    if not st.session_state.google_credentials:

        st.warning(
            "Google Drive belum terhubung."
        )

        flow = create_google_flow()

        authorization_url, state = (
            flow.authorization_url(
                access_type="offline",
                prompt="consent"
            )
        )

        st.link_button(
            "🔗 Hubungkan Google Drive",
            authorization_url,
            type="primary",
            use_container_width=True
        )

    else:

        st.success(
            "✅ Google Drive berhasil terhubung."
        )

        try:

            credentials = Credentials(
                **st.session_state.google_credentials
            )

            drive_service = build(
                "drive",
                "v3",
                credentials=credentials,
                cache_discovery=False
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

            email = user.get(
                "emailAddress",
                ""
            )

            st.write(
                "### Akun Google"
            )

            st.success(
                email
            )

            st.markdown("---")

            if GOOGLE_DRIVE_FOLDER_ID:

                st.write(
                    "### 📁 Folder Document Vault"
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
                        f"{folder.get('name')}"
                    )

                except Exception as folder_error:

                    st.warning(
                        "Google Drive sudah terhubung, "
                        "tetapi folder yang dibuat manual "
                        "belum dapat diakses dengan izin "
                        "drive.file."
                    )

                    st.caption(
                        str(folder_error)
                    )

        except Exception as e:

            st.error(
                f"Gagal membaca Google Drive: {e}"
            )


# =========================================================
# SUPABASE
# =========================================================

elif menu == "📚 Supabase":

    st.subheader(
        "📚 Metadata Supabase"
    )

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

        data = response.data

        if data:

            st.dataframe(
                data,
                use_container_width=True
            )

        else:

            st.info(
                "Belum ada dokumen."
            )

    except Exception as e:

        st.error(
            f"Gagal mengambil data Supabase: {e}"
        )
