# Documentação Técnica - Dataset LEIA

## 📋 Sumário Executivo

O LEIA (*Legal-Administrative Enrichment and Information Annotation Dataset*) é um dataset público para classificação de conformidade documental no setor público brasileiro. Esta documentação técnica detalha a arquitetura, metodologia e implementação do projeto.

## 🏗️ Arquitetura do Sistema

### Visão Geral da Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Coleta de     │    │  Pré-           │    │  Enriquecimento │
│   Dados         │───▶│  Processamento  │───▶│  e Geração      │
│   (TRT-13)      │    │  (Anonimização) │    │  Sintética      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dataset       │◀───│  Validação      │◀───│  Rotulagem      │
│   Final         │    │  Humana         │    │  Automática     │
│   (JSON)        │    │  (10%)          │    │  (Gemini)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Componentes Principais

1. **Sistema de Coleta**: Extração de documentos do TRT-13
2. **Pipeline de Processamento**: Anonimização e segmentação
3. **Sistema de Enriquecimento**: Geração de dados sintéticos
4. **Sistema de Classificação**: Rotulagem automática com LLMs
5. **Sistema de Validação**: Curadoria humana
6. **Sistema de Armazenamento**: MongoDB + JSON

## 🔧 Metodologia de Construção

### Pipeline de 9 Etapas

#### Etapa 1: Coleta de Dados
- **Fonte**: Sistema PROAD-OUV do TRT-13
- **Critério**: Apenas documentos classificados como "públicos"
- **Formato**: Metadados + conteúdo binário (BLOB)
- **Armazenamento**: MongoDB

#### Etapa 2: Extração de Texto
- **Tecnologia**: PyPDF2 + OCR (quando necessário)
- **Critério de Qualidade**: Avaliação automática de legibilidade
- **Fallback**: OCR para documentos escaneados

#### Etapa 3: Anonimização
- **API**: Shiva (interna do TRT-13)
- **Técnicas**:
  - NER baseado em Transformer
  - Microsoft Presidio
  - Expressões regulares para identificadores brasileiros
- **Substituição**: Placeholders genéricos (`[NOME]`, `[CPF]`, etc.)

#### Etapa 4: Segmentação
- **Tamanho**: ~200 palavras por chunk
- **Estratégia**: Segmentação não sobreposta
- **Justificativa**: Compatibilidade com modelos Transformer (512 tokens)

#### Etapa 5: Reformulação Contextual
- **Modelo**: Gemini 1.5 Flash
- **Objetivo**: Camada adicional de privacidade
- **Preservação**: Significado e contexto original
- **Alteração**: Estrutura de frases e vocabulário

#### Etapa 6: Geração Sintética
- **Modelo**: Gemini 1.5 Flash
- **Foco**: Classe minoritária (Sigiloso)
- **Tipos**: Documentos médicos, jurídicos, de RH
- **Níveis**: Alto e Médio sigilo

#### Etapa 7: Rotulagem Automática
- **Modelo**: Gemini 2.5 Flash
- **Métricas**: Classificação, justificativa, confiança
- **Validação**: Índice Kappa de Cohen = 0.512

#### Etapa 8: Validação Humana
- **Amostra**: 10% dos registros
- **Critério**: Seleção aleatória
- **Responsável**: Pesquisador especialista

#### Etapa 9: Balanceamento Final
- **Estratégia**: Subamostragem inteligente
- **Critério**: Maior escore de confiança
- **Resultado**: 2.000 registros por classe

## 📊 Especificações Técnicas

### Dataset Final

| Característica | Especificação |
|----------------|---------------|
| **Formato** | JSON |
| **Encoding** | UTF-8 |
| **Tamanho** | ~6.8MB |
| **Registros** | 6.000 |
| **Classes** | 3 (balanceadas) |
| **Comprimento Médio** | ~200 palavras |

### Esquema de Dados

```json
{
  "_id": {
    "$oid": "string"
  },
  "texto": "string",
  "classificacao_acesso": "integer (0, 1, 2)",
  "fonte": "string ('reformulação' ou 'sintético')"
}
```

### Classes de Classificação

| Código | Nome | Descrição | Critérios |
|--------|------|-----------|-----------|
| **0** | Sigiloso | Acesso restrito | Processos de investigação, dados sensíveis, sigilo legal |
| **1** | Interno | Acesso interno | Atos preparatórios, dados pessoais de servidores |
| **2** | Público | Acesso público | Atos finais, interesse geral, transparência |

## 🛠️ Implementação dos Scripts

### 1. `gemini_classificacao_utils.py`

#### Arquitetura
```python
class ClassificadorGemini:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.model = self.configurar_modelo()
    
    def classificar_chunk(self, texto):
        # Implementação da classificação
        pass
```

