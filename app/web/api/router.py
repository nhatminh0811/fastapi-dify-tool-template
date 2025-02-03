import os
import uuid
import logging
import traceback
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.schemas.request_schema import GenerateQuizz
from app.repositories.generate_quiz import process_file
from app.repositories.generate_lession import process_lession_file
from app.repositories.mindmap_generator import process_mindmap 
from app.repositories.generate_presentation import process_file_to_pptx

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

api_router = APIRouter()

UPLOAD_FOLDER = "./uploads/"
OUTPUT_FOLDER = "./outputs/"

# Đảm bảo thư mục tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {".docx", ".pdf", ".pptx"}  # Hỗ trợ các định dạng file


def is_allowed_file(filename):
    """Kiểm tra xem file có thuộc định dạng hỗ trợ không"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@api_router.post("/generate_text")
async def generate_text_endpoint(file: UploadFile = File(...), num_questions: int = 5):
    """Tạo câu hỏi từ file và trả về file PDF"""
    try:
        secure_filename = f"{uuid.uuid4()}_{file.filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, secure_filename)

        # Lưu file
        with open(upload_path, "wb") as buffer:
            buffer.write(await file.read())

        # Tạo file PDF output
        output_filename = f"{os.path.splitext(secure_filename)[0]}_questions.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Xử lý file
        process_file(upload_path, num_questions, output_path)

        return FileResponse(path=output_path, filename=output_filename, media_type="application/pdf")

    except Exception as e:
        logging.error(f"Error processing text file: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@api_router.post("/generate_lession")
async def generate_lesson_endpoint(file: UploadFile = File(...)):
    """Create lesson content from an uploaded file and return a PDF."""
    try:
        if not is_allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Only .docx, .pdf, and .pptx files are supported.")

        secure_filename = f"{uuid.uuid4()}_{file.filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, secure_filename)

        # Save file to the upload directory
        with open(upload_path, "wb") as buffer:
            buffer.write(await file.read())

        # Generate PDF output
        output_filename = f"{os.path.splitext(secure_filename)[0]}_lesson.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        generated_pdf = process_lession_file(upload_path, output_path)
        if not generated_pdf:
            raise HTTPException(status_code=500, detail="Failed to process the file.")

        return FileResponse(path=generated_pdf, filename=output_filename, media_type="application/pdf")

    except HTTPException as http_err:
        logging.error(f"Client Error: {http_err.detail}")
        raise http_err

    except Exception as e:
        logging.error(f"Error processing lesson file: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@api_router.post("/generate_mindmap")
async def generate_mindmap_endpoint(file: UploadFile = File(...)):
    """Nhận file input, xử lý bằng Gemini AI và trả về mindmap Markdown."""
    try:
        logging.info(f"Received file: {file.filename}")

        if not is_allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Only .docx, .pdf, and .pptx files are supported.")

        # Lưu file tải lên
        secure_filename = f"{uuid.uuid4()}_{file.filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, secure_filename)

        with open(upload_path, "wb") as buffer:
            buffer.write(await file.read())

        logging.info(f"File saved to {upload_path}")

        # Tạo file output Markdown
        output_md = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(secure_filename)[0]}.md")

        # Gọi hàm xử lý mindmap
        result = process_mindmap(upload_path, output_md)

        if "Error" in result:
            logging.error(f"Mindmap processing failed: {result}")
            raise HTTPException(status_code=500, detail="Failed to process the mindmap.")

        logging.info(f"Mindmap successfully generated: {output_md}")

        return FileResponse(path=output_md, filename=f"{os.path.splitext(file.filename)[0]}.md", media_type="text/markdown")

    except Exception as e:
        logging.error(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")


@api_router.post("/generate_presentation")
async def generate_presentation_endpoint(file: UploadFile = File(...)):
    """Tạo bài thuyết trình từ file input và trả về file PowerPoint"""
    try:
        if not is_allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Only .docx, .pdf, and .pptx files are supported.")

        # Tạo tên file an toàn và đường dẫn lưu
        secure_filename = f"{uuid.uuid4()}_{file.filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, secure_filename)

        # Lưu file tải lên
        with open(upload_path, "wb") as buffer:
            buffer.write(await file.read())

        logging.info(f"File saved to {upload_path}")

        # Tạo file PowerPoint đầu ra
        output_filename = f"{os.path.splitext(secure_filename)[0]}_presentation.pptx"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Gọi hàm xử lý file để tạo PowerPoint
        # Gọi phiên bản mới của process_file_to_pptx có xử lý hình ảnh
        process_file_to_pptx(input_path=upload_path, output_path=output_path)

        logging.info(f"Presentation successfully generated: {output_path}")

        # Trả về file PowerPoint đã tạo
        return FileResponse(
            path=output_path,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    except HTTPException as http_err:
        logging.error(f"Client Error: {http_err.detail}")
        raise http_err

    except Exception as e:
        logging.error(f"Error processing presentation file: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
