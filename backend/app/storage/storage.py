import os
import uuid
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from backend.app.config import settings

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp"
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

class StorageProvider(ABC):

    @abstractmethod
    def save_file(self, content_bytes: bytes, mime_type: str) -> str:
        """Salva o arquivo e retorna URL ou chave pública de acesso."""
        pass

    @abstractmethod
    def delete_file(self, file_key: str) -> bool:
        """Exclui o arquivo armazenado."""
        pass


class LocalStorageProvider(StorageProvider):

    def __init__(self, base_dir: str = settings.LOCAL_STORAGE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, content_bytes: bytes, mime_type: str) -> str:
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type inválido: {mime_type}. Permitidos: {list(ALLOWED_MIME_TYPES.keys())}")
        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"Arquivo excede o tamanho máximo de 10MB")

        ext = ALLOWED_MIME_TYPES[mime_type]
        safe_name = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(self.base_dir, safe_name)
        with open(target_path, "wb") as f:
            f.write(content_bytes)
        return f"/uploads/{safe_name}"

    def delete_file(self, file_key: str) -> bool:
        try:
            filename = os.path.basename(file_key)
            target_path = os.path.join(self.base_dir, filename)
            if os.path.exists(target_path):
                os.remove(target_path)
                return True
            return False
        except Exception:
            return False


class S3StorageProvider(StorageProvider):

    def __init__(self):
        self.bucket = settings.STORAGE_BUCKET
        self.endpoint = settings.STORAGE_ENDPOINT

    def save_file(self, content_bytes: bytes, mime_type: str) -> str:
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type inválido: {mime_type}")
        if len(content_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValueError("Arquivo excede 10MB")

        ext = ALLOWED_MIME_TYPES[mime_type]
        safe_name = f"receipts/{uuid.uuid4().hex}{ext}"

        # Se boto3 estiver configurado em produção
        try:
            import boto3
            s3 = boto3.client(
                's3',
                endpoint_url=settings.STORAGE_ENDPOINT,
                aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=settings.STORAGE_SECRET_KEY
            )
            s3.put_object(
                Bucket=self.bucket,
                Key=safe_name,
                Body=content_bytes,
                ContentType=mime_type
            )
            return f"{self.endpoint}/{self.bucket}/{safe_name}" if self.endpoint else safe_name
        except Exception:
            # Fallback para local se S3 não estiver provisionado
            return LocalStorageProvider().save_file(content_bytes, mime_type)

    def delete_file(self, file_key: str) -> bool:
        try:
            import boto3
            s3 = boto3.client('s3')
            s3.delete_object(Bucket=self.bucket, Key=file_key)
            return True
        except Exception:
            return False

def get_storage_provider() -> StorageProvider:
    if settings.STORAGE_PROVIDER == "s3" and settings.STORAGE_ACCESS_KEY:
        return S3StorageProvider()
    return LocalStorageProvider()
