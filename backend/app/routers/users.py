from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.user_repo import user_repo
from app.schemas.user import UserResponse, UserUpdate, UserStats, ChangePasswordRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    from app.services.voucher_service import calcular_nivel
    current_user.nivel = calcular_nivel(current_user.xp_total)
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    update_data = data.model_dump(exclude_none=True)

    if "cpf" in update_data:
        from fastapi import HTTPException, status as http_status
        import re
        if current_user.cpf_locked:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, "CPF não pode ser alterado")
        if not current_user.cpf_edit_allowed:
            raise HTTPException(http_status.HTTP_403_FORBIDDEN, "Edição de CPF não autorizada")
        digits = re.sub(r"\D", "", update_data["cpf"])
        if len(digits) != 11:
            raise HTTPException(http_status.HTTP_400_BAD_REQUEST, "CPF inválido")
        from app.models.user import User as UserModel
        existing = db.query(UserModel).filter(UserModel.cpf == digits, UserModel.id != current_user.id).first()
        if existing:
            raise HTTPException(http_status.HTTP_409_CONFLICT, "CPF já cadastrado em outra conta")
        update_data["cpf"] = digits
        update_data["cpf_edit_allowed"] = False
        update_data["cpf_locked"] = True

    return user_repo.update(db, current_user, update_data)


@router.patch("/me/ack-cpf-notification", response_model=UserResponse)
def ack_cpf_notification(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.cpf_notified = True
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/stats", response_model=UserStats)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.coleta import Agendamento
    from app.models.missao import MissaoUsuario
    total_ag = db.query(Agendamento).filter(Agendamento.usuario_id == current_user.id).count()
    missoes_ok = db.query(MissaoUsuario).filter(
        MissaoUsuario.usuario_id == current_user.id, MissaoUsuario.status == "completed"
    ).count()
    from app.services.voucher_service import calcular_nivel
    return UserStats(
        xp_total=current_user.xp_total,
        nivel=calcular_nivel(current_user.xp_total),
        total_agendamentos=total_ag,
        missoes_concluidas=missoes_ok,
    )


@router.patch("/me/password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException, status
    from app.core.security import verify_password, hash_password
    if data.novaSenha != data.confirmacaoNovaSenha:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Confirmação de senha não confere")
    if not verify_password(data.senhaAtual, current_user.senha):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Senha atual incorreta")
    current_user.senha = hash_password(data.novaSenha)
    db.commit()
    return {"message": "Senha atualizada com sucesso"}
