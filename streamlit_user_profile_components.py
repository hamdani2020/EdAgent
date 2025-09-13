"""
Comprehensive User Profile Management Components for EdAgent Streamlit Application

This module provides complete user profile management including:
- User profile display with data loading from API endpoints
- User preference editing with form validation and API updates
- Skill level management with interactive updates and persistence
- User goal management with add/edit/delete functionality
- Profile setup wizard for new users with guided onboarding
- Profile completion tracking and encouragement for incomplete profiles
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from streamlit_api_client import EnhancedEdAgentAPI
from streamlit_session_manager import SessionManager, UserPreferences


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UserProfileData:
    """User profile data structure"""
    user_id: str
    email: str
    name: Optional[str] = None
    current_skills: Dict[str, Dict[str, Any]] = None
    career_goals: List[str] = None
    learning_preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    profile_completion: float = 0.0
    
    def __post_init__(self):
        if self.current_skills is None:
            self.current_skills = {}
        if self.career_goals is None:
            self.career_goals = []


class UserProfileManager:
    """
    Comprehensive user profile management system
    
    Features:
    - Profile data loading and caching
    - Interactive profile editing
    - Skill level management
    - Goal management
    - Profile completion tracking
    - Guided onboarding for new users
    """
    
    def __init__(self, api: EnhancedEdAgentAPI, session_manager: SessionManager):
        self.api = api
        self.session_manager = session_manager
        
        # Skill categories and levels
        self.skill_categories = {
            "Programming Languages": [
                "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "TypeScript",
                "PHP", "Ruby", "Swift", "Kotlin", "Scala", "R", "MATLAB"
            ],
            "Web Development": [
                "HTML/CSS", "React", "Vue.js", "Angular", "Node.js", "Express.js",
                "Django", "Flask", "FastAPI", "Spring Boot", "ASP.NET"
            ],
            "Data Science & AI": [
                "Machine Learning", "Deep Learning", "Data Analysis", "Statistics",
                "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "Jupyter"
            ],
            "Cloud & DevOps": [
                "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Jenkins",
                "Git", "CI/CD", "Terraform", "Ansible"
            ],
            "Databases": [
                "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
                "SQLite", "Oracle", "Cassandra"
            ],
            "Mobile Development": [
                "iOS Development", "Android Development", "React Native", "Flutter",
                "Xamarin", "Ionic"
            ],
            "Design & UX": [
                "UI/UX Design", "Figma", "Adobe Creative Suite", "Sketch",
                "User Research", "Prototyping", "Wireframing"
            ],
            "Business & Soft Skills": [
                "Project Management", "Leadership", "Communication", "Problem Solving",
                "Critical Thinking", "Teamwork", "Agile/Scrum", "Public Speaking"
            ]
        }
        
        self.skill_levels = ["beginner", "intermediate", "advanced"]
        
        # Career goal categories
        self.career_goal_categories = {
            "Software Development": [
                "Become a Full-Stack Developer",
                "Specialize in Frontend Development",
                "Become a Backend Developer",
                "Learn Mobile App Development",
                "Master DevOps Engineering"
            ],
            "Data & AI": [
                "Become a Data Scientist",
                "Learn Machine Learning",
                "Specialize in AI/Deep Learning",
                "Become a Data Analyst",
                "Learn Business Intelligence"
            ],
            "Leadership & Management": [
                "Become a Tech Lead",
                "Transition to Engineering Management",
                "Start My Own Tech Company",
                "Become a Product Manager",
                "Lead Cross-functional Teams"
            ],
            "Career Transition": [
                "Transition to Tech from Another Field",
                "Change Programming Languages",
                "Move to a Different Industry",
                "Freelance/Consulting Career",
                "Remote Work Opportunities"
            ]
        }
        
        logger.info("UserProfileManager initialized")
    
    async def load_user_profile(self, user_id: str, force_refresh: bool = False) -> Optional[UserProfileData]:
        """Load user profile data from API with caching"""
        try:
            # Check cache first unless force refresh
            cache_key = f"user_profile_{user_id}"
            if not force_refresh:
                cached_profile = self.session_manager.get_cached_data(cache_key)
                if cached_profile:
                    logger.info("Loaded user profile from cache")
                    return UserProfileData(**cached_profile)
            
            # Load from API
            profile_data = await self.api.get_user_profile(user_id)
            if not profile_data:
                return None
            
            # Extract user data
            user_data = profile_data.get("user", {})
            
            # Create profile object
            profile = UserProfileData(
                user_id=user_data.get("user_id", user_id),
                email=self.session_manager.get_current_user().email,
                name=self.session_manager.get_current_user().name,
                current_skills=user_data.get("current_skills", {}),
                career_goals=user_data.get("career_goals", []),
                learning_preferences=user_data.get("learning_preferences"),
                created_at=user_data.get("created_at"),
                last_active=user_data.get("last_active")
            )
            
            # Calculate profile completion
            profile.profile_completion = self._calculate_profile_completion(profile)
            
            # Cache the profile
            self.session_manager.set_cached_data(cache_key, profile.__dict__, ttl_hours=1)
            
            logger.info(f"Loaded user profile for {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            st.error(f"Failed to load profile: {str(e)}")
            return None
    
    def _calculate_profile_completion(self, profile: UserProfileData) -> float:
        """Calculate profile completion percentage"""
        total_sections = 5
        completed_sections = 0
        
        # Check name
        if profile.name:
            completed_sections += 1
        
        # Check skills (at least 3 skills)
        if len(profile.current_skills) >= 3:
            completed_sections += 1
        
        # Check career goals (at least 1 goal)
        if len(profile.career_goals) >= 1:
            completed_sections += 1
        
        # Check learning preferences
        if profile.learning_preferences:
            completed_sections += 1
        
        # Check if profile is recent (active in last 30 days)
        if profile.last_active:
            try:
                if isinstance(profile.last_active, str):
                    last_active = datetime.fromisoformat(profile.last_active.replace('Z', '+00:00'))
                else:
                    last_active = profile.last_active
                
                if datetime.now() - last_active.replace(tzinfo=None) <= timedelta(days=30):
                    completed_sections += 1
            except:
                pass
        
        return (completed_sections / total_sections) * 100
    
    def render_profile_dashboard(self) -> None:
        """Render the main profile dashboard"""
        st.header("👤 User Profile")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.warning("🔐 Please log in to view your profile.")
            return
        
        user_info = self.session_manager.get_current_user()
        
        # Load profile data
        with st.spinner("Loading profile..."):
            profile = asyncio.run(self.load_user_profile(user_info.user_id))
        
        if not profile:
            st.error("Failed to load profile data.")
            return
        
        # Profile completion indicator
        self._render_profile_completion_indicator(profile)
        
        # Main profile tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Overview", "🎯 Skills", "🚀 Goals", "⚙️ Preferences", "📊 Analytics"
        ])
        
        with tab1:
            self._render_profile_overview(profile)
        
        with tab2:
            self._render_skills_management(profile)
        
        with tab3:
            self._render_goals_management(profile)
        
        with tab4:
            self._render_preferences_management(profile)
        
        with tab5:
            self._render_profile_analytics(profile)
    
    def _render_profile_completion_indicator(self, profile: UserProfileData) -> None:
        """Render profile completion progress indicator"""
        completion = profile.profile_completion
        
        # Progress bar with color coding
        if completion < 30:
            color = "red"
            message = "Let's complete your profile to get better recommendations!"
        elif completion < 70:
            color = "orange"
            message = "Good progress! Add more details for personalized recommendations."
        else:
            color = "green"
            message = "Great! Your profile is well-completed."
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: #1f77b4;">Profile Completion: {completion:.0f}%</h4>
                <div style="background-color: #e0e0e0; border-radius: 10px; height: 20px; margin: 0.5rem 0;">
                    <div style="background-color: {color}; width: {completion}%; height: 100%; border-radius: 10px;"></div>
                </div>
                <p style="margin: 0; color: #666;">{message}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if completion < 100:
                if st.button("🚀 Complete Profile", key="complete_profile_btn"):
                    self.render_profile_setup_wizard()
    
    def _render_profile_overview(self, profile: UserProfileData) -> None:
        """Render profile overview section"""
        st.subheader("📋 Profile Overview")
        
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Information**")
            st.write(f"**Name:** {profile.name or 'Not set'}")
            st.write(f"**Email:** {profile.email}")
            st.write(f"**User ID:** {profile.user_id}")
            
            if profile.created_at:
                try:
                    created_date = datetime.fromisoformat(str(profile.created_at).replace('Z', '+00:00'))
                    st.write(f"**Member since:** {created_date.strftime('%B %Y')}")
                except:
                    st.write(f"**Member since:** {profile.created_at}")
        
        with col2:
            st.markdown("**Profile Statistics**")
            st.metric("Skills Tracked", len(profile.current_skills))
            st.metric("Career Goals", len(profile.career_goals))
            st.metric("Profile Completion", f"{profile.profile_completion:.0f}%")
        
        # Quick actions
        st.markdown("**Quick Actions**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✏️ Edit Basic Info", key="edit_basic_info"):
                self._show_basic_info_editor(profile)
        
        with col2:
            if st.button("🎯 Add Skills", key="add_skills_quick"):
                st.session_state.show_skills_editor = True
        
        with col3:
            if st.button("🚀 Set Goals", key="set_goals_quick"):
                st.session_state.show_goals_editor = True
        
        with col4:
            if st.button("🔄 Refresh Profile", key="refresh_profile"):
                # Clear cache and reload
                cache_key = f"user_profile_{profile.user_id}"
                self.session_manager.clear_cached_data(cache_key)
                st.rerun()
    
    def _show_basic_info_editor(self, profile: UserProfileData) -> None:
        """Show basic information editor"""
        with st.expander("✏️ Edit Basic Information", expanded=True):
            with st.form("basic_info_form"):
                new_name = st.text_input("Full Name", value=profile.name or "")
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Save Changes", type="primary")
                with col2:
                    cancelled = st.form_submit_button("❌ Cancel")
                
                if submitted and new_name.strip():
                    # Update name in session manager
                    user_info = self.session_manager.get_current_user()
                    user_info.name = new_name.strip()
                    
                    # Update in session state
                    st.session_state.user_name = new_name.strip()
                    
                    # Clear profile cache to force refresh
                    cache_key = f"user_profile_{profile.user_id}"
                    self.session_manager.clear_cached_data(cache_key)
                    
                    st.success("✅ Basic information updated!")
                    st.rerun()
                
                if cancelled:
                    st.rerun()
    
    def _render_skills_management(self, profile: UserProfileData) -> None:
        """Render skills management section"""
        st.subheader("🎯 Skills Management")
        
        # Current skills overview
        if profile.current_skills:
            st.markdown("**Current Skills**")
            
            # Create skills DataFrame for better display
            skills_data = []
            for skill_name, skill_data in profile.current_skills.items():
                if isinstance(skill_data, dict):
                    skills_data.append({
                        "Skill": skill_name,
                        "Level": skill_data.get("level", "intermediate").title(),
                        "Confidence": f"{skill_data.get('confidence_score', 0.5) * 100:.0f}%",
                        "Last Updated": skill_data.get("last_updated", "Unknown")
                    })
                else:
                    # Handle simple skill format
                    skills_data.append({
                        "Skill": skill_name,
                        "Level": "Intermediate",
                        "Confidence": "50%",
                        "Last Updated": "Unknown"
                    })
            
            if skills_data:
                df = pd.DataFrame(skills_data)
                st.dataframe(df, use_container_width=True)
                
                # Skills visualization
                self._render_skills_radar_chart(profile.current_skills)
            else:
                st.info("No skills data available in the expected format.")
        else:
            st.info("No skills added yet. Add your first skill below!")
        
        # Add/Edit skills interface
        with st.expander("➕ Add/Edit Skills", expanded=not profile.current_skills):
            self._render_skills_editor(profile)
    
    def _render_skills_radar_chart(self, skills: Dict[str, Any]) -> None:
        """Render skills radar chart"""
        if not skills:
            return
        
        try:
            # Prepare data for radar chart
            skill_names = []
            skill_levels = []
            
            # Convert skill levels to numeric values
            level_mapping = {"beginner": 1, "intermediate": 2, "advanced": 3}
            
            for skill_name, skill_data in skills.items():
                if isinstance(skill_data, dict):
                    level = skill_data.get("level", "intermediate").lower()
                    skill_names.append(skill_name)
                    skill_levels.append(level_mapping.get(level, 2))
            
            if skill_names and skill_levels:
                # Create radar chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=skill_levels,
                    theta=skill_names,
                    fill='toself',
                    name='Skill Levels',
                    line_color='rgb(31, 119, 180)'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 3],
                            tickvals=[1, 2, 3],
                            ticktext=['Beginner', 'Intermediate', 'Advanced']
                        )),
                    showlegend=False,
                    title="Skills Overview",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            logger.error(f"Error rendering skills radar chart: {e}")
            st.info("Skills visualization not available.")
    
    def _render_skills_editor(self, profile: UserProfileData) -> None:
        """Render skills editor interface"""
        # Skill category selection
        selected_category = st.selectbox(
            "Select Skill Category:",
            list(self.skill_categories.keys()),
            key="skill_category_select"
        )
        
        # Skill selection within category
        available_skills = self.skill_categories[selected_category]
        selected_skill = st.selectbox(
            "Select Skill:",
            available_skills,
            key="skill_select"
        )
        
        # Custom skill option
        custom_skill = st.text_input(
            "Or enter a custom skill:",
            key="custom_skill_input"
        )
        
        # Use custom skill if provided
        skill_to_add = custom_skill.strip() if custom_skill.strip() else selected_skill
        
        # Skill level and confidence
        col1, col2 = st.columns(2)
        
        with col1:
            skill_level = st.selectbox(
                "Skill Level:",
                self.skill_levels,
                index=1,  # Default to intermediate
                key="skill_level_select"
            )
        
        with col2:
            confidence_score = st.slider(
                "Confidence (%):",
                min_value=0,
                max_value=100,
                value=70,
                key="confidence_slider"
            ) / 100.0
        
        # Add skill button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("➕ Add/Update Skill", key="add_skill_btn", type="primary"):
                if skill_to_add:
                    success = self._add_or_update_skill(
                        profile.user_id,
                        skill_to_add,
                        skill_level,
                        confidence_score
                    )
                    
                    if success:
                        st.success(f"✅ Added/updated skill: {skill_to_add}")
                        # Clear cache and refresh
                        cache_key = f"user_profile_{profile.user_id}"
                        self.session_manager.clear_cached_data(cache_key)
                        st.rerun()
                    else:
                        st.error("Failed to add/update skill")
                else:
                    st.warning("Please select or enter a skill name")
        
        with col2:
            # Remove skill functionality
            if profile.current_skills:
                skill_to_remove = st.selectbox(
                    "Remove Skill:",
                    [""] + list(profile.current_skills.keys()),
                    key="skill_remove_select"
                )
                
                if skill_to_remove and st.button("🗑️ Remove Skill", key="remove_skill_btn"):
                    success = self._remove_skill(profile.user_id, skill_to_remove)
                    
                    if success:
                        st.success(f"✅ Removed skill: {skill_to_remove}")
                        # Clear cache and refresh
                        cache_key = f"user_profile_{profile.user_id}"
                        self.session_manager.clear_cached_data(cache_key)
                        st.rerun()
                    else:
                        st.error("Failed to remove skill")
    
    def _add_or_update_skill(self, user_id: str, skill_name: str, level: str, confidence: float) -> bool:
        """Add or update a user skill"""
        try:
            # Prepare skill data
            skill_data = {
                skill_name: {
                    "skill_name": skill_name,
                    "level": level,
                    "confidence_score": confidence,
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            # Update via API - handle both sync and async contexts
            try:
                # Try to run in current event loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.api.update_user_skills(user_id, skill_data))
                    success = future.result()
            except RuntimeError:
                # We're in an async context, use asyncio.run
                success = asyncio.run(self.api.update_user_skills(user_id, skill_data))
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add/update skill: {e}")
            return False
    
    def _remove_skill(self, user_id: str, skill_name: str) -> bool:
        """Remove a user skill"""
        try:
            # Load current profile to get all skills
            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.load_user_profile(user_id, force_refresh=True))
                    profile = future.result()
            except RuntimeError:
                profile = asyncio.run(self.load_user_profile(user_id, force_refresh=True))
            
            if not profile or not profile.current_skills:
                return False
            
            # Remove the skill from current skills
            updated_skills = profile.current_skills.copy()
            if skill_name in updated_skills:
                del updated_skills[skill_name]
            
            # Update via API with remaining skills
            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.api.update_user_skills(user_id, updated_skills))
                    success = future.result()
            except RuntimeError:
                success = asyncio.run(self.api.update_user_skills(user_id, updated_skills))
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to remove skill: {e}")
            return False
    
    def _render_goals_management(self, profile: UserProfileData) -> None:
        """Render goals management section"""
        st.subheader("🚀 Career Goals Management")
        
        # Current goals display
        if profile.career_goals:
            st.markdown("**Current Career Goals**")
            
            for i, goal in enumerate(profile.career_goals):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"{i+1}. {goal}")
                
                with col2:
                    if st.button("🗑️", key=f"remove_goal_{i}", help="Remove this goal"):
                        success = self._remove_goal(profile.user_id, goal)
                        if success:
                            st.success("✅ Goal removed!")
                            # Clear cache and refresh
                            cache_key = f"user_profile_{profile.user_id}"
                            self.session_manager.clear_cached_data(cache_key)
                            st.rerun()
                        else:
                            st.error("Failed to remove goal")
        else:
            st.info("No career goals set yet. Add your first goal below!")
        
        # Add new goals interface
        with st.expander("➕ Add Career Goals", expanded=not profile.career_goals):
            self._render_goals_editor(profile)
    
    def _render_goals_editor(self, profile: UserProfileData) -> None:
        """Render goals editor interface"""
        # Goal category selection
        selected_category = st.selectbox(
            "Select Goal Category:",
            list(self.career_goal_categories.keys()),
            key="goal_category_select"
        )
        
        # Goal selection within category
        available_goals = self.career_goal_categories[selected_category]
        selected_goal = st.selectbox(
            "Select a Goal:",
            available_goals,
            key="goal_select"
        )
        
        # Custom goal option
        custom_goal = st.text_area(
            "Or enter a custom career goal:",
            key="custom_goal_input",
            height=100
        )
        
        # Use custom goal if provided
        goal_to_add = custom_goal.strip() if custom_goal.strip() else selected_goal
        
        # Add goal button
        if st.button("➕ Add Goal", key="add_goal_btn", type="primary"):
            if goal_to_add and goal_to_add not in profile.career_goals:
                success = self._add_goal(profile.user_id, goal_to_add)
                
                if success:
                    st.success(f"✅ Added goal: {goal_to_add}")
                    # Clear cache and refresh
                    cache_key = f"user_profile_{profile.user_id}"
                    self.session_manager.clear_cached_data(cache_key)
                    st.rerun()
                else:
                    st.error("Failed to add goal")
            elif goal_to_add in profile.career_goals:
                st.warning("This goal is already in your list")
            else:
                st.warning("Please select or enter a career goal")
    
    def _add_goal(self, user_id: str, goal: str) -> bool:
        """Add a career goal"""
        try:
            # Load current goals
            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.api.get_user_goals(user_id))
                    current_goals = future.result()
            except RuntimeError:
                current_goals = asyncio.run(self.api.get_user_goals(user_id))
            
            # Add new goal if not already present
            if goal not in current_goals:
                updated_goals = current_goals + [goal]
                try:
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.api.update_user_goals(user_id, updated_goals))
                        success = future.result()
                except RuntimeError:
                    success = asyncio.run(self.api.update_user_goals(user_id, updated_goals))
                return success
            
            return True  # Goal already exists
            
        except Exception as e:
            logger.error(f"Failed to add goal: {e}")
            return False
    
    def _remove_goal(self, user_id: str, goal: str) -> bool:
        """Remove a career goal"""
        try:
            # Load current goals
            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.api.get_user_goals(user_id))
                    current_goals = future.result()
            except RuntimeError:
                current_goals = asyncio.run(self.api.get_user_goals(user_id))
            
            # Remove goal if present
            if goal in current_goals:
                updated_goals = [g for g in current_goals if g != goal]
                try:
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.api.update_user_goals(user_id, updated_goals))
                        success = future.result()
                except RuntimeError:
                    success = asyncio.run(self.api.update_user_goals(user_id, updated_goals))
                return success
            
            return True  # Goal already removed
            
        except Exception as e:
            logger.error(f"Failed to remove goal: {e}")
            return False
    
    def _render_preferences_management(self, profile: UserProfileData) -> None:
        """Render preferences management section"""
        st.subheader("⚙️ Learning Preferences")
        
        # Load current preferences
        current_prefs = profile.learning_preferences or {}
        session_prefs = self.session_manager.get_user_preferences()
        
        # Merge API preferences with session preferences
        if session_prefs:
            session_prefs_dict = session_prefs.to_dict()
            # API preferences take precedence
            merged_prefs = {**session_prefs_dict, **current_prefs}
        else:
            merged_prefs = current_prefs
        
        # Preferences form
        with st.form("preferences_form"):
            st.markdown("**Learning Style & Preferences**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                learning_style = st.selectbox(
                    "Preferred Learning Style:",
                    ["visual", "auditory", "kinesthetic", "reading"],
                    index=["visual", "auditory", "kinesthetic", "reading"].index(
                        merged_prefs.get("learning_style", "visual")
                    ),
                    key="pref_learning_style"
                )
                
                time_commitment = st.selectbox(
                    "Time Commitment (hours per week):",
                    ["1-5", "5-10", "10-20", "20+"],
                    index=["1-5", "5-10", "10-20", "20+"].index(
                        merged_prefs.get("time_commitment", "5-10")
                    ),
                    key="pref_time_commitment"
                )
                
                budget_preference = st.selectbox(
                    "Budget Preference:",
                    ["free", "low_cost", "moderate", "premium"],
                    index=["free", "low_cost", "moderate", "premium"].index(
                        merged_prefs.get("budget_preference", "free")
                    ),
                    key="pref_budget"
                )
            
            with col2:
                preferred_platforms = st.multiselect(
                    "Preferred Learning Platforms:",
                    ["youtube", "coursera", "udemy", "edx", "khan_academy", "codecademy", "pluralsight", "linkedin_learning"],
                    default=merged_prefs.get("preferred_platforms", []),
                    key="pref_platforms"
                )
                
                content_types = st.multiselect(
                    "Preferred Content Types:",
                    ["video", "text", "interactive", "project_based", "quiz", "live_session"],
                    default=merged_prefs.get("content_types", ["video", "interactive"]),
                    key="pref_content_types"
                )
                
                difficulty_preference = st.selectbox(
                    "Difficulty Preference:",
                    ["beginner", "intermediate", "advanced", "mixed"],
                    index=["beginner", "intermediate", "advanced", "mixed"].index(
                        merged_prefs.get("difficulty_preference", "intermediate")
                    ),
                    key="pref_difficulty"
                )
            
            # Additional preferences
            st.markdown("**Additional Preferences**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                notifications_enabled = st.checkbox(
                    "Enable Learning Reminders",
                    value=merged_prefs.get("notifications_enabled", True),
                    key="pref_notifications"
                )
                
                theme = st.selectbox(
                    "Interface Theme:",
                    ["light", "dark", "auto"],
                    index=["light", "dark", "auto"].index(
                        merged_prefs.get("theme", "light")
                    ),
                    key="pref_theme"
                )
            
            with col2:
                privacy_level = st.selectbox(
                    "Privacy Level:",
                    ["minimal", "standard", "strict"],
                    index=["minimal", "standard", "strict"].index(
                        merged_prefs.get("privacy_level", "standard")
                    ),
                    key="pref_privacy"
                )
            
            # Save preferences
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button("💾 Save Preferences", type="primary")
            
            with col2:
                reset = st.form_submit_button("🔄 Reset to Defaults")
            
            if submitted:
                # Prepare preferences data
                preferences_data = {
                    "learning_style": learning_style,
                    "time_commitment": time_commitment,
                    "budget_preference": budget_preference,
                    "preferred_platforms": preferred_platforms,
                    "content_types": content_types,
                    "difficulty_preference": difficulty_preference,
                    "notifications_enabled": notifications_enabled,
                    "theme": theme,
                    "privacy_level": privacy_level
                }
                
                # Update via API
                success = asyncio.run(self.api.update_user_preferences(profile.user_id, preferences_data))
                
                if success:
                    # Also update session manager
                    session_preferences = UserPreferences(
                        learning_style=learning_style,
                        time_commitment=time_commitment,
                        budget_preference=budget_preference,
                        preferred_platforms=preferred_platforms,
                        content_types=content_types,
                        difficulty_preference=difficulty_preference,
                        notifications_enabled=notifications_enabled,
                        theme=theme,
                        privacy_level=privacy_level
                    )
                    
                    self.session_manager.update_user_preferences(session_preferences)
                    
                    st.success("✅ Preferences saved successfully!")
                    
                    # Clear cache and refresh
                    cache_key = f"user_profile_{profile.user_id}"
                    self.session_manager.clear_cached_data(cache_key)
                    st.rerun()
                else:
                    st.error("Failed to save preferences")
            
            if reset:
                # Clear preferences and reload
                self.session_manager.update_user_preferences(UserPreferences())
                st.success("✅ Preferences reset to defaults!")
                st.rerun()
    
    def _render_profile_analytics(self, profile: UserProfileData) -> None:
        """Render profile analytics section"""
        st.subheader("📊 Profile Analytics")
        
        # Profile completion breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Profile Completion Breakdown**")
            
            completion_data = {
                "Section": ["Basic Info", "Skills", "Goals", "Preferences", "Activity"],
                "Status": [
                    "Complete" if profile.name else "Incomplete",
                    "Complete" if len(profile.current_skills) >= 3 else "Incomplete",
                    "Complete" if len(profile.career_goals) >= 1 else "Incomplete",
                    "Complete" if profile.learning_preferences else "Incomplete",
                    "Complete" if profile.last_active else "Incomplete"
                ]
            }
            
            df = pd.DataFrame(completion_data)
            
            # Color code the status
            def color_status(val):
                color = 'green' if val == 'Complete' else 'red'
                return f'color: {color}'
            
            styled_df = df.style.applymap(color_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
        
        with col2:
            # Skills distribution pie chart
            if profile.current_skills:
                st.markdown("**Skills by Level**")
                
                level_counts = {"beginner": 0, "intermediate": 0, "advanced": 0}
                
                for skill_data in profile.current_skills.values():
                    if isinstance(skill_data, dict):
                        level = skill_data.get("level", "intermediate").lower()
                        if level in level_counts:
                            level_counts[level] += 1
                
                if sum(level_counts.values()) > 0:
                    fig = px.pie(
                        values=list(level_counts.values()),
                        names=[level.title() for level in level_counts.keys()],
                        title="Skills Distribution by Level"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No skill level data available")
            else:
                st.info("Add skills to see analytics")
        
        # Goals and recommendations
        if profile.career_goals:
            st.markdown("**Career Goals Progress**")
            
            # Mock progress data (in real implementation, this would come from learning paths)
            goals_progress = []
            for goal in profile.career_goals:
                # Simulate progress based on related skills
                progress = min(len(profile.current_skills) * 15, 100)  # Mock calculation
                goals_progress.append({
                    "Goal": goal,
                    "Progress": f"{progress}%",
                    "Status": "In Progress" if progress < 100 else "Completed"
                })
            
            goals_df = pd.DataFrame(goals_progress)
            st.dataframe(goals_df, use_container_width=True)
        
        # Profile insights and recommendations
        st.markdown("**Profile Insights & Recommendations**")
        
        insights = self._generate_profile_insights(profile)
        
        for insight in insights:
            if insight["type"] == "success":
                st.success(f"✅ {insight['message']}")
            elif insight["type"] == "warning":
                st.warning(f"⚠️ {insight['message']}")
            elif insight["type"] == "info":
                st.info(f"💡 {insight['message']}")
    
    def _generate_profile_insights(self, profile: UserProfileData) -> List[Dict[str, str]]:
        """Generate profile insights and recommendations"""
        insights = []
        
        # Skills insights
        skill_count = len(profile.current_skills)
        if skill_count == 0:
            insights.append({
                "type": "warning",
                "message": "Add your skills to get personalized learning recommendations."
            })
        elif skill_count < 5:
            insights.append({
                "type": "info",
                "message": f"You have {skill_count} skills tracked. Consider adding more for better recommendations."
            })
        else:
            insights.append({
                "type": "success",
                "message": f"Great! You have {skill_count} skills tracked."
            })
        
        # Goals insights
        goal_count = len(profile.career_goals)
        if goal_count == 0:
            insights.append({
                "type": "warning",
                "message": "Set career goals to create focused learning paths."
            })
        elif goal_count == 1:
            insights.append({
                "type": "info",
                "message": "Consider adding 2-3 career goals for comprehensive planning."
            })
        else:
            insights.append({
                "type": "success",
                "message": f"Excellent! You have {goal_count} career goals defined."
            })
        
        # Preferences insights
        if not profile.learning_preferences:
            insights.append({
                "type": "warning",
                "message": "Set learning preferences to get content recommendations that match your style."
            })
        else:
            insights.append({
                "type": "success",
                "message": "Your learning preferences are set for personalized recommendations."
            })
        
        # Profile completion insights
        if profile.profile_completion < 50:
            insights.append({
                "type": "info",
                "message": "Complete your profile to unlock advanced features and better recommendations."
            })
        elif profile.profile_completion >= 80:
            insights.append({
                "type": "success",
                "message": "Your profile is well-completed! You'll get the best personalized experience."
            })
        
        return insights
    
    def render_profile_setup_wizard(self) -> None:
        """Render guided profile setup wizard for new users"""
        st.header("🚀 Profile Setup Wizard")
        st.write("Let's set up your profile to provide personalized learning recommendations!")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.warning("🔐 Please log in to set up your profile.")
            return
        
        user_info = self.session_manager.get_current_user()
        
        # Multi-step wizard
        if "wizard_step" not in st.session_state:
            st.session_state.wizard_step = 1
        
        # Progress indicator
        progress = (st.session_state.wizard_step - 1) / 4
        st.progress(progress)
        st.write(f"Step {st.session_state.wizard_step} of 5")
        
        if st.session_state.wizard_step == 1:
            self._wizard_step_basic_info(user_info)
        elif st.session_state.wizard_step == 2:
            self._wizard_step_career_goals(user_info)
        elif st.session_state.wizard_step == 3:
            self._wizard_step_skills(user_info)
        elif st.session_state.wizard_step == 4:
            self._wizard_step_preferences(user_info)
        elif st.session_state.wizard_step == 5:
            self._wizard_step_completion(user_info)
    
    def _wizard_step_basic_info(self, user_info) -> None:
        """Wizard step 1: Basic information"""
        st.subheader("👤 Basic Information")
        
        with st.form("wizard_basic_info"):
            name = st.text_input(
                "Full Name",
                value=user_info.name or "",
                help="This helps personalize your experience"
            )
            
            st.markdown("**About You**")
            current_role = st.text_input(
                "Current Role/Position (optional)",
                help="e.g., Software Developer, Student, Career Changer"
            )
            
            experience_level = st.selectbox(
                "Overall Experience Level:",
                ["Beginner (0-2 years)", "Intermediate (2-5 years)", "Advanced (5+ years)", "Expert (10+ years)"]
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("⬅️ Skip", help="Skip this step"):
                    st.session_state.wizard_step = 2
                    st.rerun()
            
            with col2:
                if st.form_submit_button("Next ➡️", type="primary"):
                    # Save basic info
                    if name.strip():
                        user_info.name = name.strip()
                        st.session_state.user_name = name.strip()
                        st.session_state.wizard_current_role = current_role
                        st.session_state.wizard_experience_level = experience_level
                    
                    st.session_state.wizard_step = 2
                    st.rerun()
    
    def _wizard_step_career_goals(self, user_info) -> None:
        """Wizard step 2: Career goals"""
        st.subheader("🎯 Career Goals")
        st.write("What do you want to achieve in your career? Select or add your goals.")
        
        # Initialize goals in session state
        if "wizard_goals" not in st.session_state:
            st.session_state.wizard_goals = []
        
        # Quick goal selection
        st.markdown("**Popular Career Goals**")
        
        popular_goals = [
            "Learn a new programming language",
            "Become a full-stack developer",
            "Transition to data science",
            "Get promoted to senior role",
            "Start freelancing",
            "Learn cloud technologies",
            "Master machine learning",
            "Improve leadership skills"
        ]
        
        cols = st.columns(2)
        for i, goal in enumerate(popular_goals):
            with cols[i % 2]:
                if st.button(f"➕ {goal}", key=f"quick_goal_{i}"):
                    if goal not in st.session_state.wizard_goals:
                        st.session_state.wizard_goals.append(goal)
                        st.rerun()
        
        # Custom goal input
        with st.form("custom_goal_form"):
            custom_goal = st.text_area(
                "Add a custom career goal:",
                height=100,
                help="Describe your specific career objective"
            )
            
            if st.form_submit_button("➕ Add Custom Goal"):
                if custom_goal.strip() and custom_goal.strip() not in st.session_state.wizard_goals:
                    st.session_state.wizard_goals.append(custom_goal.strip())
                    st.rerun()
        
        # Display selected goals
        if st.session_state.wizard_goals:
            st.markdown("**Your Selected Goals:**")
            for i, goal in enumerate(st.session_state.wizard_goals):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{i+1}. {goal}")
                with col2:
                    if st.button("🗑️", key=f"remove_wizard_goal_{i}"):
                        st.session_state.wizard_goals.pop(i)
                        st.rerun()
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Previous"):
                st.session_state.wizard_step = 1
                st.rerun()
        
        with col2:
            if st.button("Skip ➡️"):
                st.session_state.wizard_step = 3
                st.rerun()
        
        with col3:
            if st.button("Next ➡️", type="primary"):
                st.session_state.wizard_step = 3
                st.rerun()
    
    def _wizard_step_skills(self, user_info) -> None:
        """Wizard step 3: Skills assessment"""
        st.subheader("🎯 Skills Assessment")
        st.write("Tell us about your current skills to get personalized recommendations.")
        
        # Initialize skills in session state
        if "wizard_skills" not in st.session_state:
            st.session_state.wizard_skills = {}
        
        # Skill category tabs
        categories = list(self.skill_categories.keys())
        selected_tab = st.selectbox("Select skill category:", categories)
        
        # Skills in selected category
        skills_in_category = self.skill_categories[selected_tab]
        
        st.markdown(f"**{selected_tab} Skills**")
        
        # Display skills with level selection
        for skill in skills_in_category[:8]:  # Limit to first 8 skills per category
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(skill)
            
            with col2:
                current_level = st.session_state.wizard_skills.get(skill, {}).get("level", "")
                level = st.selectbox(
                    "Level",
                    ["", "beginner", "intermediate", "advanced"],
                    index=["", "beginner", "intermediate", "advanced"].index(current_level) if current_level else 0,
                    key=f"skill_level_{skill}",
                    label_visibility="collapsed"
                )
                
                if level:
                    if skill not in st.session_state.wizard_skills:
                        st.session_state.wizard_skills[skill] = {}
                    st.session_state.wizard_skills[skill]["level"] = level
                elif skill in st.session_state.wizard_skills:
                    del st.session_state.wizard_skills[skill]
            
            with col3:
                if skill in st.session_state.wizard_skills:
                    confidence = st.slider(
                        "Confidence",
                        0, 100, 70,
                        key=f"skill_confidence_{skill}",
                        label_visibility="collapsed"
                    )
                    st.session_state.wizard_skills[skill]["confidence"] = confidence / 100.0
        
        # Display selected skills summary
        if st.session_state.wizard_skills:
            st.markdown("**Your Skills Summary:**")
            skills_df = pd.DataFrame([
                {
                    "Skill": skill,
                    "Level": data["level"].title(),
                    "Confidence": f"{data.get('confidence', 0.7) * 100:.0f}%"
                }
                for skill, data in st.session_state.wizard_skills.items()
            ])
            st.dataframe(skills_df, use_container_width=True)
        
        # Navigation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Previous"):
                st.session_state.wizard_step = 2
                st.rerun()
        
        with col2:
            if st.button("Skip ➡️"):
                st.session_state.wizard_step = 4
                st.rerun()
        
        with col3:
            if st.button("Next ➡️", type="primary"):
                st.session_state.wizard_step = 4
                st.rerun()
    
    def _wizard_step_preferences(self, user_info) -> None:
        """Wizard step 4: Learning preferences"""
        st.subheader("⚙️ Learning Preferences")
        st.write("Help us understand how you like to learn.")
        
        with st.form("wizard_preferences"):
            col1, col2 = st.columns(2)
            
            with col1:
                learning_style = st.selectbox(
                    "How do you learn best?",
                    ["visual", "auditory", "kinesthetic", "reading"],
                    format_func=lambda x: {
                        "visual": "Visual (videos, diagrams, charts)",
                        "auditory": "Auditory (podcasts, lectures)",
                        "kinesthetic": "Hands-on (projects, practice)",
                        "reading": "Reading (articles, books)"
                    }[x]
                )
                
                time_commitment = st.selectbox(
                    "How much time can you dedicate per week?",
                    ["1-5", "5-10", "10-20", "20+"],
                    format_func=lambda x: f"{x} hours per week"
                )
                
                budget_preference = st.selectbox(
                    "Budget preference:",
                    ["free", "low_cost", "moderate", "premium"],
                    format_func=lambda x: {
                        "free": "Free resources only",
                        "low_cost": "Under $50/month",
                        "moderate": "$50-200/month",
                        "premium": "No budget limit"
                    }[x]
                )
            
            with col2:
                preferred_platforms = st.multiselect(
                    "Preferred learning platforms:",
                    ["youtube", "coursera", "udemy", "edx", "khan_academy", "codecademy"],
                    default=["youtube", "coursera"]
                )
                
                content_types = st.multiselect(
                    "Preferred content types:",
                    ["video", "text", "interactive", "project_based", "quiz"],
                    default=["video", "interactive"]
                )
                
                difficulty_preference = st.selectbox(
                    "Learning difficulty preference:",
                    ["beginner", "intermediate", "advanced", "mixed"],
                    format_func=lambda x: {
                        "beginner": "Start with basics",
                        "intermediate": "Moderate challenge",
                        "advanced": "Advanced content",
                        "mixed": "Mix of all levels"
                    }[x]
                )
            
            # Navigation
            col1, col2, col3 = st.columns(3)
            
            with col1:
                previous = st.form_submit_button("⬅️ Previous")
            
            with col2:
                skip = st.form_submit_button("Skip ➡️")
            
            with col3:
                next_btn = st.form_submit_button("Next ➡️", type="primary")
            
            if previous:
                st.session_state.wizard_step = 3
                st.rerun()
            
            if skip or next_btn:
                if next_btn:
                    # Save preferences
                    st.session_state.wizard_preferences = {
                        "learning_style": learning_style,
                        "time_commitment": time_commitment,
                        "budget_preference": budget_preference,
                        "preferred_platforms": preferred_platforms,
                        "content_types": content_types,
                        "difficulty_preference": difficulty_preference
                    }
                
                st.session_state.wizard_step = 5
                st.rerun()
    
    def _wizard_step_completion(self, user_info) -> None:
        """Wizard step 5: Completion and save"""
        st.subheader("🎉 Profile Setup Complete!")
        st.write("Review your profile information and save it.")
        
        # Display summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Information**")
            st.write(f"Name: {user_info.name or 'Not provided'}")
            st.write(f"Email: {user_info.email}")
            
            if hasattr(st.session_state, 'wizard_current_role'):
                st.write(f"Role: {st.session_state.wizard_current_role}")
            
            st.markdown("**Career Goals**")
            goals = getattr(st.session_state, 'wizard_goals', [])
            if goals:
                for goal in goals:
                    st.write(f"• {goal}")
            else:
                st.write("No goals set")
        
        with col2:
            st.markdown("**Skills**")
            skills = getattr(st.session_state, 'wizard_skills', {})
            if skills:
                for skill, data in list(skills.items())[:5]:  # Show first 5
                    st.write(f"• {skill}: {data['level'].title()}")
                if len(skills) > 5:
                    st.write(f"... and {len(skills) - 5} more")
            else:
                st.write("No skills added")
            
            st.markdown("**Learning Preferences**")
            prefs = getattr(st.session_state, 'wizard_preferences', {})
            if prefs:
                st.write(f"Style: {prefs.get('learning_style', 'Not set').title()}")
                st.write(f"Time: {prefs.get('time_commitment', 'Not set')} hours/week")
                st.write(f"Budget: {prefs.get('budget_preference', 'Not set').title()}")
            else:
                st.write("No preferences set")
        
        # Save profile
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⬅️ Previous"):
                st.session_state.wizard_step = 4
                st.rerun()
        
        with col2:
            if st.button("💾 Save Profile", type="primary"):
                success = self._save_wizard_profile(user_info)
                
                if success:
                    st.success("🎉 Profile saved successfully!")
                    
                    # Clear wizard state
                    for key in list(st.session_state.keys()):
                        if key.startswith('wizard_'):
                            del st.session_state[key]
                    
                    # Clear profile cache to force refresh
                    cache_key = f"user_profile_{user_info.user_id}"
                    self.session_manager.clear_cached_data(cache_key)
                    
                    st.balloons()
                    
                    # Redirect to main profile
                    if st.button("View Profile Dashboard"):
                        st.session_state.wizard_step = 1  # Reset for next time
                        st.rerun()
                else:
                    st.error("Failed to save profile. Please try again.")
        
        with col3:
            if st.button("Skip & Finish"):
                # Clear wizard state without saving
                for key in list(st.session_state.keys()):
                    if key.startswith('wizard_'):
                        del st.session_state[key]
                
                st.session_state.wizard_step = 1  # Reset for next time
                st.success("Profile setup skipped. You can complete it later from your profile page.")
                st.rerun()
    
    def _save_wizard_profile(self, user_info) -> bool:
        """Save profile data collected from wizard"""
        try:
            success_count = 0
            total_operations = 0
            
            # Save goals
            goals = getattr(st.session_state, 'wizard_goals', [])
            if goals:
                total_operations += 1
                if asyncio.run(self.api.update_user_goals(user_info.user_id, goals)):
                    success_count += 1
            
            # Save skills
            skills = getattr(st.session_state, 'wizard_skills', {})
            if skills:
                total_operations += 1
                # Convert to API format
                api_skills = {}
                for skill_name, skill_data in skills.items():
                    api_skills[skill_name] = {
                        "skill_name": skill_name,
                        "level": skill_data["level"],
                        "confidence_score": skill_data.get("confidence", 0.7),
                        "last_updated": datetime.now().isoformat()
                    }
                
                if asyncio.run(self.api.update_user_skills(user_info.user_id, api_skills)):
                    success_count += 1
            
            # Save preferences
            prefs = getattr(st.session_state, 'wizard_preferences', {})
            if prefs:
                total_operations += 1
                if asyncio.run(self.api.update_user_preferences(user_info.user_id, prefs)):
                    success_count += 1
                
                # Also update session manager
                session_preferences = UserPreferences(**prefs)
                self.session_manager.update_user_preferences(session_preferences)
            
            # Consider success if at least half of operations succeeded
            return success_count >= (total_operations / 2) if total_operations > 0 else True
            
        except Exception as e:
            logger.error(f"Failed to save wizard profile: {e}")
            return False


# Convenience functions for easy integration
def render_user_profile_dashboard(api: EnhancedEdAgentAPI, session_manager: SessionManager) -> None:
    """Render the complete user profile dashboard"""
    profile_manager = UserProfileManager(api, session_manager)
    profile_manager.render_profile_dashboard()


def render_profile_setup_wizard(api: EnhancedEdAgentAPI, session_manager: SessionManager) -> None:
    """Render the profile setup wizard"""
    profile_manager = UserProfileManager(api, session_manager)
    profile_manager.render_profile_setup_wizard()


def get_profile_completion_status(api: EnhancedEdAgentAPI, session_manager: SessionManager, user_id: str) -> float:
    """Get profile completion percentage"""
    try:
        profile_manager = UserProfileManager(api, session_manager)
        profile = asyncio.run(profile_manager.load_user_profile(user_id))
        return profile.profile_completion if profile else 0.0
    except Exception as e:
        logger.error(f"Failed to get profile completion status: {e}")
        return 0.0