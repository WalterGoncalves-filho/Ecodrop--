# EcoDrop — Project Memory

## Visão Geral

**EcoDrop v2** é uma aplicação web brasileira de gestão de reciclagem com sistema de fidelidade verde. Usuários levam materiais recicláveis a pontos de coleta, ganham **Eco Points (VoucherVerde)**, completam missões de sustentabilidade e resgatam vouchers em empresas parceiras.

**Tagline:** "Recicle · Ganhe · Preserve"

**Repositório:** https://github.com/WalterGoncalves-filho/EcoDrop--.git

---

## Stack Tecnológica

### Backend
- **Linguagem:** Python 3.12
- **Framework:** FastAPI 0.115.12
- **Servidor:** Uvicorn 0.30.1 (ASGI)
- **ORM:** SQLAlchemy 2.0.41 (tipo-anotado, declarativo)
- **Migrações:** Alembic 1.13.1
- **Banco de dados:** MySQL 8.0+ / PostgreSQL (selecionável via env)
- **Autenticação:** JWT (python-jose) + bcrypt
- **Validação:** Pydantic 2.11.4 + Pydantic Settings 2.9.1
- **Testes:** pytest, httpx, pytest-asyncio

### Frontend
- **Servidor:** Node.js 18+ + Express 4.22.2 (serve arquivos estáticos)
- **Cliente:** HTML5/CSS3/JavaScript vanilla — sem frameworks
- **Fontes:** Google Fonts (Sora, Playfair Display)
- **Padrão:** SPA mobile-first
- **PWA:** service worker + manifest.json

### Infra
- **Containers:** Docker + Docker Compose
- **DB no Docker:** PostgreSQL 16

---

## Estrutura de Diretórios

```
EcoDrop--/
├── backend/
│   ├── app/
│   │   ├── core/           # security.py, dependencies.py, exceptions.py
│   │   ├── models/         # SQLAlchemy models (21 classes)
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── routers/        # FastAPI route handlers (11 arquivos)
│   │   ├── services/       # Lógica de negócio (7 serviços)
│   │   ├── repositories/   # Camada de acesso ao banco
│   │   ├── seed/           # Dados iniciais (idempotente)
│   │   ├── config.py       # Classe Settings
│   │   ├── database.py     # Engine SQLAlchemy
│   │   └── main.py         # Inicialização da app FastAPI
│   ├── migrations/         # Versões Alembic
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   ├── index.html      # SPA principal (573 linhas)
│   │   ├── script.js       # Lógica cliente (1886 linhas)
│   │   ├── api.js          # Abstração HTTP (116 linhas)
│   │   ├── admin.js        # Interface admin
│   │   ├── service-worker.js
│   │   └── css/style.css
│   ├── server.js           # Express server
│   └── package.json
├── docs/                   # Documentação técnica
├── docker-compose.yml
└── .env.example
```

---

## Modelos de Banco de Dados (18 tabelas)

| Tabela | Propósito |
|--------|-----------|
| `usuarios` | Perfil do usuário (CPF, email, role, nível, XP, saldo) |
| `materiais` | Catálogo de materiais recicláveis |
| `pontos_coleta` | Pontos físicos de coleta com localização e horários |
| `ponto_materiais` | N:N — materiais aceitos por ponto |
| `operadores_ponto` | Operadores alocados em pontos de coleta |
| `agendamentos` | Reservas de horário em pontos de coleta |
| `entregas` | Registros de entrega de materiais |
| `entrega_itens` | Itens de cada entrega (material, qtd, pontos gerados) |
| `transacoes_carteira` | Histórico de transações da carteira |
| `parceiros` | Empresas parceiras que oferecem benefícios |
| `beneficios_parceiro` | Ofertas de desconto/crédito de parceiros |
| `resgates_voucher` | Resgates de voucher realizados |
| `missoes` | Missões de reciclagem ativas |
| `missoes_usuario` | Progresso do usuário nas missões |
| `bonus_mensais` | Metas coletivas mensais |
| `tickets_suporte` | Tickets de suporte |
| `interacoes_suporte` | Mensagens dos tickets de suporte |
| `refresh_tokens` | Gerenciamento de tokens JWT |

### Enums principais
- **Roles:** `user`, `operator`, `admin`
- **Unidades de material:** `kg`, `un`
- **Status de entrega:** `pending_confirmation` → `confirmed` / `rejected` → `cancelled`
- **Tipos de transação:** `credit`, `debit`, `bonus`, `reversal`, `adjustment`
- **Tipos de missão:** `material_weight`, `material_count`, `monthly_goal`
- **Prioridade de ticket:** `low`, `medium`, `high`
- **Tipos de benefício:** `discount`, `credit`, `cashback`, `bill_payment`

---

## Endpoints da API

**Base URL:** `http://localhost:8000`

