# Avisador de señales GRATIS (sin servidor, sin pagar)

Cada 15 minutos GitHub revisa el mercado con tu estrategia y te manda un mensaje a Telegram cuando hay una señal nueva. Tú abres la operación a mano en la app de MT5 del iPhone. No ejecuta órdenes solo.

## Qué necesitas (todo gratis, solo con el iPhone)
Cuenta de GitHub y Telegram. No pide tarjeta.

## Paso 1 – Telegram
1. Abre @BotFather, escribe `/newbot`, ponle nombre y copia el **token**.
2. Escríbele "hola" a tu bot nuevo.
3. Abre @userinfobot y copia tu número de **ID**.

## Paso 2 – GitHub
1. En Safari entra a github.com y crea tu cuenta gratis.
2. Toca **+ > New repository**. Ponle un nombre. Elígelo **Public** (gratis e ilimitado) y créalo.
   - Es público, así que el código se puede ver, pero tus claves NO (van en Secrets).
   - Si lo quieres privado, GitHub da 2,000 minutos al mes: con 15 minutos se acaban; pon `timeframe: 1h` en `config.yaml` y `cron: "5 * * * 1-5"` en `signals.yml`.
3. En la app Archivos descomprime el zip. En el repositorio toca **Add file > Upload files** y sube TODO el contenido, incluida la carpeta `.github`.
   - Si el iPhone no te deja subir la carpeta oculta `.github`: toca **Add file > Create new file**, escribe el nombre `.github/workflows/signals.yml` y pega el contenido del archivo.

## Paso 3 – Tus claves (Secrets)
En el repositorio: **Settings > Secrets and variables > Actions > New repository secret**. Crea dos:
- `TELEGRAM_TOKEN` = el token de BotFather
- `TELEGRAM_CHAT_ID` = tu ID

## Paso 4 – Probar
Pestaña **Actions** > **signals** > **Run workflow**. Si sale verde, está funcionando. Solo te escribirá cuando haya una señal nueva, así que puede pasar rato sin mensajes.
Si no llegan señales en días, revisa la pestaña Actions: GitHub puede pausar tareas programadas si el repositorio lleva mucho sin actividad (el bot guarda `state.json` solo cuando avisa).

## Cómo usar una señal
Llega algo como: COMPRA Oro, Stop Loss 5.1 debajo de tu precio de entrada, Take Profit 10.2 arriba.
1. Abre MT5 en el iPhone y entra a la operación a mercado.
2. Pon el SL y el TP usando esas distancias sobre TU precio de entrada.
3. Calcula el lote para arriesgar máximo 0.5 % de tu cuenta.
4. Primero hazlo en una cuenta demo.

## Límites
- Datos de Yahoo ≠ precios de tu broker: por eso se dan distancias, no precios exactos.
- Yahoo a veces bloquea servidores en la nube. Si pasa, el bot te avisa por Telegram (máximo una vez cada 6 h).
- GitHub no garantiza la hora exacta de las tareas programadas: pueden retrasarse o saltarse alguna.
- Ninguna señal garantiza ganancias.
