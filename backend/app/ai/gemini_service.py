import json
import re
import datetime
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from backend.app.config import settings
from backend.app.schemas.schemas import AiParsedData

class GeminiService:

    @staticmethod
    def parse_natural_text(user_text: str) -> AiParsedData:
        """
        Interpreta texto livre utilizando Google Gemini API exclusivamente no backend.
        Extrai informações estruturadas em JSON estrito com validação Pydantic.
        """
        api_key = settings.GEMINI_API_KEY
        today_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        if api_key and not api_key.startswith("your_"):
            prompt = f"""Você é o assistente inteligente de entrada de dados do app automotivo 'Meu Carro'.
Sua ÚNICA função é extrair entidades presentes no texto do usuário para JSON estrito.
Hoje é {today_iso}.

REGRAS ABSOLUTAS:
1. Retorne APENAS um objeto JSON válido, sem texto explicativo, sem markdown.
2. NUNCA invente números, preços, datas ou quilometragens não informados. Use null para campos ausentes.
3. Se a data for relativa como 'hoje', use '{today_iso}'. Se for 'ontem', calcule o dia anterior.
4. Tipo DEVE ser estritamente: "fuel", "maintenance" ou "expense".
5. Se for combustível, fuel_type deve ser: "gasoline", "ethanol", "diesel" ou "flex".
6. Se for manutenção, category deve ser uma de: "oil", "filters", "tires", "brakes", "suspension", "engine", "electrical", "inspection", "other".
7. Se for despesa geral, category deve ser uma de: "washing", "parking", "toll", "insurance", "documentation", "accessories", "fine", "other".
8. Forneça um campo 'confidence' entre 0.0 e 1.0. Se faltar dados vitais, use confidence menor que 0.8.

Estrutura JSON obrigatória:
{{
  "type": "fuel" | "maintenance" | "expense",
  "date": "YYYY-MM-DD" | null,
  "odometer": int | null,
  "liters": float | null,
  "price_per_liter": float | null,
  "total_cost": float | null,
  "fuel_type": string | null,
  "category": string | null,
  "description": string | null,
  "station": string | null,
  "workshop": string | null,
  "confidence": float
}}

Texto do usuário: "{user_text}"
"""
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.1
                }
            }

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={api_key}"
            try:
                data_bytes = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=data_bytes,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    if resp.status == 200:
                        body = json.loads(resp.read().decode('utf-8'))
                        candidates = body.get("candidates", [])
                        if candidates:
                            raw_text = candidates[0]["content"]["parts"][0]["text"]
                            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                            parsed = json.loads(clean_text)
                            return GeminiService._build_response(parsed, default_date=today_iso)
            except Exception:
                # Se houver erro de rede com a API externa, aciona parser seguro de fallback
                pass

        # Parser heurístico determinístico de fallback (para testes e modo offline)
        return GeminiService._fallback_regex_parser(user_text, today_iso)

    @staticmethod
    def analyze_receipt(receipt_text: Optional[str] = None, image_base64: Optional[str] = None) -> AiParsedData:
        """
        Analisa comprovante ou nota fiscal através do Gemini Multimodal.
        """
        api_key = settings.GEMINI_API_KEY
        today_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        if api_key and not api_key.startswith("your_") and image_base64:
            prompt = f"""Analise este cupom fiscal ou recibo de despesa veicular.
Hoje é {today_iso}.
Extraia apenas o que estiver realmente impresso no documento. NUNCA invente informações ausentes.
Retorne APENAS um JSON estrito:
{{
  "type": "fuel" | "maintenance" | "expense",
  "date": "YYYY-MM-DD" | null,
  "odometer": int | null,
  "liters": float | null,
  "price_per_liter": float | null,
  "total_cost": float | null,
  "fuel_type": string | null,
  "category": string | null,
  "description": string | null,
  "station": string | null,
  "workshop": string | null,
  "confidence": float
}}
"""
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inlineData": {"mimeType": "image/jpeg", "data": image_base64}}
                    ]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.0
                }
            }
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={api_key}"
            try:
                data_bytes = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=data_bytes,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=25) as resp:
                    if resp.status == 200:
                        body = json.loads(resp.read().decode('utf-8'))
                        candidates = body.get("candidates", [])
                        if candidates:
                            raw_text = candidates[0]["content"]["parts"][0]["text"]
                            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                            parsed = json.loads(clean_text)
                            return GeminiService._build_response(parsed, default_date=today_iso)
            except Exception:
                pass

        if receipt_text:
            return GeminiService._fallback_regex_parser(receipt_text, today_iso)

        return AiParsedData(
            type="fuel",
            date=today_iso,
            description="Recibo analisado",
            confidence=0.75
        )

    @staticmethod
    def _build_response(d: Dict[str, Any], default_date: str) -> AiParsedData:
        confidence = float(d.get("confidence", 0.95))
        return AiParsedData(
            type=str(d.get("type", "fuel")).lower(),
            date=d.get("date") or default_date,
            odometer=int(d["odometer"]) if d.get("odometer") is not None else None,
            liters=float(d["liters"]) if d.get("liters") is not None else None,
            price_per_liter=float(d["price_per_liter"]) if d.get("price_per_liter") is not None else None,
            total_cost=float(d["total_cost"]) if d.get("total_cost") is not None else None,
            fuel_type=d.get("fuel_type") or "gasoline",
            category=d.get("category"),
            description=d.get("description"),
            station=d.get("station"),
            workshop=d.get("workshop"),
            confidence=confidence
        )

    @staticmethod
    def _fallback_regex_parser(text: str, default_date: str) -> AiParsedData:
        lower = text.lower()
        is_maint = any(w in lower for w in ["troca", "revis", "oficina", "oleo", "óleo", "freio", "pneu", "filtro", "vela", "alinhamento"])
        is_exp = any(w in lower for w in ["lavagem", "estacionamento", "pedágio", "pedagio", "seguro", "ipva", "multa", "acessório", "licenciamento"])
        rec_type = "maintenance" if is_maint else ("expense" if is_exp else "fuel")

        # Odômetro
        odometer = None
        odo_match = re.search(r'(\d{1,3}(?:\.\d{3})*|\d{2,6})\s*(?:km|quilometros|kms)', lower)
        if odo_match:
            odometer = int(odo_match.group(1).replace(".", ""))

        # Litros
        liters = None
        liters_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:litros|litro|l\b)', lower)
        if liters_match:
            liters = float(liters_match.group(1).replace(",", "."))

        # Preço por litro
        price_per_liter = None
        price_match = re.search(r'(?:a|de|por)\s*r?\$?\s*(\d+[.,]\d{2})', lower)
        if price_match:
            price_per_liter = float(price_match.group(1).replace(",", "."))

        # Custo total
        total_cost = None
        total_match = re.search(r'(?:paguei|custou|total|deu|gastei|r\$)\s*(\d+(?:[.,]\d{2})?)', lower)
        if total_match:
            total_cost = float(total_match.group(1).replace(",", "."))
        elif liters and price_per_liter:
            total_cost = round(liters * price_per_liter, 2)

        # Tipo de combustível
        fuel_type = "gasoline"
        if "etanol" in lower or "álcool" in lower or "alcool" in lower:
            fuel_type = "ethanol"
        elif "diesel" in lower:
            fuel_type = "diesel"

        # Categoria de manutenção ou gasto
        category = "other"
        description = "Abastecimento"
        if is_maint:
            if "óleo" in lower or "oleo" in lower:
                category = "oil"
                description = "Troca de óleo"
            elif "filtro" in lower:
                category = "filters"
                description = "Troca de filtros"
            elif "pneu" in lower:
                category = "tires"
                description = "Pneus e alinhamento"
            elif "freio" in lower:
                category = "brakes"
                description = "Pastilhas e discos de freio"
            else:
                category = "inspection"
                description = "Revisão veicular"
        elif is_exp:
            if "lavagem" in lower:
                category = "washing"
                description = "Lavagem do veículo"
            elif "estacionamento" in lower:
                category = "parking"
                description = "Estacionamento"
            elif "pedágio" in lower or "pedagio" in lower:
                category = "toll"
                description = "Pedágio"
            elif "seguro" in lower:
                category = "insurance"
                description = "Seguro automotivo"
            elif "ipva" in lower:
                category = "documentation"
                description = "IPVA e taxas"

        confidence = 0.90 if (odometer or liters or total_cost) else 0.65

        return AiParsedData(
            type=rec_type,
            date=default_date,
            odometer=odometer,
            liters=liters,
            price_per_liter=price_per_liter,
            total_cost=total_cost,
            fuel_type=fuel_type,
            category=category,
            description=description,
            confidence=confidence
        )
