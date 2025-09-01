"""
Demo script showing resume analysis functionality
"""

import asyncio
from datetime import date
from edagent.models.resume import Resume, WorkExperience, Education, IndustryType
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum
from edagent.services.resume_analyzer import ResumeAnalyzer
from edagent.services.conversation_manager import ConversationManager


async def demo_resume_analysis():
    """Demonstrate resume analysis functionality"""
    
    print("🎯 EdAgent Resume Analysis Demo")
    print("=" * 50)
    
    # Create a sample resume
    work_exp = WorkExperience(
        job_title="Junior Software Developer",
        company="TechStart Inc",
        start_date=date(2022, 3, 1),
        end_date=date(2024, 1, 15),
        description="Developed web applications using React and Node.js. Collaborated with senior developers on feature implementation and bug fixes.",
        achievements=[
            "Improved application load time by 35%",
            "Implemented 20+ new user features",
            "Reduced customer-reported bugs by 40%",
            "Mentored 2 new junior developers"
        ],
        skills_used=["JavaScript", "React", "Node.js", "MongoDB", "Git"]
    )
    
    education = Education(
        degree="Bachelor of Science in Computer Science",
        institution="State University",
        graduation_date=date(2022, 5, 15),
        gpa=3.7,
        relevant_coursework=["Data Structures", "Web Development", "Software Engineering"],
        honors=["Dean's List", "Magna Cum Laude"]
    )
    
    resume = Resume(
        user_id="demo_user",
        name="Sarah Johnson",
        email="sarah.johnson@email.com",
        phone="+1-555-0123",
        location="Austin, TX",
        summary="Motivated software developer with 2 years of experience in full-stack web development. Passionate about creating efficient, user-friendly applications and continuously learning new technologies.",
        work_experience=[work_exp],
        education=[education],
        skills=["JavaScript", "React", "Node.js", "Python", "MongoDB", "PostgreSQL", "Git", "Docker"],
        certifications=["AWS Certified Developer Associate", "React Developer Certification"],
        projects=[
            {
                "name": "Personal Finance Tracker",
                "description": "Full-stack web app for tracking expenses and budgets",
                "technologies": ["React", "Node.js", "MongoDB"]
            }
        ],
        target_industry=IndustryType.TECHNOLOGY,
        target_role="Software Developer"
    )
    
    # Create user context
    user_context = UserContext(
        user_id="demo_user",
        career_goals=["become a senior software developer", "work at a major tech company"],
        current_skills={
            "javascript": SkillLevel("javascript", SkillLevelEnum.INTERMEDIATE, 0.8),
            "react": SkillLevel("react", SkillLevelEnum.INTERMEDIATE, 0.7),
            "python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.5)
        }
    )
    
    print(f"📄 Analyzing resume for: {resume.name}")
    print(f"🎯 Target role: {resume.target_role}")
    print(f"🏢 Target industry: {resume.target_industry.value}")
    print(f"💼 Experience: {resume.get_total_experience_months()} months")
    print(f"📚 Education: {resume.education[0].degree}")
    print()
    
    # Create analyzer (without AI service for demo)
    analyzer = ResumeAnalyzer(ai_service=None)
    
    # Perform analysis
    print("🔍 Performing resume analysis...")
    analysis = await analyzer.analyze_resume(resume, user_context)
    
    # Display results
    print("\n📊 ANALYSIS RESULTS")
    print("=" * 30)
    print(f"Overall Score: {analysis.overall_score:.1f}/100")
    
    if analysis.overall_score >= 80:
        print("🟢 Excellent resume!")
    elif analysis.overall_score >= 60:
        print("🟡 Good resume with room for improvement")
    else:
        print("🔴 Resume needs significant improvement")
    
    print(f"\n📈 Detailed Metrics:")
    print(f"  • Industry Alignment: {analysis.industry_alignment*100:.0f}%")
    print(f"  • ATS Compatibility: {analysis.ats_compatibility*100:.0f}%")
    print(f"  • Keyword Optimization: {analysis.keyword_optimization*100:.0f}%")
    
    if analysis.strengths:
        print(f"\n✅ Strengths ({len(analysis.strengths)}):")
        for strength in analysis.strengths:
            print(f"  • {strength}")
    
    if analysis.feedback:
        print(f"\n💡 Feedback ({len(analysis.feedback)}):")
        for feedback in analysis.feedback:
            severity_emoji = {
                "critical": "🔴",
                "important": "🟡", 
                "suggestion": "🟢",
                "positive": "✅"
            }.get(feedback.severity.value, "ℹ️")
            
            print(f"  {severity_emoji} {feedback.category}: {feedback.message}")
            print(f"     💡 {feedback.suggestion}")
    
    if analysis.recommendations:
        print(f"\n🎯 Top Recommendations:")
        for i, rec in enumerate(analysis.recommendations[:5], 1):
            print(f"  {i}. {rec}")
    
    print(f"\n📅 Analysis completed at: {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")


async def demo_conversation_flow():
    """Demonstrate resume analysis through conversation"""
    
    print("\n" + "=" * 50)
    print("💬 Conversation Flow Demo")
    print("=" * 50)
    
    # This would normally use real services, but for demo we'll show the flow
    print("User: 'Can you help me improve my resume?'")
    print()
    print("EdAgent: 'I'd be happy to analyze your resume and provide personalized feedback!'")
    print()
    print("Here's what I can help you with:")
    print("• Overall resume structure and formatting")
    print("• Content quality and impact")
    print("• Industry-specific optimization") 
    print("• ATS (Applicant Tracking System) compatibility")
    print("• Keyword optimization for your target role")
    print()
    print("To get started, you can:")
    print("1. Share specific sections of your resume for targeted feedback")
    print("2. Ask about resume best practices for your industry")
    print("3. Get advice on how to highlight your achievements")
    print()
    print("What specific aspect of your resume would you like to work on first?")


if __name__ == "__main__":
    print("Starting EdAgent Resume Analysis Demo...\n")
    
    # Run the demos
    asyncio.run(demo_resume_analysis())
    asyncio.run(demo_conversation_flow())
    
    print("\n✨ Demo completed! Resume analysis functionality is ready to use.")