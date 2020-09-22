from datetime import datetime, timedelta

import bcrypt
from app.core.security import verify_password, create_access_token

from app.models import User
from app.errors import UnauthorizedError

def create_session(email: str, password: str) -> str:
    user = User.first_or_fail(email=email)
    
    try:
        if verify_password(password, user.password):
            token = create_access_token(user.uuid, timedelta(days=14))
            return str(token)
        else:
            raise UnauthorizedError
    except Exception:
        raise UnauthorizedError
