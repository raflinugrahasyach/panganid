import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==============================================================================
# KONFIGURASI HALAMAN STREAMLIT
# ==============================================================================
# Konfigurasi ini harus menjadi perintah pertama yang dijalankan
st.set_page_config(
    page_title="Dashboard Prediksi Harga Komoditas",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CSS KUSTOM UNTUK GAYA PROFESIONAL
# ==============================================================================
# Ini adalah kunci untuk mendapatkan tampilan & nuansa dashboard BI modern
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Buat file style.css di folder yang sama dengan dashboard.py
# Atau, kita bisa inject CSS langsung di sini
st.markdown("""
<style>
/* General styling */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Main content area */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: #0F1116; /* Darker sidebar */
    border-right: 1px solid #2D3748;
}

.css-1d391kg .css-1v3fvcr {
    color: #A0AEC0; /* Lighter text in sidebar */
}

/* Metric cards styling */
.metric-card {
    background-color: #1A202C;
    border: 1px solid #2D3748;
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
    text-align: center;
    color: white;
}
.metric-card h3 {
    font-size: 1.25rem;
    color: #A0AEC0; /* Lighter gray for title */
    margin-bottom: 0.5rem;
}
.metric-card p {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0rem;
}
.metric-card .delta {
    font-size: 1rem;
    font-weight: 500;
}

/* Plotly chart background */
.js-plotly-plot {
    background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# FUNGSI UNTUK MEMUAT DAN MEMPROSES DATA
# ==============================================================================
# Menggunakan cache agar data hanya dimuat sekali
@st.cache_data
def load_data():
    # Ganti path ini sesuai dengan lokasi file CSV Anda
    path_eda = 'semua_output.xlsx - 1. GRAFIK EDA.csv'
    path_peramalan = 'semua_output.xlsx - 2. GRAFIK HASIL PERAMALAN.csv'
    path_mape = 'semua_output.xlsx - 3. MAPE PER KOTA DAN KOMODITAS.csv'
    
    df_eda = pd.read_csv(path_eda)
    df_peramalan = pd.read_csv(path_peramalan)
    df_mape = pd.read_csv(path_mape)
    
    # --- Pre-processing Data ---
    # Konversi tanggal
    df_eda['ds'] = pd.to_datetime(df_eda['ds'])
    df_peramalan['ds'] = pd.to_datetime(df_peramalan['ds'])
    
    # Pisahkan unique_id di df_mape
    df_mape[['lokasi', 'komoditas']] = df_mape['unique_id'].str.split('/', n=1, expand=True)
    
    return df_eda, df_peramalan, df_mape

# Muat data
df_eda, df_peramalan, df_mape = load_data()


# ==============================================================================
# SIDEBAR UNTUK NAVIGASI DAN FILTER
# ==============================================================================
st.sidebar.title("Navigasi Dashboard")

page = st.sidebar.radio(
    "Pilih Halaman:",
    ("Ringkasan Eksekutif", "Analisis Peramalan", "Evaluasi Model (MAPE)")
)

st.sidebar.markdown("---")
st.sidebar.header("Filter Data")

# Filter Lokasi
lokasi_list = ['Semua Lokasi'] + sorted(df_peramalan['lokasi'].unique().tolist())
selected_lokasi = st.sidebar.selectbox("Pilih Lokasi:", lokasi_list)

# Filter Komoditas
komoditas_list = ['Semua Komoditas'] + sorted(df_peramalan['komoditas'].unique().tolist())
selected_komoditas = st.sidebar.selectbox("Pilih Komoditas:", komoditas_list)

# Filter data berdasarkan pilihan sidebar
if selected_lokasi != 'Semua Lokasi':
    df_peramalan_filtered = df_peramalan[df_peramalan['lokasi'] == selected_lokasi]
    df_mape_filtered = df_mape[df_mape['lokasi'] == selected_lokasi]
else:
    df_peramalan_filtered = df_peramalan
    df_mape_filtered = df_mape

if selected_komoditas != 'Semua Komoditas':
    df_peramalan_filtered = df_peramalan_filtered[df_peramalan_filtered['komoditas'] == selected_komoditas]
    df_mape_filtered = df_mape_filtered[df_mape_filtered['komoditas'] == selected_komoditas]


# ==============================================================================
# FUNGSI UNTUK MERENDER SETIAP HALAMAN
# ==============================================================================

def create_metric_card(title, value, delta=None, delta_color="normal"):
    st.markdown(f"""
    <div class="metric-card">
        <h3>{title}</h3>
        <p>{value}</p>
        {f'<p class="delta" style="color: {"#38A169" if delta_color == "inverse" else "#E53E3E"};">{delta}</p>' if delta else ""}
    </div>
    """, unsafe_allow_html=True)

def render_ringkasan_eksekutif():
    st.title("📈 Ringkasan Eksekutif Prediksi Harga")
    st.markdown("Gambaran umum performa model dan tren harga komoditas.")
    st.markdown("---")
    
    # --- KPI Cards ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_mape = df_mape_filtered['MAPE (%)'].mean() if not df_mape_filtered.empty else 0
        create_metric_card("MAPE Rata-rata", f"{avg_mape:.2f}%")
        
    with col2:
        last_actual_date = df_peramalan_filtered[df_peramalan_filtered['tipe'] == 'Aktual']['ds'].max()
        last_price = df_peramalan_filtered[df_peramalan_filtered['ds'] == last_actual_date]['harga'].mean() if pd.notna(last_actual_date) else 0
        create_metric_card("Harga Aktual Terkini", f"Rp {last_price:,.0f}")

    with col3:
        first_pred_date = df_peramalan_filtered[df_peramalan_filtered['tipe'] == 'Prediksi']['ds'].min()
        first_pred_price = df_peramalan_filtered[df_peramalan_filtered['ds'] == first_pred_date]['harga'].mean() if pd.notna(first_pred_date) else 0
        create_metric_card("Prediksi Harga Berikutnya", f"Rp {first_pred_price:,.0f}")
        
    with col4:
        total_series = len(df_mape_filtered['unique_id'].unique())
        create_metric_card("Jumlah Seri Data", f"{total_series}")

    st.markdown("---")

    # --- Grafik Utama ---
    st.subheader("Tren Harga Historis dan Prediksi")
    
    if selected_lokasi == 'Semua Lokasi' or selected_komoditas == 'Semua Komoditas':
        st.info("Pilih satu Lokasi dan satu Komoditas untuk melihat grafik tren harga.")
    else:
        fig = go.Figure()
        
        # Data Aktual
        aktual_data = df_peramalan_filtered[df_peramalan_filtered['tipe'] == 'Aktual']
        fig.add_trace(go.Scatter(x=aktual_data['ds'], y=aktual_data['harga'], mode='lines', 
                                 name='Harga Aktual', line=dict(color='#4299E1', width=2)))

        # Data Prediksi
        prediksi_data = df_peramalan_filtered[df_peramalan_filtered['tipe'] == 'Prediksi']
        fig.add_trace(go.Scatter(x=prediksi_data['ds'], y=prediksi_data['harga'], mode='lines',
                                 name='Harga Prediksi', line=dict(color='#ED64A6', width=2, dash='dash')))

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Tanggal",
            yaxis_title="Harga (Rp)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)


def render_analisis_peramalan():
    st.title("🔍 Analisis Detail Peramalan")
    st.markdown("Visualisasi perbandingan antara harga aktual dan hasil peramalan model.")
    st.markdown("---")

    if selected_lokasi == 'Semua Lokasi' or selected_komoditas == 'Semua Komoditas':
        st.warning("Silakan pilih satu Lokasi dan satu Komoditas di sidebar untuk melihat analisis detail.")
        return

    st.header(f"Hasil Prediksi untuk: {selected_komoditas} di {selected_lokasi}")

    # --- Grafik Utama ---
    fig = go.Figure()
    aktual_data = df_peramalan_filtered[df_peramalan_filtered['tipe'] == 'Aktual']
    prediksi_data = df_peramalan_filtered[df_peramalan_filtered['tipe'] == 'Prediksi']

    fig.add_trace(go.Scatter(x=aktual_data['ds'], y=aktual_data['harga'], name='Aktual', line=dict(color='cyan', width=2)))
    fig.add_trace(go.Scatter(x=prediksi_data['ds'], y=prediksi_data['harga'], name='Prediksi', line=dict(color='magenta', width=2, dash='dot')))

    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Tanggal",
        yaxis_title="Harga (Rp)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=500,
        xaxis=dict(rangeslider=dict(visible=True), type="date")
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Tabel Data ---
    st.subheader("Data Tabel Prediksi vs Aktual")
    tabel_data = pd.merge(
        aktual_data.rename(columns={'harga': 'Harga Aktual'}),
        prediksi_data.rename(columns={'harga': 'Harga Prediksi'}),
        on=['ds', 'lokasi', 'komoditas'],
        how='inner'
    )[['ds', 'Harga Aktual', 'Harga Prediksi']]
    
    tabel_data['Selisih (%)'] = ((tabel_data['Harga Prediksi'] - tabel_data['Harga Aktual']) / tabel_data['Harga Aktual']) * 100
    
    st.dataframe(tabel_data.style.format({
        "Harga Aktual": "Rp {:,.0f}",
        "Harga Prediksi": "Rp {:,.0f}",
        "Selisih (%)": "{:.2f}%"
    }).background_gradient(cmap='RdYlGn_r', subset=['Selisih (%)'], vmin=-10, vmax=10), use_container_width=True)

def render_evaluasi_model():
    st.title("📊 Evaluasi Model (MAPE)")
    st.markdown("Analisis Mean Absolute Percentage Error (MAPE) untuk mengukur akurasi model di berbagai lokasi dan komoditas.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Performa Model per Komoditas")
        mape_by_comm = df_mape_filtered.groupby('komoditas')['MAPE (%)'].mean().sort_values(ascending=False).reset_index()
        fig_comm = px.bar(mape_by_comm, x='MAPE (%)', y='komoditas', orientation='h', 
                          template="plotly_dark", color='MAPE (%)', color_continuous_scale=px.colors.sequential.Tealgrn)
        fig_comm.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_comm, use_container_width=True)

    with col2:
        st.subheader("Performa Model per Lokasi")
        mape_by_loc = df_mape_filtered.groupby('lokasi')['MAPE (%)'].mean().sort_values(ascending=False).reset_index()
        fig_loc = px.bar(mape_by_loc, x='MAPE (%)', y='lokasi', orientation='h', 
                         template="plotly_dark", color='MAPE (%)', color_continuous_scale=px.colors.sequential.Purpor)
        fig_loc.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_loc, use_container_width=True)
        
    st.markdown("---")
    
    st.subheader("Tabel Detail MAPE")
    st.dataframe(df_mape_filtered[['lokasi', 'komoditas', 'MAPE (%)']].style.format({
        "MAPE (%)": "{:.2f}%"
    }).background_gradient(cmap='viridis_r', subset=['MAPE (%)']), use_container_width=True)

# ==============================================================================
# KONTROL ALUR HALAMAN UTAMA
# ==============================================================================
if page == "Ringkasan Eksekutif":
    render_ringkasan_eksekutif()
elif page == "Analisis Peramalan":
    render_analisis_peramalan()
elif page == "Evaluasi Model (MAPE)":
    render_evaluasi_model()