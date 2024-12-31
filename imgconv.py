from PIL import Image
import os
import shutil

def convertImage():
    
    def convert_to_jpg(image_path, output_path):
        image = Image.open(image_path)

        rgb_image = image.convert('RGB')
        rgb_image.save(output_path, 'JPEG')

    def is_jpg(image_path):
        return image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg')

    def convert_images_in_folder(input_folder_path, output_folder_path, jpg_folder_path):
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)
        if not os.path.exists(jpg_folder_path):
            os.makedirs(jpg_folder_path)

        if not os.path.exists(input_folder_path):
            print(f"Input folder '{input_folder_path}' does not exist.")
            return

        for filename in os.listdir(input_folder_path):
            input_image_path = os.path.join(input_folder_path, filename)
            
            if os.path.isdir(input_image_path):
                continue  

            base_filename = os.path.splitext(filename)[0]
            if not is_jpg(input_image_path):
                output_image_path = os.path.join(output_folder_path, base_filename + '.jpg')
                try:
                    convert_to_jpg(input_image_path, output_image_path)
                    print(f"Converted {filename} to JPG and saved as {output_image_path}")
                except PermissionError as e:
                    print(f"Permission error: {e}")
            else:
                new_jpg_path = os.path.join(jpg_folder_path, filename)
                try:
                    shutil.move(input_image_path, new_jpg_path)
                    print(f"Moved {filename} to {new_jpg_path}")
                except PermissionError as e:
                    print(f"Permission error: {e}")

    input_folder_path = 'cache/imgconv'
    output_folder_path = 'fetch_img'
    jpg_folder_path = 'fetch_img'
    os.rmdir('fetch_img')
    os.mkdir('fetch_img')
    convert_images_in_folder(input_folder_path, output_folder_path, jpg_folder_path)
