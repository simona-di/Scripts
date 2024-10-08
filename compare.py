import os
import hashlib
import argparse
import sys
import json

bytes_to_read = 8192
checked_files = []

UNIQUE_FILES = "unique_files"
FILES_DIFF_CHECKSUM = "same_name_diff_checksum"
FILES_SAME_CHECKSUM = "same_name_same_checksum"
UNIQUE_FOLDERS = "unique_folders"
SYMLINKS_DIFF_TARGET = "symlinks_diff_target"
SYMLINKS_SAME_TARGET = "symlinks_same_target"
DIFF_FILETYPES = "same_name_diff_filetypes"

results_dict = {
    UNIQUE_FILES: [],
    FILES_DIFF_CHECKSUM: [],
    FILES_SAME_CHECKSUM: [],
    UNIQUE_FOLDERS: [],
    SYMLINKS_DIFF_TARGET: [],
    SYMLINKS_SAME_TARGET: [],
    DIFF_FILETYPES: []
}

def create_json(): 
    workspace = os.getcwd()
    file_path = os.path.join(workspace, "result.json")
    result_file = open(file_path, "w")
    json.dump(results_dict, result_file, indent=4)
    result_file.close()

def create_report(folder1, folder2):
    def print_list(_list):
        if len(_list):
            for item in _list:
                result_file.write("<tr><td>" + item + "<br></td></tr>")
                print(item)
            result_file.write("</table>")
        else:
            result_file.write("<p>None! <br></p>")
            print("None!")
    
    def print_tuple(_tuple, sign):
        if len(_tuple):
            for item in _tuple:
                result_file.write("<tr><td>" + item[0] + sign + item[1] + "<br></td></tr>")
                print(item[0], sign, item[1])
            result_file.write("</table>")
        else:
            result_file.write("<p>None! <br></p>")
            print("None!")
    
    workspace = os.getcwd()
    file_path = os.path.join(workspace, "result.html")
    print("Comparison for folders ", folder1, " and ", folder2)
    result_file = open(file_path, "w")
    result_file.write("<style> p,table{font-family:verdana; font-size:14px;}</style>")
    result_file.write("<pre><br>=================================================================================<br>")
    result_file.write("<p style='font-family:verdana; font-size:16px;'>Comparison for folders <b>" + folder1  + " </b> and <b> " + folder2  + "</b></p>")
    result_file.write("=================================================================================<br><br>")
    result_file.write("<style> td {border:0.5px solid black;}</style>")

    print("\n 1. Unique files (located only in one folder): ")
    result_file.write("<p style='font-family:verdana; font-size:16px;'>1. Unique files (located only in one folder): <br></p>")
    print_list(results_dict[UNIQUE_FILES])

    print("\n 2. Files with same names, but different checksums: ")
    result_file.write("<p style='font-family:verdana; font-size:16px;'>2. Files with same names, but different checksums: <br></p>")
    print_tuple(results_dict[FILES_DIFF_CHECKSUM], " | ")

    print("\n 3. Files with same names and checksums: ")
    result_file.write("<p style='font-family:verdana; font-size:16px;'>3. Files with same names and checksums: <br></p>")
    print_tuple(results_dict[FILES_SAME_CHECKSUM], " == ")

    print("\n 4. Unique folders (located only in one folder): ")
    result_file.write("<p style='font-family:verdana; font-size:16px;'>4. Unique folders (located only in one folder): <br></p>")
    print_list(results_dict[UNIQUE_FOLDERS])

    print("\n 5. Symlinks with different target: ")
    result_file.write("<p style='font-family:verdana; font-size:16px;'>5. Symlinks with different target: <br></p>")
    print_tuple(results_dict[SYMLINKS_DIFF_TARGET], " | ")

    print("\n 6. Symlinks with the same target: ")
    result_file.write("<p style='font-family:verdana; font-size:16px;'>6. Symlinks with the same target: <br></p>")
    print_tuple(results_dict[SYMLINKS_SAME_TARGET], " == ")

    print("\n 7. Different filetypes with the same name (file vs symlink): ")
    result_file.write("<p style='font-family:verdana; font-size:16px;'>7. Different filetypes with the same name (file vs symlink): <br></p>")
    print_tuple(results_dict[DIFF_FILETYPES], " | ")

    result_file.write("</table> ")
    result_file.close()

def calculate_checksum(file):
    with open(file, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(bytes_to_read)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(bytes_to_read)
    return file_hash.hexdigest()

def _compare_files(current_path, folder1, folder2, files):
    for file in files:
        relative_path = current_path.replace(folder1, "")
        folder1_full_path = os.path.join(current_path, file)
        folder2_full_path = os.path.join(folder2, relative_path, file)
        # If file from folder1 is not found in folder2, skip next checks
        if not os.path.exists(folder2_full_path):
            results_dict[UNIQUE_FILES].append(folder1_full_path)
            continue
        
        # If a file is already compared, skip next checks
        # Logic added mostly for the second comparison between folder2 and folder1 in order to not compare files we already did
        if folder1_full_path in checked_files:
            continue

        # File from folder1 is found in folder2 and is not yet compared
        checked_files.append(folder2_full_path)
        if os.path.islink(folder1_full_path) and os.path.islink(folder2_full_path): 
            if os.readlink(folder1_full_path) != os.readlink(folder2_full_path):
                results_dict[SYMLINKS_DIFF_TARGET].append(tuple([folder1_full_path, folder2_full_path]))
            else:
                results_dict[SYMLINKS_SAME_TARGET].append(tuple([folder1_full_path, folder2_full_path]))
        elif os.path.isfile(folder1_full_path) and os.path.isfile(folder2_full_path):
            if calculate_checksum(folder1_full_path) != calculate_checksum(folder2_full_path):
                results_dict[FILES_DIFF_CHECKSUM].append(tuple([folder1_full_path, folder2_full_path]))
            else:
                results_dict[FILES_SAME_CHECKSUM].append(tuple([folder1_full_path, folder2_full_path]))
        else:
            results_dict[DIFF_FILETYPES].append(tuple([folder1_full_path, folder2_full_path]))

def _compare_folders(current_path, folder1, folder2, folders):
    for folder in folders:
        relative_path = current_path.replace(folder1, "")
        folder1_full_path = os.path.join(current_path, folder)
        folder2_full_path = os.path.join(folder2, relative_path, folder)
        # If folder from folder1 is not found in folder2, add it to unique folders
        if not os.path.exists(folder2_full_path):
            results_dict[UNIQUE_FOLDERS].append(folder1_full_path)         

def _compare(folder1, folder2):
    for (current_path, folder_names, file_names) in os.walk(folder1):
        _compare_files(current_path, folder1, folder2, file_names)
        _compare_folders(current_path, folder1, folder2, folder_names)

def compare(folder1, folder2):
    _compare(folder1, folder2)
    _compare(folder2, folder1)

def main(parser):
    parser.add_argument("-f1", "--folder1", dest="folder_1", default="", help="Input path for Folder 1")
    parser.add_argument("-f2", "--folder2", dest="folder_2", default="", help="Input path for Folder 2")

    args = parser.parse_args()
    folder1 = args.folder_1
    folder2 = args.folder_2

    if os.path.isdir(folder1) and os.path.isdir(folder2): 
        compare(folder1, folder2)
        create_report(folder1, folder2)
        create_json()
    else:
        print("Provided input is not valid! ")
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    main(parser)