#### Funcionalidades Principais
- **Gerenciamento de Chaves**: Rotação automática para rate limiting
- **Tratamento de Erros**: Retry com diferentes chaves
- **Parsing Robusto**: Extração de classificação, justificativa e confiança
- **Logging Detalhado**: Monitoramento de performance

#### Prompt de Classificação
```
Você é um Analista Sênior de Classificação de Dados...
PRINCÍPIOS-CHAVE:
1. ATO PREPARATÓRIO vs. ATO FINAL
2. INVESTIGAÇÃO E APURAÇÃO = SIGILO
3. DADO PESSOAL EM CONTEXTO ADMINISTRATIVO
```

### 2. `sintetizador_de_chunks.py`

#### Arquitetura
```python
class SintetizadorChunks:
    def __init__(self, batch_size=10):
        self.batch_size = batch_size
        self.model = self.configurar_gemini()
    
    def processar_lote(self, chunks):
        # Processamento em lotes
        pass
```

#### Funcionalidades Principais
- **Processamento em Lotes**: Eficiência operacional
- **Substituição de Placeholders**: Dados fictícios realistas
- **Preservação de Contexto**: Jargão técnico mantido
- **Controle de Qualidade**: Escore de confiança

#### Prompt de Sintetização
```
Você é um especialista na criação de dados sintéticos...
REGRAS PRINCIPAIS:
1. REESCRITA E DADOS FICTÍCIOS
2. SUBSTITUIÇÃO DE PLACEHOLDERS
3. MANTER CONTEXTO E SENSIBILIDADE
```

### 3. `aumentador_dataset_sigiloso.py`

#### Arquitetura
```python
class GeradorSigiloso:
    def __init__(self):
        self.model = self.configurar_gemini()
        self.niveis_sigilo = ['ALTO', 'MÉDIO']
    
    def gerar_documento_sigiloso(self, inspiracao):
        # Geração baseada em inspiração
        pass
```

#### Funcionalidades Principais
- **Transformação Conceitual**: Pivô inteligente de conceitos
- **Níveis de Sigilo**: Alto e Médio
- **Tipos de Documentos**: Médicos, jurídicos, RH
- **Realismo**: Estrutura e jargão apropriados

#### Tipos de Documentos Gerados

**Documentos Médicos:**
- Laudos de doenças graves (CID-10)
- Atestados médicos detalhados
- Prontuários psiquiátricos

**Documentos Jurídicos:**
- Processos administrativos disciplinares
- Relatórios de investigação
- Comunicações confidenciais

**Documentos de RH:**
- Avaliações de desempenho
- Reclamações de assédio
- Processos internos

### 4. `rotular_chunks_gemini.py`

#### Arquitetura
```python
class PreparadorDataset:
    def __init__(self, db_origem, db_destino):
        self.col_origem = db_origem
        self.col_destino = db_destino
    
    def transferir_melhores_exemplos(self):
        # Seleção por confiança
        pass
```

#### Funcionalidades Principais
- **Seleção Inteligente**: Maior escore de confiança
- **Mapeamento de Fontes**: Reformulação vs. Sintético
- **Preparação Final**: Formato para treinamento

### 5. `revisar_com_gemini-2.5-flash.py`

#### Arquitetura
```python
class RevisorWeb:
    def __init__(self, chrome_port=9222):
        self.chrome_port = chrome_port
        self.driver = self.conectar_chrome()
    
    def revisar_documento(self, texto, prompt):
        # Automação web via Selenium
        pass
```

#### Funcionalidades Principais
- **Automação Web**: Selenium WebDriver
- **Conexão Chrome**: Modo debug remoto
- **Tratamento de Timeouts**: Retry automático
- **Gestão de Sessão**: Recarregamento periódico

#### Configurações Técnicas
- **Porta Debug**: 9222 (configurável)
- **Delay entre documentos**: 60 segundos
- **Recarregamento**: A cada 100 documentos
- **Timeout de resposta**: 120 segundos

## 🔒 Segurança e Privacidade

### Proteções Implementadas

1. **Anonimização Completa**
   - NER com Transformer
   - Microsoft Presidio
   - Regex para identificadores brasileiros

2. **Dados Sintéticos**
   - 100% dos textos são fictícios
   - Reformulação contextual
   - Geração sintética

3. **Validação Humana**
   - Verificação de qualidade
   - Confirmação de privacidade
   - Amostra representativa

### Conformidade Legal

- ✅ **LGPD**: Lei Geral de Proteção de Dados
- ✅ **LAI**: Lei de Acesso à Informação
- ✅ **Ciência Aberta**: Licença Creative Commons
- ✅ **Transparência**: Metodologia documentada

## 📈 Métricas de Qualidade

### Validação Automática
- **Índice Kappa de Cohen**: 0.512 (concordância moderada)
- **Modelo**: Gemini 2.5 Flash
- **Amostra**: Corpus completo

