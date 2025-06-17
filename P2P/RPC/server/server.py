from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/download')
def download():
    file_path = os.getenv("FILE_PATH", "file.iso")
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)