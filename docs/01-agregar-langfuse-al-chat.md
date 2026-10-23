# Tutorial: añadir Langfuse al chat básico

Esta guía parte de [`01-basic-chat/chat.py`](../01-basic-chat/chat.py) y explica
cómo obtener [`chat_with_langfuse.py`](../01-basic-chat/chat_with_langfuse.py).

## 1. Levantar Langfuse

El `docker-compose.yml` de la raíz es la distribución oficial de Langfuse v4.
Incluye la aplicación web, el worker, PostgreSQL, ClickHouse, Redis y MinIO.

```bash
docker compose up -d
```

La primera descarga puede tardar varios minutos. Comprueba el estado con:

```bash
docker compose ps
```

Abre <http://localhost:3000>, crea una cuenta local y después crea un proyecto.

> Este Compose usa credenciales predeterminadas pensadas exclusivamente para
> una demo local. No debe exponerse en una red ni emplearse en producción.

## 2. Crear las claves del proyecto

En Langfuse:

1. Abre el proyecto.
2. Entra en **Settings > API Keys**.
3. Crea un nuevo par de claves.
4. Copia la clave pública y la secreta.

Completa estas variables en `.env`:

```dotenv
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=http://localhost:3000
```

`python-dotenv` carga estas variables antes de inicializar Langfuse. No añadas
el archivo `.env` al control de versiones.

## 3. Añadir el SDK

El proyecto ya incluye la dependencia. En un proyecto nuevo se añadiría así:

```bash
uv add langfuse
```

## 4. Importar Langfuse

Añade estos imports al chat original:

```python
from uuid import uuid4

from langfuse import get_client
from langfuse.langchain import CallbackHandler
```

`get_client()` devuelve el cliente configurado mediante el entorno.
`CallbackHandler` escucha los eventos que LangChain emite durante la invocación.

## 5. Inicializar la instrumentación

Después de cargar `.env`, crea el cliente, el callback y un identificador para
la conversación:

```python
load_dotenv(override=True)
model = create_model()
langfuse = get_client()
langfuse_handler = CallbackHandler()
session_id = str(uuid4())
```

El `session_id` permite localizar juntos en Langfuse todos los turnos de una
misma ejecución del chat.

## 6. Instrumentar cada llamada al modelo

El chat original invoca el modelo así:

```python
response = model.invoke(messages)
```

Sustituye esa línea por:

```python
response = model.invoke(
    messages,
    config={
        "callbacks": [langfuse_handler],
        "run_name": "basic-chat-turn",
        "metadata": {
            "langfuse_session_id": session_id,
            "langfuse_tags": ["demo", "basic-chat"],
        },
    },
)
```

Con esto, cada turno produce una traza con la entrada, la respuesta, el modelo,
la latencia y el uso de tokens disponible. Los turnos son trazas separadas,
pero comparten una sesión.

## 7. Cerrar el cliente

Langfuse envía los eventos en segundo plano. Como este programa es una CLI,
hay que cerrar el cliente al finalizar para no perder los últimos eventos:

```python
try:
    # Bucle del chat
    ...
finally:
    langfuse.shutdown()
```

## 8. Ejecutar y observar

```bash
uv run python 01-basic-chat/chat_with_langfuse.py
```

Realiza varios turnos, escribe `salir` y abre **Tracing > Traces** en Langfuse.
Comprueba:

- el nombre `basic-chat-turn`;
- el modelo utilizado;
- los mensajes enviados y recibidos;
- latencia y consumo de tokens;
- las etiquetas `demo` y `basic-chat`;
- que los turnos aparecen agrupados bajo la misma sesión.

## Detener la infraestructura

Conservando los datos:

```bash
docker compose down
```

Para borrar también los datos persistidos de esta demo:

```bash
docker compose down --volumes
```

Este último comando elimina cuentas, proyectos, claves y trazas locales.
