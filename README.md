# 🛒 DHgate Scraper App

Aplicação web completa para pesquisar produtos no [DHgate](https://pt.dhgate.com) e exportar os resultados para Excel ou Google Sheets — automaticamente.

---

## 🗂️ Estrutura do Projecto

```
dhgate-scraper-app/
├── backend/
│   ├── app.py           # API FastAPI (endpoints)
│   ├── scraper.py       # Lógica de scraping (BeautifulSoup)
│   ├── sheets.py        # Integração Google Sheets (opcional)
│   └── requirements.txt
├── frontend/
│   ├── index.html       # Interface web
│   ├── style.css        # Estilos
│   └── script.js        # Lógica JS (fetch, render, export)
├── data/
│   └── output.xlsx      # Excel gerado automaticamente
├── .env                 # Variáveis de ambiente
├── .gitignore
├── Dockerfile
└── README.md
```

---

## ✨ Funcionalidades

| Feature | Detalhe |
|---|---|
| 🔍 Pesquisa | Campo de texto + nº de páginas |
| 📦 Dados recolhidos | Nome, Preço, Avaliação, Vendedor, Link, Imagem, Encomendas |
| 📥 Export Excel | Download directo do `.xlsx` formatado |
| 📊 Export Sheets | Envia para Google Sheets via Service Account |
| 🛡️ Anti-bloqueio | User-Agent rotativo + delay aleatório entre requests |
| 🔧 Modular | Scraper, API e frontend completamente separados |
| 🐳 Docker-ready | Dockerfile multi-stage incluído |

---

## 🚀 Instalação e Execução Local

### Pré-requisitos

- Python 3.11+
- pip

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USER/dhgate-scraper-app.git
cd dhgate-scraper-app
```

### 2. Criar ambiente virtual e instalar dependências

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r backend/requirements.txt
```

### 3. Configurar variáveis de ambiente

Edita o ficheiro `.env` na raiz do projecto:

```env
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Google Sheets (opcional)
# GOOGLE_CREDENTIALS_FILE=credentials.json
# GOOGLE_SHEET_ID=SEU_ID_AQUI
```

### 4. Arrancar o servidor

```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 5. Abrir o frontend

Abre `frontend/index.html` directamente no browser, ou acede a:

```
http://localhost:8000/app
```

> O FastAPI serve os ficheiros estáticos do frontend em `/app`.

---

## 🧪 Testar a API

### Documentação interactiva (Swagger)

```
http://localhost:8000/docs
```

### cURL — Pesquisa básica

```bash
curl "http://localhost:8000/search?query=wireless+earbuds&pages=1"
```

### cURL — Download Excel

```bash
curl -o produtos.xlsx \
  "http://localhost:8000/export/excel?query=phone+case&pages=2"
```

### cURL — Export para Google Sheets

```bash
curl "http://localhost:8000/export/sheets?query=led+strip&sheet_id=SEU_ID"
```

---

## 📊 Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/search?query=X&pages=N` | Pesquisa e retorna JSON + guarda Excel |
| `GET` | `/export/excel?query=X&pages=N` | Retorna ficheiro `.xlsx` para download |
| `GET` | `/export/sheets?query=X&pages=N&sheet_id=ID` | Envia para Google Sheets |
| `GET` | `/docs` | Swagger UI |

---

## 🐳 Docker

### Build e arranque

```bash
docker build -t dhgate-scraper .
docker run -p 8000:8000 --env-file .env dhgate-scraper
```

### Docker Compose (opcional)

```yaml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
```

---

## 📋 Google Sheets (opcional)

1. Acede à [Google Cloud Console](https://console.cloud.google.com/)
2. Activa a **Google Sheets API** e a **Google Drive API**
3. Cria uma **Service Account** e descarrega o JSON de credenciais
4. Guarda o ficheiro como `credentials.json` na raiz do projecto
5. Partilha a tua Spreadsheet com o email da Service Account
6. Define `GOOGLE_CREDENTIALS_FILE` e `GOOGLE_SHEET_ID` no `.env`
7. Instala as dependências extra:

```bash
pip install gspread google-auth
```

---

## 🔧 Arquitectura do Scraper

O `scraper.py` usa múltiplos selectores CSS em cascata para ser resiliente a mudanças de layout:

```python
# Exemplo: extracção de preço com fallback
selectors = [".price-current", ".product-price", ".prd-price", "[class*='price']"]
```

Se o DHgate alterar classes CSS, basta adicionar o novo selector à lista — sem reescrever a lógica.

**Medidas anti-bloqueio:**
- Pool de User-Agents rotativos
- Delay aleatório entre requests (1.5–3.5s)
- Headers de browser realistas (`Referer`, `Accept-Language`, etc.)
- Session HTTP reutilizada por pesquisa

---

## ⚠️ Aviso Legal

Este projecto é para fins educativos. Antes de usar em produção, lê e respeita os [Termos de Serviço do DHgate](https://www.dhgate.com/information/terms.html). O scraping pode estar sujeito a restrições.

---

## 📄 Licença

MIT
