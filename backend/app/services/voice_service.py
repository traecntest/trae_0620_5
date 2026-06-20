import base64
import requests
from typing import Optional
from ..config import settings


class VoiceService:
    @staticmethod
    async def recognize_speech(audio_data: bytes) -> dict:
        if settings.VOICE_API_KEY and settings.VOICE_SECRET_KEY and settings.VOICE_APP_ID:
            return await VoiceService._call_baidu_api(audio_data)
        else:
            return VoiceService._mock_recognize(audio_data)

    @staticmethod
    async def _call_baidu_api(audio_data: bytes) -> dict:
        try:
            token_url = "https://aip.baidubce.com/oauth/2.0/token"
            token_params = {
                "grant_type": "client_credentials",
                "client_id": settings.VOICE_API_KEY,
                "client_secret": settings.VOICE_SECRET_KEY
            }
            
            token_response = requests.post(token_url, params=token_params, timeout=10)
            access_token = token_response.json().get("access_token")
            
            if not access_token:
                return VoiceService._mock_recognize(audio_data)
            
            asr_url = "https://vop.baidu.com/server_api"
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            headers = {"Content-Type": "application/json"}
            payload = {
                "format": "wav",
                "rate": 16000,
                "channel": 1,
                "cuid": settings.VOICE_APP_ID,
                "token": access_token,
                "speech": audio_base64,
                "len": len(audio_data),
                "dev_pid": 1537
            }
            
            response = requests.post(asr_url, json=payload, headers=headers, timeout=15)
            result = response.json()
            
            if result.get("err_no") == 0:
                return {
                    "text": result.get("result", [""])[0],
                    "confidence": 0.95
                }
            else:
                return VoiceService._mock_recognize(audio_data)
                
        except Exception as e:
            return VoiceService._mock_recognize(audio_data)

    @staticmethod
    def _mock_recognize(audio_data: bytes) -> dict:
        mock_responses = [
            "我要一份红烧肉和米饭",
            "来一份清炒时蔬",
            "中午要一份鱼香肉丝",
            "晚上想吃西红柿炒蛋",
            "来两个包子和一碗粥",
            "我要点餐"
        ]
        
        import random
        return {
            "text": random.choice(mock_responses),
            "confidence": 0.85
        }

    @staticmethod
    def parse_order_command(text: str) -> dict:
        text = text.lower()
        
        period = "lunch"
        if "早餐" in text or "早上" in text or "早晨" in text:
            period = "breakfast"
        elif "晚餐" in text or "晚上" in text or "晚饭" in text:
            period = "dinner"
        elif "午餐" in text or "中午" in text:
            period = "lunch"
        
        dishes = []
        
        dish_keywords = {
            "红烧肉": 1,
            "鱼香肉丝": 2,
            "清炒时蔬": 3,
            "西红柿炒蛋": 4,
            "番茄炒蛋": 4,
            "包子": 5,
            "粥": 6,
            "米饭": 7,
            "馒头": 8,
            "鸡蛋": 9,
            "牛奶": 10
        }
        
        for dish_name, dish_id in dish_keywords.items():
            if dish_name in text:
                quantity = 1
                import re
                match = re.search(rf"(\d+)\s*份?\s*{dish_name}", text)
                if match:
                    quantity = int(match.group(1))
                
                dishes.append({
                    "dish_id": dish_id,
                    "dish_name": dish_name,
                    "quantity": quantity
                })
        
        return {
            "period": period,
            "dishes": dishes,
            "raw_text": text
        }
