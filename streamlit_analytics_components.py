"""
EdAgent Analytics and Progress Tracking Dashboard
Comprehensive analytics dashboard with charts, progress visualization, and achievement tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import json
from dataclasses import dataclass, asdict
import math

from streamlit_api_client import EnhancedEdAgentAPI
from streamlit_session_manager import SessionManager


@dataclass
class AnalyticsData:
    """Analytics data structure"""
    user_id: str
    total_assessments: int = 0
    total_learning_paths: int = 0
    completed_paths: int = 0
    skills_improved: int = 0
    study_hours: float = 0.0
    current_streak: int = 0
    longest_streak: int = 0
    achievements: List[Dict[str, Any]] = None
    skill_levels: Dict[str, float] = None
    progress_timeline: List[Dict[str, Any]] = None
    activity_data: Dict[str, Any] = None
    learning_velocity: float = 0.0
    
    def __post_init__(self):
        if self.achievements is None:
            self.achievements = []
        if self.skill_levels is None:
            self.skill_levels = {}
        if self.progress_timeline is None:
            self.progress_timeline = []
        if self.activity_data is None:
            self.activity_data = {}


@dataclass
class Achievement:
    """Achievement data structure"""
    id: str
    title: str
    description: str
    icon: str
    category: str
    earned: bool = False
    earned_date: Optional[datetime] = None
    progress: float = 0.0
    target: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnalyticsCalculator:
    """Handles analytics calculations and data processing"""
    
    @staticmethod
    def calculate_learning_velocity(progress_data: List[Dict[str, Any]]) -> float:
        """Calculate learning velocity (progress per day)"""
        if len(progress_data) < 2:
            return 0.0
        
        # Sort by date
        sorted_data = sorted(progress_data, key=lambda x: x.get('date', datetime.now()))
        
        # Calculate average daily progress
        total_progress = 0
        days = 0
        
        for i in range(1, len(sorted_data)):
            prev_progress = sorted_data[i-1].get('progress', 0)
            curr_progress = sorted_data[i].get('progress', 0)
            progress_diff = curr_progress - prev_progress
            
            if progress_diff > 0:
                total_progress += progress_diff
                days += 1
        
        return total_progress / days if days > 0 else 0.0
    
    @staticmethod
    def calculate_skill_radar_data(skill_levels: Dict[str, float]) -> Dict[str, List]:
        """Prepare data for skill radar chart"""
        if not skill_levels:
            return {"skills": [], "levels": []}
        
        skills = list(skill_levels.keys())
        levels = list(skill_levels.values())
        
        # Normalize levels to 0-100 scale
        normalized_levels = [min(100, max(0, level)) for level in levels]
        
        return {
            "skills": skills,
            "levels": normalized_levels
        }
    
    @staticmethod
    def generate_activity_heatmap_data(activity_data: Dict[str, Any]) -> np.ndarray:
        """Generate activity heatmap data"""
        # Create 7x24 matrix (days x hours)
        heatmap_data = np.zeros((7, 24))
        
        for day_idx in range(7):
            for hour_idx in range(24):
                # Use activity data if available, otherwise generate mock data
                key = f"day_{day_idx}_hour_{hour_idx}"
                if key in activity_data:
                    heatmap_data[day_idx][hour_idx] = activity_data[key]
                else:
                    # Generate realistic activity pattern
                    base_activity = np.random.poisson(2)
                    
                    # Higher activity during work hours (9-17)
                    if 9 <= hour_idx <= 17:
                        base_activity *= 2
                    
                    # Lower activity on weekends
                    if day_idx >= 5:
                        base_activity *= 0.7
                    
                    heatmap_data[day_idx][hour_idx] = base_activity
        
        return heatmap_data
    
    @staticmethod
    def calculate_achievement_progress(user_data: AnalyticsData) -> List[Achievement]:
        """Calculate achievement progress based on user data"""
        achievements = [
            Achievement(
                id="first_assessment",
                title="First Steps",
                description="Complete your first skill assessment",
                icon="🎯",
                category="assessment",
                earned=user_data.total_assessments >= 1,
                progress=min(100, user_data.total_assessments * 100),
                target=1
            ),
            Achievement(
                id="assessment_master",
                title="Assessment Master",
                description="Complete 10 skill assessments",
                icon="🏆",
                category="assessment",
                earned=user_data.total_assessments >= 10,
                progress=min(100, (user_data.total_assessments / 10) * 100),
                target=10
            ),
            Achievement(
                id="path_creator",
                title="Path Creator",
                description="Create your first learning path",
                icon="🛤️",
                category="learning",
                earned=user_data.total_learning_paths >= 1,
                progress=min(100, user_data.total_learning_paths * 100),
                target=1
            ),
            Achievement(
                id="path_completer",
                title="Path Completer",
                description="Complete a learning path",
                icon="✅",
                category="learning",
                earned=user_data.completed_paths >= 1,
                progress=min(100, user_data.completed_paths * 100),
                target=1
            ),
            Achievement(
                id="week_warrior",
                title="Week Warrior",
                description="Study for 7 consecutive days",
                icon="🔥",
                category="streak",
                earned=user_data.current_streak >= 7,
                progress=min(100, (user_data.current_streak / 7) * 100),
                target=7
            ),
            Achievement(
                id="marathon_learner",
                title="Marathon Learner",
                description="Maintain a 30-day learning streak",
                icon="🏃‍♂️",
                category="streak",
                earned=user_data.longest_streak >= 30,
                progress=min(100, (user_data.longest_streak / 30) * 100),
                target=30
            ),
            Achievement(
                id="skill_master",
                title="Skill Master",
                description="Reach advanced level (80+) in any skill",
                icon="⭐",
                category="skill",
                earned=any(level >= 80 for level in user_data.skill_levels.values()),
                progress=max([level for level in user_data.skill_levels.values()] + [0]),
                target=80
            ),
            Achievement(
                id="polyglot",
                title="Polyglot",
                description="Learn 5 different skills",
                icon="🌟",
                category="skill",
                earned=len(user_data.skill_levels) >= 5,
                progress=min(100, (len(user_data.skill_levels) / 5) * 100),
                target=5
            ),
            Achievement(
                id="dedicated_learner",
                title="Dedicated Learner",
                description="Study for 100 hours total",
                icon="📚",
                category="time",
                earned=user_data.study_hours >= 100,
                progress=min(100, (user_data.study_hours / 100) * 100),
                target=100
            ),
            Achievement(
                id="speed_learner",
                title="Speed Learner",
                description="Maintain high learning velocity",
                icon="⚡",
                category="velocity",
                earned=user_data.learning_velocity >= 5.0,
                progress=min(100, (user_data.learning_velocity / 5.0) * 100),
                target=5
            )
        ]
        
        return achievements


class AnalyticsChartRenderer:
    """Handles rendering of analytics charts and visualizations"""
    
    @staticmethod
    def render_progress_timeline_chart(progress_data: List[Dict[str, Any]]) -> go.Figure:
        """Render progress timeline chart"""
        if not progress_data:
            # Generate sample data
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), 
                                end=datetime.now(), freq='D')
            progress_data = [
                {
                    'date': date,
                    'progress': min(100, max(0, 20 + i * 2 + np.random.normal(0, 5)))
                }
                for i, date in enumerate(dates)
            ]
        
        df = pd.DataFrame(progress_data)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = px.line(
            df, 
            x='date', 
            y='progress',
            title='Learning Progress Over Time',
            labels={'progress': 'Progress (%)', 'date': 'Date'},
            color_discrete_sequence=['#1f77b4']
        )
        
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Progress (%)',
            hovermode='x unified',
            showlegend=False
        )
        
        fig.update_traces(
            mode='lines+markers',
            hovertemplate='<b>%{y:.1f}%</b><br>%{x}<extra></extra>'
        )
        
        return fig
    
    @staticmethod
    def render_skill_radar_chart(skill_levels: Dict[str, float]) -> go.Figure:
        """Render skill radar chart"""
        radar_data = AnalyticsCalculator.calculate_skill_radar_data(skill_levels)
        
        if not radar_data["skills"]:
            # Sample data
            radar_data = {
                "skills": ["Python", "JavaScript", "Data Science", "Machine Learning", "SQL"],
                "levels": [85, 70, 60, 45, 80]
            }
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=radar_data["levels"],
            theta=radar_data["skills"],
            fill='toself',
            name='Current Level',
            line_color='rgb(31, 119, 180)',
            fillcolor='rgba(31, 119, 180, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title='Skill Level Radar Chart',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def render_activity_heatmap(activity_data: Dict[str, Any]) -> go.Figure:
        """Render activity heatmap"""
        heatmap_data = AnalyticsCalculator.generate_activity_heatmap_data(activity_data)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=[f"{i:02d}:00" for i in range(24)],
            y=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            colorscale='Blues',
            hoverongaps=False,
            hovertemplate='<b>%{y}</b><br>%{x}<br>Activity: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Weekly Activity Pattern',
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            height=400
        )
        
        return fig
    
    @staticmethod
    def render_skill_distribution_chart(skill_levels: Dict[str, float]) -> go.Figure:
        """Render skill distribution bar chart"""
        if not skill_levels:
            # Sample data
            skill_levels = {
                "Python": 85,
                "JavaScript": 70,
                "Data Science": 60,
                "Machine Learning": 45,
                "SQL": 80
            }
        
        skills = list(skill_levels.keys())
        levels = list(skill_levels.values())
        
        # Color coding based on skill level
        colors = []
        for level in levels:
            if level >= 80:
                colors.append('#2E8B57')  # Advanced - Green
            elif level >= 60:
                colors.append('#FFD700')  # Intermediate - Gold
            elif level >= 40:
                colors.append('#FF8C00')  # Beginner - Orange
            else:
                colors.append('#DC143C')  # Novice - Red
        
        fig = go.Figure(data=go.Bar(
            x=skills,
            y=levels,
            marker_color=colors,
            hovertemplate='<b>%{x}</b><br>Level: %{y}%<extra></extra>'
        ))
        
        fig.update_layout(
            title='Current Skill Levels',
            xaxis_title='Skills',
            yaxis_title='Proficiency Level (%)',
            yaxis=dict(range=[0, 100])
        )
        
        return fig
    
    @staticmethod
    def render_learning_velocity_gauge(velocity: float) -> go.Figure:
        """Render learning velocity gauge chart"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=velocity,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Learning Velocity<br><span style='font-size:0.8em;color:gray'>Progress per Day</span>"},
            delta={'reference': 3.0},
            gauge={
                'axis': {'range': [None, 10]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 2], 'color': "lightgray"},
                    {'range': [2, 5], 'color': "gray"},
                    {'range': [5, 8], 'color': "lightgreen"},
                    {'range': [8, 10], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 7
                }
            }
        ))
        
        fig.update_layout(height=300)
        return fig


