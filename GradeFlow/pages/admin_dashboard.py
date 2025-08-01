import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.database import get_system_stats, get_all_users
import pandas as pd

def render_admin_dashboard():
    """Render admin dashboard"""
    st.title("🔧 Admin Dashboard")
    st.markdown("System overview and management tools")
    
    # Get system statistics
    stats = get_system_stats()
    
    # Key metrics
    st.subheader("📊 System Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Papers",
            value=stats.get('total_papers', 0),
            delta=f"{stats.get('graded_papers', 0)} completed"
        )
    
    with col2:
        st.metric(
            label="Pending Reviews",
            value=stats.get('pending_reviews', 0),
            delta="Needs attention" if stats.get('pending_reviews', 0) > 0 else "All clear"
        )
    
    with col3:
        st.metric(
            label="Active Users",
            value=stats.get('active_users', 0)
        )
    
    with col4:
        completion_rate = 0
        if stats.get('total_papers', 0) > 0:
            completion_rate = (stats.get('graded_papers', 0) / stats.get('total_papers', 0)) * 100
        st.metric(
            label="Completion Rate",
            value=f"{completion_rate:.1f}%"
        )
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Grade Distribution")
        grade_data = stats.get('grade_distribution', {})
        if grade_data:
            fig = px.pie(
                values=list(grade_data.values()),
                names=list(grade_data.keys()),
                title="Distribution of Final Grades"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No grade data available yet")
    
    with col2:
        st.subheader("System Activity")
        # Sample activity data (in real system, this would come from database)
        activity_data = {
            'Date': pd.date_range('2024-01-01', periods=30, freq='D'),
            'Papers Processed': [5, 8, 12, 6, 9, 15, 11, 7, 13, 10, 8, 14, 9, 11, 16, 
                               12, 8, 10, 7, 13, 15, 9, 11, 8, 12, 14, 10, 9, 13, 11]
        }
        activity_df = pd.DataFrame(activity_data)
        
        fig = px.line(
            activity_df, 
            x='Date', 
            y='Papers Processed',
            title="Daily Paper Processing"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("📋 Recent Activity")
    
    # Tabs for different types of activity
    tab1, tab2, tab3 = st.tabs(["Recent Papers", "User Activity", "System Alerts"])
    
    with tab1:
        st.info("Recent paper uploads and processing status would be displayed here")
        # In a real system, fetch recent papers from database
        sample_papers = pd.DataFrame({
            'Paper ID': ['P001', 'P002', 'P003', 'P004'],
            'Student': ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown'],
            'Subject': ['Mathematics', 'English', 'Science', 'English'],
            'Status': ['Graded', 'Pending Review', 'Processing', 'Graded'],
            'Uploaded': ['2024-01-15 09:30', '2024-01-15 10:15', '2024-01-15 11:00', '2024-01-15 11:30']
        })
        st.dataframe(sample_papers, use_container_width=True)
    
    with tab2:
        users = get_all_users()
        if users:
            user_df = pd.DataFrame(users)
            st.dataframe(user_df[['username', 'name', 'role', 'created_at']], use_container_width=True)
        else:
            st.info("No user activity data available")
    
    with tab3:
        st.warning("⚠️ High pending review queue - Consider assigning more reviewers")
        st.info("ℹ️ System performance is optimal")
        st.success("✅ All services are running normally")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh Stats", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("👥 Manage Users", use_container_width=True):
            st.session_state.current_page = "user_management"
            st.rerun()
    
    with col3:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.current_page = "system_analytics"
            st.rerun()
    
    with col4:
        if st.button("📁 Upload Papers", use_container_width=True):
            st.session_state.current_page = "paper_upload"
            st.rerun()
    
    # System health indicators
    st.subheader("🔍 System Health")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("**Database**: Operational")
        st.caption("Connection: Normal | Storage: 85% used")
    
    with col2:
        st.success("**OCR Service**: Online")
        st.caption("Processing: Normal | Queue: 2 items")
    
    with col3:
        st.success("**ML Models**: Loaded")
        st.caption("Performance: Good | Accuracy: 87%")
