"""
Comprehensive Assessment System Components for EdAgent Streamlit Frontend
Implements complete assessment workflow with API integration, state management, and visualization.
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import time

from streamlit_api_client import EnhancedEdAgentAPI, AssessmentSession
from streamlit_session_manager import SessionManager


class AssessmentManager:
    """Manages assessment state and workflow"""
    
    def __init__(self, api_client: EnhancedEdAgentAPI, session_manager: SessionManager):
        self.api = api_client
        self.session_manager = session_manager
        self.session_key_prefix = "assessment_"
    
    def get_current_assessment(self) -> Optional[AssessmentSession]:
        """Get current assessment session from state"""
        return st.session_state.get(f"{self.session_key_prefix}current")
    
    def set_current_assessment(self, assessment: Optional[AssessmentSession]) -> None:
        """Set current assessment session in state"""
        st.session_state[f"{self.session_key_prefix}current"] = assessment
    
    def get_assessment_history(self) -> List[Dict[str, Any]]:
        """Get assessment history from state"""
        return st.session_state.get(f"{self.session_key_prefix}history", [])
    
    def set_assessment_history(self, history: List[Dict[str, Any]]) -> None:
        """Set assessment history in state"""
        st.session_state[f"{self.session_key_prefix}history"] = history
    
    def get_assessment_responses(self) -> Dict[int, str]:
        """Get current assessment responses"""
        return st.session_state.get(f"{self.session_key_prefix}responses", {})
    
    def set_assessment_response(self, question_index: int, response: str) -> None:
        """Set response for specific question"""
        responses = self.get_assessment_responses()
        responses[question_index] = response
        st.session_state[f"{self.session_key_prefix}responses"] = responses
    
    def clear_assessment_state(self) -> None:
        """Clear current assessment state"""
        keys_to_clear = [
            f"{self.session_key_prefix}current",
            f"{self.session_key_prefix}responses",
            f"{self.session_key_prefix}start_time"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_assessment_start_time(self) -> Optional[datetime]:
        """Get assessment start time"""
        return st.session_state.get(f"{self.session_key_prefix}start_time")
    
    def set_assessment_start_time(self, start_time: datetime) -> None:
        """Set assessment start time"""
        st.session_state[f"{self.session_key_prefix}start_time"] = start_time


def render_assessment_dashboard(api_client: EnhancedEdAgentAPI, session_manager: SessionManager) -> None:
    """
    Render the main assessment dashboard with history and quick start options
    """
    st.header("📊 Skill Assessment Dashboard")
    
    if not session_manager.is_authenticated():
        st.warning("🔐 Please log in to access skill assessments.")
        return
    
    user_info = session_manager.get_current_user()
    assessment_manager = AssessmentManager(api_client, session_manager)
    
    # Load assessment history if not already loaded
    if "assessment_history_loaded" not in st.session_state:
        with st.spinner("Loading assessment history..."):
            try:
                history = asyncio.run(api_client.get_user_assessments(user_info.user_id))
                assessment_manager.set_assessment_history(history)
                st.session_state.assessment_history_loaded = True
            except Exception as e:
                st.error(f"Failed to load assessment history: {str(e)}")
                assessment_manager.set_assessment_history([])
                st.session_state.assessment_history_loaded = True
    
    # Main dashboard layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_assessment_history_section(assessment_manager)
    
    with col2:
        render_quick_assessment_section(assessment_manager, user_info.user_id)
    
    st.divider()
    
    # Current assessment section
    current_assessment = assessment_manager.get_current_assessment()
    if current_assessment:
        render_active_assessment_section(assessment_manager, user_info.user_id)
    else:
        render_assessment_categories_section(assessment_manager, user_info.user_id)


def render_assessment_history_section(assessment_manager: AssessmentManager) -> None:
    """Render assessment history with visualization and progress tracking"""
    st.subheader("📈 Assessment History")
    
    history = assessment_manager.get_assessment_history()
    
    if not history:
        st.info("No assessment history found. Take your first assessment to get started!")
        return
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Recent Assessments", "📊 Progress Charts", "🎯 Skill Levels"])
    
    with tab1:
        render_recent_assessments_table(history)
    
    with tab2:
        render_assessment_progress_charts(history)
    
    with tab3:
        render_skill_level_visualization(history)


def render_recent_assessments_table(history: List[Dict[str, Any]]) -> None:
    """Render table of recent assessments with actions"""
    if not history:
        st.info("No assessments completed yet.")
        return
    
    # Convert to DataFrame for better display
    df_data = []
    for assessment in history[-10:]:  # Show last 10
        df_data.append({
            "Skill Area": assessment.get("skill_area", "Unknown").title(),
            "Status": assessment.get("status", "Unknown").title(),
            "Score": f"{assessment.get('overall_score', 0):.1f}%" if assessment.get('overall_score') else "N/A",
            "Level": assessment.get("overall_level", "Unknown").title(),
            "Date": assessment.get("completed_at", assessment.get("started_at", "Unknown"))[:10] if assessment.get("completed_at") or assessment.get("started_at") else "Unknown",
            "Duration": f"{assessment.get('duration_minutes', 0):.0f} min" if assessment.get('duration_minutes') else "N/A"
        })
    
    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Action buttons for recent assessments
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 View Detailed Results", key="view_detailed_results"):
                st.info("Detailed results view coming soon!")
        
        with col2:
            if st.button("🔄 Retake Assessment", key="retake_assessment"):
                st.info("Select a skill area below to retake an assessment.")
        
        with col3:
            if st.button("📤 Export History", key="export_history"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"assessment_history_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )


def render_assessment_progress_charts(history: List[Dict[str, Any]]) -> None:
    """Render progress charts and analytics"""
    if len(history) < 2:
        st.info("Take more assessments to see progress trends!")
        return
    
    # Prepare data for charts
    skill_progress = {}
    dates = []
    
    for assessment in history:
        skill_area = assessment.get("skill_area", "Unknown")
        date = assessment.get("completed_at", assessment.get("started_at"))
        score = assessment.get("overall_score", 0)
        
        if date and score:
            if skill_area not in skill_progress:
                skill_progress[skill_area] = {"dates": [], "scores": []}
            
            skill_progress[skill_area]["dates"].append(date[:10])
            skill_progress[skill_area]["scores"].append(score)
            dates.append(date[:10])
    
    if skill_progress:
        # Progress over time chart
        fig = go.Figure()
        
        for skill, data in skill_progress.items():
            fig.add_trace(go.Scatter(
                x=data["dates"],
                y=data["scores"],
                mode='lines+markers',
                name=skill.title(),
                line=dict(width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="Assessment Score Progress Over Time",
            xaxis_title="Date",
            yaxis_title="Score (%)",
            yaxis=dict(range=[0, 100]),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_score = sum(assessment.get("overall_score", 0) for assessment in history) / len(history)
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col2:
            completed_assessments = len([a for a in history if a.get("status") == "completed"])
            st.metric("Completed Assessments", completed_assessments)
        
        with col3:
            unique_skills = len(set(a.get("skill_area") for a in history))
            st.metric("Skills Assessed", unique_skills)


def render_skill_level_visualization(history: List[Dict[str, Any]]) -> None:
    """Render skill level radar chart and breakdown"""
    if not history:
        st.info("No skill data available.")
        return
    
    # Get latest assessment for each skill
    latest_skills = {}
    for assessment in history:
        skill_area = assessment.get("skill_area", "Unknown")
        if skill_area not in latest_skills or assessment.get("completed_at", "") > latest_skills[skill_area].get("completed_at", ""):
            latest_skills[skill_area] = assessment
    
    if latest_skills:
        # Create radar chart
        skills = list(latest_skills.keys())
        scores = [latest_skills[skill].get("overall_score", 0) for skill in skills]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=[skill.title() for skill in skills],
            fill='toself',
            name='Current Level',
            line_color='rgb(0, 123, 255)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Current Skill Levels"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Skill breakdown table
        st.subheader("Skill Level Breakdown")
        
        breakdown_data = []
        for skill, assessment in latest_skills.items():
            level_map = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴", "expert": "🟣"}
            level = assessment.get("overall_level", "beginner")
            
            breakdown_data.append({
                "Skill": skill.title(),
                "Level": f"{level_map.get(level, '⚪')} {level.title()}",
                "Score": f"{assessment.get('overall_score', 0):.1f}%",
                "Last Assessed": assessment.get("completed_at", "Unknown")[:10] if assessment.get("completed_at") else "Unknown"
            })
        
        if breakdown_data:
            df = pd.DataFrame(breakdown_data)
            st.dataframe(df, use_container_width=True)


def render_quick_assessment_section(assessment_manager: AssessmentManager, user_id: str) -> None:
    """Render quick assessment start section"""
    st.subheader("🚀 Quick Assessment")
    
    # Popular skill areas
    popular_skills = [
        "Python Programming",
        "JavaScript",
        "Data Science",
        "Machine Learning",
        "Web Development",
        "SQL & Databases",
        "Cloud Computing",
        "DevOps",
        "Project Management",
        "Digital Marketing"
    ]
    
    selected_skill = st.selectbox(
        "Choose a skill to assess:",
        popular_skills,
        key="quick_skill_select"
    )
    
    # Assessment type selection
    assessment_type = st.radio(
        "Assessment Type:",
        ["Quick (5 questions)", "Standard (10 questions)", "Comprehensive (15 questions)"],
        key="assessment_type_select"
    )
    
    # Estimated time display
    time_estimates = {
        "Quick (5 questions)": "5-10 minutes",
        "Standard (10 questions)": "10-15 minutes", 
        "Comprehensive (15 questions)": "15-25 minutes"
    }
    
    st.info(f"⏱️ Estimated time: {time_estimates[assessment_type]}")
    
    if st.button("Start Assessment", type="primary", key="start_quick_assessment"):
        start_assessment_session(assessment_manager, user_id, selected_skill.lower(), assessment_type)


def render_assessment_categories_section(assessment_manager: AssessmentManager, user_id: str) -> None:
    """Render assessment categories with detailed options"""
    st.subheader("🎯 Assessment Categories")
    
    # Define assessment categories
    categories = {
        "💻 Programming & Development": {
            "skills": ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript"],
            "description": "Assess your programming language proficiency and coding skills"
        },
        "🌐 Web Development": {
            "skills": ["HTML/CSS", "React", "Vue.js", "Angular", "Node.js", "Django", "Flask"],
            "description": "Evaluate your web development and framework knowledge"
        },
        "📊 Data & Analytics": {
            "skills": ["Data Science", "Machine Learning", "SQL", "Pandas", "NumPy", "Tableau", "Power BI"],
            "description": "Test your data analysis and machine learning capabilities"
        },
        "☁️ Cloud & Infrastructure": {
            "skills": ["AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform", "DevOps"],
            "description": "Assess your cloud computing and infrastructure skills"
        },
        "💼 Business & Management": {
            "skills": ["Project Management", "Agile", "Scrum", "Leadership", "Strategy", "Analytics"],
            "description": "Evaluate your business and management competencies"
        },
        "🎨 Design & Creative": {
            "skills": ["UI/UX Design", "Graphic Design", "Adobe Creative Suite", "Figma", "Sketch"],
            "description": "Test your design and creative skills"
        }
    }
    
    # Render categories
    for category, info in categories.items():
        with st.expander(category, expanded=False):
            st.write(info["description"])
            
            # Create skill buttons
            cols = st.columns(3)
            for i, skill in enumerate(info["skills"]):
                with cols[i % 3]:
                    if st.button(f"📝 {skill}", key=f"assess_{skill.lower().replace('/', '_').replace(' ', '_')}"):
                        start_assessment_session(assessment_manager, user_id, skill.lower(), "Standard (10 questions)")


def start_assessment_session(assessment_manager: AssessmentManager, user_id: str, skill_area: str, assessment_type: str) -> None:
    """Start a new assessment session"""
    with st.spinner(f"Starting {skill_area} assessment..."):
        try:
            # Start assessment via API
            assessment_session = asyncio.run(assessment_manager.api.start_assessment(user_id, skill_area))
            
            if assessment_session:
                # Store assessment in state
                assessment_manager.set_current_assessment(assessment_session)
                assessment_manager.set_assessment_start_time(datetime.now())
                assessment_manager.clear_assessment_state()  # Clear previous responses
                
                st.success(f"✅ Started {skill_area} assessment!")
                st.info(f"📋 Assessment Type: {assessment_type}")
                st.rerun()
            else:
                st.error("Failed to start assessment. Please try again.")
                
        except Exception as e:
            st.error(f"Error starting assessment: {str(e)}")


def render_active_assessment_section(assessment_manager: AssessmentManager, user_id: str) -> None:
    """Render active assessment interface with questions and progress"""
    st.header("📝 Active Assessment")
    
    current_assessment = assessment_manager.get_current_assessment()
    if not current_assessment:
        st.error("No active assessment found.")
        return
    
    # Assessment header with progress
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"🎯 {current_assessment.skill_area.title()} Assessment")
    
    with col2:
        progress = current_assessment.progress
        st.metric("Progress", f"{progress:.0%}")
    
    with col3:
        start_time = assessment_manager.get_assessment_start_time()
        if start_time:
            elapsed = datetime.now() - start_time
            st.metric("Time Elapsed", f"{elapsed.seconds // 60}m {elapsed.seconds % 60}s")
    
    # Progress bar
    st.progress(progress)
    
    # Question display and response
    if current_assessment.questions:
        render_assessment_questions(assessment_manager, current_assessment, user_id)
    else:
        st.warning("No questions available for this assessment.")
        if st.button("End Assessment", key="end_empty_assessment"):
            assessment_manager.clear_assessment_state()
            st.rerun()


def render_assessment_questions(assessment_manager: AssessmentManager, assessment: AssessmentSession, user_id: str) -> None:
    """Render assessment questions with response handling"""
    current_index = assessment.current_question_index
    total_questions = len(assessment.questions)
    
    if current_index >= total_questions:
        # Assessment completed
        render_assessment_completion(assessment_manager, assessment.id, user_id)
        return
    
    current_question = assessment.questions[current_index]
    responses = assessment_manager.get_assessment_responses()
    
    # Question display
    st.markdown(f"### Question {current_index + 1} of {total_questions}")
    st.markdown(f"**{current_question.get('question', 'Question not available')}**")
    
    question_type = current_question.get('type', 'open')
    
    # Handle different question types
    if question_type == 'multiple_choice':
        render_multiple_choice_question(assessment_manager, current_question, current_index, responses)
    elif question_type == 'rating':
        render_rating_question(assessment_manager, current_question, current_index, responses)
    elif question_type == 'boolean':
        render_boolean_question(assessment_manager, current_question, current_index, responses)
    else:
        render_open_question(assessment_manager, current_question, current_index, responses)
    
    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if current_index > 0:
            if st.button("⬅️ Previous", key="prev_question"):
                # Move to previous question (update assessment state)
                assessment.current_question_index = max(0, current_index - 1)
                assessment_manager.set_current_assessment(assessment)
                st.rerun()
    
    with col2:
        if st.button("💾 Save Progress", key="save_progress"):
            save_assessment_progress(assessment_manager, assessment.id, current_index, responses.get(current_index, ""))
    
    with col3:
        if current_index < total_questions - 1:
            if st.button("Next ➡️", key="next_question"):
                # Submit current response and move to next
                current_response = responses.get(current_index, "")
                if current_response.strip():
                    submit_assessment_response(assessment_manager, assessment.id, current_response, current_index, user_id)
                else:
                    st.warning("Please provide a response before continuing.")
        else:
            if st.button("🏁 Complete Assessment", key="complete_assessment", type="primary"):
                current_response = responses.get(current_index, "")
                if current_response.strip():
                    submit_assessment_response(assessment_manager, assessment.id, current_response, current_index, user_id, complete=True)
                else:
                    st.warning("Please provide a response before completing the assessment.")
    
    with col4:
        if st.button("❌ Cancel Assessment", key="cancel_assessment"):
            if st.session_state.get("confirm_cancel", False):
                assessment_manager.clear_assessment_state()
                st.success("Assessment cancelled.")
                st.rerun()
            else:
                st.session_state.confirm_cancel = True
                st.warning("⚠️ Click again to confirm cancellation")
                st.rerun()


def render_multiple_choice_question(assessment_manager: AssessmentManager, question: Dict[str, Any], index: int, responses: Dict[int, str]) -> None:
    """Render multiple choice question"""
    options = question.get('options', [])
    if not options:
        st.error("No options available for this question.")
        return
    
    current_response = responses.get(index, "")
    selected_index = None
    
    if current_response and current_response in options:
        selected_index = options.index(current_response)
    
    selected_option = st.radio(
        "Select your answer:",
        options,
        index=selected_index,
        key=f"mc_question_{index}"
    )
    
    if selected_option:
        assessment_manager.set_assessment_response(index, selected_option)


def render_rating_question(assessment_manager: AssessmentManager, question: Dict[str, Any], index: int, responses: Dict[int, str]) -> None:
    """Render rating scale question"""
    current_response = responses.get(index, "")
    current_value = 5
    
    if current_response and current_response.isdigit():
        current_value = int(current_response)
    
    rating = st.slider(
        "Rate your proficiency (1 = Beginner, 10 = Expert):",
        min_value=1,
        max_value=10,
        value=current_value,
        key=f"rating_question_{index}"
    )
    
    assessment_manager.set_assessment_response(index, str(rating))
    
    # Show rating description
    rating_descriptions = {
        1: "No experience",
        2: "Very basic knowledge",
        3: "Some exposure",
        4: "Basic understanding",
        5: "Moderate proficiency",
        6: "Good working knowledge",
        7: "Strong proficiency",
        8: "Very strong skills",
        9: "Expert level",
        10: "Master level"
    }
    
    st.info(f"**{rating}/10**: {rating_descriptions.get(rating, 'Unknown level')}")


def render_boolean_question(assessment_manager: AssessmentManager, question: Dict[str, Any], index: int, responses: Dict[int, str]) -> None:
    """Render yes/no question"""
    current_response = responses.get(index, "")
    
    answer = st.radio(
        "Your answer:",
        ["Yes", "No"],
        index=0 if current_response == "Yes" else (1 if current_response == "No" else None),
        key=f"bool_question_{index}"
    )
    
    if answer:
        assessment_manager.set_assessment_response(index, answer)


def render_open_question(assessment_manager: AssessmentManager, question: Dict[str, Any], index: int, responses: Dict[int, str]) -> None:
    """Render open-ended question"""
    current_response = responses.get(index, "")
    
    response = st.text_area(
        "Your answer:",
        value=current_response,
        height=150,
        placeholder="Please provide a detailed answer...",
        key=f"open_question_{index}"
    )
    
    if response != current_response:
        assessment_manager.set_assessment_response(index, response)
    
    # Character count
    char_count = len(response)
    if char_count < 50:
        st.warning(f"Consider providing more detail ({char_count} characters)")
    else:
        st.success(f"Good response length ({char_count} characters)")


def submit_assessment_response(assessment_manager: AssessmentManager, assessment_id: str, response: str, question_index: int, user_id: str, complete: bool = False) -> None:
    """Submit assessment response to API"""
    with st.spinner("Submitting response..."):
        try:
            # Submit response via API
            updated_assessment = asyncio.run(
                assessment_manager.api.submit_assessment_response(assessment_id, response)
            )
            
            if updated_assessment:
                # Update local state
                assessment_manager.set_current_assessment(updated_assessment)
                
                if complete:
                    # Complete the assessment
                    complete_assessment_session(assessment_manager, assessment_id, user_id)
                else:
                    st.success("✅ Response submitted!")
                    st.rerun()
            else:
                st.error("Failed to submit response. Please try again.")
                
        except Exception as e:
            st.error(f"Error submitting response: {str(e)}")


def save_assessment_progress(assessment_manager: AssessmentManager, assessment_id: str, current_index: int, current_response: str) -> None:
    """Save current assessment progress"""
    try:
        # Save current response
        if current_response.strip():
            assessment_manager.set_assessment_response(current_index, current_response)
        
        st.success("💾 Progress saved!")
        time.sleep(1)  # Brief pause to show success message
        
    except Exception as e:
        st.error(f"Error saving progress: {str(e)}")


def complete_assessment_session(assessment_manager: AssessmentManager, assessment_id: str, user_id: str) -> None:
    """Complete assessment and show results"""
    with st.spinner("Completing assessment and generating results..."):
        try:
            # Complete assessment via API
            results = asyncio.run(assessment_manager.api.complete_assessment(assessment_id))
            
            if results:
                # Clear current assessment state
                assessment_manager.clear_assessment_state()
                
                # Refresh assessment history
                history = asyncio.run(assessment_manager.api.get_user_assessments(user_id))
                assessment_manager.set_assessment_history(history)
                
                # Show results
                render_assessment_results(results)
                
                st.success("🎉 Assessment completed successfully!")
                st.balloons()
                
            else:
                st.error("Failed to complete assessment. Please try again.")
                
        except Exception as e:
            st.error(f"Error completing assessment: {str(e)}")


def render_assessment_completion(assessment_manager: AssessmentManager, assessment_id: str, user_id: str) -> None:
    """Render assessment completion interface"""
    st.success("🎉 Assessment Complete!")
    st.write("You have answered all questions. Click below to get your results.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Get Results", type="primary", key="get_results"):
            complete_assessment_session(assessment_manager, assessment_id, user_id)
    
    with col2:
        if st.button("🔄 Review Answers", key="review_answers"):
            # Allow user to review their answers
            st.info("Review functionality coming soon!")


def render_assessment_results(results: Dict[str, Any]) -> None:
    """Render detailed assessment results"""
    st.header("📊 Assessment Results")
    
    # Overall results
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        overall_score = results.get("overall_score", 0)
        st.metric("Overall Score", f"{overall_score:.1f}%")
    
    with col2:
        overall_level = results.get("overall_level", "Unknown")
        level_colors = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴", "expert": "🟣"}
        st.metric("Skill Level", f"{level_colors.get(overall_level, '⚪')} {overall_level.title()}")
    
    with col3:
        confidence_score = results.get("confidence_score", 0)
        st.metric("Confidence", f"{confidence_score:.1%}")
    
    with col4:
        skill_area = results.get("skill_area", "Unknown")
        st.metric("Skill Area", skill_area.title())
    
    # Detailed breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💪 Strengths")
        strengths = results.get("strengths", [])
        if strengths:
            for strength in strengths:
                st.write(f"✅ {strength}")
        else:
            st.info("No specific strengths identified.")
    
    with col2:
        st.subheader("🎯 Areas for Improvement")
        weaknesses = results.get("weaknesses", [])
        if weaknesses:
            for weakness in weaknesses:
                st.write(f"📈 {weakness}")
        else:
            st.info("No specific areas for improvement identified.")
    
    # Recommendations
    st.subheader("📚 Personalized Recommendations")
    recommendations = results.get("recommendations", [])
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")
    else:
        st.info("No specific recommendations available.")
    
    # Detailed scores breakdown
    detailed_scores = results.get("detailed_scores", {})
    if detailed_scores:
        st.subheader("📊 Detailed Score Breakdown")
        
        # Create bar chart
        categories = list(detailed_scores.keys())
        scores = list(detailed_scores.values())
        
        fig = px.bar(
            x=categories,
            y=scores,
            title="Score by Category",
            labels={"x": "Category", "y": "Score (%)"},
            color=scores,
            color_continuous_scale="RdYlGn"
        )
        
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retake Assessment", key="retake_from_results"):
            st.info("Select the same skill area from the dashboard to retake.")
    
    with col2:
        if st.button("📚 Find Learning Resources", key="find_resources"):
            st.info("Learning resource recommendations coming soon!")
    
    with col3:
        if st.button("📤 Share Results", key="share_results"):
            results_summary = f"""
