from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from PIL import Image, ImageDraw, ImageFont

UPLOAD_FOLDER = 'uploads'
FONT_FOLDER = 'fonts'
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # limit to 16MB


def resize_image(image, base_width=None, base_height=None):
    original_width, original_height = image.size
    if base_width:
        ratio = (base_width / float(original_width))
        new_height = int((float(original_height) * float(ratio)))
        resized_image = image.resize((base_width, new_height), Image.LANCZOS)  # Updated filter here
    elif base_height:
        ratio = (base_height / float(original_height))
        new_width = int((float(original_width) * float(ratio)))
        resized_image = image.resize((new_width, base_height), Image.LANCZOS)  # Updated filter here
    else:
        resized_image = image  # If no dimensions are provided, return the original
    return resized_image



@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image = request.files['image']
    filename = secure_filename(image.filename)
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(image_path)

    try:
        with Image.open(image_path) as img:
            resized_img = resize_image(img, base_width=800)
            draw = ImageDraw.Draw(resized_img)
            default_x = resized_img.width // 2
            default_y = resized_img.height // 2

            texts = request.form.getlist('texts')
            colors = request.form.getlist('colors')
            fonts = request.form.getlist('fonts')
            positions_x = request.form.getlist('positions_x') or [default_x] * len(texts)
            positions_y = request.form.getlist('positions_y') or [default_y] * len(texts)

            for i, text in enumerate(texts):
                font_path = os.path.join(FONT_FOLDER, fonts[i] + '.ttf')
                font = ImageFont.truetype(font_path, 36)
                color_hex = colors[i]
                color_rgb = tuple(int(color_hex[j:j+2], 16) for j in (1, 3, 5))
                pos_x = int(positions_x[i]) if positions_x[i] else default_x
                pos_y = int(positions_y[i]) if positions_y[i] else default_y
                text_position = (pos_x, pos_y)
                
                draw.text(text_position, text, font=font, fill=color_rgb)

            modified_img_path = os.path.join(UPLOAD_FOLDER, 'modified_' + filename)
            resized_img.save(modified_img_path)

        os.remove(image_path)
        return jsonify({'message': 'Image processed successfully', 'modified_image': modified_img_path}), 200
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
