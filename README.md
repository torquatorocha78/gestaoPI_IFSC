🏛️ Gestão de Patentes do IFSC
Sistema Integrado de Gestão de Propriedade Intelectual

O SIGPI-IF é um sistema desenvolvido em Python para apoiar a gestão da propriedade intelectual do Instituto Federal de Educação, Ciência e Tecnologia de Santa Catarina. A plataforma permite o gerenciamento integrado de ativos de propriedade intelectual, oferecendo ferramentas para acompanhamento de patentes, controle de prazos e anuidades, monitoramento de processos e geração de indicadores estratégicos.


# Alterações — Gestão PI IFSC

## Inventores
- Cadastro agora contém todos os campos da planilha `inventores.xlsx`.
- `Código Pedido` é tratado como relacionamento, não como atributo do inventor.
- Relação N:N: `patente_inventor.numero_patente -> patentes.numero_patente`.
- Importação `.xls` e `.xlsx` cria/atualiza o inventor e cria o vínculo com a PI.
- Exportação retorna a estrutura da planilha, incluindo os processos vinculados.

## Gerenciar PIs
Removidos do formulário:
- CPF dos Inventores
- Observações FORMICT

Incluídos:
- Setor econômico / CNAE
- CNAE / Subclassificação
- TRL
- Território
- Sigilo
- Cotitularidade
- Cotitulares

## Relatório FORMICT
Agora integra:
- dados da tabela `patentes`;
- pagamentos/anuidades;
- inventores da relação N:N e seus principais atributos;
- Excel com aba `FORMICT_Completo` e aba `Inventores`.

## Importante
Antes de usar a nova estrutura, execute `MIGRACAO_INVENTORES_FORMICT.sql` no Supabase.
A migração é não destrutiva.
