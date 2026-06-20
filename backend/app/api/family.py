from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.models import User
from ..schemas.schemas import (
    FamilyBindRequest, FamilyBindConfirmRequest,
    OrderSubmitRequest, ResponseModel
)
from ..services.family_service import FamilyService
from ..utils.auth import get_current_user
from ..utils.response import success_response, error_response

router = APIRouter(prefix="/family", tags=["亲属绑定"])


@router.post("/bind", response_model=ResponseModel)
@router.post("/invite", response_model=ResponseModel)
async def send_bind_request(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        body = await request.json()
        phone = body.get('phone') or body.get('elderly_phone')
        relation = body.get('relation', 'other')
        
        if not phone:
            raise ValueError("请输入手机号码")
        
        result = FamilyService.send_bind_request(
            db, current_user.id, phone, relation
        )
        return success_response(result, "绑定请求已发送")
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"操作失败: {str(e)}")


@router.post("/bind/confirm", response_model=ResponseModel)
async def confirm_bind_post(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role != "elderly":
            return error_response(403, "只有老人可以确认绑定")
        
        body = await request.json()
        bind_id = body.get('bind_id') or body.get('id')
        confirm = body.get('confirm', True)
        
        result = FamilyService.confirm_bind(
            db, current_user.id, bind_id, confirm
        )
        return success_response(result, result["message"])
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"操作失败: {str(e)}")


@router.put("/requests/{request_id}/accept", response_model=ResponseModel)
def accept_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role != "elderly":
            return error_response(403, "只有老人可以确认绑定")
        
        result = FamilyService.confirm_bind(
            db, current_user.id, request_id, True
        )
        return success_response(result, result["message"])
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"操作失败: {str(e)}")


@router.put("/requests/{request_id}/reject", response_model=ResponseModel)
def reject_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role != "elderly":
            return error_response(403, "只有老人可以确认绑定")
        
        result = FamilyService.confirm_bind(
            db, current_user.id, request_id, False
        )
        return success_response(result, result["message"])
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"操作失败: {str(e)}")


@router.post("/bind/unbind", response_model=ResponseModel)
@router.delete("/members/{bind_id}", response_model=ResponseModel)
def unbind(
    bind_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        success = FamilyService.unbind(db, current_user.id, bind_id)
        if not success:
            return error_response(404, "绑定关系不存在")
        return success_response(None, "解绑成功")
    except Exception as e:
        return error_response(500, f"操作失败: {str(e)}")


@router.get("/members", response_model=ResponseModel)
def get_family_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        members = FamilyService.get_family_members(
            db, current_user.id, current_user.role
        )
        
        pending = []
        if current_user.role == "elderly":
            pending = FamilyService.get_pending_requests(db, current_user.id)
        
        return success_response({
            "members": members,
            "pending": pending
        })
    except Exception as e:
        return error_response(500, f"获取失败: {str(e)}")


@router.get("/pending-requests", response_model=ResponseModel)
def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role != "elderly":
            return error_response(403, "只有老人可以查看绑定请求")
        
        requests = FamilyService.get_pending_requests(db, current_user.id)
        return success_response({"requests": requests, "pending": requests})
    except Exception as e:
        return error_response(500, f"获取失败: {str(e)}")


@router.post("/order-for", response_model=ResponseModel)
async def order_for_elderly(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role != "family":
            return error_response(403, "只有亲属可以代订")
        
        body = await request.json()
        elderly_user_id = body.get('elderly_user_id') or body.get('family_member_id')
        
        if not elderly_user_id:
            raise ValueError("请选择要代订的老人")
        
        from datetime import date
        meal_period = body.get('meal_period') or body.get('period')
        meal_date = body.get('meal_date') or date.today().isoformat()
        dining_type = body.get('dining_type') or body.get('delivery_type') or 'dinein'
        if dining_type == 'dine_in':
            dining_type = 'dinein'
        
        items_raw = body.get('items', [])
        items = []
        for item in items_raw:
            items.append({
                'dish_id': item.get('dish_id'),
                'quantity': item.get('quantity', 1),
                'price': item.get('price') or item.get('unit_price') or 0
            })
        
        order_data = {
            'meal_period': meal_period,
            'meal_date': meal_date,
            'items': items,
            'remark': body.get('remark', ''),
            'dining_type': dining_type
        }
        
        result = FamilyService.order_for_elderly(
            db, current_user.id, elderly_user_id, order_data
        )
        return success_response(result, "代订成功")
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(500, f"代订失败: {str(e)}")
