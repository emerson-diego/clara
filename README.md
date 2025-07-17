# CLARA: Dataset para Classificação de Conformidade Documental

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📋 Visão Geral

O **CLARA** (*Classificação Legal de Arquivos e Registros Administrativos*) é um dataset público e balanceado para classificação de conformidade documental no setor público brasileiro. O projeto aborda o delicado equilíbrio entre transparência (Lei de Acesso à Informação - LAI) e proteção de dados (Lei Geral de Proteção de Dados - LGPD).

### 🎯 Objetivos

- Fornecer um dataset balanceado para treinamento de modelos de IA
- Facilitar a automação da classificação documental no setor público
- Garantir total privacidade através de reformulação contextual e dados sintéticos
- Fomentar pesquisas em Processamento de Linguagem Natural (PLN)

### 🔑 Características Principais

- **~6.000 registros** balanceados (~2.000 por classe)
- **3 classes de acesso**: Sigiloso (0), Interno (1), Público (2)
- **100% dados fictícios** para proteção de privacidade
- **Compatível** com modelos Transformer (BERT, RoBERTa, Legal-BERT)
- **Validação humana** em 10% dos registros
- **F1-Score de 0.94** com Legal-BERT

## 📊 Estrutura do Dataset

### Classes de Classificação

| Classe | Código | Descrição |
|--------|--------|-----------|
| **Sigiloso** | 0 | Acesso restrito, informações confidenciais |
| **Interno** | 1 | Acesso interno, dados pessoais de servidores |
| **Público** | 2 | Acesso público, transparência administrativa |

### Esquema de Dados

```json
{
  "_id": "ObjectId",
  "texto": "String - Conteúdo textual do documento",
  "classificacao_acesso": "Integer - Rótulo (0, 1, 2)",
  "fonte": "String - Origem (reformulação/sintético)"
}
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- MongoDB
- Chaves de API do Google Gemini

### Configuração

1. **Clone o repositório:**
```bash
git clone https://github.com/emerson-diego/clara.git
cd clara
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure as variáveis de ambiente:**
Crie um arquivo `.env` na pasta `projeto/` com:

```env
# MongoDB
MONGO_USER=seu_usuario
MONGO_PASS=sua_senha
MONGO_HOST=localhost
MONGO_PORT=27017

# Google Gemini API Keys
GEMINI_API_KEY=sua_chave_principal
GEMINI_API_KEY_4=chave_adicional_1
GEMINI_API_KEY_5=chave_adicional_2
# ... adicione mais chaves conforme necessário
```

## 📁 Estrutura do Projeto

```
clara/
├── scripts/
│   ├── gemini_classificacao_utils.py     # Classificação semiautomática
│   ├── sintetizador_de_chunks.py         # Reformulação contextual
│   ├── aumentador_dataset_sigiloso.py    # Geração sintética
│   └── rotular_chunks_gemini.py          # Rotulagem automática
├── DOCUMENTACAO_TECNICA.md               # Documentação técnica detalhada
└── README.md                             # Este arquivo
```

## 🔧 Pipeline de Construção

O dataset CLARA foi construído através de um pipeline metodológico de 9 etapas:

### 1. Coleta de Dados
- Extração de documentos públicos do TRT-13 (PROAD-OUV)
- Foco em documentos classificados como públicos (com premissa de rótulos incorretos)
- Migração Oracle → MongoDB para processamento modular

### 2. Extração de Metadados
- Captura de informações estruturadas (assunto, data, classificação)
- Armazenamento em MongoDB com rastreabilidade completa

### 3. Extração de Texto
- Processamento de PDFs com abordagem condicional
- Extração direta + OCR para documentos escaneados

### 4. Anonimização
- API Shiva (TRT-13): NER + Microsoft Presidio + Regex
- Substituição de PIIs por placeholders genéricos

### 5. Segmentação
- Divisão em chunks de ~200 palavras
- Compatibilidade com modelos Transformer (limite de 512 tokens)

### 6. Reformulação Contextual
- **Técnica Principal**: Reescrita semântica via Gemini 2.5 Flash
- **Objetivo**: Camada adicional de privacidade + desvinculação das formulações originais
- **Preservação**: Significado e contexto mantidos

### 7. Geração Sintética
- **Foco**: Classe minoritária 'Sigiloso'
- **Estratégia**: Criação de dados (Data Creation)
- **Template**: Persona de especialistas (Corregedor-Geral + DPO)
- **Resultado**: 1.500 trechos adicionais

