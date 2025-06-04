from sqlite.db_creator import insert_csv_to_sqlite
import sqlite3
import pandas as pd
import streamlit as st
import os

# ==========================
# PENETAPAN VARIABEL
# ==========================
DB_PATH = "transjakarta.db"
TABLE_NAME = "transjakarta"
CSV_PATH = "C:/Users/tesar/Downloads/TransJakarta.csv"

# ==========================
# LOAD DATA
# ==========================
if not os.path.exists(DB_PATH):
    insert_csv_to_sqlite(CSV_PATH)

conn = sqlite3.connect(DB_PATH)
print(f"Successfully connected to the database {TABLE_NAME}")

df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
df = df.dropna(subset=['payUserID'])
df['payUserID'] = df['payUserID'].apply(lambda x: str(int(float(x)))).str.strip()
users_df = df[['payUserID', 'typeCard', 'userName', 'userSex', 'userBirthYear']].drop_duplicates()

# ==========================
# MENDEFINISIKAN JUDUL
# ==========================
def show_title():
    st.title("🚍 TransJakarta Travel Tracker")

# ==========================
# MENYIMPAN USER YANG LOGIN
# ==========================
if 'page' not in st.session_state:
    st.session_state.page = 'login'

if 'user_id' not in st.session_state:
    st.session_state.user_id = None

# ==========================
# HALAMAN LOGIN 
# ==========================
if st.session_state.page == 'login':
    show_title()
    st.header("🔐 Login Pengguna")
    user_input = st.text_input("Masukkan PayUserID")
    login = st.button("Login")
    register = st.button("Register")

    if login:
        if user_input in users_df['payUserID'].values:
            st.session_state.user_id = user_input
            st.session_state.page = 'main_menu'
        else:
            st.warning("PayUserID tidak ditemukan. Silakan registrasi.")

    if register:
        st.session_state.page = 'register'

# ==========================
# MENU LOGIN/REGISTER
# ==========================
elif st.session_state.page == 'register':
    show_title()
    st.header("📝 Registrasi Pengguna Baru")
    new_id = st.text_input("PayUserID")
    type_card = st.selectbox("Jenis Kartu", sorted(df['typeCard'].dropna().unique()))
    name = st.text_input("Nama")
    sex = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
    birth_year = st.number_input("Tahun Lahir", min_value=1900, max_value=2025, value=2000)

    daftar = st.button("Daftar")
    kembali = st.button("Kembali")

    if daftar:
        if not new_id.strip() or not name.strip():
            st.warning("Setiap kolom tidak boleh kosong.")
        elif not (new_id.isdigit() and len(new_id) == 12):
            st.warning("PayUserID harus terdiri dari 12 digit angka.")
        elif new_id in users_df['payUserID'].values:
            st.warning("PayUserID sudah terdaftar.")
        elif not type_card or not sex or not birth_year:
            st.warning("Semua kolom harus diisi.")
        else:
            conn.execute(f"""
                INSERT INTO {TABLE_NAME} (payUserID, typeCard, userName, userSex, userBirthYear)
                VALUES (?, ?, ?, ?, ?)
            """, (new_id, type_card, name.strip(), sex, int(birth_year)))
            conn.commit()

            users_df.loc[len(users_df)] = [new_id, type_card, name.strip(), sex, birth_year]
            st.success("Registrasi berhasil!")
            st.session_state.page = 'login'

    if kembali:
        st.session_state.page = 'login'

# ==========================
# MAIN MENU
# ==========================
elif st.session_state.page == 'main_menu':
    show_title()
    user = users_df[users_df['payUserID'] == st.session_state.user_id].iloc[0]
    st.title(f"👋 Selamat datang, {user['userName']}!")  # Judul besar

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Cek Riwayat"):
            st.session_state.page = 'history'
    with col2:
        if st.button("Cari Kode Koridor"):
            st.session_state.page = 'corridor'
    with col3:
        if st.button("Logout"):
            st.session_state.page = 'login'
            st.session_state.user_id = None

# ==========================
# RIWAYAT PERJALANAN
# ==========================
elif st.session_state.page == 'history':
    show_title()
    st.header("📜 Riwayat Perjalanan")
    user = users_df[users_df['payUserID'] == st.session_state.user_id].iloc[0]

    st.info(f"""
    **Nama:** {user['userName']}  
    **Tipe Kartu:** {user['typeCard']}  
    **Jenis Kelamin:** {user['userSex']}  
    **Tahun Lahir:** {user['userBirthYear']}
    """)

    user_data = pd.read_sql_query("""
        SELECT transID, routeName, transDate, tapInTime, tapOutTime, duration, direction
        FROM transjakarta WHERE payUserID = ?
    """, conn, params=(st.session_state.user_id,))

    if user_data.empty:
        st.info("Tidak ada riwayat perjalanan.")
    else:
        st.dataframe(user_data)

    if st.button("Kembali"):
        st.session_state.page = 'main_menu'

# ==========================
# CCARI KORIDOR
# ==========================
elif st.session_state.page == 'corridor':
    show_title()
    st.header("🛣️ Cari Kode Koridor")
    selected = st.selectbox("Pilih Rute", sorted(df['routeName'].dropna().unique()))

    if st.button("Cari"):
        matched = df[df['routeName'] == selected]
        if not matched.empty:
            st.success(f"✅ Kode Koridor: {matched.iloc[0]['corridorID']}")
        else:
            st.warning("Kode rute tidak ditemukan.")

    if st.button("Kembali"):
        st.session_state.page = 'main_menu'
