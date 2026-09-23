Gestão de Propriedade Intelectual – NIT/IFSC
Resumo das tecnologias e funcionalidades
1. Visão geral

O sistema é uma aplicação web desenvolvida em Python, utilizando Streamlit como interface, Supabase/PostgreSQL como banco de dados e integração com Inteligência Artificial generativa para apoiar atividades de análise jurídica e avaliação de patenteabilidade.

A proposta é centralizar, em um único ambiente, a gestão das Propriedades Intelectuais do IFSC, incluindo:

Patentes;
Modelos de Utilidade;
Desenhos Industriais;
Programas de computador;
Controle de anuidades e obrigações financeiras;
Relatórios;
Informações de inventores;
Apoio à análise de patenteabilidade;
Assistência jurídica baseada em IA;
Histórico das análises realizadas.
2. Tecnologias utilizadas
Tecnologia	Função no sistema
Python	Linguagem principal de desenvolvimento
Streamlit	Interface web e construção dos módulos do sistema
Supabase	Banco de dados em nuvem
PostgreSQL	Banco de dados relacional utilizado pelo Supabase
API REST do Supabase	Comunicação entre o aplicativo e o banco
Groq API	Plataforma utilizada para acesso aos modelos de IA
OpenAI-compatible API	Interface utilizada para comunicação com os modelos da Groq
OpenAI GPT-OSS-20B	Modelo de IA utilizado no módulo de Parecer de Patenteabilidade, conforme configuração atual
python-docx	Geração dos pareceres em Word
pypdf	Leitura e extração de texto dos formulários PDF
Pandas	Tratamento e manipulação de dados e planilhas
OpenPyXL	Leitura e geração de arquivos Excel
SQL	Criação, consulta e gerenciamento das estruturas do banco
3. Inteligência Artificial

O sistema possui dois usos principais de IA.

⚖️ Assistente Jurídico NIT

Utiliza IA para auxiliar o NIT em atividades relacionadas à análise jurídica e de propriedade intelectual.

A IA funciona como ferramenta de apoio à análise, permitindo consultar e produzir respostas a partir das informações/documentos fornecidos.

O objetivo é reduzir o tempo gasto em tarefas de pesquisa, interpretação e elaboração preliminar de documentos.

📝 Parecer de Patenteabilidade – NIT/IFSC

É o módulo mais recente de IA.

O fluxo é:

Formulário de Notificação de Criação/Invenção → extração do PDF → informações da reunião do NIT → análise da IA → parecer técnico → armazenamento no histórico.

A IA recebe:

formulário de criação/invenção;
informações preenchidas pelo inventor;
observações da reunião do NIT;
informações complementares fornecidas pelo responsável pela análise.

A IA é instruída a:

utilizar somente informações efetivamente preenchidas;
ignorar campos vazios;
ignorar campos marcados como “Não aplicável”;
não inventar informações;
analisar aspectos de patenteabilidade;
considerar informações técnicas e estratégicas fornecidas pelo NIT;
estruturar o parecer de acordo com o modelo utilizado pelo NIT/IFSC.

O sistema também permite gerar o resultado em Word (.docx).

4. Módulos do sistema
🏠 1. Dashboard

Apresenta uma visão geral da carteira de Propriedade Intelectual.

Permite ao NIT acompanhar informações como:

quantidade de PIs;
modalidades;
situação dos processos;
obrigações financeiras;
pagamentos;
informações gerais da carteira.

Objetivo: fornecer uma visão gerencial rápida da situação da propriedade intelectual do IFSC.

📋 2. Gerenciamento das PIs

É o núcleo operacional do sistema.

Permite:

cadastrar PI;
editar informações;
consultar processos;
visualizar modalidade;
titular;
gestor;
inventores;
datas;
situação;
informações técnicas;
informações relacionadas ao FORMICT.

As modalidades contempladas incluem:

Patente
Desenho Industrial
Software
💰 3. Controle de anuidades e pagamentos

O sistema calcula e acompanha as obrigações relacionadas à manutenção das PIs.

Patentes

Controle das anuidades.

Desenho Industrial

Controle dos pagamentos periódicos previstos para a modalidade.

Software

Controle do pagamento relacionado ao registro.

O módulo permite registrar:

número da obrigação;
período ordinário;
período extraordinário;
data do pagamento;
valor pago;
descrição;
observação;
situação.

Situações utilizadas incluem, entre outras:

Pendente, Pago, Não pagar, Vencido, Em análise e Cancelado.

📊 4. Relatórios / FORMICT

Permite gerar informações para acompanhamento e prestação de informações.

Os dados podem ser exportados para:

Excel
PDF
CSV, conforme os recursos disponíveis no sistema.

