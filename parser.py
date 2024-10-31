from bs4 import BeautifulSoup
import re
import glob
import os
import json
import opencc
from html_util import generate_test_html_page
from font_util import *

def extract_id_from_href(href):
    """Extracts the id from the href by removing the path and file extension."""
    return os.path.splitext(os.path.basename(href))[0]

def extract_bu_links(file_path):
    """Extracts links with href starting with a number from the specified HTML file."""
    # Compile regex patterns
    href_pattern = re.compile(r'^../htmljw/\d.*\.htm$')
    title_pattern = re.compile(r'\[\s*(.*?)\s*\]\s*(.*)')

    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Find all <a> tags with href matching the pattern
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href_pattern.match(href):
            # Extract sub-information from within the <a> tag
            title_tag = a_tag.find('h4')
            title_full = title_tag.get_text(strip=True) if title_tag else ''

            # Extract bu and title from the full title
            match = title_pattern.match(title_full)
            if match:
                bu = match.group(1)
                title = match.group(2)
            else:
                bu = ''
                title = title_full

            dleft_tag = a_tag.find('div', class_='dleft')
            if dleft_tag:
                author_volume_text = dleft_tag.get_text(strip=True)
                # Assuming the format "Author . Volume"
                parts = author_volume_text.split('.')
                author = parts[0].strip() if len(parts) > 0 else ''
                volume = parts[1].strip() if len(parts) > 1 else ''
            else:
                author = ''
                volume = ''

            # Extract name from the <a> tag's text or a specific child element
            # Here, we assume the name is within the <h4> tag. Adjust if necessary.
            name = title_full if title_full else a_tag.get_text(strip=True)

            links.append({
                'id': extract_id_from_href(href),
                'name': name,          # Added name field
                'href': href,          # Included href for further processing
                'bu': bu,
                'title': title,
                'author': author,
                'volume': volume
            })

    return links

