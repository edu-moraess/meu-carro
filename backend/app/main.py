from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.routes import (
    auth,
    vehicle,
    fuel,
    maintenance,
    expenses,
    dashboard,
    ai,
    referral,
    feedback
)

# Cria tabelas caso ainda não criadas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend oficial da plataforma Meu Carro - Gestão Veicular Inteligente e Econômica com IA"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Rotas com prefixo da API v1
api_v1_prefix = settings.API_V1_STR

app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(vehicle.router, prefix=api_v1_prefix)
app.include_router(fuel.router, prefix=api_v1_prefix)
app.include_router(maintenance.router, prefix=api_v1_prefix)
app.include_router(expenses.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(ai.router, prefix=api_v1_prefix)
app.include_router(referral.router, prefix=api_v1_prefix)
app.include_router(feedback.router, prefix=api_v1_prefix)

# Compatibilidade também nas rotas raiz para flexibilidade dos clientes
app.include_router(auth.router)
app.include_router(vehicle.router)
app.include_router(fuel.router)
app.include_router(maintenance.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(referral.router)
app.include_router(feedback.router)

@app.get("/health", tags=["Sistema"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/", tags=["Sistema"])
def root():
    return {
        "message": "Meu Carro API está operando perfeitamente.",
        "docs": "/docs",
        "health": "/health"
    }
