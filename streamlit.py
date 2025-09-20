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
body { font-family: 'Segoe UI', sans-serif; }
.main .block-container { padding: 2rem 3rem; }
.css-1d391kg { background-color: #0F1116; }
.metric-card {
    background-color: #1A202C;
    border: 1px solid #2D3748;
    border-radius: 0.5rem;
    padding: 1.5rem;
    margin-bottom: 1rem;
    text-align: center;
    color: white;
}
.metric-card h3 { font-size: 1.25rem; color: #A0AEC0; margin-bottom: 0.5rem; }
.metric-card p { font-size: 2.5rem; font-weight: 700; margin: 0; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# FUNGSI UNTUK MEMUAT DAN MEMPROSES DATA
# ==============================================================================
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    df['ds'] = pd.to_datetime(df['ds'])
    
    df_pred_only = df.dropna(subset=['harga_prediksi', 'harga_aktual'])
    df_pred_only = df_pred_only[df_pred_only['harga_aktual'] != 0]
    
    mape_list = []
    for (lokasi, komoditas), group in df_pred_only.groupby(['lokasi', 'komoditas']):
        mape = np.mean(np.abs((group['harga_aktual'] - group['harga_prediksi']) / group['harga_aktual'])) * 100
        mape_list.append({'lokasi': lokasi, 'komoditas': komoditas, 'MAPE (%)': mape})
    
    df_mape = pd.DataFrame(mape_list)
    return df, df_mape

try:
    df, df_mape = load_data('semua_output.xlsx')
except FileNotFoundError:
    st.error("Error: File `semua_output.xlsx` tidak ditemukan. Pastikan file ada di folder yang sama.")
    st.stop()


# ==============================================================================
# SIDEBAR UNTUK NAVIGASI DAN FILTER
# ==============================================================================
st.sidebar.title("Navigasi Dashboard")
page = st.sidebar.radio("Pilih Halaman:", ("Ringkasan Eksekutif", "Analisis Peramalan", "Evaluasi Model (MAPE)"))

st.sidebar.markdown("---")
st.sidebar.header("Filter Data")

sorted_lokasi = sorted(df['lokasi'].unique().tolist())
selected_lokasi = st.sidebar.multiselect("Pilih Lokasi:", sorted_lokasi, default=sorted_lokasi[:1])

sorted_komoditas = sorted(df['komoditas'].unique().tolist())
selected_komoditas = st.sidebar.multiselect("Pilih Komoditas:", sorted_komoditas, default=sorted_komoditas[:1])

if not selected_lokasi or not selected_komoditas:
    st.warning("Silakan pilih minimal satu Lokasi dan satu Komoditas di sidebar.")
    st.stop()

df_filtered = df[(df['lokasi'].isin(selected_lokasi)) & (df['komoditas'].isin(selected_komoditas))]
df_mape_filtered = df_mape[(df_mape['lokasi'].isin(selected_lokasi)) & (df_mape['komoditas'].isin(selected_komoditas))]


# ==============================================================================
# HEADER UTAMA DENGAN DETAIL
# ==============================================================================
st.title("Dashboard Prediksi Harga Pangan")
st.subheader(f"Menampilkan: {len(selected_komoditas)} Komoditas di {len(selected_lokasi)} Lokasi")
min_date = df_filtered['ds'].min().strftime('%d %B %Y')
max_date = df_filtered['ds'].max().strftime('%d %B %Y')
st.markdown(f"**Rentang Waktu Data:** {min_date} hingga {max_date}")
st.markdown("---")


# ==============================================================================
# FUNGSI UNTUK MERENDER SETIAP HALAMAN
# ==============================================================================

def create_metric_card(title, value):
    st.markdown(f'<div class="metric-card"><h3>{title}</h3><p>{value}</p></div>', unsafe_allow_html=True)

def render_ringkasan_eksekutif():
    st.header("📈 Ringkasan Eksekutif")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_mape = df_mape_filtered['MAPE (%)'].mean() if not df_mape_filtered.empty else 0
        create_metric_card("MAPE Rata-rata", f"{avg_mape:.2f}%")
    with col2:
        last_actual = df_filtered.dropna(subset=['harga_aktual']).sort_values('ds').iloc[-1] if not df_filtered.empty else None
        create_metric_card("Harga Aktual Terkini", f"Rp {last_actual['harga_aktual']:,.0f}" if last_actual is not None else "N/A")
    with col3:
        first_pred = df_filtered.dropna(subset=['harga_prediksi']).sort_values('ds').iloc[0] if not df_filtered.dropna(subset=['harga_prediksi']).empty else None
        create_metric_card("Prediksi Awal", f"Rp {first_pred['harga_prediksi']:,.0f}" if first_pred is not None else "N/A")
    with col4:
        total_series = len(df_filtered.groupby(['lokasi', 'komoditas']))
        create_metric_card("Jumlah Seri Data", f"{total_series}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- PERBAIKAN: Tampilkan banyak grafik ---
    st.subheader("Grafik Tren Harga Historis dan Prediksi")
    for (lokasi, komoditas), group in df_filtered.groupby(['lokasi', 'komoditas']):
        st.markdown(f"#### {komoditas} di {lokasi}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=group['ds'], y=group['harga_aktual'], mode='lines', name='Harga Aktual', line=dict(color='#4299E1', width=2)))
        fig.add_trace(go.Scatter(x=group['ds'], y=group['harga_prediksi'], mode='lines', name='Harga Prediksi', line=dict(color='#ED64A6', width=2, dash='dash')))
        fig.update_layout(template="plotly_dark", xaxis_title=None, yaxis_title="Harga (Rp)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400, margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

def render_analisis_peramalan():
    st.header("🔍 Analisis Detail Peramalan")
    st.markdown("Visualisasi perbandingan antara harga aktual dan hasil peramalan model untuk setiap data yang dipilih.")

    # --- PERBAIKAN: Tampilkan banyak grafik dengan tabel detail ---
    for (lokasi, komoditas), group in df_filtered.groupby(['lokasi', 'komoditas']):
        st.markdown("---")
        st.subheader(f"Hasil Prediksi untuk: {komoditas} di {lokasi}")

        col1, col2 = st.columns([2, 1]) # Buat 2 kolom, grafik lebih besar
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=group['ds'], y=group['harga_aktual'], name='Aktual', line=dict(color='cyan', width=2)))
            fig.add_trace(go.Scatter(x=group['ds'], y=group['harga_prediksi'], name='Prediksi', line=dict(color='magenta', width=2, dash='dot')))
            fig.update_layout(template="plotly_dark", yaxis_title="Harga (Rp)", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400, legend=dict(orientation="h", y=1.1), margin=dict(t=40, b=40))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Data Tabel**")
            tabel_data = group.dropna(subset=['harga_prediksi'])[['ds', 'harga_aktual', 'harga_prediksi']]
            tabel_data['Selisih (%)'] = ((tabel_data['harga_prediksi'] - tabel_data['harga_aktual']) / tabel_data['harga_aktual']) * 100
            st.dataframe(tabel_data.style.format({"harga_aktual": "Rp {:,.0f}", "harga_prediksi": "Rp {:,.0f}", "Selisih (%)": "{:.2f}%"}), height=380)

def render_evaluasi_model():
    st.header("📊 Evaluasi Model (MAPE)")
    
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
    st.dataframe(df_mape_filtered[['lokasi', 'komoditas', 'MAPE (%)']].sort_values('MAPE (%)').style.format({"MAPE (%)": "{:.2f}%"}).background_gradient(cmap='viridis_r', subset=['MAPE (%)']), use_container_width=True)

# ==============================================================================
# KONTROL ALUR HALAMAN UTAMA
# ==============================================================================
if page == "Ringkasan Eksekutif":
    render_ringkasan_eksekutif()
elif page == "Analisis Peramalan":
    render_analisis_peramalan()
elif page == "Evaluasi Model (MAPE)":
    render_evaluasi_model()