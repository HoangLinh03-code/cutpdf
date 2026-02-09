# 🚀 CutPdfByDrive - Intelligent Education Platform

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green?style=for-the-badge&logo=qt&logoColor=white)
![VertexAI](https://img.shields.io/badge/AI-Google%20Vertex-orange?style=for-the-badge&logo=googlecloud&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

**CutPdfByDrive** is a premier "All-in-One" desktop solution designed specifically for educators and content creators. harnessing the power of **Google Gemini 2.5 Pro** and **PyQt5**, it streamlines the workflow of digitizing, processing, and generating high-quality educational materials.

---

## 🌟 Key Features

The platform is divided into four specialized modules, each serving a critical role in the document processing pipeline:

### 1. ✂️ **Cut PDF (Smart Segmentation)**
*Precision document splitting enhanced by AI.*
- **🤖 Intelligent Analysis**: Utilizes Google Vertex AI to understand document structure and Table of Contents.
- **📄 Auto-Split**: Automatically segments large PDFs into individual lessons or chapters with accurate naming.
- **📊 Structural Reports**: Generates detailed Excel reports of the document's organization.
- **☁️ Cloud Integration**: Direct import and processing from **Google Drive**.

### 2. 🔄 **Convert PDF (Advanced Conversion)**
*Transform documents with high fidelity.*
- **📝 PDF to Markdown**: Converts complex PDFs to Markdown, preserving **MathJax** formulas.
- **📄 PDF to DOCX**: Exports to Microsoft Word with professional formatting.
- **🧠 Mathpix & OCR Integration**: Industry-leading recognition for handwritten notes and complex mathematical equations.
- **⚡ High-Speed Batching**: Process hundreds of files simultaneously.

### 3. & 4. 📝 **GenQues (AI Question Generation)**
*Specialized modules for Natural Sciences (KHTN) & Social Sciences (KHXH).*
Conforms to the **2025 Education Standards**, supporting 4 key question types:
- **✅ Multiple Choice**: Auto-generation of distractors.
- **⚖️ True/False**: Complex proposition evaluation.
- **✍️ Short Answer**: Fill-in-the-blank and concise response generation.
- **📝 Essay**: In-depth essay questions with detailed grading guides.

#### **Advanced Capabilities:**
| Feature | Description |
| :--- | :--- |
| **🚀 Multi-threading** | Concurrent processing of multiple files (customizable threads). |
| **📂 Smart Grouping** | Automatically groups cut files into lesson units for comprehensive question generation. |
| **🎨 Live Preview** | Instant visual preview of generated DOCX files within the app. |
| **🔧 Custom Prompts** | Full control over AI prompts to tailor output styles and difficulty. |

---

## 🏗️ System Architecture

A modular architecture ensures stability and extensibility.

```
d:\CheckTool\OneInAll\cutpdf\
├── ui/                         # User Interface Layer (PyQt5)
│   ├── main_window.py          # Core Application Window
│   ├── cut_pdf_widget.py       # PDF Segmentation Interface
│   ├── convert_pdf_widget.py   # Conversion Interface
│   ├── gen_ques.py             # Base Class for GenQues Modules
│   ├── genques_khtn_widget.py  # Natural Sciences Module
│   └── genques_khxh_widget.py  # Social Sciences Module
├── modules/                    # Business Logic Layer
│   ├── common/                 # Shared Utilities (OCR, Image Proc)
│   ├── khtn/                   # KHTN Logic Implementation
│   └── khxh/                   # KHXH Logic Implementation
├── config/                     # Configuration & Secrets
├── output/                     # Generated Artifacts
└── main.py                     # Application Entry Point
```

---

## 📋 System Requirements

| Component | Recommendation |
| :--- | :--- |
| **OS** | Windows 10 / 11 |
| **Python** | Version 3.8 or higher |
| **RAM** | 8GB+ recommended for batch processing |
| **Cloud APIs** | **Google Cloud** (Vertex AI, Drive), **Mathpix** (Optional) |

---

## 🚀 Installation & Setup

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Configure Credentials**
To enable AI and Cloud features, configure your API keys:
1.  **Google Cloud**: Place your `service_account.json` or `client_secret.json` in the root directory.
2.  **Environment Variables**: Rename `.env.example` to `.env` and populate necessary keys (e.g., Mathpix).

### **3. Launch Application**
```bash
python main.py
```

---

## 📖 Quick Start Guide

### **Generating Questions (GenQues)**
1.  **Select Source**: Drag & drop PDF lesson files (or folders). The system auto-groups them by lesson.
2.  **Configure**:
    -   Select desired question types (MCQ, T/F, Short Answer, Essay).
    -   (Optional) Customize the prompt for specific requirements.
3.  **Process**:
    -   Set **Worker Threads** (Default: 3).
    -   Click **"Start Processing"**.
4.  **Review**:
    -   Access generated files in the **Results** tab.
    -   Preview content instantly or open in Microsoft Word.

---

## 📄 License
**Internal Use Only**. All rights reserved.
Developed for internal educational content production.

---

<p align="center">
  <i>Built with ❤️ for Education</i>
</p>

