import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# ---------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------
st.set_page_config(page_title="Gestão de Patentes IFSC")
st.title("Gestão de Patentes – IFSC")

# ---------------------------------
# UPLOAD
# ---------------------------------
uploaded = st.file_uploader(
    "Upload da planilha base",
    type=["xlsx", "csv"]
)

# ---------------------------------
# FUNÇÃO PDF
# ---------------------------------
def gerar_pdf(df):
    buffer = BytesIO()
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(buffer)
    elementos = [
        Paragraph("Relatório de Patentes", styles["Title"])
    ]

    tabela = Table([df.columns.tolist()] + df.values.tolist())
    elementos.append(tabela)

    doc.build(elementos)
    buffer.seek(0)
    return buffer

# ---------------------------------
# PROCESSAMENTO
# ---------------------------------
if uploaded is not None:

    # Leitura da planilha
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    # Regra da anuidade

    
    gestores_ifsc = [
        "ifsc",
        "instituto federal de santa catarina",
        "instituto federal de educação, ciência e tecnologia de santa catarina",
        "instituto federal de santa catarina (br/sc)"
    ]

    df["pagar_anuidade"] = df["gestor"].apply(
        lambda x: "SIM"
        if str(x).strip().lower() in gestores_ifsc
        else "NÃO"
    )

    # Exibição
    st.subheader("Tabela processada")
    st.dataframe(df)

    # Download CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar CSV",
        csv,
        "relatorio_patentes.csv",
        "text/csv"
    )

    # PDF
    if st.button("Gerar PDF"):
        df_r = df.copy()
        pdf_buffer = gerar_pdf(df_r)

        st.download_button(
            "Baixar PDF",
            pdf_buffer,
            file_name="relatorio_patentes.pdf",
            mime="application/pdf"
        )

else:
    st.info("Faça o upload de uma planilha para iniciar.")
