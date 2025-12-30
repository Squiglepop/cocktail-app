"""
Authentication router for user registration, login, and profile management.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..config import settings

# Rate limiter for auth endpoints - stricter than upload
limiter = Limiter(key_func=get_remote_address)
from ..models import User, RefreshToken
from ..schemas import UserCreate, UserLogin, UserUpdate, UserResponse, Token
from ..services.auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    get_user_by_email,
    get_user_by_id,
    store_refresh_token,
    is_refresh_token_valid,
    revoke_refresh_token,
    revoke_all_user_tokens,
    revoke_token_family,
)
from ..services.database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    """
    # Check if email already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        display_name=user_data.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, response: Response, user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns access token in body, sets refresh token as httpOnly cookie.
    """
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create short-lived access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )

    # Create refresh token and store in database (Story 0.2)
    refresh_token, jti, expires_at = create_refresh_token(data={"sub": user.id})
    store_refresh_token(db, user.id, jti, expires_at)

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,  # HTTPS only in production
        samesite="lax",  # CSRF protection
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth"  # Only sent to auth endpoints
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/token", response_model=Token)
@limiter.limit("10/minute")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token endpoint (for Swagger UI).
    Uses form data instead of JSON body.
    Sets refresh token as httpOnly cookie.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )

    # Create refresh token and store in database (Story 0.2)
    refresh_token, jti, expires_at = create_refresh_token(data={"sub": user.id})
    store_refresh_token(db, user.id, jti, expires_at)

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,  # HTTPS only in production
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth"
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
@limiter.limit("5/minute")
async def refresh_access_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Refresh the access token using the refresh token from httpOnly cookie.
    Returns new access token, optionally rotates refresh token.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate refresh token (Story 0.2)
    token_data = decode_refresh_token(refresh_token)
    if not token_data:
        response.delete_cookie(key="refresh_token", path="/api/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = token_data["jti"]
    user_id = token_data["user_id"]

    # Check if token exists and is valid in database (Story 0.2)
    if not is_refresh_token_valid(db, jti):
        # Token is revoked, expired, or doesn't exist
        # Check if it was revoked (possible token theft detection)
        old_token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        if old_token and old_token.revoked:
            # Token was already used and revoked - possible theft!
            # Revoke entire token family
            revoke_token_family(db, old_token.family_id)
            response.delete_cookie(key="refresh_token", path="/api/auth")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token reuse detected - all sessions revoked. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        response.delete_cookie(key="refresh_token", path="/api/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user and verify active
    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        response.delete_cookie(key="refresh_token", path="/api/auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get old token's family for rotation tracking (Story 0.2)
    old_token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    family_id = old_token.family_id if old_token else None

    # Revoke old refresh token (Story 0.2)
    revoke_refresh_token(db, jti)

    # Create new access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )

    # Issue new refresh token with same family_id (rotation - Story 0.2)
    new_refresh_token, new_jti, new_expires = create_refresh_token(data={"sub": user.id})
    store_refresh_token(db, user.id, new_jti, new_expires, family_id)

    # Set new refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.cookie_secure,  # HTTPS only in production
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth"
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Logout by revoking refresh token and clearing cookie (Story 0.2).
    Revokes the token in database before deleting cookie.
    Access token will expire on its own (short-lived).
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        # Try to decode and revoke the token
        token_data = decode_refresh_token(refresh_token)
        if token_data:
            jti = token_data["jti"]
            # Revoke token in database (Story 0.2)
            revoke_refresh_token(db, jti)

    # Always delete cookie and return success (even if token invalid/missing)
    response.delete_cookie(key="refresh_token", path="/api/auth")
    return {"message": "Successfully logged out"}


@router.post("/revoke-all")
@limiter.limit("3/hour")
async def revoke_all_tokens(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke all refresh tokens for the current user (Story 0.2).
    Useful for logging out from all devices at once.
    Requires authentication via access token.
    """
    # Revoke all refresh tokens for this user
    count = revoke_all_user_tokens(db, current_user.id)

    # Clear the current refresh token cookie
    response.delete_cookie(key="refresh_token", path="/api/auth")

    return {"message": f"Successfully revoked all sessions ({count} tokens)"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile.
    """
    if user_update.display_name is not None:
        current_user.display_name = user_update.display_name

    db.commit()
    db.refresh(current_user)

    return current_user
