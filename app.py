import streamlit as st
import random
import string
import qrcode
from io import BytesIO
import cv2
from pyzbar import pyzbar
import numpy as np

# ----------------------
# ピン候補一覧
# ----------------------
ALL_PINS = [
    {"id": 1, "name": "日本館ピン", "rarity": "common"},
    {"id": 2, "name": "アメリカ館ピン", "rarity": "common"},
    {"id": 3, "name": "SDGsピン", "rarity": "rare"},
    {"id": 4, "name": "ロボットピン", "rarity": "epic"},
    {"id": 5, "name": "宇宙館ピン", "rarity": "common"},
    {"id": 6, "name": "ドバイ館ピン", "rarity": "common"},
    {"id": 7, "name": "マスコットピン", "rarity": "rare"},
    {"id": 8, "name": "期間限定ピン", "rarity": "legendary"},
    {"id": 9, "name": "こどもピン", "rarity": "common"},
    {"id": 10, "name": "食文化ピン", "rarity": "rare"},
]

# ----------------------
# セッション初期化
# ----------------------
if "user_pins" not in st.session_state:
    # 初期所持ピンとしてランダムで1つ付与
    st.session_state.user_pins = [random.choice(ALL_PINS)]
if "exchange_pool" not in st.session_state:
    # QRコードとピンの紐付け情報を格納
    st.session_state.exchange_pool = {}
# ----------------------
# シリアルコード生成関数
# ----------------------
def generate_serial_code():
    return "EXPO-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

# ----------------------
# QRコード画像生成関数
# ----------------------
def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ----------------------
# QRコード読み取り関数（OpenCV + pyzbar）
# ----------------------
def read_qr_from_camera():
    cap = cv2.VideoCapture(0)
    st.info("カメラを起動中... QRコードをかざしてください。")

    detected_code = None
    placeholder = st.empty()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        decoded_objs = pyzbar.decode(frame)

        for obj in decoded_objs:
            code = obj.data.decode("utf-8")
            detected_code = code

            points = obj.polygon
            pts = [(p.x, p.y) for p in points]

            for i in range(len(pts)):
                pt1 = pts[i]
                pt2 = pts[(i + 1) % len(pts)]
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

            cv2.putText(frame, code, (pts[0][0], pts[0][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        placeholder.image(frame_rgb, channels="RGB")

        if detected_code:
            st.success(f"QRコード検出: {detected_code}")
            break

    cap.release()
    return detected_code

# ----------------------
# UI構成
# ----------------------
st.set_page_config(page_title="デジタル万博ピン交換", layout="centered")
st.title("デジタル万博ピン交換")

st.header("🔁 ピンを出す")

user_pins = st.session_state.user_pins
if user_pins:
    selected_pin_name = st.selectbox("交換に出すピンを選んでください", [p["name"] for p in user_pins])
    if st.button("QRコードとシリアルコードを発行"):
        selected_pin = next(p for p in user_pins if p["name"] == selected_pin_name)
        code = generate_serial_code()
        st.session_state.exchange_pool[code] = selected_pin
        # user_pins.remove(selected_pin) // 交換後に削除する場合はコメントアウトを外す
        st.success(f"ピン『{selected_pin_name}』のQRコードを発行しました")
        qr_buf = generate_qr_code(code)
        st.image(qr_buf)
        st.success(f"ピン『{selected_pin_name}』のシリアルコードを発行しました")
        st.text(code) 
        st.info("このQRコードかシリアルコードを相手に見せてください")
else:
    st.info("ピンがありません")

# ----------------------
# ピンを受け取る方法
# ----------------------
st.header("📥 ピンを受け取る")




if st.button("📸 カメラでQRを読み取る"):
    code_from_cam = read_qr_from_camera()
    if code_from_cam:
        pool = st.session_state.exchange_pool
        if code_from_cam in pool:
            received_pin = pool.pop(code_from_cam)
            user_pins.append(received_pin)
            st.success(f"🎉 『{received_pin['name']}』 を受け取りました！（QRから）")
        else:
            st.error("❌ QRコードは無効でした")

# 👇 手入力での受け取り処理を追加
input_code = st.text_input("シリアルコードを入力して下さい")

if st.button("✍️ コードを入力して受け取る"):
    pool = st.session_state.exchange_pool
    if input_code in pool:
        received_pin = pool.pop(input_code)
        user_pins.append(received_pin)
        st.success(f"🎉 『{received_pin['name']}』 を受け取りました！（手入力）")
    else:
        st.error("❌ 入力されたコードは無効です")


# ----------------------
# 所持ピン表示
# ----------------------
st.subheader("🎒 あなたの所持ピン")
if user_pins:
    for pin in user_pins:
        st.write(f"- {pin['name']} ({pin['rarity']})")
else:
    st.write("ピンなし")
