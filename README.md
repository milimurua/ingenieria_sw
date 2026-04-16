# SAMUR Telegram Bot

Bot de prueba en Python para gestionar ausencias, alertas operativas y reorganización de equipos SAMUR desde Telegram.

## Qué hace

- registra ausencias
- sugiere reemplazos de la misma categoría
- reorganiza bases por prioridad mínima
- asigna vehículo según la dotación resultante
- registra alertas rápidas estilo “Ojo en Alerta”
- usa SQLite para que puedas probarlo sin instalar nada extra

## Estructura

```text
samur_telegram/
├── .env.example
├── README.md
├── requirements.txt
├── run.py
├── data/
└── app/
    ├── __init__.py
    ├── bot.py
    ├── config.py
    ├── db.py
    ├── handlers/
    │   └── commands.py
    └── services/
        ├── allocation.py
        └── seed.py
```

## Requisitos

- Python 3.10 o superior
- un bot token de Telegram creado con BotFather

La librería `python-telegram-bot` ofrece una interfaz asíncrona y es compatible con Python 3.10+; además puede instalarse con `pip install python-telegram-bot --upgrade`. citeturn898644search0turn898644search1

## Puesta en marcha

### 1. Crear el bot en Telegram

1. Abrí Telegram.
2. Buscá `@BotFather`.
3. Ejecutá `/newbot`.
4. Elegí nombre y username.
5. Copiá el token que te devuelve.

### 2. Preparar variables

```bash
cp .env.example .env
```

Editá `.env` y completá:

```env
TELEGRAM_BOT_TOKEN=tu_token_real
SAMUR_DB_PATH=data/samur_telegram.db
TIMEZONE=Europe/Madrid
```

### 3. Instalar dependencias

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

Instalación:

```bash
pip install -r requirements.txt
```

### 4. Ejecutar

```bash
python run.py
```


## Ejecutarlo con Docker

### 1. Preparar variables

```bash
cp .env.example .env
```

Completá tu token en `.env`:

```env
TELEGRAM_BOT_TOKEN=tu_token_real
SAMUR_DB_PATH=data/samur_telegram.db
TIMEZONE=Europe/Madrid
```

### 2. Levantar el bot

```bash
docker compose up --build
```

### 3. Ejecutarlo en segundo plano

```bash
docker compose up -d --build
```

### 4. Ver logs

```bash
docker compose logs -f
```

### 5. Pararlo

```bash
docker compose down
```

### 6. Borrar también la base de datos del volumen

```bash
docker compose down -v
```

Con esto todos usan la misma versión de Python, las mismas dependencias y el mismo comando de arranque.

## Comandos del bot

- `/start` iniciar menú
- `/estado` ver cobertura actual
- `/ausencia` cargar una baja
- `/alerta` registrar una incidencia
- `/reorganizar` recalcular asignaciones
- `/personas` ver personal de prueba cargado
- `/reset_demo` restaurar los datos demo
- `/cancel` cancelar una conversación

## Cómo probar rápido

1. Iniciá el bot.
2. Abrí el chat con tu bot.
3. Mandá `/start`.
4. Mandá `/estado`.
5. Mandá `/ausencia` y probá con `Ana Pérez`.
6. Revisá `/estado` otra vez.
7. Mandá `/reorganizar`.

## Ideas para ampliarlo

- autenticación por roles
- varias guardias por turno
- restricciones laborales reales
- mapa y geolocalización
- panel web para supervisión
- conexión con WhatsApp, formularios o central telefónica
- motor de optimización más avanzado

## Nota

Este proyecto es un prototipo funcional para pruebas. La lógica de asignación es heurística y está pensada para demo.
