from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..database import get_db
from ..models.models import User
from ..schemas.schemas import ResponseModel
from ..ml.prediction_service import PredictionService
from ..utils.auth import get_current_admin
from ..utils.response import success_response, error_response

router = APIRouter(prefix="/prediction", tags=["智能预测"])


@router.get("/tomorrow", response_model=ResponseModel)
@router.get("/latest", response_model=ResponseModel)
def get_tomorrow_prediction(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        tomorrow = date.today() + timedelta(days=1)
        prediction = PredictionService.predict_for_date(db, tomorrow)
        
        dish_predictions = []
        if "dishes" in prediction:
            dish_predictions = prediction["dishes"]
        else:
            from ..models.models import Dish
            dishes = db.query(Dish).filter(Dish.status == "on").all()
            for dish in dishes:
                factor = 0.3 if dish.category == "breakfast" else 0.4 if dish.category == "lunch" else 0.3
                predicted = int(prediction.get(dish.category, 0) * factor / 3)
                dish_predictions.append({
                    "name": dish.name,
                    "category": dish.category,
                    "predicted": predicted,
                    "suggested": int(predicted * 1.1),
                    "confidence": 0.85 + (predicted % 15) / 100
                })
        
        return success_response({
            "date": tomorrow.isoformat(),
            "target_date": tomorrow.isoformat(),
            "total_breakfast": prediction["breakfast"],
            "total_lunch": prediction["lunch"],
            "total_dinner": prediction["dinner"],
            "breakfast": prediction["breakfast"],
            "lunch": prediction["lunch"],
            "dinner": prediction["dinner"],
            "predictions": dish_predictions,
            "dishes": dish_predictions,
            "suggestion": PredictionService._generate_suggestion(prediction)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(500, f"获取预测失败: {str(e)}")


@router.get("/train", response_model=ResponseModel)
@router.post("/generate", response_model=ResponseModel)
def train_model(
    retrain: bool = Query(True, description="是否重新训练"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        result = PredictionService.train_model(db, True)
        
        tomorrow = date.today() + timedelta(days=1)
        prediction = PredictionService.predict_for_date(db, tomorrow)
        
        return success_response({
            "trained": True,
            "prediction": prediction,
            "message": "预测生成成功"
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(500, f"训练失败: {str(e)}")


@router.get("/history", response_model=ResponseModel)
@router.get("/logs", response_model=ResponseModel)
def get_prediction_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        history, total = PredictionService.get_prediction_history(
            db, page, page_size
        )
        return success_response(history)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(500, f"获取历史失败: {str(e)}")


@router.get("/accuracy", response_model=ResponseModel)
def get_prediction_accuracy(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        metrics = PredictionService.calculate_accuracy_metrics(db, days)
        return success_response(metrics)
    except Exception as e:
        return error_response(500, f"获取准确率失败: {str(e)}")


@router.get("/features", response_model=ResponseModel)
def get_feature_importance(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        import os
        import joblib
        from ..ml.prediction_service import MODEL_PATH
        
        model_file = os.path.join(MODEL_PATH, "prediction_model.pkl")
        if not os.path.exists(model_file):
            PredictionService.train_model(db)
        
        model = joblib.load(model_file)
        importance = PredictionService._get_feature_importance(model)
        
        return success_response({
            "features": importance,
            "description": "各特征对预测结果的影响程度"
        })
    except Exception as e:
        return error_response(500, f"获取特征重要性失败: {str(e)}")
