from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import User
from ..schemas.schemas import ResponseModel, UserInfo
from ..utils.auth import get_current_user
from ..utils.response import success_response, error_response

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=ResponseModel)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return success_response({
            "id": current_user.id,
            "phone": current_user.phone,
            "name": current_user.name,
            "role": current_user.role,
            "avatar": current_user.avatar,
            "birth_date": str(current_user.birth_date) if current_user.birth_date else None,
            "address": current_user.address
        })
    except Exception as e:
        return error_response(500, f"获取失败: {str(e)}")


@router.put("/profile", response_model=ResponseModel)
def update_profile(
    name: str = None,
    avatar: str = None,
    birth_date: str = None,
    address: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from datetime import datetime
        
        if name:
            current_user.name = name
        if avatar:
            current_user.avatar = avatar
        if birth_date:
            current_user.birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        if address:
            current_user.address = address
        
        db.commit()
        db.refresh(current_user)
        
        return success_response({
            "id": current_user.id,
            "phone": current_user.phone,
            "name": current_user.name,
            "role": current_user.role,
            "avatar": current_user.avatar,
            "birth_date": str(current_user.birth_date) if current_user.birth_date else None,
            "address": current_user.address
        }, "更新成功")
    except ValueError as e:
        return error_response(400, f"日期格式错误: {str(e)}")
    except Exception as e:
        return error_response(500, f"更新失败: {str(e)}")
