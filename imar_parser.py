import os
import re
import pdfplumber
import pandas as pd


class ImarFizibiliteParser:

    def __init__(self, kaks=0.30):
        self.kaks = kaks

    @staticmethod
    def parse_float(val_str):
        if not val_str:
            return 0.0
        clean_str = re.sub(r"[^\d,\.]", "", str(val_str))
        if not clean_str:
            return 0.0
        clean_str = clean_str.replace(".", "").replace(",", ".")
        try:
            return float(clean_str)
        except ValueError:
            return 0.0

    def extract_from_pdf(self, pdf_path):
        parsel_list = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                ada_match = re.search(r"Ada\s*[:|]?\s*(\d+)", text)
                parsel_match = re.search(r"Parsel\s*[:|]?\s*(\d+)", text)
                alan_match = re.search(
                    r"Alan\s*\*?\s*[:|]?\s*([\d\.,]+)\s*m²", text
                )

                if ada_match and parsel_match:
                    ada = ada_match.group(1)
                    parsel = int(parsel_match.group(1))
                    brut_alan = (
                        self.parse_float(alan_match.group(1))
                        if alan_match
                        else 0.0
                    )

                    konut_alan = 0.0
                    terk_alan = 0.0

                    konut_match = re.search(
                        r"KONUT ALANI.*?(?:%[\d\.,]+\s*-\s*|%[\d\.,]+\s+|)([\d\.,]+)\s*m²",
                        text,
                        re.DOTALL,
                    )
                    if konut_match:
                        konut_alan = self.parse_float(konut_match.group(1))

                    park_match = re.search(
                        r"PARK.*?(?:%[\d\.,]+\s*-\s*|%[\d\.,]+\s+|)([\d\.,]+)\s*m²",
                        text,
                        re.DOTALL,
                    )
                    if park_match:
                        terk_alan += self.parse_float(park_match.group(1))

                    yol_match = re.search(
                        r"YOL.*?(?:%[\d\.,]+\s*-\s*|%[\d\.,]+\s+|)([\d\.,]+)\s*m²",
                        text,
                        re.DOTALL,
                    )
                    if yol_match:
                        terk_alan += self.parse_float(yol_match.group(1))

                    if brut_alan > 0 and konut_alan > 0 and terk_alan == 0:
                        terk_alan = max(0.0, brut_alan - konut_alan)

                    parsel_list.append(
                        {
                            "Ada": ada,
                            "Parsel": parsel,
                            "Brut_Alan": brut_alan,
                            "Net_Konut_Alan": konut_alan,
                            "Terk_Alan": terk_alan,
                        }
                    )

        return (
            pd.DataFrame(parsel_list).drop_duplicates(subset=["Ada", "Parsel"])
            if parsel_list
            else pd.DataFrame()
        )

    def generate_report(self, df_parsels):
        if df_parsels.empty:
            return pd.DataFrame()

        report_rows = []
        grouped = df_parsels.groupby("Ada")

        for ada, group in grouped:
            group_sorted = group.sort_values("Parsel")
            parseller = group_sorted["Parsel"].astype(str).tolist()

            ada_parsel_str = (
                f"Ada: {ada} | Parsel: {parseller[0]}"
                if len(parseller) == 1
                else f"Ada: {ada} | Parseller: {', '.join(parseller)}"
            )

            toplam_brut = group_sorted["Brut_Alan"].sum()
            toplam_terk = group_sorted["Terk_Alan"].sum()
            toplam_net_konut = group_sorted["Net_Konut_Alan"].sum()

            if toplam_net_konut == 0 and toplam_brut > 0:
                toplam_net_konut = toplam_brut - toplam_terk

            terk_orani = (
                (toplam_terk / toplam_brut * 100) if toplam_brut > 0 else 0.0
            )
            net_emsal_insaat = toplam_net_konut * self.kaks

            report_rows.append(
                {
                    "Ada / Parsel Formatı": ada_parsel_str,
                    "Brüt Arazi Alanı (m²)": round(toplam_brut, 2),
                    "Terk Alanı (Park/Yol) (m²)": round(toplam_terk, 2),
                    "Ağırlıklı Terk Oranı (%)": f"%{round(terk_orani, 2)}",
                    "Net Arazi Alanı (Konut) (m²)": round(toplam_net_konut, 2),
                    "Net Emsal İnşaat Alanı (m²)": round(
                        net_emsal_insaat, 2
                    ),
                }
            )

        return pd.DataFrame(report_rows)
