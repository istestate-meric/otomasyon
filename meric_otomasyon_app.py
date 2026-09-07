# ==============================================================================
# MERİÇ İNŞAAT EMLAK & İSTESTATE MERİÇ GAYRİMENKUL DANIŞMANLIK
# Çoklu Parsel (Tevhit) Destekli Otomatik İmar ve Fizibilite Portalı
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

# Base64 Görsel Dönüştürücü
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

istestate_logo_b64 = get_image_base64("istestate_logo.png")
meric_logo_b64 = get_image_base64("meric_insaat_emlak_logo.png")

# Sayı Temizleme Fonksiyonu
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

# Hassas İmar PDF Okuyucu (Konum Odaklı Terk ve Nitelik Ayrıştırma)
def parse_single_imar_pdf(pdf_bytes):
    extracted = {}
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    
    mahalle_map = {
        "YAVUZSELİM": "Yavuzselim", "YAVUZSELIM": "Yavuzselim",
        "ÇİFTLİK": "Çiftlik", "CİFTLİK": "Çiftlik", "CIFTLIK": "Çiftlik",
        "BAKLACI": "Baklacı", "GÖRELE": "Görele", "GORELE": "Görele",
        "ÇENGELDERE": "Çengeldere", "CENGELDERE": "Çengeldere",
        "FATİH": "Fatih", "FATIH": "Fatih"
    }

    # 1. Mahalle
    mah_match = re.search(r"(YAVUZSELİM|YAVUZSELIM|ÇİFTLİK|CİFTLİK|CIFTLIK|BAKLACI|GÖRELE|GORELE|ÇENGELDERE|CENGELDERE|FATİH|FATIH)", text, re.IGNORECASE)
    extracted['mahalle'] = mahalle_map.get(mah_match.group(1).upper(), "Yavuzselim") if mah_match else "Yavuzselim"

    # 2. Ada / Parsel / Brüt Alan
    table_match = re.search(r"(\d{3,5})\s*[\|\s]+\s*(\d{1,5})\s*[\|\s]+\s*([\d\.,]+)\s*m²", text)
    if table_match:
        extracted['ada'] = table_match.group(1)
        extracted['parsel'] = table_match.group(2)
        extracted['brut_alan'] = parse_float(table_match.group(3))
    else:
        ada_m = re.search(r"Ada\s*[:\n\|\s]*(\d+)", text, re.IGNORECASE)
        parsel_m = re.search(r"Parsel\s*[:\n\|\s]*(\d+)", text, re.IGNORECASE)
        alan_m = re.search(r"([\d\.,]+)\s*m²", text)
        extracted['ada'] = ada_m.group(1) if ada_m else "1647"
        extracted['parsel'] = parsel_m.group(1) if parsel_m else "10"
        extracted['brut_alan'] = parse_float(alan_m.group(1)) if alan_m else 1000.0

    # 3. Konut Alanı Yüzdesi ve Terk / Tapu Niteliği Hesabı
    konut_perc = None
    konut_pos = re.search(r"(?:KONUT|TİCARİ|TICARI)\s+ALANI", text, re.IGNORECASE)
    if konut_pos:
        sub_text = text[konut_pos.start():konut_pos.start()+350]
        perc_match = re.search(r"%\s*([\d\.,]+)", sub_text)
        if perc_match:
            konut_perc = parse_float(perc_match.group(1))

    if konut_perc is None:
        perc_all = re.findall(r"%\s*([\d\.,]+)", text)
        if perc_all:
            valid_percs = [parse_float(p) for p in perc_all if parse_float(p) is not None and parse_float(p) <= 100]
            if valid_percs:
                konut_perc = valid_percs[0]

    if konut_perc is not None and konut_perc < 99.0:
        extracted['terk_orani'] = round(100.0 - konut_perc, 2)
        extracted['nitelik'] = "Bahçe"
    else:
        extracted['terk_orani'] = 0.0
        extracted['nitelik'] = "Arsa"

    # 4. KAKS / TAKS / Kat
    kaks_m = re.search(r"Kaks\s*\(Emsal\)\s*[:\n\|\s]*([\d\.,]+)", text, re.IGNORECASE)
    extracted['kaks'] = parse_float(kaks_m.group(1)) if kaks_m else 0.45
    
    taks_m = re.search(r"Taks\s*[:\n\|\s]*([\d\.,]+)", text, re.IGNORECASE)
    extracted['taks'] = parse_float(taks_m.group(1)) if taks_m else 0.30
    
    kat_m = re.search(r"Kat\s*Adedi\s*[:\n\|\s]*(\d+)", text, re.IGNORECASE)
    extracted['kat_sayisi'] = f"{kat_m.group(1)} Kat" if (kat_m and kat_m.group(1) != "0") else "2 Kat"

    return extracted