### Validação Humana
- **Amostra**: 10% dos registros
- **Critério**: Seleção aleatória
- **Responsável**: Pesquisador especialista
- **Resultado**: Validação de qualidade e privacidade

### Balanceamento
- **Distribuição Final**: 2.000 registros por classe
- **Estratégia**: Subamostragem inteligente
- **Critério**: Maior escore de confiança

## 🚀 Performance e Escalabilidade

### Otimizações Implementadas

1. **Processamento em Lotes**
   - Tamanho: 10 chunks por lote
   - Redução de overhead de API
   - Melhor utilização de recursos

2. **Gerenciamento de Rate Limiting**
   - Múltiplas chaves de API
   - Rotação automática
   - Retry inteligente

3. **Armazenamento Eficiente**
   - MongoDB para processamento
   - JSON para distribuição
   - Índices otimizados

### Métricas de Performance

| Métrica | Valor |
|---------|-------|
| **Tempo de Processamento** | ~2-3 horas (corpus completo) |
| **Taxa de Sucesso** | >95% |
| **Uso de Memória** | ~2GB |
| **Taxa de Erro** | <5% |

## 🔧 Configuração e Deploy

### Requisitos de Sistema

- **Python**: 3.8+
- **MongoDB**: 4.4+
- **Google Chrome**: Para automação web
- **RAM**: 4GB+
- **Disco**: 10GB+
- **Rede**: Conexão estável com internet

### Configuração de Ambiente

```bash
# Instalação de dependências
pip install -r requirements.txt

# Configuração do MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Configuração do Chrome para automação
google-chrome --remote-debugging-port=9222 --user-data-dir=~/.config/google-chrome/Default

# Configuração das variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais
```

### Monitoramento

```python
import logging
import psutil

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('leia.log'),
        logging.StreamHandler()
    ]
)

# Monitoramento de recursos
def monitorar_sistema():
    return {
        'cpu': psutil.cpu_percent(),
        'memory': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent
    }
```

## 🧪 Testes e Validação

### Testes Unitários

```python
import pytest
from scripts.gemini_classificacao_utils import classificar_chunk_gemini

def test_classificacao_sigiloso():
    texto = "Relatório de investigação disciplinar..."
    resultado = classificar_chunk_gemini(texto, keys, key_names, model)
    assert resultado[0] == 0  # Deve ser classificado como sigiloso

def test_classificacao_publico():
    texto = "Edital de concurso público..."
    resultado = classificar_chunk_gemini(texto, keys, key_names, model)
    assert resultado[0] == 2  # Deve ser classificado como público
```

### Testes de Integração

```python
def test_pipeline_completo():
    # Teste do pipeline completo
    # 1. Carregar dados
    # 2. Processar
    # 3. Validar resultado
    pass
```

### Validação de Qualidade

```python
def validar_qualidade_dataset():
    # Verificar balanceamento
    # Verificar qualidade dos textos
    # Verificar conformidade com LGPD/LAI
    pass
```

## 📚 Referências Técnicas

### Bibliotecas Utilizadas

- **google-generativeai**: API do Google Gemini
- **pymongo**: Cliente MongoDB
- **python-dotenv**: Gerenciamento de variáveis de ambiente
- **selenium**: Automação web
- **pyperclip**: Manipulação de clipboard
- **pandas**: Manipulação de dados
- **numpy**: Computação numérica

### APIs Externas

- **Google Gemini API**: Classificação e geração de texto
- **MongoDB**: Armazenamento de dados
- **API Shiva**: Anonimização (interna do TRT-13)

### Padrões e Metodologias

- **Data Augmentation**: Técnicas de aumento de dados
- **Active Learning**: Validação humana seletiva
- **Privacy by Design**: Privacidade desde o design
- **Explainable AI**: Justificativas para classificações

## 🔮 Roadmap Técnico

### Versão 2.0 (Planejada)

- [ ] **Dataset Dinâmico**: Atualizações contínuas
- [ ] **Modelos Pré-treinados**: Fine-tuning específico
- [ ] **Interface Web**: Classificação interativa
- [ ] **API REST**: Serviço de classificação
- [ ] **Integração**: Sistemas de gestão documental

### Melhorias Técnicas

- [ ] **Cache Inteligente**: Redução de chamadas de API
- [ ] **Processamento Paralelo**: Aceleração de pipeline
- [ ] **Validação Automática**: Verificação contínua
- [ ] **Monitoramento Avançado**: Métricas em tempo real

### Expansão de Domínio

- [ ] **Outros Órgãos**: Expansão interinstitucional
- [ ] **Novos Tipos**: Documentos específicos
- [ ] **Multilíngue**: Suporte a outros idiomas
- [ ] **Tempo Real**: Classificação instantânea

---

**Nota**: Esta documentação técnica é atualizada conforme o desenvolvimento do projeto. Para a versão mais recente, consulte o repositório oficial. 