# LEIA: Dataset para Classificação de Conformidade Documental

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📋 Visão Geral

O **LEIA** (*Legal-Administrative Enrichment and Information Annotation Dataset*) é um dataset público e balanceado para classificação de conformidade documental no setor público brasileiro. O projeto aborda o delicado equilíbrio entre transparência (Lei de Acesso à Informação - LAI) e proteção de dados (Lei Geral de Proteção de Dados - LGPD).

### 🎯 Objetivos

- Fornecer um dataset balanceado para treinamento de modelos de IA
- Facilitar a automação da classificação documental no setor público
- Garantir total privacidade através de dados sintéticos
- Fomentar pesquisas em Processamento de Linguagem Natural (PLN)

### 🔑 Características Principais

- **6.000 registros** balanceados (2.000 por classe)
- **3 classes de acesso**: Sigiloso (0), Interno (1), Público (2)
- **100% dados sintéticos** para proteção de privacidade
- **Compatível** com modelos Transformer (BERT, RoBERTa, etc.)
- **Validação humana** em 10% dos registros

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
  "_id": "ObjectID",
  "texto": "String - Conteúdo textual do documento",
  "classificacao_acesso": "Integer - Rótulo (0, 1, 2)",
  "fonte": "String - 'reformulação' ou 'sintético'"
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
git clone https://github.com/emerson-diego/leia.git
cd leia
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
leia/
├── dataset_final/
│   └── dataset_treinamento.chunks_treinamento.json  # Dataset final
├── scripts/
│   ├── gemini_classificacao_utils.py     # Utilitários de classificação
│   ├── sintetizador_de_chunks.py         # Geração de dados sintéticos
│   ├── aumentador_dataset_sigiloso.py    # Aumento da classe sigilosa
│   └── rotular_chunks_gemini.py          # Rotulagem automática
└── README.md
```

## 🔧 Pipeline de Construção

O dataset LEIA foi construído através de um pipeline de 9 etapas:

### 1. Coleta de Dados
- Extração de documentos públicos do TRT-13
- Foco em documentos já classificados como públicos
- Armazenamento em MongoDB

### 2. Pré-processamento
- Extração de texto de PDFs (OCR quando necessário)
- Anonimização com API Shiva (NER + Presidio + Regex)
- Segmentação em chunks de ~200 palavras

### 3. Enriquecimento
- **Reformulação Contextual**: Reescreve textos preservando significado
- **Geração Sintética**: Cria novos exemplos para classe minoritária

### 4. Rotulagem e Validação
- Classificação automática com Gemini 2.5 Flash
- Validação humana em amostra de 10%
- Índice Kappa de Cohen: 0.512 (concordância moderada)

### 5. Balanceamento
- Subamostragem inteligente das classes majoritárias
- Preservação dos exemplos com maior confiança

## 🛠️ Scripts Disponíveis

### `gemini_classificacao_utils.py`
Utilitários para classificação automática de documentos usando a API Gemini.

**Funcionalidades:**
- Classificação de chunks de texto
- Gerenciamento de múltiplas chaves de API
- Tratamento de erros e rate limiting

**Uso:**
```python
from scripts.gemini_classificacao_utils import classificar_chunk_gemini

classificacao, justificativa, confianca, modelo, versao = classificar_chunk_gemini(
    texto, gemini_keys, gemini_key_names, model
)
```

### `sintetizador_de_chunks.py`
Gera versões sintéticas de documentos através de reformulação contextual.

**Funcionalidades:**
- Processamento em lotes para eficiência
- Substituição de placeholders anonimizados
- Preservação de contexto e jargão técnico

**Uso:**
```bash
python scripts/sintetizador_de_chunks.py
```

### `aumentador_dataset_sigiloso.py`
Cria dados sintéticos específicos para a classe "Sigiloso".

**Funcionalidades:**
- Geração de documentos médicos, jurídicos e de RH
- Diferentes níveis de sigilo (Alto e Médio)
- Transformação conceitual de documentos de inspiração

**Uso:**
```bash
python scripts/aumentador_dataset_sigiloso.py
```

### `rotular_chunks_gemini.py`
Script para transferir dados classificados para o dataset final.

**Funcionalidades:**
- Seleção dos melhores exemplos por confiança
- Mapeamento de fontes (reformulação/sintético)
- Preparação para treinamento

## 📈 Estatísticas do Dataset

| Métrica | Valor |
|---------|-------|
| **Total de Registros** | 6.000 |
| **Registros por Classe** | 2.000 |
| **Comprimento Médio** | ~200 palavras |
| **Formato** | JSON |
| **Tamanho do Arquivo** | ~6.8MB |

## 🎯 Aplicações

### Treinamento de Modelos
```python
import json
import pandas as pd

# Carregar o dataset
with open('dataset_final/dataset_treinamento.chunks_treinamento.json', 'r') as f:
    data = json.load(f)

# Converter para DataFrame
df = pd.DataFrame(data)

# Preparar para treinamento
X = df['texto'].values
y = df['classificacao_acesso'].values
```

### Análise de Risco
- Identificação de padrões em documentos propensos a erros
- Auditoria de conformidade documental
- Desenvolvimento de políticas de governança

## 🔒 Privacidade e Segurança

### Proteções Implementadas

1. **Anonimização Completa**: Remoção de PIIs (CPF, CNPJ, nomes)
2. **Dados Sintéticos**: 100% dos textos são fictícios
3. **Reformulação Contextual**: Desvinculação de formulações originais
4. **Validação Humana**: Verificação de qualidade e privacidade

### Conformidade Legal

- ✅ Lei Geral de Proteção de Dados (LGPD)
- ✅ Lei de Acesso à Informação (LAI)
- ✅ Princípios de ciência aberta
- ✅ Licença Creative Commons (CC BY-SA 4.0)

## 📚 Citação

Se você usar o dataset LEIA em sua pesquisa, cite:

```bibtex
@article{araujo2024leia,
  title={LEIA: Um Dataset Curado e Enriquecido para Classificação de Conformidade Documental no Setor Público Brasileiro},
  author={Araujo, Emerson Diego da Costa and Pessoa, Diego Ernesto Rosa},
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

- **Emerson Diego da Costa Araujo** - [emerson.diego@academico.ifpb.edu.br](mailto:emerson.diego@academico.ifpb.edu.br)
- **Diego Ernesto Rosa Pessoa** - [diego.pessoa@ifpb.edu.br](mailto:diego.pessoa@ifpb.edu.br)

**Instituição:** Instituto Federal da Paraíba (IFPB)

## 📞 Contato

Para dúvidas, sugestões ou problemas:

- **Email:** emerson.diego@academico.ifpb.edu.br
- **Issues:** [GitHub Issues](https://github.com/emerson-diego/leia/issues)
- **Repositório:** [https://github.com/emerson-diego/leia](https://github.com/emerson-diego/leia)

## 🔮 Trabalhos Futuros

- [ ] Dataset dinâmico com atualizações contínuas
- [ ] Expansão para outros órgãos públicos
- [ ] Modelos pré-treinados específicos para o domínio
- [ ] Interface web para classificação interativa
- [ ] Integração com sistemas de gestão documental

---

**Nota:** Este dataset foi desenvolvido para fins de pesquisa e desenvolvimento de tecnologias de IA no setor público brasileiro, sempre respeitando a privacidade e a conformidade legal. 