"""
Main Entry Point - CutPDF Multi-Tool Platform
Hỗ trợ: Cut PDF, Convert PDF, GenQues KHTN, GenQues KHXH
"""
import sys
import os
from dotenv import load_dotenv
import multiprocessing
# Load environment variables
load_dotenv()

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("CutPDF Multi-Tool")
    app.setOrganizationName("EdMicro")
    app.setApplicationVersion("2.5")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if sys.platform == "win32":
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            pass
    main()
    