import streamlit as st
from PIL import Image
import io
import os
from utils.ocr_processor import process_exam_paper, validate_paper_quality
from utils.grading_engine import grade_answer
from utils.database import save_paper, save_grade
from utils.auth import get_current_user

def render_paper_upload():
    """Render paper upload and processing interface"""
    st.title("📤 Paper Upload & Processing")
    st.markdown("Upload exam papers for AI-assisted grading")
    
    user = get_current_user()
    
    # Upload interface
    tab1, tab2, tab3 = st.tabs(["Single Upload", "Batch Upload", "Processing Queue"])
    
    with tab1:
        st.subheader("📄 Single Paper Upload")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an exam paper image",
            type=['png', 'jpg', 'jpeg', 'pdf'],
            help="Supported formats: PNG, JPG, JPEG, PDF"
        )
        
        if uploaded_file:
            # Display image
            try:
                if uploaded_file.type == "application/pdf":
                    st.warning("PDF processing requires additional setup. Please upload image files (PNG, JPG) for now.")
                    return
                
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Paper", use_column_width=True)
                
                # Image quality validation
                quality_check = validate_paper_quality(image)
                
                if quality_check["valid"]:
                    st.success(f"✅ Image quality: {quality_check['reason']}")
                else:
                    st.error(f"❌ Image quality issue: {quality_check['reason']}")
                    st.info("💡 Try improving image lighting, focus, or resolution")
                
                # Paper information form
                with st.form("paper_info_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        exam_id = st.text_input("Exam ID", value="EXAM2024_001")
                        subject = st.selectbox("Subject", ["Mathematics", "English", "Science", "History", "Geography"])
                    
                    with col2:
                        student_id = st.text_input("Student ID (if known)", help="Leave empty if to be extracted from paper")
                        student_name = st.text_input("Student Name (if known)", help="Leave empty if to be extracted from paper")
                    
                    process_button = st.form_submit_button("🔄 Process Paper", use_container_width=True)
                    
                    if process_button:
                        if quality_check["valid"]:
                            process_single_paper(image, exam_id, subject, student_id, student_name, user['id'])
                        else:
                            st.error("Please upload a better quality image before processing")
            
            except Exception as e:
                st.error(f"Error loading image: {str(e)}")
    
    with tab2:
        st.subheader("📁 Batch Upload")
        st.info("Batch upload functionality - Upload multiple papers at once")
        
        # Multiple file uploader
        uploaded_files = st.file_uploader(
            "Choose multiple exam papers",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Select multiple image files for batch processing"
        )
        
        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} files")
            
            # Batch processing options
            col1, col2 = st.columns(2)
            with col1:
                batch_exam_id = st.text_input("Batch Exam ID", value="BATCH2024_001")
                batch_subject = st.selectbox("Batch Subject", ["Mathematics", "English", "Science", "History", "Geography"], key="batch_subject")
            
            with col2:
                auto_process = st.checkbox("Auto-process all papers", value=True)
                notify_completion = st.checkbox("Send notification when complete", value=True)
            
            if st.button("🚀 Start Batch Processing", use_container_width=True):
                process_batch_papers(uploaded_files, batch_exam_id, batch_subject, user['id'], auto_process)
    
    with tab3:
        st.subheader("⏳ Processing Queue")
        st.info("View the status of papers being processed")
        
        # Mock processing queue (in real system, this would come from database)
        import pandas as pd
        
        queue_data = {
            'Paper ID': ['P001', 'P002', 'P003'],
            'Student': ['John Doe', 'Jane Smith', 'Processing...'],
            'Subject': ['Mathematics', 'English', 'Science'],
            'Status': ['Completed', 'Grading', 'OCR Processing'],
            'Progress': ['100%', '75%', '25%'],
            'Uploaded': ['10:30 AM', '10:45 AM', '11:00 AM']
        }
        
        df = pd.DataFrame(queue_data)
        st.dataframe(df, use_container_width=True)
        
        # Queue controls
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Queue"):
                st.rerun()
        with col2:
            if st.button("⏸️ Pause Processing"):
                st.info("Processing paused")
        with col3:
            if st.button("🗑️ Clear Completed"):
                st.success("Cleared completed items")