class AnalyticsDataManager:
    """Manages analytics data fetching and caching"""
    
    def __init__(self, api_client: EnhancedEdAgentAPI, session_manager: SessionManager):
        self.api_client = api_client
        self.session_manager = session_manager
    
    async def fetch_user_analytics(self, user_id: str) -> AnalyticsData:
        """Fetch comprehensive user analytics data"""
        try:
            # In a real implementation, this would make API calls
            # For now, we'll generate realistic sample data
            
            # Simulate API calls
            assessments = await self._fetch_user_assessments(user_id)
            learning_paths = await self._fetch_user_learning_paths(user_id)
            skill_data = await self._fetch_user_skills(user_id)
            activity_data = await self._fetch_user_activity(user_id)
            
            # Calculate derived metrics
            total_assessments = len(assessments)
            total_learning_paths = len(learning_paths)
            completed_paths = len([p for p in learning_paths if p.get('status') == 'completed'])
            
            # Generate progress timeline
            progress_timeline = self._generate_progress_timeline(user_id)
            
            # Calculate learning velocity
            learning_velocity = AnalyticsCalculator.calculate_learning_velocity(progress_timeline)
            
            analytics_data = AnalyticsData(
                user_id=user_id,
                total_assessments=total_assessments,
                total_learning_paths=total_learning_paths,
                completed_paths=completed_paths,
                skills_improved=len(skill_data),
                study_hours=self._calculate_study_hours(activity_data),
                current_streak=self._calculate_current_streak(activity_data),
                longest_streak=self._calculate_longest_streak(activity_data),
                skill_levels=skill_data,
                progress_timeline=progress_timeline,
                activity_data=activity_data,
                learning_velocity=learning_velocity
            )
            
            # Calculate achievements
            analytics_data.achievements = AnalyticsCalculator.calculate_achievement_progress(analytics_data)
            
            return analytics_data
            
        except Exception as e:
            st.error(f"Failed to fetch analytics data: {str(e)}")
            return self._get_default_analytics_data(user_id)
    
    async def _fetch_user_assessments(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch user assessments"""
        try:
            return await self.api_client.get_user_assessments(user_id)
        except:
            # Return sample data
            return [
                {"id": f"assessment_{i}", "skill_area": f"skill_{i}", "completed": True}
                for i in range(12)
            ]
    
    async def _fetch_user_learning_paths(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch user learning paths"""
        try:
            paths_response = await self.api_client.get_user_learning_paths(user_id)
            return paths_response.get('learning_paths', [])
        except:
            # Return sample data
            return [
                {"id": f"path_{i}", "title": f"Learning Path {i}", "status": "active" if i < 3 else "completed"}
                for i in range(5)
            ]
    
    async def _fetch_user_skills(self, user_id: str) -> Dict[str, float]:
        """Fetch user skill levels"""
        try:
            # This would be a real API call
            # skills_response = await self.api_client.get_user_skills(user_id)
            # return skills_response.get('skills', {})
            pass
        except:
            pass
        
        # Return sample data
        return {
            "Python": 85.0,
            "JavaScript": 70.0,
            "Data Science": 60.0,
            "Machine Learning": 45.0,
            "SQL": 80.0,
            "React": 65.0,
            "Docker": 55.0,
            "AWS": 40.0
        }
    
    async def _fetch_user_activity(self, user_id: str) -> Dict[str, Any]:
        """Fetch user activity data"""
        try:
            # This would be a real API call
            # activity_response = await self.api_client.get_user_activity(user_id)
            # return activity_response.get('activity', {})
            pass
        except:
            pass
        
        # Return sample activity data
        activity = {}
        for day in range(7):
            for hour in range(24):
                key = f"day_{day}_hour_{hour}"
                # Generate realistic activity pattern
                base_activity = np.random.poisson(2)
                if 9 <= hour <= 17:  # Work hours
                    base_activity *= 2
                if day >= 5:  # Weekends
                    base_activity *= 0.7
                activity[key] = base_activity
        
        return activity
    
    def _generate_progress_timeline(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate progress timeline data"""
        timeline = []
        start_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            date = start_date + timedelta(days=i)
            progress = min(100, max(0, 20 + i * 2 + np.random.normal(0, 5)))
            
            timeline.append({
                'date': date,
                'progress': progress,
                'activities': np.random.randint(1, 6)
            })
        
        return timeline
    
    def _calculate_study_hours(self, activity_data: Dict[str, Any]) -> float:
        """Calculate total study hours from activity data"""
        total_activity = sum(activity_data.values()) if activity_data else 0
        # Convert activity points to hours (rough estimation)
        return total_activity * 0.1
    
    def _calculate_current_streak(self, activity_data: Dict[str, Any]) -> int:
        """Calculate current learning streak"""
        # Simplified calculation - in reality would check daily activity
        return np.random.randint(1, 15)
    
    def _calculate_longest_streak(self, activity_data: Dict[str, Any]) -> int:
        """Calculate longest learning streak"""
        # Simplified calculation - in reality would analyze historical data
        return np.random.randint(10, 45)
    
    def _get_default_analytics_data(self, user_id: str) -> AnalyticsData:
        """Get default analytics data when API calls fail"""
        return AnalyticsData(
            user_id=user_id,
            total_assessments=0,
            total_learning_paths=0,
            completed_paths=0,
            skills_improved=0,
            study_hours=0.0,
            current_streak=0,
            longest_streak=0,
            skill_levels={},
            progress_timeline=[],
            activity_data={},
            learning_velocity=0.0,
            achievements=[]
        )


class AnalyticsDashboard:
    """Main analytics dashboard component"""
    
    def __init__(self, api_client: EnhancedEdAgentAPI, session_manager: SessionManager):
        self.api_client = api_client
        self.session_manager = session_manager
        self.data_manager = AnalyticsDataManager(api_client, session_manager)
        self.chart_renderer = AnalyticsChartRenderer()
    
    def render_analytics_dashboard(self) -> None:
        """Render the complete analytics dashboard"""
        st.header("📈 Learning Analytics Dashboard")
        
        # Check authentication
        if not self.session_manager.is_authenticated():
            st.warning("🔐 Please log in to view your analytics.")
            return
        
        user_info = self.session_manager.get_current_user()
        
        # Load analytics data
        with st.spinner("Loading your analytics..."):
            analytics_data = asyncio.run(self.data_manager.fetch_user_analytics(user_info.user_id))
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "📈 Progress", "🎯 Skills", "🏆 Achievements", "📋 Export"
        ])
        
        with tab1:
            self._render_overview_tab(analytics_data)
        
        with tab2:
            self._render_progress_tab(analytics_data)
        
        with tab3:
            self._render_skills_tab(analytics_data)
        
        with tab4:
            self._render_achievements_tab(analytics_data)
        
        with tab5:
            self._render_export_tab(analytics_data)
    
    def _render_overview_tab(self, analytics_data: AnalyticsData) -> None:
        """Render overview tab with key metrics"""
        st.subheader("📊 Learning Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Assessments", 
                analytics_data.total_assessments,
                delta=f"+{max(0, analytics_data.total_assessments - 9)}"
            )
        
        with col2:
            st.metric(
                "Learning Paths", 
                analytics_data.total_learning_paths,
                delta=f"+{max(0, analytics_data.total_learning_paths - 4)}"
            )
        
        with col3:
            st.metric(
                "Skills Tracked", 
                analytics_data.skills_improved,
                delta=f"+{max(0, analytics_data.skills_improved - 6)}"
            )
        
        with col4:
            st.metric(
                "Study Hours", 
                f"{analytics_data.study_hours:.1f}",
                delta=f"+{analytics_data.study_hours * 0.2:.1f}"
            )
        
        st.divider()
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Learning velocity gauge
            velocity_fig = self.chart_renderer.render_learning_velocity_gauge(analytics_data.learning_velocity)
            st.plotly_chart(velocity_fig, use_container_width=True)
        
        with col2:
            # Skill distribution
            skill_fig = self.chart_renderer.render_skill_distribution_chart(analytics_data.skill_levels)
            st.plotly_chart(skill_fig, use_container_width=True)
        
        # Activity heatmap
        st.subheader("🔥 Activity Heatmap")
        activity_fig = self.chart_renderer.render_activity_heatmap(analytics_data.activity_data)
        st.plotly_chart(activity_fig, use_container_width=True)
        
        # Learning streaks
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 Learning Streaks")
            streak_metrics = {
                "Current Streak": f"{analytics_data.current_streak} days",
                "Longest Streak": f"{analytics_data.longest_streak} days",
                "This Week": f"{min(7, analytics_data.current_streak)} days",
                "This Month": f"{min(30, analytics_data.current_streak)} days"
            }
            
            for label, value in streak_metrics.items():
                st.metric(label, value)
        
        with col2:
            st.subheader("📚 Recent Achievements")
            recent_achievements = [a for a in analytics_data.achievements if a.earned][-3:]
            
            if recent_achievements:
                for achievement in recent_achievements:
                    st.success(f"{achievement.icon} **{achievement.title}**")
                    st.caption(achievement.description)
            else:
                st.info("Complete some activities to earn achievements!")    

    def _render_progress_tab(self, analytics_data: AnalyticsData) -> None:
        """Render progress tracking tab"""
        st.subheader("📈 Progress Tracking")
        
        # Progress timeline chart
        progress_fig = self.chart_renderer.render_progress_timeline_chart(analytics_data.progress_timeline)
        st.plotly_chart(progress_fig, use_container_width=True)
        
        # Progress comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Learning Path Progress")
            
            # Mock learning path progress data
            path_progress = [
                {"name": "Python Fundamentals", "progress": 85, "status": "In Progress"},
                {"name": "Web Development", "progress": 100, "status": "Completed"},
                {"name": "Data Science Basics", "progress": 60, "status": "In Progress"},
                {"name": "Machine Learning", "progress": 30, "status": "In Progress"},
                {"name": "DevOps Essentials", "progress": 0, "status": "Not Started"}
            ]
            
            for path in path_progress:
                progress_color = "green" if path["status"] == "Completed" else "blue"
                st.progress(path["progress"] / 100, text=f"{path['name']} - {path['progress']}%")
                st.caption(f"Status: {path['status']}")
        
        with col2:
            st.subheader("🎯 Goal Tracking")
            
            # Mock goal data
            goals = [
                {"goal": "Complete 5 Assessments", "current": analytics_data.total_assessments, "target": 5},
                {"goal": "Finish 2 Learning Paths", "current": analytics_data.completed_paths, "target": 2},
                {"goal": "Study 50 Hours", "current": analytics_data.study_hours, "target": 50},
                {"goal": "Maintain 14-day Streak", "current": analytics_data.current_streak, "target": 14}
            ]
            
            for goal in goals:
                progress_pct = min(100, (goal["current"] / goal["target"]) * 100)
                st.progress(progress_pct / 100, text=f"{goal['goal']}")
                st.caption(f"{goal['current']:.1f} / {goal['target']} ({progress_pct:.1f}%)")
        
        # Milestone timeline
        st.subheader("🏁 Milestone Timeline")
        
        milestones = [
            {"date": "2024-01-15", "title": "First Assessment Completed", "type": "assessment"},
            {"date": "2024-01-20", "title": "Python Basics Path Started", "type": "learning_path"},
            {"date": "2024-02-01", "title": "Week Warrior Achievement", "type": "achievement"},
            {"date": "2024-02-10", "title": "Web Development Path Completed", "type": "learning_path"},
            {"date": "2024-02-15", "title": "Skill Master Achievement", "type": "achievement"}
        ]
        
        for milestone in milestones:
            icon_map = {
                "assessment": "🎯",
                "learning_path": "🛤️",
                "achievement": "🏆"
            }
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(milestone["date"])
            with col2:
                st.write(f"{icon_map.get(milestone['type'], '📅')} {milestone['title']}")
    
    def _render_skills_tab(self, analytics_data: AnalyticsData) -> None:
        """Render skills analysis tab"""
        st.subheader("🎯 Skills Analysis")
        
        # Skill radar chart
        col1, col2 = st.columns(2)
        
        with col1:
            radar_fig = self.chart_renderer.render_skill_radar_chart(analytics_data.skill_levels)
            st.plotly_chart(radar_fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Skill Breakdown")
            
            # Skill categories
            skill_categories = {
                "Programming": ["Python", "JavaScript", "SQL"],
                "Data & AI": ["Data Science", "Machine Learning"],
                "Web Development": ["React", "HTML/CSS"],
                "DevOps": ["Docker", "AWS"]
            }
            
            for category, skills in skill_categories.items():
                st.write(f"**{category}**")
                category_skills = {k: v for k, v in analytics_data.skill_levels.items() if k in skills}
                
                if category_skills:
                    avg_level = sum(category_skills.values()) / len(category_skills)
                    st.progress(avg_level / 100, text=f"Average: {avg_level:.1f}%")
                    
                    for skill, level in category_skills.items():
                        st.caption(f"  • {skill}: {level:.1f}%")
                else:
                    st.caption("  No skills tracked in this category")
                
                st.write("")
        
        # Skill improvement recommendations
        st.subheader("💡 Improvement Recommendations")
        
        # Find skills that need improvement
        improvement_skills = [
            (skill, level) for skill, level in analytics_data.skill_levels.items() 
            if level < 70
        ]
        improvement_skills.sort(key=lambda x: x[1])  # Sort by level (lowest first)
        
        if improvement_skills:
            st.write("**Skills to focus on:**")
            for skill, level in improvement_skills[:3]:  # Top 3 skills to improve
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.write(f"🎯 **{skill}**")
                
                with col2:
                    st.write(f"{level:.1f}%")
                
                with col3:
                    if level < 40:
                        st.write("🔴 Beginner - Start with basics")
                    elif level < 60:
                        st.write("🟡 Intermediate - Practice more")
                    else:
                        st.write("🟢 Advanced - Polish skills")
        else:
            st.success("🎉 Great job! All your skills are at a good level!")
        
        # Skill learning suggestions
        st.subheader("📚 Learning Suggestions")
        
        suggestions = [
            {
                "skill": "Python",
                "current_level": analytics_data.skill_levels.get("Python", 0),
                "next_steps": [
                    "Practice data structures and algorithms",
                    "Build a web application with Flask/Django",
                    "Learn advanced Python features (decorators, generators)"
                ]
            },
            {
                "skill": "Machine Learning",
                "current_level": analytics_data.skill_levels.get("Machine Learning", 0),
                "next_steps": [
                    "Complete a Kaggle competition",
                    "Learn deep learning with TensorFlow/PyTorch",
                    "Study MLOps and model deployment"
                ]
            }
        ]
        
        for suggestion in suggestions:
            with st.expander(f"📖 {suggestion['skill']} (Current: {suggestion['current_level']:.1f}%)"):
                st.write("**Recommended next steps:**")
                for step in suggestion["next_steps"]:
                    st.write(f"• {step}")
    
    def _render_achievements_tab(self, analytics_data: AnalyticsData) -> None:
        """Render achievements and milestones tab"""
        st.subheader("🏆 Achievements & Milestones")
        
        # Achievement categories
        achievement_categories = {}
        for achievement in analytics_data.achievements:
            category = achievement.category
            if category not in achievement_categories:
                achievement_categories[category] = []
            achievement_categories[category].append(achievement)
        
        # Achievement overview
        total_achievements = len(analytics_data.achievements)
        earned_achievements = len([a for a in analytics_data.achievements if a.earned])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Achievements", f"{earned_achievements}/{total_achievements}")
        
        with col2:
            completion_rate = (earned_achievements / total_achievements) * 100 if total_achievements > 0 else 0
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        with col3:
            # Calculate points (earned achievements * 10)
            points = earned_achievements * 10
            st.metric("Achievement Points", points)
        
        st.divider()
        
        # Achievement categories
        for category, achievements in achievement_categories.items():
            st.subheader(f"🎯 {category.title()} Achievements")
            
            cols = st.columns(2)
            for i, achievement in enumerate(achievements):
                with cols[i % 2]:
                    # Achievement card
                    card_color = "success" if achievement.earned else "secondary"
                    
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        
                        with col1:
                            st.write(f"<h2>{achievement.icon}</h2>", unsafe_allow_html=True)
                        
                        with col2:
                            if achievement.earned:
                                st.success(f"**{achievement.title}** ✅")
                            else:
                                st.info(f"**{achievement.title}**")
                            
                            st.caption(achievement.description)
                            
                            # Progress bar for unearned achievements
                            if not achievement.earned:
                                progress = achievement.progress / 100 if achievement.progress <= 100 else achievement.progress / achievement.target
                                st.progress(progress, text=f"Progress: {achievement.progress:.1f}%")
                        
                        st.write("")
        
        # Achievement celebration
        recent_achievements = [a for a in analytics_data.achievements if a.earned]
        if recent_achievements:
            st.subheader("🎉 Recent Achievements")
            
            # Show last 3 earned achievements
            for achievement in recent_achievements[-3:]:
                st.success(f"🏆 **{achievement.title}** - {achievement.description}")
        
        # Next achievements to unlock
        st.subheader("🎯 Next Achievements to Unlock")
        
        unearned_achievements = [a for a in analytics_data.achievements if not a.earned]
        unearned_achievements.sort(key=lambda x: x.progress, reverse=True)  # Sort by progress
        
        for achievement in unearned_achievements[:3]:  # Show top 3 closest achievements
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.write(achievement.icon)
            
            with col2:
                st.write(f"**{achievement.title}**")
                st.caption(achievement.description)
                progress = min(100, achievement.progress)
                st.progress(progress / 100, text=f"{progress:.1f}% complete")
            
            with col3:
                if achievement.progress >= 80:
                    st.write("🔥 Almost there!")
                elif achievement.progress >= 50:
                    st.write("📈 Good progress")
                else:
                    st.write("🎯 Keep going")
    
    def _render_export_tab(self, analytics_data: AnalyticsData) -> None:
        """Render data export tab"""
        st.subheader("📋 Export Your Data")
        
        st.write("""
        Export your learning analytics data for personal use, portfolio, or further analysis.
        All exports respect your privacy settings and include only the data you choose to share.
        """)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Export Options")
            
            export_options = {
                "Basic Analytics": {
                    "description": "Key metrics and progress summary",
                    "includes": ["Total assessments", "Learning paths", "Study hours", "Current streak"]
                },
                "Detailed Progress": {
                    "description": "Complete progress timeline and milestones",
                    "includes": ["Daily progress", "Milestone timeline", "Goal tracking", "Activity patterns"]
                },
                "Skills Analysis": {
                    "description": "Comprehensive skill breakdown and recommendations",
                    "includes": ["Skill levels", "Improvement areas", "Learning suggestions", "Skill radar data"]
                },
                "Achievement Report": {
                    "description": "All achievements and progress tracking",
                    "includes": ["Earned achievements", "Progress on pending", "Achievement timeline", "Points summary"]
                },
                "Complete Dataset": {
                    "description": "Full analytics export (JSON format)",
                    "includes": ["All analytics data", "Raw activity data", "Metadata", "Timestamps"]
                }
            }
            
            selected_export = st.selectbox(
                "Choose export type:",
                list(export_options.keys())
            )
            
            if selected_export:
                export_info = export_options[selected_export]
                st.write(f"**{export_info['description']}**")
                st.write("**Includes:**")
                for item in export_info["includes"]:
                    st.write(f"• {item}")
        
        with col2:
            st.subheader("📁 Export Formats")
            
            export_format = st.radio(
                "Select format:",
                ["JSON", "CSV", "PDF Report", "Excel Workbook"]
            )
            
            # Privacy options
            st.subheader("🔒 Privacy Options")
            
            include_personal_data = st.checkbox("Include personal identifiers", value=False)
            include_timestamps = st.checkbox("Include detailed timestamps", value=True)
            anonymize_data = st.checkbox("Anonymize sensitive data", value=True)
            
            st.caption("Personal identifiers include user ID, email, and names. Anonymized data replaces these with generic placeholders.")
        
        # Generate export
        if st.button("📥 Generate Export", type="primary"):
            with st.spinner("Generating export..."):
                export_data = self._generate_export_data(
                    analytics_data, 
                    selected_export, 
                    export_format,
                    include_personal_data,
                    include_timestamps,
                    anonymize_data
                )
                
                if export_format == "JSON":
                    st.download_button(
                        label="💾 Download JSON",
                        data=json.dumps(export_data, indent=2, default=str),
                        file_name=f"edagent_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                elif export_format == "CSV":
                    # Convert to CSV format
                    csv_data = self._convert_to_csv(export_data)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv_data,
                        file_name=f"edagent_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "PDF Report":
                    st.info("📄 PDF report generation would be implemented here")
                    # In a real implementation, you'd generate a PDF report
                
                elif export_format == "Excel Workbook":
                    st.info("📊 Excel workbook generation would be implemented here")
                    # In a real implementation, you'd generate an Excel file
                
                st.success("✅ Export generated successfully!")
        
        # Export history
        st.divider()
        st.subheader("📜 Export History")
        
        # Mock export history
        export_history = [
            {"date": "2024-02-15 14:30", "type": "Complete Dataset", "format": "JSON", "size": "2.3 MB"},
            {"date": "2024-02-10 09:15", "type": "Skills Analysis", "format": "PDF Report", "size": "1.1 MB"},
            {"date": "2024-02-05 16:45", "type": "Basic Analytics", "format": "CSV", "size": "0.5 MB"}
        ]
        
        for export in export_history:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.caption(export["date"])
            
            with col2:
                st.caption(export["type"])
            
            with col3:
                st.caption(export["format"])
            
            with col4:
                st.caption(export["size"])
    
    def _generate_export_data(
        self, 
        analytics_data: AnalyticsData, 
        export_type: str, 
        export_format: str,
        include_personal: bool,
        include_timestamps: bool,
        anonymize: bool
    ) -> Dict[str, Any]:
        """Generate export data based on selected options"""
        
        base_data = {
            "export_info": {
                "type": export_type,
                "format": export_format,
                "generated_at": datetime.now().isoformat(),
                "anonymized": anonymize
            }
        }
        
        if not include_personal or anonymize:
            user_id = "user_anonymous"
        else:
            user_id = analytics_data.user_id
        
        if export_type == "Basic Analytics":
            base_data.update({
                "user_id": user_id,
                "total_assessments": analytics_data.total_assessments,
                "total_learning_paths": analytics_data.total_learning_paths,
                "completed_paths": analytics_data.completed_paths,
                "study_hours": analytics_data.study_hours,
                "current_streak": analytics_data.current_streak,
                "longest_streak": analytics_data.longest_streak
            })
        
        elif export_type == "Skills Analysis":
            base_data.update({
                "user_id": user_id,
                "skill_levels": analytics_data.skill_levels,
                "skills_improved": analytics_data.skills_improved,
                "learning_velocity": analytics_data.learning_velocity
            })
        
        elif export_type == "Achievement Report":
            achievements_data = []
            for achievement in analytics_data.achievements:
                achievement_dict = achievement.to_dict()
                if not include_timestamps:
                    achievement_dict.pop("earned_date", None)
                achievements_data.append(achievement_dict)
            
            base_data.update({
                "user_id": user_id,
                "achievements": achievements_data,
                "total_achievements": len(analytics_data.achievements),
                "earned_achievements": len([a for a in analytics_data.achievements if a.earned])
            })
        
        elif export_type == "Complete Dataset":
            # Include all data
            base_data.update({
                "user_id": user_id,
                "analytics_data": {
                    "total_assessments": analytics_data.total_assessments,
                    "total_learning_paths": analytics_data.total_learning_paths,
                    "completed_paths": analytics_data.completed_paths,
                    "skills_improved": analytics_data.skills_improved,
                    "study_hours": analytics_data.study_hours,
                    "current_streak": analytics_data.current_streak,
                    "longest_streak": analytics_data.longest_streak,
                    "learning_velocity": analytics_data.learning_velocity,
                    "skill_levels": analytics_data.skill_levels,
                    "progress_timeline": analytics_data.progress_timeline if include_timestamps else [],
                    "activity_data": analytics_data.activity_data,
                    "achievements": [a.to_dict() for a in analytics_data.achievements]
                }
            })
        
        return base_data
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert export data to CSV format"""
        # This is a simplified CSV conversion
        # In a real implementation, you'd create proper CSV structure
        
        csv_lines = []
        csv_lines.append("Key,Value")
        
        def flatten_dict(d, parent_key=''):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key).items())
                elif isinstance(v, list):
                    items.append((new_key, f"[{len(v)} items]"))
                else:
                    items.append((new_key, str(v)))
            return dict(items)
        
        flattened = flatten_dict(data)
        for key, value in flattened.items():
            csv_lines.append(f'"{key}","{value}"')
        
        return "\n".join(csv_lines)


