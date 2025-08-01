import subprocess
import sys
import os

def run_pipeline(html_input_path, html_output_path):
    """
    Runs the HTML parsing and schedule generation pipeline.

    Args:
        html_input_path (str): Path to the input HTML file.
        html_output_path (str): Path to save the generated HTML schedule.
    """
    # Define a temporary JSON file path
    # We'll place it in the same directory as the script for simplicity
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_json_path = os.path.join(script_dir, "temp_data.json")

    print(f"Starting pipeline for input: {html_input_path}")

    # Step 1: Run parser.py to convert HTML to JSON
    print(f"Running parser.py to convert '{html_input_path}' to '{temp_json_path}'...")
    try:
        # Use sys.executable to ensure the correct Python interpreter is used
        parser_process = subprocess.run(
            [sys.executable, "parser.py", html_input_path, temp_json_path],
            capture_output=True,
            text=True,
            check=True # Raise an exception for non-zero exit codes
        )
        print("parser.py output:")
        print(parser_process.stdout)
        if parser_process.stderr:
            print("parser.py errors (if any):")
            print(parser_process.stderr)
        print("Parsing complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error running parser.py: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return
    except FileNotFoundError:
        print("Error: parser.py not found. Make sure 'parser.py' is in the same directory.")
        return
    except Exception as e:
        print(f"An unexpected error occurred during parsing: {e}")
        return

    # Check if the temporary JSON file was created
    if not os.path.exists(temp_json_path) or os.path.getsize(temp_json_path) == 0:
        print(f"Error: Temporary JSON file '{temp_json_path}' was not created or is empty by parser.py.")
        return

    print(f"Running gen_schedule.py to generate HTML from '{temp_json_path}'...")
    try:
        gen_schedule_process = subprocess.run(
            [sys.executable, "gen_schedule.py", temp_json_path, html_output_path],
            check=True # Raise an exception for non-zero exit codes
        )
        if gen_schedule_process.stderr:
            print("gen_schedule.py errors (if any):")
            print(gen_schedule_process.stderr)
        print("HTML generation complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error running gen_schedule.py: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return
    except FileNotFoundError:
        print("Error: gen_schedule.py not found. Make sure 'gen_schedule.py' is in the same directory.")
        return
    except Exception as e:
        print(f"An unexpected error occurred during HTML generation: {e}")
        return

    # Clean up the temporary JSON file
    if os.path.exists(temp_json_path):
        os.remove(temp_json_path)
        print(f"Cleaned up temporary file: {temp_json_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_html_file_path> <output_schedule_html_path>")
        sys.exit(1)

    input_html = sys.argv[1]
    output_html = sys.argv[2]
    run_pipeline(input_html, output_html)

