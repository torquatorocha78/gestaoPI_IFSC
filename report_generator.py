from reportlab.pdfgen import canvas
from io import BytesIO
import pandas as pd

def _pdf_bytes_from_text(title, lines):
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica", 12)
    y = 800
    c.drawString(50, y, title)
    y -= 30
    for line in lines:
        c.drawString(50, y, str(line))
        y -= 20
        if y < 50:
            c.showPage()
            y = 800
    c.save()
    buf.seek(0)
    return buf.read()

def gerar_relatorio_completo(df_patentes):
    lines = []
    for _, r in df_patentes.iterrows():
        lines.append(f"{r.get('numero_patente')} - {r.get('titular')} - {r.get('gestor')}")
    return _pdf_bytes_from_text("Relatório Completo de Patentes", lines)

def gerar_relatorio_anuidades(df_patentes):
    lines = ["Relatório de Anuidades"]
    for _, r in df_patentes.iterrows():
        lines.append(f"{r.get('numero_patente')}")
    return _pdf_bytes_from_text("Relatório de Anuidades", lines)

def gerar_relatorio_alertas(df_patentes):
    lines = ["Relatório de Alertas"]
    for _, r in df_patentes.iterrows():
        lines.append(f"{r.get('numero_patente')}")
    return _pdf_bytes_from_text("Relatório de Alertas", lines)

def exportar_para_excel(df_patentes):
    buf = BytesIO()
    # Se df_patentes já é DataFrame, usar diretamente; app passa df_patentes
    df = df_patentes.copy() if hasattr(df_patentes, "copy") else pd.DataFrame(df_patentes)
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="patentes")
    buf.seek(0)
    return buf.getvalue()

def exportar_para_csv(df_patentes):
    df = df_patentes.copy() if hasattr(df_patentes, "copy") else pd.DataFrame(df_patentes)
    return df.to_csv(index=False).encode("utf-8")
