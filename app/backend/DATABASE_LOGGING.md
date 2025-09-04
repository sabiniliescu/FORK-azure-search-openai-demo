# Configurație Database Logging pentru MihAI Web

Această aplicație include un sistem de logging pentru chat-uri care salvează informațiile în baza de date Azure SQL.

## Variabile de mediu necesare

Pentru a activa logging-ul în baza de date Azure SQL, adaugă următoarele variabile în fișierul `.env` sau setează-le în mediul de deployment:

```bash
# Azure SQL Database Configuration pentru Logging
AZURE_SQL_SERVER=mihaiweb.database.windows.net
AZURE_SQL_DATABASE=MihAI_Web_logs
AZURE_SQL_USERNAME=your_username
AZURE_SQL_PASSWORD=your_password
```

## Funcționare

### Logging automat
- Aplicația loghează automat toate conversațiile în baza de date
- Dacă baza de date nu este disponibilă, aplicația continuă să funcționeze normal
- Logging-ul se face asincron pentru a nu bloca operațiile principale

### Informații logged
- **Conversation ID**: Identificator unic pentru conversație
- **Request ID**: Identificator unic pentru fiecare request
- **Question**: Întrebarea utilizatorului
- **Answer**: Răspunsul sistemului
- **Timestamp Start**: Când a început procesarea
- **Timestamp End**: Când s-a terminat procesarea
- **Feedback**: Feedback-ul utilizatorului (positive/negative)
- **Feedback Text**: Textul explicativ al feedback-ului
- **User ID**: ID-ul utilizatorului din Azure AD
- **Tokens Used**: Numărul de tokeni utilizați
- **Model Used**: Modelul AI utilizat
- **Temperature**: Parametrul de temperatură
- **Session ID**: ID-ul sesiunii
- **Prompt Text**: Textul complet al prompt-ului
- **Duration**: Durata procesării în secunde

### Schema bazei de date

Aplicația creează automat tabela `chat_logs` cu următoarea structură:

```sql
CREATE TABLE chat_logs (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    conversation_id NVARCHAR(255) NOT NULL,
    request_id NVARCHAR(255) NULL,
    question NVARCHAR(MAX) NULL,
    answer NVARCHAR(MAX) NULL,
    timestamp_start DATETIME2 NOT NULL,
    timestamp_start_streaming DATETIME2 NULL,
    timestamp_end DATETIME2 NULL,
    feedback NVARCHAR(50) NULL,
    feedback_text NVARCHAR(MAX) NULL,
    user_id NVARCHAR(255) NULL,
    model_used NVARCHAR(255) NULL,
    temperature FLOAT NULL,
    prompt_text NVARCHAR(MAX) NULL,
    prompt_total_token_usage INT NULL,
    agentic_retrival_total_token_usage INT NULL,
    agentic_retrival_duration_seconds FLOAT NULL,
    duration_seconds FLOAT NULL
);
```

### Resilience și Error Handling

- **Conexiuni cu retry robust**: Sistemul folosește tenacity pentru retry logic cu exponential backoff (5 încercări, până la 30s delay)
- **Handling pentru serverless**: Detectează și gestionează erorile specifice Azure SQL Serverless (40613, 40615)
- **Timeouts configurabile**: Conexiunile au timeout de 60 secunde pentru serverless care se trezește
- **Continuitate aplicație**: Dacă baza de date nu este disponibilă, aplicația continuă să funcționeze
- **Logging minimal de erori**: Erorile de bază de date sunt loggate o dată la 5 minute pentru a evita spam-ul

### Instalare dependințe

Pentru a instala dependința necesară pentru Azure SQL:

```bash
# În directorul app/backend
pip install pyodbc
```

Sau recompilează requirements:

```bash
# În directorul app/backend
uv pip compile requirements.in -o requirements.txt --python-version 3.9
pip install -r requirements.txt
```

### Testing

Pentru a testa sistemul fără baza de date:
1. Nu seta variabilele `AZURE_SQL_USERNAME` și `AZURE_SQL_PASSWORD`
2. Aplicația va rula normal și va loga doar în terminal
3. În log-uri vei vedea mesajul: "Database logging dezactivat"

Pentru a testa cu baza de date:
1. Seteaza toate variabilele de mediu
2. Aplicația va încerca să se conecteze și să creeze tabela
3. Toate conversațiile vor fi salvate în baza de date
4. În cazul problemelor de conectivitate, aplicația va continua să funcționeze
