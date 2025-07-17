# Documentação Técnica - Dataset CLARA

## 📋 Sumário Executivo

O CLARA (*Classificação Legal de Arquivos e Registros Administrativos*) é um dataset público para classificação de conformidade documental no setor público brasileiro. Esta documentação técnica detalha a arquitetura, metodologia e implementação do projeto.

## 🏗️ Arquitetura do Sistema

### Visão Geral da Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Coleta de     │    │  Extração de    │    │  Anonimização   │
│   Dados         │───▶│  Texto e        │───▶│  e              │
│   (TRT-13)      │    │  Metadados      │    │  Segmentação    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dataset       │◀───│  Rotulagem      │◀───│  Enriquecimento │
│   Final         │    │  e Validação    │    │  (Reformulação  │
│   (JSON)        │    │  (10%)          │    │  + Sintética)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Componentes Principais

1. **Sistema de Coleta**: Extração de documentos do TRT-13 (PROAD-OUV)
2. **Pipeline de Processamento**: Anonimização e segmentação
3. **Sistema de Enriquecimento**: Reformulação contextual e geração sintética
4. **Sistema de Classificação**: Rotulagem semiautomática com LLMs
5. **Sistema de Validação**: Curadoria humana (10% dos registros)
6. **Sistema de Armazenamento**: MongoDB (coleção `chunks_treinamento`)

## 🔧 Metodologia de Construção

### Pipeline de 9 Etapas

#### Etapa 1: Coleta de Dados
- **Fonte**: Sistema PROAD-OUV do TRT-13
- **Critério**: Apenas documentos classificados como "públicos"
- **Formato**: Metadados + conteúdo binário (BLOB)
- **Armazenamento**: Oracle → MongoDB

#### Etapa 2: Extração de Metadados
- **Captura**: Informações estruturadas (assunto, data, classificação)
- **Armazenamento**: MongoDB para processamento modular
- **Rastreabilidade**: Cada etapa gera nova coleção

#### Etapa 3: Extração de Texto
- **Tecnologia**: PyPDF2 + OCR (quando necessário)
- **Abordagem**: Condicional (texto nativo → OCR se baixa qualidade)
- **Formato**: Exclusivamente PDFs

#### Etapa 4: Anonimização
- **API**: Shiva (interna do TRT-13)
- **Técnicas**:
  - NER baseado em Transformer
  - Microsoft Presidio
  - Expressões regulares para identificadores brasileiros
- **Substituição**: Placeholders genéricos (`[NOME]`, `[CPF]`, etc.)

#### Etapa 5: Segmentação
- **Tamanho**: ~200 palavras por chunk
- **Estratégia**: Segmentação não sobreposta
- **Justificativa**: Compatibilidade com modelos Transformer (512 tokens)

#### Etapa 6: Reformulação Contextual
- **Modelo**: Gemini 2.5 Flash
- **Objetivo**: Camada adicional de privacidade + desvinculação das formulações originais
- **Preservação**: Significado e contexto original
- **Alteração**: Estrutura de frases e vocabulário

#### Etapa 7: Geração Sintética
- **Modelo**: Gemini 2.5 Flash
- **Foco**: Classe minoritária (Sigiloso)
- **Estratégia**: Criação de dados (Data Creation)
- **Resultado**: 1.500 trechos adicionais
- **Tipos**: Documentos médicos, jurídicos, de RH

#### Etapa 8: Rotulagem Semiautomática
- **Modelo**: Gemini 2.5 Flash (classificação zero-shot)
- **Saída**: Classe + justificativa + confiança
- **Validação**: Índice Kappa de Cohen = 0.865 ("quase perfeito")
- **Amostra validada**: 10% dos registros

#### Etapa 9: Balanceamento Final
- **Estratégia**: Subamostragem inteligente
- **Critério**: Maior escore de confiança
- **Resultado**: ~2.000 registros por classe (~6.000 total)

## 📊 Especificações Técnicas

### Estrutura de Dados MongoDB

| Característica | Especificação |
|----------------|---------------|
| **Banco de Dados** | `dataset_treinamento` |
| **Coleção Principal** | `chunks_treinamento` |
| **Encoding** | UTF-8 |
| **Classes** | 3 (0: Sigiloso, 1: Interno, 2: Público) |
| **Comprimento Médio** | ~200 palavras |

### Esquema de Dados - chunks_treinamento

