import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import pyperclip

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Carregar Configurações do .env ---
try:
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / 'projeto' / '.env'
    load_dotenv(dotenv_path=env_path)
    logging.info(f"Carregando configurações de: {env_path}")
except Exception as e:
    logging.error(f"Não foi possível carregar o arquivo .env: {e}")
    exit()

# --- Configurações ---
MONGO_USER = os.getenv("MONGO_USER", "usuario")
MONGO_PASS = os.getenv("MONGO_PASS", "senha")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
DB_NAME = "dataset_treinamento"
COLLECTION_NAME = "chunks_rotulados"
GEMINI_URL = "https://gemini.google.com/app/3fb09e64298c2898"
CHROME_DEBUG_PORT = "9222"
DELAY_ENTRE_DOCUMENTOS = 60 # Segundos de espera entre cada revisão
PROMPT_FILE_PATH = Path(__file__).parent / "prompt_revisao"

# --- Conexão com o Banco de Dados ---
try:
    mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    logging.info("Conexão com o MongoDB estabelecida com sucesso.")
except Exception as e:
    logging.error(f"Não foi possível conectar ao MongoDB: {e}")
    exit()

def conectar_chrome_existente(port):
    """Conecta a uma instância do Chrome em execução com a porta de depuração remota."""
    logging.info(f"Tentando se conectar ao Chrome na porta de depuração {port}...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logging.info("Conexão com o Chrome estabelecida com sucesso.")
        return driver
    except Exception as e:
        logging.error(f"Não foi possível conectar ao Chrome. Verifique se ele foi iniciado com a porta de depuração remota.")
        logging.error(f"Comando sugerido: google-chrome --remote-debugging-port={port} --user-data-dir=~/.config/google-chrome/Default")
        logging.error(f"Erro: {e}")
        return None

def carregar_prompt(caminho_arquivo):
    """Carrega o conteúdo do prompt de um arquivo."""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            prompt = f.read()
        logging.info(f"Prompt carregado com sucesso de {caminho_arquivo}")
        return prompt
    except FileNotFoundError:
        logging.error(f"Arquivo de prompt não encontrado em: {caminho_arquivo}")
        return None
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo de prompt: {e}")
        return None

def obter_documentos_para_revisar():
    """Busca documentos que atendem aos critérios de revisão."""
    query = {
        "confianca_classificacao": {"$gte": 0.85},
        "revisado": {"$ne": True},
        "revisado_2": {"$ne": True}
    }
    documentos = list(collection.find(query))
    logging.info(f"Encontrados {len(documentos)} documentos para revisar.")
    return documentos

def revisar_com_gemini(driver, texto, prompt):
    """Envia um texto para o Gemini e retorna a classificação."""
    try:
        # SELETOR ATUALIZADO para o campo de prompt, com maior tempo de espera
        prompt_box = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.ql-editor[contenteditable="true"]'))
        )
        
        # Limpa o campo simulando a ação de um usuário (Ctrl+A, Backspace)
        prompt_box.send_keys(Keys.CONTROL + "a")
        prompt_box.send_keys(Keys.BACK_SPACE)
        time.sleep(0.5)

        # --- ESTRATÉGIA DE COPIAR/COLAR ---
        texto_completo = f"{prompt}\\n\\n---\\n\\n{texto}"
        pyperclip.copy(texto_completo)
        prompt_box.send_keys(Keys.CONTROL + "v")
        time.sleep(1) # Pausa para garantir que o texto foi colado

        # Adiciona um evento de input para garantir que o site reconheça a mudança.
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }))", prompt_box)
        time.sleep(0.5) # Pequena pausa para o evento propagar
        
        # --- SELETOR ATUALIZADO E MAIS ROBUSTO PARA O BOTÃO ENVIAR ---
        # Procura por um botão dentro da área de entrada que contenha um ícone,
        # uma abordagem mais resistente a mudanças de `data-testid`.
        submit_button_selector = (By.CSS_SELECTOR, '.input-area-container button.send-button')
        submit_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(submit_button_selector)
        )
        
        # --- ESTRATÉGIA DE ESPERA CORRIGIDA ---
        footer_completo_selector = (By.CSS_SELECTOR, 'div.response-footer.complete')
        respostas_completas_antes = driver.find_elements(*footer_completo_selector)
        
        # Usando JavaScript para clicar, que é mais robusto
        driver.execute_script("arguments[0].click();", submit_button)
        
        # Espera até que o número de respostas completas aumente.
        WebDriverWait(driver, 120).until(
            lambda d: len(d.find_elements(*footer_completo_selector)) > len(respostas_completas_antes),
            message="A resposta do Gemini não foi marcada como 'completa' no tempo esperado."
        )
        
        # Agora que a resposta está completa, pegamos o último bloco de resposta.
        response_selector = (By.CSS_SELECTOR, '.response-content .markdown')
        respostas = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(response_selector)
        )
        resultado_texto = respostas[-1].text.strip()
        
        # Tenta converter o resultado para inteiro
        return int(resultado_texto)

    except TimeoutException as e:
        # Se o erro for o timeout específico da resposta, propaga a exceção para ser tratada no loop principal.
        if "A resposta do Gemini não foi marcada como 'completa' no tempo esperado." in e.msg:
            raise
        # Para outros timeouts (ex: elemento não clicável), apenas loga o erro e continua.
        logging.error(f"Tempo de espera excedido: {e.msg}")
        return None
    except (NoSuchElementException, IndexError):
        logging.error("Não foi possível encontrar um dos elementos (prompt, botão ou resposta) na página do Gemini.")
        return None
    except ValueError:
        logging.warning(f"O resultado do Gemini '{resultado_texto}' não é um número inteiro válido. Será marcado como -1.")
        return -1

