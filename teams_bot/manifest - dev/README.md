# Teams App Manifest

Acest director conține manifestul aplicației Teams.

## Fișiere necesare

1. **manifest.json** - Manifestul principal al aplicației
2. **color.png** - Iconița color (192x192 px)
3. **outline.png** - Iconița outline (32x32 px)

## Configurare

Înainte de deployment, înlocuiește următoarele placeholder-uri în `manifest.json`:

- `{{TEAMS_APP_ID}}` - Un UUID unic pentru aplicația Teams (generează cu `uuidgen` sau online)
- `{{MICROSOFT_APP_ID}}` - App ID din Azure Bot Registration
- `{{BOT_DOMAIN}}` - Domeniul unde este hosted bot-ul (ex: `your-bot.azurewebsites.net`)

## Crearea pachetului Teams

Pentru a crea un pachet Teams (.zip) pe care să-l încarci:

```powershell
# Comprimă toate fișierele din acest director
Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath ../teams-app.zip -Force
```

## Upload în Teams

1. Deschide Microsoft Teams
2. Click pe "Apps" în sidebar
3. Click pe "Manage your apps" → "Upload an app"
4. Selectează "Upload a custom app"
5. Selectează fișierul `teams-app.zip`

## Note importante

- Dimensiunea fișierului color.png trebuie să fie exact 192x192 pixeli
- Dimensiunea fișierului outline.png trebuie să fie exact 32x32 pixeli
- Toate URL-urile din manifest trebuie să fie HTTPS (în producție)
- Bot-ul trebuie să fie deja înregistrat în Azure Bot Service
