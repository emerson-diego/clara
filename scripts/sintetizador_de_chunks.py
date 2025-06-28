import os
import logging
import google.generativeai as genai
from pymongo import MongoClient
import pymongo.errors
import time
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import json
from bson import ObjectId

# --- Configurações Iniciais ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
try:
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / 'projeto' / '.env'
    load_dotenv(env_path)
    logger.info(f"Arquivo .env carregado de: {env_path}")
except Exception as e:
    logger.warning(f"Não foi possível carregar o arquivo .env: {e}. Usando variáveis de ambiente do sistema.")

# Configurações do Processo
MONGO_USER = os.getenv("MONGO_USER", "usuario")
MONGO_PASS = os.getenv("MONGO_PASS", "senha")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"
TAMANHO_LOTE = 10  # Número de chunks a processar por chamada de API
MAX_TENTATIVAS_CHUNK = 3 # Máximo de tentativas para um chunk que falha consistentemente

# Carregar chaves Gemini
key_names = [
    "GEMINI_API_KEY", "GEMINI_API_KEY_4", "GEMINI_API_KEY_5",
    "GEMINI_API_KEY_6", "GEMINI_API_KEY_7", "GEMINI_API_KEY_8", "GEMINI_API_KEY_9",
]
gemini_keys = [os.getenv(name) for name in key_names if os.getenv(name)]
if not gemini_keys:
    raise ValueError("Nenhuma chave Gemini encontrada no arquivo .env")
current_key_index = 0

# --- Funções do Gemini (Otimizadas para Lote) ---

