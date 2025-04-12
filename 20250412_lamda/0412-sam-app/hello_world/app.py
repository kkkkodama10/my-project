
import smtplib
from email.mime.text import MIMEText
import os
import json

def lambda_handler(event, context):
    try:
        # POSTされたJSONを読み取る
        body = json.loads(event.get("body", "{}"))
        to = body.get("to", "youraddress@gmail.com")
        message_body = body.get("body", "デフォルトメッセージ")

        # メール送信設定
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.environ["GMAIL_USER"]
        sender_pass = os.environ["GMAIL_PASS"]

        msg = MIMEText(message_body)
        msg["Subject"] = "Lambda POSTメール通知"
        msg["From"] = sender_email
        msg["To"] = to

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_pass)
        server.sendmail(sender_email, to, msg.as_string())
        server.quit()

        return {
            "statusCode": 200,
            "body": json.dumps({"result": "送信成功！"}, ensure_ascii=False)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