Assessment Results - {skill_area.title()}
Overall Score: {overall_score:.1f}%
Skill Level: {overall_level.title()}
Date: {datetime.now().strftime('%Y-%m-%d')}
            """
            st.download_button(
                label="Download Summary",
                data=results_summary,
                file_name=f"assessment_results_{skill_area}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )


def render_assessment_retry_interface(assessment_manager: AssessmentManager, user_id: str) -> None:
    """Render interface for retrying assessments"""
    st.subheader("🔄 Retry Assessment")
    
    history = assessment_manager.get_assessment_history()
    completed_assessments = [a for a in history if a.get("status") == "completed"]
    
    if not completed_assessments:
        st.info("No completed assessments available for retry.")
        return
    
    # Select assessment to retry
    assessment_options = {}
    for assessment in completed_assessments:
        skill_area = assessment.get("skill_area", "Unknown")
        date = assessment.get("completed_at", "Unknown")[:10]
        score = assessment.get("overall_score", 0)
        key = f"{skill_area.title()} - {date} (Score: {score:.1f}%)"
        assessment_options[key] = assessment
    
    selected_key = st.selectbox(
        "Select assessment to retry:",
        list(assessment_options.keys())
    )
    
    if selected_key:
        selected_assessment = assessment_options[selected_key]
        skill_area = selected_assessment.get("skill_area")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Previous Results:**")
            st.write(f"Score: {selected_assessment.get('overall_score', 0):.1f}%")
            st.write(f"Level: {selected_assessment.get('overall_level', 'Unknown').title()}")
            st.write(f"Date: {selected_assessment.get('completed_at', 'Unknown')[:10]}")
        
        with col2:
            if st.button("🔄 Start Retry", type="primary", key="start_retry"):
                start_assessment_session(assessment_manager, user_id, skill_area, "Standard (10 questions)")