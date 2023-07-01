import tkinter as tk
from tkinter import filedialog
import os
import logging
import glob

# Set up logging
logging.basicConfig(filename='file_splitter.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

number_of_chunks_needed = 0


def validate_input(file_path, max_file_size):
    # Check if the file path exists
    if not os.path.exists(file_path):
        print(f'Error: File not found - {file_path}')
        logging.error(f'File not found - {file_path}')
        return False

    # Check if the maximum file size is a positive number
    if max_file_size <= 0:
        print('Error: Maximum file size must be a positive number')
        logging.error('Maximum file size must be a positive number')
        return False

    return True


def split_file(file_path, max_file_size, output_folder):
    if not validate_input(file_path, max_file_size):
        return

    # file_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)
    chunk_size = max_file_size * 1024 * 1024  # Convert max_file_size from MB to bytes

    # Get the size of the original file
    try:
        original_file_size = os.path.getsize(file_path)
    except FileNotFoundError:
        print(f'Error: File not found - {file_path}')
        logging.error(f'File not found - {file_path}')
        return

    original_file_size_in_mb = original_file_size / (1024 * 1024)

    print(f'Original File: {file_path}')
    print(f'File Size: {original_file_size_in_mb:.2f} MB')
    print(f'Maximum Chunk Size: {max_file_size} MB')

    logging.info(f'Started splitting file: {file_path}')
    logging.info(f'Original File Size: {original_file_size_in_mb:.2f} MB')
    logging.info(f'Maximum Chunk Size: {max_file_size} MB')

    # No need to split if the max given size already exceeds the file size
    if original_file_size_in_mb < max_file_size:
        print(f'Chunk size is greater than the original file size! No need to split.')
        logging.info(f'Chunk size is greater than the original file size! No need to split.')
        return

    # Calculate the number of chunks needed
    global number_of_chunks_needed
    number_of_chunks_needed = original_file_size // chunk_size + (1 if original_file_size % chunk_size != 0 else 0)
    print(f'Number of Chunks needed: {number_of_chunks_needed}\n')
    logging.info(f'Number of Chunks needed: {number_of_chunks_needed}\n')

    with open(file_path, 'rb') as f:
        index = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                break

            chunk_name = f'{file_name}.part{index}'
            # To create chunks in the same folder, use file_dir instead of output_folder
            chunk_path = os.path.join(output_folder, chunk_name)
            try:
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(data)
            except IOError as e:
                print(f'Error: Failed to write chunk {chunk_name}: {e}')
                logging.error(f'Failed to write chunk {chunk_name}: {e}')
                return
            index += 1

            logging.info(f'Split: {chunk_name} ({len(data) / (1024 * 1024):.2f} MB)')
            print(f'Split: {chunk_name} ({len(data) / (1024 * 1024):.2f} MB)')

    logging.info(f'Finished splitting the file {file_path}.')
    print(f'Finished splitting the file {file_path}.')


# Input the path of first part (.part0) of the split files to start joining
# TODO: consistency check -> all parts (last part excluded) should have the same size.
# NOTE: You cant know if the last .part file is missing so that you cant rejoin the original file -> broken joined file
def join_files(file_path, output_path):
    if not os.path.exists(file_path):
        print(f'Error: File not found - {file_path}')
        logging.error(f'File not found - {file_path}')
        return False

    print(f"Joining files")
    logging.error(f"Joining files")
    incomplete = False

    file_name_without_full_path = os.path.basename(file_path)

    # Get the full path file name without the .part
    full_path_file_name_without_part = file_path.rsplit(".part", 1)[0]
    # print(f"full_path_file_name_without_part {full_path_file_name_without_part}")

    # Get the file name without the .part
    file_name_without_part = file_name_without_full_path.rsplit(".", 1)[0]
    # print(f"file_name_without_part {file_name_without_part}")
    # Get the folder path of the selected part0 file
    folder_path = os.path.dirname(file_path)  # os.path.dirname(os.path.abspath(__file__))  # To create the output file in the same folder as the script
    # print(f"folder_path {folder_path}")
    # Define the pattern of the part files using the file name
    pattern = f'{file_name_without_part}.part*'
    file_paths = glob.glob(folder_path + "/" + pattern)
    # print(f"file_paths {file_paths}")
    # Display all part files
    listing_index = 1
    found_part_file_index = 0
    missing_part_file_indexes = []
    print(f"Found part files:")

    # Define a sorting key function
    def sort_key(filename):
        # Extract the numeric part by removing "filename.part"
        number = filename.rsplit(".part", 1)[1]
        return int(number)

    # Sort the filenames using the custom sorting key
    sorted_filenames = sorted(file_paths, key=sort_key)
    # print(f"SORTED: {sorted_filenames}")

    for found_file in sorted_filenames:
        # Detect any missing consecutive part files here and display error message if missing
        part_number = found_file.rsplit(".part", 1)[1]
        # Handle edge case if there is a file with filename.pathXYZ or similar exists
        # and check the part numbering for missing parts
        if part_number.isdigit():
            print(f"  ({listing_index}) {found_file}  [Part number: {part_number}]")
            # When a part number is missing, cancel join
            if found_part_file_index != int(part_number):
                missing_part_file_indexes.append(found_part_file_index)
                incomplete = True
                found_part_file_index = int(part_number)
                # print(f"    Part number is missing: {found_part_file_index}")
        else:
            continue
        found_part_file_index += 1
        listing_index += 1

    if incomplete:
        print(f"Missing parts: {missing_part_file_indexes}")
        print(f'Cancelling join operation.')
        logging.error(f"Missing parts: {missing_part_file_indexes}")
        logging.error(f'Cancelling join operation.')
        return

    # Create the output file in the given output directory
    joined_file_path = os.path.join(output_path, f'joined_{file_name_without_part}')

    with open(joined_file_path, 'wb') as joined_file:
        index = 0
        while True:
            chunk_name = f'{file_name_without_part}.part{index}'
            chunk_path = os.path.join(folder_path, chunk_name)

            if not os.path.exists(chunk_path):
                # If one of the .part<index> file is missing, cancel join
                if index < number_of_chunks_needed or index == 0:
                    print(f'Error: Chunk path does not exist: {chunk_path}')
                    logging.error(f'Chunk path does not exist: {chunk_path}')

                    print(f'Cancelling join operation for {file_path} (Missing part {index})')
                    logging.error(f'Cancelling join operation for {file_path} (Missing part {index})')
                    incomplete = True
                # return
                break

            try:
                with open(chunk_path, 'rb') as chunk_file:
                    joined_file.write(chunk_file.read())
                    index += 1
            except IOError as e:
                print(f'Error: Failed to read chunk {chunk_name}: {e}')
                logging.error(f'Failed to read chunk {chunk_name}: {e}')
                return

            print(f'Joined: {chunk_name}')
            logging.info(f'Joined: {chunk_name}')

    if not incomplete:
        print(f'\nJoined File: {joined_file_path}')
        logging.info('Finished joining the files.')
    else:
        # Remove the unfinished joined file
        if os.path.exists(joined_file_path):
            os.remove(joined_file_path)


input_file_path_split = ""
output_folder_path_split = ""
input_file_path_join = ""
output_folder_path_join = ""


class FileSplitterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Splitter/Joiner")

        # Create Split button
        self.split_button = tk.Button(self.root, text="Split", command=self.split_button_click)
        self.split_button.pack(pady=10)

        # Create Join button
        self.join_button = tk.Button(self.root, text="Join", command=self.join_button_click)
        self.join_button.pack(pady=10)

        # Create Back button (initially hidden)
        self.back_button = tk.Button(self.root, text="Back", command=self.back_button_click)

        # Create Start Split button (initially hidden)
        self.start_split_button = tk.Button(self.root, text="Start Split", command=self.start_split_button_click)

        # Create Start Join button (initially hidden)
        self.start_join_button = tk.Button(self.root, text="Start Join", command=self.start_join_button_click)

        # Create labels for displaying file paths (initially hidden)
        self.split_input_file_label = tk.Label(self.root, text="Selected Input File: ")
        self.split_output_file_label = tk.Label(self.root, text="Selected Output Folder: ")

        # Create labels for displaying file paths (initially hidden)
        self.join_input_file_label = tk.Label(self.root, text="Selected Input File: ")
        self.join_output_file_label = tk.Label(self.root, text="Selected Output Folder: ")

    def split_button_click(self):
        # Hide existing buttons
        self.split_button.pack_forget()
        self.join_button.pack_forget()

        # Create Input File button
        self.input_file_button = tk.Button(self.root, text="Input File", command=self.select_input_file_split)
        self.input_file_button.pack(pady=5)  # side=tk.LEFT
        self.split_input_file_label.pack(pady=5)

        # Create Output File button
        self.output_file_button = tk.Button(self.root, text="Output File", command=self.select_output_folder_split)
        self.output_file_button.pack(pady=5)  # side=tk.LEFT
        self.split_output_file_label.pack(pady=5)

        # Create text input and label for Chunks in MB
        self.chunks_label = tk.Label(self.root, text="Chunks in MB")
        self.chunks_label.pack(pady=10)

        self.chunks_entry = tk.Entry(self.root)
        self.chunks_entry.pack()

        # Start Split button
        self.start_split_button.pack(pady=5)

        # Show Back button
        self.back_button.pack(pady=5)

    def join_button_click(self):
        # Hide existing buttons
        self.split_button.pack_forget()
        self.join_button.pack_forget()

        # Create Input File button
        self.input_file_button = tk.Button(self.root, text="Input File", command=self.select_input_file_join)
        self.input_file_button.pack(pady=5)  # side=tk.LEFT
        self.join_input_file_label.pack(pady=5)

        # Create Output File button
        self.output_file_button = tk.Button(self.root, text="Output File", command=self.select_output_folder_join)
        self.output_file_button.pack(pady=5)  # side=tk.LEFT
        self.join_output_file_label.pack(pady=5)

        # Start Join button
        self.start_join_button.pack(pady=5)

        # Show Back button
        self.back_button.pack(pady=5)

    def back_button_click(self):
        # Destroy the split/join related widgets
        self.back_button.pack_forget()
        self.input_file_button.pack_forget()
        self.output_file_button.pack_forget()
        self.split_input_file_label.pack_forget()
        self.split_output_file_label.pack_forget()
        self.join_input_file_label.pack_forget()
        self.join_output_file_label.pack_forget()

        self.start_split_button.pack_forget()
        self.start_join_button.pack_forget()

        # Clear Chunk input
        self.chunks_label.pack_forget()
        self.chunks_entry.pack_forget()

        # Show the original buttons
        self.split_button.pack(pady=10)
        self.join_button.pack(pady=10)

    def start_split_button_click(self):
        if len(input_file_path_split) == 0 or len(output_folder_path_split) == 0:
            return

        chunk_in_mb = int(self.chunks_entry.get())
        validate_input(input_file_path_split, chunk_in_mb)
        split_file(input_file_path_split, chunk_in_mb, output_folder_path_split)

    def start_join_button_click(self):
        if len(input_file_path_join) == 0 or len(output_folder_path_join) == 0:
            return

        join_files(input_file_path_join, output_folder_path_join)

    def select_input_file_split(self):
        global input_file_path_split
        input_file_path_split = filedialog.askopenfilename()
        self.split_input_file_label.config(text="Selected Input File: " + input_file_path_split)

    def select_output_folder_split(self):
        global output_folder_path_split
        output_folder_path_split = filedialog.askdirectory()
        self.split_output_file_label.config(text="Selected Output Folder: " + output_folder_path_split)

    def select_input_file_join(self):
        global input_file_path_join
        input_file_path_join = filedialog.askopenfilename()
        self.join_input_file_label.config(text="Selected Input File: " + input_file_path_join)

    def select_output_folder_join(self):
        global output_folder_path_join
        output_folder_path_join = filedialog.askdirectory()
        self.join_output_file_label.config(text="Selected Output Folder: " + output_folder_path_join)


root = tk.Tk()
file_splitter = FileSplitterGUI(root)
root.mainloop()
