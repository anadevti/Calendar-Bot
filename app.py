from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import datetime
import os

# Escopo para acesso ao Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']


def authenticate_google():
    """Autentica o usuário no Google API e retorna as credenciais."""
    creds = None
    token_path = 'token.json'
    credentials_path = 'credentials.json'

    # Verifica se já existe um token salvo
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # Se não houver token ou ele for inválido, solicita autenticação
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Arquivo de credenciais '{credentials_path}' não encontrado.")

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva o token para reutilização
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
        print(f"Evento criado com sucesso: {created_event.get('htmlLink')}\n")
    except Exception as e:
        print(f"Erro ao criar evento: {e}")


def get_event_details():
    """Solicita ao usuário os detalhes do evento."""
    summary = input("Título do evento: ")
    description = input("Descrição do evento (opcional): ")
    location = input("Localização do evento (opcional): ")

    start_date = input("Data de início (AAAA-MM-DD): ")
    start_time = input("Horário de início (HH:MM): ")
    end_date = input("Data de término (AAAA-MM-DD): ")
    end_time = input("Horário de término (HH:MM): ")

    try:
        start_datetime = datetime.datetime.fromisoformat(f"{start_date}T{start_time}")
        end_datetime = datetime.datetime.fromisoformat(f"{end_date}T{end_time}")
        return start_datetime, end_datetime, summary, description, location
    except ValueError as ve:
        print(f"Erro no formato da data ou hora: {ve}")
        return None, None, None, None, None


if __name__ == "__main__":
    print("\nBem-vindo Calendar-Bot, o criador de eventos automatizados do Google Calendar!\n")
    event_details = get_event_details()

    if all(event_details):
        start_datetime, end_datetime, summary, description, location = event_details
        create_event(start_datetime, end_datetime, summary, description, location)
    else:
        print("Detalhes do evento inválidos. Por favor, tente novamente.")