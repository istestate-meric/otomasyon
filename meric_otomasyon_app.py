# ==============================================================================
# MERİÇ İNŞAAT EMLAK & İSTESTATE MERİÇ GAYRİMENKUL DANIŞMANLIK
# Otomatik İmar Okumalı, Logolu Fizibilite ve Sunum Portalı
# ==============================================================================

import streamlit as st
import pandas as pd
from weasyprint import HTML
import base64
import io
import re
import os
from pypdf import PdfWriter
import pdfplumber

st.set_page_config(
    page_title="Meriç & İstestate Ortak Portföy ve Fizibilite Otomasyonu",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Base64 Görsel Dönüştürücü (PDF ve HTML Logoları İçin)
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

istestate_logo_b64 = get_image_base64("istestate_logo.png")
meric_logo_b64 = get_image_base64("meric_insaat_emlak_logo.png")

# Sayı Temizleme Fonksiyonu (TR/US Format Dönüştürücü)
def parse_float(val_str):
    if not val_str:
        return None
    val_str = val_str.strip()
    if ',' in val_str and '.' in val_str:
        if val_str.find(',') < val_str.find('.'):
            val_str = val_str.replace(',', '')
        else:
            val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        parts = val_str.split(',')
        if len(parts[-1]) == 2:
            val_str = val_str.replace(',', '.')
        else:
            val_str = val_str.replace(',', '')
    try:
        return float(val_str)
    except:
        return None

# CSS Stilleri
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

# Üst Başlık ve Logolar
col_l1, col_l2 = st.columns([1, 1])
with col_l1:
    if istestate_logo_b64:
        st.image("istestate_logo.png", width=260)
    else:
        st.markdown("**İSTESTATE GAYRİMENKUL**")
with col_l2:
    if meric_logo_b64:
        st.image("meric_insaat_emlak_logo.png", width=260)
    else:
        st.markdown("**MERİÇ İNŞAAT EMLAK**")

st.markdown('<div class="main-title">Beykoz Arsa İmar, Kat Karşılığı Fizibilite ve Otomatik Sunum Hazırlayıcı</div>', unsafe_allow_html=True)

# Geliştirilmiş Akıllı İmar PDF Okuma Fonksiyonu
def parse_imar_pdf(pdf_bytes):
    extracted = {}
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    
    # Mahalle Tespit
    mahalleler = ["Baklacı", "Görele", "Çiftlik", "Yavuzselim", "Çengeldere", "Fatih"]
    for m in mahalleler:
        if re.search(r'\b' + m + r'\b', text, re.IGNORECASE):
            extracted['mahalle'] = m
            break
            
    # Ada
    ada_match = re.search(r"Ada\s*\n?\s*(\d+)", text)
    if ada_match:
        extracted['ada'] = ada_match.group(1)
        
    # Parsel
    parsel_match = re.search(r"Parsel\s*\n?\s*(\d+)", text)
    if parsel_match:
        extracted['parsel'] = parsel_match.group(1)

    # Arazi Alanı (m²) Okuma - Toplam Parsel Alanı veya Konut Alanı
    alan_matches = re.findall(r"([\d\.,]+)\s*m²", text)
    if alan_matches:
        for am in alan_matches:
            val = parse_float(am)
            if val and val > 100.0:
                extracted['brut_alan'] = val
                break

    # KAKS (Emsal) - 0'dan büyük Konut imar oranını al
    kaks_matches = re.findall(r"Kaks\s*\(Emsal\)\s*\n?\s*([\d\.,]+)", text, re.IGNORECASE)
    for km in kaks_matches:
        val = parse_float(km)
        if val is not None and val > 0:
            extracted['kaks'] = val
            break

    # TAKS - 0'dan büyük olanı al
    taks_matches = re.findall(r"Taks\s*\n?\s*([\d\.,]+)", text, re.IGNORECASE)
    for tm in taks_matches:
        val = parse_float(tm)
        if val is not None and val > 0:
            extracted['taks'] = val
            break

    # Kat Adedi
    kat_matches = re.findall(r"Kat Adedi\s*\n?\s*(\d+)", text, re.IGNORECASE)
    for km in kat_matches:
        if km != "0":
            extracted['kat_sayisi'] = f"{km} Kat"
            break

    return extracted

# --- ANA EKRAN SEKMELERİ ---
tab1, tab2, tab3 = st.tabs(["📊 Canlı Hesaplama & Ön İzleme", "🖼️ Medya ve Belge Yükleme", "📄 PDF Sunum Raporu Oluştur"])

with tab2:
    st.subheader("📷 Arazi Fotoğrafları ve İmar Durum Belgesi Yükleme")
    imar_pdf = st.file_uploader("İmar Durum Belgesi (PDF)", type=["pdf"])
    arazi_fotograflari = st.file_uploader("Arazi / Saha Fotoğrafları (JPG/PNG)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    if imar_pdf:
        st.success(f"✅ İmar Durum Belgesi Yüklendi: {imar_pdf.name}")
        if st.button("⚡ İmar Durumu Verilerini PDF'ten Otomatik Çek ve Hesapla"):
            parsed_data = parse_imar_pdf(imar_pdf.getvalue())
            for k, v in parsed_data.items():
                st.session_state[k] = v
            st.success("🎉 Mahalle, Ada, Parsel, Arazi Alanı (m²), KAKS, TAKS ve Kat Adedi verileri başarıyla aktarıldı!")

# Sidebar Parametreleri
st.sidebar.header("📍 1. Taşınmaz Bilgileri")
mahalle_list = ["Baklacı", "Yavuzselim", "Görele", "Çiftlik", "Çengeldere", "Fatih", "Diğer"]
default_mah_idx = mahalle_list.index(st.session_state.get('mahalle', 'Baklacı')) if st.session_state.get('mahalle') in mahalle_list else 0

mahalle = st.sidebar.selectbox("Mahalle Seçimi", mahalle_list, index=default_mah_idx)
ada = st.sidebar.text_input("Ada No", value=st.session_state.get('ada', '1324'))
parsel = st.sidebar.text_input("Parsel No", value=st.session_state.get('parsel', '9'))
nitelik = st.sidebar.text_input("Tapu Niteliği", value="Bahçe (Terksiz)")
imar_durumu = st.sidebar.selectbox("İmar Statüsü", ["Konut Alanı (KDKS)", "Ticari + Konut", "Gelişme Konut Alanı", "Özel Proje Alanı"])

st.sidebar.header("📐 2. Beykoz İmar Parametreleri")

raw_brut = float(st.session_state.get('brut_alan', 22709.72))
safe_brut = max(100.0, min(500000.0, raw_brut))

raw_kaks = float(st.session_state.get('kaks', 0.40))
safe_kaks = max(0.0, min(3.00, raw_kaks))

raw_taks = float(st.session_state.get('taks', 0.30))
safe_taks = max(0.0, min(0.80, raw_taks))

brut_alan = st.sidebar.number_input("Brüt Arazi Alanı (m²)", min_value=100.0, max_value=500000.0, value=safe_brut, step=50.0)
terk_orani = st.sidebar.slider("Terk Oranı (% - DOP / Yol / Park)", min_value=0.0, max_value=45.0, value=30.0, step=5.0)
kaks = st.sidebar.number_input("KAKS (Emsal)", min_value=0.00, max_value=3.00, value=safe_kaks, step=0.05)
emsal_harici_carpan = st.sidebar.number_input("Emsal Dışı İnşaat Çarpanı", min_value=1.00, max_value=1.50, value=1.30, step=0.05)
taks = st.sidebar.number_input("TAKS (Taban Alanı Katsayısı)", min_value=0.00, max_value=0.80, value=safe_taks, step=0.05)
kat_sayisi = st.sidebar.text_input("Maksimum Kat İzni", value=st.session_state.get('kat_sayisi', '2 Kat'))

st.sidebar.header("💰 3. Maliyet ve Satış Parametreleri")
maliyet_m2 = st.sidebar.number_input("M² İnşaat Birim Maliyeti (₺)", min_value=5000, max_value=200000, value=40000, step=1000)
satis_m2 = st.sidebar.number_input("Bölgesel M² Satış Rayici (₺)", min_value=10000, max_value=1000000, value=250000, step=5000)
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
    st.subheader("🔍 Çıktı Öncesi Özel Notlar")
    ozel_not = st.text_area("Sunuma Eklenecek Özel Notlar / Ekspertiz Görüşü", 
                            value=f"Beykoz {mahalle} Mahallesi {ada}/{parsel} parselde bulunan {brut_alan:,.0f} m² bahçe niteliğindeki arazide %{terk_orani:.0f} terk sonrası net {net_alan:,.0f} m² inşaat alanı kalmaktadır. Kat karşılığı %{kat_karsiligi_oran} paylaşım modeliyle yüksek karlılık öngörülmektedir.")

with tab3:
    st.subheader("🖨️ Kurumsal Sunum Raporu Basımı")
    if st.button("🚀 Logolu PDF Sunum Raporunu Oluştur"):
        foto_html = ""
        if arazi_fotograflari:
            foto_html += '<div class="section-header">📷 Arazi ve Saha Görselleri</div><div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for img in arazi_fotograflari:
                b64_str = base64.b64encode(img.getvalue()).decode("utf-8")
                foto_html += f'<img src="data:{img.type};base64,{b64_str}" style="width: 48%; max-height: 220px; object-fit: cover; border-radius: 6px; border: 1px solid #CBD5E1;" />'
            foto_html += '</div>'

        logo_header_html = '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #F59E0B; padding-bottom: 10px;">'
        if istestate_logo_b64:
            logo_header_html += f'<img src="data:image/png;base64,{istestate_logo_b64}" style="height: 55px;" />'
        else:
            logo_header_html += '<div style="font-size:16px; font-weight:bold; color:#1E293B;">İSTESTATE GAYRİMENKUL</div>'

        if meric_logo_b64:
            logo_header_html += f'<img src="data:image/png;base64,{meric_logo_b64}" style="height: 55px;" />'
        else:
            logo_header_html += '<div style="font-size:16px; font-weight:bold; color:#F59E0B;">MERİÇ İNŞAAT EMLAK</div>'
        logo_header_html += '</div>'

        html_content = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 15mm; }}
                body {{ font-family: Arial, sans-serif; color: #1E293B; line-height: 1.4; }}
                .title {{ font-size: 18px; font-weight: bold; color: #1E293B; margin: 0; text-align: center; }}
                .subtitle {{ font-size: 12px; color: #64748B; margin-top: 4px; text-align: center; margin-bottom: 15px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 15px; }}
                th, td {{ border: 1px solid #E2E8F0; padding: 7px 10px; font-size: 11px; text-align: left; }}
                th {{ background-color: #F8FAFC; color: #475569; }}
                .highlight-row {{ background-color: #FEF3C7; font-weight: bold; }}
                .section-header {{ font-size: 13px; font-weight: bold; color: #0F172A; border-left: 4px solid #F59E0B; padding-left: 8px; margin-top: 18px; margin-bottom: 8px; }}
                .note-box {{ background-color: #F8FAFC; border: 1px solid #CBD5E1; padding: 10px; font-size: 10px; border-radius: 6px; font-style: italic; }}
                .footer {{ margin-top: 25px; text-align: center; font-size: 9px; color: #94A3B8; border-top: 1px solid #E2E8F0; padding-top: 8px; }}
            </style>
        </head>
        <body>
            {logo_header_html}
            
            <div class="title">ARSA İMAR VE FİZİBİLİTE ANALİZ RAPORU</div>
            <div class="subtitle">Beykoz / {mahalle} Mahallesi - {ada} Ada / {parsel} Parsel</div>

            <div class="section-header">📍 1. Taşınmaz ve İmar Durum Bilgileri</div>
            <table>
                <tr><th>Mahalle / Konum</th><td>Beykoz / {mahalle}</td><th>Tapu Niteliği</th><td>{nitelik}</td></tr>
                <tr><th>Ada / Parsel</th><td>{ada} / {parsel}</td><th>İmar Statüsü</th><td>{imar_durumu}</td></tr>
                <tr><th>Brüt Arazi Alanı</th><td>{brut_alan:,.2f} m²</td><th>Terk Oranı</th><td>%{terk_orani:.0f}</td></tr>
                <tr><th>Net Arazi Alanı</th><td>{net_alan:,.2f} m²</td><th>KAKS (Emsal) / TAKS</th><td>{kaks:.2f} / {taks:.2f}</td></tr>
                <tr><th>Maksimum Kat İzni</th><td>{kat_sayisi}</td><th>Emsal Dışı Çarpan</th><td>{emsal_harici_carpan:.2f}</td></tr>
            </table>

            <div class="section-header">📐 2. İnşaat ve Yapılaşma Kapasitesi</div>
            <table>
                <tr><th>Net Emsal İnşaat Alanı</th><td>{net_emsal_inşaat_alani:,.2f} m²</td></tr>
                <tr><th>Taban Oturum Alanı (TAKS)</th><td>{taban_alani:,.2f} m²</td></tr>
                <tr class="highlight-row"><th>Toplam İnşaat Alanı (Satılabilir/Kullanılabilir)</th><td>{toplam_inşaat_alani:,.2f} m²</td></tr>
            </table>

            <div class="section-header">💰 3. Kat Karşılığı Fizibilite ve Karlılık Tablosu</div>
            <table>
                <tr><th>M² İnşaat Birim Maliyeti</th><td>{maliyet_m2:,.0f} ₺</td><th>Bölgesel M² Satış Rayici</th><td>{satis_m2:,.0f} ₺</td></tr>
                <tr><th>Toplam Proje Maliyeti</th><td>{toplam_maliyet:,.0f} ₺</td><th>Toplam Proje Hasılatı</th><td>{toplam_hasilat:,.0f} ₺</td></tr>
                <tr><th>Kat Karşılığı Paylaşım Oranı</th><td colspan="3">% {kat_karsiligi_oran} Müteahhit / % {100 - kat_karsiligi_oran} Arsa Sahibi</td></tr>
                <tr><th>Müteahhit Hasılat Payı</th><td>{muteahhit_hasilat_payi:,.0f} ₺</td><th>Arsa Sahibi Hasılat Payı</th><td>{arsa_sahibi_hasilat_payi:,.0f} ₺</td></tr>
                <tr class="highlight-row"><th>Müteahhit Net Karı</th><td>{muteahhit_net_kar:,.0f} ₺</td><th>Öngörülen Kar Marjı</th><td>%{kar_marji:.1f}</td></tr>
            </table>

            <div class="section-header">📝 4. Ekspertiz Notları ve Değerlendirme</div>
            <div class="note-box">{ozel_not}</div>

            {foto_html}

            <div class="footer">
                Bu rapor Istestate Gayrimenkul ve Meriç İnşaat Emlak bilgi sistemleri tarafından otomatik üretilmiştir.<br>
                Resmi belge niteliği taşımaz, fizibilite ve ön inceleme amaçlıdır.
            </div>
        </body>
        </html>
        """
        
        try:
            main_pdf_bytes = HTML(string=html_content).write_pdf()
            
            if imar_pdf is not None:
                merger = PdfWriter()
                merger.append(io.BytesIO(main_pdf_bytes))
                merger.append(io.BytesIO(imar_pdf.getvalue()))
                
                final_output = io.BytesIO()
                merger.write(final_output)
                final_pdf_bytes = final_output.getvalue()
                merger.close()
            else:
                final_pdf_bytes = main_pdf_bytes

            st.session_state['pdf_bytes'] = final_pdf_bytes
            st.success("✅ Logolu PDF Sunum Raporu başarıyla oluşturuldu!")
        except Exception as e:
            st.error(f"PDF oluşturulurken hata meydana geldi: {e}")

    if 'pdf_bytes' in st.session_state:
        st.download_button(
            label="📥 Logolu PDF Raporunu Bilgisayara İndir",
            data=st.session_state['pdf_bytes'],
            file_name=f"Beykoz_{mahalle}_{ada}_{parsel}_Fizibilite_Raporu.pdf",
            mime="application/pdf"
        )
