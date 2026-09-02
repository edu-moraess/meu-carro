# Meu Carro 🚗 — Gestão Inteligente de Veículos

**Meu Carro** é um produto mobile e backend de ponta, desenvolvido para permitir que proprietários de veículos acompanhem com facilidade seus abastecimentos, manutenções preventivas e gastos gerais, com inteligência artificial integrada através do **Google Gemini**.

---

## 🏛️ Arquitetura do Sistema

O projeto adota uma arquitetura limpa, desacoplada e escalável:

```
├── backend/                  # API REST em Python (FastAPI + SQLAlchemy)
│   ├── app/
│   │   ├── api/              # Endpoints (veículos, abastecimentos, manutenções, gastos, dashboard, IA)
│   │   ├── core/             # Configurações de ambiente e conexão com banco
│   │   ├── models/           # Modelos relacionais (vehicles, fuel_records, maintenance_records, expense_records)
│   │   ├── schemas/          # Schemas de validação e serialização Pydantic
│   │   ├── services/         # Regras de negócio, cálculos matemáticos e integração Gemini
│   │   └── main.py           # Ponto de entrada FastAPI com documentação Swagger/OpenAPI
│   ├── tests/                # Testes automatizados (pytest)
│   ├── requirements.txt      # Dependências Python
│   └── .env.example          # Modelo de variáveis de ambiente
│
├── mobile/                   # Aplicativo Mobile Multiplataforma (React Native + Expo)
│   ├── src/
│   │   ├── components/       # Componentes visuais reutilizáveis (MetricCard, ActivityItem, etc.)
│   │   ├── screens/          # Telas (Home, Abastecimentos, Manutenção, Gastos, Onboarding)
│   │   ├── services/         # Cliente HTTP (Axios) integrado à API
│   │   ├── navigation/       # Navegação com abas inferiores
│   │   └── types/            # Tipagens TypeScript completas
│   ├── tests/                # Testes de unidade mobile
│   └── package.json
│
├── app/                      # Implementação Nativa Android (Kotlin + Jetpack Compose + Room)
│   └── src/main/java/com/example/
│       ├── data/             # Room Database, DAOs, Entidades e Repositório Offline-First
│       ├── ui/               # Interface Material 3 automotiva de alta fidelidade
│       └── MainActivity.kt   # Atividade principal Android com Edge-to-Edge
│
└── README.md                 # Esta documentação
```

---

## 🔒 Segurança da Inteligência Artificial

- **Google Gemini API** é integrada **exclusivamente no backend**.
- A chave de API nunca é exposta no aplicativo mobile (`.env` isolado no servidor).
- **Confirmação Obrigatória do Usuário**: A IA processa linguagem natural e recibos, mas **nunca salva diretamente no banco**. Uma tela de confirmação permite ao usuário conferir, ajustar ou cancelar os dados extraídos antes da persistência.

---

## ⚙️ Regras de Negócio Implementadas

1. **Proteção do Odômetro**:
   - A quilometragem informada nunca pode diminuir silenciosamente. Se o usuário informar um valor inferior ao odômetro atual do veículo, o sistema emite um alerta explícito com confirmação obrigatória.
2. **Cálculo de Consumo Real**:
   - $\text{Consumo (km/L)} = \frac{\text{Distância Percorrida}}{\text{Litros Abastecidos}}$
   - O cálculo só é realizado a partir do segundo abastecimento com base no intervalo real. Nunca são inventados dados aleatórios.
3. **Custo por Quilômetro**:
   - $\text{Custo por km} = \frac{\text{Total de Gastos Acumulados}}{\text{Total de km Rodados}}$
4. **Manutenção Preventiva**:
   - O sistema monitora a quilometragem atual em relação aos serviços futuros e aciona avisos de atenção quando faltam menos de 1.000 km para o próximo serviço.
5. **Insights Inteligentes**:
   - Análise de variação de consumo entre os últimos abastecimentos.
   - Análise percentual de gastos (combustível vs. oficinas vs. despesas adicionais).

---

## 🚀 Como Executar o Backend (FastAPI)

### Pré-requisitos
- Python 3.10+
- pip e virtualenv

### 1. Configuração do ambiente
```bash
cd backend
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente
Copie o `.env.example` para `.env`:
```bash
cp .env.example .env
```
Edite o arquivo `.env` e configure sua `GEMINI_API_KEY`:
```env
DATABASE_URL="sqlite:///./meu_carro.db"
GEMINI_API_KEY="AIzaSy..."
GEMINI_MODEL="gemini-2.5-flash"
```

### 3. Iniciar o servidor de desenvolvimento
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
- Acesse a documentação interativa Swagger em: **`http://localhost:8000/docs`**
- Acesse o status da API em: **`http://localhost:8000/`**

### 4. Executar os Testes Automatizados
```bash
pytest backend/tests/ -v
```

---

## 📱 Como Executar o Mobile (React Native / Expo)

### Pré-requisitos
- Node.js 18+
- npm ou yarn
- Aplicativo **Expo Go** no smartphone ou emulador Android/iOS

### 1. Instalação das dependências
```bash
cd mobile
npm install
```

### 2. Iniciar o projeto Expo
```bash
npm start
```
- Pressione `a` para abrir no emulador Android.
- Pressione `i` para abrir no simulador iOS.
- Escaneie o QR Code no app **Expo Go** para rodar no seu celular físico.

---

## 🧪 Banco de Dados: SQLite para PostgreSQL

O MVP utiliza **SQLite** por padrão para praticidade e portabilidade local zero-config.
Toda a camada de banco foi estruturada com **SQLAlchemy 2.0**. Para migrar para **PostgreSQL** em produção:
1. Instale o driver: `pip install psycopg2-binary`
2. Altere no `.env`:
   ```env
   DATABASE_URL="postgresql://usuario:senha@localhost:5432/meucarro"
   ```
As tabelas e relacionamentos serão criados sem necessidade de alterações no código da aplicação.

---

## 🗺️ Roadmap de Próximas Fases

- [x] Cadastro e gestão do veículo com odômetro e dados privados de placa.
- [x] Abastecimentos com cálculo de consumo real e histórico completo.
- [x] Manutenções preventivas com alertas quando faltar menos de 1.000 km.
- [x] Controle de despesas gerais e gráficos por categoria.
- [x] Integração com Google Gemini para texto livre e leitura de comprovantes.
- [x] Tela obrigatória de conferência e confirmação antes de salvar registros de IA.
- [ ] Exportação de relatórios em formato PDF e planilha CSV para revenda ou declaração.
- [ ] Lembretes de vencimento de IPVA, licenciamento e seguro obrigatório via notificações push.
- [ ] Comparativo entre Etanol vs. Gasolina (regra dos 70% em tempo real com base no preço do posto).
