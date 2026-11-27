import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 8)
        self.set_text_color(100, 100, 100)
        self.cell(self.epw, 5, 'AV3 - Computação em Nuvem | Grupo 3: Auditoria ODS 5 & ODS 18', border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
        self.line(self.l_margin, 14, self.l_margin + self.epw, 14)
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(self.epw, 10, f'Página {self.page_no()}/{{nb}}', align='C')

pdf = PDFReport(orientation='P', unit='mm', format='A4')
pdf.set_margins(12, 16, 12)
pdf.set_auto_page_break(auto=True, margin=15)

# Load Windows TrueType fonts with full UTF-8 Unicode support
pdf.add_font("Arial", "", "C:/Windows/Fonts/arial.ttf")
pdf.add_font("Arial", "B", "C:/Windows/Fonts/arialbd.ttf")
pdf.add_font("Arial", "I", "C:/Windows/Fonts/ariali.ttf")

pdf.add_page()

with open('docs/guia_apresentacao_av3.md', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
epw = pdf.epw

def clean_emojis(txt):
    # Remove emoji characters that font doesn't have
    return re.sub(r'[\U00010000-\U0010ffff]', '', txt).replace('🔬', '').replace('🎓', '').replace('📌', '').replace('🛠️', '').replace('🏗️', '').replace('📊', '').replace('🎯', '').replace('📁', '').replace('⚙️', '').replace('🏛️', '').replace('💻', '').replace('☁️', '').replace('➡️', '->')

for line in lines:
    line_clean = clean_emojis(line.strip())
    if not line_clean:
        pdf.ln(2)
        continue

    # Ignore code blocks for clean summary text
    if line_clean.startswith('```'):
        continue

    # Headings
    if line_clean.startswith('# '):
        pdf.set_font('Arial', 'B', 15)
        pdf.set_text_color(27, 77, 62)
        title = line_clean[2:].strip()
        pdf.multi_cell(epw, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
    elif line_clean.startswith('## '):
        pdf.set_font('Arial', 'B', 12)
        pdf.set_text_color(46, 125, 50)
        subtitle = line_clean[3:].strip()
        pdf.multi_cell(epw, 6.5, subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
    elif line_clean.startswith('### '):
        pdf.set_font('Arial', 'B', 10.5)
        pdf.set_text_color(45, 55, 72)
        pdf.multi_cell(epw, 5.5, line_clean[4:].strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
    elif line_clean.startswith('---'):
        pdf.set_draw_color(220, 220, 220)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + epw, pdf.get_y())
        pdf.ln(2)
    elif line_clean.startswith('> '):
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(34, 84, 61)
        pdf.set_fill_color(240, 255, 244)
        quote_text = line_clean[2:].replace('**', '').replace('*', '').strip()
        pdf.multi_cell(epw, 5, f"  \"{quote_text}\"", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
    elif line_clean.startswith('|') and line_clean.endswith('|'):
        if '---' in line_clean:
            continue
        cells = [c.strip().replace('**', '').replace('`', '') for c in line_clean.split('|')[1:-1]]
        pdf.set_font('Arial', 'B' if 'Camada' in cells[0] or 'Critério' in cells[0] or 'P1' in cells[0] else '', 8)
        pdf.set_text_color(30, 30, 30)
        row_str = " | ".join(cells)
        pdf.multi_cell(epw, 4.5, row_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    elif line_clean.startswith('* ') or line_clean.startswith('- '):
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(30, 30, 30)
        item_text = line_clean[2:].replace('**', '').replace('`', '').strip()
        pdf.multi_cell(epw, 4.8, f"  - {item_text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    else:
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(30, 30, 30)
        p_text = line_clean.replace('**', '').replace('`', '').strip()
        pdf.multi_cell(epw, 4.8, p_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

pdf.output('docs/guia_apresentacao_av3.pdf')
print('SUCCESS: PDF generated at docs/guia_apresentacao_av3.pdf')
