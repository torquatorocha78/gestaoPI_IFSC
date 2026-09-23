import io
import os
import re
from datetime import datetime

import requests
import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from pypdf import PdfReader

import database as db


MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def _secret(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def _extract_pdf(uploaded_file):
    data = uploaded_file.getvalue()
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[PÁGINA {i}]\n{text.strip()}")
    return "\n\n".join(pages)


def _clean_ai_text(text):
    text = text.strip()
    text = re.sub(r"^```(?:markdown|text)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _call_groq(form_text, meeting_notes):
    api_key = _secret("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada nos Secrets do Streamlit.")

    system = """
Você é um assistente técnico do Núcleo de Inovação Tecnológica – NIT/IFSC.
Elabore uma MINUTA DE PARECER TÉCNICO DE AVALIAÇÃO DE TECNOLOGIA / PATENTEABILIDADE.

REGRAS OBRIGATÓRIAS:
1. Use somente informações efetivamente presentes no formulário e nas observações da reunião.
2. Ignore completamente campos vazios e campos marcados como 'Não aplicável'.
3. Não mencione que campos estavam vazios ou como 'Não aplicável'.
4. Não invente nomes, datas, percentuais, resultados, TRL, empresas, documentos de anterioridade,
   artigos de lei, testes ou características técnicas que não estejam nas fontes fornecidas.
5. As observações da reunião são informações internas do NIT e devem ser usadas para enriquecer
   a análise final quando pertinentes; não trate como fatos externos verificados.
6. Preserve a terminologia, a organização e o nível de detalhe do modelo NIT/IFSC.
7. Quando uma conclusão jurídica depender de pesquisa oficial do INPI, deixe isso expressamente
   como ressalva, sem afirmar resultado de busca que não foi fornecido.
8. Diferencie claramente dados fornecidos pelo inventor/NIT de conclusões técnicas preliminares.
9. Não crie uma tabela de anterioridade com documentos fictícios. Só inclua documentos de anterioridade
   se eles constarem das fontes fornecidas.
10. Gere texto profissional, objetivo e pronto para revisão do servidor do NIT.

ESTRUTURA A SER SEGUIDA, quando houver informação suficiente:
PARECER TÉCNICO DE AVALIAÇÃO DE TECNOLOGIA – NIT/IFSC
I – Identificação
II – Descrição da tecnologia
III – Estado da técnica / anterioridade
IV – Patenteabilidade
V – Maturidade tecnológica
VI – Potencial de mercado
VII – Aspectos de propriedade intelectual
VIII – Riscos e recomendações
IX – Conclusão
PARECER DO NIT

Não force uma seção apenas para preencher o modelo. Se não houver conteúdo suficiente para uma
seção, não invente conteúdo; omita a seção ou registre somente o que for sustentado pelas fontes.
"""

    user = f"""
FORMULÁRIO DE NOTIFICAÇÃO DE CRIAÇÃO/INVENÇÃO:
{form_text}

OBSERVAÇÕES DA REUNIÃO COM O INVENTOR / INFORMAÇÕES COMPLEMENTARES DO NIT:
{meeting_notes.strip() if meeting_notes.strip() else '(Nenhuma informação complementar fornecida.)'}

Elabore a minuta final do parecer seguindo as regras e a estrutura acima.
"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "temperature": 0.1,
            "max_tokens": 10000,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Groq retornou {response.status_code}: {response.text}")
    data = response.json()
    return _clean_ai_text(data["choices"][0]["message"]["content"])


def _add_markdown_like(doc, text):
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            doc.add_paragraph()
            continue
        if line.startswith("### "):
            p = doc.add_heading(line[4:], level=3)
        elif line.startswith("## "):
            p = doc.add_heading(line[3:], level=2)
        elif line.startswith("# "):
            p = doc.add_heading(line[2:], level=1)
        elif re.match(r"^[IVX]+\s*[–-]", line):
            p = doc.add_heading(line, level=2)
        else:
            p = doc.add_paragraph()
            # Basic bold support for **text**.
            parts = re.split(r"(\*\*.*?\*\*)", line)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.bold = True
                else:
                    p.add_run(part)
        p.paragraph_format.space_after = Pt(6)


def gerar_docx(parecer):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Pt(45)
    section.bottom_margin = Pt(45)
    section.left_margin = Pt(55)
    section.right_margin = Pt(55)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("INSTITUTO FEDERAL DE SANTA CATARINA – IFSC\n")
    run.bold = True
    run.font.size = Pt(13)
    run2 = title.add_run("NÚCLEO DE INOVAÇÃO TECNOLÓGICA – NIT")
    run2.bold = True
    run2.font.size = Pt(12)
    doc.add_paragraph()
    _add_markdown_like(doc, parecer)

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


def _save_history(numero_patente, documento_nome, form_text, notes, parecer):
    try:
        payload = {
            "numero_patente": numero_patente or None,
            "documento_nome": documento_nome or None,
            "formulario_extraido": form_text or None,
            "observacoes_reuniao": notes or None,
            "parecer_gerado": parecer or None,
            "modelo": MODEL,
            "criado_em": datetime.now().isoformat(),
        }
        db._request("POST", db._endpoint("pareceres_patenteabilidade"), headers=db._headers("return=minimal"), json=payload)
        return True
    except Exception:
        return False


def _load_history(limit=100, numero_patente=None):
    params = f"select=*&order=criado_em.desc&limit={int(limit)}"
    if numero_patente and numero_patente.strip():
        from urllib.parse import quote
        params += f"&numero_patente=eq.{quote(numero_patente.strip(), safe='')}"
    data = db._request("GET", f"{db._endpoint('pareceres_patenteabilidade')}?{params}", headers=db._headers())
    return data or []


def _delete_history(item_id):
    from urllib.parse import quote
    db._request(
        "DELETE",
        f"{db._endpoint('pareceres_patenteabilidade')}?id=eq.{quote(str(item_id), safe='')}",
        headers=db._headers("return=minimal"),
    )


def _render_history():
    st.divider()
    st.subheader("🗂️ Histórico de pareceres de patenteabilidade")
    st.caption("As análises ficam salvas no Supabase para consulta e resgate posterior, inclusive o formulário extraído e as observações da reunião.")
    busca = st.text_input("🔎 Resgatar por número do processo / PI", key="busca_historico_parecer", placeholder="Digite o número do processo ou deixe vazio para ver os mais recentes")
    try:
        registros = _load_history(100, busca)
        if not registros:
            st.info("Nenhum parecer registrado para este filtro." if busca.strip() else "Nenhum parecer de patenteabilidade registrado ainda.")
            return
        for row in registros:
            rid = row.get("id")
            data = str(row.get("criado_em") or "")[:19].replace("T", " ")
            numero = row.get("numero_patente") or "Sem número informado"
            doc = row.get("documento_nome") or "Sem PDF"
            with st.expander(f"{data} — {numero} — {doc}"):
                st.markdown(f"**Processo / PI:** {numero}")
                st.markdown(f"**Documento:** {doc}")
                st.markdown(f"**Modelo de IA:** {row.get('modelo') or '-'}")
                st.markdown("**Observações da reunião:**")
                st.write(row.get("observacoes_reuniao") or "Nenhuma observação registrada.")
                st.markdown("**Parecer gerado:**")
                st.markdown(row.get("parecer_gerado") or "-")
                with st.expander("📄 Resgatar formulário extraído do PDF"):
                    st.text_area("Conteúdo do formulário", row.get("formulario_extraido") or "", height=300, disabled=True, key=f"form_hist_{rid}")
                if st.button("📥 Carregar este parecer para edição", key=f"load_hist_{rid}"):
                    st.session_state["parecer_patenteabilidade_resultado"] = row.get("parecer_gerado") or ""
                    st.session_state["parecer_patenteabilidade_pdf_text"] = row.get("formulario_extraido") or ""
                    st.session_state["parecer_patenteabilidade_notas_resgatadas"] = row.get("observacoes_reuniao") or ""
                    st.success("Parecer carregado no resultado atual desta sessão.")
                if st.button("🗑️ Excluir este histórico", key=f"del_hist_{rid}"):
                    try:
                        _delete_history(rid)
                        st.success("Histórico excluído.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Erro ao excluir histórico: {exc}")
    except Exception as exc:
        st.error(f"Não foi possível consultar o histórico no Supabase: {exc}")

def render():
    st.title("⚖️ Parecer de Patenteabilidade – NIT/IFSC")
    st.caption("Analisa o formulário de Notificação de Criação/Invenção e as informações complementares registradas pelo NIT.")

    st.info("A IA utiliza somente informações preenchidas. Campos em branco ou marcados como 'Não aplicável' são ignorados e não são mencionados no parecer.")

    arquivo = st.file_uploader("📄 Formulário de Notificação de Criação/Invenção (PDF)", type=["pdf"], key="pdf_patenteabilidade")
    numero = st.text_input("Número do processo / PI (opcional)", key="parecer_numero")
    notas = st.text_area(
        "📝 Observações da reunião com o inventor / Informações complementares do NIT",
        height=260,
        value=st.session_state.pop("parecer_patenteabilidade_notas_resgatadas", ""),
        key="parecer_notas_reuniao",
        placeholder=(
            "Registre aqui informações obtidas na reunião que sejam relevantes para o parecer, por exemplo:\n"
            "• interesse de empresa para futura transferência/licenciamento;\n"
            "• TRL ou nível de maturidade informado;\n"
            "• intenção do inventor ao proteger a tecnologia (transferência, exploração comercial, currículo, pesquisa etc.);\n"
            "• protótipo, testes, validações ou próximos passos relatados;\n"
            "• parceiros, mercado potencial ou estratégia de exploração."
        ),
        help="Este campo é subsídio interno para a IA. Não é uma seção que será simplesmente copiada para o parecer.",
    )

    if not arquivo:
        _render_history()
        return

    try:
        form_text = _extract_pdf(arquivo)
        st.success("PDF carregado e texto extraído com sucesso.")
        with st.expander("🔎 Conferir conteúdo extraído do formulário"):
            st.text_area("Conteúdo", form_text, height=300, disabled=True)
    except Exception as exc:
        st.error(f"Não foi possível ler o PDF: {exc}")
        return

    if st.button("🤖 Realizar análise final e gerar parecer", type="primary", use_container_width=True):
        with st.spinner("A IA está analisando o formulário e as informações da reunião..."):
            try:
                parecer = _call_groq(form_text, notas)
                st.session_state["parecer_patenteabilidade_resultado"] = parecer
                st.session_state["parecer_patenteabilidade_pdf_text"] = form_text
                _save_history(numero, arquivo.name, form_text, notas, parecer)
            except Exception as exc:
                st.error(f"Erro ao gerar o parecer: {exc}")
                return

    parecer = st.session_state.get("parecer_patenteabilidade_resultado")
    if parecer:
        st.divider()
        st.subheader("📋 Minuta do Parecer Técnico")
        st.markdown(parecer)

        docx_bytes = gerar_docx(parecer)
        nome = re.sub(r"[^A-Za-z0-9_-]+", "_", numero or "parecer_patenteabilidade").strip("_")
        st.download_button(
            "📄 Extrair Parecer em Word (.docx)",
            docx_bytes,
            f"Parecer_Patenteabilidade_NIT_IFSC_{nome or 'NIT'}.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

        st.download_button(
            "📝 Baixar texto do parecer (.txt)",
            parecer.encode("utf-8"),
            f"Parecer_Patenteabilidade_NIT_IFSC_{nome or 'NIT'}.txt",
            "text/plain",
            use_container_width=True,
        )

    _render_history()
