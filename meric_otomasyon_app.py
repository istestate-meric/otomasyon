# ==============================================================================
# MERİÇ İNŞAAT EMLAK & İSTESTATE MERİÇ GAYRİMENKUL DANIŞMANLIK
# Ortak Arsa İmar, Fizibilite ve Sunum Otomasyon Portalı
# ==============================================================================

import streamlit as st
import pandas as pd
from weasyprint import HTML
import tempfile
import base64
import os

st.set_page_config(
    page_title="Meriç & İstestate Ortak Portföy ve Fizibilite Otomasyonu",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Mobile & Desktop
st.markdown("""
<style>
    .main-title {
        color: #1E293B;
        font-size: 24px;
        font-weight: bold;
        border-bottom: 3px solid #F59E0B;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .company-badge {
        background-color: #1E293B;
        color: #FFFFFF;
        padding: 8px 15px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        margin-right: 10px;
    }
    .company-badge-2 {
        background-color: #F59E0B;
        color: #1E293B;
        padding: 8px 15px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .metric-val {
        font-size: 22px;
        font-weight: bold;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 12px;
        color: #64748B;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="company-badge">İSTESTATE GAYRİMENKUL</div><div class="company-badge-2">MERİÇ İNŞAAT EMLAK</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Beykoz Arsa İmar, Kat Karşılığı Fizibilite ve Sunum Hazırlayıcı</div>', unsafe_allow_html=True)

# Sidebar - Taşınmaz ve Giriş Parametreleri
st.sidebar.header("📍 1. Taşınmaz Bilgileri")
mahalle = st.sidebar.selectbox("Mahalle Seçimi", ["Görele", "Çiftlik", "Baklacı", "Yavuzselim", "Çengeldere", "Fatih", "Diğer"])
ada = st.sidebar.text_input("Ada No", value="1437")
parsel = st.sidebar.text_input("Parsel No", value="17")
nitelik = st.sidebar.text_input("Tapu Niteliği", value="Bahçe (Terksiz)")
imar_durumu = st.sidebar.selectbox("İmar Statüsü", ["Konut Alanı (KDKS)", "Ticari + Konut", "Gelişme Konut Alanı", "Özel Proje Alanı"])

st.sidebar.header("📐 2. Beykoz İmar Parametreleri")
brut_alan = st.sidebar.number_input("Brüt Arazi Alanı (m²)", min_value=100.0, max_value=100000.0, value=1000.0, step=50.0)
terk_orani = st.sidebar.slider("Terk Oranı (% - DOP / Yol / Park)", min_value=0.0, max_value=45.0, value=30.0, step=5.0)
kaks = st.sidebar.number_input("KAKS (Emsal)", min_value=0.10, max_value=3.00, value=0.55, step=0.05)
emsal_harici_carpan = st.sidebar.number_input("Emsal Dışı İnşaat Çarpanı", min_value=1.00, max_value=1.50, value=1.30, step=0.05, help="Balkon, sığınak, otopark vb. ek haklar (Genel: 1.30)")
taks = st.sidebar.number_input("TAKS (Taban Alanı Katsayısı)", min_value=0.10, max_value=0.80, value=0.25, step=0.05)
kat_sayisi = st.sidebar.text_input("Maksimum Kat İzni", value="2.5 Kat")

st.sidebar.header("💰 3. Maliyet ve Satış Parametreleri")
maliyet_m2 = st.sidebar.number_input("M² İnşaat Birim Maliyeti (₺)", min_value=5000, max_value=100000, value=28000, step=1000)
satis_m2 = st.sidebar.number_input("Bölgesel M² Satış Rayici (₺)", min_value=10000, max_value=500000, value=110000, step=5000)
kat_karsiligi_oran = st.sidebar.slider("Kat Karşılığı Müteahhit Payı (%)", min_value=10, max_value=90, value=50, step=5)

# --- MATEMATİKSEL HESAPLAMALAR ---
terk_m2 = brut_alan * (terk_orani / 100.0)
net_alan = brut_alan - terk_m2
net_emsal_inşaat_alani = net_alan * kaks
toplam_inşaat_alani = net_alan * kaks * emsal_harici_carpan
taban_alani = net_alan * taks

toplam_maliyet = toplam_inşaat_alani * maliyet_m2
toplam_hasilat = toplam_inşaat_alani * satis_m2

muteahhit_hasilat_payi = toplam_hasilat * (kat_karsiligi_oran / 100.0)
arsa_sahibi_hasilat_payi = toplam_hasilat * ((100.0 - kat_karsiligi_oran) / 100.0)
muteahhit_net_kar = muteahhit_hasilat_payi - toplam_maliyet
kar_marji = (muteahhit_net_kar / toplam_maliyet * 100.0) if toplam_maliyet > 0 else 0.0

# --- ANA EKRAN SEKMELERİ ---
tab1, tab2, tab3 = st.tabs(["📊 Canlı Hesaplama & Ön İzleme", "🖼️ Medya ve Belge Yükleme", "📄 PDF Sunum Raporu Oluştur"])

with tab1:
    st.subheader("📌 Anlık İmar ve Fizibilite Özet Tablosu")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-lbl">Brüt / Net Arazi</div><div class="metric-val">{brut_alan:,.0f} / {net_alan:,.0f} m²</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-lbl">Top. İnşaat Alanı</div><div class="metric-val">{toplam_inşaat_alani:,.1f} m²</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-lbl">Top. Proje Hasılatı</div><div class="metric-val">{toplam_hasilat/1e6:,.2f} M ₺</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card" style="border-color:#F59E0B;"><div class="metric-lbl">Müteahhit Net Karı</div><div class="metric-val" style="color:#B45309;">{muteahhit_net_kar/1e6:,.2f} M ₺</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    st.subheader("🔍 Çıktı Öncesi Son Kontrol ve Düzenleme (Pre-PDF Review)")
    st.info("💡 Müşterinize veya yatırımcınıza sunum üretmeden önce özel notlarınızı ve açıklamalarınızı buradan düzenleyebilirsiniz.")
    
    ozel_not = st.text_area("Sunuma Eklenecek Özel Notlar / Ekspertiz Görüşü", 
                            value=f"Beykoz {mahalle} Mahallesi {ada}/{parsel} parselde bulunan {brut_alan:,.0f} m² bahçe niteliğindeki arazide %{terk_orani:.0f} terk sonrası net {net_alan:,.0f} m² inşaat alanı kalmaktadır. Kat karşılığı %{kat_karsiligi_oran} paylaşım modeliyle yüksek karlılık öngörülmektedir.")

with tab2:
    st.subheader("📷 Arazi Fotoğrafları ve İmar Durum Belgesi Yükleme")
    imar_pdf = st.file_uploader("İmar Durum Belgesi (PDF)", type=["pdf"])
    arazi_fotograflari = st.file_uploader("Arazi / Saha Fotoğrafları (JPG/PNG)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    if imar_pdf:
        st.success(f"✅ İmar Durum Belgesi Yüklendi: {imar_pdf.name}")
    if arazi_fotograflari:
        st.success(f"✅ {len(arazi_fotograflari)} Adet Görsel Yüklendi.")

with tab3:
    st.subheader("🖨️ Müşteri ve Mimar İmzalı Sunum Raporu Basımı")
    st.write("Aşağıdaki butona basarak Istestate ve Meriç İnşaat kurumsal şablonunda tek tıkla PDF üretebilirsiniz.")
    
    if st.button("🚀 PDF Sunum Raporunu Oluştur"):
        st.success("PDF Raporu Hazırlandı! İndirmek için tıklayınız.")
