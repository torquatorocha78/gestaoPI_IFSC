from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def calcular_status_anuidade(data_inicio_ord, data_fim_ord, data_inicio_extraord, data_fim_extraord, data_pagamento=None):
    hoje = datetime.now().date()
    
    if data_pagamento:
        return 'pago'
    
    if isinstance(data_inicio_ord, str):
        data_inicio_ord = datetime.strptime(data_inicio_ord, "%Y-%m-%d").date()
    if isinstance(data_fim_ord, str):
        data_fim_ord = datetime.strptime(data_fim_ord, "%Y-%m-%d").date()
    if isinstance(data_inicio_extraord, str):
        data_inicio_extraord = datetime.strptime(data_inicio_extraord, "%Y-%m-%d").date()
    if isinstance(data_fim_extraord, str):
        data_fim_extraord = datetime.strptime(data_fim_extraord, "%Y-%m-%d").date()
    
    if data_inicio_extraord <= hoje <= data_fim_extraord:
        return 'vermelho'
    
    if hoje > data_fim_extraord:
        return 'vermelho'
    
    data_alerta = data_fim_ord - timedelta(days=30)
    if data_alerta <= hoje <= data_fim_ord:
        return 'amarelo'
    
    if data_inicio_ord <= hoje <= data_alerta:
        return 'verde'
    
    if hoje < data_inicio_ord:
        return 'verde'
    
    return 'verde'

def obter_dias_restantes(data_fim_ord, data_pagamento=None):
    if data_pagamento:
        return 0
    
    hoje = datetime.now().date()
    
    if isinstance(data_fim_ord, str):
        data_fim_ord = datetime.strptime(data_fim_ord, "%Y-%m-%d").date()
    
    dias = (data_fim_ord - hoje).days
    return max(0, dias)

def formatar_data(data):
    if isinstance(data, str):
        data = datetime.strptime(data, "%Y-%m-%d").date()
    return data.strftime("%d/%m/%Y") if data else "-"

def obter_cor_status(status):
    cores = {
        'verde': '#00CC00',
        'amarelo': '#FFCC00',
        'vermelho': '#FF0000',
        'pago': '#0099FF',
        'nao_pagar': '#CCCCCC'
    }
    return cores.get(status, '#CCCCCC')

def criar_emoji_status(status):
    emojis = {
        'verde': '✅',
        'amarelo': '⚠️',
        'vermelho': '❌',
        'pago': '💰',
        'nao_pagar': '⛔'
    }
    return emojis.get(status, '❓')