```json
{
  "_id": "ObjectId",
  "texto": "string",
  "classificacao_acesso": "integer (0, 1, 2)",
  "fonte": "string"
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

#### Funcionalidades Principais
- **Classificação Semiautomática**: Análise de conformidade documental com LGPD/LAI
- **Parsing Estruturado**: Extração de classificação (0-2), justificativa e confiança
- **Integração MongoDB**: Processamento de chunks pendentes na coleção
- **Logging Detalhado**: Monitoramento de performance e debug
- **Zero-shot Classification**: Uso do Gemini 2.5 Flash

#### Prompt de Classificação
```
Análise de Conformidade Documental - Contexto Administrativo Brasileiro
PRINCÍPIOS-CHAVE:
1. ATO PREPARATÓRIO vs. ATO FINAL
2. INVESTIGAÇÃO E APURAÇÃO = SIGILO
3. DADO PESSOAL EM CONTEXTO ADMINISTRATIVO
4. TRANSPARÊNCIA vs. PRIVACIDADE (LAI/LGPD)
```

### 2. `sintetizador_de_chunks.py`

#### Funcionalidades Principais
- **Reformulação Contextual**: Reescrita completa de textos preservando significado
- **Substituição de Placeholders**: Dados fictícios realistas e plausíveis
- **Preservação de Contexto**: Jargão técnico e nível de sigilo mantidos
- **Controle de Qualidade**: Escore de confiança (0.0-1.0)
- **Limite de Tamanho**: Máximo 200 palavras por texto

#### Configurações
- **Modelo**: Gemini 2.5 Flash
- **Técnica**: Reformulação semântica
- **Objetivo**: Camada adicional de privacidade

### 3. `aumentador_dataset_sigiloso.py`

#### Funcionalidades Principais
- **Geração Sintética**: Criação de dados para classe minoritária
- **Template Estruturado**: Prompt com persona de especialistas (Corregedor-Geral + DPO)
- **Processo em 4 Etapas**: Semente conceitual → Combinação de eixos → Transformação → Geração
- **Controle de Autenticidade**: Jargão técnico, normas, códigos específicos
- **Resultado**: 1.500 trechos adicionais para classe 'Sigiloso'

#### Tipos de Documentos Gerados
- **Licenças médicas sigilosas**
- **Processos disciplinares**
- **Documentos com dados sensíveis LGPD**
- **Investigações internas**

### 4. `rotular_chunks_gemini.py`

#### Funcionalidades Principais
- **Rotulagem Zero-shot**: Uso do Gemini 2.5 Flash
- **Saída Estruturada**: Classe + justificativa + confiança
- **Processamento em Lote**: Chunks pendentes no MongoDB
- **Controle de Qualidade**: Validação baseada em confiança
- **Integração**: Coleção `chunks_treinamento`

## 🔒 Segurança e Privacidade

### Proteções Implementadas

1. **Anonimização Completa**
   - NER com Transformer
   - Microsoft Presidio
   - Regex para identificadores brasileiros

2. **Reformulação Contextual**
   - 100% dos textos reescritos
   - Desvinculação das formulações originais
   - Preservação apenas do significado

3. **Dados Sintéticos**
   - Geração artificial para classe minoritária
   - Nenhum documento original no corpus final

4. **Validação Humana**
   - Verificação de qualidade (10% dos registros)
   - Confirmação de privacidade
   - Sistema web especializado

### Conformidade Legal

- ✅ **LGPD**: Lei Geral de Proteção de Dados
- ✅ **LAI**: Lei de Acesso à Informação
- ✅ **Ciência Aberta**: Licença Creative Commons (CC BY-SA 4.0)
- ✅ **Transparência**: Metodologia documentada

## 📈 Métricas de Qualidade

### Validação Semiautomática
- **Índice Kappa de Cohen**: 0.865 ("quase perfeito")
- **Modelo**: Gemini 2.5 Flash
- **Acurácia**: ~91%
- **Método**: Classificação zero-shot

### Validação Humana
- **Amostra**: 10% dos registros
- **Critério**: Seleção aleatória
- **Responsável**: Pesquisador especialista
- **Sistema**: Interface web customizada

### Validação Experimental
- **Modelo**: Legal-BERT (fine-tuning)
- **F1-Score**: 0.94
- **Divisão**: 80% treino, 10% validação, 10% teste
- **Performance**: Equilibrada entre as 3 classes

## 🚀 Performance e Escalabilidade

### Resultados do Pipeline

| Métrica | Valor |
|---------|-------|
| **Corpus Inicial** | Documentos públicos do TRT-13 |
| **Corpus Após Enriquecimento** | 11.478 trechos |
| **Corpus Final (Balanceado)** | ~6.000 trechos |
| **Distribuição Final** | 2.000 registros por classe |
| **Taxa de Validação** | 10% validação humana |

### Estatísticas do Dataset Final

- **Classe Sigiloso (0)**: ~2.000 registros
- **Classe Interno (1)**: ~2.000 registros  
- **Classe Público (2)**: ~2.000 registros
- **Origem**: Reformulação contextual + geração sintética
- **Compatibilidade**: Modelos Transformer (BERT, RoBERTa, Legal-BERT)

## 🔧 Configuração e Deploy

### Requisitos de Sistema

- **Python**: 3.8+
- **MongoDB**: 4.4+
- **Google Chrome**: Para automação web
- **RAM**: 8GB+
- **Disco**: 20GB+
- **GPU**: Recomendada para fine-tuning

### Configuração de Ambiente

```bash
# Instalação de dependências
pip install -r requirements.txt