def parse_juan_content(href, base_directory):
    """Parses the HTML file pointed to by the href and extracts juan, chapter, and navigation information."""
    # Resolve the href to an absolute file path
    target_path = os.path.normpath(os.path.join(base_directory, href))

    if not os.path.isfile(target_path):
        print(f"Warning: File not found for href '{href}' at path '{target_path}'.")
        return {}

    try:
        with open(target_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

        juans = []
        jwzw_div = soup.find('div', class_='jwzw')
        if jwzw_div:
            jwbt_boxes = jwzw_div.find_all('div', class_='jwbt-box')
            for jwbt_box in jwbt_boxes:
                juan_id = ''
                juan_name = ''
                chapters = []

                # Extract juan id and name from the two <a> tags
                jwbt_div = jwbt_box.find('div', class_='jwbt')
                if jwbt_div:
                    id_a_tag = jwbt_div.find('a', attrs={'name': True})
                    name_a_tag = jwbt_div.find('a', href=True)
                    
                    if id_a_tag:
                        juan_id = id_a_tag.get('name', '').strip()
                    if name_a_tag:
                        juan_name = name_a_tag.get_text(strip=True)

                # Extract chapters following the juan
                jwbtbm_divs = jwbt_box.find_all('div', class_='jwbtbm')
                if jwbtbm_divs and len(jwbtbm_divs) > 0:
                    for jwbtbm_div in jwbtbm_divs:
                        chapter_id = ''
                        chapter_name = ''
                        
                        # Extract chapter id and name from the two <a> tags
                        id_a_tag = jwbtbm_div.find('a', attrs={'name': True})
                        name_a_tag = jwbtbm_div.find('a', href=True)
                        
                        if id_a_tag:
                            chapter_id = id_a_tag.get('name', '').strip()
                        if name_a_tag:
                            chapter_name = name_a_tag.get_text(strip=True)

                        # Extract paragraphs following the chapter
                        paragraphs = []
                        next_sibling = jwbt_box.find_next_sibling()
                        while next_sibling:
                            if next_sibling.name == 'div' and 'jwbt-box' in next_sibling.get('class', []):
                                break
                            if next_sibling.name == 'p':
                                paragraphs.append(next_sibling.get_text(strip=True))
                            next_sibling = next_sibling.find_next_sibling()

                        chapters.append({
                            'id': chapter_id,
                            'name': chapter_name,
                            'paragraphs': paragraphs
                        })
                else:
                    print(f"Warning: No jwbtbm divs found for href '{href}' at path '{target_path}' so there is one chapter.")
                    #In case there is no jwbtbm, for example 0777.htm, just retrieve the single chapter
                    chapter_id = ''
                    chapter_name = ''
                    
                    # Find the <a> in jwbt_box that has the name
                    id_a_tag = jwbt_box.find('a', attrs={'name': True})
                    if id_a_tag:
                        chapter_id = id_a_tag.get('name', '').strip()

                    paragraphs = []
                    next_sibling = jwbt_box.find_next_sibling()
                    while next_sibling:
                        if next_sibling.name == 'div' and 'jwbt-box' in next_sibling.get('class', []):
                            break
                        if next_sibling.name == 'p':
                            paragraphs.append(next_sibling.get_text(strip=True))
                        next_sibling = next_sibling.find_next_sibling()
                    chapters.append({
                        'id': chapter_id,
                        'name': chapter_name,
                        'paragraphs': paragraphs
                    })

                juans.append({
                    'id': juan_id,
                    'name': juan_name,
                    'chapters': chapters
                })

        # Extract last and next bu from div class="jw-bottom"
        last_bu = {}
        next_bu = {}
        jw_bottom_div = soup.find('div', class_='jw-bottom')
        if jw_bottom_div:
            a_tags = jw_bottom_div.find_all('a', href=True)
            if len(a_tags) == 1:
                if "上一部" in a_tags[0].get_text(strip=True):
                    last_bu = {
                        'id': extract_id_from_href(a_tags[0].get('href', '').strip()),  # Use the utility function
                        'name': a_tags[0].get_text(strip=True)
                    }
                elif "下一部" in a_tags[0].get_text(strip=True):
                    next_bu = {
                        'id': extract_id_from_href(a_tags[0].get('href', '').strip()),  # Use the utility function
                        'name': a_tags[0].get_text(strip=True)
                    }
            elif len(a_tags) == 2:
                last_bu = {
                    'id': extract_id_from_href(a_tags[0].get('href', '').strip()),  # Use the utility function
                    'name': a_tags[0].get_text(strip=True)
                } 
                next_bu = {
                    'id': extract_id_from_href(a_tags[1].get('href', '').strip()),  # Use the utility function
                    'name': a_tags[1].get_text(strip=True)
                }

        return {
            'meta': {
                'id': extract_id_from_href(href),  # Use the utility function to extract id
                'Bu': soup.find('div', class_='top-left').get_text(strip=True) if soup.find('div', 'top-left') else '',
                'title': soup.find('div', class_='top-center').get_text(strip=True) if soup.find('div', 'top-center') else '',
                'Arthur': soup.find('div', class_='top-right').get_text(strip=True) if soup.find('div', 'top-right') else '',
                'last_bu': last_bu,
                'next_bu': next_bu
            },
            'juans': juans
        }

    except Exception as e:
        print(f"Error processing file '{target_path}': {e}")
        return {}

def extract_ml_from_ml_files(directory, test_mode=False, test_limit=2):
    """Extracts links starting with a number from all ml*.htm files in the specified directory."""
    # Glob pattern to match ml*.htm files within the directory
    ml_files = glob.glob(os.path.join(directory, 'ml*.htm'))
    
    # If in test mode, limit the number of files processed
    if test_mode:
        ml_files = ml_files[:test_limit]  # Use test_limit for testing

    extracted_bus = {}
    parsed_juan_data = {}

    for ml_file in ml_files:

        with open(ml_file, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
        
        # Extract the name from <h3 class="title">
        title_tag = soup.find('h3', class_='title')
        ml_name = title_tag.get_text(strip=True) if title_tag else ''

        bus = extract_bu_links(ml_file)

        # If in test mode, limit the number of bus processed
        if test_mode:
            bus = bus[:test_limit]  # Use test_limit for testing

        # Create a JSON-like structure to store in extracted_bus
        extracted_bus[os.path.basename(ml_file)] = {
            'id': os.path.splitext(os.path.basename(ml_file))[0][2:],  # Extract number part from file name
            'name': ml_name,
            'bus': bus
        }

        for bu in bus:
            href = bu.get('href')
            if href:
                parsed_data = parse_juan_content(href, directory)
                if parsed_data:
                    parsed_juan_data[bu['id']] = parsed_data

    return extracted_bus, parsed_juan_data

def save_to_json(data, filename):
    """Saves the provided data to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Failed to save data to {filename}: {e}")

def ensure_directory(path):
    """Ensures that the specified directory exists. If not, it creates the directory."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def save_parsed_href_data(parsed_href_data, output_dir):
    """Saves each parsed href data into separate JSON files within the output/books directory."""
    books_output_dir = os.path.join(output_dir, 'books')  # Changed variable name from hrefs_output_dir to books_output_dir
    ensure_directory(books_output_dir)

    for href_id, data in parsed_href_data.items():
        filename = os.path.join(books_output_dir, f"{href_id}.json")  # Updated variable name
        try:
            with open(filename, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            print(f"Parsed href data saved to {filename}")
        except Exception as e:
            print(f"Failed to save parsed href data to {filename}: {e}")

if __name__ == "__main__":

    # Initialize OpenCC converter for Simplified to Traditional Chinese
    cc = opencc.OpenCC('s2t')

    # Specify the directory containing the ml*.htm files
    directory = r'D:\Projects\Cursor\SutraParser\input\qldzj-master\s'

    # Specify the output directory
    output_dir = r'D:\Projects\Cursor\SutraParser\output'

    # Ensure the output directory exists
    ensure_directory(output_dir)

    # Set test_mode to True for development testing
    book_test_mode = True
    font_test_mode = False
    test_limit = 10  # Set the number of files and links to process during testing

    # Extract the links and parse href contents from all ml*.htm files
    extracted_links_dict, parsed_href_data_dict = extract_ml_from_ml_files(directory, book_test_mode, test_limit)

    # Save the extracted links to a single JSON file in the output directory
    mls_json_path = os.path.join(output_dir, 'mls.json')
    save_to_json(extracted_links_dict, mls_json_path)

    # Save each parsed href data to separate JSON files within output/hrefs
    save_parsed_href_data(parsed_href_data_dict, output_dir)

    # Optional: Print confirmation
    print("Extraction and parsing completed. Check the output folder for results.")

    # Specify the fonts directory
    fonts_dir = 'fonts'

    # Specify the output directory for minimized fonts
    book_fonts_output_dir = os.path.join(output_dir, 'book_fonts')
    ensure_directory(book_fonts_output_dir)

    # Get all JSON files in the output/books directory
    json_files_dir = os.path.join(output_dir, 'books')
    json_files = [os.path.join(json_files_dir, f) for f in os.listdir(json_files_dir) if f.endswith('.json')]
    for json_file in json_files:
        print(json_file)

    # Generate minimized fonts for each JSON file
    generate_minimized_fonts(fonts_dir, book_fonts_output_dir, json_files, font_test_mode)

    # Optional: Print confirmation
    print("Font generation completed. Check the output/book_fonts folder for results.")

    # Generate test HTML pages for each JSON file
    generate_test_html_page(output_dir, json_files)

    # Optional: Print confirmation
    print("Test HTML page generation completed. Check the output/test_html folder for results.")