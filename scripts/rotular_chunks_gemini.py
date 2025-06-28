import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Carregar variáveis do .env do diretório do projeto
project_root = Path(__file__).parent.parent.parent
env_path = project_root / 'projeto' / '.env'
load_dotenv(env_path)

MONGO_USER = os.getenv("MONGO_USER", "usuario")
MONGO_PASS = os.getenv("MONGO_PASS", "senha")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"

DB_NAME = 'dataset_treinamento'
COLLECTION_ORIGEM = 'chunks_rotulados'
COLLECTION_DESTINO = 'chunks_treinamento'

# Conectar ao MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
col_origem = db[COLLECTION_ORIGEM]
col_destino = db[COLLECTION_DESTINO]

def enviar_chunks_classificacao_2():
    # Buscar os 2050 documentos com maior confianca_classificacao
    cursor = col_origem.find(
        {"$or": [{"classificacao_final": 2}, {"classificacao_final_2": 2}]}
    ).sort("confianca_classificacao", -1).limit(2050)
    chunks = list(cursor)
    if not chunks:
        print("Nenhum documento com classificacao_final == 2 ou classificacao_final_2 == 2 encontrado.")
        return

    novos_chunks = []
    for doc in chunks:
        novo_doc = {}
        novo_doc["texto"] = doc.get("texto_sintetico", "")
        if "classificacao_final" in doc:
            novo_doc["classificacao_acesso"] = doc["classificacao_final"]
        else:
            novo_doc["classificacao_acesso"] = doc.get("classificacao_final_2", "")
        fonte_original = doc.get("fonte", "")
        if fonte_original == "proad_sintetico":
            novo_doc["fonte"] = "reformulação"
        elif fonte_original == "proad_sintetico_sigiloso":
            novo_doc["fonte"] = "criação sintética"
        else:
            novo_doc["fonte"] = fonte_original
        novos_chunks.append(novo_doc)

    print(f"{len(novos_chunks)} documentos seriam inseridos em '{COLLECTION_DESTINO}'.")
    # Descomente a linha abaixo para realizar a inserção
    resultado = col_destino.insert_many(novos_chunks)
    print(f"{len(resultado.inserted_ids)} documentos inseridos em '{COLLECTION_DESTINO}'.")

if __name__ == "__main__":
    enviar_chunks_classificacao_2() 