def main():
    driver = conectar_chrome_existente(CHROME_DEBUG_PORT)
    if not driver:
        return

    prompt_revisao = carregar_prompt(PROMPT_FILE_PATH)
    if not prompt_revisao:
        logging.error("Não foi possível carregar o prompt. Encerrando o script.")
        return

    driver.get(GEMINI_URL)
    time.sleep(5) # Pausa para a carga inicial completa

    documentos = obter_documentos_para_revisar()
    
    for i, doc in enumerate(documentos):
        # A cada 100 documentos, recarrega a página preventivamente para maior estabilidade
        if i > 0 and i % 100 == 0:
            logging.info(f"Marco de {i} documentos atingido. Recarregando a página do Gemini para uma nova sessão.")
            driver.get(GEMINI_URL)
            time.sleep(5)

        doc_id = doc['_id']
        texto_sintetico = doc.get('texto_sintetico')

        logging.info(f"Processando documento {i+1}/{len(documentos)} (ID: {doc_id})")

        if not texto_sintetico:
            logging.warning(f"Documento {doc_id} não possui 'texto_sintetico'. Pulando.")
            continue
            
        classificacao_gemini = None
        max_tentativas = 2
        for tentativa in range(max_tentativas):
            try:
                classificacao_gemini = revisar_com_gemini(driver, texto_sintetico, prompt_revisao)
                # Se a revisão foi bem-sucedida (retornou um número), sai do loop de tentativas
                break
            except TimeoutException as e:
                logging.error(f"Timeout na tentativa {tentativa + 1}/{max_tentativas} para o doc {doc_id}: {e.msg}")
                if tentativa < max_tentativas - 1:
                    logging.info("Recarregando a página para tentar novamente...")
                    driver.get(GEMINI_URL)
                    time.sleep(5)
                else:
                    logging.error(f"Falha final para o doc {doc_id} após {max_tentativas} tentativas. Marcando como erro de automação.")
                    classificacao_gemini = -2 # Código para erro irrecuperável de automação

        # Processa o resultado final após as tentativas
        if classificacao_gemini is not None:
            logging.info(f"Resultado final para o documento: {classificacao_gemini}. Atualizando banco de dados.")
            collection.update_one(
                {'_id': doc_id},
                {'$set': {'classificacao_final_2': classificacao_gemini, 'revisado_2': True}}
            )
            logging.info(f"Aguardando {DELAY_ENTRE_DOCUMENTOS} segundos...")
            time.sleep(DELAY_ENTRE_DOCUMENTOS)
        else:
            # Este caso só deve ocorrer para erros não-timeout (ex: NoSuchElement)
            logging.error(f"Falha não recuperável ao processar documento {doc_id}. Pulando.")

    logging.info("Processo concluído. Todos os documentos foram revisados.")
    driver.quit()

if __name__ == "__main__":
    main() 