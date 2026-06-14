import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MedCareAI-Notifications")

def send_sms(to_phone: str, message: str) -> bool:
    """
    Sends an SMS notification. If Twilio keys are missing, logs it to console as a mock.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    
    if account_sid and auth_token and from_number:
        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message,
                from_=from_number,
                to=to_phone
            )
            logger.info(f"Real SMS sent to {to_phone} successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send real SMS via Twilio: {e}. Falling back to mock.")
            
    # Mock Log Fallback
    logger.info(f"\n--- [MOCK SMS SEND] --- \nTo: {to_phone}\nMessage: {message}\n-----------------------\n")
    return True

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an Email notification. Falls back to mock logs if SMTP configurations are blank.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if smtp_username and smtp_password:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_email, msg.as_string())
            server.close()
            logger.info(f"Real Email sent to {to_email} successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to send real Email: {e}. Falling back to mock.")

    # Mock Log Fallback
    logger.info(f"\n--- [MOCK SMTP EMAIL] --- \nTo: {to_email}\nSubject: {subject}\nBody: {body}\n-------------------------\n")
    return True

def generate_voice_alert(message: str, output_dir: str, filename: str) -> str:
    """
    Uses gTTS to generate a Text-to-Speech audio reminder (.mp3).
    Falls back gracefully if offline.
    
    :return: Path to the generated audio file
    """
    # Ensure static directory exists
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    try:
        from gtts import gTTS
        tts = gTTS(text=message, lang='en', slow=False)
        tts.save(file_path)
        logger.info(f"Voice alert audio file saved at {file_path}")
        return file_path
    except Exception as e:
        logger.warning(f"Could not generate TTS file (likely offline): {e}. Creating a mock file flag.")
        # Create a dummy text file to simulate output creation if offline
        with open(file_path.replace(".mp3", ".txt"), "w") as f:
            f.write(f"[MOCK TTS AUDIO]: {message}")
        return file_path.replace(".mp3", ".txt")