def configurar_gemini(api_key):
    """Configura o modelo Gemini com a chave de API fornecida."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        logger.info("Gemini configurado com sucesso.")
        return model
    except Exception as e:
        logger.error(f"Erro ao configurar Gemini: {e}")
        raise

model = configurar_gemini(gemini_keys[current_key_index])

def gerar_textos_sinteticos_em_lote(lote_chunks):
    """Usa o Gemini para gerar textos sintéticos para um lote de chunks."""
    global current_key_index, model

    # ** PROMPT AJUSTADO PARA NÃO USAR "classificacao_original" **
    prompt = f"""
        Você é um especialista na criação de dados sintéticos para treinamento de IA, especializado em documentos jurídicos e administrativos.
        Sua tarefa é processar a lista de textos JSON abaixo. Para cada texto, crie uma nova versão sintética, seguindo as regras à risca.

        **REGRAS PRINCIPAIS:**
        1.  **REESCRITA E DADOS FICTÍCIOS:** O novo texto deve ser uma paráfrase completa do original, mantendo a estrutura e o jargão do domínio (jurídico/administrativo). Todas as informações específicas (nomes, datas, locais, valores, números de processo, etc.) devem ser substituídas por dados **totalmente fictícios**, mas que sejam realistas e plausíveis dentro do contexto.
        2.  **INSTRUÇÃO SOBRE PLACEHOLDERS (ESSENCIAL):** O texto original contém placeholders anonimizados no formato `<TIPO_DADO>` (ex: `<PESSOA>`, `<ORGANIZAÇÃO>`, `<LOCAL>`, `<DADOS_BANCARIOS>`). Você **DEVE OBRIGATORIAMENTE** substituir cada um desses placeholders por uma informação fictícia correspondente ao tipo indicado. Por exemplo, `<PESSOA>` vira "Mariana Costa", `<ORGANIZAÇÃO>` vira "Soluções Construtivas Ltda.", e assim por diante.
        3.  **MANTER CONTEXTO E SENSIBILIDADE:** A reescrita DEVE preservar o propósito, o tom formal e o nível de sensibilidade do texto original. Um ofício deve continuar parecendo um ofício.
        4.  **SAÍDA ESTRITAMENTE EM JSON:** Sua resposta DEVE ser uma string JSON válida, representando uma lista de objetos, sem nenhum texto ou formatação adicional antes ou depois (sem ```json no início ou no fim).

        ---
        **EXEMPLO DE TRANSFORMAÇÃO:**

        * **ENTRADA (Exemplo de um item da lista):**
            ```json
            {{
            "id_original": "exemplo_id_123",
            "texto_original": "OFÍCIO Nº 101/2024 - <ORGANIZAÇÃO> Requerimento de Pagamento. RECLAMANTE: <PESSOA>. RECLAMADA: <ORGANIZAÇÃO>. Foi arbitrado pelo Juízo, a título de honorários periciais, o valor de R$ 1.500,00."
            }}
            ```

        * **SAÍDA ESPERADA (Como você deve gerar o item correspondente na lista de resultados):**
            ```json
            {{
            "id_original": "exemplo_id_123",
            "texto_sintetico": "COMUNICADO OFICIAL Nº 245/2024 - TRIBUNAL REGIONAL DO TRABALHO. Assunto: Solicitação de Quitação de Verba Honorária. Requerente: Sra. Juliana Almeida. Requerida: Empresa de Logística Brasil Total S.A. Foi estipulado por este Juízo, para cobrir os honorários do perito, a quantia de R$ 1.850,00.",
            "confianca_geracao": 0.98
            }}
            ```
        ---

        **ESTRUTURA DE ENTRADA (POR ITEM):**
        - "id_original": Identificador do chunk.
        - "texto_original": O texto a ser reescrito.

        **ESTRUTURA DE SAÍDA OBRIGATÓRIA (POR ITEM):**
        - "id_original": O mesmo identificador do chunk de entrada.
        - "texto_sintetico": O texto totalmente reescrito com dados fictícios e placeholders substituídos.
        - "confianca_geracao": Um float de 0.0 a 1.0 indicando sua confiança na qualidade da geração.

        ---
        **LOTE DE CHUNKS PARA PROCESSAR:**
        {json.dumps(lote_chunks, indent=2, ensure_ascii=False)}
        """
    
    tentativas_chave = 0
    while tentativas_chave < len(gemini_keys):
        try:
            response = model.generate_content(prompt)
            # Limpeza robusta para garantir que apenas o JSON seja processado
            cleaned_response = response.text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON da resposta do Gemini: {e}\nResposta recebida: {response.text}")
            return None
        except Exception as e:
            if "quota" in str(e).lower() or "rate limit" in str(e).lower() or "blocked" in str(e).lower():
                logger.warning(f"Quota/Limite da chave atual excedido. Tentando próxima chave...")
                tentativas_chave += 1
                current_key_index = (current_key_index + 1) % len(gemini_keys)
                model = configurar_gemini(gemini_keys[current_key_index])
                continue
            else:
                logger.error(f"Erro inesperado na API do Gemini: {e}")
                return None
    
    logger.error("Todas as chaves Gemini falharam ou atingiram o limite.")
    return None

# --- Funções do MongoDB e Processamento ---

def processar_lote_e_salvar(lote_para_processar, col_origem, col_destino):
    """Processa um lote de chunks, salva os resultados e atualiza o status na origem."""
    logger.info(f"Processando um lote de {len(lote_para_processar)} chunks...")
    resultados_lote = gerar_textos_sinteticos_em_lote(lote_para_processar)
    
    if resultados_lote is None:
        logger.error("Falha ao processar o lote. Nenhum resultado recebido da API. Marcando para nova tentativa.")
        for chunk_info in lote_para_processar:
            col_origem.update_one(
                {"_id": ObjectId(chunk_info["id_original"])},
                {"$inc": {"tentativas_sintese": 1}, "$set": {"status_sintese": "pendente"}}
            )
        return

    mapa_resultados = {item['id_original']: item for item in resultados_lote}

    for chunk_original_info in lote_para_processar:
        chunk_id_str = chunk_original_info["id_original"]
        chunk_id_obj = ObjectId(chunk_id_str)
        resultado = mapa_resultados.get(chunk_id_str)

        if resultado and resultado.get("texto_sintetico"):
            try:
                doc_original = col_origem.find_one({"_id": chunk_id_obj})
                if not doc_original:
                    logger.warning(f"Documento original com ID {chunk_id_str} não encontrado. Pulando.")
                    continue
                
                doc_sintetico = {
                    "id_chunk_original": doc_original["_id"],
                    "id_documento_anonimizado": doc_original.get("id_documento_anonimizado"),
                    "id_documento_original": doc_original.get("id_documento_original"),
                    "texto_sintetico": resultado["texto_sintetico"],
                    "fonte": "proad_sintetico", 
                    "nome_modelo": 'gemini-1.5-flash-latest',
                    "versao_prompt": 'v2.1',
                    "confianca_geracao": resultado.get("confianca_geracao"),
                    "data_sintetizacao": datetime.now(),
                    "status_rotulagem": "pendente"
                }
                
                result = col_destino.update_one(
                    {"id_chunk_original": chunk_id_obj},
                    {"$set": doc_sintetico},
                    upsert=True
                )
                if result.upserted_id is not None:
                    logger.info(f"Resultado update_one: matched={result.matched_count}, modified={result.modified_count}, upserted_id={result.upserted_id} (novo documento criado)")
                else:
                    doc = col_destino.find_one({"id_chunk_original": chunk_id_obj})
                    logger.info(f"Resultado update_one: matched={result.matched_count}, modified={result.modified_count}, _id existente={doc.get('_id') if doc else None}")
                
                col_origem.update_one(
                    {"_id": chunk_id_obj},
                    {"$set": {"status_sintese": "sucesso", "tentativas_sintese": 0}}
                )
                logger.info(f"Chunk {chunk_id_str} sintetizado com sucesso.")

            except Exception as e:
                logger.error(f"Erro ao salvar o chunk sintetizado {chunk_id_str}: {e}")
                col_origem.update_one(
                    {"_id": chunk_id_obj},
                    {"$inc": {"tentativas_sintese": 1}, "$set": {"status_sintese": "erro_salvamento"}}
                )

        else:
            update_result = col_origem.update_one(
                {"_id": chunk_id_obj},
                {"$inc": {"tentativas_sintese": 1}, "$set": {"status_sintese": "pendente"}}
            )
            doc_atualizado = col_origem.find_one({"_id": chunk_id_obj})
            tentativas = doc_atualizado.get("tentativas_sintese", 0)
            if tentativas >= MAX_TENTATIVAS_CHUNK:
                col_origem.update_one(
                    {"_id": chunk_id_obj},
                    {"$set": {"status_sintese": "falha_permanente"}}
                )
                logger.error(f"Chunk {chunk_id_str} atingiu o máximo de tentativas e foi marcado como falha permanente.")
            else:
                logger.warning(f"Falha na síntese do chunk {chunk_id_str}. Tentativa {tentativas} de {MAX_TENTATIVAS_CHUNK}.")
    
    logger.info("Lote processado. Aguardando 30 segundos...")
    time.sleep(15)

def processar_chunks_para_sintetizacao():
    """Busca, processa e salva chunks que precisam de sintetização."""
    client = None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client['dataset_treinamento']
        collection_origem = db['chunks']
        collection_destino = db['chunks_sinteticos'] 
        
        collection_destino.create_index("id_chunk_original", unique=True)
        
        logger.info("Iniciando busca por chunks para sintetizar...")
        
        query = {
            "$and": [
                {
                    "$or": [
                        {"status_sintese": {"$in": ["pendente", "erro_salvamento"]}},
                        {"status_sintese": None},
                        {"status_sintese": {"$exists": False}}
                    ]
                },
                {
                    "$or": [
                        {"tentativas_sintese": {"$lt": MAX_TENTATIVAS_CHUNK}},
                        {"tentativas_sintese": {"$exists": False}}
                    ]
                },
                {
                    "$or": [
                        {"erro_rotulagem": {"$exists": False}},
                        {"erro_rotulagem": False}
                    ]
                }
            ]
        }
        
        cursor = collection_origem.find(query).limit(5000)
        lote_atual = []
        
        docs_encontrados = False
        for doc in cursor:
            docs_encontrados = True
            # ** CORREÇÃO: REMOVIDA A LEITURA DE "classificacao_original" **
            lote_atual.append({
                "id_original": str(doc["_id"]),
                "texto_original": doc.get("chunk_texto")
            })

            if len(lote_atual) >= TAMANHO_LOTE:
                processar_lote_e_salvar(lote_atual, collection_origem, collection_destino)
                lote_atual = []
        
        if lote_atual:
            processar_lote_e_salvar(lote_atual, collection_origem, collection_destino)

        if not docs_encontrados:
            logger.info("Nenhum chunk para processar encontrado neste ciclo.")

    except pymongo.errors.ConnectionFailure as e:
        logger.error(f"Erro de conexão com o MongoDB: {e}")
    except Exception as e:
        logger.error(f"Erro geral no processamento: {e}", exc_info=True)
    finally:
        if client:
            client.close()
            logger.info("Conexão com MongoDB fechada.")

def main():
    """Loop principal para executar o processo de sintetização continuamente."""
    logger.info("Serviço de Sintetização de Dados iniciado.")
    while True:
        processar_chunks_para_sintetizacao()
        logger.info("Ciclo de sintetização concluído. Aguardando 1 hora para o próximo.")
        time.sleep(3600)

if __name__ == "__main__":
    main()