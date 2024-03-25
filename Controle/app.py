from flask import Flask, render_template, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from flask_socketio import SocketIO
from datetime import datetime
import pytz
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'segredo!'
socketio = SocketIO(app)

brasil_timezone = pytz.timezone('America/Sao_Paulo')

checkin_data = []  

def reset_checkin_data():
    global checkin_data
    now = datetime.now(brasil_timezone)
    if now.hour == 0 and now.minute == 0:
        checkin_data = []
        print("Dados de check-in reiniciados.")

scheduler = BackgroundScheduler()
scheduler.add_job(reset_checkin_data, 'cron', hour=0, minute=0, timezone='America/Sao_Paulo')
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/export_excel')
def export_excel():
    df = pd.DataFrame(checkin_data, columns=['Operador', 'Timestamp'])

    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    df['Data'] = df['Timestamp'].dt.date

    df = df[['Operador','Timestamp']]

    excel_file_path = 'checkin_data.xlsx'
    df.to_excel(excel_file_path, index=False)

    return send_file(excel_file_path, as_attachment=True)

@socketio.on('checkin')
def handle_checkin(json):
    timestamp = datetime.fromisoformat(json['timestamp'])
    timestamp_brasil = timestamp.astimezone(brasil_timezone)
    formatted_time = timestamp_brasil.strftime('%H:%M')
    print('Recebido check-in: ' + str(json))
    checkin_data.append([json['operador'], formatted_time])  
    socketio.emit('checkin', {'operador': json['operador'], 'timestamp': formatted_time})



if __name__ == '__main__':
    socketio.run(app, debug=True)
