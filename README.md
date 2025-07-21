# CLARA: Dataset para Classificação de Conformidade Documental

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📋 Visão Geral

O **CLARA** (*Classificação Legal de Arquivos e Registros Administrativos*) é um dataset público e balanceado para classificação de conformidade documental no setor público brasileiro. O projeto equilibra transparência (Lei de Acesso à Informação - LAI) e proteção de dados (Lei Geral de Proteção de Dados - LGPD).

### 🎯 Características Principais

- **~10.000 registros** balanceados (~3.333 por classe)
- **3 classes**: Sigiloso (0), Interno (1), Público (2)
- **100% dados fictícios** (reformulação contextual + geração sintética)
- **Compatível** com modelos Transformer
- **F1-Score de 0.94** com Legal-BERT
- **Kappa de Cohen: 0.821** ("quase perfeito")

## 📊 Estrutura do Dataset

### Esquema de Dados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| **_id** | ObjectID | Identificador único do registro |
| **texto** | String | Conteúdo textual (~200 palavras) |
| **classificacao_acesso** | Integer | Rótulo (0: Sigiloso, 1: Interno, 2: Público) |
| **fonte** | String | Origem ("reformulação" ou "sintético") |

### Composição Final

| Classe | Registros | Distribuição |
|--------|-----------|--------------|
| **Sigiloso (0)** | ~3.333 | 33,3% |
| **Interno (1)** | ~3.333 | 33,3% |
| **Público (2)** | ~3.333 | 33,3% |
| **Total** | **~10.000** | **100%** |

## 🔧 Metodologia de Construção

### Pipeline de 9 Etapas

1. **Coleta**: Documentos do TRT-13 (PROAD-OUV)
2. **Extração de Metadados**: Informações estruturadas
3. **Extração de Texto**: PDFs → texto (OCR quando necessário)
4. **Anonimização**: API Shiva (NER + Presidio + Regex)
5. **Segmentação**: Chunks de ~200 palavras
6. **Reformulação Contextual**: Reescrita semântica (Gemini 2.5 Flash)
7. **Geração Sintética**: ~2.500 trechos para classe "Sigiloso"
8. **Rotulagem Semiautomática**: Classificação zero-shot + validação humana (10%)
9. **Balanceamento**: Subamostragem inteligente baseada em confiança

### Composição Antes vs Depois do Balanceamento

| Classe | Antes | % Antes | Depois | % Depois |
|--------|-------|---------|--------|----------|
| **Público** | 5.722 | 36,7% | 3.333 | 33,3% |
| **Interno** | 8.643 | 55,5% | 3.333 | 33,3% |
| **Sigiloso** | 1.215 | 7,8% | 3.333 | 33,3% |
| **Total** | **15.580** | **100%** | **~10.000** | **100%** |

## 🚀 Instalação e Uso

### Pré-requisitos
- Python 3.8+
- MongoDB
- Chaves API Google Gemini

### Configuração Rápida

```bash
# Clone e instale
git clone https://github.com/emerson-diego/clara.git
cd clara
pip install -r requirements.txt

# Consulte o dicionário de dados detalhado
cat dicionario_dados.md

# Configure variáveis de ambiente (.env)
MONGO_USER=seu_usuario
MONGO_PASS=sua_senha
GEMINI_API_KEY=sua_chave
```

### Carregar Dataset

```python
import pandas as pd
from pymongo import MongoClient

# Conectar MongoDB
client = MongoClient("mongodb://usuario:senha@localhost:27017/")
db = client['dataset_treinamento']
collection = db['chunks_treinamento']

# Carregar dados
data = list(collection.find({}))
df = pd.DataFrame(data)

# Preparar para ML
X = df['texto'].values
y = df['classificacao_acesso'].values
```

## 🛠️ Scripts Principais

### `gemini_classificacao_utils.py`
Classificação semiautomática com Gemini 2.5 Flash
- Parsing estruturado (classe + justificativa + confiança)
- Integração MongoDB
- Classificação zero-shot

### `sintetizador_de_chunks.py`  
Reformulação contextual para privacidade
- Reescrita semântica completa
- Preservação de significado
- Desvinculação das formulações originais

### `aumentador_dataset_sigiloso.py`
Geração sintética para balanceamento
- Template com persona de especialistas (Corregedor-Geral + DPO)
- ~2.500 trechos adicionais classe "Sigiloso"
- Tipos: processos disciplinares, dados sensíveis, investigações

### `rotular_chunks_gemini.py`
Rotulagem automática do corpus
- Processamento em lote
- Controle de qualidade por confiança
- Saída estruturada

## 📈 Validação e Performance

### Métricas de Qualidade
- **Kappa de Cohen**: 0.821 ("quase perfeito")
- **Acurácia LLM vs Humano**: ~90%
- **Validação Humana**: 10% dos registros

### Experimento Legal-BERT
**Configuração**: 80% treino, 10% validação, 10% teste

| Classe | Precisão | Revocação | F1-Score |
|--------|----------|-----------|----------|
| **Sigiloso (0)** | 0.95 | 0.93 | **0.94** |
| **Interno (1)** | 0.92 | 0.94 | **0.93** |
| **Público (2)** | 0.94 | 0.94 | **0.94** |
| **Macro Avg** | **0.94** | **0.94** | **0.94** |

## 🔒 Privacidade e Conformidade

### Garantias de Segurança
✅ **100% textos fictícios** - nenhum documento original  
✅ **Anonimização completa** (PIIs removidos)  
✅ **Reformulação contextual** (desvinculação das formulações)  
✅ **Validação humana** (10% verificado manualmente)  

### Conformidade Legal
✅ **LGPD** - Lei Geral de Proteção de Dados  
✅ **LAI** - Lei de Acesso à Informação  
✅ **CC BY 4.0** - Licença Creative Commons  

## 🎯 Aplicações

- **Treinamento de Modelos**: Classificação automática de documentos
- **Análise de Risco**: Identificação de padrões de erro
- **Auditoria de Conformidade**: Verificação LGPD/LAI
- **Governança de Dados**: Políticas automatizadas

## 📚 Citação

```bibtex
@article{araujo2024clara,
  title={CLARA: Um Dataset Validado e Enriquecido para Classificação de Conformidade Documental no Setor Público Brasileiro},
  author={Araujo, Emerson Diego da Costa and Pessoa, Diego Ernesto Rosa and Fernandes, Damires Yluska Souza and Rêgo, Alex Sandro da Cunha},
  journal={[Nome do Periódico]},
  year={2024}
}
```

## 👥 Equipe

**Instituto Federal da Paraíba (IFPB)**
- **Emerson Diego da Costa Araujo** - [emerson.diego@academico.ifpb.edu.br](mailto:emerson.diego@academico.ifpb.edu.br) *(autor correspondente)*
- **Diego Ernesto Rosa Pessoa** - [diego.pessoa@ifpb.edu.br](mailto:diego.pessoa@ifpb.edu.br)
- **Damires Yluska Souza Fernandes** - [damires@ifpb.edu.br](mailto:damires@ifpb.edu.br)
- **Alex Sandro da Cunha Rêgo** - [alex@ifpb.edu.br](mailto:alex@ifpb.edu.br)

## 📞 Contato

- **Email**: emerson.diego@academico.ifpb.edu.br
- **Repository**: [https://github.com/emerson-diego/clara](https://github.com/emerson-diego/clara)
- **Issues**: [GitHub Issues](https://github.com/emerson-diego/clara/issues)

---

**Licença**: CC BY 4.0 | **Instituição**: IFPB, João Pessoa, PB, Brasil 