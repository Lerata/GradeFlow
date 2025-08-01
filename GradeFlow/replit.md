# AI Grading System

## Overview

This is an AI-assisted centralized grading system built with Streamlit for government education departments. The system automates the grading of standardized exams using machine learning models combined with OCR technology for processing scanned exam papers. It provides role-based access for administrators, teachers, and students with features including paper upload, AI-powered grading, human review workflows, and comprehensive dashboards for system management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit-based web application with multi-page navigation
- **Page Structure**: Modular page system with separate files for different user roles (admin dashboard, teacher dashboard, student portal, paper upload, review interface)
- **Session Management**: Streamlit session state for user authentication and navigation state
- **UI Components**: Uses Plotly for data visualization and charts, PIL for image processing display

### Backend Architecture
- **Database Layer**: SQLite database with custom Python utilities for data operations
- **Authentication System**: Username/password authentication with SHA-256 hashing and role-based access control (admin, teacher, student)
- **OCR Processing**: EasyOCR integration for text extraction from scanned papers with image preprocessing using OpenCV
- **Grading Engine**: Machine learning-based grading using scikit-learn with TF-IDF vectorization and spaCy for natural language processing

### Data Storage Solutions
- **Primary Database**: SQLite with tables for users, papers, grades, and audit logs
- **File Storage**: Local file system for uploaded paper images
- **Configuration**: JSON-based rubric storage for different subjects (English, Science, Mathematics)
- **Caching**: Streamlit's caching system for ML models and heavy computations

### Authentication and Authorization
- **Authentication Method**: Session-based authentication with username/password
- **Password Security**: SHA-256 hashing for password storage
- **Role-Based Access**: Three-tier system (admin, teacher, student) with different interface access levels
- **Session Management**: Streamlit session state for maintaining user sessions

### ML/AI Components
- **OCR Pipeline**: EasyOCR for text extraction with image preprocessing (noise reduction, contrast enhancement, binary thresholding)
- **Grading Models**: TF-IDF vectorization with Random Forest regression for essay grading
- **Natural Language Processing**: spaCy integration for text analysis and feature extraction
- **Rubric System**: JSON-based scoring criteria with weighted scoring for different subjects

## External Dependencies

### Python Libraries
- **Streamlit**: Web application framework for the user interface
- **EasyOCR**: Optical character recognition for processing scanned papers
- **OpenCV (cv2)**: Image preprocessing and computer vision operations
- **scikit-learn**: Machine learning models and TF-IDF vectorization
- **spaCy**: Natural language processing and text analysis
- **Plotly**: Interactive data visualization and charts
- **PIL (Pillow)**: Image processing and manipulation
- **NumPy**: Numerical computing and array operations
- **Pandas**: Data manipulation and analysis

### Database
- **SQLite**: Embedded database for local data storage with no external database server required

### File Systems
- **Local Storage**: Direct file system access for uploaded images and configuration files
- **JSON Configuration**: Static JSON files for rubric and grading criteria storage

### Potential Future Integrations
- **Cloud Storage**: AWS S3 or Google Cloud Storage for scalable file storage
- **PostgreSQL**: Migration path for production database needs
- **Docker**: Containerization support mentioned in project requirements
- **Real-time Updates**: Socket.io integration for live system updates