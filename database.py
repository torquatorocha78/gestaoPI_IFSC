# database.py
import sqlite3
import pandas as pd
from datetime import date, timedelta

DB_NAME = "patentes.db"


def conectar():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_database():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS patentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_patente TEXT UNIQUE,
        data_deposito DATE,
        data_concessao DATE,
        descricao TEXT,
        titular TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS anuidades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patente_id INTEGER,
        numero_anuidade INTEGER,
        data_inicio_ordinario DATE,
        data_fim_ordinario DATE,
        data_inicio_extraordinario DATE,
        data_fim_extraordinario DATE,
        data_pagamento DATE,
        status TEXT,
        FOREIGN KEY (patente_id) REFERENCES patentes(id)
    )
    """)

    conn.commit()
    conn.close()


def obter_patentes():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM patentes ORDER BY id", conn)
    conn.close()
    return df


def adicionar_patente(numero, data_dep, data_conc, descricao, titular):
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO patentes
            (numero_patente, data_deposito, data_concessao, descricao, titular)
            VALUES (?, ?, ?, ?, ?)
            """,
            (numero, data_dep, data_conc, descricao, titular),
        )
        patente_id = cur.lastrowid

        inicio = pd.to_datetime(data_dep)
        for i in range(1, 21):
            ini_ord = inicio + pd.DateOffset(years=i - 1)
            fim_ord = ini_ord + pd.DateOffset(months=3)
            ini_ext = fim_ord
            fim_ext = ini_ext + pd.DateOffset(months=3)

            cur.execute(
                """
                INSERT INTO anuidades
                (patente_id, numero_anuidade,
                 data_inicio_ordinario, data_fim_ordinario,
                 data_inicio_extraordinario, data_fim_extraordinario,
                 status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patente_id,
                    i,
                    ini_ord.date(),
                    fim_ord.date(),
                    ini_ext.date(),
                    fim_ext.date(),
                    "PENDENTE",
                ),
            )

        conn.commit()
        return True, "Patente cadastrada com sucesso"

    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def obter_anuidades(patente_id):
    conn = conectar()
    df = pd.read_sql(
        "SELECT * FROM anuidades WHERE patente_id = ? ORDER BY numero_anuidade",
        conn,
        params=(patente_id,),
    )
    conn.close()

    hoje = date.today()

    def normalizar_status(row):
        if row["data_pagamento"]:
            return "PAGA"
        if row["data_fim_extraordinario"] and pd.to_datetime(row["data_fim_extraordinario"]).date() < hoje:
            return "PAGA"
        return "PENDENTE"

    df["status"] = df.apply(normalizar_status, axis=1)
    return df


def atualizar_status_anuidade(patente_id, numero_anuidade, data_pagamento):
    conn = conectar()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE anuidades
        SET data_pagamento = ?, status = 'PAGA'
        WHERE patente_id = ? AND numero_anuidade = ?
        """,
        (data_pagamento, patente_id, numero_anuidade),
    )

    conn.commit()
    conn.close()
