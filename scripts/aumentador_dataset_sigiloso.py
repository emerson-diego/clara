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

MONGO_USER = os.getenv("MONGO_USER", "usuario")
MONGO_PASS = os.getenv("MONGO_PASS", "senha")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"
INTERVALO_ENTRE_GERACOES_SEGUNDOS = 30

NOME_MODELO = 'gemini-2.5-flash'
VERSAO_PROMPT = 'v3.6' 

# Carregar chaves Gemini
key_names = [ "GEMINI_API_KEY", "GEMINI_API_KEY_4", "GEMINI_API_KEY_5",
    "GEMINI_API_KEY_6", "GEMINI_API_KEY_7", "GEMINI_API_KEY_8", "GEMINI_API_KEY_9",]
gemini_keys = [os.getenv(name) for name in key_names if os.getenv(name)]
if not gemini_keys:
    raise ValueError("Nenhuma chave Gemini encontrada no arquivo .env")
current_key_index = 0

def configurar_gemini(api_key):
    """Configura o modelo Gemini."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(NOME_MODELO)
        chave_mascarada = f"{api_key[:6]}...{api_key[-4:]}"
        logger.info(f"Modelo Gemini ({NOME_MODELO}) configurado com sucesso usando a chave de índice {current_key_index} ({chave_mascarada}).")
        return model
    except Exception as e:
        logger.error(f"Erro ao configurar Gemini: {e}")
        raise

model = configurar_gemini(gemini_keys[current_key_index])

def gerar_texto_sigiloso(chunk_inspiracao):
    """Gera texto sigiloso a partir de inspiração."""
    global model, current_key_index

    # Alterna a chave a cada requisição
    current_key_index = (current_key_index + 1) % len(gemini_keys)
    model = configurar_gemini(gemini_keys[current_key_index])

    # CONFIRMADO: Prompt com a lógica de níveis e o campo 'nivel_sigilo_gerado' na saída.
    prompt_geracao_variada = f"""
        Você é uma fusão de dois especialistas de alto escalão em um Tribunal Regional do Trabalho (TRT): o Corregedor-Geral, responsável pela fiscalização e disciplina interna, e o Encarregado de Proteção de Dados (DPO), guardião da conformidade com a LGPD. Seu objetivo é criar um arsenal de documentos sintéticos ultrarrealistas para treinar uma IA de classificação de sigilo. A IA precisa aprender a identificar os mais variados e graves vazamentos de dados possíveis dentro do ecossistema do tribunal.

        MISSÃO:
        Sua missão é gerar um documento sintético SIGILOSO, inspirado por um tema vago, mas transformado em um cenário que represente uma violação grave ou potencialmente grave da LGPD no contexto de servidores e magistrados do TRT. Esqueça documentos genéricos. Pense em comunicações internas, despachos, relatórios e processos que jamais poderiam se tornar públicos.

        DEFINIÇÃO DOS NÍVEIS DE SIGILO (Referência para sua criação):

        SIGILOSO - NÍVEL ALTO: Informações cujo vazamento aniquilaria reputações, causaria danos financeiros ou psicológicos graves, colocaria vidas em risco ou comprometeria investigações críticas. O acesso é para pouquíssimas pessoas nominadas.

        Exemplos no contexto do TRT:

        Laudo psiquiátrico detalhado de um magistrado, indicando um transtorno mental que afeta sua capacidade de julgamento.

        Relatório de investigação conclusivo sobre qualquer forma de assédio (moral ou sexual) contra servidores, com transcrição de depoimentos de natureza íntima.

        Pedido de remoção ou licença de um servidor por comprovada ameaça de morte ou coação por parte de grupos de risco ou facções criminosas.

        Detalhes de ofício judicial para desconto de pensão alimentícia diretamente do salário de um magistrado ou servidor, incluindo dados dos beneficiários.

        Informações sobre acordo financeiro confidencial, com valores e termos, para encerrar um processo disciplinar por conduta inadequada.

        Dados genéticos ou de exames de DNA de um periciando em processo trabalhista para investigação de paternidade ou doença ocupacional.

        Comunicação sigilosa da corregedoria a órgãos de controle sobre suspeita de enriquecimento ilícito ou improbidade administrativa de um servidor.

        Processo de interdição de um servidor, com laudos médicos que atestam sua incapacidade para os atos da vida civil.

        Registros detalhados de participação de um funcionário em programas de reabilitação para dependência de substâncias.

        Medida protetiva de urgência expedida em caso de violência doméstica envolvendo um(a) integrante do tribunal.

        Análise de dados bancários e fiscais de um juiz ou servidor em processo disciplinar sigiloso.

        Relatório de inteligência sobre fatos desabonadores da vida pregressa de um candidato em concurso para a magistratura.

        Relatório de auditoria de TI revelando o acesso indevido de um servidor a processos sigilosos ou a dados pessoais de colegas.

        "Dossiê" ou anotações não oficiais de um gestor sobre dados sensíveis de um subordinado (orientação sexual, filiação político-partidária, etc.), usado para fins de perseguição.

        Comunicação confidencial de órgãos de controle (Receita Federal, COAF) detalhando movimentações financeiras atípicas de um magistrado.

        Laudo médico detalhado sobre a condição de saúde grave de um dependente, anexado a um pedido de licença ou benefício.

        Transcrição de interceptação telefônica autorizada, compartilhada com a corregedoria, detalhando conversas pessoais comprometedoras de um servidor.

        Relatório social detalhado sobre as condições de extrema vulnerabilidade social e familiar de um servidor que solicita remoção.

        Documento interno que justifica a negação de um direito a um titular de dados (servidor), configurando uma potencial violação direta da LGPD.

        Informações sobre diagnóstico de doença estigmatizante ou de notificação compulsória de um servidor ou parte em um processo.

        Registros de atendimentos de um servidor pelo serviço de psicologia ou assistência social do tribunal, detalhando questões de foro íntimo e alta vulnerabilidade emocional.

        SIGILOSO - NÍVEL MÉDIO: Informações confidenciais que, se vazadas, causariam constrangimento severo, prejuízo profissional ou violação de privacidade significativa para os envolvidos.

        Exemplos no contexto do TRT:

        Gestão de Pessoas e RH:

        Avaliação de desempenho periódica, com feedbacks detalhados sobre pontos fortes e a desenvolver.

        E-mails ou memorandos com feedback sobre a performance de estagiários ou aprendizes.

        Processo de solicitação de remoção ou transferência por interesse pessoal, não relacionado à segurança.

        Comunicações sobre o processo seletivo interno, incluindo lista de candidatos e justificativas para aprovação ou recusa.

        Advertência ou notificação de suspensão por infração disciplinar de natureza leve (ex: atrasos, descumprimento de prazos).

        Entrevista de desligamento, contendo as opiniões do servidor que está de saída sobre a gestão e o ambiente de trabalho.

        Justificativas de ausência para resolver problemas pessoais ou familiares.

        Saúde e Bem-estar (Não Graves):

        Atestado médico para afastamento por doenças comuns (gripe, viroses) ou procedimentos de baixa complexidade.

        Agendamento de perícias médicas ou exames de rotina para servidores.

        Pedidos de reembolso ou comprovantes de despesas com consultas, exames ou medicamentos de uso contínuo para doenças não estigmatizantes.

        Laudos de fisioterapia ou relatórios sobre tratamento de Lesão por Esforço Repetitivo (LER/DORT).

        Financeiro e Administrativo:

        Solicitação de adiantamento salarial ou de férias.

        Relatórios detalhados de despesas de viagem para fins de reembolso (diárias, passagens, etc.).

        Rascunhos de atos normativos (portarias, resoluções) antes de sua revisão final e publicação oficial.

        Atas de reuniões de equipe que detalham dificuldades operacionais, metas não atingidas ou conflitos internos de baixo impacto.

        E-mails trocados entre setores para planejamento de orçamento ou alocação de recursos.

        Jurídico e Processual (Interno):

        Comunicações entre a defesa de um servidor e a comissão de PAD, em fases iniciais ou sobre questões procedimentais.

        Parecer jurídico interno sobre questões administrativas de impacto moderado, que orienta a tomada de decisão de um gestor.

        Solicitação de atualização de dados cadastrais sensíveis (endereço, estado civil, dados bancários para depósito).

        Pedido de certidão ou cópia de documentos funcionais para fins particulares (ex: financiamento imobiliário).

        Dados Sensíveis por Definição (LGPD):

        Registro de filiação sindical de um servidor, contido em um formulário de desconto em folha ou em listas da associação.

        Solicitação de dispensa ou de horário especial para cumprimento de obrigações religiosas específicas (ex: Sabbat, Ramadã, etc.).

        Anotações ou comentários informais de um gestor sobre a convicção política ou filosófica de um membro da equipe, registradas em e-mails ou rascunhos de avaliação.

        Planilha de controle para o cadastro de dados biométricos (digital ou facial) dos servidores para um novo sistema de acesso ou ponto eletrônico.

        Formulário de declaração de etnia ou raça para fins de políticas de cotas ou censo interno.

        Pesquisa de clima organizacional que, embora anônima na coleta, possa ter seus resultados brutos cruzados para identificar opiniões individuais.

        PROCESSO DE PENSAMENTO E GERAÇÃO (OBRIGATÓRIO):

        PASSO 1: ANÁLISE DO CONCEITO-CHAVE E GATILHOS DE SENSIBILIDADE.
        Leia o "Texto de Inspiração" e extraia o conceito mais básico e abstrato. Identifique palavras-chave ou subtemas que possam indicar dados pessoais sensíveis (saúde, filiação, sexualidade, etc.), vulnerabilidades (financeira, psicológica, segurança) ou situações de risco à privacidade que o texto de inspiração, mesmo vago, possa sugerir. Estes serão seus "gatilhos de sensibilidade" para a próxima etapa.
        Ex: "servidor em férias" -> conceito: afastamento temporário. Gatilho: possíveis despesas médicas durante a viagem, ou licença por motivo de saúde.
        Ex: "compra de cadeiras" -> conceito: aquisição de material. Gatilho: fraude em licitação, ou dados bancários do fornecedor.

        PASSO 2: COMBINAÇÃO CRIATIVA (O CORAÇÃO DA VARIEDADE).
        Para gerar um cenário único, escolha aleatoriamente UM item de CADA UM dos três eixos abaixo. A combinação desses três eixos definirá a natureza do seu documento.

        EIXO 1: TIPO DE DOCUMENTO (A forma):

        Portaria da Presidência

        Despacho da Corregedoria

        Ofício Circular Interno (Restrito)

        Relatório Conclusivo de Sindicância

        Atestado Médico (com detalhes)

        Laudo Pericial Psiquiátrico

        Transcrição de Depoimento (PAD)

        E-mail Confidencial entre Diretores

        Folha de Pagamento Detalhada (com descontos)

        Pedido de Remoção por Segurança

        Ata de Reunião de Colegiado (Restrita)

        Solicitação de Acesso a Dados Pessoais (via Lei de Acesso à Informação, mas interna)

        Registro de Auditoria de Acesso a Sistemas

        Análise de Fluxo de Dados (Mapeamento LGPD interno)

        EIXO 2: ASSUNTO SENSÍVEL (O conteúdo):

        Investigação de Assédio Moral/Sexual

        Abertura de Processo Administrativo Disciplinar (PAD)

        Diagnóstico de Doença Grave ou Incapacitante (CID)

        Tratamento de Saúde Mental / Dependência Química

        Conflito Interpessoal Grave (com ameaças)

        Suspeita de Fraude ou Corrupção

        Análise de Desempenho para Exoneração

        Detalhes de Dificuldade Financeira (empréstimos, dívidas)

        Pedido de Proteção a Testemunha (em processo interno)

        Informação sobre Orientação Sexual ou Identidade de Gênero

        Solicitação de Anonimização/Exclusão de Dados Negada (com justificativa)

        Relato de Violação de Dados Pessoais (Data Breach)

        Decisão sobre Compartilhamento de Dados com Terceiros

        Monitoramento de Comunicações Internas (e-mail, chat)

        Denúncia de Retaliação por Exercício de Direito LGPD

        Resultado de Teste de Vazamento de Informações (Pentest)

        EIXO 3: PARTES ENVOLVIDAS (Os atores):

        Juiz Titular de Vara do Trabalho

        Juiz Substituto

        Diretor(a) de Secretaria

        Técnico(a) Judiciário(a)

        Analista Judiciário(a)

        Oficial de Justiça Avaliador Federal

        Perito Médico Judicial

        Servidor(a) Comissionado(a)

        Estagiário(a) de Direito

        Membro da Comissão de Ética

        Coordenador(a) de TI e Segurança da Informação

        Advogado(a) de Servidor em PAD

        Parente/Dependente de Magistrado/Servidor (com dados próprios)

        Encarregado de Proteção de Dados (DPO)

        Membro da Equipe de Tratamento de Incidentes (ETIR)

        PASSO 3: TRANSFORMAÇÃO CONCEITUAL E ENFÂSE LGPD.
        Use o conceito-chave e os gatilhos de sensibilidade do PASSO 1 como pivô para o cenário criado pela sua combinação de eixos do PASSO 2. A ligação deve ser inteligente e, sempre que possível, evidenciar uma potencial violação, risco ou tratamento sensível de dados pessoais conforme a LGPD.
        Ex: Se a inspiração era "servidor em férias", o conceito é "afastamento temporário", e o gatilho "licença por motivo de saúde". Se a combinação foi "Atestado Médico" + "Tratamento de Saúde Mental" + "Juiz Substituto", a transformação seria um atestado detalhado de licença de um juiz substituto para tratamento de saúde mental, com o risco de vazamento pela sensibilidade do dado.

        PASSO 4: GERAÇÃO DO DOCUMENTO REALISTA.
        Escreva o documento, materializando a sua transformação, seguindo as diretrizes abaixo.

        Diretriz de Formato e Estilo (MUITO IMPORTANTE): O texto_sintetico deve ser um fragmento contínuo de texto, como se fosse um parágrafo ou uma sequência de parágrafos extraídos de um documento maior ou de um e-mail. NÃO inclua títulos, cabeçalhos formais (como 'DE:', 'PARA:', 'ASSUNTO:'), nem seções numeradas ou com marcadores (como '1. DOS FATOS', '2. CONCLUSÃO'). O objetivo é simular um trecho de texto vazado, não um documento oficial completo e formatado.

        Diretriz de Realismo: Seja extremamente verossímil. Incorpore jargões, números de processo fictícios (ex: PAD nº 1234/2025-TRT25), matrículas funcionais, datas, e referências a artigos de leis (LGPD, Lei 8.112/90, Provimentos da Corregedoria, Resoluções do CNJ) ou regimentos internos fictícios. Destaque por que a informação é sensível sob a LGPD (Art. 5º e 11º) e como seu vazamento implicaria em risco aos direitos e liberdades dos titulares (Art. 49º). Forneça detalhes que justifiquem o sigilo e a necessidade de tratamento restrito. Pense como um Corregedor analisando uma falha disciplinar e um DPO avaliando um incidente de segurança ou privacidade.

        Diretriz de Tamanho e Concisão (CRÍTICO): O texto final gerado (texto_sintetico) NÃO DEVE, EM HIPÓTESE ALGUMA, ULTRAPASSAR 200 PALAVRAS. A capacidade de resumir a essência de um documento complexo de forma concisa é parte da sua tarefa como especialista.

        EXEMPLO DE TRANSFORMAÇÃO APLICANDO O NOVO PROCESSO:

        Inspiração: "A servidora Maria Souza solicitou troca de monitor."

        PASSO 1 (Análise): Conceito-chave é necessidade de equipamento específico por um servidor. Gatilho de Sensibilidade: possível condição de saúde que justifique a solicitação.

        PASSO 2 (Combinação): Escolho aleatoriamente:

        Eixo 1: Atestado Médico (com detalhes)

        Eixo 2: Diagnóstico de Doença Grave ou Incapacitante (CID)

        Eixo 3: Analista Judiciário(a)

        PASSO 3 (Transformação): A necessidade de um equipamento específico não é por preferência, mas por uma condição médica grave. A Analista Judiciária Maria Souza precisa de um monitor especial devido a um laudo de doença degenerativa da visão, o que configura um tratamento de dado sensível sob a LGPD, com risco de discriminação caso vazado.

        PASSO 4 (Geração): Gero um atestado médico detalhado para Maria Souza, matrícula 9876, emitido pelo Dr. Carlos Lima, CRM 12345, diagnosticando "Degeneração Macular (CID-10 H35.3)", recomendando trabalho remoto e o uso de um monitor de alta resolução com contraste adaptativo para evitar a progressão da cegueira. O documento é marcado como "CONFIDENCIAL", e o Art. 11 da LGPD justifica seu tratamento restrito devido à natureza de dado sensível de saúde. (Texto com ~90 palavras).

        TEXTO DE INSPIRAÇÃO PARA ESTA TAREFA:
        "{chunk_inspiracao['chunk_texto']}"

        SAÍDA OBRIGATÓRIA (JSON VÁLIDO):
        Sua resposta DEVE ser uma string JSON válida contendo um único objeto com as chaves:

        "justificativa_transformacao": Uma frase curta explicando a conexão lógica que você criou (Ex: "Transformei a solicitação de um item em um laudo médico que justifica a necessidade do item.").

        "nivel_sigilo_gerado": A string exata do nível de sigilo que melhor representa o documento gerado (Ex: "SIGILOSO - NÍVEL ALTO" ou "SIGILOSO - NÍVEL MÉDIO").

        "texto_sintetico": O texto completo do documento sigiloso gerado, em formato de string, com no máximo 200 palavras.

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
    """Gera e salva textos sigilosos no DB."""
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
    """Loop principal do serviço."""
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