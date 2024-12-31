from PIL import Image
import json
from materialyoucolor.quantize import QuantizeCelebi
from materialyoucolor.score.score import Score

def int_to_hex(color_int):
    rgb_color = color_int & 0xFFFFFF
    return f'#{rgb_color:06X}'

def fetchColor(path, setting, writeToJson):
    image = Image.open(path)
    pixel_len = image.width * image.height
    image_data = image.getdata()

    quality = 1
    pixel_array = [image_data[_] for _ in range(0, pixel_len, quality)]

    result = QuantizeCelebi(pixel_array, 512)

    hex_result = {int_to_hex(color): count for color, count in result.items()}

    hex_scored = Score.score(result)
    
    hex_value_max = max(hex_result, key=hex_result.get)

    with open("config/accent.json", 'r') as file:
            accent = json.load(file)

    accent['accent_color_fetched'] = hex_value_max

    with open("config/accent.json", 'w') as file:
        json.dump(accent, file, indent=4)


    return hex_value_max
        