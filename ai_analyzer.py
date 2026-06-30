import pandas as pd
import database as db
from datetime import datetime
import utils

def analisar_pergunta(df_patentes, pergunta):
    """
    Análise inteligente de perguntas sobre patentes usando lógica baseada em palavras-chave
    """
    pergunta_lower = pergunta.lower()
    
    # Contar patentes concedidas
    if "concedida" in pergunta_lower or "concessão" in pergunta_lower:
        total = len(df_patentes)
        concedidas = len(df_patentes[df_patentes['data_concessao'].notna()])
        pendentes = total - concedidas
        return f"""
        **Patentes Concedidas:**
        - Total de patentes: {total}
        - Patentes concedidas: {concedidas}
        - Patentes pendentes: {pendentes}
        - Taxa de concessão: {(concedidas/total*100):.1f}%
        """
    
    # Patentes vencidas
    if "vencida" in pergunta_lower or "expirada" in pergunta_lower:
        vencidas = 0
        for _, patente in df_patentes.iterrows():
            anuidades = db.obter_anuidades(patente['id'])
            for _, anu in anuidades.iterrows():
                if anu['status'] != 'nao_pagar':
                    status = utils.calcular_status_anuidade(
                        anu['data_inicio_ordinario'],
                        anu['data_fim_ordinario'],
                        anu['data_inicio_extraordinario'],
                        anu['data_fim_extraordinario'],
                        anu['data_pagamento']
                    )
                    if status == 'vermelho':
                        vencidas += 1
        return f"**Patentes com Anuidades Vencidas:** {vencidas} anuidades precisam de atenção urgente!"
    
    # Patentes do IFSC
    if "ifsc" in pergunta_lower:
        ifsc_patentes = len(df_patentes[
            (df_patentes['gestor'].isna()) | 
            (df_patentes['gestor'].str.upper() == "IFSC")
        ])
        outras = len(df_patentes) - ifsc_patentes
        return f"""
        **Patentes por Gestor:**
        - Patentes IFSC: {ifsc_patentes}
        - Patentes de outros gestores: {outras}
        """
    
    # Status geral
    if "status" in pergunta_lower or "situação" in pergunta_lower:
        ativas = len(df_patentes[df_patentes['status'] == 'Ativo'])
        indeferidas = len(df_patentes[df_patentes['status'] == 'Indeferido'])
        arquivadas = len(df_patentes[df_patentes['status'] == 'Arquivado'])
        desistencias = len(df_patentes[df_patentes['status'] == 'Desistência'])
        
        return f"""
        **Status das Patentes:**
        - Ativas: {ativas}
        - Indeferidas: {indeferidas}
        - Arquivadas: {arquivadas}
        - Desistências: {desistencias}
        """
    
    # Contagem total
    if "quantas" in pergunta_lower or "total" in pergunta_lower:
        return f"**Total de Patentes:** {len(df_patentes)} patentes cadastradas no sistema."
    
    # Resposta padrão
    return f"**Resposta:** Analisando {len(df_patentes)} patentes... Pergunta não corresponde aos padrões conhecidos. Tente perguntar sobre: patentes concedidas, vencidas, do IFSC ou status geral."

def gerar_estatisticas(df_patentes):
    """
    Gera estatísticas gerais sobre as patentes
    """
    total = len(df_patentes)
    concedidas = len(df_patentes[df_patentes['data_concessao'].notna()])
    
    stats = f"""
    ### 📊 Estatísticas Gerais
    
    **Total de Patentes:** {total}
    
    **Patentes Concedidas:** {concedidas} ({(concedidas/total*100):.1f}%)
    
    **Patentes Pendentes:** {total - concedidas} ({((total-concedidas)/total*100):.1f}%)
    
    **Patentes por Status:**
    """
    
    for status in ['Ativo', 'Indeferido', 'Arquivado', 'Desistência']:
        count = len(df_patentes[df_patentes['status'] == status])
        if count > 0:
            stats += f"\n- {status}: {count}"
    
    return stats

def patentes_por_gestor(df_patentes):
    """
    Agrupa patentes por gestor
    """
    output = "### 🎯 Patentes por Gestor\n\n"
    
    gestores = df_patentes['gestor'].fillna('IFSC').str.upper().unique()
    
    for gestor in sorted(gestores):
        count = len(df_patentes[
            ((df_patentes['gestor'].isna()) & (gestor == 'IFSC')) |
            (df_patentes['gestor'].str.upper() == gestor)
        ])
        output += f"- **{gestor}:** {count} patentes\n"
    
    return output

def gerar_alertas(df_patentes):
    """
    Gera alertas sobre anuidades urgentes
    """
    alertas = "### ⚠️ Alertas Urgentes\n\n"
    alertas_count = 0
    
    for _, patente in df_patentes.iterrows():
        anuidades = db.obter_anuidades(patente['id'])
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
                alertas += f"- 🚨 **{patente['numero_patente']}** - Anuidade {anu['numero_anuidade']} VENCIDA!\n"
                alertas_count += 1
            elif status == 'amarelo':
                dias = utils.obter_dias_restantes(anu['data_fim_ordinario'])
                alertas += f"- ⚠️ **{patente['numero_patente']}** - Anuidade {anu['numero_anuidade']} vence em {dias} dias\n"
                alertas_count += 1
    
    if alertas_count == 0:
        alertas += "✅ Nenhum alerta urgente! Todas as anuidades estão em dia."
    
    return alertas
