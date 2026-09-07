# ==============================================================================
# MERİÇ İNŞAAT EMLAK & İSTESTATE MERİÇ GAYRİMENKUL DANIŞMANLIK
# Ortak Arsa İmar, Fizibilite ve Sunum Otomasyon Portalı
# ==============================================================================

import streamlit as st
import pandas as pd
from weasyprint import HTML
import base64
import io
from pypdf import PdfWriter, PdfReader

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
        # Yüklenen fotoğrafları HTML için base64 biçimine çevirme
        foto_html = ""
        if arazi_fotograflari:
            foto_html += '<div class="section-header">📷 Arazi ve Saha Görselleri</div><div style="display: flex; flex-wrap: wrap; gap: 10px;">'
            for img in arazi_fotograflari:
                b64_str = base64.b64encode(img.getvalue()).decode("utf-8")
                foto_html += f'<img src="data:{img.type};base64,{b64_str}" style="width: 48%; max-height: 250px; object-fit: cover; border-radius: 6px; border: 1px solid #CBD5E1;" />'
            foto_html += '</div>'

        # WeasyPrint için Kurumsal HTML Şablonu
        html_content = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 20mm; }}
                body {{ font-family: Arial, sans-serif; color: #1E293B; line-height: 1.5; }}
                .header {{ border-bottom: 3px solid #F59E0B; padding-bottom: 12px; margin-bottom: 20px; }}
                .title {{ font-size: 20px; font-weight: bold; color: #1E293B; margin: 0; }}
                .subtitle {{ font-size: 12px; color: #64748B; margin-top: 5px; }}
                .badge-container {{ margin-bottom: 15px; }}
                .badge {{ background-color: #1E293B; color: #fff; padding: 5px 10px; font-size: 11px; font-weight: bold; border-radius: 4px; display: inline-block; }}
                .badge-orange {{ background-color: #F59E0B; color: #1E293B; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #E2E8F0; padding: 8px 12px; font-size: 12px; text-align: left; }}
                th {{ background-color: #F8FAFC; color: #475569; }}
                .highlight-row {{ background-color: #FEF3C7; font-weight: bold; }}
                .section-header {{ font-size: 14px; font-weight: bold; color: #0F172A; border-left: 4px solid #F59E0B; padding-left: 8px; margin-top: 25px; margin-bottom: 10px; }}
                .note-box {{ background-color: #F8FAFC; border: 1px solid #CBD5E1; padding: 12px; font-size: 11px; border-radius: 6px; font-style: italic; }}
                .footer {{ margin-top: 40px; text-align: center; font-size: 10px; color: #94A3B8; border-top: 1px solid #E2E8F0; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="badge-container">
                <span class="badge">İSTESTATE GAYRİMENKUL</span>
                <span class="badge badge-orange">MERİÇ İNŞAAT EMLAK</span>
            </div>
            
            <div class="header">
                <div class="title">ARSA İMAR VE FİZİBİLİTE ANALİZ RAPORU</div>
                <div class="subtitle">Beykoz / {mahalle} Mahallesi - {ada} Ada / {parsel} Parsel</div>
            </div>

            <div class="section-header">📍 1. Taşınmaz ve İmar Durum Bilgileri</div>
            <table>
                <tr><th>Mahalle / Konum</th><td>Beykoz / {mahalle}</td><th>Tapu Niteliği</th><td>{nitelik}</td></tr>
                <tr><th>Ada / Parsel</th><td>{ada} / {parsel}</td><th>İmar Statüsü</th><td>{imar_durumu}</td></tr>
                <tr><th>Brüt Arazi Alanı</th><td>{brut_alan:,.0f} m²</td><th>Terk Oranı</th><td>%{terk_orani:.0f}</td></tr>
                <tr><th>Net Arazi Alanı</th><td>{net_alan:,.0f} m²</td><th>KAKS (Emsal) / TAKS</th><td>{kaks:.2f} / {taks:.2f}</td></tr>
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
            <div class="note-box">
                {ozel_not}
            </div>

            {foto_html}

            <div class="footer">
                Bu rapor Istestate Gayrimenkul ve Meriç İnşaat Emlak bilgi sistemleri tarafından otomatik üretilmiştir.<br>
                Resmi belge niteliği taşımaz, fizibilite ve ön inceleme amaçlıdır.
            </div>
        </body>
        </html>
        """
        
        try:
            # 1. Ana Rapor PDF'ini üret
            main_pdf_bytes = HTML(string=html_content).write_pdf()
            
            # 2. Eğer kullanıcı İmar Durum PDF'i yüklediyse ana raporun sonuna ekle (birleştir)
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
            st.success("✅ Rapor ve İmar Durum Belgesi başarıyla birleştirildi!")
        except Exception as e:
            st.error(f"PDF oluşturulurken bir hata meydana geldi: {e}")

    # Oturum Hafızasında PDF Varsa İndirme Butonunu Göster
    if 'pdf_bytes' in st.session_state:
        st.download_button(
            label="📥 Tam Ekli PDF Raporunu Bilgisayara İndir",
            data=st.session_state['pdf_bytes'],
            file_name=f"Beykoz_{mahalle}_{ada}_{parsel}_Fizibilite_ve_Imar_Raporu.pdf",
            mime="application/pdf"
        )
