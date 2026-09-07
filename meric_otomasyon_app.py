import io
from imar_parser import ImarFizibiliteParser
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="İmar Durum Fizibilite Analizi",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 İmar Durumu PDF Analiz ve Fizibilite")
st.markdown(
    "PDF imar durum raporlarını yükleyin; **Ada/Parsel birleştirmeleri**, **Terk (Park/Yol) oranları** ve **Net Emsal İnşaat Alanı** otomatik hesaplansın."
)

# Yan Panel - Parametreler
st.sidebar.header("Hesaplama Parametreleri")
kaks_input = st.sidebar.number_input(
    "KAKS / Emsal Oranı",
    min_value=0.01,
    max_value=10.0,
    value=0.30,
    step=0.05,
)

# Dosya Yükleme
uploaded_files = st.file_uploader(
    "İmar Durum PDF Dosyası / Dosyalarını Seçin",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    parser_engine = ImarFizibiliteParser(kaks=kaks_input)
    all_raw_dfs = []

    with st.spinner("PDF dosyaları işleniyor ve analiz ediliyor..."):
        for pdf_file in uploaded_files:
            # Streamlit uploaded_file nesnesini doğrudan pdfplumber'a paslıyoruz
            df_single = parser_engine.extract_from_pdf(pdf_file)
            if not df_single.empty:
                all_raw_dfs.append(df_single)

    if all_raw_dfs:
        # Tüm dosyaları birleştir ve tekrarları sil
        combined_raw_df = pd.concat(all_raw_dfs, ignore_index=True)
        combined_raw_df = combined_raw_df.drop_duplicates(
            subset=["Ada", "Parsel"]
        )

        # Fizibilite Raporunu Oluştur
        df_report = parser_engine.generate_report(combined_raw_df)

        st.subheader("📊 Fizibilite Analiz Sonuçları")

        # Özet Metrik Kartları
        col1, col2, col3, col4 = st.columns(4)
        toplam_brut = combined_raw_df["Brut_Alan"].sum()
        toplam_terk = combined_raw_df["Terk_Alan"].sum()
        toplam_net = combined_raw_df["Net_Konut_Alan"].sum()
        toplam_emsal = toplam_net * kaks_input
        terk_orani = (
            (toplam_terk / toplam_brut * 100) if toplam_brut > 0 else 0
        )

        col1.metric("Brüt Arazi Alanı", f"{toplam_brut:,.2f} m²")
        col2.metric(
            "Toplam Terk (Park/Yol)",
            f"{toplam_terk:,.2f} m²",
            f"%{terk_orani:.2f} Terk",
        )
        col3.metric("Net Konut Alanı", f"{toplam_net:,.2f} m²")
        col4.metric(
            "Net Emsal İnşaat Alanı",
            f"{toplam_emsal:,.2f} m²",
            f"KAKS: {kaks_input}",
        )

        st.divider()

        # Ana Tablo Gösterimi
        st.dataframe(df_report, use_container_width=True)

        # Excel İndirme Butonu
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_report.to_excel(writer, index=False, sheet_name="Fizibilite")

        st.download_button(
            label="📥 Sonuçları Excel Olarak İndir",
            data=buffer.getvalue(),
            file_name="Imar_Fizibilite_Raporu.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.error(
            "Yüklenen PDF(ler) içerisinden geçerli Ada/Parsel ve alan verisi çekilemedi."
        )
