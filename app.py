import discord
from discord import app_commands
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import datetime
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Escopo para acesso ao Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google():
    """Autenticando o usuário no Google API e retornando as credenciais."""
    creds = None
    token_path = os.getenv('GOOGLE_TOKEN_PATH')
    credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')

    if not token_path or not credentials_path:
        raise EnvironmentError("As variáveis 'GOOGLE_TOKEN_PATH' e 'GOOGLE_CREDENTIALS_PATH' precisam estar definidas no .env")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Arquivo de credenciais '{credentials_path}' não encontrado.")

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds

def create_event(start_datetime, end_datetime, summary, description="", location=""):
    """Cria um evento no Google Calendar."""
    try:
        service = build('calendar', 'v3', credentials=authenticate_google())

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return created_event.get('htmlLink')
    except Exception as e:
        print(f"Erro ao criar evento: {e}")
        return None

# Configuração do bot Discord
class CalendarBot(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Registra os comandos no servidor
        await self.tree.sync()

intents = discord.Intents.default()
bot = CalendarBot(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.tree.command(name="agendar", description="Agenda um evento no Google Calendar.")
@app_commands.describe(
    titulo="Título do evento",
    inicio="Início no formato AAAA-MM-DDTHH:MM",
    termino="Término no formato AAAA-MM-DDTHH:MM",
    descricao="Descrição do evento (opcional)",
    local="Localização do evento (opcional)"
)
async def agendar(interaction: discord.Interaction, titulo: str, inicio: str, termino: str, descricao: str = "", local: str = ""):
    """
    Comando para criar um evento no Google Calendar usando slash command.
    """
    try:
        # Converte os horários para datetime
        start_datetime = datetime.datetime.fromisoformat(inicio)
        end_datetime = datetime.datetime.fromisoformat(termino)

        # Cria o evento
        link = create_event(start_datetime, end_datetime, titulo, descricao, local)

        if link:
            await interaction.response.send_message(f"Evento criado com sucesso! Link: {link}")
        else:
            await interaction.response.send_message("Ocorreu um erro ao criar o evento.")
    except ValueError as ve:
        await interaction.response.send_message(f"Erro no formato da data/hora: {ve}")
    except Exception as e:
        await interaction.response.send_message(f"Ocorreu um erro inesperado: {e}")

# Inicializa o bot
bot.run(os.getenv('DISCORD_TOKEN'))
