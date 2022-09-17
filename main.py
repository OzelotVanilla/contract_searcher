import os
import shutil
from processor.checker import checkDocument
from processor.word_file import writeResultToWord
from util.read_file import getPDFFilePathGenerator
from util.console import console

# Start program
console.info("Starting program")

# Read each PDF file
for pdf_file_path in ["./pdf/Yum.pdf"]:
    # for pdf_file_path in getPDFFilePathGenerator("./pdf/"):
    # Name of result word file
    result_word_file_name = " ".join(os.path.split(pdf_file_path)[-1].split(".")[0:-1]) + ".docx"
    result_word_file_path = "./result/" + result_word_file_name
    console.info("Processing on " + result_word_file_name)

    # Summon a word file for saving the result
    shutil.copy("./CoE Template.docx", result_word_file_path)

    # Get checking result, and write to word file
    result_dict = checkDocument(pdf_file_path)

    # Write result to doc
    writeResultToWord(result_word_file_path, result_dict)

    # Finishing one PDF file
    console.ok("Finished " + result_word_file_name)
