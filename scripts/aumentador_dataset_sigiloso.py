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
# Supondo que a função classificar_chunk_gemini exista em outro lugar e não seja usada neste script.
# from dataset.migracao_dados.gemini_classificacao_utils import classificar_chunk_gemini

# --- Configurações Iniciais ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
try:
    # A detecção do project_root pode variar dependendo da estrutura. Ajuste se necessário.
    # Exemplo: se o script está em /projeto/dataset/geracao/script.py
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / 'projeto' / '.env'
    if not env_path.exists():
        # Tentativa alternativa caso a estrutura seja diferente
        project_root = Path(__file__).parent
        env_path = project_root / '.env'

    load_dotenv(env_path)
    logger.info(f"Arquivo .env carregado de: {env_path}")
except Exception as e:
    logger.warning(f"Não foi possível carregar o arquivo .env: {e}. Verifique o caminho.")

# --- Configurações do Processo ---
MONGO_USER = os.getenv("MONGO_USER", "usuario")
MONGO_PASS = os.getenv("MONGO_PASS", "senha")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"
INTERVALO_ENTRE_GERACOES_SEGUNDOS = 10

# --- Constantes de Versionamento ---
NOME_MODELO = 'gemini-1.5-flash-latest'
# ATUALIZADO: Nova versão do prompt para refletir a lógica de níveis.
VERSAO_PROMPT = 'v3.1-geracao-sigilosa-com-niveis' 

# Carregar chaves Gemini
key_names = [ "GEMINI_API_KEY", "GEMINI_API_KEY_4", "GEMINI_API_KEY_5",
    "GEMINI_API_KEY_6", "GEMINI_API_KEY_7", "GEMINI_API_KEY_8", "GEMINI_API_KEY_9",]
gemini_keys = [os.getenv(name) for name in key_names if os.getenv(name)]
if not gemini_keys:
    raise ValueError("Nenhuma chave Gemini encontrada no arquivo .env")
current_key_index = 0

