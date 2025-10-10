# Teams App Manifest

Acest folder conține manifestul și resursele necesare pentru aplicația Microsoft Teams.

## Fișiere Necesare

### 1. manifest.json ✅
Fișierul de configurare principal pentru aplicația Teams.

**Câmpuri importante de actualizat:**
- `id`: UUID unic pentru aplicația Teams (se generează automat de `deploy.ps1`)
- `bots[0].botId`: Microsoft App ID (din Azure AD App Registration)
- `validDomains`: Domeniul web app-ului Azure (ex: `teamsbot-mihai.azurewebsites.net`)
- `webApplicationInfo.id`: Același ca Microsoft App ID
- `webApplicationInfo.resource`: `api://<domain>/<app-id>`

### 2. color.png ⚠️ NECESARĂ
Iconița color pentru aplicația Teams.

**Cerințe:**
- Dimensiune: **192x192 pixeli**
- Format: PNG
- Fundal: Opțional (poate fi transparent)
- Recomandat: Culori vibrante pentru vizibilitate în Teams

### 3. outline.png ⚠️ NECESARĂ  
Iconița outline pentru aplicația Teams.

**Cerințe:**
- Dimensiune: **32x32 pixeli**
- Format: PNG
- Fundal: **TRANSPARENT**
- Stil: Simplu, monocrom (alb pentru fundal închis Teams)

## Cum să creezi iconițele

### Opțiunea 1: Online Icon Makers (Recomandat)

**Canva (Gratis):**
1. Mergi la [canva.com](https://www.canva.com)
2. Creează design 192x192 px (color.png)
3. Creează design 32x32 px (outline.png)
4. Descarcă ca PNG

**Figma (Gratis):**
1. Mergi la [figma.com](https://www.figma.com)
2. Creează frame 192x192
3. Desenează iconița
4. Export ca PNG

### Opțiunea 2: Folosește emoji/text (Rapid)

**PowerPoint/Paint:**
1. Deschide PowerPoint/Paint
2. Setează canvas 192x192 px
3. Adaugă emoji/text mare (🤖, 💬, 📚, etc.)
4. Salvează ca PNG
5. Repetă pentru 32x32 px

### Opțiunea 3: Generator automat Python

```python
# install: pip install pillow
from PIL import Image, ImageDraw, ImageFont

# Color icon (192x192)
img = Image.new('RGB', (192, 192), color='#0078D4')  # Microsoft Blue
draw = ImageDraw.Draw(img)

# Desenează un cerc
draw.ellipse([46, 46, 146, 146], fill='white')

# Adaugă text (necesită font)
font = ImageFont.truetype("arial.ttf", 60)
draw.text((96, 96), "AI", fill='#0078D4', anchor="mm", font=font)

img.save('color.png')

# Outline icon (32x32)
img_outline = Image.new('RGBA', (32, 32), color=(0, 0, 0, 0))  # Transparent
draw = ImageDraw.Draw(img_outline)
draw.ellipse([4, 4, 28, 28], outline='white', width=2)
img_outline.save('outline.png')
```

### Opțiunea 4: Downloadează template-uri

**Free Icon Resources:**
- [Flaticon](https://www.flaticon.com) - Caută "bot", "ai", "chat"
- [Icons8](https://icons8.com) - Download în dimensiunile necesare
- [Heroicons](https://heroicons.com) - SVG icons (convertești la PNG)

## Creare Package Teams

După ce ai toate cele 3 fișiere:

```powershell
# Din directorul manifest/
Compress-Archive -Path manifest.json,color.png,outline.png -DestinationPath ../teams-app.zip -Force
```

Sau folosește scriptul de deployment:
```powershell
cd ..
.\deploy.ps1 -ResourceGroupName "rg-teams-bot" -AppName "teamsbot-mihai" -BackendUrl "https://backend.azurecontainerapps.io"
```

## Troubleshooting

### "Invalid icon size"
Verifică dimensiunile EXACT: 192x192 și 32x32

```powershell
# PowerShell - verifică dimensiuni
Add-Type -AssemblyName System.Drawing
[System.Drawing.Image]::FromFile("$PWD/color.png").Size
[System.Drawing.Image]::FromFile("$PWD/outline.png").Size
```

### "Transparent background required"
outline.png TREBUIE să aibă fundal transparent

### "App package is invalid"
- Verifică că toate câmpurile din manifest sunt completate
- UUID-urile trebuie să fie valide
- Domeniul din validDomains fără `https://`

## Quick Setup (Pentru testare)

**Generator rapid iconițe:**

```powershell
# Creează iconițe simple pentru testare
python -c @"
from PIL import Image, ImageDraw
img = Image.new('RGB', (192, 192), '#0078D4')
d = ImageDraw.Draw(img)
d.ellipse([46, 46, 146, 146], fill='white')
img.save('color.png')
img2 = Image.new('RGBA', (32, 32), (0,0,0,0))
d2 = ImageDraw.Draw(img2)
d2.ellipse([4, 4, 28, 28], outline='white', width=2)
img2.save('outline.png')
"@
```

## Resurse

- [Teams App Manifest Schema](https://docs.microsoft.com/en-us/microsoftteams/platform/resources/schema/manifest-schema)
- [Design Guidelines](https://docs.microsoft.com/en-us/microsoftteams/platform/concepts/design/design-teams-app-overview)

---

**Gata?** Rulează `.\deploy.ps1` din folderul `teams_bot/` pentru deployment complet!
