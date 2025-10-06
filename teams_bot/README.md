# Teams Bot pentru Azure Search OpenAI Demo

Bot pentru Microsoft Teams care integrează cu backend-ul existent Azure OpenAI RAG (Retrieval Augmented Generation).

## 🚀 Quick Start - Deployment în Azure

**Vrei să deploiezi rapid în Azure?** Urmează ghidul simplu:

👉 **[QUICKSTART.md](./QUICKSTART.md)** - Deploy în 3 pași (< 10 minute)

Pentru deployment complet și detaliat, vezi [DEPLOYMENT.md](./DEPLOYMENT.md).

---

## Descriere

Acest bot permite utilizatorilor să interacționeze cu sistemul de chat AI direct din Microsoft Teams, păstrând același backend puternic bazat pe Azure OpenAI și Azure AI Search.

### Caracteristici

- ✅ Integrare completă cu backend-ul existent
- ✅ Suport pentru conversații multi-turn
- ✅ Afișare citări și surse (cu link mapping pentru optimizare tokeni)
- ✅ Mesaje de bun venit personalizate
- ✅ Formatare HTML pentru Teams (superscript, bold, etc.)
- ✅ Menținere istoric conversație per utilizator
- ✅ Typing indicators pentru feedback vizual
- ✅ Economie de tokeni prin link mapping (vezi [LINK_MAPPING.md](./LINK_MAPPING.md))

## Structură Proiect

```
teams_bot/
├── app.py                  # Aplicația principală (endpoint-uri)
├── bot.py                  # Logica botului Teams
├── backend_client.py       # Client pentru comunicare cu backend-ul
├── requirements.txt        # Dependențe Python
├── Dockerfile             # Container pentru deployment
├── .env.example           # Template variabile de mediu
├── DEPLOYMENT.md          # Ghid complet de deployment
├── manifest/              # Teams App Manifest
│   ├── manifest.json      # Configurare aplicație Teams
│   ├── color.png          # Iconița color (192x192)
│   ├── outline.png        # Iconița outline (32x32)
│   └── README.md          # Instrucțiuni manifest
└── README.md             # Acest fișier
```

## Quick Start - Dezvoltare Locală

### Prerequisite

- Python 3.11+
- Backend-ul rulează local sau în Azure
- Microsoft App ID și Password (vezi [DEPLOYMENT.md](DEPLOYMENT.md))

### Instalare

```powershell
# Navighează în directorul teams_bot
cd teams_bot

# Creează virtual environment
python -m venv venv

# Activează virtual environment
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate     # Linux/Mac

# Instalează dependențele
pip install -r requirements.txt
```

### Configurare

```powershell
# Copiază .env.example la .env
cp .env.example .env

# Editează .env cu valorile tale
# Minim necesar pentru testare locală:
# BACKEND_URL=http://localhost:50505
```

### Rulare Locală

```powershell
# Asigură-te că backend-ul rulează (din root)
cd ../app
.\start.ps1

# În alt terminal, pornește bot-ul
cd ../teams_bot
python app.py
```

Bot-ul va fi disponibil la `http://localhost:3978`

### Testare cu Bot Framework Emulator

1. Descarcă [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)
2. Deschide Emulator-ul
3. Click **Open Bot**
4. Introdu URL: `http://localhost:3978/api/messages`
5. Lasă App ID și Password goale pentru testare locală
6. Începe conversația!

## Deployment în Azure

Pentru deployment complet în Azure, urmează ghidul detaliat din [DEPLOYMENT.md](DEPLOYMENT.md).

### Pași Rapidi

```powershell
# 1. Creează App Registration în Azure AD
az ad app create --display-name "TeamsBot-RAG"

# 2. Configurează variabilele
azd env set MICROSOFT_APP_ID "<your-app-id>"
azd env set MICROSOFT_APP_PASSWORD "<your-password>" --secret
azd env set BACKEND_URL "https://your-backend.azurecontainerapps.io"

# 3. Deploy
.\scripts\deploy_teams_bot.ps1

# 4. Creează pachetul Teams
cd teams_bot/manifest
# Actualizează manifest.json cu valorile tale
Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath ../teams-app.zip

# 5. Upload în Teams
# Teams → Apps → Upload a custom app → selectează teams-app.zip
```

