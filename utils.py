from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import pandas as pd

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
        # Tentar diferentes formatos de data
        try:
            data_fim_ord = datetime.strptime(data_fim_ord, "%Y-%m-%d").date()
        except Exception:
            try:
                data_fim_ord = datetime.strptime(data_fim_ord, "%Y-%m-%d %H:%M:%S").date()
            except Exception:
                try:
                    data_fim_ord = parse(data_fim_ord).date()
                except Exception:
                    return '-'
    
    dias = (data_fim_ord - hoje).days
    return max(0, dias)

def formatar_data(data):
    """Format a date-like value to DD/MM/YYYY. Returns '-' when empty or invalid.

    Handles:
    - str in formats like 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' or other parseable strings
    - datetime.date / datetime.datetime / pandas.Timestamp / numpy datetime64
    - None / NaT / NaN
    """
    if data is None:
        return "-"

    # pandas missing
    try:
        if isinstance(data, float) and pd.isna(data):
            return "-"
    except Exception:
        pass

    # If it's already a date/datetime-like object
    try:
        # pandas Timestamp or numpy datetime64
        if hasattr(data, 'to_datetime64') or hasattr(data, 'tzinfo') or hasattr(data, 'year'):
            try:
                d = pd.to_datetime(data)
                if pd.isna(d):
                    return "-"
                return d.date().strftime("%d/%m/%Y")
            except Exception:
                pass
    except Exception:
        pass

    # If it's a string, try parsing robustly
    if isinstance(data, str):
        data = data.strip()
        if data == "":
            return "-"
        # Try common formats first for speed
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
            try:
                d = datetime.strptime(data, fmt).date()
                return d.strftime("%d/%m/%Y")
            except Exception:
                continue
        # Fallback to dateutil.parser
        try:
            d = parse(data)
            return d.date().strftime("%d/%m/%Y")
        except Exception:
            return data

    # Try to coerce with pandas as last resort
    try:
        d = pd.to_datetime(data)
        if pd.isna(d):
            return "-"
        return d.date().strftime("%d/%m/%Y")
    except Exception:
        return str(data)

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