| Prefixo | Arquivo | Descrição |
|---------|---------|-----------|
| `/auth` | `routers/auth.py` | Registro, login, refresh token, logout |
| `/users` | `routers/users.py` | Perfil, stats, troca de senha |
| `/vouchers` | `routers/vouchers.py` | Saldo, histórico, resgate |
| `/coleta` | `routers/coletas.py` | Pontos de coleta, agendamentos |
| `/deliveries` | `routers/deliveries.py` | Entregas (usuário e operador) |
| `/missoes` | `routers/missoes.py` | Missões ativas e progresso |
| `/parceiros` | `routers/parceiros.py` | Parceiros e benefícios |
| `/support` | `routers/suporte.py` | Tickets de suporte |
| `/totem` | `routers/totem.py` | Interface da máquina de coleta |
| `/admin` | `routers/admin.py` | Funções administrativas |
| `/health` | `main.py` | Verificação de saúde da API |

Documentação interativa: `http://localhost:8000/docs` (Swagger) e `/redoc`

---

## Variáveis de Ambiente

```env
# Banco de dados
DB_ENGINE=postgresql          # ou mysql
DB_USER=postgres
DB_PASSWORD=***
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecodrop_db

# JWT
SECRET_KEY=***
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=localhost:3001,...
CORS_ALLOW_ALL=true

# Frontend
PORT=3001
API_BASE=http://localhost:8000
```

---

## Comandos Úteis

### Backend
```bash
# Rodar localmente
uvicorn app.main:app --reload --port 8000

# Migrações
alembic revision --autogenerate -m "descrição"
alembic upgrade head

# Seed (idempotente, pode rodar múltiplas vezes)
python -m app.seed.seed_data

# Testes
pytest backend/tests/
```

### Frontend
```bash
npm install
npm run dev    # nodemon (hot reload)
npm start      # produção
```

### Docker
```bash
docker-compose up
docker-compose down
```

O `Dockerfile` do backend executa automaticamente `alembic upgrade head` + seed antes de iniciar o servidor.

---

## Arquitetura e Padrões

- **Repository Pattern** — camada de acesso a dados separada em `repositories/`
- **Service Layer** — lógica de negócio isolada em `services/`
- **Dependency Injection** — `Depends()` do FastAPI em todos os endpoints protegidos
- **Mixin Pattern** — `TimestampMixin` (created_at, updated_at), `CreatedAtMixin`
- **JWT Stateless** com refresh tokens armazenados em banco
- **Seed idempotente** — materiais, pontos e parceiros iniciais sem duplicações

---

## Sistema de Níveis e Eco Points

5 níveis baseados em XP acumulado. Níveis mais altos recebem desconto na hora de resgatar vouchers (0% a 20%):

1. Iniciante Verde
2. Coletor Consciente
3. Guardião Sustentável
4. Defensor Ecológico
5. Herói Amazônico

Cada entrega de material gera Eco Points proporcionais ao peso/quantidade e tipo do material.

---

## Documentação Técnica (`/docs`)

| Arquivo | Conteúdo |
|---------|---------|
| `TECH_STACK.md` | Visão geral das tecnologias |
| `DATABASE.md` | Schema completo + diagrama ER (Mermaid) |
| `ENDPOINTS.md` | Referência completa de endpoints |
| `ECO_POINTS.md` | Mecânica do sistema de pontos |
| `TOTEM_API.md` | Especificação da máquina de coleta |
| `requisitos_funcionais.md` | Requisitos funcionais |
| `requisitos_nao_funcionais.md` | Requisitos não-funcionais |
| `deploy-railway-ecodrop.md` | Guia de deploy no Railway |
| `caso_de_uso*.puml/.png` | Diagramas UML de casos de uso |

---

## Pontos de Entrada

| Serviço | URL | Arquivo |
|---------|-----|---------|
| Frontend | http://localhost:3001 | `frontend/server.js` |
| API | http://localhost:8000 | `backend/app/main.py` |
| Swagger | http://localhost:8000/docs | auto-gerado pelo FastAPI |
| ReDoc | http://localhost:8000/redoc | auto-gerado pelo FastAPI |

---

## Regras de Negócio Importantes

1. **Protocolo de entrega único** — mesmo após deleções, o número de protocolo não se repete (constraint de unicidade resolvida no commit `22801a9`).
2. **Operadores** só podem revisar entregas pendentes de seus próprios pontos de coleta.
3. **Resgate de voucher** aplica desconto de acordo com o nível do usuário, deduzido diretamente do saldo de Eco Points.
4. **CPF** é chave única de usuário e usado pelo Totem para validação sem login.
5. **Agendamentos** podem ser cancelados pelo usuário; o slot volta a ficar disponível.
6. **Missões** são verificadas automaticamente ao confirmar uma entrega.
