# Link Mapping în Teams Bot

## Descriere

Link mapping este o tehnică de optimizare care reduce dimensiunea răspunsurilor prin înlocuirea linkurilor lungi cu ID-uri scurte (`link1`, `link2`, etc.) în timpul comunicării cu LLM-ul, urmată de înlocuirea acestora cu linkurile reale înainte de afișare.

## Beneficii

### 1. **Economisire de tokeni AI**
Linkurile Azure Blob Storage sunt foarte lungi (200-300 caractere):
```
https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28406.pdf?se=2025-08-28T12%3A57%3A58Z&sp=r&sv=2024-08-04&sr=b&sig=ABC123def%2Bghi456jkl%3D#page=5
```

Cu link mapping, acestea devin:
```
link1
```

**Economie**: ~250 tokeni per link × numărul de documente = economii substanțiale

### 2. **Performanță îmbunătățită**
- Mai puțini tokeni = răspunsuri mai rapide de la LLM
- Mai puțini tokeni = cost redus per query
- Răspunsuri mai concise și focusate

### 3. **Consistență cu Frontend-ul**
Implementarea este identică cu cea din browser (`AnswerParser.tsx`), asigurând experiență uniformă.

## Cum funcționează

### 1. **Backend (approach.py)**

Backend-ul creează un mapping între ID-uri scurte și linkuri lungi:

```python
def create_link_mapping(self, results: list[Document]) -> dict[str, str]:
    link_mapping = {}
    link_counter = 1
    
    for doc in results:
        if doc.sourcepage:
            link_id = f"link{link_counter}"
            link_mapping[link_id] = doc.sourcepage
            link_counter += 1
    
    return link_mapping
```

În sources content, folosește ID-uri scurte:
```python
return f"[{titlu_pagina}](link1)"  # În loc de link lung
```

### 2. **Response Structure**

Backend-ul trimite:
```json
{
  "message": {
    "content": "Vezi [document.pdf](link1) pentru detalii..."
  },
  "context": {
    "link_mapping": {
      "link1": "https://mihairagstorageaccount.blob.core.windows.net/...",
      "link2": "https://mihairagstorageaccount.blob.core.windows.net/...",
      "link3": "https://mihairagstorageaccount.blob.core.windows.net/..."
    }
  }
}
```

### 3. **Teams Bot (bot.py)**

Bot-ul înlocuiește ID-urile cu linkurile reale înainte de afișare:

```python
def _format_response(self, response: dict) -> str:
    answer = response.get("message", {}).get("content", "")
    context_data = response.get("context", {})
    link_mapping = context_data.get("link_mapping", {})
    
    # Replace link IDs with actual URLs
    if link_mapping:
        import re
        answer = re.sub(
            r'\[([^\]]+)\]\((link\d+)\)',
            lambda match: f"[{match.group(1)}]({link_mapping.get(match.group(2), match.group(2))})",
            answer
        )
    
    return answer
```

### 4. **Frontend Browser (AnswerParser.tsx)**

Aceeași logică pentru consistență:

```typescript
if (linkMapping) {
    parsedAnswer = parsedAnswer.replace(/\[([^\]]+)\]\((link\d+)\)/g, (match, text, linkId) => {
        if (linkMapping[linkId]) {
            return `[${text}](${linkMapping[linkId]})`;
        }
        return match;
    });
}
```

## Flow complet

```
1. User trimite întrebare
   ↓
2. Backend caută documente relevante
   ↓
3. Backend creează link_mapping: {"link1": "long_url_1", "link2": "long_url_2"}
   ↓
4. Backend trimite documente cu [title](link1) către LLM
   ↓
5. LLM generează răspuns cu "Vezi [doc.pdf](link1) pentru..."
   ↓
6. Backend returnează:
   - message.content: "Vezi [doc.pdf](link1) pentru..."
   - context.link_mapping: {"link1": "long_url"}
   ↓
7. Teams Bot/Frontend înlocuiește link1 cu long_url
   ↓
8. User vede: "Vezi [doc.pdf](https://mihairagstorageaccount...) pentru..."
```

## Testing

### Test Unitar
```bash
cd teams_bot
python test_link_mapping.py
```

Verifică:
- ✅ Regex replacement funcționează corect
- ✅ Toate linkurile sunt înlocuite
- ✅ Formatul markdown este păstrat

### Test Integrare
```bash
# Pornește backend-ul
cd app
pwsh start.ps1

# În alt terminal
cd teams_bot
python test_link_mapping_integration.py
```

Verifică:
- ✅ Backend trimite link_mapping în context
- ✅ Răspunsul conține link IDs (link1, link2, etc.)
- ✅ Bot-ul înlocuiește corect ID-urile cu linkuri reale

## Exemplu concret

### ÎNAINTE de link mapping:
```
Token count: ~1500 tokeni
Content trimis la LLM:

Source 1: [document1.pdf](https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28406.pdf?se=2025-08-28T12%3A57%3A58Z&sp=r&sv=2024-08-04&sr=b&sig=ABC123def%2Bghi456jkl%3D#page=5): Informații despre beneficii...

Source 2: [document2.pdf](https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28407.pdf?se=2025-08-28T12%3A57%3A58Z&sp=r&sv=2024-08-04&sr=b&sig=XyZ123abc%2Bdef456ghi%3D#page=1): Informații despre salarizare...
```

### DUPĂ link mapping:
```
Token count: ~800 tokeni (economie 47%!)
Content trimis la LLM:

Source 1: [document1.pdf](link1): Informații despre beneficii...
Source 2: [document2.pdf](link2): Informații despre salarizare...

Link mapping (trimis separat în context):
{
  "link1": "https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28406.pdf?...",
  "link2": "https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28407.pdf?..."
}
```

### Răspuns final pentru utilizator (după înlocuire):
```
Pentru detalii despre beneficii, consultă [document1.pdf](https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28406.pdf?se=2025-08-28T12%3A57%3A58Z&sp=r&sv=2024-08-04&sr=b&sig=ABC123def%2Bghi456jkl%3D#page=5).
```

## Rezultate test real

Din `test_link_mapping.py`:
```
✅ Succes! Înlocuite 4 din 4 linkuri.

Caractere în răspuns original (cu link IDs): 254
Caractere în răspuns final (cu linkuri reale): 918
Diferență: 664 caractere (+261.4%)

Economie în prompt pentru LLM: 664 caractere × număr surse
```

## Configurare

Funcția este **activată automat** în bot, fără configurare necesară.

Backend-ul detectează automat când să folosească link mapping bazat pe:
- Prezența documentelor cu `sourcepage` în rezultate
- Lungimea linkurilor (optimizează doar pentru linkuri lungi)

## Debugging

Verifică logs pentru:
```
[DEBUG] Created link mapping: {'link1': 'https://...', 'link2': 'https://...'}
[DEBUG] get_sources_content: Replacing https://...#page=1 with link1
```

În frontend/Teams, verifică console:
```
AnswerParser: linkMapping = {link1: "https://...", link2: "https://..."}
AnswerParser: found markdown link: [doc.pdf](link1)
AnswerParser: replacing link1 with https://...
```

## Referințe

- **Frontend**: `app/frontend/src/components/Answer/AnswerParser.tsx` (liniile 41-54)
- **Backend**: `app/backend/approaches/approach.py` (`create_link_mapping`, `get_sources_content`)
- **Teams Bot**: `teams_bot/bot.py` (`_format_response`)
- **Test**: `test_link_mapping.py`, `test_link_mapping_integration.py`
