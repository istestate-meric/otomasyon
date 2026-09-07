import argparse
import sys
from imar_parser import ImarFizibiliteParser


def main():
    parser = argparse.ArgumentParser(
        description="İmar Durum PDF Fizibilite Analizi"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        required=True,
        help="İşlenecek PDF dosyasının yolu",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="Fizibilite_Raporu.xlsx",
        help="Çıktı Excel dosya adı",
    )
    parser.add_argument(
        "--kaks", type=float, default=0.30, help="KAKS / Emsal oranı"
    )

    args = parser.parse_args()

    engine = ImarFizibiliteParser(kaks=args.kaks)
    print(f"[+] PDF İşleniyor: {args.pdf}")

    df_raw = engine.extract_from_pdf(args.pdf)
    if df_raw.empty:
        print("[-] Veri okunamadı veya geçerli ada/parsel bulunamadı.")
        sys.exit(1)

    df_report = engine.generate_report(df_raw)
    df_report.to_excel(args.output, index=False)

    print(f"[+] İşlem tamamlandı. Çıktı oluşturuldu: {args.output}")
    print("\n--- RAPOR ÖZETİ ---")
    print(df_report.to_string(index=False))


if __name__ == "__main__":
    main()
