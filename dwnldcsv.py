from flask import Flask, send_file
import io
import pandas as pd
import threading

app = Flask(__name__)
dataframe = None

@app.route('/download_csv')
def download_csv():
    global dataframe
    if dataframe is None:
        return "No data available", 404
    
    output = io.BytesIO()
    dataframe.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='data.csv'
    )

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def setup_and_run_flask(df):
    global dataframe
    dataframe = df
    if not flask_thread.is_alive():
        flask_thread.start()

flask_thread = threading.Thread(target=run_flask)
