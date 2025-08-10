import json
from datetime import datetime, timedelta
import sys

# Crucial for handling Unicode characters when printing to console on Windows
# This ensures sys.stdout uses UTF-8 encoding
sys.stdout

# Define time slots in 30-minute increments for finer granularity
TIME_SLOTS = []
for h in range(8, 21): # From 8 AM to 8 PM (20:00)
    TIME_SLOTS.append(f"{h:02d}:00")
    if h < 20: # Add 30-minute mark if not the very last hour
        TIME_SLOTS.append(f"{h:02d}:30")
# Example TIME_SLOTS: ['08:00', '08:30', '09:00', '09:30', ..., '20:00']

# Original HOURS for header display purposes (full hours)
HOURS_FOR_HEADER = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

def load_classes(path):
    """Loads class data from a JSON file."""
    # Explicitly open with utf-8 encoding to ensure correct reading of characters
    with open(path, 'r', encoding='utf8') as f:
        return json.load(f)

def time_to_colspan(start, duration):
    """
    Calculates the colspan for a class based on its duration,
    where each column represents a 30-minute slot.
    """
    fmt = "%H:%M"
    start_dt = datetime.strptime(start, fmt)
    h_dur, m_dur = map(int, duration.split(":"))
    
    total_minutes = h_dur * 60 + m_dur
    
    # Calculate colspan based on 30-minute intervals, rounding up
    # e.g., 1 hour (60 min) -> 2 slots; 1 hour 30 min (90 min) -> 3 slots
    return max(1, (total_minutes + 29) // 30)

def get_start_slot_index(start_time_str):
    """
    Finds the index of the starting time slot in TIME_SLOTS.
    Assumes start_time_str is in HH:00 or HH:30 format.
    """
    try:
        return TIME_SLOTS.index(start_time_str)
    except ValueError:
        # If the time is not exactly on a 00 or 30 mark,
        # round down to the nearest 30-minute interval for placement.
        start_dt = datetime.strptime(start_time_str, "%H:%M")
        minute = start_dt.minute
        if minute < 30:
            aligned_time_str = start_dt.strftime("%H:00")
        else:
            aligned_time_str = start_dt.strftime("%H:30")
        
        try:
            return TIME_SLOTS.index(aligned_time_str)
        except ValueError:
            # Fallback if somehow still not found (shouldn't happen with proper TIME_SLOTS)
            return 0 # Default to the very beginning if something goes wrong


def compute_end(start, duration):
    """Computes the end time of a class."""
    fmt = "%H:%M"
    start_dt = datetime.strptime(start, fmt)
    h, m = map(int, duration.split(":"))
    end_dt = start_dt + timedelta(hours=h, minutes=m)
    return end_dt.strftime("%H:%M")

def generate_cell(cls):
    """Generates the HTML for a single class cell."""
    span = time_to_colspan(cls["start"], cls["duration"])
    
    # Define pastel background colors with good text contrast for each day
    color_classes = {
        "MON": "bg-yellow-400 text-neutral-900",
        "TUE": "bg-pink-400 text-neutral-900",
        "WED": "bg-green-400 text-neutral-900",
        "THU": "bg-orange-400 text-neutral-900",
        "FRI": "bg-blue-400 text-neutral-900",
        "SAT": "bg-purple-400 text-neutral-900",
        "SUN": "bg-red-400 text-neutral-900"
    }
    color = color_classes.get(cls["day"], "bg-gray-700 text-neutral-900")
    
    html = f'''
        <td colspan="{span}" class="p-3 align-top {color} rounded-lg overflow-hidden">
            <div class="text-sm leading-tight">
                <div class="mb-1 font-semibold">[{cls['start']}-{compute_end(cls['start'], cls['duration'])}]</div>
                <div class="font-bold">{cls['code']}</div>
                <div class="mb-1">{cls['title']}</div>
                <div class="text-xs opacity-90">{cls['room']} | {cls['type']} {cls['section']}</div>
            </div>
        </td>'''
    return html

def generate_row(day, classes, is_last_row):
    """Generates the HTML for a single day's row in the schedule."""
    day_colors = {
        "MON": "bg-yellow-400 text-neutral-900",
        "TUE": "bg-pink-400 text-neutral-900",
        "WED": "bg-green-400 text-neutral-900",
        "THU": "bg-orange-400 text-neutral-900",
        "FRI": "bg-blue-400 text-neutral-900",
        "SAT": "bg-purple-400 text-neutral-900",
        "SUN": "bg-red-400 text-neutral-900"
    }
    day_color = day_colors.get(day, "bg-gray-800 text-neutral-900")
    
    # Removed border-b class from here to remove horizontal borders on body rows
    row = f'<tr class="h-25">'
    
    # Sticky day column
    row += f'<td class="w-48 sticky left-0 z-20 px-4 py-3 font-bold text-center {day_color} whitespace-nowrap{' border-b border-gray-800' if not is_last_row else ''}"> {day} </td>'
    
    slot_ptr = 0 # Pointer to the current 30-minute slot index
    
    sorted_classes = sorted([cls for cls in classes if cls['day'] == day], key=lambda x: datetime.strptime(x['start'], "%H:%M"))
    
    for cls in sorted_classes:
        cls_start_slot_index = get_start_slot_index(cls["start"])
        colspan = time_to_colspan(cls["start"], cls["duration"])

        # Fill empty cells before the class starts
        empty_slots_before = cls_start_slot_index - slot_ptr
        for _ in range(empty_slots_before):
            row += f'<td class="w-12{' border-b border-gray-800' if not is_last_row else ''}"></td>' # Each empty cell is now 30 minutes
        
        slot_ptr = cls_start_slot_index

        # Add the class cell
        row += generate_cell(cls)
        slot_ptr += colspan # Advance slot pointer by the class duration in 30-minute units

    # Fill remaining empty cells until the end of the schedule
    while slot_ptr < len(TIME_SLOTS):
        row += f'<td class="w-12{' border-b border-gray-800' if not is_last_row else ''}"></td>' # Each empty cell is now 30 minutes
        slot_ptr += 1
            
    row += '</tr>'
    return row

def generate_schedule_html(classes):
    """Generates the complete HTML for the weekly schedule."""
    html = '''<!doctype html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8" /> <!-- THIS LINE IS CRUCIAL FOR THAI CHARACTERS -->
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Weekly Schedule</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
</head>
<body class="bg-[#0b0f1a] text-white min-h-screen flex flex-col items-center justify-center py-8 font-sans">
    <div class="overflow-x-auto w-[95vw] h-[96vh] rounded-xl shadow-2xl bg-[#111622] border border-gray-800">
        <table class="border-separate border-spacing-0 size-full text-sm">
            <thead>
                <tr class="bg-[#111622] sticky top-0 z-20 border-b border-gray-800">
                    <th class="w-48 sticky left-0 z-[100] bg-[#111622] px-4 py-3 text-left font-semibold text-white rounded-tl-lg border-r border-gray-800">Day/Time</th>'''
    # Generate header for full hours, each spanning two 30-minute slots
    for h in HOURS_FOR_HEADER:
        html += f'<th colspan="2" class="px-4 py-3 w-24 text-center text-gray-300 font-medium whitespace-nowrap border-r border-b border-gray-800">{h}:00</th>'
    html += '</tr></thead><tbody>'
    for i, day in enumerate(DAYS):
        is_last_row = (i == len(DAYS) - 1)
        html += generate_row(day, classes, is_last_row)
    html += '''</tbody></table>
    </div>
    <div class="text-right text-xs text-gray-400 p-4 mt-4 select-none">created by Sirapob P.</div>
</body>
</html>'''
    return html

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python gen_schedule.py <data.json_path> <output.html_path>")
        sys.exit(1)
    data = load_classes(sys.argv[1])

    with open(sys.argv[2], 'w', encoding='utf8') as f:
        f.write(generate_schedule_html(data))
    print(f"Successfully save schedule to {sys.argv[2]}")