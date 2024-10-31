from common_util import *
import json
import glob
import opencc
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools import ttLib
from fontTools.ttLib import TTFont, newTable
from fontTools.subset import Subsetter, Options
import shutil

def get_vhea_table_from_ttf(ttf_file_path):
    """
    从给定的 TTF 文件中获取 vhea 表信息并以 XML 格式打印。

    参数:
    ttf_file_path: str
        TTF 文件的路径。

    返回:
    vhea_table: table_vhea 或 None
        字体文件中的 vhea 表对象，如果不存在则返回 None。
    """
    # 加载字体文件
    font = TTFont(ttf_file_path)

    # 检查字体文件是否包含 vhea 表
    if 'vhea' in font:
        vhea_table = font['vhea']
        return vhea_table
    else:
        print(f"{ttf_file_path} 字体文件中没有 vhea 表。")
        return None

def get_characters_from_json(json_file_path):
    """Extracts all unique characters from the JSON file."""
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    characters = set()
    # Traverse the JSON structure to collect all characters
    def extract_chars(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                extract_chars(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_chars(item)
        elif isinstance(obj, str):
            characters.update(obj)
    
    extract_chars(data)
    return characters

def process_st_phrases(filter_string):
    # Step 1: Read the full.js file
    with open('full.js', 'r', encoding='utf-8') as file:
        content = file.read()

    # Step 2: Extract the content of STPhrases
    start = content.find('STPhrases = "') + len('STPhrases = "')
    end = content.find('";', start)
    st_phrases_content = content[start:end]

    # Step 3: Delimit by '|'
    phrases_list = st_phrases_content.split('|')

    # Step 4: For each item, delimit by whitespace and list the second element
    # only when the first character is in the filter_string
    second_elements = []
    for phrase in phrases_list:
        parts = phrase.split(" ")
        if len(parts) > 1 and parts[0] in filter_string:
            print(f"Matching phrase: {phrase}")
            second_elements.append(parts[1])

    # Combine all second elements into one string
    combined_string = ''.join(second_elements)

    # Get all unique characters in the string and return as a string
    unique_chars_string = ''.join(set(combined_string))

    return unique_chars_string

def get_file_content(file_path):
    """Gets the content of a file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

def generate_minimized_fonts(fonts_dir, output_dir, text_source, test_mode=False):
    """Generates minimized WOFF fonts for each text source, including traditional Chinese characters."""
    ensure_directory(output_dir)
    cctw = opencc.OpenCC('s2tw')  # Initialize OpenCC for simplified to traditional conversion

    # Determine if the text_source is a directory, a list of files, or a single file
    if isinstance(text_source, list):
        text_files = [f for f in text_source if f.endswith('.json')]
    elif os.path.isdir(text_source):
        text_files = [os.path.join(text_source, f) for f in os.listdir(text_source) if f.endswith('.json')]
    else:
        text_files = [text_source]

    generated_woff_files = []

    for text_file in text_files:
        simplified_characters = get_characters_from_json(text_file)
        simplified_text = get_file_content(text_file)

        # Convert characters to traditional Chinese
        traditional_characters_tw = cctw.convert(''.join(simplified_characters))

        # Extract special characters from the text
        special_characters_tw = process_st_phrases(simplified_text)

        # Output simplified and traditional characters to file for debugging
        debug_output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(text_file))[0]}_chars.txt")
        with open(debug_output_path, 'w', encoding='utf-8') as debug_file:
            debug_file.write("Simplified Characters:\n")
            debug_file.write(''.join(simplified_characters) + "\n\n")
            debug_file.write("Traditional Characters TW:\n")
            debug_file.write(traditional_characters_tw + "\n")
            debug_file.write("Special Characters TW:\n")
            debug_file.write(special_characters_tw + "\n")
        print(f"Simplified and traditional characters written to {debug_output_path}")
        
        # This section is responsible for generating minimized fonts by subsetting the original font files
        # based on the characters extracted from the text files. It includes both simplified and traditional
        # Chinese characters, as well as any special characters identified in the text.
        font_files = glob.glob(os.path.join(fonts_dir, '*.ttf'))

        if test_mode:
            font_files = font_files[:2]  # Limit to three fonts if test_mode is true

        for font_file in font_files:
            font = ttLib.TTFont(font_file)

            options = Options()
            options.layout_features = ['liga', 'clig', 'ccmp']  # 保留特定 OpenType 特性
            
            vhea_table = get_vhea_table_from_ttf(font_file)
            if vhea_table:
                # 添加 vhea 表到字体中
                font['vhea'] = vhea_table

            subsetter = Subsetter(options=options)
            # Populate with both simplified, traditional and special characters
            all_text = ''.join(simplified_characters) + traditional_characters_tw + special_characters_tw
            # Remove duplicate characters
            all_text = ''.join(dict.fromkeys(all_text))
            #print(all_text)

            subsetter.populate(text=all_text)
            subsetter.subset(font)
            
            # Generate the output WOFF file path
            font_name = os.path.splitext(os.path.basename(font_file))[0]
            output_font_path = os.path.join(output_dir, f"{font_name}_{os.path.splitext(os.path.basename(text_file))[0]}.woff")
            
            # Save the subset font as WOFF
            font.flavor = 'woff'
            try:
                font.save(output_font_path)
                generated_woff_files.append(output_font_path)
                print(f"Generated minimized font: {output_font_path}")
            except Exception as e:
                print(f"Failed to generate minimized font for {font_file}: {e}")
            finally:
                font.close()

    # Create an HTML page to display all text in text source with all output WOFF fonts
    html_output_path = os.path.join(output_dir, "index.html")
    with open(html_output_path, 'w', encoding='utf-8') as html_file:
        html_file.write("<html><head><title>Font Preview</title></head><body>\n")
        html_file.write("<h1>Font Preview</h1>\n")
        
        # Write CSS to include all generated WOFF fonts
        for woff_file in generated_woff_files:
            font_name = os.path.splitext(os.path.basename(woff_file))[0]
            html_file.write(f"<style>@font-face {{ font-family: '{font_name}'; src: url('{woff_file}'); }}</style>\n")
        
        # Write HTML to display all text in text source with all fonts
        for woff_file in generated_woff_files:
            font_name = os.path.splitext(os.path.basename(woff_file))[0]
            html_file.write(f"<h2>{font_name}</h2>\n")
            html_file.write(f"<p style='font-family: {font_name};'>{simplified_text}</p>\n")
        
        html_file.write("</body></html>\n")
    print(f"HTML preview generated at {html_output_path}")

def sync_woff_files(source_dir, destination_dir):
    """Copies all WOFF files from the source directory to the destination directory, overwriting if they already exist."""
    # Ensure the destination directory exists
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
        print(f"Created directory: {destination_dir}")

    # Find all WOFF files in the source directory
    woff_files = glob.glob(os.path.join(source_dir, '*.woff'))

    for woff_file in woff_files:
        try:
            shutil.copy(woff_file, destination_dir) 
            print(f"Copied {woff_file} to {destination_dir}")
        except Exception as e:
            print(f"Failed to copy {woff_file} to {destination_dir}: {e}")

# Run this to generate minimized fonts for website texts
generate_minimized_fonts("fonts", "output\\website_fonts", "website_text.json")
sync_woff_files("output\\website_fonts", "D:\\Projects\\Cursor\\qldazangjingweb\\public\\website_fonts")

# Run this to generate minimized fonts for all books
#generate_minimized_fonts("fonts", "output\\book_fonts", "output\\books", test_mode=False)
#sync_woff_files("output\\book_fonts", "D:\\Projects\\Cursor\\qldazangjingweb\\public\\data\\book_fonts")
