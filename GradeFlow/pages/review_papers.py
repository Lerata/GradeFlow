import streamlit as st
from utils.database import get_papers_for_review, get_grades_by_paper, update_grade_score, update_paper_status
from utils.auth import get_current_user
import json
from PIL import Image
import io

def render_review_papers():
    """Render paper review interface for teachers"""
    st.title("📝 Review Papers")
    st.markdown("Review AI-graded papers and provide human oversight")
    
    user = get_current_user()
    
    # Get papers for review
    papers = get_papers_for_review(50)
    
    if not papers:
        st.info("🎉 No papers pending review! All caught up!")
        return
    
    # Paper selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(f"📋 Papers Pending Review ({len(papers)})")
    
    with col2:
        if st.button("🔄 Refresh List", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    subjects = list(set(p['subject'] for p in papers if p['subject']))
    with col1:
        selected_subject = st.selectbox("Filter by Subject:", ["All"] + subjects)
    
    with col2:
        confidence_filter = st.selectbox("OCR Confidence:", ["All", "High (>80%)", "Medium (60-80%)", "Low (<60%)"])
    
    with col3:
        sort_by = st.selectbox("Sort by:", ["Upload Date", "OCR Confidence", "Student Name"])
    
    # Apply filters
    filtered_papers = papers
    if selected_subject != "All":
        filtered_papers = [p for p in filtered_papers if p['subject'] == selected_subject]
    
    if confidence_filter != "All":
        if confidence_filter == "High (>80%)":
            filtered_papers = [p for p in filtered_papers if p.get('ocr_confidence', 0) > 0.8]
        elif confidence_filter == "Medium (60-80%)":
            filtered_papers = [p for p in filtered_papers if 0.6 <= p.get('ocr_confidence', 0) <= 0.8]
        else:  # Low
            filtered_papers = [p for p in filtered_papers if p.get('ocr_confidence', 0) < 0.6]
    
    # Paper selection interface
    if 'selected_paper_id' not in st.session_state:
        st.session_state.selected_paper_id = None
    
    # Display papers list
    st.subheader("Select Paper to Review:")
    
    for paper in filtered_papers[:10]:  # Show first 10
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1, 1])
            
            with col1:
                st.write(f"**{paper['student_name'] or 'Unknown Student'}**")
                st.caption(f"ID: {paper['student_id'] or 'N/A'}")
            
            with col2:
                st.write(f"**Subject:** {paper['subject'] or 'General'}")
                st.caption(f"Exam: {paper['exam_id'] or 'N/A'}")
            
            with col3:
                confidence = paper.get('ocr_confidence', 0.8)
                confidence_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                st.write(f"{confidence_color} OCR: {confidence:.1%}")
                st.caption(f"Uploaded: {paper['uploaded_at'][:10]}")
            
            with col4:
                priority = "🔥 High" if confidence < 0.7 else "📝 Normal"
                st.write(priority)
            
            with col5:
                if st.button("Review", key=f"select_{paper['id']}", use_container_width=True):
                    st.session_state.selected_paper_id = paper['id']
                    st.rerun()
        
        st.divider()
    
    # Review interface for selected paper
    if st.session_state.selected_paper_id:
        selected_paper = next((p for p in papers if p['id'] == st.session_state.selected_paper_id), None)
        
        if selected_paper:
            render_paper_review_interface(selected_paper, user)

