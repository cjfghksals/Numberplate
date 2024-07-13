from flask import Flask, render_template, Response, request, jsonify, g
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import pytesseract
import re
import sqlite3
from PIL import ImageFont, ImageDraw, Image
from ultralytics import YOLO
import requests
import time

# Tesseract OCR 경로
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# YOLO 모델 로드
model = YOLO(r"C:\Moble\Yungeun\trianing\license-plate-5\model\64_100.pt")

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

# 데이터베이스 경로
DATABASE = r"C:\Moble\Yungeun\CAR.db"

# 소켓 클라이언트 집합 정의
socket_clients = set()

# 데이터베이스 연결 관리
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# 데이터베이스 연결 닫기
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# 번호판 검출 및 인식
def detect_and_extract_license_plate(frame):
    # YOLO 모델을 사용하여 객체 감지
    results = model(frame, stream=True)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            # 경계 상자 좌표 추출
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # 번호판 이미지 추출
            license_plate = frame[y1:y2, x1:x2]

            # 이미지 전처리: 필터링
            license_plate = cv2.GaussianBlur(license_plate, (5, 5), 0)

            # 이미지 전처리: 이진화
            gray_plate = cv2.cvtColor(license_plate, cv2.COLOR_BGR2GRAY)
            _, binary_plate = cv2.threshold(
                gray_plate, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
            )

            # 번호판에서 텍스트 인식
            text = pytesseract.image_to_string(
                gray_plate,
                config="--psm 7 --oem 1 -l kor",  # 한국어를 인식하기 위해 설정
            )

            # 띄어쓰기 제거
            text = text.replace(" ", "")

            # 텍스트 필터링 및 검증
            if (
                text
                and text[0].isdigit()
                and not re.search(r'[!@#$%^&*(),.?":{}|<>\'\[\]]', text)
                and len(text) == 9  # 앞 숫자 3글자인 번호판만으로 실험하기
                and text[3]
                in "가나다라마거너더러머버서어저고노도로모보소오구누두루무부수우주하허호배공육해"
            ):
                # 번호판 정보 출력
                print("Detected license plate:", text.strip())

                # 데이터베이스에서 번호 조회 및 출력
                with app.app_context():
                    search_and_print_data(text.strip())

                # 웹 소켓 클라이언트에게 데이터 전송
                send_data_to_clients(text.strip())

                # 번호판 주변 사각형
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # 화면에 한국어 putText
                frame = draw_text(frame, text.strip(), (x1 - 50, y1 - 20))

    return frame

# 차단기 제어 함수 추가
def control_barrier(barrier_type):
    url = f"http://192.168.0.3/control?type={barrier_type}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"{barrier_type} 차단기 열림")
        time.sleep(3)  # 3초 대기
        response = requests.get(url)
        if response.status_code == 200:
            print(f"{barrier_type} 차단기 닫힘")
        else:
            print(f"{barrier_type} 차단기 닫기 실패")
    else:
        print(f"{barrier_type} 차단기 열기 실패")

# 데이터베이스에서 번호 조회 및 출력
def search_and_print_data(license_number):
    select_query = """
        SELECT car_number, phone_number, address
        FROM DATA
        WHERE ? LIKE '%' || car_number || '%'
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(select_query, (license_number,))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            car_number, phone_number, address = row
            print(f"입주자 차량입니다.")
            print(f"차량 번호: {car_number}, 전화번호: {phone_number}, 주소: {address}")
            # 클라이언트에게 메시지 전송
            emit_to_clients(
                {
                    "plate_number": license_number,
                    "info1": f"입주자 차량입니다.",
                    "info2": f"차량 번호: {car_number}, 전화번호: {phone_number}, 주소: {address}",
                }
            )
            # 입주자 차단기 열기
            control_barrier("resident")
    else:
        print(f"방문자 차량입니다.")
        # 클라이언트에게 메시지 전송
        emit_to_clients({"plate_number": license_number, "info": "방문자 차량입니다."})
        # 방문자 차단기 열기
        control_barrier("visitor")

# 이미지에 한국어 putText
def draw_text(image, text, position):
    # PIL 이미지로 변환
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)

    # 한국어 폰트 설정
    font_path = r"C:\Moble\Yungeun\python\font\경기천년제목_MEDIUM.TTF"
    font = ImageFont.truetype(font_path, 30)

    draw.text(position, text, font=font, fill=(0, 255, 0))

    # PIL 이미지를 OpenCV 형식으로 변환
    image = np.array(pil_image)

    return image

# 클라이언트에게 데이터 전송
def send_data_to_clients(plate_number):
    for client in socket_clients:
        socketio.emit(
            "plate_info",
            {
                "plate_number": plate_number,
                "info": "차량 정보를 조회하였습니다.",  
            },
            room=client,
        )

# 웹 소켓을 통해 클라이언트에게 메시지 전송
def emit_to_clients(data):
    for client in socket_clients:
        socketio.emit("server_message", data, room=client)

# 라우트 설정
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(
        video_stream(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )

# 비디오 스트리밍 제공
def video_stream():
    cap = cv2.VideoCapture(
        "http://192.168.0.3:81/stream"
    )  # 아두이노 HTML 프로토콜 주소
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_with_plate = detect_and_extract_license_plate(frame)

        # JPEG로 인코딩
        ret, buffer = cv2.imencode(".jpg", frame_with_plate)
        frame_with_plate = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_with_plate + b"\r\n"
        )

    cap.release()

# 소켓 연결 및 이벤트 핸들링
@socketio.on("connect")
def handle_connect():
    socket_clients.add(request.sid)
    print(f"Client {request.sid} connected")

@socketio.on("disconnect")
def handle_disconnect():
    socket_clients.remove(request.sid)
    print(f"Client {request.sid} disconnected")

if __name__ == "__main__":
    socketio.run(app)
