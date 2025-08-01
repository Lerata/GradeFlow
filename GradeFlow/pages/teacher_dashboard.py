import streamlit as st
import plotly.express as px
import pandas as pd
from utils.database import get_papers_for_review, get_system_stats
from utils.auth import get_current_user

def render_teacher_dashboard():
    """Render teacher dashboard"""
    user = get_current_user()
    st.title("👩‍🏫 Teacher Dashboard")
    st.markdown(f"Welcome back, **{user['name']}**!")
    
    # Quick stats for teacher
    stats = get_system_stats()
    papers_for_review = get_papers_for_review(10)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Papers to Review", len(papers_for_review))
    
    with col2:
        st.metric("Total Pending", stats.get('pending_reviews', 0))
    
    with col3:
        st.metric("Completed Today", 0)  # Would track daily completions
    
    with col4:
        st.metric("Average Score", "78.5%")  # Would calculate from reviewed papers
    
    # Main action areas
    st.subheader("📋 Today's Tasks")
    
    tab1, tab2, tab3 = st.tabs(["Priority Reviews", "Recent Uploads", "My Progress"])
    
    with tab1:
        st.markdown("### 🔥 High Priority Papers")
        
        if papers_for_review:
            for i, paper in enumerate(papers_for_review[:5]):  # Show top 5
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{paper['student_name'] or 'Unknown Student'}**")
                        st.caption(f"ID: {paper['student_id'] or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Subject:** {paper['subject'] or 'General'}")
                        st.caption(f"Uploaded: {paper['uploaded_at'][:10]}")
                    
                    with col3:
                        confidence = paper.get('ocr_confidence', 0.8)
                        color = "green" if confidence > 0.8 else "orange" if confidence > 0.6 else "red"
                        st.write(f"**OCR**: {confidence:.1%}")
                        st.markdown(f"<div style='height:5px;background-color:{color};border-radius:3px;'></div>", 
                                  unsafe_allow_html=True)
                    
                    with col4:
                        if st.button(f"Review", key=f"review_{paper['id']}", use_container_width=True):
                            st.session_state.selected_paper_id = paper['id']
                            st.session_state.current_page = "review_papers"
                            st.rerun()
                
                st.divider()
        else:
            st.info("🎉 No papers pending review! Great job!")
    
    with tab2:
        st.markdown("### 📤 Recently Uploaded Papers")
        
        # Show recent papers in a more compact format
        if papers_for_review:
            recent_df = pd.DataFrame([
                {
                    'Student': paper['student_name'] or 'Unknown',
                    'Subject': paper['subject'] or 'General',
                    'Uploaded': paper['uploaded_at'][:16],
                    'OCR Quality': f"{paper.get('ocr_confidence', 0.8):.1%}",
                    'Status': paper['status'].title()
                }
                for paper in papers_for_review[:10]
            ])
            st.dataframe(recent_df, use_container_width=True)
        else:
            st.info("No recent uploads")
    
    with tab3:
        st.markdown("### 📈 My Review Progress")
        
        # Sample progress data (in real app, fetch from database)
        progress_data = {
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Papers Reviewed': [12, 18, 15, 22],
            'Average Time (min)': [8.5, 7.2, 6.8, 6.5]
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                x=progress_data['Week'],
                y=progress_data['Papers Reviewed'],
                title="Papers Reviewed per Week"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(
                x=progress_data['Week'],
                y=progress_data['Average Time (min)'],
                title="Average Review Time"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Start Reviewing", use_container_width=True):
            st.session_state.current_page = "review_papers"
            st.rerun()
    
    with col2:
        if st.button("📤 Upload Papers", use_container_width=True):
            st.session_state.current_page = "paper_upload"
            st.rerun()
    
    with col3:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = "grade_analytics"
            st.rerun()
    
    with col4:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Tips and notifications
    with st.expander("💡 Teaching Tips & Updates"):
        st.markdown("""
        **Recent Updates:**
        - New AI model deployed with 5% improved accuracy
        - Bulk review features now available
        - Mobile app coming soon!
        
        **Review Tips:**
        - Focus on papers with confidence scores below 70%
        - Use keyboard shortcuts: Ctrl+S to save, Ctrl+N for next paper
        - Add detailed feedback for disputed grades
        """)
    
    # Help section
    with st.expander("❓ Need Help?"):
        st.markdown("""
        **Common Tasks:**
        - **Review Papers**: Click "Start Reviewing" to begin grading papers
        - **Upload New Papers**: Use the upload section to add exam papers
        - **View Analytics**: Check grade distributions and performance metrics
        
        **Contact Support**: support@gradingsystem.edu
        """)
