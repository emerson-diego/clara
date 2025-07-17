import logging
import time
import os
import google.generativeai as genai
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import json

# Carregar variáveis do .env do diretório do projeto
project_root = Path(__file__).parent.parent.parent
env_path = project_root / 'projeto' / '.env'
load_dotenv(env_path)

MONGO_USER = os.getenv("MONGO_USER", "usuario")
MONGO_PASS = os.getenv("MONGO_PASS", "senha")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"

def classificar_chunk_gemini(texto, model):
    logger = logging.getLogger(__name__)
    VERSAO_PROMPT_CLASSIFICACAO = 'v2.6'
    prompt = f"""
        Você é um Analista Sênior de Classificação de Dados em um órgão público brasileiro, especialista em conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei 13.709/18) e a Lei de Acesso à Informação (LAI - Lei 12.527/11). Sua tarefa é analisar o texto fornecido e determinar o nível de acesso apropriado, seguindo diretrizes rigorosas.

        ### PRINCÍPIOS-CHAVE PARA DECISÃO:
        Antes de classificar, siga estes 3 princípios fundamentais. Estes princípios têm precedência e guiarão a aplicação das diretrizes de classificação subsequentes:
        1.  **ATO PREPARATÓRIO vs. ATO FINAL:** Documentos que subsidiam uma decisão (pareceres, notas técnicas, relatórios de análise) são considerados **preparatórios** e devem, por padrão, ser classificados como **INTERNOS (1)**, mesmo que o ato final (o contrato, a portaria) seja público. O acesso a eles só é garantido após a edição do ato decisório final.
            *Exemplo: Um "Parecer Técnico sobre Edital de Concurso" é interno (1), mesmo que o "Edital de Concurso" final seja público (2).*
        2.  **INVESTIGAÇÃO E APURAÇÃO = SIGILO:** Qualquer documento que faça parte de um processo de investigação, sindicância, ou apuração de irregularidades (relatórios, denúncias, depoimentos) deve ser, por padrão, classificado como **RESTRITO (0)**, devido ao risco de dano grave à investigação e à imagem dos envolvidos, conforme exceções previstas na LAI.
        3.  **DADO PESSOAL EM CONTEXTO ADMINISTRATIVO:** A simples presença de dados pessoais (nome, matrícula, cargo) em um documento de rotina administrativa interna (folha de ponto, despacho de processo, trâmite) justifica a classificação como **INTERNO (1)**, protegendo a privacidade do agente público sem ferir o interesse público geral.
            *Exemplo: O nome de um servidor em uma folha de ponto é interno (1). O nome do gestor que assina um contrato público final é público (2) se for parte essencial do ato.*

        ### DIRETRIZES DE CLASSIFICAÇÃO:
        Avalie o documento e retorne:
        1.  CLASSIFICACAO: Um número inteiro (0, 1 ou 2) para indicar a classificação de acesso:
            * 0 (ACESSO RESTRITO): Documento protegido e acessível apenas por indivíduos com autorização legal específica.
                Aplica-se se contiver:
                * Informações de processos de apuração, sindicância ou disciplinares (PAD), cujo sigilo é essencial para garantir a eficácia da investigação e o direito à ampla defesa.
                * Dados pessoais sensíveis (saúde, etnia, vida sexual, etc.) que, se divulgados, causariam dano significativo.
                * Informações protegidas por sigilo legal (fiscal, bancário, de justiça, etc.).
                * Informações estratégicas sigilosas da instituição.

            * 1 (ACESSO INTERNO): Visível para o público interno, mas não para o externo.
                Aplica-se a:
                * Atos administrativos preparatórios, como Pareceres Jurídicos, Notas Técnicas, Relatórios de Análise de Risco e Despachos que fundamentam uma decisão futura.
                * Documentos de tramitação administrativa que contenham dados pessoais de servidores ou partes, sem interesse público preponderante (ex: processos de férias, folhas de ponto, relatórios de atividades).
                * Informações de gestão interna que não se enquadrem como sigilosas (nível 0).

            * 2 (ACESSO PÚBLICO): Visível para toda a Internet.
                Aplica-se a:
                * Atos administrativos finais e de interesse geral (ex: editais, contratos finalizados e publicados, portarias de nomeação/exoneração, resultados de concursos).
                * Documentos que não contêm dados pessoais ou cujo dado pessoal é parte essencial do caráter público do ato (nome do gestor que assina um contrato público).
                * Importante: Esta classificação NÃO se aplica a documentos preparatórios, mesmo que tratem de temas que se tornarão públicos.

        2.  EXPLICACAO: Em no máximo 3 frases, explique o motivo da classificação. Inicie a explicação identificando a natureza do documento (ex: "Trata-se de um ato preparatório...") e mencione o princípio ou a regra que aplicou.

        3.  CONFIANCA: Um número de ponto flutuante entre 0.0 e 1.0.

        Responda OBRIGATORIAMENTE com um objeto JSON, sem nenhum texto adicional antes ou depois, seguindo o esquema:
        ```json
        {{
        "CLASSIFICACAO": <0, 1 ou 2>,
        "EXPLICACAO": "<explicação curta>",
        "CONFIANCA": <número entre 0.0 e 1.0>
        }}
        Texto para análise:
        {texto}
    """
    try:
        response = model.generate_content(prompt)
        resposta = response.text.strip()
        # Tenta parsear como JSON
        try:
            if resposta.startswith("```json"):
                resposta = resposta[7:]
            if resposta.endswith("```"):
                resposta = resposta[:-3]
            obj = json.loads(resposta)
            classificacao = obj.get("CLASSIFICACAO", -1)
            explicabilidade = obj.get("EXPLICACAO", "Explicação não fornecida ou formato inválido.")
            confianca = obj.get("CONFIANCA", 0.0)
            return classificacao, explicabilidade, confianca, VERSAO_PROMPT_CLASSIFICACAO
        except Exception as e_json:
            logger.warning(f"Falha ao parsear JSON, tentando parsing antigo: {e_json}")
            # Parsing antigo (linhas)
            classificacao = -1
            explicabilidade = "Explicação não fornecida ou formato inválido."
            confianca = 0.0
            linhas_resposta = resposta.splitlines()
            if len(linhas_resposta) >= 3:
                for linha in linhas_resposta:
                    if linha.upper().startswith("CLASSIFICACAO:"):
                        try:
                            valor_str = linha.split(":", 1)[1].strip()
                            valor_int = int(valor_str)
                            if valor_int in [0, 1, 2]:
                                classificacao = valor_int
                            else:
                                classificacao = -1
                                explicabilidade = f"Erro: Classificação '{valor_str}' inválida recebida do modelo."
                                break
                        except Exception:
                            classificacao = -1
                            explicabilidade = "Erro: Formato da classificação inválido."
                            break
                    elif linha.upper().startswith("EXPLICACAO:"):
                        explicabilidade = linha.split(":", 1)[1].strip()
                    elif linha.upper().startswith("CONFIANCA:"):
                        try:
                            confianca_str = linha.split(":", 1)[1].strip()
                            confianca = float(confianca_str)
                            if not 0.0 <= confianca <= 1.0:
                                confianca = max(0.0, min(1.0, confianca))
                        except Exception:
                            confianca = 0.0
            else:
                classificacao = -1
                explicabilidade = "Erro: Resposta do modelo em formato inesperado."
            if classificacao == -1 and not explicabilidade.startswith("Erro:"):
                explicabilidade = "Erro: CLASSIFICACAO não encontrada ou inválida na resposta do modelo."
            return classificacao, explicabilidade, confianca, VERSAO_PROMPT_CLASSIFICACAO
    except Exception as e:
        return -1, f"Erro ao chamar API do Gemini: {str(e)}", 0.0, VERSAO_PROMPT_CLASSIFICACAO

