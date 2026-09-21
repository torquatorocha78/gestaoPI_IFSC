import io
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import database as db


def _txt(v):
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _money(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def _money_br(v):
    return f"R$ {_money(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def obter_pagamentos(ano=None, modalidade="Todas", status="Todos"):
    try:
        params = "select=*"
        if ano is not None:
            params += f"&ano_pagamento=eq.{int(ano)}"
        data = db._request("GET", f"{db._endpoint('vw_formict_pagamentos')}?{params}&order=data_pagamento.asc",
                           headers=db._headers())
        df = pd.DataFrame(data or [])
    except Exception as exc:
        raise RuntimeError(f"Não foi possível consultar os pagamentos FORMICT: {exc}") from exc

    if modalidade != "Todas" and not df.empty:
        df = df[df["modalidade_pi"].astype(str).str.lower() == modalidade.lower()]
    if status != "Todos" and not df.empty:
        df = df[df["status_pi"].astype(str).str.lower() == status.lower()]
    return df


def _export_df(df):
    if df.empty:
        return pd.DataFrame(columns=[
            "Processo", "Título", "Modalidade", "Gestor", "Campus",
            "Número do Pagamento", "Descrição", "Valor", "Data do Pagamento",
            "Ano do Pagamento", "Status"
        ])
    return pd.DataFrame({
        "Processo": df["numero_patente"],
        "Título": df["titulo"],
        "Modalidade": df["modalidade_pi"],
        "Gestor": df["gestor"],
        "Campus": df["campus"],
        "Número do Pagamento": df["numero_anuidade"],
        "Descrição": df["descricao_pagamento"],
        "Valor": df["valor"],
        "Data do Pagamento": df["data_pagamento"],
        "Ano do Pagamento": df["ano_pagamento"],
        "Status": df["status_pagamento"],
    })


def exportar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _export_df(df).to_excel(writer, index=False, sheet_name="FORMICT_Pagamentos")
    output.seek(0)
    return output.getvalue()


def exportar_pdf(df, ano=None):
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=styles["Title"], alignment=TA_CENTER, fontSize=15)
    pequeno = ParagraphStyle("Pequeno", parent=styles["BodyText"], fontSize=7, leading=9)
    story = [Paragraph("FORMICT – PAGAMENTOS DE PROPRIEDADE INTELECTUAL – IFSC", titulo), Spacer(1, 8)]
    if ano:
        story.append(Paragraph(f"Ano do pagamento: {ano}", styles["Normal"]))
    story.append(Paragraph(f"Quantidade de pagamentos: {len(df)}", styles["Normal"]))
    story.append(Spacer(1, 8))
    dados = _export_df(df)
    if dados.empty:
        story.append(Paragraph("Nenhum pagamento encontrado.", styles["Normal"]))
    else:
        cols=["Processo","Título","Modalidade","Gestor","Número do Pagamento","Valor","Data do Pagamento"]
        table_data=[[Paragraph(f"<b>{c}</b>", pequeno) for c in cols]]
        for _,r in dados.iterrows():
            table_data.append([Paragraph(_txt(r.get(c)).replace("&","&amp;"), pequeno) for c in cols])
        table=Table(table_data, repeatRows=1, colWidths=[90,170,65,80,70,65,75])
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
            ("GRID",(0,0),(-1,-1),0.4,colors.grey),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        story.append(table)
    doc.build(story)
    output.seek(0)
    return output.getvalue()


def render():
    st.title("📑 Relatórios FORMICT")
    st.caption("Relatório baseado exclusivamente nos pagamentos efetivamente registrados nas anuidades.")

    try:
        anos_df = db._request("GET", f"{db._endpoint('vw_formict_pagamentos')}?select=ano_pagamento&order=ano_pagamento.desc",
                              headers=db._headers())
        anos = sorted({int(x["ano_pagamento"]) for x in (anos_df or []) if x.get("ano_pagamento") is not None}, reverse=True)
    except Exception as exc:
        st.error(str(exc))
        return

    c1,c2,c3=st.columns(3)
    with c1:
        ano_label=st.selectbox("Ano do pagamento", ["Todos"]+anos)
    with c2:
        modalidade=st.selectbox("Modalidade", ["Todas","Patente","Software","Desenho Industrial"])
    with c3:
        status=st.selectbox("Status da PI", ["Todos","Ativo","Patente Concedida","Tramitando Normal","Arquivado","Desistência","Indeferimento"])

    ano=None if ano_label=="Todos" else int(ano_label)
    rel=obter_pagamentos(ano, modalidade, status)

    m1,m2,m3=st.columns(3)
    m1.metric("Pagamentos encontrados", len(rel))
    m2.metric("Valor total", _money_br(rel["valor"].sum()) if not rel.empty else "R$ 0,00")
    m3.metric("PIs distintas", rel["numero_patente"].nunique() if not rel.empty else 0)

    st.divider()
    st.subheader("📋 Pagamentos registrados")
    tabela=_export_df(rel)
    st.dataframe(tabela, use_container_width=True, hide_index=True)

    b1,b2=st.columns(2)
    with b1:
        st.download_button("📊 Baixar Excel", exportar_excel(rel), "formict_pagamentos.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with b2:
        st.download_button("📄 Baixar PDF", exportar_pdf(rel, ano), "formict_pagamentos.pdf",
                           "application/pdf", use_container_width=True)
