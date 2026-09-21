import os
import json
import unicodedata
from datetime import date
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import pandas as pd
import requests

def _get_secret(nome: str, padrao: str = "") -> str:
    """Lê primeiro variável de ambiente e depois st.secrets, quando disponível."""
    valor = os.getenv(nome)
    if valor:
        return valor
    try:
        import streamlit as st
        return str(st.secrets.get(nome, padrao))
    except Exception:
        return padrao


SUPABASE_URL = _get_secret(
    "SUPABASE_URL",
    "https://ptxtclyfwlcwqgwzqieu.supabase.co",
).rstrip("/")

# Aceita os nomes mais comuns usados no Streamlit/Supabase.
SUPABASE_KEY = (
    _get_secret("SUPABASE_KEY")
    or _get_secret("SUPABASE_PUBLISHABLE_KEY")
    or _get_secret("SUPABASE_ANON_KEY")
)

SUPABASE_TABLE = _get_secret("SUPABASE_TABLE", "patentes")


def _headers(prefer: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _endpoint(table: str = SUPABASE_TABLE) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


def _supabase_error(response: requests.Response) -> str:
    try:
        detalhe = response.json()
    except Exception:
        detalhe = response.text
    return f"Supabase retornou {response.status_code}: {detalhe}"


def _request(method: str, url: str, **kwargs: Any) -> Any:
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
    except requests.RequestException as exc:
        raise RuntimeError(f"Não foi possível conectar ao Supabase: {exc}") from exc
    if response.status_code >= 400:
        raise RuntimeError(_supabase_error(response))
    if not response.text:
        return None
    try:
        return response.json()
    except Exception:
        return response.text


def _normalizar_texto(valor: Any) -> str:
    texto = "" if valor is None or pd.isna(valor) else str(valor).strip().lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    for char in ["/", "\\", "-", ".", "(", ")", ":", ";", "_"]:
        texto = texto.replace(char, " ")
    return "_".join(texto.split())


def normalizar_modalidade(modalidade: Any) -> str:
    chave = _normalizar_texto(modalidade)
    if "software" in chave or "programa" in chave:
        return "Software"
    if "desenho" in chave or chave in {"di", "desenho_industrial"}:
        return "Desenho Industrial"
    return "Patente"


def _valor_limpo(valor: Any) -> Optional[Any]:
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except Exception:
        pass
    if isinstance(valor, str):
        valor = valor.strip()
        return valor or None
    return valor


def _parse_data(valor: Any) -> Optional[str]:
    valor = _valor_limpo(valor)
    if valor is None:
        return None
    if hasattr(valor, "date") and not isinstance(valor, str):
        return valor.date().isoformat()
    try:
        return pd.to_datetime(str(valor).strip(), dayfirst=True, errors="raise").date().isoformat()
    except Exception:
        return str(valor).strip() or None


def _normalizar_status(status: Any) -> str:
    status = _valor_limpo(status)
    if not status:
        return "Ativo"
    chave = _normalizar_texto(status)
    mapa = {
        "patente_concedida": "Patente Concedida",
        "concedido": "Patente Concedida",
        "concessao": "Patente Concedida",
        "tramitando_normal": "Tramitando Normal",
        "indeferimento": "Indeferimento",
        "infederimento": "Indeferimento",
        "recurso_contra_indeferimento": "Recurso contra indeferimento",
        "pedido_de_exame": "Pedido de exame",
        "transferida_a_titularidade": "Transferida a titularidade",
        "arquivado": "Arquivado",
        "desistencia": "Desistência",
    }
    return mapa.get(chave, str(status).strip())


def _coluna_existente(df: pd.DataFrame, *nomes: str) -> Optional[str]:
    normalizadas = {_normalizar_texto(col): col for col in df.columns}
    for nome in nomes:
        coluna = normalizadas.get(_normalizar_texto(nome))
        if coluna is not None:
            return coluna
    return None


def _preparar_patentes(df: pd.DataFrame) -> pd.DataFrame:
    """Converte o schema atual do Supabase para o schema esperado pelo app.py."""
    if df.empty:
        return df

    aliases = {
        "numero_patente": ("numero_patente", "pedido", "processo", "numero de patente", "patente"),
        "data_deposito": ("data_deposito", "deposito", "depósito", "data do deposito"),
        "data_concessao": ("data_concessao", "data da concessao", "data da concessão"),
        "descricao": ("descricao", "descrição", "resumo"),
        "titular": ("titular", "depositante_titular", "depositante", "depositante/ titular"),
        "gestor": ("gestor",),
        "status": ("status", "status do pedido", "situacao", "situação"),
        "titulo": ("titulo", "título"),
        "inventores": ("inventores", "nome_inventores", "nome dos inventores", "nome do inventor"),
        "campus": ("campus",),
        "atributos": ("atributos", "atributo"),
        "id_externo": ("id_externo", "id do sistema"),
        "modalidade_pi": ("modalidade_pi", "modalidade de pi", "modalidade", "tipo"),
        "ano": ("ano",),
        "data_publicacao": ("data_publicacao", "data da publicacao", "data da publicação", "datada publicacao"),
        "data_exame": ("data_exame", "data exame", "exame"),
        "acordo_titularidade": ("acordo_titularidade", "acordo de titularidade"),
        "procuracao": ("procuracao", "procuração"),
        "termo_cessao": ("termo_cessao", "termo de cessao", "termo de cessão"),
        "ipc_classificacao": ("ipc_classificacao", "ipc classificacao", "ipc classificação", "ipc"),
    }

    # Campos adicionais do FORMICT
    aliases.update({
        "inventores_cpf": ("inventores_cpf", "cpf inventores", "cpf dos inventores"),
        "trl": ("trl",),
        "observacoes_formict": ("observacoes_formict", "observações formict", "observacoes formict"),
        "cnae_secao": ("cnae_secao", "setor economico", "setor econômico"),
        "cnae_subclassificacao": ("cnae_subclassificacao", "subclassificacao cnae", "subclassificação cnae"),
        "territorio": ("territorio", "território"),
        "sigilo": ("sigilo",),
        "cotitularidade": ("cotitularidade",),
        "cotitulares": ("cotitulares",),
        "custo_registro": ("custo_registro", "custo de registro"),
        "data_registro": ("data_registro", "data de registro", "data registro"),
        "custo_manutencao_ano_base": ("custo_manutencao_ano_base", "custo manutencao ano base", "custo manutenção ano-base"),
        "data_manutencao": ("data_manutencao", "data manutencao", "data manutenção"),
        "formict_ano_base": ("formict_ano_base", "ano base formict", "ano-base formict"),
    })

    for destino, nomes in aliases.items():
        if destino in df.columns:
            continue
        origem = _coluna_existente(df, *nomes)
        df[destino] = df[origem] if origem else None

    if "id" not in df.columns:
        df["id"] = range(1, len(df) + 1)

    df["modalidade_pi"] = df["modalidade_pi"].apply(normalizar_modalidade)
    df["status"] = df["status"].fillna("Ativo").replace("", "Ativo")

    # Mantém também os campos específicos existentes no schema atual.
    for coluna in ("linguagem", "campo_aplicacao", "tipo_programa"):
        if coluna not in df.columns:
            df[coluna] = None

    return df


def init_database() -> None:
    obter_patentes()


def obter_patentes() -> pd.DataFrame:
    data = _request(
        "GET",
        f"{_endpoint()}?select=*&order=numero_patente.asc",
        headers=_headers(),
    )
    df = pd.DataFrame(data or [])
    return _preparar_patentes(df)


def _patente_url(patente_id: Any) -> str:
    return f"{_endpoint()}?numero_patente=eq.{quote(str(patente_id), safe='')}"


def _payload_patente(dados: Dict[str, Any]) -> Dict[str, Any]:
    """Monta payload usando EXATAMENTE as colunas da tabela public.patentes.

    Importante: não usar nomes de outra arquitetura (pedido, resumo,
    depositante_titular, nome_inventores), pois a tabela oficial do sistema
    usa numero_patente, descricao, titular e inventores.
    """
    payload = {
        "numero_patente": dados.get("numero") or dados.get("numero_patente"),
        "data_deposito": _parse_data(dados.get("data_dep") or dados.get("data_deposito")),
        "data_concessao": _parse_data(dados.get("data_conc") or dados.get("data_concessao")),
        "descricao": dados.get("descricao") or dados.get("resumo"),
        "titular": dados.get("titular") or dados.get("depositante_titular"),
        "gestor": dados.get("gestor"),
        "status": _normalizar_status(dados.get("status_patente") or dados.get("status")),
        "titulo": dados.get("titulo"),
        "inventores": dados.get("inventores") or dados.get("nome_inventores"),
        "campus": dados.get("campus"),
        "atributos": dados.get("atributos"),
        "id_externo": dados.get("id_externo"),
        "modalidade_pi": normalizar_modalidade(dados.get("modalidade_pi")),
        "ano": dados.get("ano"),
        "data_publicacao": _parse_data(dados.get("data_publicacao")),
        "data_exame": _parse_data(dados.get("data_exame")),
        "acordo_titularidade": dados.get("acordo_titularidade"),
        "procuracao": dados.get("procuracao"),
        "termo_cessao": dados.get("termo_cessao"),
        "ipc_classificacao": dados.get("ipc_classificacao"),
        "linguagem": dados.get("linguagem"),
        "campo_aplicacao": dados.get("campo_aplicacao"),
        "tipo_programa": dados.get("tipo_programa"),
        # Dados FORMICT mantidos para compatibilidade/importação; não são mais editados no formulário.
        "trl": dados.get("trl"),
        "observacoes_formict": dados.get("observacoes_formict"),
        "cnae_secao": dados.get("cnae_secao"),
        "cnae_subclassificacao": dados.get("cnae_subclassificacao"),
        "territorio": dados.get("territorio"),
        "sigilo": dados.get("sigilo"),
        "cotitularidade": dados.get("cotitularidade"),
        "cotitulares": dados.get("cotitulares"),
        "custo_registro": dados.get("custo_registro"),
        "data_registro": _parse_data(dados.get("data_registro")),
        "custo_manutencao_ano_base": dados.get("custo_manutencao_ano_base"),
        "data_manutencao": _parse_data(dados.get("data_manutencao")),
        "formict_ano_base": dados.get("formict_ano_base"),
    }
    return {chave: _valor_limpo(valor) for chave, valor in payload.items() if _valor_limpo(valor) is not None}

def _calcular_cronograma(data_dep: str, modalidade_pi: Any) -> List[Dict[str, Any]]:
    inicio = pd.to_datetime(data_dep)
    modalidade = normalizar_modalidade(modalidade_pi)

    if modalidade == "Software":
        itens = [(1, "Taxa única de depósito", 0)]
    elif modalidade == "Desenho Industrial":
        itens = [(1, "Taxa de depósito", 0)]
        itens += [(i + 1, f"{i}º quinquênio", i * 5) for i in range(1, 5)]
    else:
        itens = [(i, f"{i}ª anuidade", i - 1) for i in range(1, 21)]

    cronograma = []
    for numero, descricao, anos in itens:
        ini_ord = inicio + pd.DateOffset(years=anos)
        fim_ord = ini_ord + pd.DateOffset(months=3)
        ini_ext = fim_ord + pd.DateOffset(days=1)
        fim_ext = ini_ext + pd.DateOffset(months=6)
        cronograma.append({
            "id": f"{numero}",
            "numero_patente": None,
            "numero_anuidade": numero,
            "descricao_pagamento": descricao,
            "data_inicio_ordinario": ini_ord.date().isoformat(),
            "data_fim_ordinario": fim_ord.date().isoformat(),
            "data_inicio_extraordinario": ini_ext.date().isoformat(),
            "data_fim_extraordinario": fim_ext.date().isoformat(),
            "data_pagamento": None,
            "status": "pendente",
            "modalidade_pi": modalidade,
        })
    return cronograma


def garantir_pagamentos_existentes() -> None:
    return None


def adicionar_patente(
    numero: str,
    data_dep: str,
    data_conc: Optional[str],
    descricao: Optional[str],
    titular: Optional[str],
    gestor: Optional[str] = None,
    status_patente: str = "Ativo",
    titulo: Optional[str] = None,
    inventores: Optional[str] = None,
    campus: Optional[str] = None,
    atributos: Optional[str] = None,
    id_externo: Optional[str] = None,
    modalidade_pi: Optional[str] = None,
    ano: Optional[int] = None,
    data_publicacao: Optional[str] = None,
    data_exame: Optional[str] = None,
    acordo_titularidade: Optional[str] = None,
    procuracao: Optional[str] = None,
    termo_cessao: Optional[str] = None,
    ipc_classificacao: Optional[str] = None,
) -> Tuple[bool, str]:
    try:
        _request(
            "POST",
            _endpoint(),
            headers=_headers("return=minimal"),
            json=_payload_patente(locals()),
        )
        return True, "PI cadastrada com sucesso no Supabase"
    except Exception as exc:
        return False, f"Erro ao cadastrar PI: {exc}"


def atualizar_patente(patente_id: Any, **dados: Any) -> Tuple[bool, str]:
    try:
        _request(
            "PATCH",
            _patente_url(patente_id),
            headers=_headers("return=minimal"),
            json=_payload_patente(dados),
        )
        return True, "PI atualizada com sucesso no Supabase"
    except Exception as exc:
        return False, f"Erro ao atualizar PI: {exc}"


def salvar_patente_importada(dados: Dict[str, Any], cur: Any = None) -> Tuple[bool, str]:
    try:
        numero = quote(str(dados["numero"]), safe="")
        existente = _request(
            "GET",
            f"{_endpoint()}?select=*&numero_patente=eq.{numero}&limit=1",
            headers=_headers(),
        )
        payload = _payload_patente(dados)

        # Nunca apaga dados já existentes quando a planilha deixar um campo vazio.
        if existente:
            atual = existente[0]
            payload = {k: v for k, v in payload.items() if v is not None and str(v).strip() != ""}
            # Para campos básicos, só atualiza o que veio preenchido.
            _request(
                "PATCH",
                _patente_url(atual["id"]),
                headers=_headers("return=minimal"),
                json=payload,
            )
            return True, "PI existente e atualizada no SUPABASE"

        _request(
            "POST",
            _endpoint(),
            headers=_headers("return=minimal"),
            json=payload,
        )
        return True, "Nova PI importada para o SUPABASE"
    except Exception as exc:
        return False, str(exc)


def obter_anuidades(patente_id: Any) -> pd.DataFrame:
    """Retorna o cronograma da PI mesclado com os pagamentos persistidos no Supabase."""
    df = obter_patentes()
    if df.empty:
        return pd.DataFrame()

    match = df[df["numero_patente"].astype(str) == str(patente_id)]
    if match.empty:
        return pd.DataFrame()

    pi = match.iloc[0]
    data_dep = pi.get("data_deposito")
    if not data_dep:
        return pd.DataFrame()

    resultado = pd.DataFrame(_calcular_cronograma(data_dep, pi.get("modalidade_pi")))
    if resultado.empty:
        return resultado
    resultado["numero_patente"] = patente_id

    # Recupera os registros efetivamente gravados na tabela anuidades.
    try:
        persistidos = _request(
            "GET",
            f"{SUPABASE_URL}/rest/v1/anuidades?select=*&numero_patente=eq.{quote(str(patente_id), safe='')}&order=numero_anuidade.asc",
            headers=_headers(),
        )
    except Exception:
        persistidos = []

    if persistidos:
        df_persistidos = pd.DataFrame(persistidos)
        if "numero_anuidade" in df_persistidos.columns:
            df_persistidos["numero_anuidade"] = pd.to_numeric(
                df_persistidos["numero_anuidade"], errors="coerce"
            )
            resultado["numero_anuidade"] = pd.to_numeric(
                resultado["numero_anuidade"], errors="coerce"
            )
            cols = [c for c in ["status", "data_pagamento"] if c in df_persistidos.columns]
            if cols:
                mapa = df_persistidos.set_index("numero_anuidade")[cols].to_dict("index")
                for idx, row in resultado.iterrows():
                    info = mapa.get(row["numero_anuidade"], {})
                    if info.get("status"):
                        resultado.at[idx, "status"] = info["status"]
                    if info.get("data_pagamento"):
                        resultado.at[idx, "data_pagamento"] = info["data_pagamento"]

    hoje = date.today()

    def normalizar_status(row: pd.Series) -> str:
        if row.get("status") == "nao_pagar":
            return "nao_pagar"
        if row.get("data_pagamento") or row.get("status") == "pago":
            return "pago"
        try:
            if pd.to_datetime(row["data_fim_extraordinario"]).date() < hoje:
                return "vermelho"
        except Exception:
            pass
        return "pendente"

    resultado["status"] = resultado.apply(normalizar_status, axis=1)
    return resultado


def atualizar_status_anuidade(
    patente_id: Any,
    numero_anuidade: int,
    novo_status: str,
    data_pagamento: Optional[str] = None,
) -> None:
    """Atualiza ou cria o registro da anuidade sem depender de constraint UNIQUE."""
    try:
        filtro_id = quote(str(patente_id), safe="")
        existente = _request(
            "GET",
            f"{SUPABASE_URL}/rest/v1/anuidades?select=id&numero_patente=eq.{filtro_id}&numero_anuidade=eq.{int(numero_anuidade)}&limit=1",
            headers=_headers(),
        )

        payload = {
            "numero_patente": patente_id,
            "numero_anuidade": int(numero_anuidade),
            "status": novo_status,
            "data_pagamento": _parse_data(data_pagamento) if data_pagamento else None,
        }

        if existente:
            registro_id = existente[0].get("id")
            if registro_id is None:
                raise RuntimeError("Registro de anuidade encontrado sem ID.")
            _request(
                "PATCH",
                f"{SUPABASE_URL}/rest/v1/anuidades?id=eq.{quote(str(registro_id), safe='')}",
                headers=_headers("return=minimal"),
                json=payload,
            )
        else:
            # Cria somente o registro selecionado, preservando o cronograma calculado pelo app.
            _request(
                "POST",
                f"{SUPABASE_URL}/rest/v1/anuidades",
                headers=_headers("return=minimal"),
                json=payload,
            )
    except Exception as exc:
        raise RuntimeError(
            "Não foi possível registrar o pagamento da anuidade no Supabase. "
            f"Detalhe: {exc}"
        ) from exc

def deletar_patente(patente_id: Any) -> None:
    _request("DELETE", _patente_url(patente_id), headers=_headers("return=minimal"))



def obter_inventores() -> pd.DataFrame:
    data = _request(
        "GET",
        f"{_endpoint('inventores')}?select=*&order=nome.asc",
        headers=_headers(),
    )
    return pd.DataFrame(data or [])


def _localizar_inventor_id(nome: Optional[str] = None, cpf: Optional[str] = None) -> Optional[int]:
    try:
        if cpf:
            q = quote(str(cpf), safe="")
            ex = _request(
                "GET",
                f"{_endpoint('inventores')}?select=id&cpf=eq.{q}&limit=1",
                headers=_headers(),
            )
        elif nome:
            q = quote(str(nome), safe="")
            ex = _request(
                "GET",
                f"{_endpoint('inventores')}?select=id&nome=eq.{q}&limit=1",
                headers=_headers(),
            )
        else:
            return None
        return int(ex[0]["id"]) if ex else None
    except Exception:
        return None


def adicionar_inventor(
    nome: str,
    cpf: Optional[str] = None,
    nacionalidade: Optional[str] = None,
    qualificacao: Optional[str] = None,
    afiliacao: Optional[str] = None,
    endereco_completo: Optional[str] = None,
    cidade: Optional[str] = None,
    estado: Optional[str] = None,
    pais: Optional[str] = None,
    cep: Optional[str] = None,
    telefone: Optional[str] = None,
    email: Optional[str] = None,
    observacoes: Optional[str] = None,
    endereco: Optional[str] = None,
    instituicao: Optional[str] = None,
) -> Tuple[bool, str]:
    """Cadastra um inventor com todos os campos da planilha oficial."""
    try:
        payload = {
            "nome": nome,
            "cpf": cpf,
            "nacionalidade": nacionalidade,
            "qualificacao": qualificacao,
            "afiliacao": afiliacao or instituicao,
            "endereco_completo": endereco_completo or endereco,
            "cidade": cidade,
            "estado": estado,
            "pais": pais,
            "cep": cep,
            "telefone": telefone,
            "email": email,
            "observacoes": observacoes,
            # compatibilidade com versões anteriores:
            "endereco": endereco_completo or endereco,
            "instituicao": afiliacao or instituicao,
        }
        payload = {
            k: _valor_limpo(v)
            for k, v in payload.items()
            if _valor_limpo(v) is not None
        }
        if not payload.get("nome"):
            return False, "Nome do inventor é obrigatório."

        _request(
            "POST",
            _endpoint("inventores"),
            headers=_headers("return=minimal"),
            json=payload,
        )
        return True, "Inventor cadastrado com sucesso."
    except Exception as exc:
        return False, f"Erro ao cadastrar inventor: {exc}"


def atualizar_inventor(inventor_id: Any, **dados: Any) -> Tuple[bool, str]:
    try:
        # Não permitir campos inexistentes no schema.
        permitidos = {
            "nome", "cpf", "nacionalidade", "qualificacao", "afiliacao",
            "endereco_completo", "cidade", "estado", "pais", "cep",
            "telefone", "email", "observacoes", "endereco", "instituicao"
        }
        payload = {
            k: _valor_limpo(v)
            for k, v in dados.items()
            if k in permitidos and _valor_limpo(v) is not None
        }
        _request(
            "PATCH",
            f"{_endpoint('inventores')}?id=eq.{quote(str(inventor_id), safe='')}",
            headers=_headers("return=minimal"),
            json=payload,
        )
        return True, "Inventor atualizado com sucesso."
    except Exception as exc:
        return False, f"Erro ao atualizar inventor: {exc}"


def excluir_inventor(inventor_id: Any) -> Tuple[bool, str]:
    try:
        _request(
            "DELETE",
            f"{_endpoint('inventores')}?id=eq.{quote(str(inventor_id), safe='')}",
            headers=_headers("return=minimal"),
        )
        return True, "Inventor excluído com sucesso."
    except Exception as exc:
        return False, f"Erro ao excluir inventor: {exc}"


def obter_processos_inventor(inventor_id: Any) -> List[str]:
    """Retorna os processos ligados a um inventor pela tabela N:N."""
    try:
        data = _request(
            "GET",
            f"{_endpoint('patente_inventor')}?select=numero_patente&inventor_id=eq.{quote(str(inventor_id), safe='')}&order=numero_patente.asc",
            headers=_headers(),
        ) or []
        return [str(x["numero_patente"]) for x in data if x.get("numero_patente")]
    except Exception:
        return []


def vincular_inventor_pi(numero_patente: str, inventor_id: Any, ordem: Optional[int] = None) -> Tuple[bool, str]:
    """Cria/atualiza um vínculo PI <-> inventor sem apagar os demais vínculos."""
    try:
        if not numero_patente or inventor_id is None:
            return False, "Processo e inventor são obrigatórios."

        if ordem is None:
            existentes = _request(
                "GET",
                f"{_endpoint('patente_inventor')}?select=ordem&numero_patente=eq.{quote(str(numero_patente), safe='')}&order=ordem.desc&limit=1",
                headers=_headers(),
            ) or []
            ordem = (int(existentes[0].get("ordem") or 0) + 1) if existentes else 1

        payload = {
            "numero_patente": str(numero_patente),
            "inventor_id": int(inventor_id),
            "ordem": int(ordem),
        }
        _request(
            "POST",
            _endpoint("patente_inventor"),
            headers=_headers("resolution=merge-duplicates,return=minimal"),
            json=payload,
        )
        return True, "Inventor vinculado à PI."
    except Exception as exc:
        return False, f"Erro ao vincular inventor: {exc}"


def obter_inventores_pi(numero_patente: str) -> pd.DataFrame:
    if not numero_patente:
        return pd.DataFrame()
    url = (
        f"{_endpoint('patente_inventor')}?select=ordem,inventor_id,inventores(*)&"
        f"numero_patente=eq.{quote(str(numero_patente), safe='')}&order=ordem.asc"
    )
    try:
        data = _request("GET", url, headers=_headers()) or []
        rows = []
        for x in data:
            inv = dict(x.get("inventores") or {})
            inv["ordem"] = x.get("ordem")
            inv["inventor_id"] = x.get("inventor_id")
            rows.append(inv)
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def definir_inventores_pi(numero_patente: str, inventor_ids: List[Any]) -> Tuple[bool, str]:
    try:
        _request(
            "DELETE",
            f"{_endpoint('patente_inventor')}?numero_patente=eq.{quote(str(numero_patente), safe='')}",
            headers=_headers("return=minimal"),
        )
        rows = []
        for ordem, iid in enumerate(inventor_ids, 1):
            rows.append({
                "numero_patente": numero_patente,
                "inventor_id": int(iid),
                "ordem": ordem,
            })
        if rows:
            _request(
                "POST",
                _endpoint("patente_inventor"),
                headers=_headers("resolution=merge-duplicates,return=minimal"),
                json=rows,
            )
        return True, "Inventores da PI atualizados."
    except Exception as exc:
        return False, f"Erro ao vincular inventores: {exc}"


def importar_inventores_excel(arquivo_excel) -> List[Tuple[str, bool, str]]:
    """
    Importa a planilha Inventores.xlsx completa.

    Colunas suportadas:
    Código Pedido, Afiliação, Nome Inventor, CPF, Nacionalidade,
    Qualificação, Endereço Completo, CIDADE, ESTADO, PAÍS, CEP,
    Telefone, Observações, e-mail.

    O Código Pedido não é gravado na tabela inventores: ele é usado como
    chave estrangeira na tabela patente_inventor, formando a relação N:N.
    """
    try:
        nome_arquivo = str(getattr(arquivo_excel, "name", "")).lower()
        if nome_arquivo.endswith(".xls"):
            df = pd.read_excel(arquivo_excel, engine="xlrd")
        else:
            df = pd.read_excel(arquivo_excel, engine="openpyxl")
    except Exception as exc:
        return [("ARQUIVO", False, f"Falha ao ler a planilha: {exc}")]

    colunas = {_normalizar_texto(c): c for c in df.columns}

    def col(*names):
        for n in names:
            chave = _normalizar_texto(n)
            if chave in colunas:
                return colunas[chave]
        return None

    mapa = {
        "processo": col("código pedido", "codigo pedido", "processo", "pedido", "numero patente"),
        "afiliacao": col("afiliação", "afiliacao"),
        "nome": col("nome inventor", "nome"),
        "cpf": col("cpf"),
        "nacionalidade": col("nacionalidade"),
        "qualificacao": col("qualificação", "qualificacao"),
        "endereco_completo": col("endereço completo", "endereco completo", "endereço", "endereco"),
        "cidade": col("cidade"),
        "estado": col("estado"),
        "pais": col("país", "pais"),
        "cep": col("cep"),
        "telefone": col("telefone"),
        "observacoes": col("observações", "observacoes"),
        "email": col("e-mail", "email"),
    }

    if not mapa["nome"]:
        return [("PLANILHA", False, "A coluna 'Nome Inventor' é obrigatória.")]
    if not mapa["processo"]:
        return [("PLANILHA", False, "A coluna 'Código Pedido' é obrigatória para criar a relação N:N com patentes.")]

    resultados = []

    for idx, row in df.iterrows():
        linha = idx + 2
        processo = _valor_limpo(row.get(mapa["processo"])) if mapa["processo"] else None
        nome = _valor_limpo(row.get(mapa["nome"])) if mapa["nome"] else None

        if not nome:
            resultados.append((f"Linha {linha}", False, "Nome do inventor não informado."))
            continue
        if not processo:
            resultados.append((str(nome), False, "Código Pedido/processo não informado."))
            continue

        dados = {
            "nome": nome,
            "cpf": _valor_limpo(row.get(mapa["cpf"])) if mapa["cpf"] else None,
            "nacionalidade": _valor_limpo(row.get(mapa["nacionalidade"])) if mapa["nacionalidade"] else None,
            "qualificacao": _valor_limpo(row.get(mapa["qualificacao"])) if mapa["qualificacao"] else None,
            "afiliacao": _valor_limpo(row.get(mapa["afiliacao"])) if mapa["afiliacao"] else None,
            "endereco_completo": _valor_limpo(row.get(mapa["endereco_completo"])) if mapa["endereco_completo"] else None,
            "cidade": _valor_limpo(row.get(mapa["cidade"])) if mapa["cidade"] else None,
            "estado": _valor_limpo(row.get(mapa["estado"])) if mapa["estado"] else None,
            "pais": _valor_limpo(row.get(mapa["pais"])) if mapa["pais"] else None,
            "cep": _valor_limpo(row.get(mapa["cep"])) if mapa["cep"] else None,
            "telefone": _valor_limpo(row.get(mapa["telefone"])) if mapa["telefone"] else None,
            "email": _valor_limpo(row.get(mapa["email"])) if mapa["email"] else None,
            "observacoes": _valor_limpo(row.get(mapa["observacoes"])) if mapa["observacoes"] else None,
        }

        try:
            # Primeiro garante que a PI realmente existe.
            proc = quote(str(processo), safe="")
            pi = _request(
                "GET",
                f"{_endpoint('patentes')}?select=numero_patente&numero_patente=eq.{proc}&limit=1",
                headers=_headers(),
            )
            if not pi:
                resultados.append((
                    f"{nome} / {processo}",
                    False,
                    "Processo não encontrado na tabela patentes; inventor não foi vinculado."
                ))
                continue

            # Localiza pelo CPF quando disponível; caso contrário pelo nome.
            inventor_id = _localizar_inventor_id(dados["nome"], dados["cpf"])

            payload = {
                "nome": dados["nome"],
                "cpf": dados["cpf"],
                "nacionalidade": dados["nacionalidade"],
                "qualificacao": dados["qualificacao"],
                "afiliacao": dados["afiliacao"],
                "endereco_completo": dados["endereco_completo"],
                "cidade": dados["cidade"],
                "estado": dados["estado"],
                "pais": dados["pais"],
                "cep": dados["cep"],
                "telefone": dados["telefone"],
                "email": dados["email"],
                "observacoes": dados["observacoes"],
                # mantém compatibilidade:
                "endereco": dados["endereco_completo"],
                "instituicao": dados["afiliacao"],
            }
            payload = {
                k: _valor_limpo(v)
                for k, v in payload.items()
                if _valor_limpo(v) is not None
            }

            if inventor_id:
                _request(
                    "PATCH",
                    f"{_endpoint('inventores')}?id=eq.{inventor_id}",
                    headers=_headers("return=minimal"),
                    json=payload,
                )
                acao = "Inventor existente atualizado"
            else:
                criado = _request(
                    "POST",
                    _endpoint("inventores"),
                    headers=_headers("return=representation"),
                    json=payload,
                ) or []
                inventor_id = int(criado[0]["id"]) if criado else None
                if inventor_id is None:
                    inventor_id = _localizar_inventor_id(dados["nome"], dados["cpf"])
                acao = "Novo inventor importado"

            if inventor_id is None:
                raise RuntimeError("Não foi possível obter o ID do inventor.")

            ok_vinc, msg_vinc = vincular_inventor_pi(str(processo), inventor_id)
            if not ok_vinc:
                raise RuntimeError(msg_vinc)

            resultados.append((
                f"{nome} / {processo}",
                True,
                f"{acao} e vinculado à PI {processo}."
            ))
        except Exception as exc:
            resultados.append((f"{nome} / {processo}", False, str(exc)))

    return resultados


def exportar_inventores_excel() -> bytes:
    from io import BytesIO

    df = obter_inventores()

    # Acrescenta os processos vinculados para a exportação.
    if not df.empty:
        processos = []
        for _, row in df.iterrows():
            processos.append("; ".join(obter_processos_inventor(row["id"])))
        df["Código Pedido / Processos vinculados"] = processos

    # Ordena as colunas para espelhar a planilha oficial.
    desejadas = [
        "Código Pedido / Processos vinculados",
        "afiliacao",
        "nome",
        "cpf",
        "nacionalidade",
        "qualificacao",
        "endereco_completo",
        "cidade",
        "estado",
        "pais",
        "cep",
        "telefone",
        "observacoes",
        "email",
    ]
    existentes = [c for c in desejadas if c in df.columns]
    if existentes:
        df = df[existentes]

    # Renomeia para os títulos da planilha.
    df = df.rename(columns={
        "Código Pedido / Processos vinculados": "Código Pedido",
        "afiliacao": "Afiliação",
        "nome": "Nome Inventor",
        "cpf": "CPF",
        "nacionalidade": "Nacionalidade",
        "qualificacao": "Qualificação",
        "endereco_completo": "Endereço Completo",
        "cidade": "CIDADE",
        "estado": "ESTADO",
        "pais": "PAÍS",
        "cep": "CEP",
        "telefone": "Telefone",
        "observacoes": "Observações",
        "email": "e-mail",
    })

    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventores")
    return out.getvalue()

def importar_excel(arquivo_excel) -> List[Tuple[str, bool, str]]:
    resultados = []
    try:
        df = pd.read_excel(arquivo_excel)
    except Exception as exc:
        return [("ERRO_GERAL", False, f"Falha ao ler a planilha: {exc}")]

    colunas = {_normalizar_texto(col): col for col in df.columns}
    def campo(*nomes: str) -> Optional[str]:
        for nome in nomes:
            c = colunas.get(_normalizar_texto(nome))
            if c is not None: return c
        return None

    mapa = {
        "numero": campo("processo", "pedido", "numero_patente", "numero de patente", "patente"),
        "data_dep": campo("deposito", "depósito", "data_deposito", "data do deposito"),
        "data_conc": campo("data concessao", "data da concessao", "data da concessão", "data_concessao"),
        "titulo": campo("titulo", "título"),
        "descricao": campo("descricao", "descrição", "resumo"),
        "inventores": campo("inventores", "nome dos inventores", "nome dos inventores"),
        "inventores_cpf": campo("cpf inventores", "cpf dos inventores", "inventores cpf"),
        "titular": campo("titular", "depositante titular", "depositante/ titular", "depositante"),
        "gestor": campo("gestor"),
        "status": campo("status", "status do pedido", "situacao", "situação"),
        "campus": campo("campus"),
        "atributos": campo("atributos", "atributo"),
        "modalidade_pi": campo("modalidade", "modalidade pi", "modalidade de pi", "tipo"),
        "ano": campo("ano"),
        "data_publicacao": campo("data publicacao", "data da publicacao", "datada publicacao"),
        "data_exame": campo("data exame", "data_exame", "exame"),
        "acordo_titularidade": campo("acordo de titularidade", "acordo titularidade"),
        "procuracao": campo("procuracao", "procuração"),
        "termo_cessao": campo("termo de cessao", "termo de cessão", "termo cessao"),
        "ipc_classificacao": campo("ipc classificacao", "ipc classificação", "ipc", "ipc / classificacao"),
        "trl": campo("trl"),
        "observacoes_formict": campo("observacoes", "observações", "observacoes formict", "observações formict"),
        "cnae_secao": campo("cnae secao", "setor economico", "setor econômico"),
        "cnae_subclassificacao": campo("cnae subclassificacao", "subclassificacao cnae", "subclassificação cnae"),
        "territorio": campo("territorio", "território"),
        "sigilo": campo("sigilo"),
        "cotitularidade": campo("cotitularidade"),
        "cotitulares": campo("cotitulares"),
        "custo_registro": campo("custo registro", "custo de registro", "custo_registro"),
        "data_registro": campo("data registro", "data de registro", "data_registro"),
        "custo_manutencao_ano_base": campo("custo manutencao ano base", "custo manutenção ano-base", "custo_manutencao_ano_base"),
        "data_manutencao": campo("data manutencao", "data manutenção", "data_manutencao"),
        "formict_ano_base": campo("ano base", "ano-base", "formict ano base"),
    }

    for idx, row in df.iterrows():
        numero = _valor_limpo(row.get(mapa["numero"])) if mapa["numero"] else None
        data_dep = _parse_data(row.get(mapa["data_dep"])) if mapa["data_dep"] else None
        if not numero or not data_dep:
            resultados.append((str(numero or f"Linha {idx + 2}"), False, "Processo ou depósito ausente.")); continue
        def val(k):
            c=mapa.get(k); return _valor_limpo(row.get(c)) if c else None
        try: ano_val=int(float(val("ano"))) if val("ano") is not None else None
        except Exception: ano_val=None
        try: formict_ano=int(float(val("formict_ano_base"))) if val("formict_ano_base") is not None else None
        except Exception: formict_ano=None
        def money(k):
            v=val(k)
            if v is None:return None
            try:return float(str(v).replace("R$","").replace(".","").replace(",","."))
            except:return v
        dados={
            "numero":str(numero).strip(), "data_dep":data_dep, "data_conc":_parse_data(val("data_conc")),
            "descricao":val("descricao"), "titular":val("titular"), "gestor":val("gestor"),
            "status_patente":_normalizar_status(val("status") or "Ativo"), "titulo":val("titulo"), "inventores":val("inventores"),
            "inventores_cpf":val("inventores_cpf"), "campus":val("campus"), "atributos":val("atributos"),
            "modalidade_pi":normalizar_modalidade(val("modalidade_pi") or "Patente"), "ano":ano_val,
            "data_publicacao":_parse_data(val("data_publicacao")), "data_exame":_parse_data(val("data_exame")),
            "acordo_titularidade":val("acordo_titularidade"), "procuracao":val("procuracao"), "termo_cessao":val("termo_cessao"),
            "ipc_classificacao":val("ipc_classificacao"), "trl":val("trl"), "observacoes_formict":val("observacoes_formict"),
            "cnae_secao":val("cnae_secao"), "cnae_subclassificacao":val("cnae_subclassificacao"), "territorio":val("territorio"),
            "sigilo":val("sigilo"), "cotitularidade":val("cotitularidade"), "cotitulares":val("cotitulares"),
            "custo_registro":money("custo_registro"), "data_registro":_parse_data(val("data_registro")),
            "custo_manutencao_ano_base":money("custo_manutencao_ano_base"), "data_manutencao":_parse_data(val("data_manutencao")),
            "formict_ano_base":formict_ano,
        }
        ok,msg=salvar_patente_importada(dados); resultados.append((dados["numero"],ok,msg))
    return resultados


def analisar_inconsistencias_excel(arquivo_excel) -> List[str]:
    df = pd.read_excel(arquivo_excel)
    colunas = {_normalizar_texto(col): col for col in df.columns}
    problemas = []
    if not any(c in colunas for c in ["processo", "numero_patente", "patente"]):
        problemas.append("Coluna obrigatória 'Processo' não foi encontrada.")
    if not any(c in colunas for c in ["deposito", "data_deposito"]):
        problemas.append("Coluna obrigatória 'Depósito' não foi encontrada.")
    if not any(c in colunas for c in ["modalidade_de_pi", "modalidade_pi", "modalidade", "tipo"]):
        problemas.append("Coluna 'Modalidade de PI' não encontrada; os registros serão tratados como Patente.")
    return problemas

# ============================================================
# ASSISTENTE JURÍDICO NIT
# Persistência do histórico e contexto institucional
# ============================================================

def registrar_consulta_juridica(
    pergunta: str,
    resposta: str,
    documento_nome: Optional[str] = None,
    paginas: Optional[str] = None,
    fontes: Optional[List[Dict[str, Any]]] = None,
    ativo_pi_id: Any = None,
    modelo: Optional[str] = None,
) -> Tuple[bool, str]:
    """Registra uma consulta jurídica na tabela public.historico_consultas_juridicas.

    Estrutura utilizada pela aplicação:
      pergunta, resposta, documento_nome, paginas, fontes,
      ativo_pi_id e modelo.

    O campo created_at é deixado para o DEFAULT do PostgreSQL/Supabase.
    """
    try:
        payload = {
            "pergunta": _valor_limpo(pergunta),
            "resposta": _valor_limpo(resposta),
            "documento_nome": _valor_limpo(documento_nome),
            "paginas": _valor_limpo(paginas),
            "fontes": fontes if fontes else [],
            "ativo_pi_id": _valor_limpo(ativo_pi_id),
            "modelo": _valor_limpo(modelo),
        }

        payload = {
            chave: valor
            for chave, valor in payload.items()
            if valor is not None
        }

        _request(
            "POST",
            _endpoint("historico_consultas_juridicas"),
            headers=_headers("return=minimal"),
            json=payload,
        )
        return True, "Consulta jurídica salva no histórico do Supabase."
    except Exception as exc:
        return False, f"Erro ao salvar consulta jurídica: {exc}"


def obter_historico_consultas_juridicas(
    limite: int = 50,
) -> pd.DataFrame:
    """Retorna as consultas jurídicas mais recentes."""
    try:
        try:
            limite = int(limite)
        except Exception:
            limite = 50
        limite = max(1, min(limite, 500))

        data = _request(
            "GET",
            f"{_endpoint('historico_consultas_juridicas')}?select=*&order=created_at.desc&limit={limite}",
            headers=_headers(),
        )
        return pd.DataFrame(data or [])
    except Exception as exc:
        raise RuntimeError(
            f"Não foi possível consultar o histórico jurídico: {exc}"
        ) from exc


def excluir_consulta_juridica(consulta_id: Any) -> Tuple[bool, str]:
    """Exclui uma consulta específica do histórico jurídico."""
    try:
        if consulta_id is None or str(consulta_id).strip() == "":
            return False, "ID da consulta jurídica não informado."

        filtro = quote(str(consulta_id), safe="")
        _request(
            "DELETE",
            f"{_endpoint('historico_consultas_juridicas')}?id=eq.{filtro}",
            headers=_headers("return=minimal"),
        )
        return True, "Consulta jurídica excluída com sucesso."
    except Exception as exc:
        return False, f"Erro ao excluir consulta jurídica: {exc}"


def buscar_contexto_ativo_pi(ativo_pi_id: Any = None) -> pd.DataFrame:
    """Busca uma PI específica na tabela oficial public.patentes."""
    if ativo_pi_id is None or str(ativo_pi_id).strip() == "":
        return pd.DataFrame()

    try:
        filtro = quote(str(ativo_pi_id), safe="")
        data = _request(
            "GET",
            f"{_endpoint('patentes')}?select=*&numero_patente=eq.{filtro}&limit=1",
            headers=_headers(),
        )
        if not data:
            data = _request(
                "GET",
                f"{_endpoint('patentes')}?select=*&id=eq.{filtro}&limit=1",
                headers=_headers(),
            )
        return _preparar_patentes(pd.DataFrame(data or []))
    except Exception as exc:
        raise RuntimeError(
            f"Não foi possível carregar o contexto da PI: {exc}"
        ) from exc


def obter_obrigacoes_ativo(ativo_id: Any = None) -> pd.DataFrame:
    """Busca as obrigações/anuidades vinculadas a uma PI."""
    if ativo_id is None or str(ativo_id).strip() == "":
        return pd.DataFrame()

    try:
        filtro = quote(str(ativo_id), safe="")
        data = _request(
            "GET",
            f"{_endpoint('anuidades')}?select=*&numero_patente=eq.{filtro}&order=numero_anuidade.asc",
            headers=_headers(),
        )
        return pd.DataFrame(data or [])
    except Exception as exc:
        raise RuntimeError(
            f"Não foi possível carregar as obrigações da PI: {exc}"
        ) from exc
