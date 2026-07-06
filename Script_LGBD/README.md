---

# 🛡️ Auditoria de Segurança e Conformidade com a LGPD

Este diretório contém os artefatos de simulação e comprovação de segurança desenvolvidos para o Trabalho de Conclusão de Curso (TCC). O objetivo destes arquivos é demonstrar, na prática e matematicamente, a resiliência da arquitetura de reconhecimento facial contra ataques de acesso físico, injeção de dados e tentativas de engenharia reversa, em estrita conformidade com a Lei Geral de Proteção de Dados (LGPD).

## 📁 Conteúdo do Diretório

1. `foto_banco.png` - Captura de tela do banco de dados SQLite.
2. `simulacao_ataque.py` - Script de simulação de roubo de dados em repouso.
3. `teste_biohashing.py` - Script de simulação de comprometimento total e irreversibilidade biométrica.

---

### 1. Pseudonimização Estrutural (`foto_banco.png`)

**O que é:** Uma captura de tela do banco de dados operando no software *DB Browser for SQLite*.
**O que comprova:** A ofuscação dos dados nominais de identificação.

**Por que funciona:** Ao invés de armazenar nomes em texto claro (ex: "Cleber Henrique"), o sistema aplica a função de dispersão criptográfica **SHA-256**. A imagem demonstra que a coluna `nome` armazena apenas um código hexadecimal de 64 caracteres (ex: `3b76cdb9bafe0d1f...`). Como a função *hash* é unidirecional e determinística, é impossível para um invasor reverter este código para o nome original utilizando força bruta ou engenharia reversa, garantindo o anonimato em caso de vazamento do banco relacional.

---

### 2. Proteção de Dados em Repouso (`simulacao_ataque.py`)

**O que é:** Um script Python que simula a ação de um invasor que obteve acesso físico à placa Labrador e roubou o arquivo que armazena os vetores faciais (`encodings.pickle`).
**O que comprova:** A proteção *Data-at-rest* utilizando criptografia simétrica forte.

**Por que funciona:** O sistema real cifra o arquivo de biometrias utilizando o padrão **AES-128** (via biblioteca `Fernet`). O script simula a tentativa de leitura desses dados sem a posse da chave simétrica de decodificação. Ao tentar utilizar o módulo `pickle` para desserializar o arquivo, o Python acusa um erro estrutural (`UnpicklingError`), pois os bytes encontram-se embaralhados e matematicamente ilegíveis. Isso prova que o simples roubo do hardware ou do cartão de memória não expõe as biometrias dos pacientes.

---

### 3. Irreversibilidade Biométrica e Anti-Spoofing (`teste_biohashing.py`)

**O que é:** Um script de auditoria que assume o pior cenário possível: o invasor roubou o arquivo físico **e** conseguiu a chave criptográfica, obtendo acesso direto aos vetores biométricos (os *embeddings* de 128 dimensões).
**O que comprova:** A inviabilidade técnica de reconstrução facial (proteção da privacidade) e a proteção contra injeção de dados lógicos (*spoofing*).

**Por que funciona:**
O sistema não salva o rosto gerado pelo algoritmo *FaceNet* de forma pura. Antes de gravar, ele multiplica o vetor original por uma **Matriz Ortogonal** gerada aleatoriamente (Técnica de *Bio-hashing*). O script prova o sucesso dessa técnica através de dois testes matemáticos:

1. **Falha na Reconstrução (Norma L2):** Algoritmos de IA Generativa (como GANs) treinados para desenhar rostos a partir de vetores exigem que os dados obedeçam a uma distribuição específica (Norma L2 próxima a 1). O script calcula a norma do dado roubado e comprova que a distorção introduzida pela Matriz Ortogonal destrói a integridade geométrica original da face. Qualquer tentativa de recriar a imagem gerará apenas ruído visual.
2. **Falha na Injeção (*Spoofing*):** Se o invasor tentar enviar esse dado numérico de volta para o sistema fingindo ser a câmera, o cálculo da **Distância Euclidiana** entre o vetor real esperado e o vetor injetado será gigantesco (muito acima do limiar seguro de `0.6`). O sistema rejeita o acesso automaticamente, provando que o vetor armazenado em disco é inútil para forjar falsos positivos.

---

### 🚀 Como executar as simulações

Para atestar os resultados descritos acima, certifique-se de ter o Python 3.x instalado em seu ambiente, juntamente com a biblioteca NumPy.

```bash
# Instalar dependências necessárias
pip install numpy

# Executar simulação de roubo físico (Ataque AES)
python simulacao_ataque.py

# Executar simulação matemática de Bio-hashing
python teste_biohashing.py

```