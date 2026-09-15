from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq()

modelos = client.models.list()

for modelo in modelos.data:
    print(
        f"{modelo.id} | "
        f"ativo: {modelo.active} | "
        f"contexto: {modelo.context_window}"
    )