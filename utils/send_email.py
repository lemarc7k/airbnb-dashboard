from mailjet_rest import Client
import os

api_key = os.getenv("b389be0a3006a39c7c4ead558479a3ee") or "TU_API_KEY"
api_secret = os.getenv("9a193c95dbd08684cde61dea445ce949") or "TU_API_SECRET"
mailjet = Client(auth=(api_key, api_secret), version='v3.1')

def send_cleaning_alert_email(subject, message, to_email):
    data = {
      'Messages': [
        {
          "From": {
            "Email": "tucorreo@tudominio.com",
            "Name": "Airbnb Bot"
          },
          "To": [
            {
              "Email": to_email,
              "Name": "Supervisor"
            }
          ],
          "Subject": subject,
          "TextPart": message,
        }
      ]
    }
    result = mailjet.send.create(data=data)
    return result.status_code
