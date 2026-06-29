import sqlite3
from datetime import datetime, date
import pandas as pd
from dateutil.relativedelta import relativedelta
from pathlib import Path

DATABASE_FILE = Path("patentes.db")

# =====================================================
# CONEXÃO
# =====================================================

def conectar():
    return sqlite3.connect(DATABASE_FILE, check_same_thread=False)

# =====================================================
# NORMALIZAÇÃO DE DATAS
# =====================================================

def normalizar_data(data):
    if data in (None, "", pd.NaT):
        return None

    if isinstance(data, pd.Timestamp):
        return data.date().strftime("%Y-%m-%d")

    if isinstance(data, (datetime, date)):
        return data.strftime("%Y-%m-%d")

    if isinstance(data, str):
        data = data.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(data, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None

# =====================================================
# CRIAÇÃO DO BANCO
# =====================================================

def init_database():
    conn = conectar()
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

# =====================================================
# PATENTES
# =====================================================

def adicionar_patente(numero_patente, data_deposito, data_concessao=None,
                      descricao="", titular="", gestor="", status="Ativo"):

    conn = conectar()
    cursor = conn.cursor()

    try:
        data_dep = normalizar_data(data_deposito)
        data_conc = normalizar_data(data_concessao)

        cursor.execute("""
            INSERT INTO patentes
            (numero_patente, data_deposito, data_concessao, descricao, titular, gestor, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            numero_patente,
            data_dep,
            data_conc,
            descricao.strip(),
            titular.strip(),
            gestor.strip(),
            status.strip()
        ))

        patente_id = cursor.lastrowid
        data_dep_date = datetime.strptime(data_dep, "%Y-%m-%d").date()

        # 🔴 SEM QUALQUER REGRA DE "NÃO PAGAR"
        for anuidade in range(1, 21):
            inicio_ord = data_dep_date + relativedelta(years=3 + (anuidade - 1))
            fim_ord = inicio_ord + relativedelta(months=3)
            inicio_ext = fim_ord + relativedelta(days=1)
            fim_ext = inicio_ext + relativedelta(months=6)

            cursor.execute("""
                INSERT INTO anuidades
                (patente_id, numero_anuidade,
                 data_inicio_ordinario, data_fim_ordinario,
                 data_inicio_extraordinario, data_fim_extraordinario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                patente_id,
                anuidade,
                inicio_ord.strftime("%Y-%m-%d"),
                fim_ord.strftime("%Y-%m-%d"),
                inicio_ext.strftime("%Y-%m-%d"),
                fim_ext.strftime("%Y-%m-%d")
            ))

        conn.commit()
        return True, "Patente adicionada com sucesso!"

    except sqlite3.IntegrityError:
        return False, "Patente já existe!"
    except Exception as e:
        return False, f"Erro: {e}"
    finally:
        conn.close()

# =====================================================
# CONSULTAS
# =====================================================

def obter_patentes():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM patentes ORDER BY data_deposito DESC", conn)
    conn.close()
    return df

def obter_anuidades(patente_id):
    conn = conectar()
    df = pd.read_sql("""
        SELECT *
        FROM anuidades
        WHERE patente_id = ?
        ORDER BY numero_anuidade
    """, conn, params=(patente_id,))
    conn.close()
    return df

# =====================================================
# ATUALIZAÇÕES
# =====================================================

def atualizar_status_anuidade(patente_id, numero_anuidade, status, data_pagamento=None):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE anuidades
        SET status = ?, data_pagamento = ?
        WHERE patente_id = ? AND numero_anuidade = ?
    """, (
        status,
        normalizar_data(data_pagamento),
        patente_id,
        numero_anuidade
    ))

    conn.commit()
    conn.close()

def atualizar_patente(patente_id, data_concessao, descricao, titular, gestor, status):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE patentes
        SET data_concessao = ?, descricao = ?, titular = ?, gestor = ?, status = ?
        WHERE id = ?
    """, (
        normalizar_data(data_concessao),
        descricao.strip(),
        titular.strip(),
        gestor.strip(),
        status.strip(),
        patente_id
    ))

    conn.commit()
    conn.close()
