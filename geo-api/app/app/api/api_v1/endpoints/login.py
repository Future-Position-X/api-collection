from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas, services
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils import (
    generate_password_reset_token,
    send_reset_password_email,
    verify_password_reset_token,
)

router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = services.user.authenticate(
        email=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.uuid, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}", response_model=schemas.Msg)
def recover_password(
    email: str, new_password: str, db: Session = Depends(deps.get_db)
) -> Any:
    """
    Password Recovery
    """
    user = services.user.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(
        email=email, password=new_password
    )
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}


@router.get("/reset-password/", response_model=schemas.Msg)
def reset_password(token: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Reset password
    """
    email_password_tuple = verify_password_reset_token(token)
    if not email_password_tuple:
        raise HTTPException(status_code=400, detail="Invalid token")
    email, new_password = email_password_tuple
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = services.user.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    hashed_password = get_password_hash(new_password)
    user.password = hashed_password
    services.user.update_user(user.provider_uuid, user.uuid, user)
    return {"msg": "Password updated successfully"}
