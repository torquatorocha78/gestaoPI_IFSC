import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import database as db
import utils
import ai_analyzer
import report_generator

st.set_page_config(
    page_title="Gestão de Patentes do IFSC",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

db.init_database()

st.markdown("""
<style>
    .status-verde { color: #00CC00; font-weight: bold; }
    .status-amarelo { color: #FFCC00; font-weight: bold; }
    .status-vermelho { color: #FF0000; font-weight: bold; }
    .status-pago { color: #0099FF; font-weight: bold; }
    .title-ifsc { text-align: center; color: #003366; }
</style>
""", unsafe_allow_html=True)

# Logo e Título Principal
st.markdown('<h1 class="title-ifsc">🏛️ Gestão de Patentes do IFSC</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Instituto Federal de Educação, Ciência e Tecnologia de Santa Catarina</p>', unsafe_allow_html=True)
st.divider()

st.sidebar.title("⚙️ Navegação")
pagina = st.sidebar.radio("Selecione uma página:", 
    ["📊 Dashboard", "➕ Adicionar Patente", "📁 Minhas Patentes", "📤 Importar Excel", "🤖 Análise IA", "📄 Gerar Relatórios"])

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
            anuidades = db.obter_anuidades(patente['id'])
            for _, anu in anuidades.iterrows():
                # Verificar se está marcado como "não pagar"
                if anu['status'] == 'nao_pagar':
                    continue
                    
                status = utils.calcular_status_anuidade(
                    anu['data_inicio_ordinario'],
                    anu['data_fim_ordinario'],
                    anu['data_inicio_extraordinario'],
                    anu['data_fim_extraordinario'],
                    anu['data_pagamento']
                )
                if status == 'verde':
                    alertas_verde += 1
                elif status == 'amarelo':
                    alertas_amarelo += 1
                elif status == 'vermelho':
                    alertas_vermelho += 1
                elif status == 'pago':
                    alertas_pago += 1
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📚 Total de Patentes", total_patentes)
        
        with col2:
            st.metric("✅ Normal", alertas_verde, delta="green")
        
        with col3:
            st.metric("⚠️ Atenção", alertas_amarelo, delta="orange")
        
        with col4:
            st.metric("❌ Vencido", alertas_vermelho, delta="red")
        
        with col5:
            st.metric("💰 Pago", alertas_pago, delta="blue")
        
        st.divider()
        
        st.subheader("Resumo de Patentes")
        
        dados_dashboard = []
        for _, patente in df_patentes.iterrows():
            anuidades = db.obter_anuidades(patente['id'])
            
            anuidade_proxima = None
            status_proxima = 'verde'
            
            for _, anu in anuidades.iterrows():
                if anu['status'] == 'nao_pagar':
                    continue
                    
                status = utils.calcular_status_anuidade(
                    anu['data_inicio_ordinario'],
                    anu['data_fim_ordinario'],
                    anu['data_inicio_extraordinario'],
                    anu['data_fim_extraordinario'],
                    anu['data_pagamento']
                )
                if status == 'vermelho':
                    anuidade_proxima = anu['numero_anuidade']
                    status_proxima = 'vermelho'
                    break
                elif status == 'amarelo' and status_proxima != 'vermelho':
                    anuidade_proxima = anu['numero_anuidade']
                    status_proxima = 'amarelo'
                elif anuidade_proxima is None:
                    anuidade_proxima = anu['numero_anuidade']
                    status_proxima = status
            
            emoji = utils.criar_emoji_status(status_proxima)
            
            dados_dashboard.append({
                "ID": patente['id'],
                "Patente": patente['numero_patente'],
                "Deposito": utils.formatar_data(patente['data_deposito']),
                "Status": f"{emoji} {status_proxima.upper()}",
                "Anuidade Prox.": anuidade_proxima,
                "Gestor": patente.get('gestor', 'N/A')
            })
        
        df_dashboard = pd.DataFrame(dados_dashboard)
        
        def colorir_status(row):
            if '❌' in str(row['Status']):
                return ['background-color: #ffcccc'] * len(row)
            elif '⚠️' in str(row['Status']):
                return ['background-color: #ffffcc'] * len(row)
            elif '✅' in str(row['Status']):
                return ['background-color: #ccffcc'] * len(row)
            elif '💰' in str(row['Status']):
                return ['background-color: #ccddff'] * len(row)
            else:
                return [''] * len(row)
        
        st.dataframe(
            df_dashboard.style.apply(colorir_status, axis=1),
            use_container_width=True,
            hide_index=True
        )

elif pagina == "➕ Adicionar Patente":
    st.title("➕ Adicionar Nova Patente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        numero_patente = st.text_input(
            "Numero da Patente",
            placeholder="Ex: BR1020220000001",
            help="Identificador unico da patente"
        )
        
        data_deposito = st.date_input(
            "Data do Deposito",
            help="Data em que a patente foi depositada no INPI"
        )
        
        gestor = st.text_input(
            "Gestor (opcional)",
            placeholder="Ex: IFSC, Empresa XYZ",
            help="Responsável pela gestão da patente"
        )
    
    with col2:
        data_concessao = st.date_input(
            "Data de Concessao (opcional)",
            value=None,
            help="Data em que a patente foi concedida"
        )
        
        titular = st.text_input(
            "Titular/Proprietario (opcional)",
            placeholder="Ex: Empresa XYZ"
        )
        
        status_patente = st.selectbox(
            "Status (opcional)",
            ["Ativo", "Indeferido", "Arquivado", "Desistência"],
            help="Status atual da patente"
        )
    
    descricao = st.text_area(
        "Descricao (opcional)",
        placeholder="Descreva brevemente o objeto da patente",
        height=100
    )
    
    st.divider()
    
    if st.button("✅ Adicionar Patente", use_container_width=True, type="primary"):
        if not numero_patente or not data_deposito:
            st.error("❌ Por favor, preencha pelo menos o Numero da Patente e a Data do Deposito.")
        else:
            data_dep_str = data_deposito.strftime("%Y-%m-%d")
            data_conc_str = data_concessao.strftime("%Y-%m-%d") if data_concessao else None
            
            sucesso, mensagem = db.adicionar_patente(
                numero_patente,
                data_dep_str,
                data_conc_str,
                descricao,
                titular,
                gestor,
                status_patente
            )
            
            if sucesso:
                st.success(f"✅ {mensagem}")
                st.balloons()
                
                st.subheader("📅 Anuidades Calculadas")
                
                df_patentes = db.obter_patentes()
                patente_id = df_patentes[df_patentes['numero_patente'] == numero_patente]['id'].values[0]
                anuidades = db.obter_anuidades(patente_id)
                
                dados_anuidades = []
                for _, anu in anuidades.iterrows():
                    dados_anuidades.append({
                        "Anuidade": anu['numero_anuidade'],
                        "Inicio Ordinario": utils.formatar_data(anu['data_inicio_ordinario']),
                        "Fim Ordinario": utils.formatar_data(anu['data_fim_ordinario']),
                        "Inicio Extraordinario": utils.formatar_data(anu['data_inicio_extraordinario']),
                        "Fim Extraordinario": utils.formatar_data(anu['data_fim_extraordinario'])
                    })
                
                df_anuidades = pd.DataFrame(dados_anuidades)
                st.dataframe(df_anuidades, use_container_width=True, hide_index=True)
            else:
                st.error(f"❌ {mensagem}")

elif pagina == "📁 Minhas Patentes":
    st.title("📁 Minhas Patentes")
    
    df_patentes = db.obter_patentes()
    
    if len(df_patentes) == 0:
        st.info("📭 Nenhuma patente cadastrada. Va em 'Adicionar Patente' para começar.")
    else:
        patentes_list = df_patentes['numero_patente'].tolist()
        patente_selecionada = st.selectbox("Selecione uma patente:", patentes_list)
        
        patente_dados = df_patentes[df_patentes['numero_patente'] == patente_selecionada].iloc[0]
        patente_id = patente_dados['id']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📝 Numero", patente_selecionada)
        with col2:
            st.metric("📅 Deposito", utils.formatar_data(patente_dados['data_deposito']))
        with col3:
            st.metric("✅ Concessao", utils.formatar_data(patente_dados['data_concessao']) if patente_dados['data_concessao'] else "Pendente")
        with col4:
            st.metric("👤 Titular", patente_dados['titular'] if patente_dados['titular'] else "N/A")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔑 Gestor", patente_dados.get('gestor', 'N/A'))
        with col2:
            st.metric("📊 Status", patente_dados.get('status', 'Ativo'))
        
        if patente_dados['descricao']:
            st.info(f"**Descricao:** {patente_dados['descricao']}")
        
        st.divider()
        
        st.subheader("📊 Detalhamento de Anuidades")
        
        anuidades = db.obter_anuidades(patente_id)
        
        dados_tabela = []
        for _, anu in anuidades.iterrows():
            if anu['status'] == 'nao_pagar':
                emoji = '⛔'
                status_display = 'NÃO PAGAR'
                dias_restantes = '-'
            else:
                status = utils.calcular_status_anuidade(
                    anu['data_inicio_ordinario'],
                    anu['data_fim_ordinario'],
                    anu['data_inicio_extraordinario'],
                    anu['data_fim_extraordinario'],
                    anu['data_pagamento']
                )
                
                dias_restantes = utils.obter_dias_restantes(
                    anu['data_fim_ordinario'],
                    anu['data_pagamento']
                )
                
                emoji = utils.criar_emoji_status(status)
                status_display = status.upper()
            
            dados_tabela.append({
                "Anuidade": anu['numero_anuidade'],
                "Inicio Ordinario": utils.formatar_data(anu['data_inicio_ordinario']),
                "Fim Ordinario": utils.formatar_data(anu['data_fim_ordinario']),
                "Dias Restantes": dias_restantes if dias_restantes != '-' else ("Pago" if anu['data_pagamento'] else '-'),
                "Status": f"{emoji} {status_display}",
                "Data Pagamento": utils.formatar_data(anu['data_pagamento']) if anu['data_pagamento'] else "-"
            })
        
        df_tabela = pd.DataFrame(dados_tabela)
        
        def colorir_linhas(row):
            if '⛔' in str(row['Status']):
                return ['background-color: #e6e6e6'] * len(row)
            elif '❌' in str(row['Status']):
                return ['background-color: #ffcccc'] * len(row)
            elif '⚠️' in str(row['Status']):
                return ['background-color: #ffffcc'] * len(row)
            elif '✅' in str(row['Status']):
                return ['background-color: #ccffcc'] * len(row)
            elif '💰' in str(row['Status']):
                return ['background-color: #ccddff'] * len(row)
            else:
                return [''] * len(row)
        
        st.dataframe(
            df_tabela.style.apply(colorir_linhas, axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        
        st.subheader("💰 Registrar Pagamento / Marcar Anuidade")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            num_anuidade = st.selectbox(
                "Selecione a anuidade",
                anuidades['numero_anuidade'].tolist(),
                key="select_anuidade"
            )
        
        with col2:
            data_pagamento_input = st.date_input(
                "Data do Pagamento",
                key="data_pag"
            )
        
        with col3:
            if st.button("✅ Registrar Pagamento", use_container_width=True):
                db.atualizar_status_anuidade(
                    patente_id,
                    num_anuidade,
                    "pago",
                    data_pagamento_input.strftime("%Y-%m-%d")
                )
                st.success("✅ Pagamento registrado com sucesso!")
                st.rerun()
        
        with col4:
            if st.button("🚫 Marcar Não Pagar", use_container_width=True):
                db.atualizar_status_anuidade(
                    patente_id,
                    num_anuidade,
                    "nao_pagar"
                )
                st.success("✅ Anuidade marcada como não pagar!")
                st.rerun()
        
        st.divider()
        
        if st.button("🗑️ Deletar Patente", use_container_width=True, type="secondary"):
            if st.checkbox("Tenho certeza que desejo deletar esta patente?"):
                db.deletar_patente(patente_id)
                st.success("✅ Patente deletada com sucesso!")
                st.rerun()

elif pagina == "📤 Importar Excel":
    st.title("📤 Importar Patentes do Excel")
    
    st.info("""
    📋 O arquivo Excel deve conter as seguintes colunas:
    - **numero_patente** (obrigatorio)
    - **data_deposito** (obrigatorio, formato: DD/MM/YYYY ou YYYY-MM-DD)
    - **data_concessao** (opcional)
    - **descricao** (opcional)
    - **titular** (opcional)
    - **gestor** (opcional) - Se diferente de IFSC, marcar anuidades como não pagar
    - **status** (opcional) - Se contiver: indeferido, arquivado ou desistência, marcar anuidades como não pagar
    """)
    
    arquivo_excel = st.file_uploader(
        "Selecione um arquivo Excel (.xlsx)",
        type="xlsx"
    )
    
    if arquivo_excel:
        if st.button("📥 Importar Dados", use_container_width=True, type="primary"):
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
                dados_resultados.append({
                    "Patente": patente,
                    "Status": "✅ Sucesso" if sucesso else "❌ Erro",
                    "Mensagem": mensagem
                })
            
            df_resultados = pd.DataFrame(dados_resultados)
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            if sucesso_count > 0:
                st.success(f"🎉 {sucesso_count} patente(s) importada(s) com sucesso!")
                st.balloons()

elif pagina == "🤖 Análise IA":
    st.title("🤖 Análise Inteligente de Patentes")
    st.markdown("""Utilize a IA para fazer perguntas e análises sobre suas patentes.""")
    
    df_patentes = db.obter_patentes()
    
    if len(df_patentes) == 0:
        st.warning("⚠️ Nenhuma patente cadastrada. Primeiro, adicione algumas patentes.")
    else:
        st.divider()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            pergunta = st.text_input(
                "Faça uma pergunta sobre suas patentes:",
                placeholder="Ex: Quantas patentes foram concedidas? Quais estão vencidas? Qual é o status das patentes do IFSC?"
            )
        
        with col2:
            analizar = st.button("🔍 Analisar", use_container_width=True)
        
        if analizar and pergunta:
            with st.spinner("Analisando dados..."):
                resposta = ai_analyzer.analisar_pergunta(df_patentes, pergunta)
                st.markdown("### 📋 Resposta:")
                st.info(resposta)
        
        st.divider()
        
        st.subheader("📊 Análises Rápidas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📈 Estatísticas Gerais", use_container_width=True):
                stats = ai_analyzer.gerar_estatisticas(df_patentes)
                st.markdown(stats)
        
        with col2:
            if st.button("🎯 Patentes por Gestor", use_container_width=True):
                gestores = ai_analyzer.patentes_por_gestor(df_patentes)
                st.markdown(gestores)
        
        with col3:
            if st.button("⚠️ Alertas Urgentes", use_container_width=True):
                alertas = ai_analyzer.gerar_alertas(df_patentes)
                st.markdown(alertas)

elif pagina == "📄 Gerar Relatórios":
    st.title("📄 Geração de Relatórios em PDF")
    
    df_patentes = db.obter_patentes()
    
    if len(df_patentes) == 0:
        st.warning("⚠️ Nenhuma patente cadastrada. Primeiro, adicione algumas patentes.")
    else:
        st.subheader("Escolha o tipo de relatório:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Relatório Completo", use_container_width=True):
                with st.spinner("Gerando relatório completo..."):
                    pdf = report_generator.gerar_relatorio_completo(df_patentes)
                    st.download_button(
                        "📥 Baixar Relatório Completo",
                        data=pdf,
                        file_name="relatorio_completo.pdf",
                        mime="application/pdf"
                    )
        
        with col2:
            if st.button("📊 Relatório de Anuidades", use_container_width=True):
                with st.spinner("Gerando relatório de anuidades..."):
                    pdf = report_generator.gerar_relatorio_anuidades(df_patentes)
                    st.download_button(
                        "📥 Baixar Relatório Anuidades",
                        data=pdf,
                        file_name="relatorio_anuidades.pdf",
                        mime="application/pdf"
                    )
        
        with col3:
            if st.button("⚠️ Relatório de Alertas", use_container_width=True):
                with st.spinner("Gerando relatório de alertas..."):
                    pdf = report_generator.gerar_relatorio_alertas(df_patentes)
                    st.download_button(
                        "📥 Baixar Relatório Alertas",
                        data=pdf,
                        file_name="relatorio_alertas.pdf",
                        mime="application/pdf"
                    )
        
        st.divider()
        
        st.subheader("📊 Exportação de Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Exportar para Excel", use_container_width=True):
                excel_buffer = report_generator.exportar_para_excel(df_patentes)
                st.download_button(
                    "📥 Baixar Excel",
                    data=excel_buffer,
                    file_name="patentes_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            if st.button("📤 Exportar para CSV", use_container_width=True):
                csv_buffer = report_generator.exportar_para_csv(df_patentes)
                st.download_button(
                    "📥 Baixar CSV",
                    data=csv_buffer,
                    file_name="patentes_export.csv",
                    mime="text/csv"
                )
        
