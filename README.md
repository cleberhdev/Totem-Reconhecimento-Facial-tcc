# 🛡️ Sistema de Reconhecimento Facial Seguro

### 🔐 Arquitetura Privada e Compatível com LGPD

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![LGPD](https://img.shields.io/badge/Compliance-LGPD-success)
![Security](https://img.shields.io/badge/Security-AES--128%20%7C%20JWT%20%7C%20SHA--256-red)

**Autor:** Cleber Henrique Lacerda Duarte
**Projeto:** Trabalho de Conclusão de Curso (TCC) — IFPI Campus Floriano

---

## 📌 Visão Geral

Este projeto implementa um **Totem Inteligente de Reconhecimento Facial** voltado para ambientes clínicos, com foco absoluto em **segurança da informação e privacidade de dados biométricos**.

Diferente de sistemas tradicionais, esta solução foi projetada sob o princípio de:

> 🔒 **Zero exposição de dados sensíveis**

O sistema atua como um **Provedor de Identidade (IdP)**, realizando todo o processamento biométrico localmente e comunicando-se com sistemas externos exclusivamente por meio de **tokens seguros e efêmeros**.

---

## 🎯 Objetivos do Sistema

* Garantir autenticação biométrica segura de pacientes
* Evitar armazenamento de imagens sensíveis
* Reduzir riscos de vazamento de dados
* Estar em conformidade com a **Lei Geral de Proteção de Dados (LGPD)**
* Oferecer uma arquitetura escalável e segura para clínicas

---

## 🔐 Arquitetura de Segurança (LGPD by Design)

O sistema foi desenvolvido com múltiplas camadas de proteção:

### 1. 🧠 Privacy by Design

* Nenhuma imagem (`.jpg`, `.png`) é salva em disco
* Dados visuais existem apenas na **memória RAM**
* Descarte imediato após processamento

### 2. 🔄 Biometria Cancelável (Bio-hashing)

* Vetores faciais (128D) são transformados matematicamente
* Uso de **matriz ortogonal secreta**
* Impossibilidade prática de reconstrução facial

### 3. 🔐 Criptografia em Repouso

* Banco biométrico protegido com **AES-128 (Fernet)**
* Chaves nunca são armazenadas em disco
* Uso obrigatório de variáveis de ambiente

### 4. 🎟️ Tokenização Segura

* Emissão de **JWT (JSON Web Token)**
* Validade limitada (2 horas)
* Comunicação segura com APIs externas

### 5. 🕶️ Pseudonimização de Dados

* Nenhum dado pessoal identificável é armazenado
* Uso de **SHA-256 com salt**
* Logs totalmente anonimizados

---

## 🗂️ Estrutura do Projeto

A arquitetura foi reduzida ao mínimo necessário para aumentar a segurança:

```text
/
├── 03_reconhecer.py
├── matriz_projecao.npy
├── encodings.pickle
├── totem_banco.db
└── README.md
```

> ⚠️ Arquivos sensíveis são gerados automaticamente na primeira execução

---

## ⚙️ Tecnologias Utilizadas

### 🔹 Bibliotecas Externas

* `opencv-python` → Captura de vídeo e interface
* `face_recognition` → Extração de embeddings faciais
* `numpy` → Processamento matemático e Bio-hashing
* `cryptography` → Criptografia (Fernet / AES)
* `PyJWT` → Geração de tokens seguros
* `Flask` → API local integrada

### 🔹 Bibliotecas Nativas

* `hashlib` (SHA-256)
* `sqlite3`
* `pickle`
* `threading`
* `datetime`, `time`, `os`, `sys`, `socket`

---

## 🚀 Execução do Projeto

### 1. Instale as dependências

```bash
pip install opencv-python face_recognition numpy cryptography PyJWT flask
```

---

### 2. Configure as variáveis de ambiente

O sistema **não inicia sem as chaves de segurança**.

#### 🔑 Gerar chave Fernet:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

#### 💻 Windows (PowerShell):

```powershell
$env:CHAVE_BIOMETRIA="SUA_CHAVE_FERNET"
$env:CHAVE_JWT="SUA_CHAVE_JWT"
```

#### 🐧 Linux:

```bash
export CHAVE_BIOMETRIA="SUA_CHAVE_FERNET"
export CHAVE_JWT="SUA_CHAVE_JWT"
```

---

### 3. Execute o sistema

```bash
python 03_reconhecer.py
```

---

## 🧠 Arquitetura Interna

O sistema utiliza **multithreading** para garantir desempenho em tempo real:

### 🎥 Thread Principal

* Captura e renderização de vídeo
* Interface fluida (30+ FPS)

### 🤖 Thread de IA

* Processamento assíncrono
* Reconhecimento facial
* Geração de token JWT

### 🌐 Thread do Servidor (Flask)

* Comunicação com sistemas externos

#### Endpoints disponíveis:

* `POST /api/cadastrar_direto`
  → Cadastro biométrico seguro

* `GET /api/relatorio`
  → Logs anonimizados

* `GET /video_feed`
  → Monitoramento remoto

---

## 📊 Diferenciais do Projeto

✔ Arquitetura orientada à privacidade
✔ Nenhuma exposição de dados sensíveis
✔ Aplicação real de conceitos de segurança da informação
✔ Integração com sistemas externos via tokens
✔ Ideal para ambientes clínicos e regulamentados

---

## ⚠️ Aviso

Este projeto é um **protótipo acadêmico**, desenvolvido para fins de pesquisa em:

* Segurança da Informação
* Visão Computacional
* Proteção de Dados

Não deve ser utilizado diretamente em produção sem auditoria de segurança adicional.

---

## 📄 Licença

Este projeto pode ser adaptado para fins acadêmicos e estudos.
Para uso comercial, recomenda-se revisão jurídica e técnica.

---

## 🤝 Contato

Caso queira evoluir este projeto ou integrá-lo a soluções reais, entre em contato.

---

> 🔐 *Segurança não é um recurso — é um requisito.*
