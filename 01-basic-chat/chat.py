import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openrouter import ChatOpenRouter

SYSTEM_PROMPT = """Eres un asistente útil para una demostración técnica.
Responde siempre en español, de forma clara y concisa.
Si no conoces una respuesta, dilo abiertamente."""


def create_model() -> ChatOpenRouter:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENROUTER_API_KEY en el archivo .env")

    return ChatOpenRouter(
        model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash"),
        api_key=api_key,
        temperature=0.2,
    )


def response_text(message: AIMessage) -> str:
    if isinstance(message.content, str):
        return message.content
    return "".join(
        block.get("text", "")
        for block in message.content
        if isinstance(block, dict) and block.get("type") == "text"
    )


def main() -> None:
    load_dotenv(override=True)
    model = create_model()
    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

    print("Chat básico con LangChain")
    print("Escribe 'salir' para terminar.\n")

    while True:
        try:
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if user_input.lower() in {"salir", "exit", "quit"}:
            print("Hasta luego.")
            break
        if not user_input:
            continue

        messages.append(HumanMessage(content=user_input))
        try:
            response = model.invoke(messages)
        except Exception as error:
            messages.pop()
            print(f"Error al consultar el modelo: {error}")
            continue

        messages.append(response)
        print(f"Asistente: {response_text(response)}\n")


if __name__ == "__main__":
    main()
