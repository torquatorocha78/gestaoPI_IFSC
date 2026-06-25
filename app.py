
import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path
from io import BytesIO

st.set_page_config(page_title="Gestão de Patentes IFSC")

st.title("Gestão de Patentes – IFSC")

uploaded = st.file_uploader("Upload da planilha base", type=["xlsx","csv"])

def gerar_pdf(df):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(buffer)
    elementos = [Paragraph("Relatório de Patentes", styles["Title"])]
    elementos.append(Table([df.columns.tolist()] + df.values.tolist()))
    doc.build(elementos)
    buffer.seek(0)
    return buffer

if uploaded:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    df["pagar_anuidade"] = df["gestor"].apply(
        lambda x: "NÃO" if str(x).strip().lower() not in ["ifsc", "instituto federal de santa catarina"] else "SIM"
    )

    st.subheader("Tabela processada")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV", csv, "relatorio_patentes.csv", "text/csv")

    pdf_path = Path("relatorio_patentes.pdf")
    gerar_pdf(df, pdf_path)
    with open(pdf_path, "rb") as f:
        st.download_button("Baixar PDF", f, "relatorio_patentes.pdf", "application/pdf")
