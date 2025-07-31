import json
from datetime import datetime, timedelta

HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

def load_classes(path):
    """Loads class data from a JSON file."""
    with open(path) as f:
        return json.load(f)

def time_to_colspan(start, duration):
    """Calculates the colspan for a class based on its duration."""
    fmt = "%H:%M"
    start_dt = datetime.strptime(start, fmt)
    h, m = map(int, duration.split(":"))
    # Calculate duration in hours (rounded up to nearest hour for colspan)
    total_minutes = h * 60 + m
    return max(1, int(total_minutes // 60)) # Ensure at least colspan 1

def get_start_hour(start):
    """Extracts the start hour from a time string."""
    return int(start.split(":")[0])

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
        "MON": "bg-yellow-600 text-white", # Darker yellow for better contrast
        "TUE": "bg-pink-600 text-white",   # Darker pink
        "WED": "bg-green-600 text-white",  # Darker green
        "THU": "bg-orange-600 text-white", # Darker orange
        "FRI": "bg-blue-600 text-white",   # Darker blue
        "SAT": "bg-purple-600 text-white", # Darker purple
        "SUN": "bg-red-600 text-white"     # Darker red
    }
    color = color_classes.get(cls["day"], "bg-gray-700 text-white")
    
    html = f'''
        <td colspan="{span}" class="p-3 align-top {color} rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
            <div class="text-sm leading-tight">
                <div class="mb-1 font-semibold">[{cls['start']}-{compute_end(cls['start'], cls['duration'])}]</div>
                <div class="font-bold">{cls['code']}</div>
                <div class="mb-1">{cls['title']}</div>
                <div class="text-xs opacity-90">{cls['room']} | {cls['type']} {cls['section']}</div>
            </div>
        </td>'''
    return html

def generate_row(day, classes):
    """Generates the HTML for a single day's row in the schedule."""
    day_colors = {
        "MON": "bg-yellow-700 text-white",
        "TUE": "bg-pink-700 text-white",
        "WED": "bg-green-700 text-white",
        "THU": "bg-orange-700 text-white",
        "FRI": "bg-blue-700 text-white",
        "SAT": "bg-purple-700 text-white",
        "SUN": "bg-red-700 text-white"
    }
    day_color = day_colors.get(day, "bg-gray-800 text-white")
    
    row = f'<tr class="border-b border-gray-800">'
    # Sticky day column
    row += f'<td class="sticky left-0 z-10 px-4 py-3 font-bold text-center {day_color} whitespace-nowrap"> {day} </td>'
    
    hour_ptr = HOURS[0] # Start from the first hour in the HOURS list
    
    # Filter and sort classes for the current day
    sorted_classes = sorted([cls for cls in classes if cls['day'] == day], key=lambda x: datetime.strptime(x['start'], "%H:%M"))
    
    for cls in sorted_classes:
        cls_start_hour = get_start_hour(cls["start"])
        cls_start_minute = int(cls["start"].split(":")[1])
        colspan = time_to_colspan(cls["start"], cls["duration"])

        # Fill empty cells before the class starts
        # Calculate the number of empty hour slots
        empty_slots_before = cls_start_hour - hour_ptr
        if cls_start_minute > 0 and empty_slots_before >= 0:
            # If a class starts mid-hour, it occupies the current hour slot
            # So, fill empty slots only up to the hour before the class starts
            for _ in range(empty_slots_before):
                row += '<td></td>'
            hour_ptr = cls_start_hour
        elif empty_slots_before > 0:
            for _ in range(empty_slots_before):
                row += '<td></td>'
            hour_ptr = cls_start_hour

        # Add the class cell
        row += generate_cell(cls)
        hour_ptr += colspan # Advance hour pointer by the class duration in hours

    # Fill remaining empty cells until the end of the schedule
    while hour_ptr <= HOURS[-1]: # Iterate until the last hour in the HOURS list
        row += '<td></td>'
        hour_ptr += 1
        
    row += '</tr>'
    return row

def generate_schedule_html(classes):
    """Generates the complete HTML for the weekly schedule."""
    html = '''<!doctype html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Weekly Schedule</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        /* Custom scrollbar for better aesthetics */
        ::-webkit-scrollbar {
            height: 8px;
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #1a202c; /* Darker track */
        }
        ::-webkit-scrollbar-thumb {
            background: #4a5568; /* Gray thumb */
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #6b7280; /* Lighter gray on hover */
        }
        /* Ensure sticky elements are above content */
        .sticky-header-cell {
            z-index: 30;
        }
        .sticky-day-cell {
            z-index: 20;
        }
        .table-auto td {
            min-width: 6rem; /* Ensure minimum width for time slots */
            height: 5rem; /* Consistent height for rows */
            vertical-align: top; /* Align content to the top */
        }
        /* Ensure the table itself has borders for the grid effect */
        .table-auto {
            border-collapse: collapse; /* Collapse borders to remove spacing */
        }
        .table-auto th, .table-auto td {
            /* Removed border-right to eliminate y-axis borders */
            border-bottom: 1px solid #1f2937; /* Keep horizontal borders */
        }
        /* Removed specific border-right for last-child and sticky-left-0 */
        .table-auto tr:last-child td {
            border-bottom: none; /* Remove bottom border from last row */
        }
    </style>
</head>
<body class="bg-[#0b0f1a] text-white min-h-screen flex flex-col items-center justify-center py-8">
    <h1 class="text-4xl font-extrabold mb-8 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
        My Weekly Schedule
    </h1>
    <div class="overflow-x-auto w-[90vw] rounded-xl shadow-2xl bg-[#111622] border border-gray-800">
        <table class="table-auto border-separate border-spacing-1 w-full text-sm">
            <thead>
                <tr class="bg-[#111622] sticky top-0 z-20">
                    <th class="sticky left-0 z-30 bg-[#111622] px-4 py-3 text-left font-semibold text-white rounded-tl-lg">Day/Time</th>'''
    for h in HOURS:
        html += f'<th class="px-4 py-3 w-[{1/14 * 100}%] border-l border-gray-800 text-center text-gray-300 font-medium whitespace-nowrap">{h}:00</th>'
    html += '</tr></thead><tbody>'
    for day in DAYS:
        html += generate_row(day, classes)
    html += '''</tbody></table>
    </div>
    <div class="text-right text-xs text-gray-400 p-4 mt-4 select-none">created by Sirapob P. & ChatGPT</div>
</body>
</html>'''
    return html

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python gen_schedule.py <data.json_path>")
        sys.exit(1)
    data = load_classes(sys.argv[1])
    print(generate_schedule_html(data))

