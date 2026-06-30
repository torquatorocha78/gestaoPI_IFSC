import pandas as pdimport streamlit as stimport pandas as pdfrom datetime import date

import database as dbimport utilsfrom io import BytesIO

=====================================================

CONFIGURAÇÃO DA PÁGINA

=====================================================

st.set_page_config(page_title="Sistema de Gestao de Patentes",page_icon="📋",page_title="Gestão de Patentes - IFSC",page_icon="📄",layout="wide",initial_sidebar_state="expanded",)

db.init_database()

st.markdown("""

<style>
    .status-verde { color: #00CC00; font-weight: bold; }
    .status-amarelo { color: #FFCC00; font-weight: bold; }
    .status-vermelho { color: #FF0000; font-weight: bold; }
    .status-pago { color: #0099FF; font-weight: bold; }
    .status-futuro { color: #FFCC00; font-weight: bold; }
</style>

""",unsafe_allow_html=True,)

st.sidebar.title("⚙️ Navegacao")pagina = st.sidebar.radio("Selecione uma página:",["📊 Dashboard", "➕ Adicionar Patente", "📁 Minhas Patentes", "📤 Importar Excel", "📁Relatórios"],)

=====================================================

FUNÇÕES AUXILIARES (APP)

=====================================================

def colorir_linha_por_status(row):if "❌" in str(row["Status"]):return ["background-color: #ffcccc"] * len(row)if "⚠️" in str(row["Status"]):return ["background-color: #ffffcc"] * len(row)if "✅" in str(row["Status"]):return ["background-color: #ccffcc"] * len(row)if "💰" in str(row["Status"]):return ["background-color: #ccddff"] * len(row)return [""] * len(row)def emoji_status(status):if status == "PENDENTE":return "🟢"if status == "PAGA":return "✅"return "⚪"

if pagina == "📊 Dashboard":st.title("📊 Dashboard de Patentes")

=====================================================

SIDEBAR

=====================================================

df_patentes = db.obter_patentes()

st.sidebar.title("📌 Menu")

if len(df_patentes) == 0:
    st.info("📭 Nenhuma patente cadastrada ainda. Adicione uma patente para começar!")
else:
    total_patentes = len(df_patentes)

pagina = st.sidebar.radio("Selecione",["Dashboard","Cadastrar Patente","Minhas Patentes","Importar Excel",],)

    alertas_verde = 0
    alertas_amarelo = 0
    alertas_vermelho = 0
    alertas_pago = 0

=====================================================

DASHBOARD

=====================================================

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
                "Status": f"{emoji} {utils.formatar_status(status_proxima)}",
                "Anuidade Prox.": anuidade_proxima,
            }
        )

if pagina == "Dashboard":st.title("📊 Dashboard Geral")

    df_dashboard = pd.DataFrame(dados_dashboard)
    st.dataframe(
        df_dashboard.style.apply(colorir_linha_por_status, axis=1),
        width="stretch",
        hide_index=True,
    )
df_patentes = db.obter_patentes()

elif pagina == "➕ Adicionar Patente":st.title("➕ Adicionar Nova Patente")total_patentes = len(df_patentes)total_pendentes = 0total_pagas = 0

col1, col2 = st.columns(2)
for _, patente in df_patentes.iterrows():
    anuidades = db.obter_anuidades(patente["id"])

with col1:
    numero_patente = st.text_input(
        "Numero da Patente",
        placeholder="Ex: BR1020220000001",
        help="Identificador unico da patente",
    )
    total_pendentes += len(anuidades[anuidades["status"] == "PENDENTE"])
    total_pagas += len(anuidades[anuidades["status"] == "PAGA"])

    data_deposito = st.date_input(
        "Data do Deposito",
        value=None,
        help="Data em que a patente foi depositada no INPI",
    )
col1, col2, col3 = st.columns(3)

with col2:
    data_concessao = st.date_input(
        "Data de Concessao (opcional)",
        value=None,
        help="Data em que a patente foi concedida",
    )
col1.metric("Total de Patentes", total_patentes)
col2.metric("Anuidades Pendentes", total_pendentes)
col3.metric("Anuidades Pagas", total_pagas)

    titular = st.text_input(
        "Titular/Proprietario (opcional)",
        placeholder="Ex: Empresa XYZ",
    )

=====================================================

CADASTRAR PATENTE

=====================================================

descricao = st.text_area(
    "Descricao (opcional)",
    placeholder="Descreva brevemente o objeto da patente",
    height=100,
)

elif pagina == "Cadastrar Patente":st.title("➕ Cadastrar Nova Patente")

st.divider()
with st.form("form_patente"):
    numero = st.text_input("Número da Patente")
    data_dep = st.date_input("Data de Depósito")
    data_conc = st.date_input("Data de Concessão", value=None)
    descricao = st.text_area("Descrição")
    titular = st.text_input("Titular")

