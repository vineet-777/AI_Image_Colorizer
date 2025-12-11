# Image Colorization Web App

A Flask-based web application that uses deep learning to automatically colorize black and white images.

## About This Project

**VTU 5th Semester Mini Project**

### Project Overview
This project demonstrates **"Image Colour Restoration using Deep Learning (CNN)"** and provides a user-friendly dashboard to upload, process, and view restored images.  
The objective is to restore colors in faded or grayscale images using a trained Convolutional Neural Network model, showcasing the practical application of deep learning techniques.

## Features

- Upload black & white images
- Automatic colorization using neural networks
- User authentication and session management
- Image history and management
- SQLite database for data persistence

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone or download this repository

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Initialize the database:
```bash
python init_db.py
```

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

3. Create an account and start colorizing images!

## Project Structure

```
project/
│
├── app.py                  # Main Flask application
├── database.py             # Database operations
├── init_db.py             # Database initialization
├── requirements.txt        # Python dependencies
│
├── models/                 # Colorization neural network models
│   ├── colorization_release_v2.caffemodel
│   ├── models_colorization_deploy_v2.prototxt
│   └── pts_in_hull.npy
│
├── static/                 # Static files (CSS, JS, images)
│   └── uploads/           # User uploaded images
│
└── templates/             # HTML templates
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    └── about.html
```

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Database**: SQLite
- **ML Model**: OpenCV DNN with pre-trained colorization model
- **Frontend**: HTML, CSS, JavaScript

## How It Works

The application uses a deep learning model trained on millions of images to predict color information for grayscale images. The model uses the LAB color space to separate luminance (L) from color (AB) channels, making colorization more accurate.

## Security Note

- Passwords are hashed using SHA-256
- Session management for secure authentication
- File upload validation and sanitization

## License

This project is for educational purposes.

## Credits

Colorization model based on research by Richard Zhang, Phillip Isola, and Alexei A. Efros.
