from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import sys # Import the sys module to access command-line arguments

def parse_html_to_json(html_content):
    """
    Parses HTML content to extract course information and format it into JSON.
    Supports both Thai and English HTML structures for the relevant fields.

    Args:
        html_content (str): The HTML string containing course data.

    Returns:
        str: A JSON string representing the extracted course data.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    courses_data = []

    # Find all card elements, each representing a course
    course_cards = soup.find_all('div', class_='card')

    for card in course_cards:
        day_element = card.find('div', style="font-weight: 600; font-size: 10px;")
        day = day_element.get_text(strip=True) if day_element else "N/A"

        time_element = card.find('div', style="font-weight: 500; font-size: 18px;")
        time_range = time_element.get_text(strip=True) if time_element else "N/A"

        start_time = "N/A"
        duration = "N/A"
        if ' - ' in time_range:
            start_str, end_str = time_range.split(' - ')
            start_time = start_str.strip()
            try:
                # Convert times to datetime objects to calculate duration
                start_dt = datetime.strptime(start_str.strip(), '%H:%M')
                end_dt = datetime.strptime(end_str.strip(), '%H:%M')
                
                # Handle cases where end time might be on the next day (e.g., 23:00 - 02:00)
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                
                duration_td = end_dt - start_dt
                hours = int(duration_td.total_seconds() // 3600)
                minutes = int((duration_td.total_seconds() % 3600) // 60)
                
                # Format duration as HH:MM
                duration = f"{hours:02d}:{minutes:02d}"
            except ValueError:
                # Fallback if time parsing fails
                pass

        code_element = card.find('div', style="font-weight: 600; font-size: 12px;")
        code = code_element.get_text(strip=True) if code_element else "N/A"

        # The English title is now consistently the first 'cut-word' div.
        title_elements = card.find_all('div', class_='cut-word')
        title = "N/A"
        if len(title_elements) > 0: # Get the first 'cut-word' div for English title
            title = title_elements[0].get_text(strip=True) 

        # Find room element by looking for 'Room' or 'ห้อง' within a span, then extract from its parent div
        room = "N/A"
        # Look for a span whose text contains 'Room' or 'ห้อง'
        room_label_span = card.find('span', string=lambda text: text and ('Room' in text or 'ห้อง' in text))
        if room_label_span:
            # The room number is usually directly after the span within the same parent div
            # Get the text of the parent div and then clean it
            parent_div_of_room_label = room_label_span.find_parent('div')
            if parent_div_of_room_label:
                full_room_text = parent_div_of_room_label.get_text(strip=True)
                # Remove the "Room " or "ห้อง " prefix
                if 'Room' in full_room_text:
                    room = full_room_text.replace('Room', '')
                elif 'ห้อง' in full_room_text:
                    room = full_room_text.replace('ห้อง', '')
        
        # Determine type based on 'Lec', 'Lab', 'บรรยาย', or 'ปฏิบัติ'
        type_element = card.find('span', class_=lambda x: x and ('badge-blue' in x or 'badge-orange' in x))
        type_text = type_element.get_text(strip=True) if type_element else "N/A"
        
        course_type = "N/A"
        if type_text == "บรรยาย" or type_text == "Lec":
            course_type = "Lecture"
        elif type_text == "ปฏิบัติ" or type_text == "Lab":
            course_type = "Laboratory"
        else:
            course_type = type_text # Fallback for other types if any

        # Find section element by looking for 'Section' or 'หมู่'
        section_element = card.find('span', style="color: rgb(10, 187, 135);")
        section = section_element.get_text(strip=True) if section_element else "N/A"

        courses_data.append({
            "day": day,
            "start": start_time,
            "duration": duration,
            "code": code,
            "title": title,
            "room": room,
            "type": course_type,
            "section": section
        })

    return json.dumps(courses_data, indent=2, ensure_ascii=False)

# Check if a file path argument is provided
if len(sys.argv) == 3:
    html_file_path = sys.argv[1] # Get the file path from the first argument
    output_file_path = sys.argv[2] # Get the save path from the second argument

else:
    print("Usage: python your_script_name.py <path_to_html_file> <json_save_file>")
    sys.exit(1) # Exit if no file path is provided

# Read HTML content from the file
html_content = ""
try:
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
except FileNotFoundError:
    print(f"Error: The file '{html_file_path}' was not found.")
except Exception as e:
    print(f"An error occurred while reading the file: {e}")

# Generate the JSON output if content was read successfully
if html_content:
    json_output = parse_html_to_json(html_content)
    try:
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(json_output)
        print(f"JSON data successfully written to '{output_file_path}'")
    except Exception as e:
        print(f"An error occurred while writing the JSON to file: {e}")
else:
    print("No HTML content to parse. Please check the file path and content.")
