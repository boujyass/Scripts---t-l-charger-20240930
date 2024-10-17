import sys
import numpy as np
import time
import math
import socket
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Constants for the 3D tracking
FOCAL_LENGTH = 590  # Focal length for the camera in pixels
REAL_IPD = 6.3  # Interpupillary distance in cm (average human IPD)

# Set the default interpupillary distance from user input or default
user_ipd = REAL_IPD
if len(sys.argv) >= 2:
    user_ipd = float(sys.argv[1])

print(f"Tracking initialized with an interpupillary distance of {user_ipd} cm")

# UDP configuration
UDP_IP = "localhost"  # IP address to send the UDP packets
UDP_PORT = 6006  # Port number to send the UDP packets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket

# Capture frames from a webcam
cap = cv2.VideoCapture(0)  # Use the default camera (index 0)
if not cap.isOpened():
    print("Error: Could not open video stream.")
    sys.exit()

# Get image size
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Width of the video frame
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Height of the video frame
print(f"Video size: {frame_width} x {frame_height}")

# Class for storing tracking results
class TrackingResults:
    tracking_results = None

    def get_result(self, result: vision.FaceDetectorResult, output_image: mp.Image, timestamp_ms: int):
        # Callback function to store the face detection results
        self.tracking_results = result

res = TrackingResults()  # Create an instance of TrackingResults

# Initialize the face detector
base_options = python.BaseOptions(model_asset_path='blaze_face_short_range.tflite')
options = vision.FaceDetectorOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.LIVE_STREAM,
    result_callback=res.get_result  # Set the callback function to handle detection results
)
detector = vision.FaceDetector.create_from_options(options)  # Create the face detector

# Convert normalized coordinates to pixel coordinates
def _normalized_to_pixel_coordinates(normalized_x: float, normalized_y: float, image_width: int, image_height: int):
    # Convert normalized coordinates (0 to 1) to pixel coordinates
    x_px = min(int(normalized_x * image_width), image_width - 1)
    y_px = min(int(normalized_y * image_height), image_height - 1)
    return x_px, y_px

#### Visualization functions ####

MARGIN = 10  # pixels
ROW_SIZE = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 2
TEXT_COLOR = (255, 0, 0)  # Red



def visualize(
    image,
    detection_result
) -> np.ndarray:
    """Draws bounding boxes and keypoints on the input image and returns it."""
    annotated_image = image.copy()
    height, width, _ = image.shape

    if detection_result is None or not detection_result.detections:
        # No detections to visualize; return the original image
        return annotated_image

    for detection in detection_result.detections:
        # Draw bounding box around the detected face
        bbox = detection.bounding_box
        start_point = bbox.origin_x, bbox.origin_y
        end_point = bbox.origin_x + bbox.width, bbox.origin_y + bbox.height
        cv2.rectangle(annotated_image, start_point, end_point, TEXT_COLOR, 3)

        # Draw only the keypoints corresponding to the eyes
        keypoints = detection.keypoints
        if len(keypoints) >= 2:
            # Keypoints[0]: Right eye
            # Keypoints[1]: Left eye
            right_eye = keypoints[0]
            left_eye = keypoints[1]

            right_eye_px = _normalized_to_pixel_coordinates(right_eye.x, right_eye.y, width, height)
            left_eye_px = _normalized_to_pixel_coordinates(left_eye.x, left_eye.y, width, height)

            if right_eye_px and left_eye_px:
                # Draw the eyes
                eye_color = (0, 255, 0)  # Green color for eyes
                thickness = 2
                radius = 2
                cv2.circle(annotated_image, right_eye_px, radius, eye_color, thickness)
                cv2.circle(annotated_image, left_eye_px, radius, eye_color, thickness)

                # Draw the center of the eyes with a different color
                center_eye_px = (
                    int((right_eye_px[0] + left_eye_px[0]) / 2),
                    int((right_eye_px[1] + left_eye_px[1]) / 2)
                )
                center_color = (255, 0, 0)  # Blue color for center
                cv2.circle(annotated_image, center_eye_px, radius, center_color, thickness)

        # Draw label and score
        category = detection.categories[0]
        category_name = category.category_name
        category_name = '' if category_name is None else category_name
        probability = round(category.score, 2)
        result_text = category_name + ' (' + str(probability) + ')'
        text_location = (MARGIN + bbox.origin_x,
                         MARGIN + ROW_SIZE + bbox.origin_y)
        cv2.putText(annotated_image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                    FONT_SIZE, TEXT_COLOR, FONT_THICKNESS)

    return annotated_image


