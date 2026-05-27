# Roblox Limited Notifier → Telegram

Monitorea precios de ítems Limited en Roblox y te manda una alerta a Telegram.
Tú compras manualmente tocando el botón del mensaje.

## Cómo subir a Railway

1. Crea cuenta en https://railway.app (gratis)
2. New Project → Deploy from GitHub repo
   (sube esta carpeta a un repo de GitHub primero)
3. En Railway → tu proyecto → Variables → añade:
   - TELEGRAM_TOKEN = tu token de @BotFather

## Editar ítems

Abre main.py y modifica la lista ITEMS:

```python
ITEMS = [
    {"asset_id": 48545806, "name": "Darkheart", "target_price": 80000},
]
```

El asset_id está en la URL de Roblox:
roblox.com/catalog/XXXXXXX/nombre → ese número es el asset_id
