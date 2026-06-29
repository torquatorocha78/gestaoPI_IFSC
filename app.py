import pandas as pd
import streamlit as st

import database as db
import utils


st.set_page_config(
    page_title="Sistema de Gestao de Patentes",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_database()

st.markdown(
    """
<style>
    .status-verde { color: #00CC00; font-weight: bold; }
    .status-amarelo { color: #FFCC00; font-weight: bold; }
    .status-vermelho { color: #FF0000; font-weight: bold; }
    .status-pago { color: #0099FF; font-weight: bold; }
    .status-futuro { color: #FFCC00; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

st.sidebar.title("⚙️ Navegacao")
pagina = st.sidebar.radio(
    "Selecione uma página:",
    ["📊 Dashboard", "➕ Adicionar Patente", "📁 Minhas Patentes", "📤 Importar Excel", "📁Relatórios"],
)


def colorir_linha_por_status(row):
    if "❌" in str(row["Status"]):
        return ["background-color: #ffcccc"] * len(row)
    if "⚠️" in str(row["Status"]):
        return ["background-color: #ffffcc"] * len(row)
    if "✅" in str(row["Status"]):
        return ["background-color: #ccffcc"] * len(row)
    if "💰" in str(row["Status"]):
        return ["background-color: #ccddff"] * len(row)
    return [""] * len(row)


if pagina == "📊 Dashboard":
    st.title("📊 Dashboard de Patentes")

    df_patentes = db.obter_patentes()

    if len(df_patentes) == 0:
        st.info("📭 Nenhuma patente cadastrada ainda. Adicione uma patente para começar!")
    else:
        total_patentes = len(df_patentes)

        alertas_verde = 0
        alertas_amarelo = 0
        alertas_vermelho = 0
        alertas_pago = 0

        for _, patente in df_patentes.iterrows():
            anuidades = db.obter_anuidades(patente["id"])
            for _, anu in anuidades.iterrows():
                status = utils.calcular_status_anuidade(
                    anu["data_inicio_ordinario"],
                    anu["data_fim_ordinario"],
                    anu["data_inicio_extraordinario"],
                    anu["data_fim_extraordinario"],
                    anu["data_pagamento"],
                )
                if status == "verde":
                    alertas_verde += 1
                elif status in ("amarelo", "futuro"):
                    alertas_amarelo += 1
                elif status == "vermelho":
                    alertas_vermelho += 1
                elif status == "pago":
                    alertas_pago += 1

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("📚 Total de Patentes", total_patentes)
        with col2:
            st.metric("✅ Normal", alertas_verde)
        with col3:
            st.metric("⚠️ Atencao/Futuro", alertas_amarelo)
        with col4:
            st.metric("❌ Vencido", alertas_vermelho)
        with col5:
            st.metric("💰 Pago", alertas_pago)

        st.divider()
        st.subheader("Resumo de Patentes")

        dados_dashboard = []
        for _, patente in df_patentes.iterrows():
            anuidades = db.obter_anuidades(patente["id"])

            anuidade_proxima = None
            status_proxima = "verde"

            for _, anu in anuidades.iterrows():
                status = utils.calcular_status_anuidade(
                    anu["data_inicio_ordinario"],
                    anu["data_fim_ordinario"],
                    anu["data_inicio_extraordinario"],
                    anu["data_fim_extraordinario"],
                    anu["data_pagamento"],
                )
                if status == "vermelho":
                    anuidade_proxima = anu["numero_anuidade"]
                    status_proxima = "vermelho"
                    break
                if status == "amarelo" and status_proxima != "vermelho":
                    anuidade_proxima = anu["numero_anuidade"]
                    status_proxima = "amarelo"
                elif anuidade_proxima is None:
                    anuidade_proxima = anu["numero_anuidade"]
                    status_proxima = status

            emoji = utils.criar_emoji_status(status_proxima)

            dados_dashboard.append(
                {
                    "ID": patente["id"],
                    "Patente": patente["numero_patente"],
                    "Deposito": utils.formatar_data(patente["data_deposito"]),
                    "Status": f"{emoji} {status_proxima}",
                    "Anuidade Prox.": anuidade_proxima,
                }
            )

        df_dashboard = pd.DataFrame(dados_dashboard)
        st.dataframe(
            df_dashboard.style.apply(colorir_linha_por_status, axis=1),
            width="stretch",
            hide_index=True,
        )

elif pagina == "➕ Adicionar Patente":
    st.title("➕ Adicionar Nova Patente")

    col1, col2 = st.columns(2)

    with col1:
        numero_patente = st.text_input(
            "Numero da Patente",
            placeholder="Ex: BR1020220000001",
            help="Identificador unico da patente",
        )

        data_deposito = st.date_input(
            "Data do Deposito",
            value=None,
            help="Data em que a patente foi depositada no INPI",
        )

    with col2:
        data_concessao = st.date_input(
            "Data de Concessao (opcional)",
            value=None,
            help="Data em que a patente foi concedida",
        )

        titular = st.text_input(
            "Titular/Proprietario (opcional)",
            placeholder="Ex: Empresa XYZ",
        )

    descricao = st.text_area(
        "Descricao (opcional)",
        placeholder="Descreva brevemente o objeto da patente",
        height=100,
    )

    st.divider()

    if st.button("✅ Adicionar Patente", width="stretch", type="primary"):
        if not numero_patente or not data_deposito:
            st.error("❌ Por favor, preencha pelo menos o Numero da Patente e a Data do Deposito.")
        else:
            data_dep_str = data_deposito.strftime("%Y-%m-%d")
            data_conc_str = data_concessao.strftime("%Y-%m-%d") if data_concessao else None

            sucesso, mensagem = db.adicionar_patente(
                numero_patente.strip(),
                data_dep_str,
                data_conc_str,
                descricao,
                titular,
            )

            if sucesso:
                st.success(f"✅ {mensagem}")
                st.balloons()

                st.subheader("📅 Anuidades Calculadas")

                df_patentes = db.obter_patentes()
                patente_id = df_patentes[df_patentes["numero_patente"] == numero_patente.strip()]["id"].values[0]
                anuidades = db.obter_anuidades(patente_id)

                dados_anuidades = []
                for _, anu in anuidades.iterrows():
                    dados_anuidades.append(
                        {
                            "Anuidade": anu["numero_anuidade"],
                            "Inicio Ordinario": utils.formatar_data(anu["data_inicio_ordinario"]),
                            "Fim Ordinario": utils.formatar_data(anu["data_fim_ordinario"]),
                            "Inicio Extraordinario": utils.formatar_data(anu["data_inicio_extraordinario"]),
                            "Fim Extraordinario": utils.formatar_data(anu["data_fim_extraordinario"]),
                        }
                    )

                st.dataframe(pd.DataFrame(dados_anuidades), width="stretch", hide_index=True)
            else:
                st.error(f"❌ {mensagem}")

elif pagina == "📂 Minhas Patentes":
    st.title("📂 Minhas Patentes")

    if df.empty:
        st.warning("Nenhuma planilha carregada.")
    else:
        st.subheader("Selecionar patente")

        # Coluna identificadora principal
        coluna_id = "titulo" if "titulo" in df.columns else df.columns[0]

        patente_selecionada = st.selectbox(
            "Escolha a patente para editar",
            df[coluna_id].astype(str)
        )

        # Índice da patente selecionada
        idx = df[df[coluna_id].astype(str) == patente_selecionada].index[0]

        st.divider()
        st.subheader("Editar dados da patente")

        # Formulário dinâmico para TODAS as colunas
        with st.form("form_edicao_patente"):
            novos_valores = {}

            for col in df.columns:
                valor_atual = df.loc[idx, col]

                # Campos dinâmicos por tipo
                if pd.api.types.is_numeric_dtype(df[col]):
                    novos_valores[col] = st.number_input(
                        col,
                        value=float(valor_atual) if pd.notna(valor_atual) else 0.0
                    )

                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    novos_valores[col] = st.date_input(
                        col,
                        value=valor_atual
                        if pd.notna(valor_atual)
                        else pd.to_datetime("today")
                    )

                else:
                    novos_valores[col] = st.text_input(
                        col,
                        value="" if pd.isna(valor_atual) else str(valor_atual)
                    )

            salvar = st.form_submit_button("💾 Salvar alterações")

        # Aplicar alterações
        if salvar:
            for col, valor in novos_valores.items():
                df.loc[idx, col] = valor

            # Regra automática da anuidade (mantida)
            gestores_ifsc = [
                "ifsc",
                "instituto federal de santa catarina",
                "instituto federal de educação, ciência e tecnologia de santa catarina",
                "instituto federal de santa catarina (br/sc)"
            ]

            if "gestor" in df.columns:
                gestor = str(df.loc[idx, "gestor"]).strip().lower()
                df.loc[idx, "pagar_anuidade"] = (
                    "SIM" if gestor in gestores_ifsc else "NÃO"
                )

            st.success("Patente atualizada com sucesso.")

        st.divider()

        # Exportação do banco atualizado
        st.subheader("Exportar banco atualizado")

        col1, col2 = st.columns(2)

        with col1:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Baixar CSV atualizado",
                csv,
                "base_patentes_atualizada.csv",
                "text/csv"
            )

        with col2:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Patentes")

            buffer.seek(0)
            st.download_button(
                "📥 Baixar Excel atualizado",
                buffer,
                "base_patentes_atualizada.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
elif pagina == "📤 Importar Excel":
    st.title("📤 Importar Patentes do Excel")

    st.info(
        """
    📋 O arquivo Excel deve conter as seguintes colunas:
    - **numero_patente** (obrigatorio)
    - **data_deposito** (obrigatorio, formato: DD/MM/YYYY ou YYYY-MM-DD)
    - **data_concessao** (opcional)
    - **descricao** (opcional)
    - **titular** (opcional)
    """
    )

    arquivo_excel = st.file_uploader(
        "Selecione um arquivo Excel (.xlsx)",
        type="xlsx",
    )

    if arquivo_excel:
        if st.button("📥 Importar Dados", width="stretch", type="primary"):
            with st.spinner("Importando dados..."):
                resultados = db.importar_excel(arquivo_excel)

            st.subheader("📊 Resultado da Importacao")

            sucesso_count = sum(1 for _, sucesso, _ in resultados if sucesso)
            erro_count = len(resultados) - sucesso_count

            col1, col2 = st.columns(2)
            with col1:
                st.metric("✅ Importadas com Sucesso", sucesso_count)
            with col2:
                st.metric("❌ Erros", erro_count)

            dados_resultados = []
            for patente, sucesso, mensagem in resultados:
                dados_resultados.append(
                    {
                        "Patente": patente,
                        "Status": "✅ Sucesso" if sucesso else "❌ Erro",
                        "Mensagem": mensagem,
                    }
                )

            st.dataframe(pd.DataFrame(dados_resultados), width="stretch", hide_index=True)

            if sucesso_count > 0:
                st.success(f"🎉 {sucesso_count} patente(s) importada(s) com sucesso!")
                st.balloons()
