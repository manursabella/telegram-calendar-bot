# Telegram Calendar Bot

Bot de Telegram que recibe texto o imágenes y crea eventos en Google Calendar automáticamente.

## Características

- ✉️ Recibe texto en lenguaje natural y crea eventos
- 🖼️ Procesa imágenes (OCR) para extraer texto
- 📅 Crea eventos en Google Calendar
- 🔔 Soporta fechas y horas en español

## Requisitos Previos

1. **Python 3.10+** instalado
2. **Cuenta de Google** con Google Calendar
3. **Bot de Telegram** (creado con @BotFather)

## Instalación

1. Clona el repositorio:
```bash
cd telegram-calendar-bot
pip install -r requirements.txt
```

## Configuración de Google Calendar API

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto
3. Habilita la API de Google Calendar
4. Ve a "Credenciales" > "Crear credenciales" > "OAuth 2.0"
5. Descarga el archivo `credentials.json` y ponlo en la carpeta del proyecto

## Configuración del Bot de Telegram

1. Busca @BotFather en Telegram
2. Envía `/newbot` y sigue las instrucciones
3. Copia el token del bot
4. Crea un archivo `.env` con:
```
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

## Instalar Tesseract OCR (para imágenes)

### Windows:
1. Descarga Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki
2. Instala y agrega al PATH
3. O especifica la ruta en el código si es diferente

### Linux:
```bash
sudo apt-get install tesseract-ocr
```

### macOS:
```bash
brew install tesseract
```

## Uso

1. Ejecuta el bot:
```bash
python bot.py
```

2. Busca tu bot en Telegram y envíale `/start`

## Ejemplos de Uso

Envía mensajes como:
- "Tengo clase de matemáticas mañana a las 10"
- "Cita con el dentista el 15 de marzo a las 14:30"
- "Reunión de trabajo el viernes a las 9am por 2 horas"
- "Examen final el 20 de diciembre"

O envía una imagen con texto y el bot la procesará.

## Comandos

- `/start` - Iniciar el bot
- `/help` - Ver ayuda
- `/events` - Ver próximos eventos

## Solución de Problemas

**Error de OCR**: Asegúrate de tener Tesseract instalado correctamente.

**Error de Google Auth**: Verifica que `credentials.json` esté en la carpeta correcta.

**Token expirado**: Elimina `token.pickle` y ejecuta el bot de nuevo para re-autenticar.

## Estructura del Proyecto

```
telegram-calendar-bot/
├── bot.py                 # Lógica principal del bot
├── config.py              # Configuración
├── google_calendar.py      # Funciones de Google Calendar
├── requirements.txt       # Dependencias
├── credentials.json      # Credenciales de Google (descargar)
├── token.pickle         # Token de acceso (se crea automáticamente)
└── .env                # Variables de entorno
```
