from PIL import Image, ImageOps, ImageDraw, ImageFont
from argparse import ArgumentParser
import exifread
import os
from urllib.request import urlopen
from tqdm import tqdm

# Target tags to extract from the image
TARGET_TAGS = ["Image Make", "Image Model", "Image Orientation", "Image DateTime", "EXIF Exposure", "EXIF FNumber", "EXIF ISOSpeedRatings", "EXIF FocalLength", "EXIF LensModel", "EXIF LensMake", "EXIF LensSpecification", "EXIF ExposureTime"]

# URL to download the font
truetype_url = 'https://github.com/google/fonts/blob/main/ofl/oswald/Oswald%5Bwght%5D.ttf?raw=true'
opened_url = urlopen(truetype_url)

# Global values
border_size = 0
is_horizontal = True

# color
primary_color = (0, 0, 0)
secondary_color = (125, 125, 125)

def extract_exif(path: str):
    """
    Parameters
    ----------
    path : str
        Path to the image file
    """
    with open(path, 'rb') as img_file:
        tags = exifread.process_file(img_file)
        
    exif_data = {}

    for tag, value in tags.items():
        if tag in TARGET_TAGS:
            tag_str = tag.split(" ")[1]
            exif_data[tag_str] = str(value)

    # for key, value in exif_data.items():
    #     print(f"{key}: {value}")
    fnumber_list = exif_data["FNumber"].split("/")
    if len(fnumber_list) == 2:
        exif_data["FNumber"] = f'{float(fnumber_list[0])/float(fnumber_list[1])}'

    return exif_data

def add_border(path: str, exif_data: dict):
    global border_size, is_horizontal

    img = Image.open(path)
    if (exif_data["Orientation"].find("90") != -1):
        img = img.rotate(90, expand=True)
        is_horizontal = False
        border_size = int(min(img.size[0], img.size[1]) / 2.5)
    else:
        border_size = int(min(img.size[0], img.size[1]) / 5)

    border = (0,0,0,border_size)

    img_with_border = ImageOps.expand(img, border, fill='white')

    return img_with_border

def add_text(img: Image, exif_data: dict):
    """
    Add text on the image
    """
    global border_size

    draw = ImageDraw.Draw(img)

    text_border_ratio = 0.025 if is_horizontal else 0.02

    header_size = border_size // 3 if is_horizontal else border_size // 4
    header_font = ImageFont.truetype(urlopen(truetype_url), size=header_size)

    subheader_size = int(header_size * 0.4)
    subheader_font = ImageFont.truetype(urlopen(truetype_url), size=subheader_size)

    normal_size = int(header_size * 0.3)
    normal_font = ImageFont.truetype(urlopen(truetype_url), size=normal_size)

    """
        For "Make"
    """
    # Calculate the position to center the text
    x = img.size[0] * (text_border_ratio) if is_horizontal else img.size[0] // 2
    y = img.size[1] - (border_size // 2) if is_horizontal else img.size[1] * (1 + text_border_ratio) - border_size
    anchor = "lm" if is_horizontal else "mt"
    align = "left" if is_horizontal else "center"

    draw.text((x, y), exif_data["Make"], font=header_font, fill=primary_color, anchor=anchor, align=align)
    make_bbox = draw.textbbox((x, y), exif_data["Make"], font=header_font, anchor=anchor, align=align)

    """
        For "Model"
    """
    x = make_bbox[2] + 100 if is_horizontal else img.size[0] // 2
    y = img.size[1] - (border_size // 2) - 25 if is_horizontal else make_bbox[3] + img.size[1] * text_border_ratio
    anchor = "lb" if is_horizontal else "mt"
    align = "left" if is_horizontal else "center"

    text = exif_data["Model"] if is_horizontal else f'{exif_data["Model"]}  |  {exif_data["LensModel"]}'

    draw.text((x, y), text, font=subheader_font, fill=secondary_color, anchor=anchor, align=align)
    model_bbox = draw.textbbox((x, y), text, font=subheader_font, anchor=anchor, align=align)

    """
        For "LensModel"
    """
    if is_horizontal:
        x = make_bbox[2] + 100
        y = img.size[1] - (border_size // 2) + 25
        draw.text((x, y), exif_data["LensModel"], font=subheader_font, fill=secondary_color, anchor="lt", align="left")
    else:
        pass

    """
        Add horizontal line
    """
    if is_horizontal:
        pass
    else:
        y_cord = model_bbox[3] + img.size[1] * text_border_ratio
        draw.line([(model_bbox[0], y_cord), (model_bbox[2], y_cord)], fill=primary_color, width=2)

    """
        For "DateTime"
    """
    x = img.size[0] * (1 - text_border_ratio) if is_horizontal else img.size[0] // 2
    y = img.size[1] - (border_size // 2) + 25 if is_horizontal else img.size[1] * (1 - text_border_ratio)
    anchor = "rt" if is_horizontal else "mb"
    align = "right" if is_horizontal else "center"

    draw.text((x, y), exif_data["DateTime"], font=normal_font, fill=secondary_color, anchor=anchor, align=align)
    date_bbox = draw.textbbox((x, y), exif_data["DateTime"], font=normal_font, anchor=anchor, align=align)
    
    """
        For "FocalLength", "ExposureTime","" "Exposure", "ISO"
    """
    x = img.size[0] * (1 - text_border_ratio) if is_horizontal else img.size[0] // 2
    y = img.size[1] - (border_size // 2) - 25 if is_horizontal else date_bbox[1] - img.size[1] * text_border_ratio
    anchor = "rb" if is_horizontal else "mb"
    align = "right" if is_horizontal else "center"

    text = f'{exif_data["FocalLength"]}mm  {exif_data["ExposureTime"]}s  f/{float(exif_data["FNumber"]):.1f}  ISO{exif_data["ISOSpeedRatings"]}'
    draw.text((x, y), text, font=subheader_font, fill=primary_color, anchor=anchor, align=align)

    return img

def main_process(path: str, output_folder: str):
    global border_size, is_horizontal
    is_horizontal = True
    border_size = 0
    if os.path.basename(path).endswith('.jpg') or os.path.basename(path).endswith('.jpeg') or os.path.basename(path).endswith('.png') or os.path.basename(path).endswith('.JPG'):
        exif = extract_exif(path)
        added_border = add_border(path, exif)
        result = add_text(added_border, exif)
        result.save(output_folder + '/' + 'marked_' + os.path.basename(path))
    else: 
        raise ValueError(f'Invalid file format: {os.path.basename(path)}')

def main():
    parser = ArgumentParser()
    parser.add_argument('--path', '-p', type=str, required=True, help='Path to the image', default='./input')
    parser.add_argument('--output_folder', '-of', type=str, help='Path to the output image', default='./output')
    args = parser.parse_args()

    output_folder = args.output_folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    else:
        if not os.path.isdir(output_folder):
            raise ValueError(f'Invalid output folder: {output_folder}')
        for files in os.listdir(output_folder):
            os.remove(os.path.join(output_folder, files))

    if not os.path.exists(args.path):
        raise FileNotFoundError(f'File not found: {args.path}')
    elif os.path.isdir(args.path):
        for files in tqdm(os.listdir(args.path)):
            main_process(os.path.join(args.path, files), args.output_folder)
    else:
        main_process(args.path, args.output_folder)

if __name__ == '__main__':
    main()