# Dicionário de Dados - Dataset CLARA

## 📋 Informações Gerais

**Nome do Dataset**: CLARA (Classificação Legal de Arquivos e Registros Administrativos)  
**Versão**: 1.0  
**Data de Criação**: 2024  
**Formato**: JSON (JavaScript Object Notation)  
**Encoding**: UTF-8  
**Tamanho Aproximado**: ~10.000 registros  

## 🗂️ Estrutura do Dataset

### Esquema de Dados

| Campo | Tipo | Requerido | Descrição |
|-------|------|-----------|-----------|
| `_id` | ObjectID | Sim | Identificador único do registro no dataset |
| `texto` | String | Sim | Conteúdo textual do documento (~200 palavras) |
| `classificacao_acesso` | Integer | Sim | Rótulo alvo da classificação |
| `fonte` | String | Sim | Origem do registro |

### Detalhamento dos Campos

#### `_id` (ObjectID)
- **Tipo**: MongoDB ObjectID
- **Função**: Identificador único e imutável para cada registro
- **Formato**: 24 caracteres hexadecimais (ex: `507f1f77bcf86cd799439011`)
- **Uso**: Referência e rastreabilidade dos registros

#### `texto` (String)
- **Tipo**: Texto livre em português brasileiro
- **Comprimento**: Aproximadamente 200 palavras
- **Características**:
  - Texto anonimizado (PIIs removidos)
  - Conteúdo 100% fictício (reformulado ou sintético)
  - Jargão técnico administrativo/jurídico preservado
  - Compatível com modelos Transformer (limite 512 tokens)
- **Exemplo**: 
  ```
  "Relatório de atividades da equipe de projetos, período: 01/05/2024 a 31/05/2024. 
   Projetos concluídos: Projeto A, Projeto B. Projetos em andamento: Projeto C, 
   Projeto D. Observações: A equipe está trabalhando dentro do prazo e orçamento."
  ```

#### `classificacao_acesso` (Integer)
- **Tipo**: Número inteiro
- **Valores Possíveis**: 0, 1, 2
- **Distribuição**: Balanceada (~3.333 registros por classe)

| Código | Classe | Descrição | Critérios Principais |
|--------|--------|-----------|---------------------|
| **0** | Sigiloso | Acesso restrito por força de lei | Informações que coloquem em risco a segurança da sociedade ou do Estado; dados pessoais sensíveis (saúde, origem racial, etc.); segredo de justiça; sigilo fiscal e bancário; investigações em andamento |
| **1** | Interno | Acesso restrito aos agentes públicos | Documentos preparatórios (despachos, notas técnicas, pareceres) que fundamentam uma decisão futura; informações pessoais de servidores não sensíveis; discussões e deliberações internas |
| **2** | Público | Acesso irrestrito como regra geral | Atos administrativos finais; contratos; resultados de licitações; atas de reuniões abertas; dados de transparência ativa; informações de interesse coletivo ou geral |

#### `fonte` (String)
- **Tipo**: Texto categórico
- **Valores Possíveis**: `"reformulação"`, `"sintético"`
- **Função**: Rastreabilidade da origem do registro

| Valor | Descrição | Processo |
|-------|-----------|----------|
| `"reformulação"` | Texto reescrito semanticamente | Reformulação contextual via LLM |
| `"sintético"` | Texto gerado artificialmente | Geração sintética via LLM |

## 📊 Composição do Dataset

### Distribuição por Classe

| Classe | Código | Registros | Percentual |
|--------|--------|-----------|------------|
| Sigiloso | 0 | ~3.318 | 33,3% |
| Interno | 1 | ~3.325 | 33,3% |
| Público | 2 | ~3.329 | 33,3% |
| **Total** | - | **~10.000** | **100%** |

### Distribuição por Origem

| Fonte | Descrição | Proporção Estimada |
|-------|-----------|-------------------|
| `reformulação` | Textos reescritos | ~79% |
| `sintético` | Textos gerados | ~21% |

## 🔍 Exemplos de Registros

### Exemplo 1: Classe Sigiloso (0)
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "texto": "RELATÓRIO CONCLUSIVO DE SINDICÂNCIA. PROCESSO: SINDIC. Nº 005/2024-CORREG. TRT-XX. ASSUNTO: Apuração de Irregularidades no Registro de Ponto e Compensação de BCH – Juiz Titular. A Corregedoria-Geral deste Tribunal, no âmbito da Sindicância nº 005/2024, concluiu a fase de instrução referente ao Exmo. Juiz Dr. [NOME] (Matrícula Funcional [NUMERO]), Titular da 15ª Vara do Trabalho. As investigações revelaram inconsistências graves nos registros de teletrabalho e na compensação do Banco de Horas – BCH Covid-19.",
  "classificacao_acesso": 0,
  "fonte": "sintético"
}
```

### Exemplo 2: Classe Interno (1)
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "texto": "Relatório de atividades da equipe de projetos, período: 01/05/2024 a 31/05/2024. Projetos concluídos: Projeto A, Projeto B. Projetos em andamento: Projeto C, Projeto D. Observações: A equipe está trabalhando dentro do prazo e orçamento.",
  "classificacao_acesso": 1,
  "fonte": "reformulação"
}
```

