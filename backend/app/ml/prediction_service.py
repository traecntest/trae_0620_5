import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

from ..models.models import Order, PredictionLog
from ..utils.helpers import is_weekend, get_season, is_holiday


MODEL_PATH = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_PATH, exist_ok=True)


class PredictionService:
    FEATURE_COLS = [
        "day_of_week", "is_weekend", "month", "season",
        "is_holiday", "temperature", "weather_condition",
        "is_extreme_weather", "has_activity", "activity_type",
        "last_7d_avg", "last_14d_avg", "same_day_last_week"
    ]
    
    CATEGORICAL_COLS = [
        "day_of_week", "month", "season", "weather_condition",
        "activity_type"
    ]
    
    NUMERIC_COLS = [
        "is_weekend", "is_holiday", "temperature",
        "is_extreme_weather", "has_activity",
        "last_7d_avg", "last_14d_avg", "same_day_last_week"
    ]

    @staticmethod
    def load_historical_data(db: Session, start_date: date, end_date: date) -> pd.DataFrame:
        orders = db.query(Order).filter(
            Order.meal_date >= start_date,
            Order.meal_date <= end_date,
            Order.status != "cancelled"
        ).all()
        
        data = []
        for order in orders:
            data.append({
                "date": order.meal_date,
                "meal_period": order.meal_period,
                "count": 1
            })
        
        df = pd.DataFrame(data)
        if df.empty:
            return df
        
        daily_counts = df.groupby(["date", "meal_period"]).agg(
            actual_count=("count", "sum")
        ).reset_index()
        
        return daily_counts

    @staticmethod
    def enrich_features(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        df["date"] = pd.to_datetime(df["date"])
        df["day_of_week"] = df["date"].dt.dayofweek
        df["is_weekend"] = df["date"].apply(lambda x: 1 if is_weekend(x.date()) else 0)
        df["month"] = df["date"].dt.month
        df["season"] = df["date"].apply(lambda x: get_season(x.date()))
        df["is_holiday"] = df["date"].apply(lambda x: 1 if is_holiday(x.date()) else 0)
        
        df["temperature"] = PredictionService._get_temperature_feature(df["date"])
        df["weather_condition"] = PredictionService._get_weather_feature(df["date"])
        df["is_extreme_weather"] = 0
        
        df["has_activity"] = PredictionService._get_activity_feature(df["date"])
        df["activity_type"] = "none"
        
        df = PredictionService._add_historical_features(df)
        
        return df

    @staticmethod
    def _get_temperature_feature(dates: pd.Series) -> pd.Series:
        np.random.seed(42)
        base_temp = 15
        seasonal = 10 * np.sin(2 * np.pi * (dates.dt.dayofyear - 80) / 365)
        noise = np.random.normal(0, 3, len(dates))
        return base_temp + seasonal + noise

    @staticmethod
    def _get_weather_feature(dates: pd.Series) -> pd.Series:
        conditions = ["sunny", "cloudy", "rainy", "snowy"]
        weights = [0.5, 0.3, 0.15, 0.05]
        np.random.seed(42)
        return np.random.choice(conditions, size=len(dates), p=weights)

    @staticmethod
    def _get_activity_feature(dates: pd.Series) -> pd.Series:
        np.random.seed(42)
        return np.random.choice([0, 1], size=len(dates), p=[0.85, 0.15])

    @staticmethod
    def _add_historical_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values("date")
        
        for period in ["breakfast", "lunch", "dinner"]:
            mask = df["meal_period"] == period
            period_df = df[mask].copy()
            
            period_df["last_7d_avg"] = period_df["actual_count"].rolling(
                window=7, min_periods=1
            ).mean().shift(1).fillna(method="bfill")
            
            period_df["last_14d_avg"] = period_df["actual_count"].rolling(
                window=14, min_periods=1
            ).mean().shift(1).fillna(method="bfill")
            
            period_df["same_day_last_week"] = period_df["actual_count"].shift(7).fillna(
                period_df["actual_count"].mean()
            )
            
            df.loc[mask, "last_7d_avg"] = period_df["last_7d_avg"]
            df.loc[mask, "last_14d_avg"] = period_df["last_14d_avg"]
            df.loc[mask, "same_day_last_week"] = period_df["same_day_last_week"]
        
        df["last_7d_avg"] = df["last_7d_avg"].fillna(df["last_7d_avg"].mean())
        df["last_14d_avg"] = df["last_14d_avg"].fillna(df["last_14d_avg"].mean())
        df["same_day_last_week"] = df["same_day_last_week"].fillna(df["same_day_last_week"].mean())
        
        return df

    @staticmethod
    def prepare_features_for_date(
        target_date: date,
        period: str,
        db: Session
    ) -> Dict:
        features = {}
        
        features["day_of_week"] = target_date.weekday()
        features["is_weekend"] = 1 if is_weekend(target_date) else 0
        features["month"] = target_date.month
        features["season"] = get_season(target_date)
        features["is_holiday"] = 1 if is_holiday(target_date) else 0
        
        day_of_year = target_date.timetuple().tm_yday
        features["temperature"] = 15 + 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        features["weather_condition"] = PredictionService._predict_weather(target_date)
        features["is_extreme_weather"] = 0
        features["has_activity"] = PredictionService._predict_activity(target_date)
        features["activity_type"] = "none"
        
        historical = PredictionService._get_historical_averages(
            db, target_date, period
        )
        features["last_7d_avg"] = historical["last_7d_avg"]
        features["last_14d_avg"] = historical["last_14d_avg"]
        features["same_day_last_week"] = historical["same_day_last_week"]
        
        return features

    @staticmethod
    def _predict_weather(target_date: date) -> str:
        conditions = ["sunny", "cloudy", "rainy", "snowy"]
        weights = [0.5, 0.3, 0.15, 0.05]
        seed = target_date.year * 10000 + target_date.month * 100 + target_date.day
        np.random.seed(seed)
        return np.random.choice(conditions, p=weights)

    @staticmethod
    def _predict_activity(target_date: date) -> int:
        seed = target_date.year * 10000 + target_date.month * 100 + target_date.day + 1000
        np.random.seed(seed)
        return np.random.choice([0, 1], p=[0.85, 0.15])

    @staticmethod
    def _get_historical_averages(
        db: Session,
        target_date: date,
        period: str
    ) -> Dict[str, float]:
        from sqlalchemy import func
        
        week_ago = target_date - timedelta(days=7)
        two_weeks_ago = target_date - timedelta(days=14)
        same_day_last_week = target_date - timedelta(days=7)
        
        last_7d = db.query(func.count(Order.id)).filter(
            Order.meal_date >= two_weeks_ago,
            Order.meal_date < target_date,
            Order.meal_period == period,
            Order.status != "cancelled"
        ).scalar() or 0
        
        last_14d = db.query(func.count(Order.id)).filter(
            Order.meal_date >= target_date - timedelta(days=21),
            Order.meal_date < target_date,
            Order.meal_period == period,
            Order.status != "cancelled"
        ).scalar() or 0
        
        same_day = db.query(func.count(Order.id)).filter(
            Order.meal_date == same_day_last_week,
            Order.meal_period == period,
            Order.status != "cancelled"
        ).scalar() or 0
        
        return {
            "last_7d_avg": last_7d / 7,
            "last_14d_avg": last_14d / 14,
            "same_day_last_week": same_day
        }

    @staticmethod
    def train_model(db: Session, retrain: bool = False) -> Dict[str, any]:
        model_file = os.path.join(MODEL_PATH, "prediction_model.pkl")
        encoder_file = os.path.join(MODEL_PATH, "encoder.pkl")
        
        if os.path.exists(model_file) and os.path.exists(encoder_file) and not retrain:
            return {
                "message": "模型已存在，使用现有模型",
                "model_path": model_file
            }
        
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
        
        raw_data = PredictionService.load_historical_data(db, start_date, end_date)
        
        if raw_data.empty:
            PredictionService._generate_mock_training_data(db)
            raw_data = PredictionService.load_historical_data(db, start_date, end_date)
        
        feature_data = PredictionService.enrich_features(raw_data)
        
        X = feature_data[PredictionService.FEATURE_COLS]
        y = feature_data["actual_count"]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), PredictionService.CATEGORICAL_COLS),
                ("num", "passthrough", PredictionService.NUMERIC_COLS)
            ]
        )
        
        model = Pipeline([
            ("preprocessor", preprocessor),
            ("regressor", GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            ))
        ])
        
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-6))) * 100
        
        joblib.dump(model, model_file)
        
        feature_importance = PredictionService._get_feature_importance(model)
        
        return {
            "message": "模型训练完成",
            "model_path": model_file,
            "metrics": {
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "mape": round(mape, 2),
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            },
            "feature_importance": feature_importance
        }

    @staticmethod
    def _get_feature_importance(model: Pipeline) -> List[Dict]:
        regressor = model.named_steps["regressor"]
        preprocessor = model.named_steps["preprocessor"]
        
        feature_names = []
        for name, transformer, cols in preprocessor.transformers_:
            if name == "cat":
                feature_names.extend(transformer.get_feature_names_out(cols).tolist())
            else:
                feature_names.extend(cols)
        
        importances = regressor.feature_importances_
        
        importance_dict = {}
        for feat, imp in zip(feature_names, importances):
            base_feat = feat.split("_")[0] if "_" in feat else feat
            if base_feat not in importance_dict:
                importance_dict[base_feat] = 0
            importance_dict[base_feat] += imp
        
        sorted_features = sorted(
            importance_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"feature": f, "importance": round(i, 4)}
            for f, i in sorted_features
        ]

    @staticmethod
    def _load_model() -> Optional[Pipeline]:
        model_file = os.path.join(MODEL_PATH, "prediction_model.pkl")
        if os.path.exists(model_file):
            return joblib.load(model_file)
        return None

    @staticmethod
    def predict_for_date(db: Session, target_date: date) -> Dict[str, int]:
        model = PredictionService._load_model()
        
        if model is None:
            training_result = PredictionService.train_model(db)
            model = PredictionService._load_model()
            if model is None:
                return PredictionService._fallback_prediction(target_date)
        
        predictions = {}
        features_used = {}
        
        for period in ["breakfast", "lunch", "dinner"]:
            features = PredictionService.prepare_features_for_date(
                target_date, period, db
            )
            features_used[period] = features
            
            X = pd.DataFrame([features])[PredictionService.FEATURE_COLS]
            prediction = model.predict(X)[0]
            predictions[period] = max(5, int(round(prediction)))
        
        log_entry = PredictionLog(
            prediction_date=target_date,
            prediction_data=predictions,
            features_used=features_used
        )
        db.add(log_entry)
        db.commit()
        
        return predictions

    @staticmethod
    def _fallback_prediction(target_date: date) -> Dict[str, int]:
        base = 50
        if is_weekend(target_date):
            base += 10
        if is_holiday(target_date):
            base += 15
        
        return {
            "breakfast": int(base * 0.7),
            "lunch": base,
            "dinner": int(base * 0.85)
        }

    @staticmethod
    def _generate_mock_training_data(db: Session):
        from decimal import Decimal
        from ..models.models import Order, OrderItem, User, Dish
        from ..utils.helpers import generate_order_no, generate_pickup_code
        
        user = db.query(User).first()
        if not user:
            user = User(
                phone="13800000001",
                name="测试用户",
                role="elderly",
                password_hash="$2b$12$test"
            )
            db.add(user)
            db.commit()
        
        dish = db.query(Dish).first()
        if not dish:
            dish = Dish(
                name="测试菜品",
                category="lunch",
                price=Decimal("10.00"),
                status="on"
            )
            db.add(dish)
            db.commit()
        
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=180)
        
        current = start_date
        while current <= end_date:
            base = 40
            if is_weekend(current):
                base += 15
            if is_holiday(current):
                base += 20
            
            day_of_year = current.timetuple().tm_yday
            seasonal = 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
            base += int(seasonal)
            
            for period, factor in [("breakfast", 0.7), ("lunch", 1.0), ("dinner", 0.85)]:
                count = max(10, int(base * factor + np.random.normal(0, 5)))
                
                for i in range(count):
                    order_no = generate_order_no()
                    order = Order(
                        order_no=order_no,
                        user_id=user.id,
                        total_amount=Decimal("10.00"),
                        meal_period=period,
                        meal_date=current,
                        pickup_code=generate_pickup_code(),
                        status="completed"
                    )
                    db.add(order)
                    db.flush()
                    
                    item = OrderItem(
                        order_id=order.id,
                        dish_id=dish.id,
                        quantity=1,
                        unit_price=Decimal("10.00"),
                        subtotal=Decimal("10.00")
                    )
                    db.add(item)
            
            current += timedelta(days=1)
        
        db.commit()

    @staticmethod
    def get_prediction_history(
        db: Session,
        page: int = 1,
        page_size: int = 30
    ) -> Tuple[List[Dict], int]:
        logs = db.query(PredictionLog).order_by(
            PredictionLog.prediction_date.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        total = db.query(PredictionLog).count()
        
        results = []
        for log in logs:
            from sqlalchemy import func
            
            actual_data = {}
            for period in ["breakfast", "lunch", "dinner"]:
                actual = db.query(func.count(Order.id)).filter(
                    Order.meal_date == log.prediction_date,
                    Order.meal_period == period,
                    Order.status != "cancelled"
                ).scalar() or 0
                actual_data[period] = actual
            
            pred_data = log.prediction_data if isinstance(log.prediction_data, dict) else {}
            
            accuracy = None
            if all(p in pred_data for p in ["breakfast", "lunch", "dinner"]):
                abs_errors = []
                for period in ["breakfast", "lunch", "dinner"]:
                    p = pred_data.get(period, 0)
                    a = actual_data.get(period, 0)
                    if a > 0:
                        abs_errors.append(abs(p - a) / a)
                if abs_errors:
                    accuracy = round((1 - np.mean(abs_errors)) * 100, 2)
            
            results.append({
                "date": log.prediction_date,
                "prediction": pred_data,
                "actual": actual_data,
                "accuracy": accuracy
            })
        
        return results, total

    @staticmethod
    def calculate_accuracy_metrics(db: Session, days: int = 30) -> Dict:
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=days)
        
        logs = db.query(PredictionLog).filter(
            PredictionLog.prediction_date >= start_date,
            PredictionLog.prediction_date <= end_date
        ).order_by(PredictionLog.prediction_date).all()
        
        if not logs:
            return {
                "avg_accuracy": 0,
                "mae": 0,
                "rmse": 0,
                "mape": 0,
                "data_points": 0
            }
        
        all_preds = []
        all_actuals = []
        accuracies = []
        
        from sqlalchemy import func
        
        for log in logs:
            pred_data = log.prediction_data if isinstance(log.prediction_data, dict) else {}
            
            for period in ["breakfast", "lunch", "dinner"]:
                p = pred_data.get(period, 0)
                a = db.query(func.count(Order.id)).filter(
                    Order.meal_date == log.prediction_date,
                    Order.meal_period == period,
                    Order.status != "cancelled"
                ).scalar() or 0
                
                all_preds.append(p)
                all_actuals.append(a)
                
                if a > 0:
                    accuracies.append(1 - abs(p - a) / a)
        
        if not all_preds:
            return {
                "avg_accuracy": 0,
                "mae": 0,
                "rmse": 0,
                "mape": 0,
                "data_points": 0
            }
        
        preds = np.array(all_preds)
        actuals = np.array(all_actuals)
        
        mae = mean_absolute_error(actuals, preds)
        rmse = np.sqrt(mean_squared_error(actuals, preds))
        mape = np.mean(np.abs((actuals - preds) / (actuals + 1e-6))) * 100
        avg_accuracy = np.mean(accuracies) * 100 if accuracies else 0
        
        return {
            "avg_accuracy": round(avg_accuracy, 2),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2),
            "data_points": len(all_preds)
        }

    @staticmethod
    def _generate_suggestion(prediction: Dict[str, int]) -> str:
        suggestions = []
        
        b = prediction.get("breakfast", 0)
        l = prediction.get("lunch", 0)
        d = prediction.get("dinner", 0)
        
        suggestions.append(f"早餐建议准备 {b} 人份")
        suggestions.append(f"午餐建议准备 {l} 人份")
        suggestions.append(f"晚餐建议准备 {d} 人份")
        
        total = b + l + d
        if total > 200:
            suggestions.append("⚠️ 预计用餐人数较多，建议增加备餐量10%作为安全余量")
        elif total < 50:
            suggestions.append("📉 预计用餐人数较少，注意控制备餐量避免浪费")
        
        peak = max(b, l, d)
        if peak == l:
            suggestions.append("📌 午餐为高峰时段，建议重点保障")
        elif peak == b:
            suggestions.append("📌 早餐为高峰时段，建议提前准备")
        else:
            suggestions.append("📌 晚餐为高峰时段，建议重点保障")
        
        return "；".join(suggestions)