## Folosire

### Comenzi Disponibile

Bot-ul înțelege întrebări naturale, dar are și comenzi rapide:

- **Ajutor** - Afișează informații despre bot
- **Beneficii** - Întreabă despre beneficiile angajaților
- **Politici** - Întreabă despre politicile companiei
- **Joburi** - Informații despre posturi disponibile

### Exemple de Conversații

```
User: Care sunt beneficiile de sănătate?
Bot: [Răspuns detaliat cu citări din documentele companiei]

User: Poți să-mi spui mai multe despre asigurarea dentară?
Bot: [Continuă conversația cu context]

User: Ce posturi sunt disponibile în departamentul IT?
Bot: [Răspunde cu informații despre posturi]
```

## Arhitectură

### Flow Conversație

```
User în Teams
    ↓
Teams Bot (acest proiect)
    ↓
Backend Client (HTTP)
    ↓
Backend API (/chat endpoint)
    ↓
Azure OpenAI + Azure AI Search
    ↓
Response înapoi la User
```

### Componente

**app.py**
- Endpoint `/api/messages` pentru Teams
- Endpoint `/health` pentru health checks
- Middleware pentru error handling

**bot.py**
- `TeamsBot` class - logica principală
- Gestionare conversații
- Formatare răspunsuri pentru Teams
- Welcome messages

**backend_client.py**
- `BackendClient` class - client HTTP
- Metode `chat()` și `ask()`
- Gestionare sesiuni aiohttp
- Error handling

## Customizare

### Modificare Prompt-uri Welcome

Editează în `bot.py`:

```python
async def on_members_added_activity(self, members_added, turn_context):
    welcome_message = "Mesajul tău personalizat aici!"
    await turn_context.send_activity(MessageFactory.text(welcome_message))
```

### Modificare Comenzi

Editează în `teams_bot/manifest/manifest.json`:

```json
"commands": [
  {
    "title": "Comanda Ta",
    "description": "Descrierea comenzii"
  }
]
```

### Adăugare Funcționalități

Extinzi clasa `TeamsBot` în `bot.py`:

```python
async def on_message_activity(self, turn_context: TurnContext):
    user_message = turn_context.activity.text
    
    # Adaugă logică customizată
    if user_message.lower() == "status":
        await turn_context.send_activity("Bot functional!")
        return
    
    # Continuă cu logica existentă
    await super().on_message_activity(turn_context)
```

## Troubleshooting

### Bot nu primește mesaje

**Verifică:**
- App ID și Password sunt corecte
- Endpoint-ul botului e configurat în Azure Bot Service
- Web App-ul rulează (check `/health`)

```powershell
# Test health
curl https://your-bot.azurewebsites.net/health

# Vezi logs
az webapp log tail --name "your-bot-name" --resource-group "your-rg"
```

### Backend nu răspunde

**Verifică:**
- `BACKEND_URL` e corect în configurare
- Backend-ul e accesibil (test cu curl)
- Nu sunt erori de CORS

```powershell
# Test backend
curl https://your-backend.azurecontainerapps.io/health
```

### Erori în Teams

**Verifică:**
- Manifestul e valid (validare cu [App Studio](https://dev.teams.microsoft.com/appvalidation.html))
- Iconițele au dimensiunile corecte
- Toate UUID-urile sunt valide

## Dezvoltare și Contribuții

### Setup Environment Dezvoltare

```powershell
# Instalează dependențe de dezvoltare
pip install -r requirements.txt
pip install pytest black flake8

# Rulează tests (când sunt adăugate)
pytest

# Format code
black .

# Lint
flake8 .
```

## Resurse

- [Bot Framework SDK](https://github.com/microsoft/botbuilder-python)
- [Teams Platform Documentation](https://docs.microsoft.com/en-us/microsoftteams/platform/)
- [Azure Bot Service](https://docs.microsoft.com/en-us/azure/bot-service/)
- [Backend Documentation](../README.md)

## Licență

Acest proiect moștenește licența proiectului principal.

## Suport

Pentru probleme specifice bot-ului Teams, deschide un issue în repository.
Pentru probleme legate de backend, consultă documentația principală.
