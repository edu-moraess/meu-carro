import json
import re
import datetime
from typing import Optional
from backend.app.core.config import settings
from backend.app.schemas.schemas import AiParsedData

class GeminiService:

    @staticmethod
    def parse_natural_text(user_text: str) -> AiParsedData:
        """
        Interpreta texto livre utilizando Google Gemini API (ou fallback inteligente caso API key não esteja setada)
        Retorna estrutura JSON estrita conforme requisitos.
        """
        api_key = settings.GEMINI_API_KEY
        if api_key and not api_key.startswith("your_"):
            try:
                import requests
                prompt = f"""
Você é o assistente inteligente do app 'Meu Carro'.
Analise o texto do usuário e extraia as informações estruturadas em JSON estrito.
Não invente valores ausentes, use null.
Hoje é {datetime.date.today().isoformat()}.

Estrutura JSON obrigatória:
{{
  "type": "fuel" | "maintenance" | "expense",
  "date": "YYYY-MM-DD" ou null,
  "odometer": int ou null,
  "liters": float ou null,
  "price_per_liter": float ou null,
  "total_cost": float ou null,
  "fuel_type": "gasoline" | "ethanol" | "diesel" | "flex" ou null,
  "category": "oil" | "filters" | "tires" | "brakes" | "suspension" | "engine" | "electrical" | "revision" | "wash" | "parking" | "toll" | "insurance" | "taxes" | "other" ou null,
  "description": "breve resumo" ou null,
  "station": "nome do posto" ou null,
  "workshop": "nome da oficina" ou null
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
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0]["content"]["parts"][0]["text"]
                        clean_text = text.replace("```json", "").replace("```", "").strip()
                        parsed = json.loads(clean_text)
                        return GeminiService._map_to_schema(parsed)
            except Exception as e:
                # Log e segue para parser determinístico
                pass

        # Parser heurístico de fallback para desenvolvimento/testes
        return GeminiService._fallback_regex_parser(user_text)

    @staticmethod
    def parse_receipt(receipt_text: Optional[str] = None, image_base64: Optional[str] = None) -> AiParsedData:
        """
        Extrai informações de recibo/cupom fiscal com Gemini Multimodal ou texto.
        """
        api_key = settings.GEMINI_API_KEY
        if api_key and not api_key.startswith("your_") and image_base64:
            try:
                import requests
                prompt = f"""
Analise este cupom fiscal / recibo de veículo.
Extraia SOMENTE informações realmente presentes no recibo.
Se não encontrar determinada informação, use null. NUNCA INVENTE.
Hoje é {datetime.date.today().isoformat()}.

Estrutura JSON obrigatória:
{{
  "type": "fuel" | "maintenance" | "expense",
  "date": "YYYY-MM-DD" ou null,
  "odometer": int ou null,
  "liters": float ou null,
  "price_per_liter": float ou null,
  "total_cost": float ou null,
  "fuel_type": "gasoline" | "ethanol" | "diesel" | "flex" ou null,
  "category": "oil" | "filters" | "tires" | "brakes" | "suspension" | "engine" | "electrical" | "revision" | "other" ou null,
  "description": "descrição do item/serviço" ou null,
  "station": "nome do estabelecimento" ou null,
  "workshop": "nome do estabelecimento" ou null
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
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0]["content"]["parts"][0]["text"]
                        clean_text = text.replace("```json", "").replace("```", "").strip()
                        parsed = json.loads(clean_text)
                        return GeminiService._map_to_schema(parsed)
            except Exception:
                pass

        if receipt_text:
            return GeminiService._fallback_regex_parser(receipt_text)

        return AiParsedData(
            type="fuel",
            date=datetime.date.today().isoformat(),
            description="Recibo analisado"
        )

    @staticmethod
    def _map_to_schema(d: dict) -> AiParsedData:
        return AiParsedData(
            type=d.get("type") or "fuel",
            date=d.get("date") or datetime.date.today().isoformat(),
            odometer=d.get("odometer"),
            liters=d.get("liters"),
            price_per_liter=d.get("price_per_liter"),
            total_cost=d.get("total_cost"),
            fuel_type=d.get("fuel_type") or "Gasolina",
            category=d.get("category"),
            description=d.get("description"),
            station=d.get("station"),
            workshop=d.get("workshop")
        )

    @staticmethod
    def _fallback_regex_parser(text: str) -> AiParsedData:
        lower = text.lower()
        is_maint = any(w in lower for w in ["troca", "revis", "oficina", "oleo", "óleo", "freio", "pneu", "filtro"])
        is_exp = any(w in lower for w in ["lavagem", "estacionamento", "pedágio", "pedagio", "seguro", "ipva"])
        rec_type = "maintenance" if is_maint else ("expense" if is_exp else "fuel")

        # Odômetro
        odometer = None
        odo_match = re.search(r'(\d{1,3}(?:\.\d{3})*|\d{2,6})\s*(?:km|quilometros)', lower)
        if odo_match:
            odometer = int(odo_match.group(1).replace(".", ""))

        # Litros
        liters = None
        liters_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:litros|litro|l\b)', lower)
        if liters_match:
            liters = float(liters_match.group(1).replace(",", "."))

        # Preço por litro
        price_per_liter = None
        price_match = re.search(r'a\s*(\d+[.,]\d{2})', lower)
        if price_match:
            price_per_liter = float(price_match.group(1).replace(",", "."))

        # Total cost
        total_cost = None
        total_match = re.search(r'(?:paguei|custou|total|r\$)\s*(\d+(?:[.,]\d{2})?)', lower)
        if total_match:
            total_cost = float(total_match.group(1).replace(",", "."))
        elif liters and price_per_liter:
            total_cost = round(liters * price_per_liter, 2)

        # Combustível
        fuel_type = "Gasolina"
        if "etanol" in lower or "álcool" in lower or "alcool" in lower:
            fuel_type = "Etanol"
        elif "diesel" in lower:
            fuel_type = "Diesel"

        # Categoria
        category = "Outro"
        if "óleo" in lower or "oleo" in lower:
            category = "Óleo"
        elif "pneu" in lower:
            category = "Pneus"
        elif "lavagem" in lower:
            category = "lavagem"

        description = "Troca de óleo" if (is_maint and "oleo" in lower) else ("Abastecimento" if rec_type == "fuel" else "Despesa")

        return AiParsedData(
            type=rec_type,
            date=datetime.date.today().isoformat(),
            odometer=odometer,
            liters=liters,
            price_per_liter=price_per_liter,
            total_cost=total_cost,
            fuel_type=fuel_type,
            category=category,
            description=description
        )
