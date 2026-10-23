# Chat básico

Este ejemplo muestra:

- invocación de un LLM de OpenRouter mediante LangChain;
- uso de un `SystemMessage`;
- conservación del historial para conversaciones por turnos;
- incorporación de Langfuse mediante callbacks.

## Ejecutar sin observabilidad

Desde la raíz del proyecto:

```bash
uv run python 01-basic-chat/chat.py
```

## Ejecutar con Langfuse

Primero levanta Langfuse y configura sus credenciales siguiendo
[`docs/01-agregar-langfuse-al-chat.md`](../docs/01-agregar-langfuse-al-chat.md).
Después ejecuta:

```bash
uv run python 01-basic-chat/chat_with_langfuse.py
```

Para comprobar que el historial funciona, prueba esta conversación:

```text
Tú: Mi nombre es Ada y estoy preparando una charla.
Tú: ¿Cómo me llamo y qué estoy preparando?
```
