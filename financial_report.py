"""Exportação de informações financeiras de pagamentos por PI."""
import io
import pandas as pd
import streamlit as st
import database as db

def render():
    st.title("💰 Relatórios de Informações financeiras")
    st.caption("Exporta os registros de pagamento vinculados às PIs, com uma linha por pagamento.")
    try:
        patentes = db.obter_patentes()
        registros = db._request(
            "GET",
            f"{db._endpoint('anuidades')}?select=*&order=data_pagamento.desc",
            headers=db._headers(),
        ) or []
    except Exception as exc:
        st.error(f"Não foi possível consultar os pagamentos no Supabase: {exc}")
        st.info("Execute o SQL de atualização incluído no pacote e verifique as permissões da tabela anuidades.")
        return

    if not registros:
        st.info("Não há registros de pagamento na tabela anuidades.")
        return

    pmap = {}
    if not patentes.empty:
        for _, p in patentes.iterrows():
            pmap[str(p.get("id"))] = p
            pmap[str(p.get("numero_patente"))] = p

    rows = []
    for pg in registros:
        p = pmap.get(str(pg.get("patente_id")))
        if p is None:
            p = pmap.get(str(pg.get("numero_patente")))
        if p is None:
            p = {}
        status = str(pg.get("status") or "").lower()
        modalidade_pagamento = pg.get("descricao_pagamento")
        if not modalidade_pagamento and hasattr(p, "get") and p.get("data_deposito"):
            try:
                cronograma = db._calcular_cronograma(str(p.get("data_deposito")), p.get("modalidade_pi"))
                numero_pg = int(pg.get("numero_anuidade") or 0)
                modalidade_pagamento = next(
                    (item.get("descricao_pagamento") for item in cronograma
                     if int(item.get("numero_anuidade") or 0) == numero_pg),
                    None,
                )
            except Exception:
                modalidade_pagamento = None
        rows.append({
            "Processo": pg.get("numero_patente") or (p.get("numero_patente") if hasattr(p, "get") else ""),
            "GRU": pg.get("gru", ""),
            "Modalidade de pagamento": modalidade_pagamento or pg.get("numero_anuidade", ""),
            "Valor": pg.get("valor_pagamento", ""),
            "Processo SIPAC": pg.get("processo_sipac") or (p.get("processo_sipac", "") if hasattr(p, "get") else ""),
            "Data de pagamento": pg.get("data_pagamento", ""),
            "Servidor responsável": pg.get("servidor_responsavel") or (p.get("servidor_responsavel", "") if hasattr(p, "get") else ""),
            "Modalidade de PI": p.get("modalidade_pi", "") if hasattr(p, "get") else "",
            "Status": pg.get("status", ""),
            "Número do pagamento": pg.get("numero_anuidade", ""),
        })
    df = pd.DataFrame(rows)
    filtro = st.selectbox("Filtrar pagamentos", ["Todos", "Somente pagos", "Não pagar", "Pendentes"])
    if filtro == "Somente pagos":
        df = df[df["Status"].astype(str).str.lower().eq("pago")]
    elif filtro == "Não pagar":
        df = df[df["Status"].astype(str).str.lower().eq("nao_pagar")]
    elif filtro == "Pendentes":
        df = df[~df["Status"].astype(str).str.lower().isin(["pago", "nao_pagar"])]
    st.dataframe(df, use_container_width=True, hide_index=True)
    b = io.BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Informacoes_financeiras")
    st.download_button(
        "⬇️ Exportar Excel — Informações financeiras",
        data=b.getvalue(),
        file_name="Relatorio_Informacoes_Financeiras_IFSC.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
