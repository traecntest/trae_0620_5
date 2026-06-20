from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import User
from ..schemas.schemas import ResponseModel, VoiceRecognizeResponse
from ..services.voice_service import VoiceService
from ..utils.auth import get_current_user
from ..utils.response import success_response, error_response

router = APIRouter(prefix="/voice", tags=["语音辅助"])


@router.post("/recognize", response_model=ResponseModel)
async def recognize_speech(
    audio: UploadFile = File(..., description="音频文件"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        audio_data = await audio.read()
        
        result = await VoiceService.recognize_speech(audio_data)
        
        parsed = VoiceService.parse_order_command(result["text"])
        
        return success_response({
            "text": result["text"],
            "confidence": result["confidence"],
            "parsed": parsed
        })
    except Exception as e:
        return error_response(500, f"识别失败: {str(e)}")


@router.get("/parse", response_model=ResponseModel)
def parse_command(
    text: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        parsed = VoiceService.parse_order_command(text)
        return success_response(parsed)
    except Exception as e:
        return error_response(500, f"解析失败: {str(e)}")
