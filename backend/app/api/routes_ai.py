from fastapi import APIRouter, HTTPException, Depends
from backend.app.schemas.schemas import AiParseRequest, AiReceiptRequest, AiParsedData
from backend.app.services.gemini_service import GeminiService

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/parse-text", response_model=AiParsedData)
def parse_text(payload: AiParseRequest):
    """
    Analisa texto natural e extrai campos estruturados (combustível, manutenção ou gasto).
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Texto não pode ser vazio")
    
    try:
        return GeminiService.parse_natural_text(payload.text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar com Gemini: {str(e)}")

@router.post("/analyze-receipt", response_model=AiParsedData)
def analyze_receipt(payload: AiReceiptRequest):
    """
    Analisa imagem de nota/recibo fiscal (base64) ou texto de OCR.
    """
    try:
        return GeminiService.analyze_receipt(
            receipt_text=payload.receipt_text,
            image_base64=payload.image_base64
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar recibo: {str(e)}")
