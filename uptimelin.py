# Запрашиваем Отчет по Uptime и свободному ОЗУ по Linux машинам
import paramiko
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
from tabulate import tabulate  # Импортируем функцию для создания таблиц

# Загружаем переменные окружения из файла .env
load_dotenv()

# Список хостов для опроса
hosts = [
    {"name": "Bitrix", "ip": "192.25.10.80", "login": "admin"},
    {"name": "Bitrix2", "ip": "192.168.100.52", "login": "admin"},
    {"name": "crm1", "ip": "192.168.100.53", "login": "admin"},
    {"name": "crm2", "ip": "192.168.100.43", "login": "admin"},
    {"name": "zabbix", "ip": "192.168.100.50", "login": "admin"},
    # Добавляем другие хосты по мере необходимости
]
# ФАЙЛ С ПАРОЛЯМИ .env ДОЛЖЕН ЛЕЖАТЬ РЯДОМ С ОСНОВНЫМ ФАЙЛОМ .py

# Функция для получения uptime и свободного ОЗУ
def get_host_info(host):
    password = os.getenv(f"{host['name'].upper()}_PASSWORD")
    if not password:
        return f"Пароль для {host['name']} не найден в .env"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host['ip'], username=host['login'], password=password)

        # Получаем uptime
        stdin, stdout, stderr = client.exec_command("uptime -p")
        uptime = stdout.read().decode().strip()

        # Получаем информацию о свободной памяти
        stdin, stdout, stderr = client.exec_command("free -m")
        memory_info = stdout.read().decode().strip().splitlines()

        # Извлекаем количество свободного ОЗУ
        free_memory_line = memory_info[1]  # Вторая строка содержит информацию о памяти
        free_memory_values = free_memory_line.split()  # Разделяем строку на значения

        # Извлекаем информацию о swap
        swap_line = memory_info[2]  # Третья строка содержит информацию о swap
        swap_values = swap_line.split()  # Разделяем строку на значения

        client.close()
        return uptime, free_memory_values, swap_values
    except Exception as e:
        return f"Ошибка при подключении к {host['name']}: {str(e)}, None, None"


# Получаем информацию для всех хостов
report_data = []
headers = ["Host", "Total", "Used", "Free", "Used Swap", "Uptime"]
for host in hosts:
    uptime, free_memory_values, swap_values = get_host_info(host)

    if free_memory_values is not None:
        total_mem = free_memory_values[1]
        used_mem = free_memory_values[2]
        free_mem = free_memory_values[3]
        used_swap = swap_values[2]

        row = [host['name'], total_mem, used_mem, free_mem, used_swap, uptime]
        report_data.append(row)
    else:
        error_row = [host['name'], "", "", "", "", uptime]
        report_data.append(error_row)

# Формируем HTML-таблицу
html_table = tabulate(report_data, headers=headers, tablefmt="html")

# Добавляем стили для выравнивания по центру
centered_html_table = html_table.replace('<td>', '<td align="center">').replace('<th>', '<th align="center">')

# Стилизация таблицы для лучшего отображения в почтовом клиенте
styled_html_table = (
    "<style>"
    "table { border-collapse: collapse; width: 100%; font-size: 14px; } "
    "th, td { border: 1px solid black; padding: 8px; } "
    "tr:nth-child(even) { background-color: #f2f2f2; } "
    "th { background-color: #4CAF50; color: white; } "
    "</style>" + centered_html_table
)

# Отправляем отчет по электронной почте
def send_email(styled_html_table):
    smtp_server = "192.168.100.5"
    sender_email = "5u@andruhes.ru"  # Укажите свой адрес электронной почты
    receiver_email = "it@andruhes.ru"
    subject = "Отчет по Uptime и свободному ОЗУ по Linux машинам"

    # Создаем многочастное сообщение и устанавливаем альтернативные части для текста и HTML
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    # Текстовая часть сообщения
    text_part = MIMEText("Это простое текстовое представление отчета.", "plain")
    html_part = MIMEText(styled_html_table, "html")  # HTML-версия таблицы

    # Добавляем обе версии в сообщение
    message.attach(text_part)
    message.attach(html_part)

    with smtplib.SMTP(smtp_server) as server:
        server.sendmail(sender_email, receiver_email, message.as_string())


# Отправляем отчет
send_email(styled_html_table)
print("Отчет отправлен на почту.")