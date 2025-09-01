"""
Resume analysis service for EdAgent
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date

from ..models.resume import (
    Resume, ResumeAnalysis, ResumeFeedback, FeedbackSeverity, 
    IndustryType, ExperienceLevel, WorkExperience, Education
)
from ..models.user_context import UserContext
from ..interfaces.ai_interface import AIServiceInterface
from .ai_service import GeminiAIService


logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    """Service for analyzing resumes and providing feedback"""
    
    def __init__(self, ai_service: Optional[AIServiceInterface] = None):
        """Initialize the resume analyzer"""
        self.ai_service = ai_service or GeminiAIService()
        
        # Industry-specific keywords for analysis
        self.industry_keywords = {
            IndustryType.TECHNOLOGY: [
                "software", "programming", "development", "coding", "python", "javascript",
                "java", "react", "angular", "vue", "node.js", "api", "database", "sql",
                "cloud", "aws", "azure", "docker", "kubernetes", "agile", "scrum"
            ],
            IndustryType.HEALTHCARE: [
                "patient", "clinical", "medical", "healthcare", "nursing", "diagnosis",
                "treatment", "hipaa", "ehr", "emr", "pharmacy", "laboratory", "surgery"
            ],
            IndustryType.FINANCE: [
                "financial", "accounting", "investment", "banking", "portfolio", "risk",
                "compliance", "audit", "gaap", "sox", "trading", "analysis", "budget"
            ],
            IndustryType.MARKETING: [
                "marketing", "campaign", "brand", "social media", "seo", "sem", "content",
                "analytics", "conversion", "lead generation", "crm", "email marketing"
            ],
            IndustryType.EDUCATION: [
                "teaching", "curriculum", "student", "learning", "assessment", "classroom",
                "pedagogy", "educational", "training", "instruction", "academic"
            ]
        }
        
        # ATS-friendly formatting rules
        self.ats_rules = {
            "avoid_graphics": True,
            "use_standard_fonts": True,
            "avoid_tables": True,
            "use_bullet_points": True,
            "include_keywords": True,
            "standard_sections": True
        }
    
    async def analyze_resume(self, resume: Resume, user_context: Optional[UserContext] = None) -> ResumeAnalysis:
        """Perform comprehensive resume analysis"""
        try:
            logger.info(f"Starting resume analysis for user {resume.user_id}")
            
            # Initialize analysis object
            analysis = ResumeAnalysis(
                resume_id=resume.id,
                user_id=resume.user_id,
                overall_score=0.0  # Will be calculated later
            )
            
            # Perform different types of analysis
            await self._analyze_content_quality(resume, analysis)
            await self._analyze_structure_and_format(resume, analysis)
            await self._analyze_industry_alignment(resume, analysis)
            await self._analyze_ats_compatibility(resume, analysis)
            await self._analyze_keyword_optimization(resume, analysis)
            
            # Generate AI-powered feedback if available
            if user_context:
                await self._generate_ai_feedback(resume, analysis, user_context)
            
            # Calculate overall score
            analysis.overall_score = self._calculate_overall_score(analysis)
            
            # Generate final recommendations
            analysis.recommendations = self._generate_recommendations(resume, analysis)
            
            logger.info(f"Resume analysis completed with score: {analysis.overall_score:.1f}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {e}")
            # Return basic analysis with error feedback
            return self._create_fallback_analysis(resume, str(e))
    
    async def _analyze_content_quality(self, resume: Resume, analysis: ResumeAnalysis) -> None:
        """Analyze the quality of resume content"""
        
        # Check summary/objective
        if not resume.summary or len(resume.summary.strip()) < 50:
            analysis.add_feedback(
                "Summary",
                FeedbackSeverity.IMPORTANT,
                "Your resume lacks a compelling professional summary",
                "Add a 2-3 sentence summary highlighting your key qualifications and career goals"
            )
        elif len(resume.summary) > 300:
            analysis.add_feedback(
                "Summary",
                FeedbackSeverity.SUGGESTION,
                "Your professional summary is quite long",
                "Consider condensing your summary to 2-3 impactful sentences (150-200 words)"
            )
        else:
            analysis.strengths.append("Well-crafted professional summary")
        
        # Check work experience
        if not resume.work_experience:
            analysis.add_feedback(
                "Experience",
                FeedbackSeverity.CRITICAL,
                "No work experience listed",
                "Add your relevant work experience, including internships, part-time jobs, or volunteer work"
            )
        else:
            self._analyze_work_experience(resume, analysis)
        
        # Check education
        if not resume.education:
            analysis.add_feedback(
                "Education",
                FeedbackSeverity.IMPORTANT,
                "No education information provided",
                "Include your educational background, even if it's in progress"
            )
        else:
            self._analyze_education(resume, analysis)
        
        # Check skills section
        if not resume.skills:
            analysis.add_feedback(
                "Skills",
                FeedbackSeverity.IMPORTANT,
                "No skills listed",
                "Add a skills section highlighting your technical and soft skills"
            )
        elif len(resume.skills) < 5:
            analysis.add_feedback(
                "Skills",
                FeedbackSeverity.SUGGESTION,
                "Limited skills listed",
                "Consider adding more relevant skills to showcase your capabilities"
            )
        else:
            analysis.strengths.append("Comprehensive skills section")
        
        # Check contact information
        if not resume.email or not self._is_valid_email(resume.email):
            analysis.add_feedback(
                "Contact",
                FeedbackSeverity.CRITICAL,
                "Missing or invalid email address",
                "Ensure you have a professional email address listed"
            )
        
        if not resume.phone:
            analysis.add_feedback(
                "Contact",
                FeedbackSeverity.IMPORTANT,
                "No phone number provided",
                "Include a phone number where employers can reach you"
            )
    
    def _analyze_work_experience(self, resume: Resume, analysis: ResumeAnalysis) -> None:
        """Analyze work experience entries"""
        for i, exp in enumerate(resume.work_experience):
            exp_prefix = f"Experience {i+1}"
            
            # Check for achievements vs. responsibilities
            if not exp.achievements:
                analysis.add_feedback(
                    exp_prefix,
                    FeedbackSeverity.IMPORTANT,
                    f"No achievements listed for {exp.job_title} at {exp.company}",
                    "Add specific achievements and quantifiable results rather than just job duties"
                )
            
            # Check description length and quality
            if len(exp.description) < 100:
                analysis.add_feedback(
                    exp_prefix,
                    FeedbackSeverity.SUGGESTION,
                    f"Brief description for {exp.job_title} role",
                    "Expand the description to include key responsibilities and achievements"
                )
            
            # Check for quantifiable results
            if not self._has_quantifiable_results(exp.description + " ".join(exp.achievements)):
                analysis.add_feedback(
                    exp_prefix,
                    FeedbackSeverity.SUGGESTION,
                    f"No quantifiable results for {exp.job_title}",
                    "Include specific numbers, percentages, or metrics to demonstrate impact"
                )
            
            # Check employment gaps
            if i > 0:
                prev_exp = resume.work_experience[i-1]
                if prev_exp.end_date and exp.start_date:
                    gap_months = (exp.start_date.year - prev_exp.end_date.year) * 12 + \
                                (exp.start_date.month - prev_exp.end_date.month)
                    if gap_months > 6:
                        analysis.add_feedback(
                            "Experience Gap",
                            FeedbackSeverity.SUGGESTION,
                            f"Gap of {gap_months} months between positions",
                            "Consider explaining employment gaps or including relevant activities during that time"
                        )
    
    def _analyze_education(self, resume: Resume, analysis: ResumeAnalysis) -> None:
        """Analyze education entries"""
        for edu in resume.education:
            if edu.relevant_coursework:
                analysis.strengths.append("Includes relevant coursework")
            
            if edu.honors:
                analysis.strengths.append("Academic achievements highlighted")
            
            if edu.gpa and edu.gpa >= 3.5:
                analysis.strengths.append("Strong academic performance")
    
    async def _analyze_structure_and_format(self, resume: Resume, analysis: ResumeAnalysis) -> None:
        """Analyze resume structure and formatting"""
        
        # Check for standard sections
        required_sections = ["contact", "summary", "experience", "education", "skills"]
        missing_sections = []
        
        if not resume.email and not resume.phone:
            missing_sections.append("contact information")
        if not resume.summary:
            missing_sections.append("professional summary")
        if not resume.work_experience:
            missing_sections.append("work experience")
        if not resume.education:
            missing_sections.append("education")
        if not resume.skills:
            missing_sections.append("skills")
        
        if missing_sections:
            analysis.add_feedback(
                "Structure",
                FeedbackSeverity.IMPORTANT,
                f"Missing standard sections: {', '.join(missing_sections)}",
                "Include all standard resume sections for completeness"
            )
        else:
            analysis.strengths.append("Complete resume structure")
        
        # Check resume length based on experience
        experience_level = resume.get_experience_level()
        total_content_length = len(resume.summary) + sum(len(exp.description) for exp in resume.work_experience)
        
        if experience_level in [ExperienceLevel.ENTRY_LEVEL, ExperienceLevel.JUNIOR] and total_content_length > 2000:
            analysis.add_feedback(
                "Length",
                FeedbackSeverity.SUGGESTION,
                "Resume may be too long for your experience level",
                "Consider keeping your resume to 1 page for entry to junior level positions"
            )
        elif experience_level == ExperienceLevel.EXECUTIVE and total_content_length < 1500:
            analysis.add_feedback(
                "Length",
                FeedbackSeverity.SUGGESTION,
                "Resume may be too brief for executive level",
                "Executive resumes can be 2+ pages to showcase extensive experience"
            )
    
    async def _analyze_industry_alignment(self, resume: Resume, analysis: ResumeAnalysis) -> None:
        """Analyze alignment with target industry"""
        if not resume.target_industry:
            analysis.add_feedback(
                "Industry Focus",
                FeedbackSeverity.SUGGESTION,
                "No target industry specified",
                "Consider tailoring your resume for specific industries"
            )
            analysis.industry_alignment = 0.5
            return
        
        # Get industry keywords
        target_keywords = self.industry_keywords.get(resume.target_industry, [])
        if not target_keywords:
            analysis.industry_alignment = 0.5
            return
        
        # Analyze keyword presence
        resume_text = self._get_resume_text(resume).lower()
        matching_keywords = [kw for kw in target_keywords if kw.lower() in resume_text]
        
        alignment_score = len(matching_keywords) / len(target_keywords)
        analysis.industry_alignment = min(alignment_score, 1.0)
        
        if alignment_score < 0.3:
            analysis.add_feedback(
                "Industry Alignment",
                FeedbackSeverity.IMPORTANT,
                f"Limited alignment with {resume.target_industry.value} industry",
                f"Include more industry-specific keywords and experience relevant to {resume.target_industry.value}"
            )
        elif alignment_score > 0.7:
            analysis.strengths.append(f"Strong alignment with {resume.target_industry.value} industry")
    
    async def _analyze_ats_compatibility(self, resume: Resume, analysis: ResumeAnalysis) -> None:
        """Analyze ATS (Applicant Tracking System) compatibility"""
        ats_score = 1.0
        
        # Check for standard section headers (simulated)
        standard_headers = ["experience", "education", "skills", "summary"]
        # In a real implementation, this would analyze the actual resume format
        
        # Check for keyword optimization
        if not resume.skills:
            ats_score -= 0.2
            analysis.add_feedback(
                "ATS Compatibility",
                FeedbackSeverity.IMPORTANT,
                "Missing skills section reduces ATS compatibility",
                "Add a dedicated skills section with relevant keywords"
            )
        
        # Check for consistent formatting (simulated)
        if len(resume.work_experience) > 0:
            # Check if all experiences have descriptions
            missing_descriptions = [exp for exp in resume.work_experience if not exp.description]
            if missing_descriptions:
                ats_score -= 0.1
                analysis.add_feedback(
                    "ATS Compatibility",
                    FeedbackSeverity.SUGGESTION,
                    "Some work experiences lack descriptions",
                    "Ensure all positions have detailed descriptions for better ATS parsing"
                )
        
        analysis.ats_compatibility = max(ats_score, 0.0)
        
        if analysis.ats_compatibility > 0.8:
            analysis.strengths.append("Good ATS compatibility")
    
    async def _analyze_keyword_optimization(self, resume: Resume, analysis: ResumeAnalysis) -> None:
        """Analyze keyword optimization"""
        resume_text = self._get_resume_text(resume).lower()
        
        # Common action verbs for resumes
        action_verbs = [
            "achieved", "managed", "led", "developed", "created", "implemented",
            "improved", "increased", "reduced", "optimized", "designed", "built"
        ]
        
        action_verb_count = sum(1 for verb in action_verbs if verb in resume_text)
        action_verb_score = min(action_verb_count / 10, 1.0)  # Normalize to 0-1
        
        # Industry-specific keywords
        industry_score = analysis.industry_alignment
        
        # Overall keyword optimization
        analysis.keyword_optimization = (action_verb_score + industry_score) / 2
        
        if action_verb_count < 5:
            analysis.add_feedback(
                "Keywords",
                FeedbackSeverity.SUGGESTION,
                "Limited use of strong action verbs",
                "Use more action verbs like 'achieved', 'managed', 'developed' to describe your accomplishments"
            )
        else:
            analysis.strengths.append("Good use of action verbs")
    
    async def _generate_ai_feedback(self, resume: Resume, analysis: ResumeAnalysis, 
                                  user_context: UserContext) -> None:
        """Generate AI-powered feedback using Gemini"""
        try:
            # Create a prompt for resume analysis
            prompt = self._build_ai_analysis_prompt(resume, user_context)
            
            # Get AI response
            ai_response = await self.ai_service.generate_response(prompt, user_context)
            
            # Parse AI feedback and add to analysis
            ai_feedback = self._parse_ai_feedback(ai_response)
            
            for feedback_item in ai_feedback:
                analysis.add_feedback(
                    "AI Analysis",
                    FeedbackSeverity.SUGGESTION,
                    feedback_item["message"],
                    feedback_item["suggestion"],
                    industry_specific=True
                )
            
        except Exception as e:
            logger.warning(f"Could not generate AI feedback: {e}")
            # Continue without AI feedback
    
    def _build_ai_analysis_prompt(self, resume: Resume, user_context: UserContext) -> str:
        """Build prompt for AI-powered resume analysis"""
        resume_summary = f"""
        Resume Analysis Request:
        
        Candidate: {resume.name}
        Target Role: {resume.target_role or 'Not specified'}
        Target Industry: {resume.target_industry.value if resume.target_industry else 'Not specified'}
        Experience Level: {resume.get_experience_level().value}
        
        Professional Summary: {resume.summary}
        
        Work Experience ({len(resume.work_experience)} positions):
        {self._format_experience_for_ai(resume.work_experience)}
        
        Education: {len(resume.education)} entries
        Skills: {', '.join(resume.skills[:10])}{'...' if len(resume.skills) > 10 else ''}
        
        Please provide 3-5 specific, actionable pieces of feedback for improving this resume, 
        focusing on industry alignment, content quality, and competitive positioning.
        Format each as: "Issue: [description] | Suggestion: [specific action]"
        """
        
        return resume_summary
    
    def _format_experience_for_ai(self, experiences: List[WorkExperience]) -> str:
        """Format work experience for AI analysis"""
        formatted = []
        for exp in experiences[:3]:  # Limit to first 3 for prompt length
            duration = f"{exp.start_date.year}-{exp.end_date.year if exp.end_date else 'Present'}"
            formatted.append(f"- {exp.job_title} at {exp.company} ({duration})")
        
        if len(experiences) > 3:
            formatted.append(f"... and {len(experiences) - 3} more positions")
        
        return "\n".join(formatted)
    
    def _parse_ai_feedback(self, ai_response: str) -> List[Dict[str, str]]:
        """Parse AI feedback response into structured format"""
        feedback_items = []
        
        # Look for feedback patterns in the AI response
        lines = ai_response.split('\n')
        for line in lines:
            if '|' in line and ('Issue:' in line or 'Problem:' in line):
                parts = line.split('|')
                if len(parts) >= 2:
                    issue_part = parts[0].strip()
                    suggestion_part = parts[1].strip()
                    
                    # Extract the actual message and suggestion
                    message = issue_part.replace('Issue:', '').replace('Problem:', '').strip()
                    suggestion = suggestion_part.replace('Suggestion:', '').strip()
                    
                    if message and suggestion:
                        feedback_items.append({
                            "message": message,
                            "suggestion": suggestion
                        })
        
        return feedback_items
    
    def _calculate_overall_score(self, analysis: ResumeAnalysis) -> float:
        """Calculate overall resume score"""
        # Base score starts at 100
        score = 100.0
        
        # Deduct points for critical issues
        critical_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.CRITICAL)
        score -= len(critical_feedback) * 20
        
        # Deduct points for important issues
        important_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.IMPORTANT)
        score -= len(important_feedback) * 10
        
        # Deduct points for suggestions
        suggestion_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.SUGGESTION)
        score -= len(suggestion_feedback) * 5
        
        # Add points for strengths
        score += len(analysis.strengths) * 3
        
        # Factor in specific metrics
        score += analysis.industry_alignment * 10
        score += analysis.ats_compatibility * 10
        score += analysis.keyword_optimization * 10
        
        return max(min(score, 100.0), 0.0)
    
    def _generate_recommendations(self, resume: Resume, analysis: ResumeAnalysis) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Prioritize critical issues
        critical_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.CRITICAL)
        for feedback in critical_feedback:
            recommendations.append(f"🔴 {feedback.suggestion}")
        
        # Add important improvements
        important_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.IMPORTANT)
        for feedback in important_feedback[:3]:  # Limit to top 3
            recommendations.append(f"🟡 {feedback.suggestion}")
        
        # Add top suggestions
        suggestion_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.SUGGESTION)
        for feedback in suggestion_feedback[:2]:  # Limit to top 2
            recommendations.append(f"🟢 {feedback.suggestion}")
        
        # Add industry-specific recommendations
        if analysis.industry_alignment < 0.5 and resume.target_industry:
            recommendations.append(
                f"🎯 Research and include more {resume.target_industry.value}-specific keywords and skills"
            )
        
        return recommendations
    
    def _create_fallback_analysis(self, resume: Resume, error_message: str) -> ResumeAnalysis:
        """Create a basic analysis when full analysis fails"""
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            user_id=resume.user_id,
            overall_score=50.0
        )
        
        analysis.add_feedback(
            "Analysis Error",
            FeedbackSeverity.IMPORTANT,
            f"Could not complete full analysis: {error_message}",
            "Please try again or contact support if the issue persists"
        )
        
        # Add basic recommendations
        if not resume.summary:
            analysis.recommendations.append("Add a professional summary")
        if not resume.work_experience:
            analysis.recommendations.append("Include work experience")
        if not resume.skills:
            analysis.recommendations.append("Add a skills section")
        
        return analysis
    
    def _get_resume_text(self, resume: Resume) -> str:
        """Extract all text content from resume for analysis"""
        text_parts = [
            resume.name,
            resume.summary,
            " ".join(resume.skills),
            " ".join(resume.certifications)
        ]
        
        # Add work experience text
        for exp in resume.work_experience:
            text_parts.extend([
                exp.job_title,
                exp.company,
                exp.description,
                " ".join(exp.achievements),
                " ".join(exp.skills_used)
            ])
        
        # Add education text
        for edu in resume.education:
            text_parts.extend([
                edu.degree,
                edu.institution,
                " ".join(edu.relevant_coursework)
            ])
        
        return " ".join(filter(None, text_parts))
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _has_quantifiable_results(self, text: str) -> bool:
        """Check if text contains quantifiable results"""
        # Look for numbers, percentages, dollar amounts
        patterns = [
            r'\d+%',  # Percentages
            r'\$\d+',  # Dollar amounts
            r'\d+\+',  # Numbers with plus
            r'\d+k',   # Thousands (e.g., 50k)
            r'\d+m',   # Millions
            r'\d+ (users|customers|clients|projects|teams|people)',  # Quantities
            r'(increased|decreased|improved|reduced|grew|saved) by \d+',  # Improvements
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in patterns)