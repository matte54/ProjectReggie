import smtplib
from email.mime.text import MIMEText

from systems.logger import log


class MailAlert:
    def __init__(self):
        self.sender = 'woodhouse@sol'
        self.recipient = 'matte'
        self.smtp_server = 'localhost'

    def send_mail(self, subject, message):
        msg = MIMEText(message)
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = subject

        try:
            log(f'[Mail] - Exception details sent to local mail user {self.recipient} ')
            server = smtplib.SMTP(self.smtp_server)
            server.sendmail(self.sender, self.recipient, msg.as_string())
            server.quit()
        except Exception as e:
            log(f'[Mail] - Failed to send email: {e}')