BATCH_SIZE = 1

def rotular_chunks_gemini():
    logger = logging.getLogger(__name__)
    client = None
    try:
        client = MongoClient(MONGO_URI)
        db = client['dataset_treinamento']
        collection_chunks = db['chunks_para_rotular']
        while True:
            # Busca um batch de chunks pendentes
            chunks = list(collection_chunks.find({"status_rotulagem": "pendente"}).limit(BATCH_SIZE))
            if not chunks:
                logger.info("Nenhum chunk pendente para rotular. Encerrando.")
                break
            for chunk in chunks:
                try:
                    logger.info(f"Classificando chunk {chunk['_id']} (doc original: {chunk['id_documento_original']})")
                    classificacao, justificativa, confianca, versao_prompt = classificar_chunk_gemini(
                        chunk["chunk_texto"],
                        model
                    )
                    update = {
                        "classificacao_acesso": classificacao,
                        "justificativa_acesso": justificativa,
                        "confianca_classificacao": confianca,
                        "versao_prompt": versao_prompt,
                        "data_rotulagem_chunk": datetime.now(),
                        "status_rotulagem": "concluida"
                    }
                    collection_chunks.update_one({"_id": chunk["_id"]}, {"$set": update})
                    logger.info(f"Chunk {chunk['_id']} rotulado com sucesso.")
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Erro ao rotular chunk {chunk['_id']}: {e}")
                    collection_chunks.update_one({"_id": chunk["_id"]}, {"$set": {"status_rotulagem": "erro", "erro_rotulagem": str(e)}})
    except Exception as e:
        logger.error(f"Erro geral ao rotular chunks: {e}")
    finally:
        if client:
            client.close()
            logger.info("Conexão com MongoDB fechada.")

if __name__ == "__main__":
    key_names = [
        "GEMINI_API_KEY",
        "GEMINI_API_KEY_4",
        "GEMINI_API_KEY_5",
        "GEMINI_API_KEY_6",
        "GEMINI_API_KEY_7",
        "GEMINI_API_KEY_8",
        "GEMINI_API_KEY_9",
    ]
    gemini_keys = []
    gemini_key_names = []
    for name in key_names:
        value = os.getenv(name)
        if value:
            gemini_keys.append(value)
            gemini_key_names.append(name)
    if not gemini_keys:
        raise ValueError(f"Nenhuma chave Gemini encontrada no arquivo {env_path}")
    current_key_index = 0
    def configurar_gemini(key, key_name):
        """Configura o modelo Gemini."""
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        return model
    model = configurar_gemini(gemini_keys[current_key_index], gemini_key_names[current_key_index])
    # Exemplo de uso interativo
    texto = input("Digite o texto para classificar:\n")
    resultado = classificar_chunk_gemini(texto, model)
    print("Resultado:", resultado)
    rotular_chunks_gemini() 