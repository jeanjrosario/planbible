import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import settings


def send_reset_email(to_email: str, name: str, reset_url: str):
    if not settings.MAIL_USERNAME:
        print(f"[DEV] Reset link for {to_email}: {reset_url}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Redefinição de senha — Leitura Bíblica"
    msg["From"] = f"Leitura Bíblica <{settings.MAIL_FROM}>"
    msg["To"] = to_email

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#f8f7f4;font-family:'DM Sans',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center" style="padding:40px 20px;">
          <table width="480" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;border:1px solid #e8e6e1;">
            <tr><td style="padding:32px 40px 24px;border-bottom:1px solid #e8e6e1;">
              <p style="margin:0;font-size:13px;color:#a8a49d;text-transform:uppercase;letter-spacing:0.1em;">Leitura Bíblica 2026</p>
            </td></tr>
            <tr><td style="padding:32px 40px;">
              <h1 style="margin:0 0 12px;font-size:22px;font-weight:600;color:#1a1916;">Olá, {name} 👋</h1>
              <p style="margin:0 0 24px;font-size:15px;color:#6b6860;line-height:1.6;">
                Recebemos uma solicitação para redefinir a senha da sua conta. Clique no botão abaixo para criar uma nova senha.
              </p>
              <a href="{reset_url}" style="display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:13px 28px;border-radius:8px;font-size:14px;font-weight:600;">
                Redefinir minha senha
              </a>
              <p style="margin:24px 0 0;font-size:13px;color:#a8a49d;line-height:1.6;">
                Este link expira em <strong>1 hora</strong>. Se você não solicitou a redefinição, ignore este email.
              </p>
            </td></tr>
            <tr><td style="padding:20px 40px;border-top:1px solid #e8e6e1;">
              <p style="margin:0;font-size:12px;color:#a8a49d;">
                Se o botão não funcionar, copie e cole este link: <br>{reset_url}
              </p>
            </td></tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            if settings.MAIL_STARTTLS:
                server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
