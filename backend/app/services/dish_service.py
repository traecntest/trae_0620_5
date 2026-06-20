from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..models.models import Dish


class DishService:
    @staticmethod
    def get_dish_list(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        keyword: Optional[str] = None,
        status: str = "on"
    ) -> Tuple[List[Dish], int]:
        query = db.query(Dish)
        
        if status:
            query = query.filter(Dish.status == status)
        
        if category and category != "all":
            query = query.filter(Dish.category == category)
        
        if keyword:
            query = query.filter(
                or_(
                    Dish.name.contains(keyword),
                    Dish.description.contains(keyword)
                )
            )
        
        total = query.count()
        dishes = query.order_by(Dish.id.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        
        return dishes, total

    @staticmethod
    def get_dish_by_id(db: Session, dish_id: int) -> Optional[Dish]:
        return db.query(Dish).filter(Dish.id == dish_id).first()

    @staticmethod
    def create_dish(db: Session, dish_data: dict) -> Dish:
        dish = Dish(**dish_data)
        db.add(dish)
        db.commit()
        db.refresh(dish)
        return dish

    @staticmethod
    def update_dish(db: Session, dish_id: int, dish_data: dict) -> Optional[Dish]:
        dish = DishService.get_dish_by_id(db, dish_id)
        if not dish:
            return None
        
        for key, value in dish_data.items():
            if value is not None:
                setattr(dish, key, value)
        
        db.commit()
        db.refresh(dish)
        return dish

    @staticmethod
    def delete_dish(db: Session, dish_id: int) -> bool:
        dish = DishService.get_dish_by_id(db, dish_id)
        if not dish:
            return False
        
        db.delete(dish)
        db.commit()
        return True
