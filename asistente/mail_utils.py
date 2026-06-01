"""
Utilidades para envío de correos mediante Gmail API.
Factoriza la lógica MIME y autenticación para reutilizar en cualquier contexto.
"""

from pathlib import Path
import sys
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate

# Asegurar importación de módulos del proyecto
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crm.connectors import GmailConnector  # type: ignore


class GmailSender:
    """Envía correos mediante Gmail API con adjuntos (multipart)."""

    def __init__(self):
        self._gmail = GmailConnector()
        self._svc = self._gmail._svc()
        if not self._svc:
            raise RuntimeError("No se pudo obtener el servicio de Gmail. Verifica la autenticación.")

    def send(self, to: str, subject: str, body_text: str, attachments: list[Path] | None = None) -> dict:
        """
        Envía un correo.

        Args:
            to: Dirección de correo destino.
            subject: Asunto.
            body_text: Cuerpo en texto plano.
            attachments: Lista de rutas de archivos a adjuntar.

        Returns:
            Respuesta de la API (dict con 'id' y 'threadId').
        """
        msg = MIMEMultipart()
        msg['To'] = to
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)

        # Cuerpo principal
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        # Adjuntos
        if attachments:
            for file_path in attachments:
                file_path = Path(file_path)
                if not file_path.exists():
                    continue
                mime_type = self._guess_mime(file_path)
                part = MIMEBase(mime_type[0], mime_type[1])
                part.set_payload(file_path.read_bytes())
                encoders.encode_base64(part)
                filename = file_path.name
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        resp = self._svc.users().messages().send(userId='me', body={'raw': raw}).execute()
        return resp

    @staticmethod
    def _guess_mime(path: Path) -> tuple[str, str]:
        import mimetypes
        mime, _ = mimetypes.guess_type(str(path))
        if not mime:
            return 'application', 'octet-stream'
        main, sub = mime.split('/', 1)
        return main, sub


# Función de conveniencia
def send_gmail_mime(to: str, subject: str, body_text: str, attachments: list[Path] | None = None) -> dict:
    """
    Wrapper simple para enviar un correo usando GmailSender.
    Ejemplo:
        send_gmail_mime(
            to="destino@ejemplo.com",
            subject="Prueba",
            body_text="Hola, esto es una prueba",
            attachments=[Path("archivo.pdf")]
        )
    """
    sender = GmailSender()
    return sender.send(to, subject, body_text, attachments)
