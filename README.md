🏛️ Gestão de Patentes do IFSC
Sistema Integrado de Gestão de Propriedade Intelectual

O SIGPI-IF é um sistema desenvolvido em Python para apoiar a gestão da propriedade intelectual do Instituto Federal de Educação, Ciência e Tecnologia de Santa Catarina. A plataforma permite o gerenciamento integrado de ativos de propriedade intelectual, oferecendo ferramentas para acompanhamento de patentes, controle de prazos e anuidades, monitoramento de processos e geração de indicadores estratégicos.

✨ Funcionalidades
📊 Dashboard
Visão geral de todas as patentes
Métricas de status (Normal, Atenção, Vencido, Pago)
Filtros por gestor e status
Indicadores de alertas urgentes
➕ Adicionar Patente
Cadastro manual de novas patentes
Campos: Número, Data de Depósito, Concessão, Titular, Descrição
Gestor e Status configuráveis
Cálculo automático de 20 anuidades
📁 Minhas Patentes
Detalhamento completo de cada patente
Visualização de todas as anuidades (20 anos)
Registro de pagamentos
Marcação de anuidades como "Não Pagar" (para patentes com gestor diferente de IFSC ou status de indeferimento/arquivamento/desistência)
Exclusão de patentes
📤 Importar Excel
Importação em massa de patentes
Suporte para colunas: numero_patente, data_deposito, data_concessao, descricao, titular, gestor, status
Validação automática de dados
Processamento inteligente:
Se Gestor ≠ IFSC → Marcar anuidades como "não pagar"
Se Status = Indeferido/Arquivado/Desistência → Marcar anuidades como "não pagar"
🤖 Análise IA
Menu inteligente com análise automática de patentes
Responde perguntas como:
"Quantas patentes foram concedidas?"
"Quais patentes estão vencidas?"
"Quantas patentes do IFSC?"
"Qual o status geral?"
Análises rápidas pré-configuradas
Estatísticas por gestor
Alertas urgentes
📄 Gerar Relatórios
Relatório Completo: Todas as patentes e anuidades em PDF
Relatório de Anuidades: Foco em datas e status de pagamento
Relatório de Alertas: Anuidades vencidas e em atenção
Exportação Excel: Dados completos em planilha
Exportação CSV: Para integração com outros sistemas
🚀 Instalação
Pré-requisitos
Python 3.8+
pip (gerenciador de pacotes Python)
Passos de Instalação
# 1. Clone o repositório
git clone https://github.com/torquatorocha78/patent-management-system.git
cd patent-management-system

# 2. Crie um ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
streamlit run app.py
A aplicação abrirá em http://localhost:8501

📋 Estrutura de Arquivos
patent-management-system/
├── app.py                 # Aplicação principal Streamlit
├── database.py            # Gerenciamento de banco de dados SQLite
├── utils.py               # Funções utilitárias (cálculos de status, datas)
├── ai_analyzer.py         # Módulo de análise inteligente com IA
├── report_generator.py    # Geração de relatórios em PDF e exportação
├── requirements.txt       # Dependências do projeto
└── README.md             # Esta documentação
🗄️ Banco de Dados
O sistema utiliza SQLite com as seguintes tabelas:

Tabela: patentes
id (INTEGER PRIMARY KEY)
numero_patente (TEXT UNIQUE)
data_deposito (DATE)
data_concessao (DATE)
descricao (TEXT)
titular (TEXT)
gestor (TEXT) - Novo: Responsável pela patente
status (TEXT) - Novo: Ativo, Indeferido, Arquivado, Desistência
data_criacao (TIMESTAMP)
Tabela: anuidades
id (INTEGER PRIMARY KEY)
patente_id (INTEGER FK)
numero_anuidade (INTEGER)
data_inicio_ordinario (DATE)
data_fim_ordinario (DATE)
data_inicio_extraordinario (DATE)
data_fim_extraordinario (DATE)
status (TEXT) - Melhorado: 'pendente', 'pago', 'nao_pagar' (novo)
data_pagamento (DATE)
📊 Fluxo de Anuidades
Cada patente tem 20 anuidades automaticamente calculadas:

Período Ordinário: 3 meses para pagar (do 3º ano em diante)
Período Extraordinário: 6 meses extras para pagar com multa
Status:
🟢 Verde: Dentro do período ordinário
🟡 Amarelo: Últimos 30 dias do período ordinário
🔴 Vermelho: Período extraordinário ou vencido
💰 Pago: Pagamento registrado
⛔ Não Pagar: Marcado para não pagamento (gestor ≠ IFSC ou status especial)
🤖 Funcionalidades de IA
O módulo ai_analyzer.py fornece:

Análise de Perguntas Naturais: Entende perguntas em linguagem natural
Estatísticas Automáticas: Gera resumos de dados
Agrupamento por Gestor: Análise por responsável
Alertas Inteligentes: Identifica anuidades urgentes
Exemplos de Perguntas
"Quantas patentes foram concedidas?"
"Quais patentes estão vencidas?"
"Qual o status das patentes do IFSC?"
"Quantas desistências temos?"
📄 Relatórios PDF
Relatório Completo
Resumo geral de patentes
Tabela de todas as patentes com dados básicos
Detalhamento de todas as 20 anuidades por patente
Relatório de Anuidades
Tabela consolidada de todas as anuidades
Status e datas de vencimento
Dias restantes para pagamento
Relatório de Alertas
Anuidades vencidas em destaque (VERMELHO)
Anuidades com atenção (AMARELO)
Resumo de alertas urgentes
📥 Importação de Excel
Formato Esperado
Numero da Patente | Data Depósito | Data Concessão | Titular       | Gestor  | Status
BR1020220000001   | 2022-01-15    | 2024-06-20     | Instituto XYZ | IFSC    | Ativo
BR1020220000002   | 2022-02-10    |                | Empresa ABC   | Empresa | Indeferido
Processamento Inteligente
✅ Se Gestor = IFSC e Status = Ativo: Anuidades normais ❌ Se Gestor ≠ IFSC: Anuidades marcadas como "não pagar" ❌ Se Status = Indeferido/Arquivado/Desistência: Anuidades marcadas como "não pagar"

🔒 Segurança
Aplicação local (sem servidor remoto por padrão)
Banco de dados SQLite local
Acesso controlado via Streamlit
Dados sensíveis não compartilhados
🛠️ Desenvolvido com
Streamlit: Interface web interativa
Pandas: Manipulação de dados
SQLite: Banco de dados leve
ReportLab: Geração de PDF
openpyxl: Suporte a Excel
python-dateutil: Cálculos de datas
📝 Licença
Este projeto é propriedade do Instituto Federal de Educação, Ciência e Tecnologia de Santa Catarina (IFSC).

👨‍💻 Autor
Desenvolvido para o IFSC - Sistema de Gestão de Propriedade Intelectual

📞 Suporte
Para dúvidas ou problemas, entre em contato com o responsável pela propriedade intelectual do IFSC.

Versão: 2.0.0 Última Atualização: Junho 2026