if st.button("✅ Adicionar Patente", width="stretch", type="primary"):
    if not numero_patente or not data_deposito:
        st.error("❌ Por favor, preencha pelo menos o Numero da Patente e a Data do Deposito.")
    else:
        data_dep_str = data_deposito.strftime("%Y-%m-%d")
        data_conc_str = data_concessao.strftime("%Y-%m-%d") if data_concessao else None
    submitted = st.form_submit_button("Salvar")

        sucesso, mensagem = db.adicionar_patente(
            numero_patente.strip(),
            data_dep_str,
            data_conc_str,
    if submitted:
        sucesso, msg = db.adicionar_patente(
            numero,
            data_dep,
            data_conc,
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
            st.success(msg)
        else:
            st.error(f"❌ {mensagem}")
            st.error(msg)

=====================================================

MINHAS PATENTES

=====================================================

elif pagina == "📁 Minhas Patentes":elif pagina == "Minhas Patentes":st.title("📁 Minhas Patentes")

df_patentes = db.obter_patentes()

if len(df_patentes) == 0:
    st.info("📭 Nenhuma patente cadastrada. Vá em 'Adicionar Patente' para começar.")
if df_patentes.empty:
    st.info("Nenhuma patente cadastrada.")
else:
    patentes_list = df_patentes["numero_patente"].tolist()
    patente_selecionada = st.selectbox("Selecione uma patente:", patentes_list)

    patente_dados = df_patentes[df_patentes["numero_patente"] == patente_selecionada].iloc[0]
    patente_id = patente_dados["id"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Número", patente_selecionada)
    with col2:
        st.metric("📅 Depósito", utils.formatar_data(patente_dados["data_deposito"]))
    with col3:
        concessao = (
            utils.formatar_data(patente_dados["data_concessao"])
            if patente_dados["data_concessao"]
            else "Pendente"
        )
        st.metric("✅ Concessão", concessao)
    with col4:
        st.metric("👤 Titular", patente_dados["titular"] or "N/A")

    st.divider()
    st.subheader("📊 Detalhamento de Anuidades")

    anuidades = db.obter_anuidades(patente_id)

    dados_tabela = []
    for _, anu in anuidades.iterrows():
        status = utils.calcular_status_anuidade(
            anu["data_inicio_ordinario"],
            anu["data_fim_ordinario"],
            anu["data_inicio_extraordinario"],
            anu["data_fim_extraordinario"],
            anu["data_pagamento"],
        )

        dias_restantes = utils.obter_dias_restantes(
            anu["data_fim_ordinario"],
            anu["data_pagamento"],
        )

        emoji = utils.criar_emoji_status(status)

        dados_tabela.append({
            "Anuidade": anu["numero_anuidade"],
            "Início Ordinário": utils.formatar_data(anu["data_inicio_ordinario"]),
            "Fim Ordinário": utils.formatar_data(anu["data_fim_ordinario"]),
            "Dias Restantes": str(dias_restantes) if not anu["data_pagamento"] else "Pago",
            "Status": f"{emoji} {utils.formatar_status(status)}",
            "Data Pagamento": utils.formatar_data(anu["data_pagamento"]) if anu["data_pagamento"] else "-",
        })

    df_tabela = pd.DataFrame(dados_tabela)

    st.dataframe(
        df_tabela.style.apply(colorir_linha_por_status, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.subheader("💰 Registrar Pagamento")

    col1, col2, col3 = st.columns(3)
    with col1:
        num_anuidade = st.selectbox(
            "Selecione a anuidade",
            anuidades["numero_anuidade"].tolist(),
        )
    with col2:
        data_pagamento_input = st.date_input("Data do Pagamento")
    with col3:
        st.write("")
        st.write("")
        if st.button("✅ Registrar Pagamento", use_container_width=True):
            db.atualizar_status_anuidade(
                patente_id,
                num_anuidade,
                "pago",
                data_pagamento_input.strftime("%Y-%m-%d"),
            )
            st.success("✅ Pagamento registrado com sucesso!")
            st.rerun()

    # ================== BLOCO DE EDIÇÃO (AGORA NO LUGAR CERTO) ==================
    st.divider()
    st.subheader("✏️ Editar dados da patente")

    with st.form("form_editar_patente"):
        nova_data_concessao = st.date_input(
            "Data de Concessão",
            value=(
                pd.to_datetime(patente_dados["data_concessao"]).date()
                if patente_dados["data_concessao"]
                else None
            )
        )

        novo_titular = st.text_input(
            "Titular",
            value=patente_dados["titular"] or ""
        )

        nova_descricao = st.text_area(
            "Descrição",
            value=patente_dados["descricao"] or "",
            height=120
        )
    for _, patente in df_patentes.iterrows():
        with st.expander(f"📄 {patente['numero_patente']}"):
            st.write(f"**Titular:** {patente['titular']}")
            st.write(f"**Data de Depósito:** {patente['data_deposito'].date()}")
            st.write(f"**Descrição:** {patente['descricao']}")

            anuidades = db.obter_anuidades(patente["id"])

            # 🔹 Resumo: mostrar apenas pendentes
            pendentes = anuidades[anuidades["status"] == "PENDENTE"]

            st.subheader("Resumo")
            if pendentes.empty:
                st.success("Todas as anuidades estão pagas ✅")
            else:
                proxima = pendentes.iloc[0]
                st.warning(
                    f"Próxima anuidade pendente: "
                    f"{proxima['numero_anuidade']}ª"
                )

        salvar = st.form_submit_button("💾 Salvar alterações")
            st.subheader("Anuidades")

    if salvar:
        db.atualizar_patente(
            patente_id,
            nova_data_concessao.strftime("%Y-%m-%d") if nova_data_concessao else None,
            nova_descricao.strip(),
            novo_titular.strip(),
        )
        st.success("✅ Dados da patente atualizados com sucesso!")
        st.rerun()

elif pagina == "📤 Importar Excel":st.title("📤 Importar Patentes do Excel")

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
            tabela = []
            for _, a in anuidades.iterrows():
                tabela.append(
                    {
                        "Anuidade": a["numero_anuidade"],
                        "Início Ordinário": a["data_inicio_ordinario"].date(),
                        "Fim Ordinário": a["data_fim_ordinario"].date(),
                        "Fim Extraordinário": a["data_fim_extraordinario"].date(),
                        "Status": f"{emoji_status(a['status'])} {a['status']}",
                    }
                )

arquivo_excel = st.file_uploader(
    "Selecione um arquivo Excel (.xlsx)",
    type="xlsx",
            st.dataframe(pd.DataFrame(tabela), use_container_width=True)

            # 🔹 Registrar pagamento manual
            st.subheader("Registrar Pagamento")

            pendentes_nums = pendentes["numero_anuidade"].tolist()

            if pendentes_nums:
                with st.form(f"pagamento_{patente['id']}"):
                    num_anuidade = st.selectbox(
                        "Anuidade",
                        pendentes_nums,
                    )
                    data_pag = st.date_input(
                        "Data do Pagamento",
                        value=date.today(),
                    )

                    pagar = st.form_submit_button("Registrar")

                    if pagar:
                        db.atualizar_status_anuidade(
                            patente["id"],
                            num_anuidade,
                            "pago",
                            data_pag,
                        )
                        st.success("Pagamento registrado com sucesso!")
                        st.rerun()
            else:
                st.info("Nenhuma anuidade pendente.")

=====================================================

IMPORTAR EXCEL

=====================================================

elif pagina == "Importar Excel":st.title("📥 Importar Patentes via Excel")

arquivo = st.file_uploader(
    "Selecione o arquivo Excel",
    type=["xlsx"],
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

elif pagina == "📁Relatórios":st.title("📁 Exportar para Excel")

# =============================
# 1. Montar DataFrame base
# =============================
df_patentes = db.obter_patentes()

if df_patentes.empty:
    st.warning("Nenhuma patente cadastrada para gerar relatório.")
    st.stop()
if arquivo:
    resultados = db.importar_excel(arquivo)

dados_relatorio = []
    st.subheader("Resultado da Importação")

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

        dados_relatorio.append({
            "Número da Patente": patente["numero_patente"],
            "Titular": patente["titular"],
            "Data Depósito": utils.formatar_data(patente["data_deposito"]),
            "Data Concessão": utils.formatar_data(patente["data_concessao"]) if patente["data_concessao"] else "",
            "Anuidade": anu["numero_anuidade"],
            "Início Ordinário": utils.formatar_data(anu["data_inicio_ordinario"]),
            "Fim Ordinário": utils.formatar_data(anu["data_fim_ordinario"]),
            "Início Extraordinário": utils.formatar_data(anu["data_inicio_extraordinario"]),
            "Fim Extraordinário": utils.formatar_data(anu["data_fim_extraordinario"]),
            "Status": utils.formatar_status(status),
            "Data Pagamento": utils.formatar_data(anu["data_pagamento"]) if anu["data_pagamento"] else ""
        })

df = pd.DataFrame(dados_relatorio)

# =============================
# 2. Configuração do relatório
# =============================
st.subheader("Configurar relatório")

colunas_disponiveis = df.columns.tolist()
colunas_selecionadas = st.multiselect(
    "Selecione as colunas para exportar",
    colunas_disponiveis,
    default=colunas_disponiveis
)

df_filtrado = df.copy()

# =============================
# 3. Filtros dinâmicos
# =============================
with st.expander("Filtros"):
    for col in colunas_selecionadas:
        valores = df[col].dropna().unique().tolist()
        if 1 < len(valores) <= 50:
            selecionados = st.multiselect(
                f"Filtrar {col}",
                valores,
                default=valores
            )
            df_filtrado = df_filtrado[df_filtrado[col].isin(selecionados)]

df_final = df_filtrado[colunas_selecionadas]

# =============================
# 4. Pré-visualização
# =============================
st.subheader("Pré-visualização")
st.dataframe(df_final, use_container_width=True)

# =============================
# 5. Exportação Excel
# =============================
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_final.to_excel(writer, index=False, sheet_name="Relatório")

buffer.seek(0)

st.download_button(
    "📥 Baixar relatório em Excel",
    buffer,
    file_name="relatorio_patentes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
    df_res = pd.DataFrame(
        resultados,
        columns=["Número da Patente", "Sucesso", "Mensagem"],
    )

    st.dataframe(df_res, use_container_width=True)
