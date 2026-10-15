"""Relatório FORMICT refeito: campos alinhados à planilha-modelo recebida."""
import io
import pandas as pd
import streamlit as st
import database as db

COLUNAS = [
    ("Processo", "numero_patente"),
    ("Título", "titulo"),
    ("Tipo", "modalidade_pi"),
    ("Status", "status"),
    ("Sigilo", "sigilo"),
    ("Setor Econômico", "cnae_secao"),
    ("Subclassificação CNAE 2.0 IBGE", "cnae_subclassificacao"),
    ("Território", "territorio"),
    ("TLR", "trl"),
    ("Com Cotitularidade", "cotitularidade"),
    ("Custo de Registro", "custo_registro"),
    ("Data de depósito", "data_deposito"),
    ("Cotitulares", "cotitulares"),
    ("Inventores", "inventores"),
]

def _text(v):
    if v is None or pd.isna(v):
        return ""
    return str(v).strip()

def _export_frame(df):
    out = pd.DataFrame()
    for label, field in COLUNAS:
        out[label] = df[field] if field in df.columns else ""
    return out

def _date_iso(value):
    if not _text(value):
        return None
    try:
        return pd.to_datetime(value, dayfirst=True, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        return None

def render():
    st.title("📑 Relatórios FORMICT")
    st.caption("Módulo reconstruído conforme as colunas da planilha FORMICT_Pagamentos fornecida. A chave de identificação é Processo + Data de depósito.")
    df = db.obter_patentes()
    if df.empty:
        st.info("Não há PIs cadastradas no banco.")
        return

    st.subheader("Exportar dados FORMICT")
    out = _export_frame(df)
    st.dataframe(out, use_container_width=True, hide_index=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="FORMICT_Pagamentos")
    st.download_button(
        "⬇️ Exportar Excel FORMICT",
        data=buffer.getvalue(),
        file_name="Relatorio_FORMICT_IFSC.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    st.divider()
    st.subheader("Importar/atualizar dados FORMICT por planilha")
    st.caption("A planilha precisa conter as colunas Processo e Data de depósito. Campos vazios não apagam os valores existentes.")
    uploaded = st.file_uploader("Planilha Excel FORMICT", type=["xlsx", "xls"], key="formict_import_novo")
    if uploaded is not None and st.button("Importar dados FORMICT", key="formict_import_btn"):
        try:
            sheet = pd.read_excel(uploaded)
            normalized = {str(c).strip().casefold(): c for c in sheet.columns}
            process_col = normalized.get("processo")
            deposit_col = normalized.get("data de depósito") or normalized.get("data de deposito")
            if not process_col or not deposit_col:
                st.error("A planilha precisa conter as colunas 'Processo' e 'Data de depósito'.")
                return
            inverse = {label.casefold(): field for label, field in COLUNAS}
            current = db.obter_patentes()
            success, errors = 0, []
            for ix, row in sheet.iterrows():
                process = _text(row.get(process_col))
                deposit = _date_iso(row.get(deposit_col))
                if not process or not deposit:
                    continue
                match = current[
                    (current["numero_patente"].astype(str).str.strip() == process) &
                    (pd.to_datetime(current["data_deposito"], errors="coerce").dt.strftime("%Y-%m-%d") == deposit)
                ]
                if match.empty:
                    errors.append(f"Linha {ix + 2}: processo/data de depósito não localizado ({process}).")
                    continue
                record = match.iloc[0]
                updates = {}
                for label, field in COLUNAS:
                    source = normalized.get(label.casefold())
                    if source is None:
                        continue
                    value = row.get(source)
                    if pd.isna(value) or _text(value) == "":
                        continue
                    if field == "data_deposito":
                        updates["data_dep"] = _date_iso(value)
                    elif field == "numero_patente":
                        updates["numero"] = process
                    elif field == "custo_registro":
                        try: updates[field] = float(value)
                        except Exception: updates[field] = None
                    else:
                        updates[field] = value
                ok, msg = db.atualizar_patente(record["id"], **updates)
                if ok: success += 1
                else: errors.append(f"Linha {ix + 2}: {msg}")
            st.success(f"Importação concluída: {success} PI(s) atualizada(s).")
            if errors:
                st.warning("Ocorrências:")
                for error in errors[:50]:
                    st.write(f"- {error}")
        except Exception as exc:
            st.error(f"Não foi possível importar a planilha: {exc}")
