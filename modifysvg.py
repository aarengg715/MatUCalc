import os
import json
import xml.etree.ElementTree as ET
import cairo

with open("config/accent.json", "r") as file:
    accentfile = json.load(file)

def modifySvg():
    input_folder = os.path.join(os.getcwd(), "assets")
    output_folder = os.path.join(os.getcwd(), "cache", "assets")
    files = ["aboutwindow.svg", "calc.svg", "setimage.svg", "settings.svg", "star.svg"]
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for file in files:
        with open(f"assets/{file}", "rt") as fin:
            data = fin.read()
            data = data.replace('style="fill:#000000;', f'style="fill:#FF0000;')

        with open(f"assets/{file}", "wt") as fin:
            fin.write(data)

        tree = ET.parse(f"assets/{file}")
        root = tree.getroot()

        # Extract width and height, remove 'px' if present
        width = root.attrib.get('width', '500').replace('px', '')
        height = root.attrib.get('height', '500').replace('px', '')

        try:
            width = int(width)
            height = int(height)
        except ValueError:
            width = 500
            height = 500

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        context = cairo.Context(surface)
        context.set_source_rgb(1, 1, 1)
        context.paint()

        for element in root:
            if element.tag.endswith('path'):
                path_data = element.attrib.get('d', '')
                if path_data:
                    context.new_path()
                    path_commands = path_data.split()
                    for command in path_commands:
                        if command.startswith('M'):
                            x, y = map(float, command[1:].split(','))
                            context.move_to(x, y)
                        elif command.startswith('L'):
                            x, y = map(float, command[1:].split(','))
                            context.line_to(x, y)
                    context.stroke()

        surface.write_to_png(f"cache/assets/{file.replace('.svg', '.png')}")

modifySvg()
