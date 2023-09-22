from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib

def send_email(image_data):
    msg = MIMEMultipart('related')
    msg['From'] = 'hraffnir@gmail.com'
    msg['To'] = 'sareyis952@alvisani.com'
    msg['Subject'] = 'Intruder Detection Alert'

    html = """
    <html>
        <body>
            <h4 class="color: red;">A possible intruder was detected.</h4>
            <p>Please review the snapshot below.</p>
            <img src="cid:image1" alt="Snapshot">
        </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))

    image = MIMEImage(image_data, name='snapshot.jpg')
    image.add_header('Content-ID', '<image1>')
    msg.attach(image)

    with smtplib.SMTP('sandbox.smtp.mailtrap.io') as server:
        server.login('8ab6d4a56d949c', 'b4287219a0d701')
        server.sendmail('hraffnir@gmail.com', 'sareyis952@alvisani.com', msg.as_string())