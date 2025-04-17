
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_cleaning_alert_email(subject, message, to_email):
    # Configuración del remitente
    from_email = "tucorreo@gmail.com"  # ← Cambia esto por tu correo de Gmail
    password = "TU_APP_PASSWORD"       # ← Inserta aquí tu App Password de Gmail

    # Crear mensaje
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(message, "plain"))

    try:
        # Conectar a Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        print("✅ Email enviado correctamente.")
        return 200
    except Exception as e:
        print(f"❌ Error al enviar email: {e}")
        return 500