# --- Funções do Gemini ---
def configurar_gemini(api_key):
    """Configura o modelo GenerativeModel do Gemini com a API Key fornecida."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(NOME_MODELO)
        logger.info(f"Modelo Gemini ({NOME_MODELO}) configurado com sucesso.")
        return model
    except Exception as e:
        logger.error(f"Erro ao configurar Gemini: {e}")
        raise

model = configurar_gemini(gemini_keys[current_key_index])

def gerar_texto_sigiloso(chunk_inspiracao):
    """Gera texto sigiloso variado usando um prompt detalhado e estruturado."""
    global model, current_key_index

    # CONFIRMADO: Prompt com a lógica de níveis e o campo 'nivel_sigilo_gerado' na saída.
    prompt_geracao_variada = f"""
        Você é uma fusão de especialistas: um Diretor de RH, um Médico perito e um Advogado corporativo. Seu objetivo combinado é criar documentos sintéticos para treinar IAs na classificação de documentos conforme a LGPD. Sua especialidade é gerar textos que sejam indistinguíveis de documentos reais em seu formato, jargão, estrutura e conteúdo.

        MISSÃO:
        Sua missão é gerar um documento sintético que pertença à categoria SIGILOSO. Para evitar o vício do modelo, você deve criar documentos com diferentes graus de sensibilidade dentro desta categoria. O documento gerado NÃO deve ser público (Internet) nem de circulação interna geral (Intranet).

        DEFINIÇÃO DOS NÍVEIS DE SIGILO (ESCOLHA UM PARA GERAR):

        SIGILOSO - NÍVEL ALTO: Informações ultrassensíveis. O vazamento causaria danos graves, irreparáveis e generalizados a indivíduos, à instituição ou à segurança nacional. O acesso é restrito a um número mínimo de pessoas.

        Exemplos: Laudos médicos de doenças graves (câncer, HIV), prontuários psiquiátricos, detalhes de investigações criminais em andamento, dados genéticos, informações sobre vítimas de abuso.
        SIGILOSO - NÍVEL MÉDIO: Informações confidenciais e restritas. O vazamento causaria constrangimento, dano reputacional, prejuízo financeiro ou operacional, ou violação de privacidade significativa.

        Exemplos: Processos administrativos disciplinares, avaliações de desempenho de funcionários, reclamações de assédio, informações financeiras pessoais (extratos, declarações de imposto de renda), comunicações entre advogados, confirmações de consultas médicas ou resultados de exames de rotina.
        PROCESSO DE PENSAMENTO OBRIGATÓRIO:

        PASSO 1: ANÁLISE DO CONCEITO-CHAVE: Leia o "Texto de Inspiração" e identifique seu tema central (uma pessoa, um item, um evento).

        PASSO 2: DEFINIÇÃO DO NÍVEL DE SIGILO: Escolha aleatoriamente um dos níveis de sigilo definidos acima (NÍVEL ALTO ou NÍVEL MÉDIO) para guiar sua criação. Para um bom balanceamento, varie suas escolhas entre as gerações.

        PASSO 3: TRANSFORMAÇÃO CONCEITUAL: Use o conceito-chave da inspiração para criar um pivô para um novo cenário confidencial que se encaixe perfeitamente no nível de sigilo que você escolheu no passo 2. A ligação deve ser inteligente e conceitual.

        PASSO 4: GERAÇÃO DO DOCUMENTO: Escreva o documento para o novo cenário sigiloso, seguindo rigorosamente as Diretrizes de Realismo abaixo.

        DIRETRIZES DE REALISMO PARA A GERAÇÃO (PASSO 4):

        Ao gerar o texto, simule um documento real com o máximo de verossimilhança. Isso inclui:

        Estrutura e Formato: Use elementos como cabeçalho (ex: "MEMORANDO INTERNO", "ATESTADO MÉDICO"), número de protocolo/processo, datas, identificação das partes envolvidas (nome, CPF/matrícula fictícios) e campos para assinatura.
        Linguagem e Jargão: Adote um tom formal, burocrático e impessoal. Utilize jargão técnico apropriado ao contexto.
        Saúde: Inclua termos médicos, o código da Classificação Internacional de Doenças (CID-10) correspondente ao diagnóstico, nome e CRM fictício do médico, e descrição técnica do quadro ou recomendação (ex: "necessita de afastamento de suas atividades laborais por 15 (quinze) dias").
        Jurídico/RH: Faça referência a artigos fictícios de regimentos internos, políticas da empresa ou artigos da CLT. Descreva os fatos de forma objetiva e detalhada, e indique os próximos passos formais (ex: "instaurar comissão de inquérito", "apresentar defesa prévia").
        Conteúdo Detalhado: Não seja genérico. Forneça detalhes críveis que justifiquem a classificação de sigilo. Em vez de "problema de saúde", gere um "diagnóstico de Apendicite Aguda (CID-10 K35.8)". Em vez de "mau comportamento", descreva uma "infração ao Art. 482, alínea 'b', da CLT - incontinência de conduta".
        
        DIRETRIZ DE CONTEÚDO (VIÉS TEMÁTICO):
        Com maior probabilidade (~60-70% das vezes): Gere documentos relacionados à saúde, aplicando a variedade de Nível Alto (laudos graves) e Nível Médio (agendamentos, exames de rotina, atestados detalhados).
        Com menor probabilidade (~30-40% das vezes): Gere outros temas sigilosos (processos de RH, questões jurídicas, financeiras, etc.).

        EXEMPLO DE TRANSFORMAÇÃO:

        Inspiração: "Aviso de férias do servidor João da Silva."
        PASSO 1 (Análise): Conceito-chave é o afastamento do servidor João da Silva.
        PASSO 2 (Escolha): Decido gerar um documento SIGILOSO - NÍVEL MÉDIO.
        PASSO 3 (Transformação): O afastamento pode estar ligado a um processo interno. Transformo em uma notificação de RH.
        PASSO 4 (Geração): Gero uma "Notificação de Abertura de Processo Administrativo Disciplinar (PAD) contra o servidor João da Silva por uso indevido de recursos", incluindo número do processo, data e descrição da acusação.
        TEXTO DE INSPIRAÇÃO PARA ESTA TAREFA:
        "{chunk_inspiracao['chunk_texto']}"

        SAÍDA OBRIGATÓRIA (JSON VÁLIDO):
        Sua resposta DEVE ser uma string JSON válida contendo um único objeto com as chaves:

        "justificativa_transformacao": Uma frase curta explicando a conexão lógica que você criou.
        "nivel_sigilo_gerado": A string exata do nível escolhido (ex: "SIGILOSO - NÍVEL ALTO" ou "SIGILOSO - NÍVEL MÉDIO").
        "texto_sintetico": O texto do documento sigiloso gerado, em formato de string.
        "confianca_geracao_sintetica": Um número de 0.0 a 1.0.
        GERE AGORA SEU DOCUMENTO SIGILOSO SEGUINDO TODOS OS PASSOS:
        """
    

    tentativas_chave = 0
    while tentativas_chave < len(gemini_keys):
        try:
            response = model.generate_content(prompt_geracao_variada)
            # Limpeza robusta para extrair o JSON da resposta
            cleaned_response = response.text.strip()
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = cleaned_response[json_start:json_end]
                return json.loads(json_str)
            else:
                raise json.JSONDecodeError("Nenhum JSON válido encontrado.", cleaned_response, 0)
        except Exception as e:
            if "quota" in str(e).lower() or "rate limit" in str(e).lower() or "blocked" in str(e).lower():
                logger.warning(f"Quota/Limite da chave {current_key_index + 1} excedido. Tentando próxima chave...")
                tentativas_chave += 1
                current_key_index = (current_key_index + 1) % len(gemini_keys)
                model = configurar_gemini(gemini_keys[current_key_index])
                continue # Tenta novamente com a nova chave
            else:
                logger.error(f"Erro inesperado na API do Gemini: {e}")
                return None
    logger.error("Todas as chaves Gemini falharam ou atingiram o limite.")
    return None

def processo_de_aumento(client):
    """Busca um chunk, gera um texto sigiloso variado e salva no DB."""
    try:
        db = client['dataset_treinamento']
        collection_chunks = db['chunks']
        collection_sigilosos = db['chunks_sigilosos']
        
        logger.info("Procurando um chunk de inspiração em 'chunks'...")
        query_busca = {
            "usado_para_geracao_sigilosa": {"$ne": True},
            "$or": [
                {"erro_rotulagem": {"$exists": False}},
                {"erro_rotulagem": False}
            ]
        }
        pipeline = [{"$match": query_busca}, {"$sample": {"size": 1}}]
        chunk_inspiracao = next(collection_chunks.aggregate(pipeline), None)

        if not chunk_inspiracao:
            logger.warning("Nenhum chunk novo encontrado para gerar dados sigilosos.")
            return

        chunk_id_original = chunk_inspiracao["_id"]
        logger.info(f"Chunk de inspiração encontrado: {chunk_id_original}")

        resultado_geracao = gerar_texto_sigiloso(chunk_inspiracao)

        if resultado_geracao and resultado_geracao.get("texto_sintetico"):
            # --- ATUALIZADO: Lógica final para criar o documento sigiloso ---
            doc_sigiloso = {
                "id_chunk_original": chunk_id_original,
                "confianca_geracao": resultado_geracao.get("confianca_geracao_sintetica"),
                # Novos campos sendo salvos no DB
                "justificativa_transformacao": resultado_geracao.get("justificativa_transformacao"),
                "nivel_sigilo_gerado": resultado_geracao.get("nivel_sigilo_gerado"),
                "data_sintetizacao": datetime.now(),
                "fonte": "proad_sintetico_sigiloso",
                "id_documento_anonimizado": chunk_inspiracao.get("id_documento_anonimizado"),
                "id_documento_original": chunk_inspiracao.get("id_documento_original"),
                "status_rotulagem": "pendente", 
                "texto_sintetico": resultado_geracao["texto_sintetico"],
                "nome_modelo": NOME_MODELO,
                "versao_prompt": VERSAO_PROMPT
            }
            insert_result = collection_sigilosos.insert_one(doc_sigiloso)
            logger.info(f"Novo chunk sigiloso gerado e inserido com o ID: {insert_result.inserted_id}")

            # Marca o chunk original como utilizado
            collection_chunks.update_one(
                {"_id": chunk_id_original},
                {"$set": {"usado_para_geracao_sigilosa": True}}
            )
            logger.info(f"Chunk de inspiração {chunk_id_original} marcado como utilizado.")
        else:
            logger.error(f"Falha ao gerar texto sintético para o chunk de inspiração {chunk_id_original}.")
    except Exception as e:
        logger.error(f"Erro geral no processo de aumento: {e}", exc_info=True)

def main():
    """Loop principal que executa o processo de aumento de dados em intervalos."""
    while True:
        client = None
        try:
            logger.info("Iniciando ciclo de aumento de dados sigilosos...")
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
            client.admin.command('ping')
            logger.info("Conexão com MongoDB estabelecida com sucesso.")
            processo_de_aumento(client)
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"Não foi possível conectar ao MongoDB: {e}")
        finally:
            if client:
                client.close()
                logger.info("Conexão com MongoDB fechada.")
        logger.info(f"Ciclo concluído. Aguardando {INTERVALO_ENTRE_GERACOES_SEGUNDOS} segundos.")
        time.sleep(INTERVALO_ENTRE_GERACOES_SEGUNDOS)

if __name__ == "__main__":
    main()