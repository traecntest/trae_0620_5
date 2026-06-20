from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from ..database import get_db
from ..models.models import User
from ..schemas.schemas import (
    OrderSubmitRequest, OrderSubmitResponse, OrderListResponse,
    ResponseModel
)
from ..services.order_service import OrderService
from ..utils.auth import get_current_user, get_current_admin
from ..utils.response import success_response, error_response

router = APIRouter(prefix="/orders", tags=["订单管理"])


@router.get("", response_model=ResponseModel)
def get_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="订单状态"),
    meal_date: Optional[str] = Query(None, description="用餐日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        is_admin = current_user.role == "admin"
        orders, total = OrderService.get_order_list(
            db, current_user.id, page, page_size, status, meal_date, is_admin
        )
        return success_response({
            "orders": orders,
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": orders
        })
    except Exception as e:
        return error_response(500, f"获取失败: {str(e)}")


@router.post("", response_model=ResponseModel)
async def create_order(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        body = await request.json()
        
        meal_period = body.get('meal_period') or body.get('period')
        if not meal_period:
            raise ValueError("请选择用餐时段")
        
        meal_date = body.get('meal_date') or body.get('mealDate')
        if not meal_date:
            meal_date = date.today().isoformat()
        
        dining_type = body.get('dining_type') or body.get('delivery_type') or 'dine_in'
        if dining_type == 'dine_in':
            dining_type = 'dinein'
        
        elderly_user_id = body.get('elderly_user_id') or body.get('family_member_id')
        is_for_elderly = body.get('is_for_elderly') or (elderly_user_id is not None)
        
        remark = body.get('remark', '')
        
        items_raw = body.get('items', [])
        items = []
        for item in items_raw:
            items.append({
                'dish_id': item.get('dish_id'),
                'quantity': item.get('quantity', 1),
                'price': item.get('price') or item.get('unit_price') or 0
            })
        
        elderly_id = elderly_user_id if is_for_elderly else None
        
        result = OrderService.create_order(
            db=db,
            user_id=current_user.id,
            meal_period=meal_period,
            meal_date_str=meal_date,
            items=items,
            remark=remark,
            elderly_user_id=elderly_id,
            dining_type=dining_type
        )
        return success_response(result, "下单成功")
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(500, f"下单失败: {str(e)}")


@router.get("/{order_id}", response_model=ResponseModel)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        is_admin = current_user.role == "admin"
        order = OrderService.get_order_detail(db, order_id, current_user.id, is_admin)
        if not order:
            return error_response(404, "订单不存在")
        return success_response(order)
    except Exception as e:
        return error_response(500, f"获取失败: {str(e)}")


@router.put("/{order_id}/status", response_model=ResponseModel)
@router.put("/{order_id}/cancel", response_model=ResponseModel)
def update_order_status(
    order_id: int,
    status: str = Query("cancelled", description="新状态"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        is_admin = current_user.role == "admin"
        if not is_admin:
            status = "cancelled"
        
        order = OrderService.update_order_status(db, order_id, status)
        if not order:
            return error_response(404, "订单不存在")
        return success_response(None, "状态更新成功")
    except Exception as e:
        return error_response(500, f"更新失败: {str(e)}")


@router.get("/all", response_model=ResponseModel)
def get_all_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="订单状态"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        orders, total = OrderService.get_order_list(
            db, current_user.id, page, page_size, status, None, True
        )
        return success_response({
            "orders": orders,
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": orders
        })
    except Exception as e:
        return error_response(500, f"获取失败: {str(e)}")
