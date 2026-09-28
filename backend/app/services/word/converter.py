import os
import tempfile
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def convert_docx_bytes_to_pdf_bytes(docx_bytes: bytes) -> Optional[bytes]:
    """
    Converts DOCX binary bytes to PDF binary bytes using Microsoft Word COM on Windows,
    with safe temporary file handling, clean COM dispatch release, and guaranteed
    resource cleanup in a finally block.
    """
    if not docx_bytes:
        return None

    temp_dir = tempfile.gettempdir()
    unique_id = f"{int(time.time() * 1000)}_{os.getpid()}"
    temp_docx = os.path.join(temp_dir, f"temp_bill_{unique_id}.docx")
    temp_pdf = os.path.join(temp_dir, f"temp_bill_{unique_id}.pdf")

    try:
        with open(temp_docx, "wb") as f:
            f.write(docx_bytes)

        # Attempt Microsoft Word COM export
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        try:
            doc_com = word.Documents.Open(temp_docx)
            # wdFormatPDF = 17
            doc_com.SaveAs(temp_pdf, FileFormat=17)
            doc_com.Close(SaveChanges=0)
        finally:
            word.Quit()
            pythoncom.CoUninitialize()

        if os.path.exists(temp_pdf):
            with open(temp_pdf, "rb") as f:
                return f.read()
        return None
    except Exception as e:
        logger.warning(f"Word COM PDF conversion failed: {e}.")
        return None
    finally:
        # Guarantee cleanup of temporary files on both success and failure
        for temp_file in (temp_docx, temp_pdf):
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

