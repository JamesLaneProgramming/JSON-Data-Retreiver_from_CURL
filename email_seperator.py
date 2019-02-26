import csv
import sys
import openpyxl

# https://openpyxl.readthedocs.io/en/stable/

files = sys.argv
number_of_files_parsed = len(files)

excel_document = openpyxl.load_workbook(str(files[1]))

sheet_names_available = excel_document.get_sheet_names()
print("Available sheets in given file: ", sheet_names_available)

selected_sheet = excel_document.get_sheet_by_name(sheet_names_available[0])

cell_range = selected_sheet['A2': 'C96']

for each_row in cell_range:
    first_name = None
    last_name = None
    student_number = None
    for iterator in range(0, len(each_row)):
        if(iterator == 0):
            first_name = each_row[iterator].value
        if(iterator == 1):
            last_name = each_row[iterator].value
        if(iterator == 2):
            student_email = each_row[iterator].value
            student_number = student_email.split('@')[0]
    full_name = str(first_name) + str(last_name)
    print(full_name + ': ' + student_number)
