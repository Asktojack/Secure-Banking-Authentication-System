
import os
import secrets
from twilio.rest import Client

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

client = None

if ACCOUNT_SID and AUTH_TOKEN:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)


def send_sms(phone, message):
    if client is None or not TWILIO_NUMBER:
        raise RuntimeError("Twilio configuration is missing.")

    otp = str(secrets.randbelow(900000) + 100000)

    client.messages.create(
        body=f"Your Secure Bank OTP is {otp}",
        from_=TWILIO_NUMBER,
        to="+91" + phone
    )

    return otp
