from pathlib import Path
from datetime import datetime
from fpdf import FPDF
import sys

FACTURA_PATH = Path(__file__).resolve().parent / "factura_demo.txt"
factura_texto = FACTURA_PATH.read_text()

class FacturaPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'RANCHO RAIZ - POSADA', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'CABANA CUMBRE · VALLE DE ENCANTADO · BARRREAL', 0, 1, 'C')
        self.cell(0, 5, 'FACTURA DE PRUEBA - MODO DEMO CRM', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Sistema CRM Rancho Raiz · Modo Demo · Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

print("=== GENERANDO PDF ===")
pdf = FacturaPDF()
pdf.add_page()
pdf.set_font('Arial', '', 10)

for line in factura_texto.split('\n'):
    try:
        pdf.cell(0, 5, line.encode('latin-1', 'replace').decode('latin-1'), 0, 1)
    except:
        pdf.cell(0, 5, line.encode('ascii', 'replace').decode('ascii'), 0, 1)

pdf_path = Path(__file__).resolve().parent / "factura_demo.pdf"
pdf.output(str(pdf_path))
print(f"✅ PDF generado: {pdf_path} ({pdf_path.stat().st_size} bytes)")
