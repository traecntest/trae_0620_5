from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.models import User
from ..schemas.schemas import (
    DishCreate, DishUpdate, DishInfo, DishListResponse,
    ResponseModel
)
from ..services.dish_service import DishService
from ..utils.auth import get_current_user, get_current_admin
from ..utils.response import success_response, error_response

router = APIRouter(prefix="/dishes", tags=["菜品管理"])


@router.get("", response_model=ResponseModel)
def get_dishes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类"),
    period: Optional[str] = Query(None, description="时段"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: str = Query("on", description="状态"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        filter_category = category
        if period and not category:
            filter_category = period
        
        dishes, total = DishService.get_dish_list(
            db, page, page_size, filter_category, keyword, status
        )
        
        dish_list = [DishInfo.from_orm(d).model_dump() for d in dishes]
        
        return success_response({
            "dishes": dish_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": dish_list
        })
    except Exception as e:
        return error_response(500, f"获取失败: {str(e)}")


@router.get("/{dish_id}", response_model=ResponseModel)
def get_dish(
    dish_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        dish = DishService.get_dish_by_id(db, dish_id)
        if not dish:
            return error_response(404, "菜品不存在")
        return success_response(DishInfo.from_orm(dish).model_dump())
    except Exception as e:
        return error_response(500, f"获取失败: {str(e)}")


@router.post("", response_model=ResponseModel)
def create_dish(
    dish_data: DishCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        dish = DishService.create_dish(db, dish_data.model_dump())
        return success_response(DishInfo.from_orm(dish).model_dump(), "创建成功")
    except Exception as e:
        return error_response(500, f"创建失败: {str(e)}")


@router.put("/{dish_id}", response_model=ResponseModel)
def update_dish(
    dish_id: int,
    dish_data: DishUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        dish = DishService.update_dish(db, dish_id, dish_data.model_dump(exclude_unset=True))
        if not dish:
            return error_response(404, "菜品不存在")
        return success_response(DishInfo.from_orm(dish).model_dump(), "更新成功")
    except Exception as e:
        return error_response(500, f"更新失败: {str(e)}")


@router.delete("/{dish_id}", response_model=ResponseModel)
def delete_dish(
    dish_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        success = DishService.delete_dish(db, dish_id)
        if not success:
            return error_response(404, "菜品不存在")
        return success_response(None, "删除成功")
    except Exception as e:
        return error_response(500, f"删除失败: {str(e)}")
