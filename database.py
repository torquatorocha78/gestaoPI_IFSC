# database.py
import sqlite3
import pandas as pd
from datetime import date

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
        titular TEXT,
        gestor TEXT,
        status TEXT
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


def adicionar_patente(numero, data_dep, data_conc, descricao, titular, gestor=None, status_patente='Ativo'):
    """
    Agora aceita gestor e status. Insere patentes e gera anuidades.
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO patentes
            (numero_patente, data_deposito, data_concessao, descricao, titular, gestor, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (numero, data_dep, data_conc, descricao, titular, gestor, status_patente),
        )
        patente_id = cur.lastrowid

        inicio = pd.to_datetime(data_dep)
        for i in range(1, 21):
            ini_ord = inicio + pd.DateOffset(years=i - 1)
            fim_ord = ini_ord + pd.DateOffset(months=3)
            ini_ext = fim_ord
            fim_ext = ini_ext + pd.DateOffset(months=3)

            # status padrão das anuidades: 'pendente'
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
                    "pendente",
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
        # Mantemos o status explícito salvo no DB quando presente
        if row.get("status"):
            s = str(row["status"]).lower()
            # Se já foi marcado 'nao_pagar' mantém
            if s == "nao_pagar":
                return "nao_pagar"
            # se data_pagamento preenchida -> pago
            if row.get("data_pagamento"):
                return "pago"
        # se chegou após o fim extraordinário consideramos pago/expirado
        if row.get("data_fim_extraordinario"):
            try:
                if pd.to_datetime(row["data_fim_extraordinario"]).date() < hoje:
                    return "pago"
            except Exception:
                pass
        return "pendente"

    df["status"] = df.apply(normalizar_status, axis=1)
    return df


def atualizar_status_anuidade(patente_id, numero_anuidade, novo_status, data_pagamento=None):
    """
    novo_status: 'pago' ou 'nao_pagar' ou 'pendente'
    data_pagamento: string 'YYYY-MM-DD' ou None
    Compatível com os usos em app.py.
    """
    conn = conectar()
    cur = conn.cursor()

    novo_status = novo_status.lower()

    if novo_status == "pago":
        cur.execute(
            """
            UPDATE anuidades
            SET data_pagamento = ?, status = 'pago'
            WHERE patente_id = ? AND numero_anuidade = ?
            """,
            (data_pagamento, patente_id, numero_anuidade),
        )
    elif novo_status == "nao_pagar":
        cur.execute(
            """
            UPDATE anuidades
            SET data_pagamento = NULL, status = 'nao_pagar'
            WHERE patente_id = ? AND numero_anuidade = ?
            """,
            (patente_id, numero_anuidade),
        )
    else:
        # apenas atualiza status
        cur.execute(
            """
            UPDATE anuidades
            SET status = ?
            WHERE patente_id = ? AND numero_anuidade = ?
            """,
            (novo_status, patente_id, numero_anuidade),
        )

    conn.commit()
    conn.close()


def deletar_patente(patente_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM anuidades WHERE patente_id = ?", (patente_id,))
    cur.execute("DELETE FROM patentes WHERE id = ?", (patente_id,))
    conn.commit()
    conn.close()


def importar_excel(arquivo_excel):
    """
    Placeholder simples: implement conforme necessidade. Retorna lista de tuplas (patente, sucesso, mensagem)
    """
    resultados = []
    try:
        df = pd.read_excel(arquivo_excel)
        for _, row in df.iterrows():
            numero = row.get("numero_patente")
            data_dep = row.get("data_deposito")
            data_conc = row.get("data_concessao") if "data_concessao" in row else None
            descricao = row.get("descricao") if "descricao" in row else None
            titular = row.get("titular") if "titular" in row else None
            gestor = row.get("gestor") if "gestor" in row else None
            status = row.get("status") if "status" in row else "Ativo"
            ok, msg = adicionar_patente(str(numero), str(data_dep), str(data_conc) if data_conc else None, descricao, titular, gestor, status)
            resultados.append((numero, ok, msg))
    except Exception as e:
        resultados.append(("ERRO_GERAL", False, str(e)))

    return resultados