O relatório de pagamentos permite trabalhar com informações como:

processo;
título;
modalidade;
gestor;
campus;
obrigação;
descrição;
valor;
data do pagamento;
ano do pagamento;
situação.
👥 5. Gestão de inventores

O banco possui estrutura própria para relacionamento entre:

PI ↔ Inventores

Isso permite trabalhar com múltiplos inventores associados a uma mesma PI.

A estrutura suporta informações como:

nome;
CPF;
endereço;
instituição;
telefone;
e-mail;
ordem do inventor.

Isso é importante para manter a relação entre a tecnologia e seus respectivos inventores.

⚖️ 6. Assistente Jurídico NIT

Módulo de apoio baseado em IA.

Sua finalidade é auxiliar o NIT em tarefas relacionadas a:

análise de questões de propriedade intelectual;
interpretação de informações/documentos;
elaboração de respostas;
apoio à análise jurídica;
produção de textos preliminares.

A ferramenta funciona como assistente, não como substituta da análise e decisão do NIT.

📝 7. Parecer de Patenteabilidade – NIT/IFSC

Este é o módulo desenvolvido especificamente para apoiar a avaliação inicial de tecnologias recebidas pelo NIT.

Entrada

O usuário fornece:

1. Formulário de Notificação de Criação/Invenção em PDF

e

2. Observações da reunião do NIT com o inventor.

As observações podem conter, por exemplo:

interesse de empresa;
possibilidade de licenciamento;
TRL;
existência de protótipo;
testes realizados;
intenção do inventor;
potencial de mercado;
parceiros;
estratégia de proteção.
Processamento

A IA analisa as informações fornecidas e produz uma avaliação estruturada.

Saída

O sistema gera:

análise de patenteabilidade;
descrição da tecnologia;
análise do estado da técnica, quando houver informação suficiente;
análise preliminar de novidade;
atividade inventiva;
aplicação industrial;
maturidade tecnológica;
potencial de mercado;
aspectos relacionados à titularidade;
riscos;
conclusão;
recomendação técnica do NIT.

Quando não existem informações suficientes para determinada análise, o sistema não deve inventar dados.

🗂️ 8. Histórico de Pareceres de Patenteabilidade

O módulo possui agora banco de histórico próprio.

Cada análise pode ficar registrada com:

PI/processo;
data e hora;
formulário analisado;
informações da reunião;
análise realizada;
parecer produzido;
modelo de IA utilizado.

Isso permite ao NIT:

consultar → recuperar → revisar → comparar → reaproveitar informações de análises anteriores.

Esse histórico é particularmente importante porque cria uma memória institucional das avaliações realizadas pelo NIT.

🗄️ 9. Banco de dados

O sistema utiliza o Supabase, que fornece infraestrutura de banco PostgreSQL em nuvem.

A estrutura possui tabelas relacionadas para:

PIs;
inventores;
relacionamento PI/inventor;
anuidades;
pagamentos;
histórico de pareceres;
informações auxiliares.

Também existem views SQL para facilitar consultas e geração de relatórios.

A vantagem é que os dados ficam centralizados e podem ser acessados pelo sistema sem depender de uma base SQLite instalada localmente.

10. Fluxo geral do sistema
                    GESTÃO DE PI – IFSC
                           │
          ┌────────────────┴────────────────┐
          │                                 │
     Gestão das PIs                   Inteligência Artificial
          │                                 │
    ┌─────┼─────┐                    ┌──────┴──────┐
    │     │     │                    │             │
 Patentes DI  Software          Assistente    Parecer de
    │     │     │                Jurídico    Patenteabilidade
    └─────┼─────┘                    │             │
          │                           │             │
          ▼                           ▼             ▼
   Obrigações/Pagamentos        Análise       Formulário +
          │                     jurídica      reunião NIT
          ▼                                         │
      Relatórios                                    ▼
          │                                    Análise IA
          │                                         │
          └──────────────┐                          ▼
                         │                    Parecer técnico
                         ▼                          │
                   SUPABASE /                      ▼
                  PostgreSQL                  Histórico
11. Principal ganho institucional

Do ponto de vista do NIT, o sistema transforma informações que normalmente ficam dispersas em planilhas, documentos, PDFs e análises individuais em uma estrutura centralizada.

Os principais ganhos são:

Centralização das PIs do IFSC
Controle de prazos e obrigações
Registro dos pagamentos
Geração de relatórios
Histórico institucional das análises
Apoio de IA às atividades do NIT
Padronização dos pareceres
Registro das informações das reuniões com inventores
Recuperação de análises anteriores
Redução de tarefas manuais
Maior rastreabilidade das decisões e avaliações
