from pathlib import Path
from datetime import datetime
from fpdf import FPDF
import sys

BASE_DIR = Path(__file__).resolve().parent

def generar_factura(txt_path: Path | None = None) -> Path:
    if txt_path is None:
        txt_path = BASE_DIR / "factura_alejandro_beltran.txt"
    with open(txt_path, 'r', encoding='utf-8') as f:
        contenido = f.read()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, 'RANCHO RAIZ - POSADA', 0, 1, 'C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 5, 'CABAÑA CUMBRE · VALLE DE ENCANTADO · BARRREAL', 0, 1, 'C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, 'FACTURA DE PRUEBA - MODO DEMO CRM', 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    for line in contenido.splitlines():
        pdf.cell(0, 5, line.encode('latin-1', 'replace').decode('latin-1'), 0, 1)
    pdf.set_y(-15)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, f'Sistema CRM Rancho Raiz · Modo Demo · Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

    pdf_path = BASE_DIR / "factura_alejandro_beltran.pdf"
    pdf.output(str(pdf_path))
    return pdf_path

def main():
    print("=== GENERANDO PDF ===")
    pdf_path = generar_factura()
    print(f"✅ PDF generado: {pdf_path} ({pdf_path.stat().st_size} bytes)")

if __name__ == "__main__":
    main()