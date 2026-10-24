"""
AIR KEYBOARD v2  -  neon hand-tracking keyboard
------------------------------------------------
* Works with ONE or TWO hands at the same time.
* Move your index fingertip over a key, then PINCH (thumb + index) to type.
* The 3 buttons above the keyboard are word suggestions - pinch one to finish the word.
* Keys:  q = quit   c = clear text

If it types the WRONG letter  -> raise LOOKBACK (0.2 -> 0.3)
If pinch does not register    -> raise PINCH_ON (0.30 -> 0.36)
If it presses by accident     -> lower PINCH_ON (0.30 -> 0.24)
"""
import math
import os
import re
import textwrap
import threading
import time
import urllib.request
from collections import deque

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# ------------------------- SETTINGS -------------------------
SYSTEM_TYPING = False   # True = also type into other apps (pip install pyautogui)
SOUND = True            # click sound (Windows only)
CAMERA_INDEX = 0
PINCH_ON = 0.30         # pinch closer than this  -> press
PINCH_OFF = 0.45        # open wider than this    -> ready for next press
LOOKBACK = 0.20         # seconds: key is chosen from where your finger WAS before the pinch
# ------------------------------------------------------------

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/1/hand_landmarker.task")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
    (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]
HAND_COLORS = [(255, 255, 0), (255, 0, 255)]  # BGR: cyan, magenta

WORDS = list(dict.fromkeys("""
the be to of and a in that have i it for not on with he as you do at this but his by from they we say her she
or an will my one all would there their what so up out if about who get which go me when make can like time no
just him know take people into year your good some could them see other than then now look only come its over
think also back after use two how our work first well way even new want because any these give day most us is
are was were been has had did said here very hello thanks thank please yes okay great love happy today tomorrow
morning night friend family home school world life name where why should need help find going really still every
little never before always something nothing everything someone together anything again another feel keep let put
tell call try ask seem leave mean show hear play run move live believe hold bring happen write provide sit stand
lose pay meet include continue set learn change lead understand watch follow stop create speak read allow add
spend grow open walk win offer remember consider appear buy wait serve send expect build stay fall cut reach
keyboard air project awesome hand camera computer python code cool nice amazing beautiful sentence type typing
message welcome evening afternoon sorry right best better today where while with without would
""".split()))

try:
    import winsound
except ImportError:
    winsound = None

if SYSTEM_TYPING:
    import pyautogui


def click():
    if SOUND and winsound:
        threading.Thread(target=winsound.Beep, args=(1100, 25), daemon=True).start()


def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading hand model (one time)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def hue_color(frac):
    hsv = np.uint8([[[int(max(0, min(1, frac)) * 179), 255, 255]]])
    b, g, r = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
    return int(b), int(g), int(r)


def sc(color, a):
    return tuple(int(v * a) for v in color)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ------------------------- TYPING LOGIC -------------------------
class Typer:
    def __init__(self):
        self.text = ""

    def current_word(self):
        m = re.search(r"[A-Za-z']+$", self.text)
        return m.group(0) if m else ""

    def add_char(self, ch):
        if ch.isalpha():
            start = self.text == "" or self.text.endswith((". ", "? ", "! "))
            ch = ch.upper() if start else ch.lower()
        self.text += ch
        if SYSTEM_TYPING:
            pyautogui.write(ch)

    def add_space(self):
        self.text += " "
        if SYSTEM_TYPING:
            pyautogui.press("space")

    def delete(self):
        self.text = self.text[:-1]
        if SYSTEM_TYPING:
            pyautogui.press("backspace")

    def clear(self):
        self.text = ""

    def suggestions(self):
        cur = self.current_word().lower()
        if not cur:
            return ["the", "I", "hello"]
        return [w for w in WORDS if w.startswith(cur) and w != cur][:3]

    def accept(self, word):
        cur = self.current_word()
        if cur and cur[0].isupper():
            word = word[0].upper() + word[1:]
        if cur:
            self.text = self.text[:-len(cur)]
            if SYSTEM_TYPING:
                for _ in cur:
                    pyautogui.press("backspace")
        self.text += word + " "
        if SYSTEM_TYPING:
            pyautogui.write(word + " ")


