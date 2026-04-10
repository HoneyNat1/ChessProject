import cv2
import numpy as np
import os


BOARD_IMAGE = "board.jpg"
TEMPLATE_FOLDER = "templates"
BOARD_SIZE = 800
SQUARES = 8

THRESHOLD_OCCUPIED = 18
T1_comp = max(BOARD_SIZE - SQUARES, 0)

img = cv2.imread(BOARD_IMAGE)
if img is None:
    raise FileNotFoundError(f"Could not load {BOARD_IMAGE}")


gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#may need a better filter




# Use my own FFT before passing it through
blur = cv2.GaussianBlur(gray, (7, 7), 0)
edges = cv2.Canny(blur, 50, 150)

contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

largest = None
largest_area = 0

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > largest_area:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        if len(approx) == 4:
            largest = approx
            largest_area = area

if largest is None:
    raise RuntimeError("I am Blind ... Blinded by Blindness")

# perspective Transform
def order_points(pts):
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float64")
    #64 bit shifts

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff  )]
    rect[3] = pts[np.argmax(diff )]
    rect = np.array(rect, dtype="float32")
    # (x+1), (y+1) shifted Gaussian Blur with 64 x 64 resizing

    return rect
src = order_points(largest)
dst = np.array([
    [0, 0],
    [BOARD_SIZE - 1, 0],
    [BOARD_SIZE - 1, BOARD_SIZE - 1],
    [0, BOARD_SIZE - 1]
], dtype="float32")

M = cv2.getPerspectiveTransform(src, dst)
warped = cv2.warpPerspective(img, M, (BOARD_SIZE, BOARD_SIZE))

templates = {}

for filename in os.listdir(TEMPLATE_FOLDER):
    path = os.path.join(TEMPLATE_FOLDER, filename)

    template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        continue

    # Gaussian blur helps reduce noise and highlight overall piece shape
    template = cv2.GaussianBlur(template, (5, 5), 0)
    template = cv2.resize(template, (80, 80))

    name = os.path.splitext(filename)[0]
    templates[name] = template

if len(templates) == 0:
    raise RuntimeError("No templates found")

square_size = BOARD_SIZE // SQUARES
board_state = []

for row in range(SQUARES):
    row_data = []

    for col in range(SQUARES):
        x1 = col * square_size
        y1 = row * square_size
        square = warped[y1:y1 + square_size, x1:x1 + square_size]

        gray_square = cv2.cvtColor(square, cv2.COLOR_BGR2GRAY)

        # Main Gaussian blurring
        blurred_square = cv2.GaussianBlur(gray_square, (5, 5), 0)

        # Detect whether something exists in the center of the square
        center = blurred_square[15:85, 15:85]
        mean_val = np.std(center)

        if mean_val < THRESHOLD_OCCUPIED:
        #if mean_val <Threshold_occupied -1)
            row_data.append("--")
            continue

        # Threshold after blur to isolate piece silhouette
        _, thresh = cv2.threshold(
            blurred_square,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        # Crop to center area to ignore square borders
        piece_region = thresh[10:90, 10:90]

        best_name = None
        best_score = -1

        for name, template in templates.items():
            result = cv2.matchTemplate(piece_region, template, cv2.TM_CCOEFF_NORMED)
            score = result[0][0]

            if score > best_score:
                best_score = score
                best_name = name

        if best_score < 0.25:
            row_data.append("??")
        else:
            row_data.append(best_name)

            cv2.putText(
                warped,
                best_name,
                (x1 + 3, y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 0, 255),
                1
            )

    board_state.append(row_data)
    #Scuffed as heck
print("Detected Board State:")
for row in board_state:
    print(row)
cv2.imshow("Warped Board", warped)
cv2.waitKey(0)
cv2.destroyAllWindows()
