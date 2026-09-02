# Meu Carro — Streamlit MVP

Versão web do Meu Carro construída em Python + Streamlit. O projeto original Android permanece no repositório; esta versão fica em `streamlit_app.py` para facilitar execução e deploy.

## Funcionalidades

- cadastro e login com senha protegida por bcrypt;
- período inicial de 30 dias de trial;
- cadastro de veículo;
- abastecimentos e cálculo de consumo;
- manutenção;
- despesas;
- histórico;
- dashboard com Plotly;
- registro assistido por Gemini (sem salvamento automático);
- insights baseados nos dados reais;
- feedback;
- SQLite para desenvolvimento local e PostgreSQL via `DATABASE_URL` para produção.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

Sem `DATABASE_URL`, a aplicação usa `meu_carro.db` localmente. Para produção, configure PostgreSQL.

## Secrets

No Streamlit Cloud, configure em **Settings → Secrets**:

```toml
DATABASE_URL = "postgresql+psycopg://..."
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-2.5-flash"
```

Não versione chaves ou senhas.

## Deploy no Streamlit Community Cloud

1. Selecione este repositório.
2. Branch: `feat/streamlit-mvp` (ou `main` depois do merge).
3. Main file path: `streamlit_app.py`.
4. Configure `DATABASE_URL` e, se quiser IA, `GEMINI_API_KEY` nos Secrets.
5. Faça o deploy.

## Observação de produção

O SQLite é adequado para desenvolvimento local. Para usuários reais, utilize PostgreSQL gerenciado. O cálculo financeiro e de consumo é feito no Python; o Gemini é apenas uma camada de interpretação/explicação e nunca grava automaticamente um registro.
