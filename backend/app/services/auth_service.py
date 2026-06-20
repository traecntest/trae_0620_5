from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.models import User, SmsCode
from ..config import settings
from ..utils.auth import hash_password, create_access_token, verify_password
from ..utils.helpers import generate_pickup_code


class AuthService:
    @staticmethod
    def send_sms_code(db: Session, phone: str) -> dict:
        expires_at = datetime.utcnow() + timedelta(minutes=settings.SMS_EXPIRE_MINUTES)
        
        sms_code = SmsCode(
            phone=phone,
            code=settings.SMS_TEST_CODE,
            expires_at=expires_at,
            used=False
        )
        db.add(sms_code)
        db.commit()
        
        return {
            "expire_minutes": settings.SMS_EXPIRE_MINUTES,
            "test_code": settings.SMS_TEST_CODE
        }

    @staticmethod
    def login_with_sms(db: Session, phone: str, code: str, role: str) -> dict:
        sms_code = db.query(SmsCode).filter(
            SmsCode.phone == phone,
            SmsCode.code == code,
            SmsCode.used == False,
            SmsCode.expires_at > datetime.utcnow()
        ).order_by(SmsCode.created_at.desc()).first()

        if not sms_code:
            raise ValueError("验证码错误或已过期")

        sms_code.used = True
        db.commit()

        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            default_name = f"用户{phone[-4:]}"
            user = User(
                phone=phone,
                name=default_name,
                role=role,
                password_hash=hash_password("123456")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif user.role != role:
            user.role = role
            db.commit()
            db.refresh(user)

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "name": user.name,
                "role": user.role,
                "avatar": user.avatar
            }
        }

    @staticmethod
    def admin_login(db: Session, phone: str, password: str) -> dict:
        user = db.query(User).filter(
            User.phone == phone,
            User.role == "admin"
        ).first()

        if not user or not user.password_hash:
            raise ValueError("账号或密码错误")

        if not verify_password(password, user.password_hash):
            raise ValueError("账号或密码错误")

        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "name": user.name,
                "role": user.role,
                "avatar": user.avatar
            }
        }
