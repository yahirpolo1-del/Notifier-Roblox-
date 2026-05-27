"""
Roblox Limited Notifier → Telegram
Corre en Railway 24/7 y te avisa cuando un limited baja de precio.
TÚ compras manualmente tocando el botón del mensaje.
"""

import requests
import time
import os
from datetime import datetime

# ══════════════════════════════════════════════════
#   CONFIGURACIÓN
# ══════════════════════════════════════════════════

# El token se lee desde variable de entorno en Railway (más seguro)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
print(f"Token cargado: {TELEGRAM_TOKEN[:10]}...")
TELEGRAM_CHAT_ID = "8907365234"

CHECK_INTERVAL = 20  # segundos entre revisiones

ITEMS = [
    # Añade o cambia los ítems que quieres vigilar:
    # El asset_id está en la URL de Roblox:
    # roblox.com/catalog/XXXXXXX/nombre → ese número es el asset_id
    #
    # {"asset_id": 1365767,  "name": "Dominus Empyreus",  "target_price": 5000000},
    # {"asset_id": 48545806, "name": "Darkheart",         "target_price": 80000},
    #
    # EJEMPLO (cámbialo por tus ítems reales):
    {"asset_id": 1365767,  "name": "Dominus Empyreus",  "target_price": 9999999999},
    {"asset_id": 48545806, "name": "Darkheart",         "target_price": 9999999999},
]

# ══════════════════════════════════════════════════

ROBLOX_ITEM_URL  = "https://www.roblox.com/catalog/{asset_id}/"
ROBLOX_RESELLERS = "https://economy.roblox.com/v1/assets/{asset_id}/resellers?limit=1&sortOrder=Asc"
ROBLOX_RESALE    = "https://economy.roblox.com/v1/assets/{asset_id}/resale-data"
HEADERS          = {"User-Agent": "Mozilla/5.0"}
last_alert       = {}


# ─────────────────────────────────────────
#  Telegram
# ─────────────────────────────────────────

def tg(method, **kwargs):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    try:
        r = requests.post(url, json=kwargs, timeout=10)
        return r.json()
    except Exception as e:
        print(f"[Telegram error] {e}")
        return {}


def send_alert(item, current_price, rap):
    name     = item["name"]
    target   = item["target_price"]
    asset_id = item["asset_id"]
    url      = ROBLOX_ITEM_URL.format(asset_id=asset_id)
    now      = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    saving   = target - current_price
    rap_line = f"{rap:,} R$" if rap else "N/A"

    text = (
        f"🚨 <b>¡ALERTA DE LIMITED!</b>\n\n"
        f"🎮 <b>{name}</b>\n\n"
        f"💰 Precio actual:  <code>{current_price:,} R$</code>\n"
        f"🎯 Tu objetivo:    <code>{target:,} R$</code>\n"
        f"💸 Diferencia:     <code>-{saving:,} R$</code>\n"
        f"📊 RAP:            <code>{rap_line}</code>\n\n"
        f"⏰ {now}\n\n"
        f"👇 <b>Toca el botón para comprar:</b>"
    )

    keyboard = {
        "inline_keyboard": [[
            {"text": "🛒  Comprar en Roblox", "url": url}
        ]]
    }

    result = tg(
        "sendMessage",
        chat_id=TELEGRAM_CHAT_ID,
        text=text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    if result.get("ok"):
        print(f"  ✅ Alerta enviada: {name} a {current_price:,} R$")
    else:
        print(f"  ⚠ Error Telegram: {result}")


def send_startup():
    items_lines = "\n".join(
        f"  • <b>{i['name']}</b> → objetivo <code>{i['target_price']:,} R$</code>"
        for i in ITEMS
    )
    text = (
        f"✅ <b>Notificador iniciado en Railway</b>\n\n"
        f"Monitoreando <b>{len(ITEMS)}</b> ítem(s) cada <b>{CHECK_INTERVAL}s</b>:\n\n"
        + items_lines +
        f"\n\n⚡ Te avisaré cuando alguno baje del precio objetivo."
    )
    tg("sendMessage", chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode="HTML")


# ─────────────────────────────────────────
#  Roblox API
# ─────────────────────────────────────────

def get_price_info(asset_id):
    try:
        lowest = None
        r = requests.get(
            ROBLOX_RESELLERS.format(asset_id=asset_id),
            headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                lowest = data[0].get("price")

        rap = None
        r2 = requests.get(
            ROBLOX_RESALE.format(asset_id=asset_id),
            headers=HEADERS, timeout=10
        )
        if r2.status_code == 200:
            rap = r2.json().get("recentAveragePrice")

        return {"lowest": lowest, "rap": rap}
    except Exception as e:
        print(f"[ERROR] {asset_id}: {e}")
        return None


# ─────────────────────────────────────────
#  Loop principal
# ─────────────────────────────────────────

def main():
    print("=" * 50)
    print("  Roblox Limited Notifier → Telegram")
    print("  Corriendo en Railway")
    print("=" * 50)
    print(f"  Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"  Ítems: {len(ITEMS)}")
    print(f"  Intervalo: {CHECK_INTERVAL}s\n")

    send_startup()
    print("  ¡Listo! Revisando precios...\n")

    cycle = 0
    while True:
        cycle += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] Ciclo #{cycle}")

        for item in ITEMS:
            asset_id = item["asset_id"]
            target   = item["target_price"]
            name     = item["name"]

            info = get_price_info(asset_id)
            if info is None:
                print(f"  ⚠  {name}: error")
                time.sleep(1.5)
                continue

            lp  = info.get("lowest")
            rap = info.get("rap")

            if lp is None:
                print(f"  💤  {name}: sin revendedores")
            else:
                print(f"  💎  {name}: {lp:,} R$ (objetivo: {target:,})")
                if lp <= target:
                    prev = last_alert.get(asset_id)
                    if prev is None or lp < prev:
                        print(f"  🚨  ¡BAJO OBJETIVO! Enviando alerta...")
                        send_alert(item, lp, rap)
                        last_alert[asset_id] = lp

            time.sleep(1.5)

        print(f"  → Próxima revisión en {CHECK_INTERVAL}s\n")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