def process_single_paper(image, exam_id, subject, student_id, student_name, uploaded_by):
    """Process a single paper through the complete pipeline"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: OCR Processing
        status_text.text("🔍 Performing OCR...")
        progress_bar.progress(20)
        
        processing_result = process_exam_paper(image)
        
        if "error" in processing_result:
            st.error(f"OCR Error: {processing_result['error']}")
            return
        
        progress_bar.progress(40)
        
        # Extract student info if not provided
        if not student_id and processing_result["student_info"]["student_id"]:
            student_id = processing_result["student_info"]["student_id"]
        if not student_name and processing_result["student_info"]["name"]:
            student_name = processing_result["student_info"]["name"]
        
        # Step 2: Save paper to database
        status_text.text("💾 Saving paper...")
        progress_bar.progress(50)
        
        paper_id = save_paper(
            student_id or "UNKNOWN",
            student_name or "Unknown Student",
            exam_id,
            subject,
            processing_result["raw_text"],
            processing_result["ocr_confidence"],
            "",  # image_path - would save to storage in real system
            uploaded_by
        )
        
        # Step 3: Grade answers
        status_text.text("🤖 AI Grading in progress...")
        progress_bar.progress(70)
        
        answers = processing_result["answers"]
        grades = []
        
        for answer in answers:
            grade_result = grade_answer(answer["answer_text"], answer["question_number"])
            
            if "error" not in grade_result:
                # Save grade to database
                grade_id = save_grade(
                    paper_id,
                    grade_result["question_number"],
                    grade_result["grade"]["percentage"],
                    grade_result["confidence"],
                    grade_result["subject"],
                    str(grade_result),  # JSON string of full results
                    uploaded_by
                )
                grades.append(grade_result)
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        
        # Display results
        st.success("Paper processed successfully!")
        
        # Show OCR results
        with st.expander("🔍 OCR Results"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Extracted Text:**")
                st.text_area("", processing_result["raw_text"], height=200, disabled=True)
            with col2:
                st.write("**Student Information:**")
                st.write(f"**ID:** {student_id or 'Not found'}")
                st.write(f"**Name:** {student_name or 'Not found'}")
                st.write(f"**OCR Confidence:** {processing_result['ocr_confidence']:.1%}")
        
        # Show grading results
        with st.expander("🎓 Grading Results"):
            for i, grade in enumerate(grades):
                st.write(f"**Question {grade['question_number']}:**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Score", f"{grade['grade']['percentage']:.1f}%")
                with col2:
                    st.metric("Grade", grade['grade']['letter_grade'])
                with col3:
                    st.metric("Confidence", f"{grade['confidence']:.1%}")
                
                # Show suggestions
                if grade.get('suggestions'):
                    st.write("**Improvement Suggestions:**")
                    for suggestion in grade['suggestions']:
                        st.write(f"• {suggestion}")
                
                st.divider()
    
    except Exception as e:
        st.error(f"Processing error: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Processing failed")

def process_batch_papers(uploaded_files, exam_id, subject, uploaded_by, auto_process):
    """Process multiple papers in batch"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(uploaded_files)
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            status_text.text(f"Processing {uploaded_file.name} ({i+1}/{total_files})")
            progress_bar.progress((i + 1) / total_files)
            
            # Load and process image
            image = Image.open(uploaded_file)
            quality_check = validate_paper_quality(image)
            
            if not quality_check["valid"]:
                results.append({
                    'file': uploaded_file.name,
                    'status': 'Failed',
                    'reason': quality_check["reason"]
                })
                continue
            
            # Process paper
            processing_result = process_exam_paper(image)
            
            if "error" in processing_result:
                results.append({
                    'file': uploaded_file.name,
                    'status': 'Failed',
                    'reason': processing_result["error"]
                })
                continue
            
            # Save to database
            paper_id = save_paper(
                processing_result["student_info"]["student_id"] or f"AUTO_{i+1:03d}",
                processing_result["student_info"]["name"] or f"Student {i+1}",
                exam_id,
                subject,
                processing_result["raw_text"],
                processing_result["ocr_confidence"],
                "",
                uploaded_by
            )
            
            if auto_process:
                # Grade answers
                for answer in processing_result["answers"]:
                    grade_result = grade_answer(answer["answer_text"], answer["question_number"])
                    if "error" not in grade_result:
                        save_grade(
                            paper_id,
                            grade_result["question_number"],
                            grade_result["grade"]["percentage"],
                            grade_result["confidence"],
                            grade_result["subject"],
                            str(grade_result),
                            uploaded_by
                        )
            
            results.append({
                'file': uploaded_file.name,
                'status': 'Success',
                'paper_id': paper_id
            })
        
        except Exception as e:
            results.append({
                'file': uploaded_file.name,
                'status': 'Error',
                'reason': str(e)
            })
    
    # Show batch results
    st.success(f"Batch processing complete! Processed {len(results)} files.")
    
    # Results summary
    success_count = sum(1 for r in results if r['status'] == 'Success')
    failed_count = len(results) - success_count
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Successful", success_count)
    with col2:
        st.metric("Failed", failed_count)
    
    # Detailed results
    with st.expander("📋 Detailed Results"):
        import pandas as pd
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)