# ------------------------- KEYBOARD LAYOUT -------------------------
def build_keys(w, h, typer):
    kw, kh, gap = int(w * 0.078), int(h * 0.09), int(w * 0.008)
    top = int(h * 0.54)
    keys = []
    rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM,."]
    shifts = [0.0, 0.3, 0.6]
    for r, row in enumerate(rows):
        row_w = len(row) * (kw + gap) - gap
        x0 = (w - row_w) / 2 + (shifts[r] - 0.3) * kw
        for i, ch in enumerate(row):
            x = int(x0 + i * (kw + gap))
            keys.append(dict(kind="char", label=ch, value=ch, x=x, y=top + r * (kh + gap),
                             w=kw, h=kh, color=hue_color(x / w)))
    widths = [5 * kw + 4 * gap, 2 * kw + gap, 2 * kw + gap]
    x = int((w - (sum(widths) + 2 * gap)) / 2)
    for label, bw in zip(["SPACE", "DEL", "CLEAR"], widths):
        keys.append(dict(kind="action", label=label, value=label, x=x, y=top + 3 * (kh + gap),
                         w=bw, h=kh, color=hue_color(x / w)))
        x += bw + gap
    sw = int(kw * 2.8)
    sx = (w - (3 * sw + 2 * gap)) / 2
    for j, word in enumerate(typer.suggestions()):
        xx = int(sx + j * (sw + gap))
        keys.append(dict(kind="sugg", label=word, value=word, x=xx, y=top - kh - gap * 2,
                         w=sw, h=kh, color=(255, 255, 255)))
    return keys


def key_at(pt, keys, pad=4):
    if pt is None:
        return None
    for i, k in enumerate(keys):
        if k["x"] - pad <= pt[0] <= k["x"] + k["w"] + pad and k["y"] - pad <= pt[1] <= k["y"] + k["h"] + pad:
            return i
    return None


class Hand:
    def __init__(self):
        self.reset()

    def reset(self):
        self.smooth = None
        self.hist = deque()
        self.trail = deque(maxlen=22)
        self.pinched = False
        self.hover = None


def past_position(hist, target_t):
    for t, p in reversed(hist):
        if t <= target_t:
            return p
    return hist[0][1] if hist else None