### Exemplo 3: Classe Público (2)
```json
{
  "_id": "507f1f77bcf86cd799439013",
  "texto": "Ata de Pregão Eletrônico no 372.000/2024 - Inexigibilidade. Processo no 4239/2019. CNPJ: 45.678.901/0001-23. Local: Belo Horizonte. Data: 23/01/2020. Valor: R$ 372.000,00. Transparencia 080004000012020NE000102",
  "classificacao_acesso": 2,
  "fonte": "reformulação"
}
```

## 🛠️ Carregamento e Uso

### Python com Pandas
```python
import pandas as pd
import json

# Carregar dataset
with open('clara_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Verificar estrutura
print(df.info())
print(df['classificacao_acesso'].value_counts())
print(df['fonte'].value_counts())
```

### Python com MongoDB
```python
from pymongo import MongoClient
import pandas as pd

# Conectar ao MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['dataset_treinamento']
collection = db['chunks_treinamento']

# Carregar dados
data = list(collection.find({}))
df = pd.DataFrame(data)

# Preparar para ML
X = df['texto'].values
y = df['classificacao_acesso'].values
```

## 📋 Validação de Dados

### Verificações Recomendadas

1. **Integridade dos Tipos**:
   ```python
   assert df['_id'].dtype == 'object'
   assert df['texto'].dtype == 'object'
   assert df['classificacao_acesso'].dtype == 'int64'
   assert df['fonte'].dtype == 'object'
   ```

2. **Valores Válidos**:
   ```python
   assert df['classificacao_acesso'].isin([0, 1, 2]).all()
   assert df['fonte'].isin(['reformulação', 'sintético']).all()
   assert df['texto'].str.len().min() > 0  # Textos não vazios
   ```

3. **Balanceamento**:
   ```python
   class_counts = df['classificacao_acesso'].value_counts()
   assert abs(class_counts.max() - class_counts.min()) < 100  # Diferença máxima de 100
   ```

## 🔒 Considerações de Privacidade

### Garantias Implementadas
- ✅ **Anonimização Completa**: Todas as PIIs removidas
- ✅ **Reformulação Contextual**: Textos completamente reescritos
- ✅ **Dados 100% Fictícios**: Nenhum documento original presente
- ✅ **Validação Humana**: 10% validado por especialista

### Conformidade Legal
- ✅ **LGPD**: Lei Geral de Proteção de Dados
- ✅ **LAI**: Lei de Acesso à Informação
- ✅ **CC BY 4.0**: Licença Creative Commons

## 📚 Metodologia de Construção

### Pipeline de 9 Etapas
1. **Coleta**: Documentos TRT-13 (PROAD-OUV)
2. **Armazenamento**: Migração Oracle → MongoDB
3. **Extração**: PDFs → texto (OCR quando necessário)
4. **Anonimização**: API Shiva (NER + Presidio + Regex)
5. **Segmentação**: Chunks de ~200 palavras
6. **Reformulação**: Reescrita semântica (Gemini 2.5 Flash)
7. **Geração Sintética**: ~2.500 trechos classe "Sigiloso"
8. **Rotulagem**: Classificação zero-shot + validação humana
9. **Balanceamento**: Subamostragem inteligente

### Métricas de Qualidade
- **Kappa de Cohen**: 0.821 ("quase perfeito")
- **Acurácia LLM vs Humano**: ~90%
- **Validação Humana**: 10% dos registros

### Experimentos Comparativos
**Configuração**: 80% treino, 10% validação, 10% teste | 10 épocas | GPU NVIDIA T400

**BERT Base**: F1-Score médio de 0.87  
**Legal-BERT**: F1-Score médio de 0.89

## 📖 Referência

**Artigo**: "CLARA: Um Dataset Validado e Enriquecido para Classificação de Conformidade Documental no Setor Público Brasileiro"

**Dataset**: [https://zenodo.org/uploads/16044257](https://zenodo.org/uploads/16044257)  
**Código-fonte**: [https://github.com/emerson-diego/CLARA/tree/main/scripts](https://github.com/emerson-diego/CLARA/tree/main/scripts)

**Autores**: 
- Emerson Diego da Costa Araujo (emerson.diego@academico.ifpb.edu.br) *[autor correspondente]*
- Diego Ernesto Rosa Pessoa (diego.pessoa@ifpb.edu.br)
- Damires Yluska Souza Fernandes (damires@ifpb.edu.br)
- Alex Sandro da Cunha Rêgo (alex@ifpb.edu.br)

**Instituição**: Instituto Federal da Paraíba (IFPB), João Pessoa, PB, Brasil

---

**Última Atualização**: 2025  
**Versão do Documento**: 1.0 