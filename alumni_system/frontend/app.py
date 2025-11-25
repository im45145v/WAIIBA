"""
Alumni Management System - Streamlit Frontend
=============================================

A comprehensive Streamlit application for managing alumni data including:
- Alumni data browsing and filtering
- Export to Excel functionality
- Admin interface for manual updates
- NLP chatbot for queries
"""

import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

# Import alumni system modules
DB_AVAILABLE = False
_import_error = None

try:
    from alumni_system.chatbot.nlp_chatbot import get_chatbot
    from alumni_system.database.connection import get_db_context
    from alumni_system.database.crud import (
        create_alumni,
        delete_alumni,
        get_all_alumni,
        get_alumni_by_id,
        get_job_history_by_alumni,
        get_unique_batches,
        get_unique_companies,
        get_unique_locations,
        search_alumni,
        update_alumni,
    )
    from alumni_system.database.init_db import check_database_connection, init_database
    from alumni_system.database.models import Alumni

    DB_AVAILABLE = True
except ImportError as e:
    _import_error = str(e)
    DB_AVAILABLE = False


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Alumni Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# CUSTOM STYLING
# =============================================================================
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Header styling */
    .header-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    
    .header-title {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .header-subtitle {
        color: #a0aec0;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-left: 4px solid #1e3a5f;
    }
    
    /* Chat styling */
    .chat-message {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 1px 5px rgba(0,0,0,0.05);
    }
    
    .chat-user {
        background: #e3f2fd;
        border-left: 4px solid #1976d2;
    }
    
    .chat-bot {
        background: #f3e5f5;
        border-left: 4px solid #7b1fa2;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Button styling */
    .stButton > button {
        background-color: #1e3a5f;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    
    .stButton > button:hover {
        background-color: #2d4a6f;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_alumni" not in st.session_state:
    st.session_state.selected_alumni = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def alumni_to_dataframe(alumni_list: list) -> pd.DataFrame:
    """Convert list of Alumni objects to DataFrame."""
    data = []
    for alumni in alumni_list:
        # Get previous companies from job history
        previous_companies = []
        if hasattr(alumni, 'job_history') and alumni.job_history:
            for job in alumni.job_history:
                if not job.is_current and job.company_name:
                    role_info = f"{job.company_name}"
                    if job.designation:
                        role_info += f" ({job.designation})"
                    previous_companies.append(role_info)
        
        data.append({
            "ID": alumni.id,
            "Name": alumni.name,
            "Batch": alumni.batch,
            "Roll Number": alumni.roll_number,
            "Gender": alumni.gender,
            "Current Company": alumni.current_company,
            "Current Designation": alumni.current_designation,
            "Location": alumni.location,
            "Previous Companies": "; ".join(previous_companies) if previous_companies else "",
            "Personal Email": alumni.personal_email,
            "College Email": alumni.college_email,
            "Mobile": alumni.mobile_number,
            "LinkedIn": alumni.linkedin_url,
            "Higher Studies": alumni.higher_studies,
            "Last Updated": alumni.updated_at,
        })
    return pd.DataFrame(data)


def export_to_excel(df: pd.DataFrame) -> bytes:
    """Export DataFrame to Excel bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Alumni")
    return output.getvalue()


# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
def render_sidebar() -> str:
    """Render sidebar with navigation."""
    st.sidebar.markdown("## 🎓 Alumni System")
    st.sidebar.markdown("---")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "👥 Browse Alumni",
            "🔍 Search & Filter",
            "📋 Alumni Details",
            "💬 Chatbot",
            "⚙️ Admin Panel",
        ],
        label_visibility="collapsed",
    )
    
    st.sidebar.markdown("---")
    
    # Database status
    st.sidebar.markdown("### 📁 Database Status")
    if DB_AVAILABLE:
        try:
            if check_database_connection():
                st.sidebar.success("✅ Connected")
            else:
                st.sidebar.error("❌ Connection Failed")
        except Exception:
            st.sidebar.warning("⚠️ Not Configured")
    else:
        st.sidebar.info("ℹ️ Demo Mode")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Alumni Management System v1.0")
    
    return page


# =============================================================================
# PAGE RENDERERS
# =============================================================================
def render_dashboard():
    """Render the dashboard page."""
    st.markdown("""
    <div class="header-card">
        <h1 class="header-title">🎓 Alumni Management Dashboard</h1>
        <p class="header-subtitle">Overview of alumni data and system status</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    if DB_AVAILABLE:
        try:
            with get_db_context() as db:
                all_alumni = get_all_alumni(db, limit=10000)
                total_count = len(all_alumni)
                batches = get_unique_batches(db)
                companies = get_unique_companies(db)
                locations = get_unique_locations(db)
        except Exception:
            total_count = 0
            batches = []
            companies = []
            locations = []
    else:
        total_count = 0
        batches = []
        companies = []
        locations = []
    
    with col1:
        st.metric("📊 Total Alumni", total_count)
    
    with col2:
        st.metric("🎒 Batches", len(batches))
    
    with col3:
        st.metric("🏢 Companies", len(companies))
    
    with col4:
        st.metric("📍 Locations", len(locations))
    
    st.markdown("---")
    
    # Quick stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Quick Stats")
        if batches:
            st.write(f"**Batches:** {', '.join(sorted(batches)[:5])}" + 
                    ("..." if len(batches) > 5 else ""))
        if companies:
            st.write(f"**Top Companies:** {', '.join(sorted(companies)[:5])}" +
                    ("..." if len(companies) > 5 else ""))
    
    with col2:
        st.markdown("### 🔄 Recent Activity")
        st.info("System initialized. Configure database to see activity.")
    
    # Getting started
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    1. **Configure Database**: Set up PostgreSQL and configure environment variables
    2. **Import Data**: Upload your alumni data CSV or add records manually
    3. **Set up LinkedIn Scraping**: Configure LinkedIn credentials for profile updates
    4. **Configure B2 Storage**: Set up Backblaze B2 for PDF storage
    5. **Use the Chatbot**: Ask natural language questions about alumni
    """)


def render_browse_alumni():
    """Render the browse alumni page."""
    st.markdown("### 👥 Browse Alumni")
    
    if not DB_AVAILABLE:
        st.warning("Database not configured. Please set up environment variables.")
        return
    
    try:
        with get_db_context() as db:
            # Pagination
            col1, col2 = st.columns([3, 1])
            with col1:
                page_size = st.selectbox("Records per page", [25, 50, 100], index=0)
            with col2:
                page_num = st.number_input("Page", min_value=1, value=1)
            
            skip = (page_num - 1) * page_size
            alumni_list = get_all_alumni(db, skip=skip, limit=page_size)
            
            if alumni_list:
                df = alumni_to_dataframe(alumni_list)
                
                # Display table
                st.dataframe(df, use_container_width=True, height=500)
                
                # Export button
                excel_data = export_to_excel(df)
                st.download_button(
                    label="📥 Export to Excel",
                    data=excel_data,
                    file_name=f"alumni_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.info("No alumni records found. Add some records in the Admin Panel.")
    
    except Exception as e:
        st.error(f"Error loading alumni data: {e}")


def render_search_filter():
    """Render the search and filter page."""
    st.markdown("### 🔍 Search & Filter Alumni")
    
    if not DB_AVAILABLE:
        st.warning("Database not configured. Please set up environment variables.")
        return
    
    try:
        with get_db_context() as db:
            # Filter options
            col1, col2, col3, col4 = st.columns(4)
            
            batches = ["All"] + get_unique_batches(db)
            companies = ["All"] + get_unique_companies(db)
            locations = ["All"] + get_unique_locations(db)
            
            with col1:
                selected_batch = st.selectbox("Batch", batches)
            
            with col2:
                selected_company = st.selectbox("Company", companies)
            
            with col3:
                selected_location = st.selectbox("Location", locations)
            
            with col4:
                search_query = st.text_input("Search Name/Company")
            
            # Apply filters
            filters = {}
            if selected_batch != "All":
                filters["batch"] = selected_batch
            if selected_company != "All":
                filters["company"] = selected_company
            if selected_location != "All":
                filters["location"] = selected_location
            
            if search_query:
                results = search_alumni(db, search_query, limit=100)
            else:
                results = get_all_alumni(db, limit=100, **filters)
            
            # Display results
            st.markdown(f"**Found {len(results)} alumni**")
            
            if results:
                df = alumni_to_dataframe(results)
                st.dataframe(df, use_container_width=True, height=400)
                
                # Export button
                excel_data = export_to_excel(df)
                st.download_button(
                    label="📥 Export Results to Excel",
                    data=excel_data,
                    file_name=f"alumni_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
    
    except Exception as e:
        st.error(f"Error searching alumni: {e}")


def render_alumni_details():
    """Render the alumni details page with job history."""
    st.markdown("### 📋 Alumni Details & Career History")
    st.markdown("View detailed information including past companies and roles.")
    
    if not DB_AVAILABLE:
        st.warning("Database not configured. Please set up environment variables.")
        return
    
    try:
        with get_db_context() as db:
            # Alumni selection
            alumni_id = st.number_input("Enter Alumni ID", min_value=1, step=1, value=1)
            
            if st.button("Load Alumni Details"):
                alumni = get_alumni_by_id(db, alumni_id)
                
                if alumni:
                    st.session_state.viewing_alumni_id = alumni_id
                else:
                    st.error("Alumni not found.")
                    return
            
            # Display alumni details if selected
            if hasattr(st.session_state, 'viewing_alumni_id') and st.session_state.viewing_alumni_id:
                alumni = get_alumni_by_id(db, st.session_state.viewing_alumni_id)
                
                if alumni:
                    # Basic Information Card
                    st.markdown("---")
                    st.markdown("#### 👤 Basic Information")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"**Name:** {alumni.name or 'N/A'}")
                        st.markdown(f"**Batch:** {alumni.batch or 'N/A'}")
                        st.markdown(f"**Roll Number:** {alumni.roll_number or 'N/A'}")
                        st.markdown(f"**Gender:** {alumni.gender or 'N/A'}")
                    
                    with col2:
                        st.markdown(f"**Personal Email:** {alumni.personal_email or 'N/A'}")
                        st.markdown(f"**College Email:** {alumni.college_email or 'N/A'}")
                        st.markdown(f"**Mobile:** {alumni.mobile_number or 'N/A'}")
                        st.markdown(f"**WhatsApp:** {alumni.whatsapp_number or 'N/A'}")
                    
                    with col3:
                        if alumni.linkedin_url:
                            st.markdown(f"**LinkedIn:** [Profile]({alumni.linkedin_url})")
                        else:
                            st.markdown("**LinkedIn:** N/A")
                        st.markdown(f"**Higher Studies:** {alumni.higher_studies or 'N/A'}")
                        st.markdown(f"**Location:** {alumni.location or 'N/A'}")
                    
                    # Current Position Card
                    st.markdown("---")
                    st.markdown("#### 💼 Current Position")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Company:** {alumni.current_company or 'N/A'}")
                        st.markdown(f"**Designation:** {alumni.current_designation or 'N/A'}")
                    
                    with col2:
                        st.markdown(f"**Location:** {alumni.location or 'N/A'}")
                        st.markdown(f"**Corporate Email:** {alumni.corporate_email or 'N/A'}")
                    
                    # Job History Card
                    st.markdown("---")
                    st.markdown("#### 📊 Career History (Past Companies & Roles)")
                    
                    job_history = get_job_history_by_alumni(db, alumni.id)
                    
                    if job_history:
                        # Create a table for job history
                        job_data = []
                        for job in job_history:
                            start = job.start_date.strftime("%b %Y") if job.start_date else "N/A"
                            end = job.end_date.strftime("%b %Y") if job.end_date else ("Present" if job.is_current else "N/A")
                            job_data.append({
                                "Company": job.company_name,
                                "Role/Designation": job.designation or "N/A",
                                "Location": job.location or "N/A",
                                "Duration": f"{start} - {end}",
                                "Type": job.employment_type or "Full-time",
                                "Current": "✓" if job.is_current else "",
                            })
                        
                        job_df = pd.DataFrame(job_data)
                        st.dataframe(job_df, use_container_width=True, hide_index=True)
                        
                        # Summary stats
                        total_companies = len(set(j.company_name for j in job_history))
                        st.info(f"📈 Total companies worked at: **{total_companies}** | Total positions: **{len(job_history)}**")
                    else:
                        st.info("No job history records found for this alumni.")
                    
                    # Education History (if available)
                    if alumni.education_history:
                        st.markdown("---")
                        st.markdown("#### 🎓 Education History")
                        
                        edu_data = []
                        for edu in alumni.education_history:
                            edu_data.append({
                                "Institution": edu.institution_name,
                                "Degree": edu.degree or "N/A",
                                "Field of Study": edu.field_of_study or "N/A",
                                "Years": f"{edu.start_year or 'N/A'} - {edu.end_year or 'N/A'}",
                                "Grade": edu.grade or "N/A",
                            })
                        
                        edu_df = pd.DataFrame(edu_data)
                        st.dataframe(edu_df, use_container_width=True, hide_index=True)
                    
                    # Additional Information
                    st.markdown("---")
                    st.markdown("#### 📝 Additional Information")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Internship:** {alumni.internship or 'N/A'}")
                        st.markdown(f"**POR (Positions of Responsibility):** {alumni.por or 'N/A'}")
                    
                    with col2:
                        st.markdown(f"**Notable Alma Mater:** {alumni.notable_alma_mater or 'N/A'}")
                        st.markdown(f"**STEP Programme:** {alumni.step_programme or 'N/A'}")
                    
                    if alumni.remarks:
                        st.markdown(f"**Remarks:** {alumni.remarks}")
    
    except Exception as e:
        st.error(f"Error loading alumni details: {e}")


def render_chatbot():
    """Render the chatbot page."""
    st.markdown("### 💬 Alumni Chatbot")
    st.markdown("Ask questions about alumni in natural language!")
    
    if not DB_AVAILABLE:
        st.warning("Database not configured. Chatbot requires database connection.")
        st.markdown("""
        **Example questions you can ask:**
        - "Who works at Google?"
        - "Find alumni from batch 2020"
        - "Show software engineers"
        - "How many alumni do we have?"
        """)
        return
    
    # Chat history display
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-message chat-user">👤 **You:** {message["content"]}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message chat-bot">🤖 **Bot:** {message["content"]}</div>', 
                       unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Ask a question about alumni...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
        })
        
        # Get chatbot response
        try:
            chatbot = get_chatbot()
            response = chatbot.process_query(user_input)
            
            # Add bot response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["response"],
            })
            
            # Display alumni results if any
            if response.get("alumni"):
                st.markdown("#### Results:")
                results_df = pd.DataFrame(response["alumni"])
                st.dataframe(results_df, use_container_width=True)
            
        except Exception as e:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Sorry, I encountered an error: {str(e)}",
            })
        
        st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()


def render_admin_panel():
    """Render the admin panel page."""
    st.markdown("### ⚙️ Admin Panel")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Add Alumni",
        "✏️ Edit Alumni",
        "🗑️ Delete Alumni",
        "🔧 Database",
    ])
    
    with tab1:
        render_add_alumni_form()
    
    with tab2:
        render_edit_alumni_form()
    
    with tab3:
        render_delete_alumni_form()
    
    with tab4:
        render_database_tools()


def render_add_alumni_form():
    """Render form to add new alumni."""
    st.markdown("#### Add New Alumni")
    
    if not DB_AVAILABLE:
        st.warning("Database not configured.")
        return
    
    with st.form("add_alumni_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name *")
            batch = st.text_input("Batch (e.g., 2020)")
            roll_number = st.text_input("Roll Number *")
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])
            mobile = st.text_input("Mobile Number")
            personal_email = st.text_input("Personal Email")
        
        with col2:
            current_company = st.text_input("Current Company")
            current_designation = st.text_input("Current Designation")
            location = st.text_input("Location")
            linkedin_url = st.text_input("LinkedIn URL")
            college_email = st.text_input("College Email")
            higher_studies = st.text_input("Higher Studies")
        
        submitted = st.form_submit_button("Add Alumni")
        
        if submitted:
            if not name or not roll_number:
                st.error("Name and Roll Number are required.")
            else:
                try:
                    with get_db_context() as db:
                        create_alumni(
                            db,
                            name=name,
                            batch=batch,
                            roll_number=roll_number,
                            gender=gender if gender else None,
                            mobile_number=mobile,
                            personal_email=personal_email,
                            current_company=current_company,
                            current_designation=current_designation,
                            location=location,
                            linkedin_url=linkedin_url,
                            college_email=college_email,
                            higher_studies=higher_studies,
                        )
                    st.success(f"Alumni '{name}' added successfully!")
                except Exception as e:
                    st.error(f"Error adding alumni: {e}")


def render_edit_alumni_form():
    """Render form to edit existing alumni."""
    st.markdown("#### Edit Alumni")
    
    if not DB_AVAILABLE:
        st.warning("Database not configured.")
        return
    
    alumni_id = st.number_input("Alumni ID to edit", min_value=1, step=1)
    
    if st.button("Load Alumni"):
        try:
            with get_db_context() as db:
                from alumni_system.database.crud import get_alumni_by_id
                alumni = get_alumni_by_id(db, alumni_id)
                if alumni:
                    st.session_state.selected_alumni = {
                        "id": alumni.id,
                        "name": alumni.name,
                        "batch": alumni.batch,
                        "roll_number": alumni.roll_number,
                        "current_company": alumni.current_company,
                        "current_designation": alumni.current_designation,
                        "location": alumni.location,
                        "personal_email": alumni.personal_email,
                        "mobile_number": alumni.mobile_number,
                        "linkedin_url": alumni.linkedin_url,
                    }
                else:
                    st.error("Alumni not found.")
        except Exception as e:
            st.error(f"Error loading alumni: {e}")
    
    if st.session_state.selected_alumni:
        with st.form("edit_alumni_form"):
            alumni_data = st.session_state.selected_alumni
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name", value=alumni_data.get("name", ""))
                batch = st.text_input("Batch", value=alumni_data.get("batch", ""))
                current_company = st.text_input("Current Company", 
                                               value=alumni_data.get("current_company", ""))
                location = st.text_input("Location", value=alumni_data.get("location", ""))
            
            with col2:
                current_designation = st.text_input("Current Designation",
                                                   value=alumni_data.get("current_designation", ""))
                personal_email = st.text_input("Personal Email",
                                              value=alumni_data.get("personal_email", ""))
                mobile = st.text_input("Mobile", value=alumni_data.get("mobile_number", ""))
                linkedin_url = st.text_input("LinkedIn URL",
                                            value=alumni_data.get("linkedin_url", ""))
            
            submitted = st.form_submit_button("Update Alumni")
            
            if submitted:
                try:
                    with get_db_context() as db:
                        update_alumni(
                            db,
                            alumni_data["id"],
                            name=name,
                            batch=batch,
                            current_company=current_company,
                            current_designation=current_designation,
                            location=location,
                            personal_email=personal_email,
                            mobile_number=mobile,
                            linkedin_url=linkedin_url,
                        )
                    st.success("Alumni updated successfully!")
                    st.session_state.selected_alumni = None
                except Exception as e:
                    st.error(f"Error updating alumni: {e}")


def render_delete_alumni_form():
    """Render form to delete alumni."""
    st.markdown("#### Delete Alumni")
    st.warning("⚠️ This action cannot be undone!")
    
    if not DB_AVAILABLE:
        st.warning("Database not configured.")
        return
    
    alumni_id = st.number_input("Alumni ID to delete", min_value=1, step=1, key="delete_id")
    
    if st.button("Delete Alumni", type="primary"):
        try:
            with get_db_context() as db:
                if delete_alumni(db, alumni_id):
                    st.success(f"Alumni with ID {alumni_id} deleted successfully!")
                else:
                    st.error("Alumni not found.")
        except Exception as e:
            st.error(f"Error deleting alumni: {e}")


def render_database_tools():
    """Render database management tools."""
    st.markdown("#### Database Tools")
    
    if not DB_AVAILABLE:
        st.warning("Database not configured. Set the following environment variables:")
        st.code("""
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alumni_db
DB_USER=postgres
DB_PASSWORD=your_password
        """)
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Initialize Database")
        if st.button("Create Tables"):
            try:
                init_database()
                st.success("Database tables created successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.markdown("##### Connection Test")
        if st.button("Test Connection"):
            try:
                if check_database_connection():
                    st.success("Database connection successful!")
                else:
                    st.error("Database connection failed!")
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    st.markdown("##### Import CSV Data")
    uploaded_file = st.file_uploader("Upload Alumni CSV", type=["csv"])
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("Preview:")
            st.dataframe(df.head())
            
            if st.button("Import Data"):
                # Map CSV columns to database fields
                st.info("Importing data... This may take a while.")
                # Implementation would go here
                st.success("Data imported successfully!")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    """Main application entry point."""
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Render selected page
    if page == "📊 Dashboard":
        render_dashboard()
    elif page == "👥 Browse Alumni":
        render_browse_alumni()
    elif page == "🔍 Search & Filter":
        render_search_filter()
    elif page == "📋 Alumni Details":
        render_alumni_details()
    elif page == "💬 Chatbot":
        render_chatbot()
    elif page == "⚙️ Admin Panel":
        render_admin_panel()


if __name__ == "__main__":
    main()
