from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from models.user_model import User, UserRole
from config.jwt import decode_token
from sqlalchemy.orm import Session
from config.database import get_db

bearer_scheme = HTTPBearer(auto_error = False)


async def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:

    if cred is None or cred.scheme.lower() != "bearer":
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Authorization header must be Bearer {token}")
    try:
        payload = decode_token(cred.credentials)
        sub = payload.get("sub")

        if not sub:
            raise ValueError("Missing sub claim")
        user = db.query(User).filter(User.id == sub).first()
        if not user:
            raise ValueError("User not found")
        return user
    
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = f"Invalid or expired token: {str(e)}")


def require_roles(*roles: UserRole):
    def _dep(current_user: User = Depends(get_current_user)) -> User:
        if roles and current_user.role not in roles:
            raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "Insufficient permissions")
        return current_user
    return _dep
