# 📖 Leitura Bíblica 2026

App web para acompanhar o plano de leitura bíblica anual, com login, progresso individual por usuário e redistribuição automática de leituras.

## Stack

- **Backend:** Python 3.11 + FastAPI
- **Banco de dados:** PostgreSQL
- **Auth:** JWT via cookie httpOnly + bcrypt
- **Email:** SMTP (Gmail ou qualquer provedor)
- **Deploy:** Railway

---

## 🚀 Deploy no Railway (passo a passo)

### 1. Pré-requisitos

- Conta no [Railway](https://railway.app) (gratuita)
- Conta no [GitHub](https://github.com) (gratuita)
- Git instalado na sua máquina

---

### 2. Subir o código no GitHub

```bash
# Na pasta do projeto
cd biblia-app
git init
git add .
git commit -m "primeiro commit"

# Crie um repositório no GitHub (github.com/new) e conecte:
git remote add origin https://github.com/SEU_USUARIO/biblia-app.git
git push -u origin main
```

---

### 3. Criar o projeto no Railway

1. Acesse [railway.app](https://railway.app) e faça login
2. Clique em **"New Project"**
3. Escolha **"Deploy from GitHub repo"**
4. Selecione o repositório `biblia-app`
5. Railway vai detectar automaticamente que é Python e iniciar o build

---

### 4. Adicionar o banco PostgreSQL

1. No projeto do Railway, clique em **"+ New"**
2. Escolha **"Database → Add PostgreSQL"**
3. O Railway vai criar o banco e disponibilizar a variável `DATABASE_URL` automaticamente

---

### 5. Configurar as variáveis de ambiente

No Railway, vá em **"Variables"** do seu serviço e adicione:

| Variável | Valor |
|----------|-------|
| `DATABASE_URL` | *(copiada automaticamente do PostgreSQL)* |
| `SECRET_KEY` | Uma string aleatória longa (ex: rode `openssl rand -hex 32`) |
| `APP_URL` | A URL do seu app (ex: `https://biblia-app.up.railway.app`) |
| `MAIL_USERNAME` | Seu email Gmail |
| `MAIL_PASSWORD` | Sua [senha de app do Gmail](https://myaccount.google.com/apppasswords) |
| `MAIL_FROM` | Mesmo email Gmail |

> **Nota:** As variáveis de email são opcionais para desenvolvimento. Sem elas, os links de recuperação de senha aparecem apenas no log do servidor.

---

### 6. Gerar SECRET_KEY

No terminal:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

### 7. Obter senha de app do Gmail

1. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Crie uma senha de app para "Outro" → nomeie como "Leitura Bíblica"
3. Use a senha gerada (16 caracteres) como `MAIL_PASSWORD`

> Você precisa ter verificação em 2 etapas ativada no Gmail.

---

### 8. Fazer o deploy

Após configurar as variáveis, o Railway vai fazer o redeploy automaticamente. Você pode acompanhar os logs em tempo real.

O app estará disponível na URL fornecida pelo Railway (ex: `https://biblia-app.up.railway.app`).

---

## 💻 Rodar localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Copiar e preencher o .env
cp .env.example .env
# Edite o .env com suas configurações

# Rodar o servidor
uvicorn main:app --reload
```

Acesse: http://localhost:8000

> Para rodar localmente sem PostgreSQL, você pode usar SQLite trocando `DATABASE_URL` por:
> `DATABASE_URL=sqlite:///./biblia.db`
> e instalando `pip install aiosqlite`

---

## 📁 Estrutura do projeto

```
biblia-app/
├── main.py                    # Entry point FastAPI
├── requirements.txt
├── Procfile                   # Comando de start para Railway
├── railway.toml               # Config Railway
├── .env.example               # Template de variáveis
├── backend/
│   ├── config.py              # Configurações (lê do .env)
│   ├── database.py            # Models SQLAlchemy
│   ├── auth.py                # JWT + bcrypt
│   ├── routes.py              # Todos os endpoints da API
│   ├── scheduler.py           # Lógica de distribuição de leituras
│   ├── plan_data.py           # As 365 leituras do plano
│   ├── schemas.py             # Schemas Pydantic
│   └── email_service.py       # Envio de email SMTP
└── frontend/
    ├── templates/
    │   ├── base.html          # Template base com estilos
    │   ├── login.html         # Página de login
    │   ├── register.html      # Página de cadastro
    │   ├── forgot_password.html
    │   ├── reset_password.html
    │   └── app.html           # App principal
    └── static/                # CSS/JS extras (se necessário)
```

---

## 🔌 Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/auth/register` | Criar conta |
| `POST` | `/api/auth/login` | Login |
| `POST` | `/api/auth/logout` | Logout |
| `GET`  | `/api/auth/me` | Usuário atual |
| `POST` | `/api/auth/forgot-password` | Solicitar reset de senha |
| `POST` | `/api/auth/reset-password` | Redefinir senha |
| `GET`  | `/api/progress` | Progresso completo do usuário |
| `POST` | `/api/progress/toggle` | Marcar/desmarcar leitura |

---

## 🧠 Como funciona a distribuição de leituras

1. Quando o usuário abre o app pela primeira vez no dia, o servidor calcula quais leituras estão pendentes
2. Distribui usando `floor + remainder`: `base = pendentes ÷ dias_restantes`, com os primeiros `N` dias levando `base+1`
3. O snapshot do dia é salvo no banco — não muda mais durante o dia
4. Se o usuário não concluir leituras de um dia, no dia seguinte elas aparecem redistribuídas automaticamente
5. O plano sempre termina exatamente em **31 de dezembro**
