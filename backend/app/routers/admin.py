import re
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.database import get_db
from app.models.coleta import Agendamento, Entrega, EntregaItem, PontoColeta
from app.models.material import Material
from app.models.suporte import InteracaoSuporte, TicketSuporte
from app.models.user import User
from app.services.voucher_service import creditar

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito a administradores")
    return current_user


# ── Schemas ──────────────────────────────────────────────────────────────────

class AgendamentoAdminResponse(BaseModel):
    id: int
    usuario_id: int
    usuario_nome: str
    usuario_email: str
    usuario_cpf: str
    ponto_nome: str
    data_agendada: str
    janela_inicio: str
    janela_fim: str
    status: str
    observacoes: str | None

    model_config = {"from_attributes": True}


class ValidarItemInput(BaseModel):
    material_id: int
    quantidade: float


class ValidarColetaInput(BaseModel):
    itens: list[ValidarItemInput]
    observacoes: str | None = None


# ── Rotas ─────────────────────────────────────────────────────────────────────

@router.get("/agendamentos", response_model=list[AgendamentoAdminResponse])
def listar_agendamentos(
    q: str | None = Query(None, description="Filtro por nome, email ou CPF"),
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    query = (
        db.query(Agendamento)
        .join(Agendamento.usuario)
        .filter(Agendamento.status.in_(["scheduled", "confirmed", "checked_in"]))
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            User.nome.ilike(like) | User.email.ilike(like) | User.cpf.ilike(like)
        )
    agendamentos = query.order_by(Agendamento.data_agendada.asc()).all()
    return [
        AgendamentoAdminResponse(
            id=a.id,
            usuario_id=a.usuario_id,
            usuario_nome=f"{a.usuario.nome} {a.usuario.sobrenome}".strip(),
            usuario_email=a.usuario.email,
            usuario_cpf=a.usuario.cpf or "",
            ponto_nome=a.ponto.nome,
            data_agendada=str(a.data_agendada),
            janela_inicio=str(a.janela_inicio),
            janela_fim=str(a.janela_fim),
            status=a.status,
            observacoes=a.observacoes,
        )
        for a in agendamentos
    ]


@router.post("/agendamentos/{agendamento_id}/validar", status_code=200)
def validar_coleta(
    agendamento_id: int,
    data: ValidarColetaInput,
    db: Session = Depends(get_db),
    admin: User = Depends(_require_admin),
):
    ag = db.get(Agendamento, agendamento_id)
    if not ag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agendamento não encontrado")
    if ag.status not in ("scheduled", "confirmed", "checked_in"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Agendamento não está em aberto")
    if not data.itens:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe ao menos um material")

    # Gerar protocolo
    hoje = datetime.now().date()
    count = db.query(Entrega).filter(
        Entrega.criado_em >= datetime.combine(hoje, datetime.min.time())
    ).count()
    protocolo = f"ECO-{hoje.strftime('%Y%m%d')}-{count + 1:06d}"

    entrega = Entrega(
        usuario_id=ag.usuario_id,
        ponto_id=ag.ponto_id,
        agendamento_id=ag.id,
        protocolo=protocolo,
        status="confirmed",
        observacoes_operador=data.observacoes,
        confirmado_por=admin.id,
        confirmado_em=datetime.now(),
    )
    db.add(entrega)
    db.flush()

    total_pontos = 0
    total_valor = Decimal("0")

    for item in data.itens:
        material = db.get(Material, item.material_id)
        if not material or material.status != "active":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Material ID {item.material_id} inválido")
        pontos = int(material.pontos_por_unidade * item.quantidade)
        valor = Decimal(str(material.valor_por_unidade)) * Decimal(str(item.quantidade))
        db.add(EntregaItem(
            entrega_id=entrega.id,
            material_id=material.id,
            quantidade=item.quantidade,
            unidade=material.unidade,
            pontos_gerados=pontos,
            valor_creditado=valor,
        ))
        total_pontos += pontos
        total_valor += valor

    ag.status = "completed"

    usuario = db.get(User, ag.usuario_id)
    creditar(db, usuario.id, Decimal(str(total_pontos)), f"Coleta validada: {protocolo}", origem="entrega_confirmada")
    usuario.xp_total += total_pontos

    db.commit()

    return {
        "protocolo": protocolo,
        "total_pontos": total_pontos,
        "total_valor": float(total_valor),
        "usuario": usuario.nome,
    }


@router.get("/materiais")
def listar_materiais(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    materiais = db.query(Material).filter(Material.status == "active").all()
    return [{"id": m.id, "nome": m.nome, "unidade": m.unidade, "pontos_por_unidade": m.pontos_por_unidade} for m in materiais]


# ── Suporte / Tickets ─────────────────────────────────────────────────────────

class TicketAdminResponse(BaseModel):
    id: int
    usuario_id: int
    usuario_nome: str
    usuario_email: str
    usuario_cpf: str
    category: str
    subject: str
    status: str
    priority: str
    createdAt: datetime
    updatedAt: datetime
    interactionCount: int
    messages: list[dict] = []

    model_config = {"from_attributes": True}


class AdminReplyInput(BaseModel):
    message: str
    new_status: str | None = None  # open | in_progress | resolved | closed


class GrantCpfInput(BaseModel):
    ticket_id: int | None = None  # fecha o ticket junto, se informado


class AdminFixCpfInput(BaseModel):
    cpf: str


@router.get("/tickets", response_model=list[TicketAdminResponse])
def admin_listar_tickets(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    q = db.query(TicketSuporte).join(TicketSuporte.usuario)
    if status_filter:
        q = q.filter(TicketSuporte.status == status_filter)
    tickets = q.order_by(TicketSuporte.atualizado_em.desc()).all()
    return [
        TicketAdminResponse(
            id=t.id,
            usuario_id=t.usuario_id,
            usuario_nome=f"{t.usuario.nome} {t.usuario.sobrenome}".strip(),
            usuario_email=t.usuario.email,
            usuario_cpf=t.usuario.cpf or "",
            category=t.categoria,
            subject=t.assunto,
            status=t.status,
            priority=t.prioridade,
            createdAt=t.criado_em,
            updatedAt=t.atualizado_em,
            interactionCount=len(t.interacoes),
            messages=[
                {"id": i.id, "authorId": i.autor_id, "authorName": i.autor.nome,
                 "message": i.mensagem, "createdAt": i.criado_em.isoformat()}
                for i in t.interacoes
            ],
        )
        for t in tickets
    ]


@router.post("/tickets/{ticket_id}/reply", response_model=TicketAdminResponse)
def admin_responder_ticket(
    ticket_id: int,
    data: AdminReplyInput,
    db: Session = Depends(get_db),
    admin: User = Depends(_require_admin),
):
    ticket = db.get(TicketSuporte, ticket_id)
    if not ticket:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket não encontrado")

    db.add(InteracaoSuporte(ticket_id=ticket.id, autor_id=admin.id, mensagem=data.message))

    if data.new_status:
        ticket.status = data.new_status
    elif ticket.status == "open":
        ticket.status = "in_progress"

    db.commit()
    db.refresh(ticket)

    return TicketAdminResponse(
        id=ticket.id,
        usuario_id=ticket.usuario_id,
        usuario_nome=f"{ticket.usuario.nome} {ticket.usuario.sobrenome}".strip(),
        usuario_email=ticket.usuario.email,
        usuario_cpf=ticket.usuario.cpf or "",
        category=ticket.categoria,
        subject=ticket.assunto,
        status=ticket.status,
        priority=ticket.prioridade,
        createdAt=ticket.criado_em,
        updatedAt=ticket.atualizado_em,
        interactionCount=len(ticket.interacoes),
        messages=[
            {"id": i.id, "authorId": i.autor_id, "authorName": i.autor.nome,
             "message": i.mensagem, "createdAt": i.criado_em.isoformat()}
            for i in ticket.interacoes
        ],
    )


@router.post("/users/{user_id}/grant-cpf-edit")
def admin_grant_cpf_edit(
    user_id: int,
    data: GrantCpfInput,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")

    user.cpf_edit_allowed = True
    user.cpf_notified = False  # garante que o alerta será exibido

    if data.ticket_id:
        ticket = db.get(TicketSuporte, data.ticket_id)
        if ticket and ticket.usuario_id == user_id:
            ticket.status = "resolved"

    db.commit()
    return {"message": "Permissão de edição de CPF concedida"}


@router.patch("/users/{user_id}/fix-cpf")
def admin_fix_cpf(
    user_id: int,
    data: AdminFixCpfInput,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    """Admin corrige o CPF diretamente, sem passar pela permissão do usuário."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")

    digits = re.sub(r"\D", "", data.cpf)
    if len(digits) != 11:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CPF inválido")

    existing = db.query(User).filter(User.cpf == digits, User.id != user_id).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "CPF já cadastrado em outra conta")

    user.cpf = digits
    user.cpf_edit_allowed = False
    user.cpf_locked = True
    db.commit()
    return {"message": "CPF corrigido com sucesso"}


# ── Gerenciamento de Usuários ─────────────────────────────────────────────────

class UserAdminResponse(BaseModel):
    id: int
    nome: str
    sobrenome: str
    email: str
    cpf: str
    telefone: str | None = None
    role: str
    status: str
    saldo: float
    xp_total: int
    nivel: int
    criado_em: datetime

    model_config = {"from_attributes": True}


class UserAdminCreate(BaseModel):
    nome: str
    sobrenome: str
    email: EmailStr
    cpf: str
    senha: str
    role: str = "user"
    status: str = "active"


class UserAdminUpdate(BaseModel):
    nome: str | None = None
    sobrenome: str | None = None
    email: EmailStr | None = None
    cpf: str | None = None
    telefone: str | None = None
    role: str | None = None
    status: str | None = None


@router.get("/usuarios", response_model=list[UserAdminResponse])
def admin_listar_usuarios(
    q: str | None = Query(None, description="Filtro por nome, email ou CPF"),
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter(
            User.nome.ilike(like) | User.email.ilike(like) | User.cpf.ilike(like)
        )
    return query.order_by(User.criado_em.desc()).all()


@router.get("/usuarios/{user_id}", response_model=UserAdminResponse)
def admin_get_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
    return user


@router.post("/usuarios", response_model=UserAdminResponse, status_code=201)
def admin_criar_usuario(
    data: UserAdminCreate,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    digits = re.sub(r"\D", "", data.cpf)
    if len(digits) != 11:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CPF inválido")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    if db.query(User).filter(User.cpf == digits).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "CPF já cadastrado")

    user = User(
        nome=data.nome,
        sobrenome=data.sobrenome,
        email=data.email,
        cpf=digits,
        senha=hash_password(data.senha),
        role=data.role,
        status=data.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/usuarios/{user_id}", response_model=UserAdminResponse)
def admin_editar_usuario(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")

    if data.email and data.email != user.email:
        if db.query(User).filter(User.email == data.email, User.id != user_id).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
        user.email = data.email

    if data.cpf:
        digits = re.sub(r"\D", "", data.cpf)
        if len(digits) != 11:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "CPF inválido")
        if db.query(User).filter(User.cpf == digits, User.id != user_id).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "CPF já cadastrado")
        user.cpf = digits

    for field in ("nome", "sobrenome", "telefone", "role", "status"):
        val = getattr(data, field)
        if val is not None:
            setattr(user, field, val)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/usuarios/{user_id}", status_code=204)
def admin_excluir_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(_require_admin),
):
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não é possível excluir sua própria conta")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
    db.delete(user)
    db.commit()
