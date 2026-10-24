# ⌨️ Air Keyboard

Type in mid-air using nothing but your webcam and your hands. 

**Air Keyboard** tracks your hands in real time and shows a glowing virtual keyboard on screen. Move your index finger over a key, **pinch** your thumb and index finger together, and the key is typed. No hardware, no touch, just your hands.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-computer%20vision-blue?logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-hand%20tracking-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## 📸 Demo

<!-- Replace the file names below with your own screenshots / GIF inside a "screenshots" folder -->

![Main screen](<img width="1059" height="632" alt="1022" src="https://github.com/user-attachments/assets/9407f58b-04d0-4739-9939-f6fc04ad29c5" />

---

## ✨ Features

- 🖐️ **Real-time hand tracking** with MediaPipe, using one or two hands at the same time
- 🤏 **Pinch to type**: thumb + index finger press the key under your fingertip
- 💡 **Backlit keys**: a pressed key lights up blue and fades out slowly, like a real backlit keyboard
- 🎯 **Accurate key selection**: the key is chosen from where your finger was just *before* the pinch, so the wrong letter isn't typed when your finger moves
- 🧠 **Word suggestions**: three suggestion chips above the keyboard finish the word with one pinch
- 🔠 **Auto capitalization** at the start of sentences, plus `,` and `.` keys
- 🔊 **Click sound** on each key press (Windows)
- ⌨️ **Optional system typing**: send the typed keys to any other app

---

## 🧠 How it works

1. **OpenCV** reads frames from the webcam and draws the interface.
2. **MediaPipe Hand Landmarker** finds 21 landmarks on each hand.
3. The **index fingertip** (landmark 8) is the cursor.
4. The distance between **thumb tip (4)** and **index tip (8)**, divided by the hand size, is the pinch value. Dividing by hand size means pinching works at any distance from the camera.
5. When the pinch value drops below a threshold, a key press is triggered on that key.

---

## 🛠️ Tech stack

| Tool | Used for |
|---|---|
| Python | Main language |
| OpenCV | Camera, drawing, window |
| MediaPipe (Tasks API) | Hand landmark detection |
| NumPy | Image layers and glow effect |
| PyAutoGUI *(optional)* | Typing into other apps |

---

## 🚀 Getting started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Create a virtual environment (recommended)

**Windows**
```bash
py -m venv venv
venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the requirements

```bash
pip install -r requirements.txt
```

### 4. Run it

```bash
python air_keyboard.py
```

On the first run the hand-tracking model (`hand_landmarker.task`, about 8 MB) is **downloaded automatically**, so you need an internet connection once. After that it works offline.

---

## 🎮 How to use

| Action | What to do |
|---|---|
| Move the cursor | Point with your **index finger** |
| Press a key | **Pinch** thumb + index finger over the key |
| Accept a word suggestion | Pinch one of the 3 chips above the keyboard |
| Delete / clear | Pinch **DEL** or **CLEAR** |
| Clear text | Press `c` in the window |
| Fullscreen | Press `f` |
| Quit | Press `q` |

**Tips for best results**
- Sit about an arm's length from the camera in good light.
- Keep your hands in the lower half of the picture, over the keyboard.
- Pinch quickly and open your fingers fully between presses.

---

## ⚙️ Settings

All settings are at the top of `air_keyboard.py`.

| Setting | Default | What it does |
|---|---|---|
| `CAMERA_INDEX` | `0` | Which camera to use. Try `1` if the window is black |
| `CAM_W`, `CAM_H` | `1280`, `720` | Camera resolution. Use `1920`, `1080` for a sharper picture |
| `PINCH_ON` | `0.30` | Raise if pinches aren't detected, lower if keys press by accident |
| `PINCH_OFF` | `0.45` | How wide you must open your fingers to press again |
| `LOOKBACK` | `0.20` | Raise if the wrong letter gets typed |
| `FADE_SPEED` | `1.6` | Lower = backlight stays on longer |
| `SOUND` | `True` | Turn the click sound on or off |
| `SYSTEM_TYPING` | `False` | `True` sends keystrokes to other apps (needs PyAutoGUI) |

---

## 🧯 Troubleshooting

**`module 'mediapipe' has no attribute 'solutions'`**
Newer MediaPipe versions removed the old `mp.solutions` API. This project already uses the new Tasks API, so make sure you run `air_keyboard.py` from this repo.

**Camera window is black or the camera doesn't open**
Close other apps using the camera (Zoom, Teams, Camera app) and try `CAMERA_INDEX = 1`.

**Model download fails**
Download the file manually and place it next to `air_keyboard.py`:
`https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`

**`No module named 'cv2'`**
Your virtual environment isn't active or the packages aren't installed. Run `pip install -r requirements.txt` with `(venv)` showing in the terminal.

---

## 📁 Project structure

```
.
├── air_keyboard.py      # main application
├── requirements.txt     # dependencies
├── screenshots/         # images used in this README
└── README.md
```

---

## 🔮 Future ideas

- [ ] Swipe gesture for backspace
- [ ] Shift key and number row
- [ ] Better word prediction (next-word suggestions)
- [ ] Press detection using fingertip depth (a real "tap in the air")
- [ ] Custom themes and key sizes
- [ ] Gesture to move or resize the keyboard


If you like this project, give it a ⭐
