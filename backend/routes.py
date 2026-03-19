import json
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from backend.database import get_db, User, ReadingProgress, StreakLog, DaySnapshot, PasswordResetToken
from backend.auth import (
    verify_password, hash_password, create_access_token,
    get_current_user,
)
from backend.config import settings
from backend.schemas import (
    UserRegister, UserLogin, TokenOut, UserOut,
    ProgressResponse, ToggleRequest, ToggleResponse,
    ForgotPasswordRequest, ResetPasswordRequest, MessageResponse,
    DayData, ReadingItem,
)
from backend.scheduler import (
    build_day_snapshot, build_future_schedule,
    get_streak, get_today, date_key, get_end_date, days_apart
)
from backend.plan_data import PLAN
from backend.email_service import send_reset_email

router = APIRouter()


# ── AUTH ──────────────────────────────────────────────────────

@router.post("/auth/register", response_model=UserOut, status_code=201)
def register(body: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este email já está cadastrado")

    user = User(
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
        is_verified=True,  # skip email verification for simplicity
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenOut)
def login(body: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")

    token = create_access_token({"sub": str(user.id)})

    # Set cookie for browser-based access
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logout realizado"}


@router.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ── PASSWORD RESET ─────────────────────────────────────────────

@router.post("/auth/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    # Always return success to avoid email enumeration
    if not user:
        return MessageResponse(message="Se este email estiver cadastrado, você receberá as instruções em breve")

    # Invalidate old tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False
    ).update({"used": True})

    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=raw_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_token)
    db.commit()

    reset_url = f"{settings.APP_URL}/reset-password?token={raw_token}"
    send_reset_email(user.email, user.name, reset_url)

    return MessageResponse(message="Se este email estiver cadastrado, você receberá as instruções em breve")


@router.post("/auth/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token,
        PasswordResetToken.used == False,
    ).first()

    if not record or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Link inválido ou expirado")

    user = db.query(User).filter(User.id == record.user_id).first()
    user.hashed_password = hash_password(body.password)
    record.used = True
    db.commit()

    return MessageResponse(message="Senha redefinida com sucesso")


# ── PROGRESS ──────────────────────────────────────────────────

@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = get_today()
    today_str = date_key(today)

    # Done indices
    done_records = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.completed == True,
    ).all()
    done_indices = {r.reading_index for r in done_records}

    # Today's snapshot — create if missing
    snap_record = db.query(DaySnapshot).filter(
        DaySnapshot.user_id == current_user.id,
        DaySnapshot.date == today_str,
    ).first()

    if not snap_record:
        indices = build_day_snapshot(done_indices, today)
        snap_record = DaySnapshot(
            user_id=current_user.id,
            date=today_str,
            reading_indices=json.dumps(indices),
        )
        db.add(snap_record)
        db.commit()

    today_indices = json.loads(snap_record.reading_indices)

    # Build today's reading items
    today_readings = []
    for idx in today_indices:
        reading, category = PLAN[idx]
        today_readings.append(ReadingItem(
            index=idx,
            reading=reading,
            category=category,
            completed=idx in done_indices,
        ))

    # Future schedule (for plan view)
    future_sched = build_future_schedule(done_indices, today_indices, today)

    # Streak
    streak_log = db.query(StreakLog).filter(StreakLog.user_id == current_user.id).all()
    streak = get_streak(streak_log)

    # Stats
    total = len(PLAN)
    done_count = len(done_indices)
    pct = round(done_count / total * 100, 1)
    days_left = days_apart(today, get_end_date())
    pending = total - done_count
    per_day = max(1, -(-pending // (days_left + 1))) if days_left >= 0 else pending  # ceil division

    return ProgressResponse(
        total=total,
        done=done_count,
        pct=pct,
        days_left=days_left,
        per_day_today=len(today_indices),
        streak=streak,
        today=DayData(date=today_str, readings=today_readings),
        future=future_sched,
    )


@router.post("/progress/toggle", response_model=ToggleResponse)
def toggle_reading(
    body: ToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    idx = body.reading_index
    if idx < 0 or idx >= len(PLAN):
        raise HTTPException(status_code=400, detail="Índice inválido")

    today = get_today()
    today_str = date_key(today)

    # Get or create progress record
    record = db.query(ReadingProgress).filter(
        ReadingProgress.user_id == current_user.id,
        ReadingProgress.reading_index == idx,
    ).first()

    if record:
        record.completed = not record.completed
        record.completed_at = datetime.now(timezone.utc) if record.completed else None
    else:
        record = ReadingProgress(
            user_id=current_user.id,
            reading_index=idx,
            completed=True,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(record)

    db.flush()

    # Check if today is fully done
    snap_record = db.query(DaySnapshot).filter(
        DaySnapshot.user_id == current_user.id,
        DaySnapshot.date == today_str,
    ).first()

    day_complete = False
    if snap_record:
        today_indices = json.loads(snap_record.reading_indices)
        done_records = db.query(ReadingProgress).filter(
            ReadingProgress.user_id == current_user.id,
            ReadingProgress.completed == True,
        ).all()
        done_set = {r.reading_index for r in done_records}
        day_complete = all(i in done_set for i in today_indices)

        # Update streak log
        streak_record = db.query(StreakLog).filter(
            StreakLog.user_id == current_user.id,
            StreakLog.date == today_str,
        ).first()
        if streak_record:
            streak_record.completed = day_complete
        else:
            db.add(StreakLog(
                user_id=current_user.id,
                date=today_str,
                completed=day_complete,
            ))

    db.commit()

    streak_log = db.query(StreakLog).filter(StreakLog.user_id == current_user.id).all()
    streak = get_streak(streak_log)

    return ToggleResponse(
        reading_index=idx,
        completed=record.completed,
        day_complete=day_complete,
        streak=streak,
    )
