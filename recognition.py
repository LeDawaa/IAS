import cv2
import string
import win32gui
import numpy as np
import tkinter as tk


from tkinter import *
from PIL import ImageOps, ImageGrab

from keras.models import load_model

# Load the best model from the saved file
model = load_model("best_model.h5")

# Function to predict the letter from the image
def predict_digit(img):
    # Resize image to 28x28 pixels
    img = img.resize((28,28))
    # Convert RGB to grayscale
    img = img.convert('L')
    img = np.array(img)
    # Reshape to support our model input and normalize
    img = img.reshape(1,28,28,1)
    img = img/255.0
    # Predict the class
    res = model.predict([img])[0]
    return string.ascii_uppercase[np.argmax(res)], max(res)

# Define the main application class
class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.x = self.y = 0
        # Creating elements
        self.canvas = tk.Canvas(self, width=900, height=300, bg = "white", cursor="cross")
        self.label = tk.Label(self, text="Thinking..", font=("Helvetica", 32))
        self.classify_btn = tk.Button(self, text = "Recognise", command = self.classify_handwriting)
        self.button_clear = tk.Button(self, text = "Clear", command = self.clear_all)
        # Grid structure
        self.canvas.grid(row=0, column=0, pady=2, sticky=W, )
        self.label.grid(row=0, column=1,pady=2, padx=2)
        self.classify_btn.grid(row=1, column=1, pady=2, padx=2)
        self.button_clear.grid(row=1, column=0, pady=2)
        # Bind canvas events
        self.canvas.bind("<B1-Motion>", self.draw_lines)

    # Function to clear the canvas
    def clear_all(self):
        self.canvas.delete("all")
        self.label.configure(text="Thinking..")

        # Function to group connected components by line
    def group_components_by_line(self, stats, y_tolerance=20):
        # Sort the stats array (excluding the background component at index 0) by the top-left y-coordinate (stat[1]) and then by the top-left x-coordinate (stat[0])
        stats_sorted = sorted(stats[1:], key=lambda stat: (stat[1], stat[0]))
        
        # Initialize the list of grouped stats and the current line
        grouped_stats = []
        current_line = []

        # Iterate through the sorted stats
        for stat in stats_sorted:
            # If the current line is empty, add the first stat to the line
            if not current_line:
                current_line.append(stat)
            # If the vertical distance between the current stat and the previous stat is less than or equal to y_tolerance,
            # it means they belong to the same line, so add the current stat to the current line
            elif abs(stat[1] - current_line[-1][1]) <= y_tolerance:
                current_line.append(stat)
            # If the vertical distance is greater than y_tolerance, it means we have reached a new line
            else:
                # Sort the current line by the top-left x-coordinate (s[0]) and append it to the grouped_stats list
                grouped_stats.append(sorted(current_line, key=lambda s: s[0]))
                # Reset the current line to start a new line with the current stat
                current_line = [stat]

        # If there are any remaining stats in the current line, sort them by the top-left x-coordinate (s[0]) and append them to the grouped_stats list
        if current_line:
            grouped_stats.append(sorted(current_line, key=lambda s: s[0]))

        return grouped_stats

    # Function to classify the handwriting on the canvas
    def classify_handwriting(self):
        HWND = self.canvas.winfo_id() # Get the handle of the canvas
        rect = win32gui.GetWindowRect(HWND) # Get the coordinate of the canvas
        im = ImageGrab.grab(rect)

        # Preprocess the image
        gray = cv2.cvtColor(np.array(im), cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        _, _, stats, _ = cv2.connectedComponentsWithStats(thresh)

        # Group connected components by line
        lines = self.group_components_by_line(stats)

        # Iterate over each line and perform character recognition
        margin_size = 50
        border_color = (255, 255, 255)
        predictions = []

        for line in lines:
            line_predictions = []
            for i in range(len(line)):
                x, y, w, h, _ = line[i]
                # Add a border around the cropped image to avoid cutting off the edges of the character
                image_with_border = ImageOps.expand(im.crop((x, y, x+w, y+h)), border=(margin_size, margin_size, margin_size, margin_size), fill=border_color)
                # Invert the image and resize it to 28x28 pixels
                image_with_border = ImageOps.invert(image_with_border).resize((28,28))
                # Predict the character and its probability
                digit, acc = predict_digit(image_with_border)
                line_predictions.append((digit, acc))
            predictions.append(line_predictions)

        # Display the predictions in a formatted text
        text, word = '', ''
        for prediction in predictions:
            for pred in prediction:
                text += f"Letter: {pred[0]}, Accuracy: {pred[1]:.3f} \n"
                word += pred[0]
            text += '\n'
            word += '\n'
        text += f"Word:\n{word}"
                
        self.label.configure(text=text)

    def draw_lines(self, event):
        r = 8
        self.x = event.x
        self.y = event.y
        self.canvas.create_oval(self.x - r, self.y - r, self.x + r, self.y + r, fill='black')

app = App()
mainloop()