# Script para rotular chunks já gerados usando Gemini
import os
import logging
import google.generativeai as genai
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import time
from dataset.migracao_dados.gemini_classificacao_utils import classificar_chunk_gemini
from bson import ObjectId

# Carregar variáveis do .env do diretório do projeto
project_root = Path(__file__).parent.parent.parent
env_path = project_root / 'projeto' / '.env'
load_dotenv(env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MONGO_USER = os.getenv("MONGO_USER", "usuario")
MONGO_PASS = os.getenv("MONGO_PASS", "senha")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"

# Definição de constantes
BATCH_SIZE = 1
KEY_NAMES = [
    "GEMINI_API_KEY",
    "GEMINI_API_KEY_4",
    "GEMINI_API_KEY_5",
    "GEMINI_API_KEY_6",
    "GEMINI_API_KEY_7",
    "GEMINI_API_KEY_8",
    "GEMINI_API_KEY_9",
]
NOME_MODELO = 'gemini-2.5-flash'

gemini_keys = []
gemini_key_names = []
for name in KEY_NAMES:
    value = os.getenv(name)
    if value:
        gemini_keys.append(value)
        gemini_key_names.append(name)
if not gemini_keys:
    raise ValueError(f"Nenhuma chave Gemini encontrada no arquivo {env_path}")
current_key_index = 0

def configurar_gemini(key, key_name):
    """Configura o modelo Gemini."""
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(NOME_MODELO)
        
        logger.info(f"Gemini configurado com a chave: {key_name}")
        return model
    except Exception as e:
        logger.error(f"Erro ao configurar Gemini com a chave {key_name}: {str(e)}")
        raise

model = configurar_gemini(gemini_keys[current_key_index], gemini_key_names[current_key_index])

def rotular_chunks_gemini():
    client = None
    global current_key_index, model
    try:
        client = MongoClient(MONGO_URI)
        db = client['dataset_treinamento']
        collection_chunks = db['chunks_sinteticos']
        collection_rotulados = db['chunks_rotulados']
        while True:
            # Busca um batch de chunks pendentes
            chunks = list(collection_chunks.find({
                "status_rotulagem": "pendente",
                "$or": [
                    {"erro_rotulagem": {"$exists": False}},
                    {"erro_rotulagem": False}
                ],
                "nome_modelo": "gemini-2.5-flash"
            }).limit(BATCH_SIZE))
            if not chunks:
                logger.info("Nenhum chunk pendente para rotular. Encerrando.")
                break
            for chunk in chunks:
                tentativas_chave = 0
                sucesso_classificacao = False
                while tentativas_chave < len(gemini_keys):
                    # Avança para a próxima chave (round-robin)
                    current_key_index = (current_key_index + 1) % len(gemini_keys)
                    try:
                        # Garante que o model está sempre atualizado com a chave corrente
                        model = configurar_gemini(gemini_keys[current_key_index], gemini_key_names[current_key_index])
                        logger.info(f"Classificando chunk sintético {chunk['_id']} (chunk original: {chunk.get('id_chunk_original')}, doc original: {chunk.get('id_documento_original')})")
                        classificacao, justificativa, confianca, versao_prompt = classificar_chunk_gemini(
                            chunk["texto_sintetico"],
                            model
                        )
                        # Checa se houve erro de quota ou modelo inesperado
                        erro_quota = False
                        erro_modelo = False
                        if justificativa is not None:
                            if ("quota" in justificativa.lower() or "rate limit" in justificativa.lower() or "bloqueio" in justificativa.lower()):
                                erro_quota = True
                            if ("unexpected model name format" in justificativa.lower()):
                                erro_modelo = True
                        if erro_quota or erro_modelo:
                            logger.warning(f"Quota/modelo excedido para a chave {gemini_key_names[current_key_index]}. Avançando para a próxima chave...")
                            tentativas_chave += 1
                            time.sleep(30)
                            continue
                        # Se não for erro de quota/modelo, segue fluxo normal
                        novo_doc = dict(chunk)
                        novo_doc.pop('_id', None)  # Garante que o MongoDB gere um novo _id
                        # Garante que id_documento_original seja ObjectId e sempre presente
                        id_doc_original = chunk.get("id_documento_original")
                        if id_doc_original is not None and not isinstance(id_doc_original, ObjectId):
                            try:
                                id_doc_original = ObjectId(str(id_doc_original))
                            except Exception:
                                pass
                        novo_doc["id_documento_original"] = id_doc_original
                        # Garante que id_documento_anonimizado seja ObjectId e sempre presente
                        id_doc_anonimizado = chunk.get("id_documento_anonimizado")
                        if id_doc_anonimizado is not None and not isinstance(id_doc_anonimizado, ObjectId):
                            try:
                                id_doc_anonimizado = ObjectId(str(id_doc_anonimizado))
                            except Exception:
                                pass
                        novo_doc["id_documento_anonimizado"] = id_doc_anonimizado
                        novo_doc['id_chunk_sintetico'] = chunk['_id']  # Referência ao _id do chunk sintético

                        # LOG DETALHADO PARA DEPURAÇÃO
                        logger.info(f"DEBUG: classificacao={classificacao} ({type(classificacao)}), confianca={confianca} ({type(confianca)}), justificativa={justificativa}")
                        # Padroniza tipos para evitar erro de comparação
                        try:
                            classificacao_int = int(classificacao)
                        except Exception:
                            classificacao_int = -1
                        try:
                            confianca_float = float(confianca)
                        except Exception:
                            confianca_float = 0.0
                        justificativa_lower = justificativa.lower().strip() if justificativa else ""
                        # Só grava e marca como concluída se a classificação for válida
                        if (
                            classificacao_int not in [-1, None] and
                            confianca_float > 0 and
                            justificativa_lower and
                            "erro ao chamar api" not in justificativa_lower and
                            "unexpected model name format" not in justificativa_lower and
                            "quota" not in justificativa_lower and
                            "rate limit" not in justificativa_lower and
                            "bloqueio" not in justificativa_lower
                        ):
                            novo_doc.update({
                                "classificacao_acesso": classificacao,
                                "justificativa_acesso": justificativa,
                                "confianca_classificacao": confianca,
                                "modelo_rotulador": NOME_MODELO,
                                "versao_prompt_rotulacao": versao_prompt,
                                "data_rotulagem_chunk": datetime.now(),
                                "status_rotulagem": "concluida"
                            })
                            result = collection_rotulados.insert_one(novo_doc)
                            collection_chunks.update_one({"_id": chunk["_id"]}, {"$set": {"status_rotulagem": "concluida"}})
                            logger.info(f"Chunk sintético {chunk['_id']} rotulado e salvo em 'chunks_rotulados' com sucesso. Novo _id: {result.inserted_id}")
                        else:
                            logger.warning(f"Classificação FALHOU para o chunk {chunk['_id']}. Mantendo como pendente para nova tentativa. Justificativa: {justificativa}")
                        sucesso_classificacao = True
                        time.sleep(30)
                        break  # Sai do while de tentativas de chave
                    except Exception as e:
                        logger.error(f"Erro ao rotular chunk {chunk['_id']}: {e}")
                        time.sleep(30)
                        break  # Sai do while de tentativas de chave em caso de erro inesperado
                # Se não conseguiu classificar com nenhuma chave, não grava nada e vai para o próximo chunk
    except Exception as e:
        logger.error(f"Erro geral ao rotular chunks: {e}")
    finally:
        if client:
            client.close()
            logger.info("Conexão com MongoDB fechada.")

if __name__ == "__main__":
    rotular_chunks_gemini() 