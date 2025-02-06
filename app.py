from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import cv2
import mediapipe as mp
import base64
import numpy as np

client = MongoClient("mongodb://localhost:27017/")
db = client['shop']
users = db['users']
dress = db['dress']

app = Flask(__name__)
app.secret_key = "9999"

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

def overlay_dress(image, pose_landmarks, dress_img):
    left_shoulder = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = pose_landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = pose_landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

    dress_width = int((right_shoulder.x - left_shoulder.x) * image.shape[1])
    dress_height = int((left_hip.y - left_shoulder.y) * image.shape[0])

    dress_resized = cv2.resize(dress_img, (dress_width, dress_height))
    top_left = (int(left_shoulder.x * image.shape[1]), int(left_shoulder.y * image.shape[0]))
    bottom_right = (top_left[0] + dress_width, top_left[1] + dress_height)

    overlay_image_alpha(image, dress_resized[:, :, 0:3], dress_resized[:, :, 3] / 255.0, top_left)

def overlay_image_alpha(background, overlay, alpha, position):
    x, y = position
    y2 = y + overlay.shape[0]
    x2 = x + overlay.shape[1]

    if y2 > background.shape[0]:
        overlay = overlay[:background.shape[0] - y, :, :]
        y2 = background.shape[0]
    if x2 > background.shape[1]:
        overlay = overlay[:, :background.shape[1] - x, :]
        x2 = background.shape[1]

    for c in range(0, 3):
        background[y:y2, x:x2, c] = (1 - alpha) * background[y:y2, x:x2, c] + alpha * overlay[:, :, c]

@app.route('/tryon', methods=['POST'])
def tryon():
    data = request.json
    image_data = base64.b64decode(data['image'])
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    dress_img = cv2.imread('static/images/dress1.png', cv2.IMREAD_UNCHANGED)

    results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    if results.pose_landmarks:
        overlay_dress(image, results.pose_landmarks.landmark, dress_img)

    _, buffer = cv2.imencode('.png', image)
    return jsonify({'image': base64.b64encode(buffer).decode('utf-8')})

@app.route('/')
def one():
    return render_template('main.html')

@app.route('/home')
def onett():
    return render_template('home.html')

@app.route('/about')
def two():
    return render_template('aboutus.html')

@app.route('/contact')
def twotw():
    return render_template('contactus.html')

@app.route('/products')
def three():
    data = dress.find()
    return render_template('products.html', data=data)

@app.route('/cart')
def threeth():
    data = users.find_one({'mail': session['user']})
    return render_template('cart2.html', data=data)

@app.route('/sign')
def four():
    return render_template('signupsigin.html')

@app.route('/signup', methods=['post'])
def six():
    name = request.form['Name']
    email = request.form['email']
    passs = request.form['password']
    passs2 = request.form['password1']
    cart = []
    if passs == passs2:
        exist = users.find_one({'mail': email})
        if not exist:
            users.insert_one({'name': name, 'mail': email, 'pass': passs, 'cart': cart})
            return render_template('signupsigin.html', res="registration successful")
    return render_template('signupsigin.html', res="registration failed")

@app.route('/login', methods=['post'])
def five():
    email = request.form['email']
    passs = request.form['password']
    exist = users.find_one({'mail': email})
    if exist and passs == exist['pass']:
        session['user'] = email
        return render_template('home.html')
    return render_template('signupsigin.html', res="login failed")

@app.route('/addtocart')
def nine():
    name = request.args.get('name')
    users.update_one({'mail': session['user']}, {'$push': {'cart': name}})
    return redirect('/cart')

if __name__ == "__main__":
    app.run(debug=True)