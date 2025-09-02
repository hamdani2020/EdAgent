"""
Custom Streamlit components for EdAgent frontend
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

def render_skill_assessment_widget(api_client, user_id: str):
    """Render interactive skill assessment widget"""
    st.subheader("🎯 Interactive Skill Assessment")
    
    # Assessment categories
    categories = {
        "Programming": ["Python", "JavaScript", "Java", "C++", "Go"],
        "Web Development": ["HTML/CSS", "React", "Vue.js", "Node.js", "Django"],
        "Data Science": ["Pandas", "NumPy", "Matplotlib", "Scikit-learn", "TensorFlow"],
        "Cloud & DevOps": ["AWS", "Docker", "Kubernetes", "CI/CD", "Terraform"],
        "Databases": ["SQL", "MongoDB", "PostgreSQL", "Redis", "Elasticsearch"]
    }
    
    selected_category = st.selectbox("Select Category:", list(categories.keys()))
    selected_skill = st.selectbox("Select Skill:", categories[selected_category])
    
    col1, col2 = st.columns(2)
    
    with col1:
        experience_level = st.radio(
            "Your experience level:",
            ["Never used", "Beginner", "Intermediate", "Advanced", "Expert"]
        )
        
        confidence = st.slider("Confidence level (1-10):", 1, 10, 5)
    
    with col2:
        years_experience = st.number_input("Years of experience:", 0.0, 20.0, 0.0, 0.5)
        
        project_count = st.number_input("Number of projects:", 0, 100, 0)
    
    if st.button("Start Detailed Assessment", key="detailed_assessment"):
        # Start assessment
        result = api_client.start_assessment(user_id, selected_skill.lower())
        if result:
            st.success(f"✅ Started {selected_skill} assessment!")
            
            # Show sample questions (mock)
            st.subheader("Assessment Questions")
            
            questions = [
                f"How would you implement a basic {selected_skill} application?",
                f"What are the key concepts in {selected_skill} that you're familiar with?",
                f"Describe a challenging {selected_skill} project you've worked on.",
                f"What tools and libraries do you use with {selected_skill}?"
            ]
            
            for i, question in enumerate(questions, 1):
                with st.expander(f"Question {i}"):
                    st.write(question)
                    answer = st.text_area(f"Your answer:", key=f"q_{i}")
                    if answer:
                        st.info("Answer recorded ✓")

def render_learning_path_builder(api_client, user_id: str):
    """Render learning path builder widget"""
    st.subheader("🛤️ Learning Path Builder")
    
    # Step 1: Goal Setting
    with st.expander("Step 1: Define Your Goal", expanded=True):
        goal_type = st.selectbox(
            "What type of goal?",
            ["Career Change", "Skill Enhancement", "New Technology", "Certification", "Project-based"]
        )
        
        if goal_type == "Career Change":
            current_role = st.text_input("Current role:")
            target_role = st.text_input("Target role:")
            timeline = st.selectbox("Timeline:", ["3 months", "6 months", "1 year", "2+ years"])
            
        elif goal_type == "Skill Enhancement":
            skill_area = st.text_input("Skill to enhance:")
            current_level = st.selectbox("Current level:", ["Beginner", "Intermediate", "Advanced"])
            target_level = st.selectbox("Target level:", ["Intermediate", "Advanced", "Expert"])
            
        goal_description = st.text_area(
            "Describe your goal in detail:",
            placeholder="e.g., I want to transition from marketing to data science within 6 months"
        )
    
    # Step 2: Preferences
    with st.expander("Step 2: Learning Preferences"):
        col1, col2 = st.columns(2)
        
        with col1:
            time_per_week = st.slider("Hours per week:", 1, 40, 10)
            learning_style = st.multiselect(
                "Preferred learning styles:",
                ["Video tutorials", "Reading", "Hands-on projects", "Interactive courses", "Mentorship"]
            )
        
        with col2:
            budget = st.selectbox("Budget:", ["Free only", "Under $50/month", "Under $100/month", "No limit"])
            platforms = st.multiselect(
                "Preferred platforms:",
                ["YouTube", "Coursera", "Udemy", "edX", "Pluralsight", "LinkedIn Learning"]
            )
    
    # Step 3: Generate Path
    if st.button("Generate Learning Path", key="generate_path"):
        if goal_description:
            with st.spinner("Creating your personalized learning path..."):
                result = api_client.create_learning_path(user_id, goal_description)
                if result:
                    st.success("✅ Learning path created!")
                    
                    # Display generated path (mock)
                    st.subheader("Your Learning Path")
                    
                    milestones = [
                        {"title": "Foundation", "duration": "2 weeks", "skills": ["Basics", "Setup"]},
                        {"title": "Core Concepts", "duration": "4 weeks", "skills": ["Key principles", "Best practices"]},
                        {"title": "Practical Application", "duration": "3 weeks", "skills": ["Projects", "Real-world examples"]},
                        {"title": "Advanced Topics", "duration": "3 weeks", "skills": ["Advanced features", "Optimization"]},
                        {"title": "Portfolio Project", "duration": "2 weeks", "skills": ["Integration", "Deployment"]}
                    ]
                    
                    for i, milestone in enumerate(milestones, 1):
                        with st.container():
                            col1, col2, col3 = st.columns([1, 3, 1])
                            
                            with col1:
                                st.write(f"**Week {i*2-1}-{i*2}**")
                            
                            with col2:
                                st.write(f"**{milestone['title']}**")
                                st.write(f"Skills: {', '.join(milestone['skills'])}")
                            
                            with col3:
                                st.write(milestone['duration'])
                            
                            st.divider()
        else:
            st.error("Please describe your goal")

def render_progress_dashboard(user_data: Dict[str, Any]):
    """Render user progress dashboard"""
    st.subheader("📊 Your Progress Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Skills Assessed",
            user_data.get("skills_assessed", 0),
            delta=user_data.get("skills_delta", 0)
        )
    
    with col2:
        st.metric(
            "Learning Paths",
            user_data.get("learning_paths", 0),
            delta=user_data.get("paths_delta", 0)
        )
    
    with col3:
        st.metric(
            "Hours Studied",
            user_data.get("study_hours", 0),
            delta=user_data.get("hours_delta", 0)
        )
    
    with col4:
        st.metric(
            "Completion Rate",
            f"{user_data.get('completion_rate', 0):.1%}",
            delta=f"{user_data.get('completion_delta', 0):.1%}"
        )
    
    # Progress charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Skill levels radar chart
        skills = user_data.get("skills", {})
        if skills:
            categories = list(skills.keys())
            values = [skills[cat].get("level", 0) for cat in categories]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Current Level'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Skill Levels"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Learning progress over time
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        progress = [i + (i % 7) * 2 for i in range(30)]
        
        df = pd.DataFrame({'Date': dates, 'Progress': progress})
        
        fig = px.line(df, x='Date', y='Progress', title='Learning Progress')
        st.plotly_chart(fig, use_container_width=True)

def render_resource_recommendations(recommendations: List[Dict[str, Any]]):
    """Render learning resource recommendations"""
    st.subheader("📚 Recommended Resources")
    
    if not recommendations:
        st.info("No recommendations available. Complete a skill assessment to get personalized recommendations!")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        content_type = st.selectbox(
            "Content Type:",
            ["All", "Video", "Article", "Course", "Book", "Interactive"]
        )
    
    with col2:
        difficulty = st.selectbox(
            "Difficulty:",
            ["All", "Beginner", "Intermediate", "Advanced"]
        )
    
    with col3:
        cost = st.selectbox(
            "Cost:",
            ["All", "Free", "Paid", "Premium"]
        )
    
    # Display recommendations
    for i, rec in enumerate(recommendations):
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                # Resource type icon
                type_icons = {
                    "video": "🎥",
                    "article": "📄",
                    "course": "🎓",
                    "book": "📚",
                    "interactive": "💻"
                }
                st.write(f"{type_icons.get(rec.get('type', 'course'), '📚')} {rec.get('type', 'Course').title()}")
            
            with col2:
                st.write(f"**{rec.get('title', 'Resource Title')}**")
                st.write(rec.get('description', 'No description available'))
                
                # Tags
                tags = rec.get('tags', [])
                if tags:
                    tag_str = " ".join([f"`{tag}`" for tag in tags[:3]])
                    st.markdown(tag_str)
            
            with col3:
                # Rating and cost
                rating = rec.get('rating', 0)
                if rating > 0:
                    st.write(f"⭐ {rating:.1f}")
                
                cost_info = rec.get('cost', 'Free')
                color = "green" if cost_info == "Free" else "orange"
                st.markdown(f":{color}[{cost_info}]")
                
                if st.button("View", key=f"view_{i}"):
                    st.info(f"Opening: {rec.get('url', '#')}")
            
            st.divider()

def render_interview_prep_widget():
    """Render interview preparation widget"""
    st.subheader("🎤 Interview Preparation")
    
    # Interview type selection
    interview_type = st.selectbox(
        "Interview Type:",
        ["Technical", "Behavioral", "System Design", "Case Study", "General"]
    )
    
    role_type = st.text_input("Role/Position:", placeholder="e.g., Software Engineer, Data Scientist")
    
    if st.button("Generate Practice Questions", key="generate_questions"):
        st.subheader("Practice Questions")
        
        # Mock questions based on type
        questions = {
            "Technical": [
                "Explain the difference between a list and a tuple in Python.",
                "How would you optimize a slow database query?",
                "Describe the concept of Big O notation.",
                "What is the difference between supervised and unsupervised learning?"
            ],
            "Behavioral": [
                "Tell me about a time you faced a challenging problem at work.",
                "How do you handle tight deadlines?",
                "Describe a situation where you had to work with a difficult team member.",
                "What motivates you in your work?"
            ],
            "System Design": [
                "Design a URL shortening service like bit.ly.",
                "How would you design a chat application?",
                "Design a recommendation system for an e-commerce platform.",
                "How would you handle scaling a web application?"
            ]
        }
        
        question_list = questions.get(interview_type, questions["Technical"])
        
        for i, question in enumerate(question_list, 1):
            with st.expander(f"Question {i}"):
                st.write(f"**Q:** {question}")
                
                # Answer input
                answer = st.text_area(f"Your answer:", key=f"answer_{i}", height=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Get Tips", key=f"tips_{i}"):
                        st.info("💡 **Tip:** Structure your answer using the STAR method (Situation, Task, Action, Result)")
                
                with col2:
                    if st.button(f"Practice", key=f"practice_{i}"):
                        st.success("🎯 Great! Practice this answer out loud for better delivery.")

def render_resume_analyzer():
    """Render resume analysis widget"""
    st.subheader("📄 Resume Analyzer")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF or TXT):",
        type=['pdf', 'txt', 'docx'],
        help="Upload your resume for AI-powered analysis and feedback"
    )
    
    if uploaded_file is not None:
        st.success("✅ Resume uploaded successfully!")
        
        # Analysis options
        analysis_type = st.selectbox(
            "Analysis Type:",
            ["General Review", "ATS Optimization", "Industry-Specific", "Skills Gap Analysis"]
        )
        
        target_role = st.text_input("Target Role (optional):", placeholder="e.g., Software Engineer")
        
        if st.button("Analyze Resume", key="analyze_resume"):
            with st.spinner("Analyzing your resume..."):
                # Mock analysis results
                st.subheader("📊 Analysis Results")
                
                # Overall score
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Overall Score", "78/100", "+5")
                
                with col2:
                    st.metric("ATS Compatibility", "85%", "+10%")
                
                with col3:
                    st.metric("Keyword Match", "72%", "+8%")
                
                # Detailed feedback
                st.subheader("🔍 Detailed Feedback")
                
                feedback_sections = {
                    "Strengths": [
                        "Clear professional summary",
                        "Quantified achievements",
                        "Relevant technical skills listed"
                    ],
                    "Areas for Improvement": [
                        "Add more action verbs",
                        "Include specific project outcomes",
                        "Optimize for ATS keywords"
                    ],
                    "Suggestions": [
                        "Add a skills section with relevant technologies",
                        "Include links to portfolio/GitHub",
                        "Tailor content for target role"
                    ]
                }
                
                for section, items in feedback_sections.items():
                    with st.expander(section):
                        for item in items:
                            st.write(f"• {item}")
                
                # Action items
                st.subheader("✅ Action Items")
                
                action_items = [
                    "Update professional summary to include target role keywords",
                    "Add 2-3 more quantified achievements",
                    "Include relevant certifications or courses",
                    "Optimize formatting for ATS systems"
                ]
                
                for i, item in enumerate(action_items, 1):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"{i}. {item}")
                    with col2:
                        if st.button("Done", key=f"action_{i}"):
                            st.success("✓")

def render_career_roadmap():
    """Render career roadmap visualization"""
    st.subheader("🗺️ Career Roadmap")
    
    # Career path selection
    career_paths = {
        "Software Engineer": {
            "Junior Developer": ["HTML/CSS", "JavaScript", "Git"],
            "Mid-level Developer": ["React/Vue", "Node.js", "Databases"],
            "Senior Developer": ["System Design", "Architecture", "Leadership"],
            "Tech Lead": ["Team Management", "Project Planning", "Mentoring"],
            "Engineering Manager": ["People Management", "Strategy", "Business Acumen"]
        },
        "Data Scientist": {
            "Data Analyst": ["SQL", "Excel", "Basic Statistics"],
            "Junior Data Scientist": ["Python/R", "Machine Learning", "Visualization"],
            "Data Scientist": ["Advanced ML", "Deep Learning", "MLOps"],
            "Senior Data Scientist": ["Research", "Model Architecture", "Team Leadership"],
            "Principal Data Scientist": ["Strategy", "Innovation", "Cross-functional Leadership"]
        }
    }
    
    selected_path = st.selectbox("Select Career Path:", list(career_paths.keys()))
    
    # Visualize roadmap
    path_data = career_paths[selected_path]
    
    # Create a timeline visualization
    levels = list(path_data.keys())
    
    for i, level in enumerate(levels):
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.write(f"**Level {i+1}**")
        
        with col2:
            st.write(f"**{level}**")
            skills = path_data[level]
            skill_tags = " ".join([f"`{skill}`" for skill in skills])
            st.markdown(skill_tags)
        
        with col3:
            if i < len(levels) - 1:
                st.write("⬇️")
        
        if i < len(levels) - 1:
            st.divider()
    
    # Progress tracking
    st.subheader("📈 Your Progress")
    
    current_level = st.selectbox("Current Level:", levels)
    current_index = levels.index(current_level)
    
    progress = (current_index + 1) / len(levels)
    st.progress(progress)
    st.write(f"Progress: {progress:.1%} ({current_index + 1}/{len(levels)} levels)")
    
    # Next steps
    if current_index < len(levels) - 1:
        next_level = levels[current_index + 1]
        next_skills = path_data[next_level]
        
        st.subheader("🎯 Next Steps")
        st.write(f"To reach **{next_level}**, focus on:")
        
        for skill in next_skills:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"• {skill}")
            with col2:
                if st.button("Learn", key=f"learn_{skill}"):
                    st.info(f"Starting learning path for {skill}")