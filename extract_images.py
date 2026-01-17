import os
from pypdf import PdfReader

def extract_images(pdf_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    reader = PdfReader(pdf_path)
    count = 0

    for page_num, page in enumerate(reader.pages):
        for image_file_object in page.images:
            try:
                with open(os.path.join(output_dir, f"page_{page_num+1}_{image_file_object.name}"), "wb") as fp:
                    fp.write(image_file_object.data)
                count += 1
                print(f"Extracted: page_{page_num+1}_{image_file_object.name}")
            except Exception as e:
                print(f"Error extracting image on page {page_num+1}: {e}")

    print(f"Total images extracted: {count}")

if __name__ == "__main__":
    pdf_path = "documents/ALEA DL Manual.pdf"
    output_dir = "images"
    extract_images(pdf_path, output_dir)