def render_paper_review_interface(paper, user):
    """Render the detailed review interface for a selected paper"""
    
    st.markdown("---")
    st.subheader(f"📝 Reviewing: {paper['student_name'] or 'Unknown Student'}")
    
    # Paper information
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Student ID", paper['student_id'] or 'Unknown')
    with col2:
        st.metric("Subject", paper['subject'] or 'General')
    with col3:
        st.metric("OCR Confidence", f"{paper.get('ocr_confidence', 0.8):.1%}")
    with col4:
        st.metric("Upload Date", paper['uploaded_at'][:10])
    
    # Get grades for this paper
    grades = get_grades_by_paper(paper['id'])
    
    # Main review interface
    tab1, tab2, tab3 = st.tabs(["📄 Paper Content", "🎓 Grade Review", "💬 Comments & Feedback"])
    
    with tab1:
        st.subheader("Original Text (OCR Extracted)")
        
        # Display raw text
        if paper['raw_text']:
            st.text_area("Extracted Text:", paper['raw_text'], height=300, disabled=True)
        else:
            st.info("No extracted text available")
        
        # OCR quality indicators
        col1, col2 = st.columns(2)
        with col1:
            confidence = paper.get('ocr_confidence', 0.8)
            if confidence > 0.8:
                st.success("✅ High OCR quality - Text extraction reliable")
            elif confidence > 0.6:
                st.warning("⚠️ Medium OCR quality - Review text carefully")
            else:
                st.error("❌ Low OCR quality - Manual verification recommended")
        
        with col2:
            text_length = len(paper['raw_text']) if paper['raw_text'] else 0
            st.info(f"📊 Text Statistics: {text_length} characters, ~{text_length//5} words")
    
    with tab2:
        st.subheader("AI Grading Results & Review")
        
        if grades:
            for i, grade in enumerate(grades):
                with st.expander(f"Question {grade['question_number']} - Current Score: {grade['ai_score']:.1f}%", expanded=True):
                    
                    # Parse grading details
                    try:
                        grading_details = json.loads(grade['grading_details']) if grade['grading_details'] else {}
                    except:
                        grading_details = {}
                    
                    # Display AI analysis
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**AI Analysis:**")
                        st.metric("AI Score", f"{grade['ai_score']:.1f}%")
                        st.metric("Confidence", f"{grade['ai_confidence']:.1%}")
                        st.metric("Subject Classification", grading_details.get('subject', 'Unknown'))
                        
                        # Show grade breakdown if available
                        if grading_details.get('grade', {}).get('breakdown'):
                            st.write("**Score Breakdown:**")
                            for criterion, scores in grading_details['grade']['breakdown'].items():
                                st.write(f"• {criterion.title()}: {scores['score']:.1f}/{scores['max_score']}")
                    
                    with col2:
                        st.write("**Human Review:**")
                        
                        # Current human score
                        current_human_score = grade['human_score'] if grade['human_score'] else grade['ai_score']
                        
                        # Score adjustment
                        new_score = st.slider(
                            "Adjust Score:",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(current_human_score),
                            step=0.5,
                            key=f"score_{grade['id']}"
                        )
                        
                        # Review comments
                        review_comments = st.text_area(
                            "Review Comments:",
                            placeholder="Add comments about the grading decision...",
                            key=f"comments_{grade['id']}"
                        )
                        
                        # Quick action buttons
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            if st.button("✅ Approve AI", key=f"approve_{grade['id']}", use_container_width=True):
                                update_grade_score(grade['id'], grade['ai_score'], user['id'], "Approved AI grading")
                                st.success("Grade approved!")
                                st.rerun()
                        
                        with col_b:
                            if st.button("💾 Save Changes", key=f"save_{grade['id']}", use_container_width=True):
                                update_grade_score(grade['id'], new_score, user['id'], review_comments)
                                st.success("Changes saved!")
                                st.rerun()
                        
                        with col_c:
                            if st.button("🚩 Flag Issue", key=f"flag_{grade['id']}", use_container_width=True):
                                st.warning("Issue flagged for supervisor review")
                    
                    # Show AI suggestions if available
                    if grading_details.get('suggestions'):
                        st.write("**AI Improvement Suggestions:**")
                        for suggestion in grading_details['suggestions']:
                            st.write(f"• {suggestion}")
                    
                    # Agreement indicator
                    if grade['human_score']:
                        ai_score = grade['ai_score']
                        human_score = grade['human_score']
                        difference = abs(ai_score - human_score)
                        
                        if difference <= 5:
                            st.success(f"✅ Good AI-Human Agreement (±{difference:.1f}%)")
                        elif difference <= 10:
                            st.warning(f"⚠️ Moderate AI-Human Difference (±{difference:.1f}%)")
                        else:
                            st.error(f"❌ Large AI-Human Difference (±{difference:.1f}%)")
        else:
            st.info("No grades found for this paper. The paper may need to be processed first.")
            
            if st.button("🔄 Process Paper Now"):
                st.info("Processing functionality would be called here")
    
    with tab3:
        st.subheader("Overall Comments & Feedback")
        
        # Overall paper review
        overall_comments = st.text_area(
            "Overall Paper Comments:",
            placeholder="Provide general feedback about the paper quality, student performance, etc.",
            height=150
        )
        
        # Paper status update
        col1, col2 = st.columns(2)
        
        with col1:
            new_status = st.selectbox(
                "Update Paper Status:",
                ["pending", "reviewed", "completed", "flagged"],
                index=0
            )
        
        with col2:
            if st.button("💾 Update Paper Status", use_container_width=True):
                if update_paper_status(paper['id'], new_status):
                    st.success(f"Paper status updated to: {new_status}")
                    # If completed, move to next paper
                    if new_status == "completed":
                        st.session_state.selected_paper_id = None
                        st.rerun()
                else:
                    st.error("Failed to update paper status")
        
        # Reviewer notes
        st.subheader("Reviewer Notes")
        reviewer_notes = st.text_area(
            "Private Notes (visible to other reviewers):",
            placeholder="Add any notes for other reviewers or supervisors...",
            height=100
        )
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("⬅️ Previous Paper", use_container_width=True):
                # Logic to select previous paper
                st.info("Previous paper functionality")
        
        with col2:
            if st.button("➡️ Next Paper", use_container_width=True):
                # Logic to select next paper
                st.info("Next paper functionality")
        
        with col3:
            if st.button("📋 Back to List", use_container_width=True):
                st.session_state.selected_paper_id = None
                st.rerun()
        
        with col4:
            if st.button("✅ Complete Review", use_container_width=True):
                update_paper_status(paper['id'], "completed")
                st.success("Review completed!")
                st.session_state.selected_paper_id = None
                st.rerun()
    
    # Keyboard shortcuts help
    with st.expander("⌨️ Keyboard Shortcuts"):
        st.markdown("""
        - **Ctrl + Enter**: Save current changes
        - **Ctrl + →**: Next paper
        - **Ctrl + ←**: Previous paper
        - **Ctrl + A**: Approve current grade
        - **Escape**: Back to paper list
        """)
