import streamlit as st
import plotly.express as px
import pandas as pd
from utils.database import get_student_grades
from utils.auth import get_current_user

def render_student_portal():
    """Render student results portal"""
    user = get_current_user()
    st.title("🎓 Student Portal")
    st.markdown(f"Welcome, **{user['name']}**!")
    
    # Student ID input (in real system, this would be from user profile)
    student_id = st.text_input("Enter your Student ID:", value="STU001", help="Enter your official student ID to view results")
    
    if student_id:
        # Get student grades
        grades = get_student_grades(student_id)
        
        if grades:
            # Calculate summary statistics
            total_exams = len(set(f"{g['exam_id']}_{g['subject']}" for g in grades))
            avg_score = sum(g['final_score'] for g in grades if g['final_score']) / len(grades) if grades else 0
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Exams", total_exams)
            
            with col2:
                st.metric("Average Score", f"{avg_score:.1f}%")
            
            with col3:
                passed_exams = sum(1 for g in grades if g['final_score'] and g['final_score'] >= 60)
                st.metric("Passed Exams", passed_exams)
            
            with col4:
                latest_score = grades[0]['final_score'] if grades[0]['final_score'] else 0
                st.metric("Latest Score", f"{latest_score:.1f}%")
            
            # Results tabs
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Detailed Results", "📈 Performance Trends", "📝 Feedback"])
            
            with tab1:
                st.subheader("Grade Overview")
                
                # Grade distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    # Subject-wise performance
                    subject_scores = {}
                    for grade in grades:
                        subject = grade['subject']
                        if subject not in subject_scores:
                            subject_scores[subject] = []
                        if grade['final_score']:
                            subject_scores[subject].append(grade['final_score'])
                    
                    subject_avg = {subject: sum(scores)/len(scores) for subject, scores in subject_scores.items()}
                    
                    if subject_avg:
                        fig = px.bar(
                            x=list(subject_avg.keys()),
                            y=list(subject_avg.values()),
                            title="Average Score by Subject",
                            labels={'x': 'Subject', 'y': 'Average Score (%)'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Grade distribution
                    grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
                    for grade in grades:
                        if grade['final_score']:
                            score = grade['final_score']
                            if score >= 90:
                                grade_counts['A'] += 1
                            elif score >= 80:
                                grade_counts['B'] += 1
                            elif score >= 70:
                                grade_counts['C'] += 1
                            elif score >= 60:
                                grade_counts['D'] += 1
                            else:
                                grade_counts['F'] += 1
                    
                    if any(grade_counts.values()):
                        fig = px.pie(
                            values=list(grade_counts.values()),
                            names=list(grade_counts.keys()),
                            title="Grade Distribution"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.subheader("Detailed Results")
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    subjects = list(set(g['subject'] for g in grades if g['subject']))
                    selected_subject = st.selectbox("Filter by Subject:", ["All"] + subjects)
                
                with col2:
                    exam_ids = list(set(g['exam_id'] for g in grades if g['exam_id']))
                    selected_exam = st.selectbox("Filter by Exam:", ["All"] + exam_ids)
                
                # Filter grades
                filtered_grades = grades
                if selected_subject != "All":
                    filtered_grades = [g for g in filtered_grades if g['subject'] == selected_subject]
                if selected_exam != "All":
                    filtered_grades = [g for g in filtered_grades if g['exam_id'] == selected_exam]
                
                # Display results table
                if filtered_grades:
                    results_df = pd.DataFrame([
                        {
                            'Exam': grade['exam_id'],
                            'Subject': grade['subject'],
                            'Question': grade['question_number'],
                            'Score': f"{grade['final_score']:.1f}%" if grade['final_score'] else "Pending",
                            'AI Confidence': f"{grade['ai_confidence']:.1%}" if grade['ai_confidence'] else "N/A",
                            'Status': grade['status'].title(),
                            'Date': grade['uploaded_at'][:10]
                        }
                        for grade in filtered_grades
                    ])
                    st.dataframe(results_df, use_container_width=True)
                else:
                    st.info("No results match the selected filters")
            
            with tab3:
                st.subheader("Performance Trends")
                
                # Time series of scores
                if len(grades) > 1:
                    df = pd.DataFrame([
                        {
                            'Date': pd.to_datetime(grade['uploaded_at']),
                            'Score': grade['final_score'],
                            'Subject': grade['subject']
                        }
                        for grade in grades if grade['final_score']
                    ])
                    
                    if not df.empty:
                        fig = px.line(
                            df, 
                            x='Date', 
                            y='Score',
                            color='Subject',
                            title="Score Trends Over Time"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Performance summary
                    st.subheader("Performance Summary")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        best_subject = max(subject_avg.items(), key=lambda x: x[1]) if subject_avg else None
                        if best_subject:
                            st.success(f"**Best Subject**: {best_subject[0]} ({best_subject[1]:.1f}%)")
                    
                    with col2:
                        improvement_needed = min(subject_avg.items(), key=lambda x: x[1]) if subject_avg else None
                        if improvement_needed and improvement_needed[1] < 70:
                            st.warning(f"**Needs Improvement**: {improvement_needed[0]} ({improvement_needed[1]:.1f}%)")
                else:
                    st.info("More data needed to show trends")
            
            with tab4:
                st.subheader("Personalized Feedback")
                
                # Generate feedback based on performance
                if avg_score >= 85:
                    st.success("🌟 **Excellent Performance!** You're doing great across all subjects.")
                elif avg_score >= 70:
                    st.info("👍 **Good Performance!** Keep up the good work with some areas for improvement.")
                else:
                    st.warning("📈 **Improvement Needed** - Focus on study strategies and seek help when needed.")
                
                # Subject-specific feedback
                st.subheader("Subject-wise Recommendations")
                
                for subject, avg in subject_avg.items():
                    with st.expander(f"{subject} - {avg:.1f}%"):
                        if avg >= 85:
                            st.write("✅ Excellent understanding! Consider helping classmates or taking advanced topics.")
                        elif avg >= 70:
                            st.write("👍 Good grasp of concepts. Focus on practice problems and exam technique.")
                        else:
                            st.write("📚 Needs attention. Consider:")
                            st.write("- Review fundamental concepts")
                            st.write("- Practice more problems")
                            st.write("- Seek help from teachers or tutors")
                            st.write("- Form study groups")
                
                # Study tips
                with st.expander("💡 General Study Tips"):
                    st.markdown("""
                    **Effective Study Strategies:**
                    - Set specific study goals for each session
                    - Use active recall techniques (flashcards, practice tests)
                    - Take regular breaks (Pomodoro technique)
                    - Teach concepts to others to reinforce learning
                    - Stay organized with a study schedule
                    
                    **Before Exams:**
                    - Review past feedback and common mistakes
                    - Practice time management with mock exams
                    - Get adequate sleep and stay hydrated
                    - Arrive early and bring all necessary materials
                    """)
        
        else:
            st.info("No results found for this student ID. Please check your ID or contact your teacher.")
    
    # Appeal process information
    with st.expander("📝 Grade Appeal Process"):
        st.markdown("""
        **How to Appeal a Grade:**
        1. Review your paper and feedback carefully
        2. Gather supporting evidence if you believe there's an error
        3. Contact your teacher within 7 days of grade publication
        4. Submit a formal appeal form with your reasoning
        5. Wait for the review committee's decision
        
        **Valid Reasons for Appeal:**
        - Calculation errors in scoring
        - Misinterpretation of your answer
        - Technical issues during grading
        - Unfair application of grading criteria
        """)
