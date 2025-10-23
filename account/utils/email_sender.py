import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

def send_email_with_attachments(sender_email, receiver_email, password, subject, body, file_paths):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    for file_path in file_paths:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                msg.attach(part)

    try:
        with smtplib.SMTP('smtp.yandex.ru', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            text = msg.as_string()
            server.sendmail(sender_email, receiver_email, text)
            print('Сообщение с вложениями отправлено успешно!')
    except Exception as e:
        print(f'Ошибка при отправке письма: {e}')