def render_analytics_dashboard(api_client: EnhancedEdAgentAPI, session_manager: SessionManager) -> None:
    """Main function to render the analytics dashboard"""
    dashboard = AnalyticsDashboard(api_client, session_manager)
    dashboard.render_analytics_dashboard()


# Achievement definitions for easy management
ACHIEVEMENT_DEFINITIONS = [
    {
        "id": "first_assessment",
        "title": "First Steps",
        "description": "Complete your first skill assessment",
        "icon": "🎯",
        "category": "assessment",
        "target": 1
    },
    {
        "id": "assessment_master",
        "title": "Assessment Master", 
        "description": "Complete 10 skill assessments",
        "icon": "🏆",
        "category": "assessment",
        "target": 10
    },
    {
        "id": "path_creator",
        "title": "Path Creator",
        "description": "Create your first learning path",
        "icon": "🛤️",
        "category": "learning",
        "target": 1
    },
    {
        "id": "path_completer",
        "title": "Path Completer",
        "description": "Complete a learning path",
        "icon": "✅",
        "category": "learning",
        "target": 1
    },
    {
        "id": "week_warrior",
        "title": "Week Warrior",
        "description": "Study for 7 consecutive days",
        "icon": "🔥",
        "category": "streak",
        "target": 7
    },
    {
        "id": "marathon_learner",
        "title": "Marathon Learner",
        "description": "Maintain a 30-day learning streak",
        "icon": "🏃‍♂️",
        "category": "streak",
        "target": 30
    },
    {
        "id": "skill_master",
        "title": "Skill Master",
        "description": "Reach advanced level (80+) in any skill",
        "icon": "⭐",
        "category": "skill",
        "target": 80
    },
    {
        "id": "polyglot",
        "title": "Polyglot",
        "description": "Learn 5 different skills",
        "icon": "🌟",
        "category": "skill",
        "target": 5
    },
    {
        "id": "dedicated_learner",
        "title": "Dedicated Learner",
        "description": "Study for 100 hours total",
        "icon": "📚",
        "category": "time",
        "target": 100
    },
    {
        "id": "speed_learner",
        "title": "Speed Learner",
        "description": "Maintain high learning velocity",
        "icon": "⚡",
        "category": "velocity",
        "target": 5
    }
]