import sqlite3
from datetime import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta
import os

DATABASE_FILE = "patentes.db"

def init_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_patente TEXT UNIQUE NOT NULL,
            data_deposito DATE NOT NULL,
            data_concessao DATE,
            descricao TEXT,
            titular TEXT,
            gestor TEXT,
            status TEXT DEFAULT 'Ativo',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anuidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patente_id INTEGER NOT NULL,
            numero_anuidade INTEGER NOT NULL,
            data_inicio_ordinario DATE NOT NULL,
            data_fim_ordinario DATE NOT NULL,
            data_inicio_extraordinario DATE NOT NULL,
            data_fim_extraordinario DATE NOT NULL,
            status TEXT DEFAULT 'pendente',
            data_pagamento DATE,
            FOREIGN KEY (patente_id) REFERENCES patentes(id),
            UNIQUE(patente_id, numero_anuidade)
        )
    """)
    
    conn.commit()
    conn.close()

def adicionar_patente(numero_patente, data_deposito, data_concessao=None, descricao="", titular="", gestor="", status="Ativo"):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO patentes (numero_patente, data_deposito, data_concessao, descricao, titular, gestor, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (numero_patente, data_deposito, data_concessao, descricao, titular, gestor, status))
        
        patente_id = cursor.lastrowid
        
        data_dep = datetime.strptime(data_deposito, "%Y-%m-%d").date() if isinstance(data_deposito, str) else data_deposito
        
        # Determinar se deve marcar anuidades como "não pagar"
        marca_nao_pagar = False
        if gestor and gestor.upper() != "IFSC":
            marca_nao_pagar = True
        if status in ["Indeferido", "Arquivado", "Desistência"]:
            marca_nao_pagar = True
        
        # Criar 20 anuidades
        for anuidade in range(1, 21):
            data_inicio_ord = data_dep + relativedelta(years=3, days=(anuidade-1)*365)
            data_fim_ord = data_inicio_ord + relativedelta(months=3)
            data_inicio_extraord = data_fim_ord + relativedelta(days=1)
            data_fim_extraord = data_inicio_extraord + relativedelta(months=6)
            
            status_anuidade = "nao_pagar" if marca_nao_pagar else "pendente"
            
            cursor.execute("""
                INSERT INTO anuidades 
                (patente_id, numero_anuidade, data_inicio_ordinario, data_fim_ordinario, 
                 data_inicio_extraordinario, data_fim_extraordinario, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (patente_id, anuidade, data_inicio_ord, data_fim_ord, 
                  data_inicio_extraord, data_fim_extraord, status_anuidade))
        
        conn.commit()
        return True, "Patente adicionada com sucesso!"
        
    except sqlite3.IntegrityError:
        return False, "Patente ja existe no banco de dados!"
    except Exception as e:
        return False, f"Erro ao adicionar patente: {str(e)}"
    finally:
        conn.close()

def obter_patentes():
    conn = sqlite3.connect(DATABASE_FILE)
    query = "SELECT id, numero_patente, data_deposito, data_concessao, descricao, titular, gestor, status FROM patentes ORDER BY data_deposito DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def obter_anuidades(patente_id):
    conn = sqlite3.connect(DATABASE_FILE)
    query = '''
        SELECT numero_anuidade, data_inicio_ordinario, data_fim_ordinario,
               data_inicio_extraordinario, data_fim_extraordinario, status, data_pagamento
        FROM anuidades
        WHERE patente_id = ?
        ORDER BY numero_anuidade
    '''
    df = pd.read_sql_query(query, conn, params=(patente_id,))
    conn.close()
    return df

def atualizar_status_anuidade(patente_id, numero_anuidade, status, data_pagamento=None):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE anuidades
        SET status = ?, data_pagamento = ?
        WHERE patente_id = ? AND numero_anuidade = ?
    """, (status, data_pagamento, patente_id, numero_anuidade))
    
    conn.commit()
    conn.close()

def deletar_patente(patente_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM anuidades WHERE patente_id = ?', (patente_id,))
    cursor.execute('DELETE FROM patentes WHERE id = ?', (patente_id,))
    
    conn.commit()
    conn.close()

def importar_excel(caminho_arquivo):
    try:
        df = pd.read_excel(caminho_arquivo)
        resultados = []
        
        for _, row in df.iterrows():
            numero = str(row['numero_patente']) if 'numero_patente' in df.columns else str(row.iloc[0])
            data_dep = row['data_deposito'] if 'data_deposito' in df.columns else row.iloc[1]
            
            if isinstance(data_dep, datetime):
                data_dep = data_dep.strftime("%Y-%m-%d")
            else:
                # Tentar converter string em data
                try:
                    data_dep = pd.to_datetime(data_dep).strftime("%Y-%m-%d")
                except:
                    pass
            
            data_conc = row.get('data_concessao', None)
            if isinstance(data_conc, datetime):
                data_conc = data_conc.strftime("%Y-%m-%d")
            elif pd.notna(data_conc) and data_conc != '':
                try:
                    data_conc = pd.to_datetime(data_conc).strftime("%Y-%m-%d")
                except:
                    data_conc = None
            else:
                data_conc = None
            
            descricao = str(row.get('descricao', '')).strip()
            titular = str(row.get('titular', '')).strip()
            gestor = str(row.get('gestor', '')).strip()
            status = str(row.get('status', 'Ativo')).strip()
            
            sucesso, mensagem = adicionar_patente(numero, data_dep, data_conc, descricao, titular, gestor, status)
            resultados.append((numero, sucesso, mensagem))
        
        return resultados
    except Exception as e:
        return [("Erro", False, f"Erro ao importar: {str(e)}")]
