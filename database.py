# database.py
import sqlite3
import pandas as pd
from datetime import date
import unicodedata

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

    colunas_existentes = {
        row[1] for row in cur.execute("PRAGMA table_info(patentes)").fetchall()
    }
    novas_colunas = {
        "titulo": "TEXT",
        "inventores": "TEXT",
        "campus": "TEXT",
        "atributos": "TEXT",
    }
    for coluna, tipo in novas_colunas.items():
        if coluna not in colunas_existentes:
            cur.execute(f"ALTER TABLE patentes ADD COLUMN {coluna} {tipo}")

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


def _valor_limpo(valor):
    if pd.isna(valor):
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


def _normalizar_coluna(coluna):
    texto = str(coluna).strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    for char in ["/", "\\", "-", ".", "(", ")", ":", ";"]:
        texto = texto.replace(char, " ")
    return "_".join(texto.split())


def _normalizar_status(status):
    status = _valor_limpo(status)
    if not status:
        return "Ativo"

    status_texto = str(status).strip()
    chave = _normalizar_coluna(status_texto)
    mapa = {
        "patente_concedida": "Patente Concedida",
        "patente_concedda": "Patente Concedida",
        "concedido": "Patente Concedida",
        "tramitando_normal": "Tramitando Normal",
        "infederimento": "Indeferimento",
        "indeferimento": "Indeferimento",
        "recurso_contra_indeferimento": "Recurso contra indeferimento",
        "pedido_de_exame": "Pedido de exame",
        "transferida_a_titularidade": "Transferida a titularidade",
    }
    return mapa.get(chave, status_texto)


def _parse_data(valor):
    valor = _valor_limpo(valor)
    if valor is None:
        return None
    if hasattr(valor, "date") and not isinstance(valor, str):
        return valor.date().isoformat()

    texto = str(valor).strip()
    if not texto:
        return None

    try:
        partes = texto.replace("-", "/").split("/")
        if len(partes) == 3 and all(p.isdigit() for p in partes):
            primeiro, segundo = int(partes[0]), int(partes[1])
            dayfirst = primeiro > 12 or segundo <= 12
            data = pd.to_datetime(texto, dayfirst=dayfirst, errors="raise")
        else:
            data = pd.to_datetime(texto, dayfirst=True, errors="raise")
        return data.date().isoformat()
    except Exception:
        return texto


def adicionar_patente(
    numero,
    data_dep,
    data_conc,
    descricao,
    titular,
    gestor=None,
    status_patente='Ativo',
    titulo=None,
    inventores=None,
    campus=None,
    atributos=None,
):
    """
    Agora aceita gestor e status. Insere patentes e gera anuidades.
    """
    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO patentes
            (numero_patente, data_deposito, data_concessao, descricao, titular, gestor, status,
             titulo, inventores, campus, atributos)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                numero,
                data_dep,
                data_conc,
                descricao,
                titular,
                gestor,
                _normalizar_status(status_patente),
                titulo,
                inventores,
                campus,
                atributos,
            ),
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