# Compute the 3D position from the eye positions and interpupillary distance
def compute3DPos(ibe_x, ibe_y, ipd_pixels):
    z = (user_ipd * FOCAL_LENGTH) / ipd_pixels  # Distance from the camera
    x = (ibe_x - frame_width / 2) * z / FOCAL_LENGTH  # X coordinate in cm
    y = (ibe_y - frame_height / 2) * z / FOCAL_LENGTH  # Y coordinate in cm
    return x, y, z


# Helper function to send UDP commands
def send_udp_command(command):
    # Send a command via UDP
    print(f"Sending command: {command}")
    sock.sendto(command.encode(), (UDP_IP, UDP_PORT))




# Main tracking function
def runtracking():
    print("\nTracking started !!! Hit ESC key to quit...")

    # Variables to track the previous head state
    previous_left = False
    previous_right = False
    previous_accelerate = False
    previous_brake = False

    while True:
        time.sleep(0.05)  # Sleep to reduce CPU usage
        ret, img_bgr = cap.read()  # Capture a frame from the camera
        if not ret:
            print("Failed to capture frame from camera.")
            break
        
        img_bgr=cv2.flip(img_bgr,1)
        
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)  # Convert the frame to RGB
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)  # Convert to MediaPipe image format
        detector.detect_async(mp_image, int(time.time() * 1000))  # Perform asynchronous face detection

        if res.tracking_results and res.tracking_results.detections:
            # Find the biggest face in the frame
            biggest_face = max(res.tracking_results.detections, key=lambda d: d.bounding_box.width * d.bounding_box.height)
            right_eye = biggest_face.keypoints[0]  # Get right eye keypoint
            left_eye = biggest_face.keypoints[1]  # Get left eye keypoint

            # Convert normalized eye coordinates to pixel coordinates
            right_eye_px = _normalized_to_pixel_coordinates(right_eye.x, right_eye.y, frame_width, frame_height)
            left_eye_px = _normalized_to_pixel_coordinates(left_eye.x, left_eye.y, frame_width, frame_height)

            if right_eye_px and left_eye_px:
                # Calculate the average position between the eyes
                ibe_x = (right_eye_px[0] + left_eye_px[0]) / 2
                ibe_y = (right_eye_px[1] + left_eye_px[1]) / 2
                # Calculate the interpupillary distance in pixels
                ipd_pixels = math.hypot(right_eye_px[0] - left_eye_px[0], right_eye_px[1] - left_eye_px[1])

                if ipd_pixels != 0:
                    # Compute the 3D position of the user's head
                    pos_x, pos_y, pos_z = compute3DPos(ibe_x, ibe_y, ipd_pixels)
                    print(f"3D position: {pos_x:.2f} - {pos_y:.2f} - {pos_z:.2f}")

                    # Head movements mapped to game controls
                    if pos_x > 2:  # Turn right
                        if not previous_right:
                            send_udp_command('P_RIGHT')  # Press right
                            previous_right = True
                        if previous_left:  # Release left if previously pressed
                            send_udp_command('R_LEFT')
                            previous_left = False
                    elif pos_x < -2:  # Turn left
                        if not previous_left:
                            send_udp_command('P_LEFT')  # Press left
                            previous_left = True
                        if previous_right:  # Release right if previously pressed
                            send_udp_command('R_RIGHT')
                            previous_right = False
                    else:  # Head is centered, release both left and right
                        if previous_left:
                            send_udp_command('R_LEFT')
                            previous_left = False
                        if previous_right:
                            send_udp_command('R_RIGHT')
                            previous_right = False

                    if pos_z < 30:  # Accelerate (close to the camera)
                        if not previous_accelerate:
                            send_udp_command('P_ACCELERATE')
                            previous_accelerate = True
                    elif pos_z > 40:  # Brake (far from the camera)
                        if not previous_brake:
                            send_udp_command('P_BRAKE')
                            previous_brake = True
                        if previous_accelerate:  # Release accelerate
                            send_udp_command('R_ACCELERATE')
                            previous_accelerate = False
                    else:  # Neither brake nor accelerate
                        if previous_brake:
                            send_udp_command('R_BRAKE')
                            previous_brake = False
                        if previous_accelerate:
                            send_udp_command('R_ACCELERATE')
                            previous_accelerate = False
                else:
                    print("Invalid interpupillary distance.")
            else:
                print("Could not detect eye positions.")
        else:
            print("No face detected.")

        # Display the image with or without annotations
        annotated_image = mp_image.numpy_view()
        annotated_image = visualize(annotated_image, res.tracking_results)
        bgr_annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
        cv2.imshow('img', bgr_annotated_image)

        # Wait for Esc key to stop
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break

    cap.release()  # Release the camera
    cv2.destroyAllWindows()  # Close all OpenCV windows

# Run the tracking
runtracking()
