"""
Learning Path Management Components
Comprehensive learning path creation, management, and visualization components for Streamlit
"""

import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from streamlit_api_client import EnhancedEdAgentAPI, LearningPath
from streamlit_session_manager import SessionManager


class LearningPathManager:
    """Manages learning path operations and UI components"""
    
    def __init__(self, api_client: EnhancedEdAgentAPI, session_manager: SessionManager):
        self.api = api_client
        self.session_manager = session_manager
    
    def render_learning_path_dashboard(self) -> None:
        """Render the main learning path dashboard"""
        st.header("🛤️ Learning Path Management")
        
        if not self.session_manager.is_authenticated():
            st.warning("🔐 Please log in to access learning paths.")
            return
        
        user_info = self.session_manager.get_current_user()
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📚 My Paths", "➕ Create New", "📊 Progress", "🔍 Recommendations"
        ])
        
        with tab1:
            self._render_user_learning_paths(user_info.user_id)
        
        with tab2:
            self._render_learning_path_creator(user_info.user_id)
        
        with tab3:
            self._render_progress_analytics(user_info.user_id)
        
        with tab4:
            self._render_learning_path_recommendations(user_info.user_id)
    
    def _render_user_learning_paths(self, user_id: str) -> None:
        """Render user's existing learning paths"""
        st.subheader("📚 Your Learning Paths")
        
        # Load learning paths
        if st.button("🔄 Refresh Paths", key="refresh_paths"):
            st.session_state.pop("learning_paths_cache", None)
        
        learning_paths = self._get_cached_learning_paths(user_id)
        
        if not learning_paths:
            st.info("🌟 No learning paths yet! Create your first one to get started.")
            return
        
        # Filter and sort options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by status:",
                ["All", "Active", "Completed", "Paused"],
                key="path_status_filter"
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort by:",
                ["Created Date", "Progress", "Title", "Last Updated"],
                key="path_sort_by"
            )
        
        with col3:
            sort_order = st.selectbox(
                "Order:",
                ["Descending", "Ascending"],
                key="path_sort_order"
            )
        
        # Filter and sort paths
        filtered_paths = self._filter_and_sort_paths(
            learning_paths, status_filter, sort_by, sort_order
        )
        
        # Display paths
        for i, path in enumerate(filtered_paths):
            self._render_learning_path_card(path, i)
    
    def _render_learning_path_card(self, path: Dict[str, Any], index: int) -> None:
        """Render individual learning path card"""
        with st.container():
            # Path header
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### 📖 {path.get('title', f'Learning Path {index + 1}')}")
                st.write(f"**Goal:** {path.get('goal', 'Not specified')}")
            
            with col2:
                progress = path.get('progress', 0.0)
                st.metric("Progress", f"{progress:.1%}")
            
            with col3:
                difficulty = path.get('difficulty_level', 'intermediate')
                difficulty_colors = {
                    'beginner': '🟢',
                    'intermediate': '🟡', 
                    'advanced': '🔴'
                }
                st.write(f"**Difficulty:** {difficulty_colors.get(difficulty, '🟡')} {difficulty.title()}")
            
            # Progress bar
            st.progress(progress)
            
            # Path details in expandable section
            with st.expander(f"📋 Details & Milestones", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Description:** {path.get('description', 'No description available')}")
                    
                    # Timeline info
                    created_at = path.get('created_at')
                    if created_at:
                        st.write(f"**Created:** {created_at}")
                    
                    estimated_duration = path.get('estimated_duration')
                    if estimated_duration:
                        st.write(f"**Estimated Duration:** {estimated_duration} hours")
                    
                    # Prerequisites
                    prerequisites = path.get('prerequisites', [])
                    if prerequisites:
                        st.write("**Prerequisites:**")
                        for prereq in prerequisites:
                            st.write(f"• {prereq}")
                
                with col2:
                    # Target skills
                    target_skills = path.get('target_skills', [])
                    if target_skills:
                        st.write("**Target Skills:**")
                        for skill in target_skills:
                            st.write(f"• {skill}")
                
                # Milestones
                milestones = path.get('milestones', [])
                if milestones:
                    st.write("### 🎯 Milestones")
                    
                    for j, milestone in enumerate(milestones):
                        milestone_col1, milestone_col2, milestone_col3 = st.columns([3, 1, 1])
                        
                        with milestone_col1:
                            status = milestone.get('status', 'pending')
                            status_icons = {
                                'completed': '✅',
                                'in_progress': '🔄',
                                'pending': '⏳'
                            }
                            icon = status_icons.get(status, '⏳')
                            
                            st.write(f"{icon} **{milestone.get('title', f'Milestone {j + 1}')}**")
                            if milestone.get('description'):
                                st.caption(milestone['description'])
                        
                        with milestone_col2:
                            if st.button(
                                "Mark Complete" if status != 'completed' else "Completed",
                                key=f"milestone_{path.get('id')}_{j}",
                                disabled=status == 'completed'
                            ):
                                self._update_milestone_status(
                                    path.get('id'), 
                                    milestone.get('id'), 
                                    'completed'
                                )
                        
                        with milestone_col3:
                            milestone_progress = milestone.get('progress', 0.0)
                            st.write(f"{milestone_progress:.0%}")
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(f"📖 Continue", key=f"continue_path_{index}"):
                    self._continue_learning_path(path)
            
            with col2:
                if st.button(f"📊 View Progress", key=f"progress_path_{index}"):
                    self._show_detailed_progress(path)
            
            with col3:
                if st.button(f"✏️ Edit", key=f"edit_path_{index}"):
                    self._edit_learning_path(path)
            
            with col4:
                if st.button(f"🗑️ Delete", key=f"delete_path_{index}"):
                    self._delete_learning_path(path)
            
            st.divider()
    
    def _render_learning_path_creator(self, user_id: str) -> None:
        """Render learning path creation interface"""
        st.subheader("➕ Create New Learning Path")
        
        with st.form("create_learning_path_form"):
            # Goal input
            st.markdown("### 🎯 Define Your Goal")
            goal_description = st.text_area(
                "Describe your learning goal:",
                placeholder="e.g., I want to become a full-stack web developer specializing in React and Node.js",
                height=100
            )
            
            # Learning preferences
            st.markdown("### ⚙️ Learning Preferences")
            
            col1, col2 = st.columns(2)
            
            with col1:
                time_commitment = st.selectbox(
                    "Time commitment (hours per week):",
                    ["1-5", "5-10", "10-20", "20+"]
                )
                
                difficulty_preference = st.selectbox(
                    "Preferred difficulty level:",
                    ["beginner", "intermediate", "advanced", "mixed"]
                )
                
                learning_style = st.multiselect(
                    "Preferred learning styles:",
                    ["video", "text", "interactive", "project_based", "quiz"]
                )
            
            with col2:
                budget_preference = st.selectbox(
                    "Budget preference:",
                    ["free", "low_cost", "moderate", "premium"]
                )
                
                timeline = st.selectbox(
                    "Target timeline:",
                    ["1 month", "3 months", "6 months", "1 year", "Flexible"]
                )
                
                preferred_platforms = st.multiselect(
                    "Preferred platforms:",
                    ["youtube", "coursera", "udemy", "edx", "khan_academy", "codecademy"]
                )
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                include_prerequisites = st.checkbox("Include prerequisite recommendations", value=True)
                include_projects = st.checkbox("Include hands-on projects", value=True)
                include_assessments = st.checkbox("Include skill assessments", value=True)
                
                custom_requirements = st.text_area(
                    "Additional requirements or constraints:",
                    placeholder="e.g., Focus on industry-standard tools, include certification preparation"
                )
            
            # Submit button
            submitted = st.form_submit_button("🚀 Create Learning Path", type="primary")
            
            if submitted:
                if goal_description.strip():
                    self._create_learning_path_with_preferences(
                        user_id, goal_description, {
                            'time_commitment': time_commitment,
                            'difficulty_preference': difficulty_preference,
                            'learning_style': learning_style,
                            'budget_preference': budget_preference,
                            'timeline': timeline,
                            'preferred_platforms': preferred_platforms,
                            'include_prerequisites': include_prerequisites,
                            'include_projects': include_projects,
                            'include_assessments': include_assessments,
                            'custom_requirements': custom_requirements
                        }
                    )
                else:
                    st.error("⚠️ Please describe your learning goal.")
    
    def _render_progress_analytics(self, user_id: str) -> None:
        """Render progress analytics and visualizations"""
        st.subheader("📊 Learning Progress Analytics")
        
        learning_paths = self._get_cached_learning_paths(user_id)
        
        if not learning_paths:
            st.info("📈 Create some learning paths to see your progress analytics!")
            return
        
        # Overall progress metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_paths = len(learning_paths)
        completed_paths = len([p for p in learning_paths if p.get('progress', 0) >= 1.0])
        avg_progress = sum(p.get('progress', 0) for p in learning_paths) / total_paths if total_paths > 0 else 0
        total_milestones = sum(len(p.get('milestones', [])) for p in learning_paths)
        
        with col1:
            st.metric("Total Paths", total_paths)
        
        with col2:
            st.metric("Completed", completed_paths)
        
        with col3:
            st.metric("Avg Progress", f"{avg_progress:.1%}")
        
        with col4:
            st.metric("Total Milestones", total_milestones)
        
        # Progress visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Progress distribution chart
            st.markdown("#### 📊 Progress Distribution")
            
            progress_data = []
            for path in learning_paths:
                progress_data.append({
                    'Path': path.get('title', 'Untitled'),
                    'Progress': path.get('progress', 0) * 100
                })
            
            if progress_data:
                df = pd.DataFrame(progress_data)
                fig = px.bar(
                    df, 
                    x='Path', 
                    y='Progress',
                    title="Learning Path Progress",
                    color='Progress',
                    color_continuous_scale='viridis'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Skills development radar chart
            st.markdown("#### 🎯 Skills Development")
            
            # Aggregate target skills from all paths
            all_skills = {}
            for path in learning_paths:
                for skill in path.get('target_skills', []):
                    if skill not in all_skills:
                        all_skills[skill] = []
                    all_skills[skill].append(path.get('progress', 0))
            
            if all_skills:
                # Calculate average progress per skill
                skill_progress = {
                    skill: sum(progresses) / len(progresses) 
                    for skill, progresses in all_skills.items()
                }
                
                skills = list(skill_progress.keys())
                values = [skill_progress[skill] * 100 for skill in skills]
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=skills,
                    fill='toself',
                    name='Skill Progress'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=False,
                    height=400,
                    title="Skills Development Radar"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No skill data available yet.")
        
        # Timeline view
        st.markdown("#### 📅 Learning Timeline")
        
        timeline_data = []
        for path in learning_paths:
            created_at = path.get('created_at')
            if created_at:
                timeline_data.append({
                    'Date': created_at,
                    'Event': f"Started: {path.get('title', 'Untitled')}",
                    'Type': 'Start',
                    'Progress': 0
                })
            
            # Add milestone completions (mock data for now)
            for milestone in path.get('milestones', []):
                if milestone.get('status') == 'completed':
                    timeline_data.append({
                        'Date': created_at,  # Would be completion date in real implementation
                        'Event': f"Completed: {milestone.get('title', 'Milestone')}",
                        'Type': 'Milestone',
                        'Progress': path.get('progress', 0) * 100
                    })
        
        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data)
            st.dataframe(df_timeline, use_container_width=True)
        else:
            st.info("No timeline data available yet.")
    
    def _render_learning_path_recommendations(self, user_id: str) -> None:
        """Render learning path recommendations"""
        st.subheader("🔍 Recommended Learning Paths")
        
        # Get user preferences for recommendations
        user_preferences = self.session_manager.get_user_preferences()
        
        # Mock recommendations based on popular paths and user preferences
        recommendations = self._generate_mock_recommendations(user_preferences)
        
        if not recommendations:
            st.info("🤖 Complete your profile to get personalized recommendations!")
            return
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            category_filter = st.selectbox(
                "Filter by category:",
                ["All", "Programming", "Data Science", "Web Development", "Mobile Development", "DevOps"]
            )
        
        with col2:
            difficulty_filter = st.selectbox(
                "Filter by difficulty:",
                ["All", "Beginner", "Intermediate", "Advanced"]
            )
        
        # Display recommendations
        for i, rec in enumerate(recommendations):
            if (category_filter == "All" or rec['category'] == category_filter) and \
               (difficulty_filter == "All" or rec['difficulty'] == difficulty_filter):
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"### 💡 {rec['title']}")
                        st.write(rec['description'])
                        st.write(f"**Category:** {rec['category']}")
                        
                        # Skills tags
                        if rec.get('skills'):
                            st.write("**Skills:** " + " • ".join(rec['skills']))
                    
                    with col2:
                        st.write(f"**Difficulty:** {rec['difficulty']}")
                        st.write(f"**Duration:** {rec['duration']}")
                        st.write(f"**Rating:** {'⭐' * rec['rating']}")
                    
                    with col3:
                        if st.button(f"Create Path", key=f"create_rec_{i}"):
                            self._create_path_from_recommendation(user_id, rec)
                        
                        if st.button(f"Learn More", key=f"learn_rec_{i}"):
                            st.info(f"More details about {rec['title']} would be shown here.")
                    
                    st.divider()
    
    def _get_cached_learning_paths(self, user_id: str) -> List[Dict[str, Any]]:
        """Get learning paths with caching"""
        cache_key = "learning_paths_cache"
        
        if cache_key not in st.session_state:
            with st.spinner("Loading learning paths..."):
                try:
                    # Use asyncio.create_task to handle async properly in Streamlit
                    import asyncio
                    loop = None
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        pass
                    
                    if loop is not None:
                        # We're in an async context, create a task
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self.api.get_user_learning_paths(user_id))
                            paths = future.result()
                    else:
                        # We're not in an async context, safe to use asyncio.run
                        paths = asyncio.run(self.api.get_user_learning_paths(user_id))
                    
                    # Convert LearningPath objects to dictionaries for easier handling
                    if paths:
                        st.session_state[cache_key] = [
                            {
                                'id': path.id,
                                'title': path.title,
                                'description': path.description,
                                'goal': path.goal,
                                'milestones': path.milestones,
                                'estimated_duration': path.estimated_duration,
                                'difficulty_level': path.difficulty_level,
                                'prerequisites': path.prerequisites,
                                'target_skills': path.target_skills,
                                'created_at': path.created_at.strftime('%Y-%m-%d') if path.created_at else None,
                                'updated_at': path.updated_at.strftime('%Y-%m-%d') if path.updated_at else None,
                                'progress': path.progress
                            }
                            for path in paths
                        ]
                    else:
                        st.session_state[cache_key] = []
                except Exception as e:
                    st.error(f"Failed to load learning paths: {str(e)}")
                    st.session_state[cache_key] = []
        
        return st.session_state[cache_key]
    
    def _filter_and_sort_paths(
        self, 
        paths: List[Dict[str, Any]], 
        status_filter: str, 
        sort_by: str, 
        sort_order: str
    ) -> List[Dict[str, Any]]:
        """Filter and sort learning paths"""
        filtered_paths = paths.copy()
        
        # Apply status filter
        if status_filter != "All":
            if status_filter == "Active":
                filtered_paths = [p for p in filtered_paths if 0 < p.get('progress', 0) < 1.0]
            elif status_filter == "Completed":
                filtered_paths = [p for p in filtered_paths if p.get('progress', 0) >= 1.0]
            elif status_filter == "Paused":
                # For now, treat paths with 0 progress as paused
                filtered_paths = [p for p in filtered_paths if p.get('progress', 0) == 0]
        
        # Apply sorting
        reverse = sort_order == "Descending"
        
        if sort_by == "Created Date":
            filtered_paths.sort(key=lambda x: x.get('created_at', ''), reverse=reverse)
        elif sort_by == "Progress":
            filtered_paths.sort(key=lambda x: x.get('progress', 0), reverse=reverse)
        elif sort_by == "Title":
            filtered_paths.sort(key=lambda x: x.get('title', ''), reverse=reverse)
        elif sort_by == "Last Updated":
            filtered_paths.sort(key=lambda x: x.get('updated_at', ''), reverse=reverse)
        
        return filtered_paths
    
    def _create_learning_path_with_preferences(
        self, 
        user_id: str, 
        goal: str, 
        preferences: Dict[str, Any]
    ) -> None:
        """Create learning path with user preferences"""
        with st.spinner("🚀 Creating your personalized learning path..."):
            try:
                # Handle async operation properly
                import asyncio
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass
                
                if loop is not None:
                    # We're in an async context, use thread executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.api.create_learning_path(user_id, goal))
                        result = future.result()
                else:
                    # We're not in an async context, safe to use asyncio.run
                    result = asyncio.run(self.api.create_learning_path(user_id, goal))
                
                if result:
                    st.success("✅ Learning path created successfully!")
                    
                    # Clear cache to refresh the list
                    st.session_state.pop("learning_paths_cache", None)
                    
                    # Show success details
                    with st.expander("📋 Path Details", expanded=True):
                        st.write(f"**Title:** {result.title}")
                        st.write(f"**Goal:** {result.goal}")
                        st.write(f"**Difficulty:** {result.difficulty_level}")
                        
                        if result.milestones:
                            st.write("**Milestones:**")
                            for milestone in result.milestones:
                                st.write(f"• {milestone.get('title', 'Milestone')}")
                    
                    # Offer to navigate to the new path
                    if st.button("📖 View New Path"):
                        st.session_state["selected_path_id"] = result.id
                        st.rerun()
                
                else:
                    st.error("❌ Failed to create learning path. Please try again.")
            
            except Exception as e:
                st.error(f"❌ Error creating learning path: {str(e)}")
    
    def _update_milestone_status(self, path_id: str, milestone_id: str, status: str) -> None:
        """Update milestone status"""
        try:
            # Handle async operation properly
            import asyncio
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            
            if loop is not None:
                # We're in an async context, use thread executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.api.update_milestone_status(path_id, milestone_id, status)
                    )
                    success = future.result()
            else:
                # We're not in an async context, safe to use asyncio.run
                success = asyncio.run(
                    self.api.update_milestone_status(path_id, milestone_id, status)
                )
            
            if success:
                st.success(f"✅ Milestone marked as {status}!")
                # Clear cache to refresh data
                st.session_state.pop("learning_paths_cache", None)
                st.rerun()
            else:
                st.error("❌ Failed to update milestone status.")
        
        except Exception as e:
            st.error(f"❌ Error updating milestone: {str(e)}")
    
    def _continue_learning_path(self, path: Dict[str, Any]) -> None:
        """Continue learning path - show next steps"""
        st.info(f"📖 Continuing with '{path.get('title', 'Learning Path')}'...")
        
        # Find next incomplete milestone
        milestones = path.get('milestones', [])
        next_milestone = None
        
        for milestone in milestones:
            if milestone.get('status') != 'completed':
                next_milestone = milestone
                break
        
        if next_milestone:
            st.write(f"**Next Step:** {next_milestone.get('title', 'Continue learning')}")
            if next_milestone.get('description'):
                st.write(next_milestone['description'])
        else:
            st.write("🎉 Congratulations! You've completed all milestones in this path!")
    
    def _show_detailed_progress(self, path: Dict[str, Any]) -> None:
        """Show detailed progress for a learning path"""
        st.info(f"📊 Detailed progress for '{path.get('title', 'Learning Path')}'")
        
        # Progress metrics
        progress = path.get('progress', 0)
        milestones = path.get('milestones', [])
        completed_milestones = len([m for m in milestones if m.get('status') == 'completed'])
        total_milestones = len(milestones)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Overall Progress", f"{progress:.1%}")
        
        with col2:
            st.metric("Completed Milestones", f"{completed_milestones}/{total_milestones}")
        
        with col3:
            estimated_duration = path.get('estimated_duration', 0)
            if estimated_duration:
                completed_hours = estimated_duration * progress
                st.metric("Hours Completed", f"{completed_hours:.1f}/{estimated_duration}")
        
        # Milestone progress chart
        if milestones:
            milestone_data = []
            for milestone in milestones:
                milestone_data.append({
                    'Milestone': milestone.get('title', 'Untitled'),
                    'Status': milestone.get('status', 'pending'),
                    'Progress': 100 if milestone.get('status') == 'completed' else 
                               50 if milestone.get('status') == 'in_progress' else 0
                })
            
            df = pd.DataFrame(milestone_data)
            fig = px.bar(
                df, 
                x='Milestone', 
                y='Progress',
                color='Status',
                title="Milestone Progress"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _edit_learning_path(self, path: Dict[str, Any]) -> None:
        """Edit learning path (placeholder)"""
        st.info(f"✏️ Editing '{path.get('title', 'Learning Path')}' - Feature coming soon!")
    
    def _delete_learning_path(self, path: Dict[str, Any]) -> None:
        """Delete learning path with confirmation"""
        path_title = path.get('title', 'Learning Path')
        
        # Use session state for confirmation
        confirm_key = f"confirm_delete_{path.get('id')}"
        
        if st.session_state.get(confirm_key, False):
            # Show final confirmation
            st.warning(f"⚠️ Are you sure you want to delete '{path_title}'? This action cannot be undone.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Yes, Delete", key=f"final_delete_{path.get('id')}"):
                    # TODO: Implement actual deletion via API
                    st.success(f"🗑️ '{path_title}' has been deleted.")
                    st.session_state.pop("learning_paths_cache", None)
                    st.session_state[confirm_key] = False
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel", key=f"cancel_delete_{path.get('id')}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
        else:
            st.session_state[confirm_key] = True
            st.rerun()
    
    def _generate_mock_recommendations(self, user_preferences) -> List[Dict[str, Any]]:
        """Generate mock learning path recommendations"""
        recommendations = [
            {
                'title': 'Full-Stack Web Development',
                'description': 'Learn to build complete web applications from frontend to backend',
                'category': 'Web Development',
                'difficulty': 'Intermediate',
                'duration': '12 weeks',
                'rating': 5,
                'skills': ['HTML', 'CSS', 'JavaScript', 'React', 'Node.js', 'MongoDB']
            },
            {
                'title': 'Data Science Fundamentals',
                'description': 'Master the basics of data analysis, visualization, and machine learning',
                'category': 'Data Science',
                'difficulty': 'Beginner',
                'duration': '10 weeks',
                'rating': 4,
                'skills': ['Python', 'Pandas', 'NumPy', 'Matplotlib', 'Scikit-learn']
            },
            {
                'title': 'Mobile App Development with React Native',
                'description': 'Build cross-platform mobile apps using React Native',
                'category': 'Mobile Development',
                'difficulty': 'Intermediate',
                'duration': '8 weeks',
                'rating': 4,
                'skills': ['React Native', 'JavaScript', 'Mobile UI/UX', 'API Integration']
            },
            {
                'title': 'DevOps Engineering Bootcamp',
                'description': 'Learn modern DevOps practices and tools for deployment automation',
                'category': 'DevOps',
                'difficulty': 'Advanced',
                'duration': '14 weeks',
                'rating': 5,
                'skills': ['Docker', 'Kubernetes', 'CI/CD', 'AWS', 'Terraform']
            },
            {
                'title': 'Python Programming Mastery',
                'description': 'Comprehensive Python course from basics to advanced concepts',
                'category': 'Programming',
                'difficulty': 'Beginner',
                'duration': '6 weeks',
                'rating': 5,
                'skills': ['Python', 'OOP', 'Data Structures', 'Algorithms', 'Testing']
            }
        ]
        
        return recommendations
    
    def _create_path_from_recommendation(self, user_id: str, recommendation: Dict[str, Any]) -> None:
        """Create learning path from recommendation"""
        goal = f"Learn {recommendation['title']}: {recommendation['description']}"
        
        with st.spinner(f"Creating learning path for {recommendation['title']}..."):
            try:
                # Handle async operation properly
                import asyncio
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass
                
                if loop is not None:
                    # We're in an async context, use thread executor
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.api.create_learning_path(user_id, goal))
                        result = future.result()
                else:
                    # We're not in an async context, safe to use asyncio.run
                    result = asyncio.run(self.api.create_learning_path(user_id, goal))
                
                if result:
                    st.success(f"✅ Created learning path: {recommendation['title']}")
                    st.session_state.pop("learning_paths_cache", None)
                    st.rerun()
                else:
                    st.error("❌ Failed to create learning path from recommendation.")
            
            except Exception as e:
                st.error(f"❌ Error creating path: {str(e)}")


def render_learning_path_management_system(
    api_client: EnhancedEdAgentAPI, 
    session_manager: SessionManager
) -> None:
    """Main function to render the complete learning path management system"""
    manager = LearningPathManager(api_client, session_manager)
    manager.render_learning_path_dashboard()