### 8. Rotulagem Semiautomática
- **Método**: Classificação zero-shot com Gemini 2.5 Flash
- **Saída**: Classe + justificativa + confiança
- **Validação**: Kappa de Cohen = 0.865 ("quase perfeito")

### 9. Balanceamento Final
- **Estratégia**: Subamostragem inteligente baseada em confiança
- **Resultado**: ~2.000 registros por classe (~6.000 total)

## 🛠️ Scripts Disponíveis

### `gemini_classificacao_utils.py`
Utilitários para classificação semiautomática de documentos usando a API Gemini.

**Funcionalidades:**
- Classificação zero-shot com base em LGPD/LAI
- Parsing estruturado de respostas (classificação + justificativa + confiança)
- Processamento automático de chunks pendentes no MongoDB
- Integração com coleção `chunks_treinamento`

**Uso:**
```python
from scripts.gemini_classificacao_utils import classificar_chunk_gemini

# Classificação individual
classificacao, justificativa, confianca = classificar_chunk_gemini(texto, model)
```

### `sintetizador_de_chunks.py`
Implementa a reformulação contextual para adicionar camada de privacidade.

**Funcionalidades:**
- Reescrita semântica completa preservando significado
- Substituição obrigatória de placeholders anonimizados
- Desvinculação das formulações originais
- Preservação de contexto, nível de sigilo e jargão técnico
- Limitação de tamanho (máximo 200 palavras)

**Uso:**
```bash
python scripts/sintetizador_de_chunks.py
```

### `aumentador_dataset_sigiloso.py`
Cria dados sintéticos específicos para a classe "Sigiloso" através de geração criativa.

**Funcionalidades:**
- Template estruturado com persona de especialistas
- Processo em 4 etapas: semente conceitual → combinação de eixos → transformação → geração
- Criação de 1.500 trechos adicionais para classe minoritária
- Tipos: licenças médicas, processos disciplinares, dados sensíveis LGPD

**Uso:**
```bash
python scripts/aumentador_dataset_sigiloso.py
```

### `rotular_chunks_gemini.py`
Script para rotulagem semiautomática usando classificação zero-shot.

**Funcionalidades:**
- Classificação zero-shot com Gemini 2.5 Flash
- Saída estruturada: classe + justificativa + confiança
- Integração com MongoDB (`chunks_treinamento`)
- Controle de qualidade baseado em escore de confiança

**Uso:**
```bash
python scripts/rotular_chunks_gemini.py
```

## 📈 Estatísticas do Dataset

### Composição Final

| Métrica | Valor |
|---------|-------|
| **Total de Registros** | ~6.000 |
| **Sigiloso (0)** | ~2.000 registros |
| **Interno (1)** | ~2.000 registros |
| **Público (2)** | ~2.000 registros |
| **Comprimento Médio** | ~200 palavras |
| **Origem dos Dados** | Reformulação + Sintética |

### Validação de Qualidade

| Métrica | Valor |
|---------|-------|
| **Kappa de Cohen** | 0.865 ("quase perfeito") |
| **Acurácia (LLM vs Humano)** | ~91% |
| **Validação Humana** | 10% dos registros |
| **F1-Score (Legal-BERT)** | 0.94 |

## 🎯 Aplicações

### Treinamento de Modelos
```python
import pandas as pd
from pymongo import MongoClient

# Conectar ao MongoDB
client = MongoClient("mongodb://usuario:senha@localhost:27017/")
db = client['dataset_treinamento']
collection = db['chunks_treinamento']

# Carregar dados
cursor = collection.find({})
data = list(cursor)

# Converter para DataFrame
df = pd.DataFrame(data)

# Preparar para treinamento
X = df['texto'].values
y = df['classificacao_acesso'].values
```

### Validação Experimental
O dataset foi validado experimentalmente com o modelo Legal-BERT:

- **Configuração**: 80% treino, 10% validação, 10% teste
- **Resultados por classe**:
  - Sigiloso (0): F1-Score = 0.94
  - Interno (1): F1-Score = 0.93  
  - Público (2): F1-Score = 0.94
- **F1-Score médio**: 0.94

### Análise de Risco
- Identificação de padrões em documentos propensos a erros
- Auditoria de conformidade documental
- Desenvolvimento de políticas de governança

