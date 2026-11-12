from flask_mail import Message


def send_email(mail, receiver_email, otp):

    msg = Message(

        subject="Secure Banking OTP Verification",

        sender=mail.app.config["MAIL_USERNAME"],

        recipients=[receiver_email]

    )

    msg.body = f"""
Welcome to Secure Banking.

Your One-Time Password (OTP) is:

{otp}

This OTP is valid for 5 minutes.

Do not share this OTP with anyone.

Thank you,
Secure Banking Team
"""

    mail.send(msg)