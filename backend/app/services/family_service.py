from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.models import User, FamilyBind


class FamilyService:
    @staticmethod
    def send_bind_request(
        db: Session,
        family_user_id: int,
        elderly_phone: str,
        relation: str
    ) -> dict:
        elderly = db.query(User).filter(
            User.phone == elderly_phone,
            User.role == "elderly"
        ).first()
        
        if not elderly:
            raise ValueError("未找到该老人用户，请先让老人注册")
        
        existing_bind = db.query(FamilyBind).filter(
            FamilyBind.family_user_id == family_user_id,
            FamilyBind.elderly_user_id == elderly.id
        ).first()
        
        if existing_bind:
            if existing_bind.status == "active":
                raise ValueError("已经绑定该老人")
            elif existing_bind.status == "pending":
                raise ValueError("绑定请求已发送，等待老人确认")
        
        bind = FamilyBind(
            family_user_id=family_user_id,
            elderly_user_id=elderly.id,
            relation=relation,
            status="pending"
        )
        
        db.add(bind)
        db.commit()
        db.refresh(bind)
        
        return {
            "bind_id": bind.id,
            "elderly_user_id": elderly.id,
            "elderly_name": elderly.name,
            "elderly_phone": elderly.phone,
            "relation": relation,
            "status": "pending"
        }

    @staticmethod
    def confirm_bind(
        db: Session,
        elderly_user_id: int,
        bind_id: int,
        confirm: bool
    ) -> dict:
        bind = db.query(FamilyBind).filter(
            FamilyBind.id == bind_id,
            FamilyBind.elderly_user_id == elderly_user_id,
            FamilyBind.status == "pending"
        ).first()
        
        if not bind:
            raise ValueError("绑定请求不存在或已处理")
        
        if confirm:
            bind.status = "active"
            bind.confirmed_at = datetime.utcnow()
            message = "绑定成功"
        else:
            bind.status = "rejected"
            message = "已拒绝绑定请求"
        
        db.commit()
        db.refresh(bind)
        
        return {
            "bind_id": bind.id,
            "status": bind.status,
            "message": message
        }

    @staticmethod
    def unbind(
        db: Session,
        user_id: int,
        bind_id: int
    ) -> bool:
        bind = db.query(FamilyBind).filter(
            FamilyBind.id == bind_id,
            (FamilyBind.family_user_id == user_id) | (FamilyBind.elderly_user_id == user_id),
            FamilyBind.status == "active"
        ).first()
        
        if not bind:
            return False
        
        bind.status = "inactive"
        db.commit()
        return True

    @staticmethod
    def get_family_members(
        db: Session,
        user_id: int,
        user_role: str
    ) -> List[dict]:
        members = []
        
        if user_role == "family":
            binds = db.query(FamilyBind).filter(
                FamilyBind.family_user_id == user_id,
                FamilyBind.status == "active"
            ).all()
            
            for bind in binds:
                elderly = db.query(User).filter(User.id == bind.elderly_user_id).first()
                if elderly:
                    members.append({
                        "bind_id": bind.id,
                        "user_id": elderly.id,
                        "name": elderly.name,
                        "phone": elderly.phone,
                        "relation": bind.relation,
                        "status": bind.status,
                        "bound_at": bind.confirmed_at
                    })
        
        elif user_role == "elderly":
            binds = db.query(FamilyBind).filter(
                FamilyBind.elderly_user_id == user_id,
                FamilyBind.status == "active"
            ).all()
            
            for bind in binds:
                family = db.query(User).filter(User.id == bind.family_user_id).first()
                if family:
                    members.append({
                        "bind_id": bind.id,
                        "user_id": family.id,
                        "name": family.name,
                        "phone": family.phone,
                        "relation": bind.relation,
                        "status": bind.status,
                        "bound_at": bind.confirmed_at
                    })
        
        return members

    @staticmethod
    def get_pending_requests(
        db: Session,
        elderly_user_id: int
    ) -> List[dict]:
        binds = db.query(FamilyBind).filter(
            FamilyBind.elderly_user_id == elderly_user_id,
            FamilyBind.status == "pending"
        ).all()
        
        requests = []
        for bind in binds:
            family = db.query(User).filter(User.id == bind.family_user_id).first()
            if family:
                requests.append({
                    "bind_id": bind.id,
                    "family_user_id": family.id,
                    "family_name": family.name,
                    "family_phone": family.phone,
                    "relation": bind.relation,
                    "created_at": bind.created_at
                })
        
        return requests

    @staticmethod
    def order_for_elderly(
        db: Session,
        family_user_id: int,
        elderly_user_id: int,
        order_data: dict
    ) -> dict:
        bind = db.query(FamilyBind).filter(
            FamilyBind.family_user_id == family_user_id,
            FamilyBind.elderly_user_id == elderly_user_id,
            FamilyBind.status == "active"
        ).first()
        
        if not bind:
            raise ValueError("未绑定该老人，无法代订")
        
        from .order_service import OrderService
        
        return OrderService.create_order(
            db=db,
            user_id=family_user_id,
            meal_period=order_data["meal_period"],
            meal_date_str=order_data["meal_date"],
            items=order_data["items"],
            remark=order_data.get("remark"),
            elderly_user_id=elderly_user_id,
            dining_type=order_data.get("dining_type", "dinein")
        )
