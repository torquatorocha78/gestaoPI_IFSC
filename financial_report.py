"""Relatórios financeiros filtráveis e exportáveis em Excel e ODT."""
import io

import pandas as pd
import streamlit as st
import database as db


def _odt_bytes(df: pd.DataFrame) -> bytes:
    """Cria documento ODT sem depender de LibreOffice instalado no servidor."""
    from odf.opendocument import OpenDocumentText
    from odf.style import Style, TextProperties, TableColumnProperties
    from odf.table import Table, TableColumn, TableRow, TableCell
    from odf.text import P

    doc = OpenDocumentText()
    title_style = Style(name="ReportTitle", family="paragraph")
    title_style.addElement(TextProperties(fontsize="16pt", fontweight="bold"))
    doc.styles.addElement(title_style)
    doc.text.addElement(P(text="Relatório de Informações Financeiras", stylename=title_style))
    doc.text.addElement(P(text=f"Registros: {len(df)}"))

    table = Table(name="Pagamentos")
    for _ in df.columns:
        table.addElement(TableColumn())
    header = TableRow()
    for col in df.columns:
        cell = TableCell()
        cell.addElement(P(text=str(col)))
        header.addElement(cell)
    table.addElement(header)
    for _, record in df.iterrows():
        row = TableRow()
        for value in record:
            cell = TableCell()
            cell.addElement(P(text="" if pd.isna(value) else str(value)))
            row.addElement(cell)
        table.addElement(row)
    doc.text.addElement(table)
    output = io.BytesIO()
    doc.write(output)
    return output.getvalue()


def render():
    st.title("💰 Relatórios de Informações financeiras")
    st.caption("Consulte pagamentos importados e baixas de anuidades; filtre por processo ou ano e exporte o resultado.")
    try:
        patentes = db.obter_patentes()
        importados = db._request(
            "GET", f"{db._endpoint('pagamentos_inpi')}?select=*&order=ano_pagamento.desc,data_pagamento.desc",
            headers=db._headers(),
        ) or []
        anuidades = db._request(
            "GET", f"{db._endpoint('anuidades')}?select=*&order=data_pagamento.desc",
            headers=db._headers(),
        ) or []
    except Exception as exc:
        st.error(f"Não foi possível consultar os pagamentos no Supabase: {exc}")
        st.info("Confirme que a migração de pagamentos INPI foi executada e que as tabelas estão acessíveis.")
        return

    mapa = {}
    if not patentes.empty:
        for _, patente in patentes.iterrows():
            mapa[str(patente.get("numero_patente"))] = patente

    rows = []
    gru_vistas = set()
    for pg in importados:
        processo = str(pg.get("numero_patente") or "")
        patente = mapa.get(processo, {})
        gru = str(pg.get("gru") or "")
        if gru:
            gru_vistas.add(gru)
        rows.append({
            "Processo": processo,
            "GRU": gru,
            "Tipo de pagamento": pg.get("tipo_pagamento") or "",
            "Valor (R$)": pg.get("valor"),
            "Processo SIPAC": pg.get("processo_sipac") or "",
            "Data": pg.get("data_pagamento") or "",
            "Ano": pg.get("ano_pagamento") or (str(pg.get("data_pagamento", ""))[:4] or ""),
            "Servidor responsável": pg.get("servidor_responsavel") or "",
            "Modalidade PI": patente.get("modalidade_pi", "") if hasattr(patente, "get") else "",
            "Origem": "Planilha INPI",
        })

    # Inclui baixas manuais não presentes na planilha, sem repetir GRUs já listadas.
    for pg in anuidades:
        gru = str(pg.get("gru") or "")
        if gru and gru in gru_vistas:
            continue
        processo = str(pg.get("numero_patente") or pg.get("patente_id") or "")
        patente = mapa.get(processo, {})
        data = pg.get("data_pagamento") or ""
        rows.append({
            "Processo": processo, "GRU": gru,
            "Tipo de pagamento": pg.get("descricao_pagamento") or pg.get("numero_anuidade") or "Anuidade",
            "Valor (R$)": pg.get("valor") or pg.get("valor_pagamento"),
            "Processo SIPAC": pg.get("processo_sipac") or "",
            "Data": data, "Ano": str(data)[:4] if data else "",
            "Servidor responsável": pg.get("servidor_responsavel") or "",
            "Modalidade PI": patente.get("modalidade_pi", "") if hasattr(patente, "get") else "",
            "Origem": "Baixa de anuidade",
        })

    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Não há pagamentos para exibir.")
        return
    df["Ano"] = df["Ano"].astype(str).replace({"nan": "", "None": ""})
    anos = sorted((a for a in df["Ano"].unique() if a), reverse=True)
    processos = sorted((p for p in df["Processo"].unique() if p))
    f1, f2 = st.columns(2)
    with f1:
        ano = st.selectbox("Ano do pagamento", ["Todos"] + anos)
    with f2:
        processo = st.selectbox("Patente / número do processo", ["Todas"] + processos)
    filtrado = df.copy()
    if ano != "Todos":
        filtrado = filtrado[filtrado["Ano"] == ano]
    if processo != "Todas":
        filtrado = filtrado[filtrado["Processo"] == processo]
    st.caption(f"{len(filtrado)} pagamento(s) correspondem aos filtros.")
    st.dataframe(filtrado, use_container_width=True, hide_index=True)

    excel = io.BytesIO()
    with pd.ExcelWriter(excel, engine="openpyxl") as writer:
        filtrado.to_excel(writer, index=False, sheet_name="Pagamentos")
    nome = f"Pagamentos_{ano if ano != 'Todos' else 'todos_anos'}"
    b1, b2 = st.columns(2)
    with b1:
        st.download_button(
            "⬇️ Exportar Excel", data=excel.getvalue(), file_name=f"{nome}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with b2:
        st.download_button(
            "⬇️ Exportar ODT", data=_odt_bytes(filtrado), file_name=f"{nome}.odt",
            mime="application/vnd.oasis.opendocument.text", use_container_width=True,
        )
