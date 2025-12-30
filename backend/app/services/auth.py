"""
Authentication service for JWT token handling and password management.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User, RefreshToken
from ..schemas import TokenData
from .database import get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# JWT settings
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str, datetime]:
    """
    Create a JWT refresh token with longer expiry.
    Returns: (token, jti, expires_at) tuple
    """
    jti = str(uuid.uuid4())
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt, jti, expire


def decode_refresh_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT refresh token.
    Returns: dict with {'user_id': str, 'jti': str} or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        # Verify this is a refresh token
        if payload.get("type") != "refresh":
            return None
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if user_id is None:
            return None
        return {
            "user_id": user_id,
            "jti": jti
        }
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return TokenData(user_id=user_id)
    except JWTError:
        return None


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get a user by their ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by their email address."""
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception

    user = get_user_by_id(db, token_data.user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency to optionally get the current user.
    Returns None if no token provided or token is invalid.
    Useful for endpoints that work with or without authentication.
    """
    if token is None:
        return None

    token_data = decode_access_token(token)
    if token_data is None:
        return None

    user = get_user_by_id(db, token_data.user_id)
    if user is None or not user.is_active:
        return None

    return user


# Refresh token management functions (Story 0.2)

def store_refresh_token(
    db: Session,
    user_id: str,
    jti: str,
    expires_at: datetime,
    family_id: Optional[str] = None
) -> RefreshToken:
    """
    Store a new refresh token in the database.
    If family_id not provided, generates a new one for token family tracking.
    """
    token = RefreshToken(
        jti=jti,
        user_id=user_id,
        expires_at=expires_at,
        family_id=family_id or str(uuid.uuid4())
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def is_refresh_token_valid(db: Session, jti: str) -> bool:
    """
    Check if refresh token exists and is not revoked.
    Returns False if token is revoked, expired, or doesn't exist.
    """
    token = db.query(RefreshToken).filter(
        RefreshToken.jti == jti,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    return token is not None


def revoke_refresh_token(db: Session, jti: str) -> bool:
    """
    Revoke a specific refresh token.
    Returns True if token was found and revoked, False otherwise.
    """
    token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if token:
        token.revoked = True
        token.revoked_at = datetime.utcnow()
        db.commit()
        return True
    return False


def revoke_all_user_tokens(db: Session, user_id: str) -> int:
    """
    Revoke all refresh tokens for a user.
    Returns count of tokens revoked.
    """
    result = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False
    ).update({"revoked": True, "revoked_at": datetime.utcnow()})
    db.commit()
    return result


def revoke_token_family(db: Session, family_id: str) -> int:
    """
    Revoke entire token family (for stolen token detection).
    Returns count of tokens revoked.
    """
    result = db.query(RefreshToken).filter(
        RefreshToken.family_id == family_id,
        RefreshToken.revoked == False
    ).update({"revoked": True, "revoked_at": datetime.utcnow()})
    db.commit()
    return result
