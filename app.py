# app.py
import streamlit as st
import pandas as pd
from datetime import date
import database as db

st.set_page_config(
    page_title="Gestão de Patentes - IFSC",
    page_icon="📄",
    layout="wide"
)

db.init_database()

st.sidebar.title("Menu")
pagina = st.sidebar.radio(
    "Selecione",
    ["Dashboard", "Cadastrar Patente", "Minhas Patentes"]
)

if pagina == "Dashboard":
    st.title("📊 Dashboard")

    df_patentes = db.obter_patentes()

    if df_patentes.empty:
        st.info("Nenhuma patente cadastrada")
    else:
        st.metric("Total de Patentes", len(df_patentes))

        dados = []
        for _, p in df_patentes.iterrows():
            anu = db.obter_anuidades(p["id"])
            pendentes = anu[anu["status"] == "PENDENTE"]
            dados.append({
                "Patente": p["numero_patente"],
                "Pendentes": len(pendentes),
                "Pagas": len(anu) - len(pendentes)
            })

        st.dataframe(pd.DataFrame(dados), use_container_width=True)

elif pagina == "Cadastrar Patente":
    st.title("➕ Cadastrar Patente")

    with st.form("form_patente"):
        numero = st.text_input("Número da patente")
        data_dep = st.date_input("Data de depósito")
        data_conc = st.date_input("Data de concessão", value=None)
        descricao = st.text_area("Descrição")
        titular = st.text_input("Titular")

        salvar = st.form_submit_button("Salvar")

    if salvar:
        ok, msg = db.adicionar_patente(
            numero,
            data_dep.strftime("%Y-%m-%d"),
            data_conc.strftime("%Y-%m-%d") if data_conc else None,
            descricao,
            titular
        )
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

elif pagina == "Minhas Patentes":
    st.title("📁 Minhas Patentes")

    df_patentes = db.obter_patentes()

    if df_patentes.empty:
        st.info("Nenhuma patente cadastrada")
    else:
        patente_sel = st.selectbox(
            "Selecione a patente",
            df_patentes["numero_patente"].tolist()
        )

        patente = df_patentes[df_patentes["numero_patente"] == patente_sel].iloc[0]
        st.write("**Titular:**", patente["titular"])
        st.write("**Depósito:**", patente["data_deposito"])

        anuidades = db.obter_anuidades(patente["id"])
        st.subheader("Anuidades")

        st.dataframe(
            anuidades[[
                "numero_anuidade",
                "data_inicio_ordinario",
                "data_fim_ordinario",
                "data_fim_extraordinario",
                "status",
                "data_pagamento"
            ]],
            use_container_width=True
        )

        pendentes = anuidades[anuidades["status"] == "PENDENTE"]
        if not pendentes.empty:
            st.subheader("Registrar pagamento")
            num = st.selectbox(
                "Anuidade",
                pendentes["numero_anuidade"].tolist()
            )
            data_pag = st.date_input("Data do pagamento", value=date.today())

            if st.button("Registrar"):
                db.atualizar_status_anuidade(
                    patente["id"],
                    num,
                    data_pag.strftime("%Y-%m-%d")
                )
                st.success("Pagamento registrado")
                st.rerun()
