import os
import glob
from common_util import *

def generate_test_html_page(output_dir, json_files):
    """Generates a test HTML page for each JSON file using the minimized fonts."""
    html_output_dir = os.path.join(output_dir, 'test_html')
    ensure_directory(html_output_dir)

    for json_file in json_files:
        json_file_path = os.path.join('output/books', json_file)
        
        # Read the original JSON file content
        with open(json_file_path, 'r', encoding='utf-8') as file:
            original_json_content = file.read()

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Page for {json_file}</title>
            <style>
        """

        # Get the list of font files
        font_files = glob.glob(os.path.join(output_dir, 'book_fonts', f'*_{os.path.splitext(json_file)[0]}.woff'))

        # Add @font-face rules for each minimized font
        for font_file in font_files:
            font_name = os.path.splitext(os.path.basename(font_file))[0]
            html_content += f"""
                @font-face {{
                    font-family: '{font_name}';
                    src: url('../book_fonts/{os.path.basename(font_file)}') format('woff');
                }}
            """

        html_content += """
            </style>
            <script src="https://cdn.jsdelivr.net/npm/opencc-js@1.0.5/dist/umd/full.min.js"></script>
            <script>
                function convertToSimplified() {
                    var converter = OpenCC.Converter({ from: 'tw', to: 'cn' });
                    document.querySelectorAll('.convertible').forEach(function(element) {
                        element.textContent = converter(element.textContent);
                    });
                }

                function convertToTraditional() {
                    var converter = OpenCC.Converter({ from: 'cn', to: 'tw' });
                    document.querySelectorAll('.convertible').forEach(function(element) {
                        element.textContent = converter(element.textContent);
                    });
                }

                function changeFont() {
                    var selectedFont = document.getElementById('fontSelector').value;
                    document.getElementById('textParagraph').style.fontFamily = selectedFont;
                }
            </script>
        </head>
        <body>
            <h1>Test Page for {json_file}</h1>
            <button onclick="convertToSimplified()">Convert to Simplified</button>
            <button onclick="convertToTraditional()">Convert to Traditional</button>
            <select id="fontSelector" onchange="changeFont()">
        """

        # Add options for each font in the dropdown, setting the first one as selected
        for index, font_file in enumerate(font_files):
            font_name = os.path.splitext(os.path.basename(font_file))[0]
            selected = "selected" if index == 0 else ""
            html_content += f"""
                <option value='{font_name}' {selected}>{font_name}</option>
            """

        html_content += f"""
            </select>
            <p id="textParagraph" class="convertible" style="font-family: '{font_files[0] if font_files else ''}'; white-space: pre-wrap;">{original_json_content}</p>
        </body>
        </html>
        """

        # Save the HTML content to a file
        html_file_path = os.path.join(html_output_dir, f"{os.path.splitext(json_file)[0]}.html")
        with open(html_file_path, 'w', encoding='utf-8') as html_file:
            html_file.write(html_content)
        print(f"Generated test HTML page: {html_file_path}")