## 🔒 Privacidade e Segurança

### Proteções Implementadas

1. **Anonimização Completa**: Remoção de PIIs (CPF, CNPJ, nomes)
2. **Reformulação Contextual**: Reescrita semântica completa
3. **Dados Sintéticos**: Geração artificial para classe minoritária
4. **Validação Humana**: Verificação de qualidade e privacidade (10%)

### Conformidade Legal

- ✅ Lei Geral de Proteção de Dados (LGPD)
- ✅ Lei de Acesso à Informação (LAI)
- ✅ Princípios de ciência aberta
- ✅ Licença Creative Commons (CC BY-SA 4.0)

### Garantias de Privacidade

**100% dos textos no dataset CLARA são fictícios.** Nenhum documento original está presente no corpus público. Os dados foram gerados através de:

1. **Reformulação contextual** de documentos reais (alteração completa de texto e estrutura)
2. **Geração sintética** de novos documentos para balanceamento

## 📚 Citação

Se você usar o dataset CLARA em sua pesquisa, cite:

```bibtex
@article{araujo2024clara,
  title={CLARA: Um Dataset Validado e Enriquecido para Classificação de Conformidade Documental no Setor Público Brasileiro},
  author={Araujo, Emerson Diego da Costa and Pessoa, Diego Ernesto Rosa and Fernandes, Damires Yluska Souza and Rêgo, Alex Sandro da Cunha},
  journal={[Nome do Periódico]},
  year={2024},
  publisher={[Editora]}
}
```

## 🤝 Contribuições

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).

## 👥 Autores

- **Emerson Diego da Costa Araujo** - [emerson.diego@academico.ifpb.edu.br](mailto:emerson.diego@academico.ifpb.edu.br) *[autor correspondente]*
- **Diego Ernesto Rosa Pessoa** - [diego.pessoa@ifpb.edu.br](mailto:diego.pessoa@ifpb.edu.br)
- **Damires Yluska Souza Fernandes** - [damires@ifpb.edu.br](mailto:damires@ifpb.edu.br)
- **Alex Sandro da Cunha Rêgo** - [alex@ifpb.edu.br](mailto:alex@ifpb.edu.br)

**Instituição:** Instituto Federal da Paraíba (IFPB), João Pessoa, Paraíba, Brasil

## 📞 Contato

Para dúvidas, sugestões ou problemas:

- **Email:** emerson.diego@academico.ifpb.edu.br
- **Issues:** [GitHub Issues](https://github.com/emerson-diego/clara/issues)
- **Repositório:** [https://github.com/emerson-diego/clara](https://github.com/emerson-diego/clara)

## 🔮 Trabalhos Futuros

- [ ] Dataset dinâmico com atualizações contínuas
- [ ] Expansão interinstitucional para outros órgãos públicos
- [ ] Modelos pré-treinados específicos para o domínio
- [ ] Interface web para classificação interativa
- [ ] API REST para classificação em tempo real
- [ ] Integração com sistemas de gestão documental

## 📊 Performance do Dataset

### Experimento de Validação

O dataset CLARA foi validado experimentalmente através do fine-tuning do modelo Legal-BERT:

**Configuração:**
- **Modelo**: Legal-BERT (Transformer pré-treinado)
- **Hardware**: GPU NVIDIA A100
- **Divisão**: 80% treino, 10% validação, 10% teste
- **Parâmetros**: 3 épocas, batch size 16, learning rate 2×10⁻⁵

**Resultados:**

| Classe | Precisão | Revocação | F1-Score | Suporte |
|--------|----------|-----------|----------|---------|
| Sigiloso (0) | 0.95 | 0.93 | **0.94** | 200 |
| Interno (1) | 0.92 | 0.94 | **0.93** | 200 |
| Público (2) | 0.94 | 0.94 | **0.94** | 200 |
| **Macro Avg** | **0.94** | **0.94** | **0.94** | 600 |

### Análise dos Resultados

- **Performance equilibrada** entre todas as classes
- **Poucos erros** entre classes extremas (Sigiloso vs Público)
- **Erros residuais** concentrados entre classes adjacentes
- **Excelente baseline** para pesquisas futuras

---

**Nota:** Este dataset foi desenvolvido para fins de pesquisa e desenvolvimento de tecnologias de IA no setor público brasileiro, sempre respeitando a privacidade e a conformidade legal. 