# ------------------------- MAIN -------------------------
def main():
    ensure_model()
    options = vision.HandLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    landmarker = vision.HandLandmarker.create_from_options(options)

    cap = (cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW) if os.name == "nt"
           else cv2.VideoCapture(CAMERA_INDEX))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    typer = Typer()
    hands = [Hand(), Hand()]
    flash, ripples = {}, []
    start, last_ts, prev, fps = time.time(), 0, time.time(), 0.0

    def activate(k):
        if k["kind"] == "char":
            typer.add_char(k["value"])
        elif k["kind"] == "sugg":
            typer.accept(k["value"])
        elif k["label"] == "SPACE":
            typer.add_space()
        elif k["label"] == "DEL":
            typer.delete()
        elif k["label"] == "CLEAR":
            typer.clear()
        click()

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        now = time.time()
        fps = 0.9 * fps + 0.1 / max(now - prev, 1e-3)
        prev = now

        keys = build_keys(w, h, typer)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ts = max(int((now - start) * 1000), last_ts + 1)
        last_ts = ts
        result = landmarker.detect_for_video(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)

        # ---------- hands ----------
        skeletons = []
        for i in range(2):
            st = hands[i]
            if i >= len(result.hand_landmarks):
                st.reset()
                continue
            lm = result.hand_landmarks[i]
            pts = [(p.x * w, p.y * h) for p in lm]
            raw = pts[8]
            st.smooth = raw if st.smooth is None else (
                st.smooth[0] * 0.5 + raw[0] * 0.5, st.smooth[1] * 0.5 + raw[1] * 0.5)
            st.hist.append((now, st.smooth))
            while st.hist and now - st.hist[0][0] > 0.8:
                st.hist.popleft()
            st.trail.append(st.smooth)

            ratio = dist(pts[4], pts[8]) / max(dist(pts[0], pts[9]), 1.0)
            if not st.pinched and ratio < PINCH_ON:
                st.pinched = True
                idx = key_at(past_position(st.hist, now - LOOKBACK), keys)
                if idx is None:
                    idx = key_at(st.smooth, keys)
                st.hover = idx
                if idx is not None:
                    k = keys[idx]
                    activate(k)
                    flash[k["label"]] = now
                    ripples.append([k["x"] + k["w"] / 2, k["y"] + k["h"] / 2, now, HAND_COLORS[i]])
            elif st.pinched and ratio > PINCH_OFF:
                st.pinched = False
            if not st.pinched:
                st.hover = key_at(st.smooth, keys)
            skeletons.append((i, pts))

        # ---------- drawing ----------
        frame = cv2.convertScaleAbs(frame, alpha=0.42)            # dim camera
        overlay = frame.copy()
        for k in keys:
            cv2.rectangle(overlay, (k["x"], k["y"]), (k["x"] + k["w"], k["y"] + k["h"]), (28, 22, 30), -1)
        bar_bottom = int(h * 0.20)
        cv2.rectangle(overlay, (40, 20), (w - 40, bar_bottom), (28, 22, 30), -1)
        frame = cv2.addWeighted(overlay, 0.65, frame, 0.35, 0)

        fx = np.zeros_like(frame)                                 # glow layer
        hover_map = {hands[i].hover: HAND_COLORS[i] for i in range(2) if hands[i].hover is not None}
        for idx, k in enumerate(keys):
            p1, p2 = (k["x"], k["y"]), (k["x"] + k["w"], k["y"] + k["h"])
            col = k["color"]
            thick = 2
            if idx in hover_map:
                cv2.rectangle(fx, p1, p2, sc(hover_map[idx], 0.35), -1)
                col, thick = hover_map[idx], 4
            f = flash.get(k["label"])
            if f is not None and now - f < 0.3:
                cv2.rectangle(fx, p1, p2, sc((255, 255, 255), 1 - (now - f) / 0.3), -1)
            cv2.rectangle(fx, p1, p2, col, thick)
        cv2.rectangle(fx, (40, 20), (w - 40, bar_bottom), (255, 160, 60), 2)

        ripples[:] = [r for r in ripples if now - r[2] < 0.6]
        for rx, ry, rt, rc in ripples:
            age = now - rt
            cv2.circle(fx, (int(rx), int(ry)), int(20 + age * 500), sc(rc, 1 - age / 0.6), 3)

        for i, pts in skeletons:
            c = HAND_COLORS[i]
            ip = [(int(x), int(y)) for x, y in pts]
            for a, b in CONNECTIONS:
                cv2.line(fx, ip[a], ip[b], sc(c, 0.7), 2)
            for p in ip:
                cv2.circle(fx, p, 4, c, -1)
            tr = [(int(x), int(y)) for x, y in hands[i].trail]
            for j in range(1, len(tr)):
                cv2.line(fx, tr[j - 1], tr[j], sc(c, j / len(tr)), 4)
            tip = tr[-1]
            if hands[i].pinched:
                cv2.circle(fx, tip, 18, (255, 255, 255), -1)
            else:
                cv2.circle(fx, tip, 12, c, -1)

        small = cv2.resize(fx, (w // 3, h // 3))
        glow = cv2.resize(cv2.GaussianBlur(small, (0, 0), 4), (w, h))
        frame = cv2.add(frame, glow)
        frame = cv2.add(frame, fx)

        # ---------- text ----------
        for k in keys:
            label = k["label"]
            scale = 0.9 if k["kind"] == "char" else 0.75
            size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)[0]
            cv2.putText(frame, label, (k["x"] + (k["w"] - size[0]) // 2, k["y"] + (k["h"] + size[1]) // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 2, cv2.LINE_AA)

        cursor = "_" if int(now * 2) % 2 == 0 else " "
        lines = textwrap.wrap(typer.text + cursor, width=34, drop_whitespace=False,
                              replace_whitespace=False) or [cursor]
        for n, line in enumerate(lines[-2:]):
            cv2.putText(frame, line, (60, 68 + n * 52), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Pinch thumb+index to type  |  2 hands OK  |  c: clear  |  q: quit",
                    (44, bar_bottom + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, f"{fps:.0f} FPS", (w - 120, bar_bottom + 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1, cv2.LINE_AA)

        cv2.imshow("Air Keyboard", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("c"):
            typer.clear()

    landmarker.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
