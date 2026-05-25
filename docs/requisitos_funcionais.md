# Requisitos Funcionais — EcoDrop v2

**Projeto:** EcoDrop — Plataforma de Gamificação de Reciclagem  
**Versão:** 2.0  
**Data:** 2026-05-24  
**Convenção:** `[Nome da Subseção.Identificador]`  

---

## Sumário

1. [Autenticação e Controle de Acesso](#1-autenticação-e-controle-de-acesso)
2. [Cadastro e Gestão de Usuários](#2-cadastro-e-gestão-de-usuários)
3. [Gestão de Pontos de Coleta](#3-gestão-de-pontos-de-coleta)
4. [Agendamento de Coleta](#4-agendamento-de-coleta)
5. [Registro e Validação de Entregas](#5-registro-e-validação-de-entregas)
6. [Carteira Digital — VoucherVerde](#6-carteira-digital--voucherverde)
7. [Gestão de Parceiros e Benefícios](#7-gestão-de-parceiros-e-benefícios)
8. [Missões e Gamificação](#8-missões-e-gamificação)
9. [Totem de Autoatendimento](#9-totem-de-autoatendimento)
10. [Painel Administrativo](#10-painel-administrativo)
11. [Operação de Ponto — Operador](#11-operação-de-ponto--operador)
12. [Suporte ao Usuário](#12-suporte-ao-usuário)

---

## 1. Autenticação e Controle de Acesso

### [RF001]
**Registro de Conta**  
O sistema deve permitir que um novo usuário crie uma conta informando nome, sobrenome, CPF, e-mail, senha e confirmação de senha. O CPF e o e-mail devem ser únicos no sistema.

### [RF002]
**Login com E-mail e Senha**  
O sistema deve autenticar o usuário por e-mail e senha, retornando um `access_token` (JWT, validade 30 minutos) e um `refresh_token` (validade 7 dias) em caso de credenciais válidas.

### [RF003]
**Renovação de Token (Refresh)**  
O sistema deve permitir a renovação do `access_token` a partir de um `refresh_token` válido e não revogado, sem necessidade de reautenticação com senha.

### [RF004]
**Logout**  
O sistema deve revogar o `refresh_token` do usuário ao receber uma requisição de logout, impedindo futuras renovações com esse token.

### [RF005]
**Controle de Acesso por Papel (Role-Based)**  
O sistema deve reconhecer três papéis de usuário — `user`, `operator` e `admin` — e restringir o acesso a recursos conforme o papel atribuído. Rotas administrativas devem ser acessíveis apenas ao papel `admin`; rotas de revisão de entrega devem ser acessíveis aos papéis `operator` e `admin`.

### [RF006]
**Bloqueio de Conta**  
O sistema deve impedir o acesso de usuários com status `inactive` ou `blocked`, retornando erro de autenticação com mensagem adequada.

---

## 2. Cadastro e Gestão de Usuários

### [RF007]
**Consulta de Perfil Próprio**  
O sistema deve permitir que o usuário autenticado consulte seus dados cadastrais: nome, sobrenome, CPF, e-mail, telefone e endereço completo.

### [RF008]
**Atualização de Dados Cadastrais**  
O sistema deve permitir que o usuário autenticado atualize nome, sobrenome, e-mail, telefone e endereço. A atualização de e-mail deve verificar a ausência de conflito com outros registros.

### [RF009]
**Alteração de Senha**  
O sistema deve permitir que o usuário autenticado altere sua senha, exigindo a confirmação da senha atual antes de registrar a nova.

### [RF010]
**Preenchimento Automático de Endereço por CEP**  
O sistema deve, ao receber um CEP válido, preencher automaticamente os campos de rua, bairro, cidade e estado do endereço do usuário.

### [RF011]
**Consulta de Estatísticas do Usuário**  
O sistema deve disponibilizar ao usuário autenticado um resumo com: XP total acumulado, nível atual, número de agendamentos realizados e número de missões concluídas.

---

## 3. Gestão de Pontos de Coleta

### [RF012]
**Listagem de Pontos de Coleta**  
O sistema deve listar os pontos de coleta com status `active`, exibindo nome, endereço, bairro, cidade, horário de funcionamento e materiais aceitos.

### [RF013]
**Filtro de Pontos por Material**  
O sistema deve permitir filtrar os pontos de coleta pelo tipo de material aceito (plástico, vidro, metal, papel, eletrônico, entre outros).

### [RF014]
**Filtro de Pontos por Cidade**  
O sistema deve permitir filtrar os pontos de coleta pela cidade informada.

### [RF015]
**Consulta de Detalhes de Ponto**  
O sistema deve permitir a consulta detalhada de um ponto de coleta específico, incluindo descrição, localização (latitude/longitude), horário de abertura e fechamento, e lista de materiais aceitos com seus respectivos status.

---

## 4. Agendamento de Coleta

### [RF016]
**Criação de Agendamento**  
O sistema deve permitir que o usuário autenticado crie um agendamento de entrega em um ponto de coleta ativo, informando ponto, data desejada, horário de início e horário de fim da janela de entrega.

### [RF017]
**Listagem de Agendamentos do Usuário**  
O sistema deve listar todos os agendamentos do usuário autenticado, incluindo ponto, data, janela horária, status e observações.

### [RF018]
**Atualização de Status do Agendamento**  
O sistema deve permitir a atualização do status de um agendamento pelos fluxos permitidos: `scheduled` → `confirmed`, `checked_in`, `completed` ou `cancelled`.

### [RF019]
**Cancelamento de Agendamento**  
O sistema deve permitir que o usuário cancele um agendamento com status `scheduled` ou `confirmed`, alterando seu status para `cancelled`.

---

## 5. Registro e Validação de Entregas

### [RF020]
**Registro de Entrega pelo Usuário**  
O sistema deve permitir que o usuário autenticado registre uma entrega, informando o ponto de coleta, os materiais entregues com suas quantidades e, opcionalmente, o agendamento vinculado e observações.

### [RF021]
**Cálculo Automático de Pontos e Valor**  
Ao registrar uma entrega, o sistema deve calcular automaticamente os pontos gerados e o valor a ser creditado para cada item, com base nas configurações do material (`pontos_por_unidade` e `valor_por_unidade`).

### [RF022]
**Geração de Protocolo de Entrega**  
O sistema deve gerar um protocolo único para cada entrega no formato `ECO-AAAAMMDD-XXXXXX` (sequencial, persistente mesmo após deleções).

### [RF023]
**Consulta de Entregas do Usuário**  
O sistema deve permitir que o usuário autenticado consulte o histórico de todas as suas entregas, com status, data, materiais, pontos gerados e protocolo.

### [RF024]
**Revisão de Entrega pelo Operador**  
O sistema deve permitir que o operador autenticado, vinculado ao ponto de coleta da entrega, revise e confirme ou rejeite entregas com status `pending_confirmation`.

### [RF025]
**Crédito de Saldo e XP ao Confirmar Entrega**  
Ao confirmar uma entrega, o sistema deve:
- Creditar o saldo em Eco Points ao usuário (transação do tipo `credit`);
- Incrementar o XP total do usuário;
- Atualizar o progresso de missões ativas relacionadas aos materiais entregues.

### [RF026]
**Consulta de Entregas Pendentes pelo Operador**  
O sistema deve listar ao operador as entregas com status `pending_confirmation` do seu ponto de coleta, em ordem cronológica.

---

## 6. Carteira Digital — VoucherVerde

### [RF027]
**Consulta de Saldo e Nível**  
O sistema deve permitir que o usuário autenticado consulte seu saldo atual em Eco Points, nível de gamificação, percentual de bônus ativo e progresso para o próximo nível.

### [RF028]
**Histórico de Transações da Carteira**  
O sistema deve listar o histórico de transações do usuário, contendo: tipo (`credit`, `debit`, `bonus`, `reversal`, `adjustment`), origem, valor, saldo resultante e descrição.

### [RF029]
**Resgate de Benefício com Eco Points**  
O sistema deve permitir que o usuário resgate um benefício de parceiro utilizando seu saldo em Eco Points, desde que o saldo seja suficiente. O sistema deve:
- Aplicar o bônus de nível ao valor efetivo do resgate;
- Debitar o valor do saldo (transação do tipo `debit`);
- Gerar um código único de resgate com validade de 30 dias.

### [RF030]
**Imutabilidade do Histórico de Transações**  
Todas as transações registradas na carteira devem ser imutáveis (somente leitura após criação), garantindo auditabilidade do saldo.

---

## 7. Gestão de Parceiros e Benefícios

### [RF031]
**Listagem de Parceiros**  
O sistema deve listar os parceiros com status `active`, exibindo nome, categoria, descrição, cidade e logomarca.

### [RF032]
**Filtro de Parceiros por Categoria**  
O sistema deve permitir filtrar a listagem de parceiros pela categoria (ex.: Supermercados, Farmácias, Alimentação, Contas/Serviços).

### [RF033]
**Consulta de Detalhes do Parceiro e Benefícios**  
O sistema deve permitir consultar os detalhes de um parceiro específico, incluindo todos os benefícios disponíveis com status `active`, seus tipos (`discount`, `credit`, `cashback`, `bill_payment`), custo em Eco Points e valor do desconto/crédito.

### [RF034]
**Controle de Validade de Voucher Resgatado**  
O sistema deve registrar a data de expiração de cada voucher gerado (30 dias após o resgate) e controlar seu status (`generated`, `used`, `expired`, `cancelled`).

---

## 8. Missões e Gamificação

### [RF035]
**Listagem de Missões Ativas do Usuário**  
O sistema deve listar as missões ativas (dentro do período vigente) do usuário autenticado, exibindo título, descrição, tipo, meta, progresso atual, percentual de conclusão e recompensa.

### [RF036]
**Atualização Automática de Progresso em Missões**  
Ao confirmar uma entrega, o sistema deve verificar todas as missões ativas do usuário cujo material seja compatível com os itens entregues, incrementando o progresso proporcional à quantidade entregue.

### [RF037]
**Conclusão Automática de Missão e Crédito de Recompensa**  
Quando o progresso de uma missão atingir ou ultrapassar a meta, o sistema deve:
- Atualizar o status da missão do usuário para `completed`;
- Registrar a data de conclusão;
- Creditar a recompensa: saldo em Eco Points (tipo `voucher`) ou XP (tipo `xp`).

### [RF038]
**Sistema de Níveis com XP**  
O sistema deve calcular o nível do usuário com base no XP total acumulado, seguindo a tabela:

| Nível | XP Mínimo | Título                 | Bônus de Resgate |
|-------|-----------|------------------------|------------------|
| 1     | 0         | Iniciante Verde        | 0%               |
| 2     | 100       | Coletor Ativo          | 5%               |
| 3     | 250       | Reciclador Dedicado    | 10%              |
| 4     | 500       | Guardião da Floresta   | 15%              |
| 5     | 1000      | Herói Amazônico        | 20%              |

### [RF039]
**Bônus Mensal de Metas**  
O sistema deve suportar a configuração de um bônus mensal com meta de reciclagem global. Ao atingir a meta, o usuário deve receber a recompensa definida para aquele mês.

### [RF040]
**Expiração de Missão Não Concluída**  
O sistema deve marcar como `expired` as missões cujo prazo (`fim_em`) foi ultrapassado sem que o usuário tenha atingido a meta.

---

## 9. Totem de Autoatendimento

### [RF041]
**Validação de Usuário por CPF no Totem**  
O sistema deve permitir que o totem identifique um usuário a partir do CPF informado, retornando nome, saldo atual e missão ativa compatível com o material coletado pelo totem (garrafa plástica 2L).

### [RF042]
**Registro de Coleta pelo Totem**  
O sistema deve registrar automaticamente uma entrega via totem, sem necessidade de revisão por operador. A operação deve ser atômica (ACID) e incluir:
- Criação da entrega com status `confirmed`;
- Criação dos itens de entrega com quantidade informada;
- Crédito de saldo (Eco Points) e XP ao usuário;
- Atualização do progresso em missões ativas.

### [RF043]
**Consulta de Histórico de Coletas no Totem**  
O sistema deve disponibilizar ao totem o histórico das últimas 10 entregas confirmadas de um usuário, identificado por ID.

### [RF044]
**Consulta de Missão Ativa Global via Totem**  
O sistema deve disponibilizar ao totem a missão ativa global vigente, sem necessidade de autenticação.

---

## 10. Painel Administrativo

### [RF045]
**Listagem de Agendamentos em Aberto pelo Admin**  
O sistema deve listar ao administrador todos os agendamentos com status `scheduled`, `confirmed` ou `checked_in`, com filtro por nome, e-mail ou CPF do usuário.

### [RF046]
**Validação de Coleta pelo Admin**  
O sistema deve permitir que o administrador valide uma coleta a partir de um agendamento, informando os materiais entregues e suas quantidades. A validação deve:
- Criar a entrega com status `confirmed` e os itens correspondentes;
- Gerar o protocolo único;
- Atualizar o status do agendamento para `completed`;
- Creditar saldo e XP ao usuário;
- Atualizar o progresso de missões ativas;
- Executar tudo em transação ACID.

### [RF047]
**Listagem de Materiais pelo Admin**  
O sistema deve disponibilizar ao administrador a lista de materiais ativos cadastrados, com ID, nome, unidade de medida e pontos por unidade.

---

## 11. Operação de Ponto — Operador

### [RF048]
**Visualização de Entregas Pendentes do Ponto**  
O sistema deve exibir ao operador apenas as entregas com status `pending_confirmation` referentes ao ponto de coleta ao qual ele está vinculado.

### [RF049]
**Confirmação de Entrega pelo Operador**  
O sistema deve permitir que o operador confirme uma entrega, registrando observações do operador e acionando o crédito de saldo, XP e atualização de missões.

### [RF050]
**Rejeição de Entrega pelo Operador**  
O sistema deve permitir que o operador rejeite uma entrega, registrando o motivo em campo de observações.

---

## 12. Suporte ao Usuário

### [RF051]
**Abertura de Ticket de Suporte**  
O sistema deve permitir que o usuário autenticado abra um ticket de suporte informando categoria, assunto, descrição e nível de prioridade (`low`, `medium`, `high`).

### [RF052]
**Listagem de Tickets do Usuário**  
O sistema deve listar todos os tickets do usuário autenticado, ordenados pela data de última atualização (mais recente primeiro), com status e prioridade.

### [RF053]
**Consulta de Detalhes e Thread de Ticket**  
O sistema deve permitir a consulta detalhada de um ticket, incluindo o histórico completo de interações (mensagens), com autor e data/hora de cada interação.

### [RF054]
**Resposta a Ticket de Suporte**  
O sistema deve permitir que o usuário autenticado adicione respostas a um ticket seu. Se o ticket estiver com status `resolved`, ele deve ser reaberto automaticamente para `open` ao receber nova mensagem.

### [RF055]
**Isolamento de Tickets por Usuário**  
O sistema deve garantir que cada usuário acesse apenas seus próprios tickets, impedindo visualização ou interação com tickets de terceiros.