# Configuração do MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Configuração das variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais Gemini
```

### Sistema de Validação Humana

```python
# Interface web para curadoria
# Componentes:
# - ID do Documento
# - Fonte (reformulação/sintético)
# - Texto completo
# - Classificação original (LLM)
# - Confiança da classificação
# - Justificativa da IA (XAI)
# - Botões de classificação final
```

## 🧪 Validação Experimental

### Configuração do Experimento

```python
# Modelo: Legal-BERT
# Dataset: CLARA (~6.000 registros)
# Divisão: 80% treino, 10% validação, 10% teste
# Épocas: 3
# Batch size: 16
# Taxa de aprendizado: 2 × 10^-5
# Hardware: GPU NVIDIA A100
```

### Resultados por Classe

| Classe | Precisão | Revocação | F1-Score | Suporte |
|--------|----------|-----------|----------|---------|
| **Sigiloso (0)** | 0.95 | 0.93 | 0.94 | 200 |
| **Interno (1)** | 0.92 | 0.94 | 0.93 | 200 |
| **Público (2)** | 0.94 | 0.94 | 0.94 | 200 |
| **Macro Avg** | - | - | **0.94** | 600 |

## 📚 Referências Técnicas

### Bibliotecas Utilizadas

- **google-generativeai**: API do Google Gemini 2.5 Flash
- **pymongo**: Cliente MongoDB
- **python-dotenv**: Gerenciamento de variáveis de ambiente
- **transformers**: Hugging Face Transformers (Legal-BERT)
- **torch**: PyTorch para fine-tuning
- **pandas**: Manipulação de dados
- **sklearn**: Métricas de avaliação

### APIs Externas

- **Google Gemini API**: Reformulação contextual e classificação
- **MongoDB**: Armazenamento de dados (`chunks_treinamento`)
- **API Shiva**: Anonimização (interna do TRT-13)

### Modelos Utilizados

- **Gemini 2.5 Flash**: Reformulação, geração sintética e classificação
- **Legal-BERT**: Validação experimental (fine-tuning)
- **Transformer NER**: Anonimização (via API Shiva)
- **Microsoft Presidio**: Detecção de PIIs

## 🔮 Roadmap Técnico

### Melhorias Planejadas

- [ ] **Dataset Dinâmico**: Atualizações contínuas
- [ ] **Expansão Interinstitucional**: Outros órgãos públicos
- [ ] **Modelos Especializados**: Fine-tuning para domínio específico
- [ ] **Interface Web**: Classificação interativa
- [ ] **API REST**: Serviço de classificação em tempo real

### Aplicações Futuras

- [ ] **Análise de Risco**: Identificação de padrões de erro
- [ ] **Auditoria Automática**: Verificação de conformidade
- [ ] **Governança de Dados**: Políticas automatizadas
- [ ] **Treinamento Contínuo**: Aprendizado incremental

---

**Nota**: Esta documentação técnica reflete a metodologia descrita no artigo científico "CLARA: Um Dataset Validado e Enriquecido para Classificação de Conformidade Documental no Setor Público Brasileiro". Para a versão mais recente, consulte o repositório oficial. 