# Üst Başlık
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

st.markdown('<h2 style="color:#1E293B; border-bottom:3px solid #F59E0B; padding-bottom:10px;">Beykoz Çoklu Parsel (Tevhit) Fizibilite ve Otomatik Sunum Portalı</h2>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Canlı Hesaplama & Ön İzleme", "🖼️ Medya ve Belge Yükleme", "📄 PDF Sunum Raporu Oluştur"])

with tab2:
    st.subheader("📷 İmar Belgesi (Tek/Çoklu PDF) ve Saha Fotoğrafları Yükleme")
    imar_pdfs = st.file_uploader("İmar Durum Belgeleri (Birden fazla seçebilirsiniz)", type=["pdf"], accept_multiple_files=True)
    arazi_fotograflari = st.file_uploader("Arazi Fotoğrafları (JPG/PNG)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    
    if imar_pdfs:
        st.success(f"✅ {len(imar_pdfs)} Adet İmar Durum Belgesi Yüklendi.")
        if st.button("⚡ Parselleri Oku ve Tevhit (Birleştirme) Yaparak Hesapla"):
            parcels = []
            for pdf_file in imar_pdfs:
                p_data = parse_single_imar_pdf(pdf_file.getvalue())
                parcels.append(p_data)
            
            total_brut = sum(p.get('brut_alan', 0) for p in parcels)
            total_net = sum(p.get('brut_alan', 0) * (1.0 - p.get('terk_orani', 0)/100.0) for p in parcels)
            agg_terk = round((1.0 - (total_net / total_brut)) * 100.0, 2) if total_brut > 0 else 0.0
            
            adas = list(set(p['ada'] for p in parcels if p.get('ada')))
            parsel_names = [f"{p.get('ada')}/{p.get('parsel')}" for p in parcels if p.get('parsel')]
            
            st.session_state['mahalle'] = parcels[0]['mahalle']
            st.session_state['ada'] = "/".join(adas)
            st.session_state['parsel'] = " + ".join(parsel_names) if len(parcels) > 1 else parcels[0]['parsel']
            st.session_state['brut_alan'] = total_brut
            st.session_state['terk_orani'] = agg_terk
            st.session_state['nitelik'] = "Bahçe" if agg_terk > 0 else "Arsa"
            st.session_state['kaks'] = parcels[0]['kaks']
            st.session_state['taks'] = parcels[0]['taks']
            st.session_state['kat_sayisi'] = parcels[0]['kat_sayisi']
            st.session_state['pdf_files'] = [f.getvalue() for f in imar_pdfs]
            
            st.success(f"🎉 {len(parcels)} Parsel Başarıyla Birleştirildi! Toplam Brüt: {total_brut:,.2f} m² | Ağırlıklı Terk: %{agg_terk:.2f}")
            st.rerun()

# Sidebar
st.sidebar.header("📍 1. Taşınmaz Bilgileri")
mahalle_list = ["Yavuzselim", "Çiftlik", "Baklacı", "Görele", "Çengeldere", "Fatih", "Diğer"]
default_mah_idx = mahalle_list.index(st.session_state.get('mahalle', 'Yavuzselim')) if st.session_state.get('mahalle') in mahalle_list else 0

mahalle = st.sidebar.selectbox("Mahalle Seçimi", mahalle_list, index=default_mah_idx)
ada = st.sidebar.text_input("Ada No", value=st.session_state.get('ada', '1647'))
parsel = st.sidebar.text_input("Parsel No (Tevhit için + ile birleşir)", value=st.session_state.get('parsel', '10'))
nitelik = st.sidebar.text_input("Tapu Niteliği", value=st.session_state.get('nitelik', 'Bahçe'))
imar_durumu = st.sidebar.selectbox("İmar Statüsü", ["Konut Alanı (KDKS)", "Ticari + Konut", "Gelişme Konut Alanı", "Özel Proje Alanı"])

st.sidebar.header("📐 2. Beykoz İmar Parametreleri")
brut_alan = st.sidebar.number_input("Brüt Arazi Alanı (m²)", min_value=100.0, max_value=500000.0, value=float(st.session_state.get('brut_alan', 6398.86)), step=50.0)
terk_orani = st.sidebar.number_input("Terk Oranı (%)", min_value=0.0, max_value=45.0, value=float(st.session_state.get('terk_orani', 21.06)), step=0.1)
kaks = st.sidebar.number_input("KAKS (Emsal)", min_value=0.00, max_value=3.00, value=float(st.session_state.get('kaks', 0.40)), step=0.05)
emsal_harici_carpan = st.sidebar.number_input("Emsal Dışı İnşaat Çarpanı", min_value=1.00, max_value=1.50, value=1.30, step=0.05)
taks = st.sidebar.number_input("TAKS (Taban Alanı Katsayısı)", min_value=0.00, max_value=0.80, value=float(st.session_state.get('taks', 0.30)), step=0.05)
kat_sayisi = st.sidebar.text_input("Maksimum Kat İzni", value=st.session_state.get('kat_sayisi', '2 Kat'))

st.sidebar.header("💰 3. Maliyet ve Satış Parametreleri")
maliyet_m2 = st.sidebar.number_input("M² İnşaat Birim Maliyeti (₺)", min_value=5000, max_value=200000, value=40000, step=1000)
satis_m2 = st.sidebar.number_input("Bölgesel M² Satış Rayici (₺)", min_value=10000, max_value=1000000, value=250000, step=5000)
kat_karsiligi_oran = st.sidebar.slider("Kat Karşılığı Müteahhit Payı (%)", min_value=10, max_value=90, value=50, step=5)

# Matematik
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
    col1.metric("Brüt / Net Arazi", f"{brut_alan:,.2f} m²", f"Net: {net_alan:,.2f} m²")
    col2.metric("Top. İnşaat Alanı", f"{toplam_inşaat_alani:,.1f} m²")
    col3.metric("Top. Proje Hasılatı", f"{toplam_hasilat/1e6:,.2f} M ₺")
    col4.metric("Müteahhit Net Karı", f"{muteahhit_net_kar/1e6:,.2f} M ₺", f"%{kar_marji:.1f} Kar Marjı")

    st.markdown("---")
    default_not = f"Beykoz {mahalle} Mahallesi {ada} Ada / {parsel} parsel(ler)inde toplam {brut_alan:,.2f} m² {nitelik.lower()} alan üzerinde %{terk_orani:.2f} terk sonrası net {net_alan:,.2f} m² proje alanı kalmaktadır."
    ozel_not = st.text_area("Sunuma Eklenecek Özel Notlar / Ekspertiz Görüşü", value=default_not)

with tab3:
    st.subheader("🖨️ Kurumsal Sunum Raporu Basımı")
    if st.button("🚀 Logolu PDF Sunum Raporunu Oluştur"):
        foto_html = ""
        if arazi_fotograflari:
            foto_html += '<div style="font-weight:bold; margin-top:15px;">📷 Arazi Görselleri</div><div style="display:flex; flex-wrap:wrap; gap:10px;">'
            for img in arazi_fotograflari:
                b64_str = base64.b64encode(img.getvalue()).decode("utf-8")
                foto_html += f'<img src="data:{img.type};base64,{b64_str}" style="width:48%; max-height:200px; object-fit:cover; border-radius:4px;" />'
            foto_html += '</div>'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 12mm; }}
                body {{ font-family: Arial, sans-serif; color: #1E293B; font-size: 11px; }}
                .title {{ font-size: 16px; font-weight: bold; text-align: center; color: #1E293B; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 12px; }}
                th, td {{ border: 1px solid #CBD5E1; padding: 6px 8px; text-align: left; }}
                th {{ background-color: #F8FAFC; }}
                .highlight {{ background-color: #FEF3C7; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="title">ARSA İMAR VE TEVHİT FİZİBİLİTE ANALİZ RAPORU</div>
            <div style="text-align:center; color:#64748B; margin-bottom:12px;">Beykoz / {mahalle} - Ada: {ada} | Parsel: {parsel}</div>

            <strong>📍 1. Taşınmaz ve İmar Durumu</strong>
            <table>
                <tr><th>Mahalle / Konum</th><td>Beykoz / {mahalle}</td><th>Tapu Niteliği</th><td>{nitelik}</td></tr>
                <tr><th>Ada / Parsel</th><td>{ada} / {parsel}</td><th>İmar Statüsü</th><td>{imar_durumu}</td></tr>
                <tr><th>Brüt Arazi Alanı</th><td>{brut_alan:,.2f} m²</td><th>Ağırlıklı Terk Oranı</th><td>%{terk_orani:.2f}</td></tr>
                <tr><th>Net Arazi Alanı</th><td>{net_alan:,.2f} m²</td><th>KAKS / TAKS</th><td>{kaks:.2f} / {taks:.2f}</td></tr>
            </table>

            <strong>📐 2. İnşaat Kapasitesi</strong>
            <table>
                <tr><th>Net Emsal İnşaat Alanı</th><td>{net_emsal_inşaat_alani:,.2f} m²</td></tr>
                <tr class="highlight"><th>Toplam Satılabilir / Kullanılabilir Alan</th><td>{toplam_inşaat_alani:,.2f} m²</td></tr>
            </table>

            <strong>💰 3. Kat Karşılığı Fizibilite</strong>
            <table>
                <tr><th>M² İnşaat Birim Maliyeti</th><td>{maliyet_m2:,.0f} ₺</td><th>Bölgesel M² Satış Rayici</th><td>{satis_m2:,.0f} ₺</td></tr>
                <tr><th>Toplam Proje Maliyeti</th><td>{toplam_maliyet:,.0f} ₺</td><th>Toplam Proje Hasılatı</th><td>{toplam_hasilat:,.0f} ₺</td></tr>
                <tr class="highlight"><th>Müteahhit Net Karı</th><td>{muteahhit_net_kar:,.0f} ₺</td><th>Kar Marjı</th><td>%{kar_marji:.1f}</td></tr>
            </table>

            <div style="background:#F8FAFC; border:1px solid #CBD5E1; padding:8px; font-style:italic;">{ozel_not}</div>
            {foto_html}
        </body>
        </html>
        """
        
        main_pdf_bytes = HTML(string=html_content).write_pdf()
        
        if 'pdf_files' in st.session_state and st.session_state['pdf_files']:
            merger = PdfWriter()
            merger.append(io.BytesIO(main_pdf_bytes))
            for pdf_b in st.session_state['pdf_files']:
                merger.append(io.BytesIO(pdf_b))
            
            final_output = io.BytesIO()
            merger.write(final_output)
            final_pdf_bytes = final_output.getvalue()
            merger.close()
        else:
            final_pdf_bytes = main_pdf_bytes

        st.session_state['pdf_bytes'] = final_pdf_bytes
        st.success("✅ Rapor Hazırlandı!")

    if 'pdf_bytes' in st.session_state:
        st.download_button(
            label="📥 PDF Raporunu İndir",
            data=st.session_state['pdf_bytes'],
            file_name=f"Beykoz_{mahalle}_Tevhit_Fizibilite_Raporu.pdf",
            mime="application/pdf"
        )