def atualizar_patente(
    patente_id,
    numero,
    data_dep,
    data_conc,
    descricao,
    titular,
    gestor=None,
    status_patente="Ativo",
    titulo=None,
    inventores=None,
    campus=None,
    atributos=None,
):
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE patentes
            SET numero_patente = ?, data_deposito = ?, data_concessao = ?,
                descricao = ?, titular = ?, gestor = ?, status = ?,
                titulo = ?, inventores = ?, campus = ?, atributos = ?
            WHERE id = ?
            """,
            (
                numero,
                data_dep,
                data_conc,
                descricao,
                titular,
                gestor,
                _normalizar_status(status_patente),
                titulo,
                inventores,
                campus,
                atributos,
                patente_id,
            ),
        )
        conn.commit()
        return True, "Patente atualizada com sucesso"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def salvar_patente_importada(dados):
    conn = conectar()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM patentes WHERE numero_patente = ?",
            (dados["numero"],),
        )
        existente = cur.fetchone()
    finally:
        conn.close()

    if existente:
        ok, msg = atualizar_patente(existente[0], **dados)
        return ok, "Atualizada: " + msg if ok else msg

    ok, msg = adicionar_patente(**dados)
    return ok, "Importada: " + msg if ok else msg


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
        colunas = {_normalizar_coluna(col): col for col in df.columns}

        def campo(*nomes):
            for nome in nomes:
                coluna = colunas.get(_normalizar_coluna(nome))
                if coluna is not None:
                    return coluna
            return None

        mapa = {
            "numero": campo("numero_patente", "número patente", "numero patente", "patente"),
            "data_dep": campo("data_deposito", "data depósito", "data deposito"),
            "data_conc": campo("data_concessao", "data_concessão", "data concessão", "data concessao"),
            "titulo": campo("titulo", "título"),
            "descricao": campo("resumo", "descricao", "descrição"),
            "inventores": campo("nome dos inventores", "inventores", "nome_dos_inventores"),
            "titular": campo("depositante titular", "depositante/ titular", "titular", "depositante"),
            "gestor": campo("gestor"),
            "status": campo("status do pedido", "status", "situacao", "situação"),
            "campus": campo("campus"),
            "atributos": campo("atributos", "atributo"),
        }

        for _, row in df.iterrows():
            numero = _valor_limpo(row.get(mapa["numero"])) if mapa["numero"] else None
            data_dep = _parse_data(row.get(mapa["data_dep"])) if mapa["data_dep"] else None

            if not numero or not data_dep:
                resultados.append((numero or "SEM_NUMERO", False, "Número da patente ou data de depósito ausente"))
                continue

            dados = {
                "numero": str(numero),
                "data_dep": data_dep,
                "data_conc": _parse_data(row.get(mapa["data_conc"])) if mapa["data_conc"] else None,
                "descricao": _valor_limpo(row.get(mapa["descricao"])) if mapa["descricao"] else None,
                "titular": _valor_limpo(row.get(mapa["titular"])) if mapa["titular"] else None,
                "gestor": _valor_limpo(row.get(mapa["gestor"])) if mapa["gestor"] else None,
                "status_patente": _normalizar_status(row.get(mapa["status"])) if mapa["status"] else "Ativo",
                "titulo": _valor_limpo(row.get(mapa["titulo"])) if mapa["titulo"] else None,
                "inventores": _valor_limpo(row.get(mapa["inventores"])) if mapa["inventores"] else None,
                "campus": _valor_limpo(row.get(mapa["campus"])) if mapa["campus"] else None,
                "atributos": _valor_limpo(row.get(mapa["atributos"])) if mapa["atributos"] else None,
            }
            ok, msg = salvar_patente_importada(dados)
            resultados.append((numero, ok, msg))
    except Exception as e:
        resultados.append(("ERRO_GERAL", False, str(e)))

    return resultados


def analisar_inconsistencias_excel(arquivo_excel):
    df = pd.read_excel(arquivo_excel)
    problemas = []

    colunas_originais = list(df.columns)
    colunas_normalizadas = {_normalizar_coluna(col): col for col in colunas_originais}
    if any(str(col) != str(col).strip() for col in colunas_originais):
        problemas.append("Há cabeçalhos com espaços sobrando; o importador corrige isso automaticamente.")

    obrigatorias = ["numero_patente", "data_deposito"]
    for obrigatoria in obrigatorias:
        if _normalizar_coluna(obrigatoria) not in colunas_normalizadas:
            problemas.append(f"Coluna obrigatória não encontrada: {obrigatoria}")

    numero_col = colunas_normalizadas.get("numero_patente")
    if numero_col:
        vazios = df[df[numero_col].isna()].index.tolist()
        duplicados = df[df[numero_col].duplicated(keep=False)][numero_col].dropna().unique().tolist()
        if vazios:
            problemas.append(f"{len(vazios)} linha(s) sem número de patente.")
        if duplicados:
            problemas.append(f"Números de patente duplicados: {', '.join(map(str, duplicados))}")

    for nome in ["titulo", "resumo", "nome_dos_inventores", "depositante_titular"]:
        col = colunas_normalizadas.get(nome)
        if col:
            vazios = int(df[col].isna().sum())
            if vazios:
                problemas.append(f"{vazios} linha(s) sem {col}.")

    status_col = colunas_normalizadas.get("status_do_pedido") or colunas_normalizadas.get("status")
    if status_col:
        status_unicos = sorted({_normalizar_status(v) for v in df[status_col].dropna().tolist()})
        problemas.append("Status identificados: " + ", ".join(status_unicos))

    if "campus" not in colunas_normalizadas:
        problemas.append("A planilha não tem uma coluna chamada Campus; o campo existe no app e ficará vazio até ser preenchido/importado.")
    if "atributos" not in colunas_normalizadas and "atributo" not in colunas_normalizadas:
        problemas.append("A planilha não tem uma coluna chamada Atributos; o campo existe no app e ficará vazio até ser preenchido/importado.")

    return problemas
