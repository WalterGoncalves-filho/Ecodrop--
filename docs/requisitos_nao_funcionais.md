# Requisitos Não Funcionais — EcoDrop v2

**Projeto:** EcoDrop — Plataforma de Gamificação de Reciclagem  
**Versão:** 2.0  
**Data:** 2026-05-24  
**Convenção:** `[Nome da Subseção.Identificador]`  

---

## Sumário

1. [Desempenho](#1-desempenho)
2. [Confiabilidade](#2-confiabilidade)
3. [Segurança](#3-segurança)
4. [Usabilidade](#4-usabilidade)
5. [Manutenibilidade](#5-manutenibilidade)
6. [Portabilidade](#6-portabilidade)
7. [Escalabilidade](#7-escalabilidade)
8. [Conformidade](#8-conformidade)

---

## 1. Desempenho

### [NF001]
**Tempo de Resposta da API**  
As respostas da API para operações de leitura (GET) devem ter latência inferior a **500 ms** em condições normais de carga (até 200 requisições simultâneas). Operações de escrita críticas (confirmação de entrega, resgate de voucher) devem responder em até **1 segundo**.

### [NF002]
**Throughput Mínimo**  
O sistema deve suportar no mínimo **500 requisições por minuto** sem degradação perceptível de desempenho, considerando a infraestrutura padrão de deploy (Docker + MySQL).

### [NF003]
**Atomicidade de Operações Críticas**  
Operações que envolvem múltiplas tabelas do banco de dados (confirmação de entrega, resgate de voucher, validação de coleta pelo admin, registro via totem) devem ser executadas em transações ACID, com rollback total em caso de falha em qualquer etapa.

### [NF004]
**Paginação de Listas**  
Todas as listagens que possam crescer de forma ilimitada (histórico de transações, lista de entregas, lista de tickets) devem suportar paginação com parâmetros `skip` e `limit`, evitando varredura completa de tabelas.

---

## 2. Confiabilidade

### [NF005]
**Disponibilidade do Sistema**  
O sistema deve estar disponível **99% do tempo** em ambiente de produção, com tolerância a falhas transitórias de banco de dados por meio de reconexão automática (connection pool do SQLAlchemy).

### [NF006]
**Imutabilidade do Histórico Financeiro**  
Transações da carteira (`transacoes_carteira`) não devem poder ser alteradas ou excluídas após sua criação. O saldo resultante de cada transação deve ser armazenado como snapshot, garantindo rastreabilidade mesmo que o cálculo seja refeito no futuro.

### [NF007]
**Unicidade de Protocolos de Entrega**  
O sistema deve garantir a unicidade do protocolo de entrega (`ECO-AAAAMMDD-XXXXXX`) mesmo em cenários de alta concorrência ou após exclusão de registros, utilizando sequência monotônica persistente.

### [NF008]
**Consistência de Saldo**  
O sistema deve garantir que o saldo do usuário nunca seja negativo. Toda operação de débito deve verificar o saldo disponível antes de efetuar a transação, com controle de concorrência no nível do banco de dados.

### [NF009]
**Integridade Referencial**  
O banco de dados deve manter integridade referencial entre todas as entidades relacionadas (entregas ↔ itens, usuários ↔ transações, missões ↔ progresso), por meio de chaves estrangeiras e constraints explícitas.

---

## 3. Segurança

### [NF010]
**Autenticação Stateless com JWT**  
O sistema deve utilizar tokens JWT assinados com algoritmo HS256 e chave secreta configurável via variável de ambiente (`SECRET_KEY`). O `access_token` deve ter validade de 30 minutos; o `refresh_token`, 7 dias.

### [NF011]
**Armazenamento Seguro de Senhas**  
As senhas dos usuários devem ser armazenadas exclusivamente como hash bcrypt, nunca em texto plano. O hash deve usar fator de custo compatível com as recomendações atuais do algoritmo.

### [NF012]
**Armazenamento Seguro de Refresh Tokens**  
Os `refresh_tokens` devem ser armazenados no banco de dados apenas em formato de hash SHA-256, nunca em texto plano. O token original deve trafegar somente no canal seguro (HTTPS) e ser descartado após o hash.

### [NF013]
**Autorização Baseada em Papel (RBAC)**  
O sistema deve verificar o papel (`role`) do usuário autenticado em cada rota protegida antes de executar a lógica de negócio. A ausência de papel suficiente deve retornar HTTP 403 com mensagem padronizada.

### [NF014]
**Isolamento de Dados por Operador**  
Um operador deve ter acesso apenas às entregas e dados do ponto de coleta ao qual está vinculado (tabela `operadores_ponto`). O sistema deve validar esse vínculo a cada requisição de revisão de entrega.

### [NF015]
**Configuração de CORS por Ambiente**  
O sistema deve permitir configuração de CORS (origens permitidas, métodos e cabeçalhos) por variável de ambiente, restringindo origens em produção e permitindo abertura apenas em ambiente de desenvolvimento.

### [NF016]
**Proteção de Variáveis Sensíveis**  
Credenciais, chaves de API e strings de conexão devem ser fornecidas exclusivamente via variáveis de ambiente (`.env`), nunca embutidas no código-fonte. O repositório não deve conter arquivos `.env` com valores reais.

### [NF017]
**Validação de Entrada**  
Todos os dados recebidos pela API devem ser validados por schemas Pydantic antes de qualquer processamento. Dados inválidos devem retornar HTTP 422 com detalhes do campo e do erro.

---

## 4. Usabilidade

### [NF018]
**Interface Mobile-First**  
A interface web deve ser projetada e otimizada prioritariamente para dispositivos móveis (smartphones), com layout responsivo que se adapte a telas a partir de 320px de largura.

### [NF019]
**Suporte a Progressive Web App (PWA)**  
A aplicação frontend deve ser instalável como PWA, com `manifest.json` configurado e Service Worker registrado, permitindo acesso ao ícone de atalho na tela inicial e comportamento básico offline (cache de assets estáticos).

### [NF020]
**Navegação por Abas Fixas**  
A navegação principal deve ser acessível por uma barra de abas fixa (bottom navigation) com no máximo 5 destinos: Home, Mapa, Carteira, Serviços e Perfil.

### [NF021]
**Máscaras de Entrada**  
O sistema deve aplicar máscaras automáticas nos campos de CPF (formato 000.000.000-00) e telefone (formato (00) 00000-0000) durante a digitação, sem necessidade de ação adicional do usuário.

### [NF022]
**Suporte a Temas Claro e Escuro**  
A interface deve suportar alternância entre tema claro e escuro por meio de variáveis CSS, respeitando a preferência do sistema operacional do usuário quando não houver seleção explícita.

### [NF023]
**Feedback Visual em Operações Assíncronas**  
O sistema deve exibir indicadores de carregamento (loading) durante chamadas à API e mensagens de confirmação ou erro imediatamente após a conclusão de operações críticas (resgate, entrega, agendamento).

---

## 5. Manutenibilidade

### [NF024]
**Arquitetura em Camadas**  
O backend deve seguir separação clara em camadas: `routers` (entrada HTTP), `services` (lógica de negócio), `repositories` (acesso a dados) e `models` (entidades ORM). Lógica de negócio não deve residir em routers ou models.

### [NF025]
**Migrações de Banco de Dados via Alembic**  
Toda alteração no schema do banco de dados deve ser gerenciada por migrations Alembic versionadas, permitindo upgrade e downgrade controlados sem perda de dados.

### [NF026]
**Documentação Automática da API**  
A API deve expor documentação interativa gerada automaticamente pelo FastAPI (Swagger UI em `/docs` e ReDoc em `/redoc`), incluindo schemas de requisição/resposta para todos os endpoints.

### [NF027]
**Configuração Centralizada**  
Todas as configurações de ambiente (URL do banco de dados, chaves JWT, configurações de CORS) devem ser lidas a partir de uma classe de settings centralizada (`app/config.py`), usando `pydantic-settings`.

### [NF028]
**Tratamento Global de Exceções**  
A aplicação deve registrar handlers globais para exceções não tratadas, retornando respostas JSON padronizadas com código HTTP adequado, sem expor stack traces em produção.

---

## 6. Portabilidade

### [NF029]
**Containerização com Docker**  
O backend e o frontend devem ser executáveis como containers Docker, com `Dockerfile` para cada serviço e `docker-compose.yml` para orquestração local, sem dependências de configuração do host.

### [NF030]
**Compatibilidade com Múltiplos Bancos de Dados**  
O backend deve ser compatível com MySQL 8+ e PostgreSQL 13+, utilizando dialetos SQLAlchemy sem SQL nativo específico de banco, exceto onde documentado explicitamente.

### [NF031]
**Independência de Sistema Operacional**  
O sistema deve ser executável em ambientes Linux, macOS e Windows (via Docker), sem dependência de APIs ou caminhos de sistema operacional específicos.

### [NF032]
**Compatibilidade de Navegadores**  
A interface frontend deve funcionar nos navegadores modernos (Chrome 90+, Firefox 90+, Safari 14+, Edge 90+) sem dependência de plugins ou extensões.

---

## 7. Escalabilidade

### [NF033]
**Stateless no Backend**  
O backend deve ser stateless: nenhum estado de sessão deve ser armazenado em memória da instância. Todo estado deve ser persistido no banco de dados, permitindo execução de múltiplas instâncias em paralelo.

### [NF034]
**Pool de Conexões com Banco de Dados**  
O sistema deve utilizar pool de conexões (SQLAlchemy `create_engine` com `pool_size` configurável) para reutilização eficiente de conexões com o banco de dados, evitando abertura de nova conexão por requisição.

### [NF035]
**Separação de Serviços por Container**  
A arquitetura de deploy deve separar backend, frontend e banco de dados em containers independentes, permitindo escalonamento horizontal de cada componente de forma independente.

---

## 8. Conformidade

### [NF036]
**Proteção de Dados Pessoais (LGPD)**  
O sistema deve armazenar apenas os dados pessoais estritamente necessários para a operação do serviço (nome, CPF, e-mail, telefone, endereço). O CPF deve ser utilizado exclusivamente para identificação e não deve ser exposto em respostas de API para terceiros.

### [NF037]
**Auditabilidade de Operações Financeiras**  
Toda movimentação de saldo (crédito, débito, bônus, estorno, ajuste) deve ser registrada na tabela `transacoes_carteira` com tipo, origem, valor, saldo resultante, descrição e timestamp, possibilitando auditoria completa do histórico financeiro.

### [NF038]
**Unicidade e Rastreabilidade de Vouchers**  
Cada voucher gerado deve possuir código único (baseado em UUID), data de expiração explícita e status rastreável (`generated` → `used` ou `expired` ou `cancelled`), permitindo verificação de autenticidade e controle de uso.