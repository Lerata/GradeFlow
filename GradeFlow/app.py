import streamlit as st
import os
from utils.auth import authenticate_user, logout_user, get_current_user
from utils.database import init_database
import pandas as pd

# Initialize database
init_database()

# Page configuration
st.set_page_config(
    page_title="AI Grading System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "login"

def main():
    # Authentication check
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_authenticated_app()

def show_login_page():
    st.title("🎓 AI-Assisted Grading System")
    st.markdown("### Secure Login Portal")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login", use_container_width=True)
            
            if login_button:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(f"Welcome, {user['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
        
        # Demo credentials
        st.info("Demo Credentials:\n\n"
                "**Admin**: admin/admin123\n\n"
                "**Teacher**: teacher/teacher123\n\n"
                "**Student**: student/student123")

def show_authenticated_app():
    user = st.session_state.user
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        st.write(f"Welcome, **{user['name']}**")
        st.write(f"Role: **{user['role'].title()}**")
        
        # Role-based navigation
        if user['role'] == 'admin':
            pages = {
                "Admin Dashboard": "admin_dashboard",
                "User Management": "user_management",
                "System Analytics": "system_analytics",
                "Paper Upload": "paper_upload"
            }
        elif user['role'] == 'teacher':
            pages = {
                "Teacher Dashboard": "teacher_dashboard",
                "Review Papers": "review_papers",
                "Upload Papers": "paper_upload",
                "Grade Analytics": "grade_analytics"
            }
        elif user['role'] == 'student':
            pages = {
                "My Results": "student_portal",
                "Grade History": "grade_history"
            }
        else:
            pages = {"Dashboard": "dashboard"}
        
        # Navigation buttons
        for page_name, page_key in pages.items():
            if st.button(page_name, use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    # Main content area
    current_page = st.session_state.current_page
    
    if current_page == "admin_dashboard":
        show_admin_dashboard()
    elif current_page == "teacher_dashboard":
        show_teacher_dashboard()
    elif current_page == "student_portal":
        show_student_portal()
    elif current_page == "paper_upload":
        show_paper_upload()
    elif current_page == "review_papers":
        show_review_papers()
    elif current_page == "user_management":
        show_user_management()
    elif current_page == "system_analytics":
        show_system_analytics()
    elif current_page == "grade_analytics":
        show_grade_analytics()
    elif current_page == "grade_history":
        show_grade_history()
    else:
        show_default_dashboard()

def show_admin_dashboard():
    from pages.admin_dashboard import render_admin_dashboard
    render_admin_dashboard()

def show_teacher_dashboard():
    from pages.teacher_dashboard import render_teacher_dashboard
    render_teacher_dashboard()

def show_student_portal():
    from pages.student_portal import render_student_portal
    render_student_portal()

def show_paper_upload():
    from pages.paper_upload import render_paper_upload
    render_paper_upload()

def show_review_papers():
    from pages.review_papers import render_review_papers
    render_review_papers()

def show_user_management():
    st.title("👥 User Management")
    st.info("User management functionality - Add, edit, and manage system users")
    
    tab1, tab2, tab3 = st.tabs(["All Users", "Add User", "Bulk Operations"])
    
    with tab1:
        # Display users table
        from utils.database import get_all_users
        users = get_all_users()
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df[['username', 'name', 'email', 'role', 'created_at']], use_container_width=True)
        else:
            st.info("No users found")
    
    with tab2:
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username")
                new_name = st.text_input("Full Name")
                new_email = st.text_input("Email")
            with col2:
                new_role = st.selectbox("Role", ["admin", "teacher", "student"])
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Add User"):
                if new_password == confirm_password:
                    from utils.database import create_user
                    if create_user(new_username, new_password, new_name, new_email, new_role):
                        st.success("User created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create user")
                else:
                    st.error("Passwords don't match")

def show_system_analytics():
    st.title("📊 System Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    from utils.database import get_system_stats
    stats = get_system_stats()
    
    with col1:
        st.metric("Total Papers", stats.get('total_papers', 0))
    with col2:
        st.metric("Graded Papers", stats.get('graded_papers', 0))
    with col3:
        st.metric("Pending Reviews", stats.get('pending_reviews', 0))
    with col4:
        st.metric("Active Users", stats.get('active_users', 0))
    
    # Charts and analytics
    st.subheader("Grade Distribution")
    grade_data = stats.get('grade_distribution', {})
    if grade_data:
        import plotly.express as px
        fig = px.bar(x=list(grade_data.keys()), y=list(grade_data.values()))
        st.plotly_chart(fig, use_container_width=True)

def show_grade_analytics():
    st.title("📈 Grade Analytics")
    st.info("Grade analytics and performance metrics for teachers")

def show_grade_history():
    st.title("📚 Grade History")
    st.info("Historical grade information for students")

def show_default_dashboard():
    st.title("🎓 AI Grading System Dashboard")
    st.write("Welcome to the AI-assisted grading system!")

if __name__ == "__main__":
    main()
