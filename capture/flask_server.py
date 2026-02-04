from flask import Flask, jsonify, Response, request, send_file
import subprocess
import threading
import time
import os
import re

app = Flask(__name__)

PYTHON_EXE = r"C:\Users\smhrd\.conda\envs\est_capture\pythonw.exe"
CAPTURE_SCRIPT = r"C:\scripts\estcapture.py"
BASE_FOLDER = r"C:\Users\smhrd\Desktop\출결"

TIMEOUT_SEC = 120
lock = threading.Lock()


def find_latest_image():
    """BASE_FOLDER에서 가장 최근 jpg 파일 찾기"""
    from datetime import datetime
    import glob

    # 오늘 날짜 폴더
    today_folder = os.path.join(BASE_FOLDER, datetime.now().strftime("%Y%m%d"))
    if not os.path.isdir(today_folder):
        return None

    # 해당 폴더의 jpg 파일들
    files = glob.glob(os.path.join(today_folder, "*.jpg"))
    if not files:
        return None

    # 수정 시간 기준 가장 최근 파일
    return max(files, key=os.path.getmtime)


@app.get("/ui")
def ui():
    html = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8"/>
  <title>Capture</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    #preview { max-width: 50%; margin-top: 15px; border: 1px solid #ccc; display: none; }
    button { font-size: 18px; padding: 10px 30px; cursor: pointer; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    #status { margin-top: 10px; color: #666; }
    #filepath { margin-top: 5px; font-size: 12px; color: #888; }
  </style>
</head>
<body>
  <h3>Capture</h3>
  <button id="btn" onclick="run()">찰칵</button>
  <div id="status"></div>
  <div id="filepath"></div>
  <img id="preview" alt="captured"/>
  <script>
    async function run(){
      const btn = document.getElementById('btn');
      const status = document.getElementById('status');
      const preview = document.getElementById('preview');
      const filepath = document.getElementById('filepath');

      btn.disabled = true;
      status.textContent = '캡처 중...';
      preview.style.display = 'none';

      try {
        const r = await fetch('/capture', {method:'POST'});
        const data = await r.json();

        if(data.ok && data.image_path){
          status.textContent = '캡처 완료!';
          filepath.textContent = data.image_path;
          preview.src = '/image?path=' + encodeURIComponent(data.image_path) + '&t=' + Date.now();
          preview.style.display = 'block';
        } else {
          status.textContent = '캡처 실패: ' + (data.message || data.result || 'Unknown error');
        }
      } catch(e) {
        status.textContent = '오류: ' + e.message;
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>"""
    return Response(html, mimetype="text/html; charset=utf-8")


@app.post("/capture")
def capture():
    # 동시 실행 방지
    if not lock.acquire(blocking=False):
        return jsonify(ok=False, message="capture already running"), 429

    try:
        start = time.time()

        # 캡처 전 최신 파일 시간 기록
        before_latest = find_latest_image()
        before_mtime = os.path.getmtime(before_latest) if before_latest else 0

        proc = subprocess.run(
            [PYTHON_EXE, CAPTURE_SCRIPT, "--force"],
            capture_output=True,
            text=False,
            timeout=TIMEOUT_SEC
        )

        elapsed = round(time.time() - start, 2)

        if proc.returncode != 0:
            return jsonify(
                ok=False,
                elapsed_sec=elapsed,
                returncode=proc.returncode
            ), 500

        # 캡처 후 최신 파일 찾기
        time.sleep(0.3)  # 파일 저장 완료 대기
        image_path = find_latest_image()

        # 새 파일인지 확인
        if image_path and os.path.getmtime(image_path) > before_mtime:
            return jsonify(
                ok=True,
                elapsed_sec=elapsed,
                image_path=image_path
            )
        else:
            return jsonify(
                ok=False,
                elapsed_sec=elapsed,
                message="캡처 파일을 찾을 수 없습니다"
            ), 500

    except subprocess.TimeoutExpired:
        return jsonify(ok=False, message=f"capture timeout ({TIMEOUT_SEC}s)"), 504

    finally:
        lock.release()


@app.get("/image")
def get_image():
    """저장된 이미지 파일 제공"""
    path = request.args.get("path", "")

    # 보안: BASE_FOLDER 내의 파일만 허용
    if not path or not path.startswith(BASE_FOLDER):
        return jsonify(ok=False, message="Invalid path"), 400

    if not os.path.isfile(path):
        return jsonify(ok=False, message="File not found"), 404

    return send_file(path, mimetype="image/jpeg")


@app.get("/health")
def health():
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
