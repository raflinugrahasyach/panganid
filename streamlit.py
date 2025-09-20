import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ==============================================================================
# KONFIGURASI HALAMAN STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Prediksi Harga Pangan",
    page_icon="🥬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CSS KUSTOM UNTUK GAYA PROFESIONAL
# ==============================================================================
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
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# FUNGSI UNTUK MEMUAT DAN MEMPROSES DATA
# ==============================================================================
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    
    # --- Pre-processing Data ---
    df['ds'] = pd.to_datetime(df['ds'])
    
    # Buat df_mape secara dinamis
    # Hapus baris di mana harga prediksi kosong, karena di situ kita tidak bisa hitung MAPE
    df_pred_only = df.dropna(subset=['harga_prediksi'])
    
    # Hitung MAPE untuk setiap grup
    mape_list = []
    for (lokasi, komoditas), group in df_pred_only.groupby(['lokasi', 'komoditas']):
        mape = np.mean(np.abs((group['harga_aktual'] - group['harga_prediksi']) / group['harga_aktual'])) * 100
        mape_list.append({'lokasi': lokasi, 'komoditas': komoditas, 'MAPE (%)': mape})
    
    df_mape = pd.DataFrame(mape_list)
    
    return df, df_mape

# Muat data dari satu file Excel
df, df_mape = load_data('semua_output.xlsx')


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
lokasi_list = ['Semua Lokasi'] + sorted(df['lokasi'].unique().tolist())
selected_lokasi = st.sidebar.selectbox("Pilih Lokasi:", lokasi_list)

# Filter Komoditas
komoditas_list = ['Semua Komoditas'] + sorted(df['komoditas'].unique().tolist())
selected_komoditas = st.sidebar.selectbox("Pilih Komoditas:", komoditas_list)

# Filter data berdasarkan pilihan sidebar
df_filtered = df.copy()
df_mape_filtered = df_mape.copy()

if selected_lokasi != 'Semua Lokasi':
    df_filtered = df_filtered[df_filtered['lokasi'] == selected_lokasi]
    df_mape_filtered = df_mape_filtered[df_mape_filtered['lokasi'] == selected_lokasi]

if selected_komoditas != 'Semua Komoditas':
    df_filtered = df_filtered[df_filtered['komoditas'] == selected_komoditas]
    df_mape_filtered = df_mape_filtered[df_mape_filtered['komoditas'] == selected_komoditas]


# ==============================================================================
# FUNGSI UNTUK MERENDER SETIAP HALAMAN
# ==============================================================================

def create_metric_card(title, value):
    st.markdown(f"""
    <div class="metric-card">
        <h3>{title}</h3>
        <p>{value}</p>
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
        last_actual_price = df_filtered['harga_aktual'].iloc[-1] if not df_filtered.empty else 0
        create_metric_card("Harga Aktual Terkini", f"Rp {last_actual_price:,.0f}")

    with col3:
        first_pred_price = df_filtered.dropna(subset=['harga_prediksi'])['harga_prediksi'].iloc[0] if not df_filtered.dropna(subset=['harga_prediksi']).empty else 0
        create_metric_card("Prediksi Harga Berikutnya", f"Rp {first_pred_price:,.0f}")
        
    with col4:
        total_series = len(df_filtered.groupby(['lokasi', 'komoditas']))
        create_metric_card("Jumlah Seri Data", f"{total_series}")

    st.markdown("---")

    # --- Grafik Utama ---
    st.subheader("Tren Harga Historis dan Prediksi")
    
    if selected_lokasi == 'Semua Lokasi' or selected_komoditas == 'Semua Komoditas':
        st.info("Pilih satu Lokasi dan satu Komoditas di sidebar untuk melihat grafik tren harga.")
    else:
        fig = go.Figure()
        
        # Data Aktual (solid line)
        fig.add_trace(go.Scatter(x=df_filtered['ds'], y=df_filtered['harga_aktual'], mode='lines', 
                                 name='Harga Aktual', line=dict(color='#4299E1', width=2)))

        # Data Prediksi (dashed line)
        fig.add_trace(go.Scatter(x=df_filtered['ds'], y=df_filtered['harga_prediksi'], mode='lines',
                                 name='Harga Prediksi', line=dict(color='#ED64A6', width=2, dash='dash')))

        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Tanggal",
            yaxis_title="Harga (Rp)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=500
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

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_filtered['ds'], y=df_filtered['harga_aktual'], name='Aktual', line=dict(color='cyan', width=2)))
    fig.add_trace(go.Scatter(x=df_filtered['ds'], y=df_filtered['harga_prediksi'], name='Prediksi', line=dict(color='magenta', width=2, dash='dot')))

    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Tanggal", yaxis_title="Harga (Rp)",
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=500,
        xaxis=dict(rangeslider=dict(visible=True), type="date")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Data Tabel Prediksi vs Aktual")
    tabel_data = df_filtered.dropna(subset=['harga_prediksi'])[['ds', 'harga_aktual', 'harga_prediksi']]
    tabel_data['Selisih (%)'] = ((tabel_data['harga_prediksi'] - tabel_data['harga_aktual']) / tabel_data['harga_aktual']) * 100
    
    st.dataframe(tabel_data.style.format({
        "harga_aktual": "Rp {:,.0f}", "harga_prediksi": "Rp {:,.0f}", "Selisih (%)": "{:.2f}%"
    }).background_gradient(cmap='RdYlGn_r', subset=['Selisih (%)'], vmin=-10, vmax=10), use_container_width=True)

def render_evaluasi_model():
    st.title("📊 Evaluasi Model (MAPE)")
    st.markdown("Analisis Mean Absolute Percentage Error (MAPE) untuk mengukur akurasi model.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Performa Model per Komoditas")
        mape_by_comm = df_mape_filtered.groupby('komoditas')['MAPE (%)'].mean().sort_values(ascending=False).reset_index()
        fig_comm = px.bar(mape_by_comm, x='MAPE (%)', y='komoditas', orientation='h', template="plotly_dark", color='MAPE (%)', color_continuous_scale=px.colors.sequential.Tealgrn)
        fig_comm.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_comm, use_container_width=True)
    with col2:
        st.subheader("Performa Model per Lokasi")
        mape_by_loc = df_mape_filtered.groupby('lokasi')['MAPE (%)'].mean().sort_values(ascending=False).reset_index()
        fig_loc = px.bar(mape_by_loc, x='MAPE (%)', y='lokasi', orientation='h', template="plotly_dark", color='MAPE (%)', color_continuous_scale=px.colors.sequential.Purpor)
        fig_loc.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_loc, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Tabel Detail MAPE")
    st.dataframe(df_mape_filtered[['lokasi', 'komoditas', 'MAPE (%)']].style.format({"MAPE (%)": "{:.2f}%"}).background_gradient(cmap='viridis_r', subset=['MAPE (%)']), use_container_width=True)

# ==============================================================================
# KONTROL ALUR HALAMAN UTAMA
# ==============================================================================
if page == "Ringkasan Eksekutif":
    render_ringkasan_eksekutif()
elif page == "Analisis Peramalan":
    render_analisis_peramalan()
elif page == "Evaluasi Model (MAPE)":
    render_evaluasi_model()