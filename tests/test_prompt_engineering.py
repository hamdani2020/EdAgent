"""
Unit tests for the prompt engineering system
"""

import pytest
from datetime import datetime

from edagent.services.prompt_engineering import (
    PromptTemplates, 
    PromptBuilder, 
    SkillAssessmentQuestionGenerator,
    build_conversation_prompt,
    build_skill_assessment_prompt,
    build_learning_path_prompt,
    get_assessment_questions
)
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum


class TestPromptTemplates:
    """Test cases for PromptTemplates"""
    
    def test_base_system_prompt_contains_key_elements(self):
        """Test that base system prompt contains essential elements"""
        templates = PromptTemplates()
        prompt = templates.BASE_SYSTEM_PROMPT
        
        assert "EdAgent" in prompt
        assert "career coach" in prompt
        assert "encouraging" in prompt
        assert "beginners" in prompt
        assert "free" in prompt
        assert "learning paths" in prompt
    
    def test_skill_assessment_questions_exist(self):
        """Test that skill assessment questions are defined"""
        templates = PromptTemplates()
        
        assert "programming" in templates.SKILL_ASSESSMENT_QUESTIONS
        assert "web_development" in templates.SKILL_ASSESSMENT_QUESTIONS
        assert "data_science" in templates.SKILL_ASSESSMENT_QUESTIONS
        assert "design" in templates.SKILL_ASSESSMENT_QUESTIONS
        
        # Each category should have multiple questions
        for category, questions in templates.SKILL_ASSESSMENT_QUESTIONS.items():
            assert len(questions) >= 3
            assert all(isinstance(q, str) and len(q) > 10 for q in questions)
    
    def test_learning_path_system_prompt_has_guidelines(self):
        """Test that learning path prompt has clear guidelines"""
        templates = PromptTemplates()
        prompt = templates.LEARNING_PATH_SYSTEM_PROMPT
        
        assert "learning path designer" in prompt
        assert "beginner-friendly" in prompt
        assert "free" in prompt
        assert "milestones" in prompt
        assert "practical" in prompt


class TestPromptBuilder:
    """Test cases for PromptBuilder"""
    
    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing"""
        return PromptBuilder()
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context for testing"""
        preferences = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week",
            budget_preference="free"
        )
        
        context = UserContext(
            user_id="test-user-123",
            career_goals=["become a software developer"],
            learning_preferences=preferences,
            conversation_history=["Hello", "I want to learn Python"]
        )
        
        context.add_skill("python", SkillLevelEnum.BEGINNER, 0.6)
        return context
    
    def test_build_conversation_prompt_basic(self, prompt_builder):
        """Test building basic conversation prompt without context"""
        context = UserContext(user_id="test-user")
        prompt = prompt_builder.build_conversation_prompt("Hello", context)
        
        assert "EdAgent" in prompt
        assert "Hello" in prompt
        assert "test-user" in prompt
        assert "User message:" in prompt
        assert "Response:" in prompt
    
    def test_build_conversation_prompt_with_context(self, prompt_builder, sample_user_context):
        """Test building conversation prompt with full user context"""
        prompt = prompt_builder.build_conversation_prompt("How do I learn Python?", sample_user_context)
        
        assert "EdAgent" in prompt
        assert "test-user-123" in prompt
        assert "become a software developer" in prompt
        assert "python (beginner)" in prompt
        assert "visual" in prompt
        assert "2-3 hours/week" in prompt
        assert "How do I learn Python?" in prompt
        assert "Recent conversation context" in prompt
    
    def test_build_skill_assessment_prompt(self, prompt_builder):
        """Test building skill assessment prompt"""
        responses = [
            "I know basic Python syntax",
            "I've built a simple calculator",
            "I struggle with object-oriented programming"
        ]
        
        prompt = prompt_builder.build_skill_assessment_prompt("Python Programming", responses)
        
        assert "Python Programming" in prompt
        assert "basic Python syntax" in prompt
        assert "simple calculator" in prompt
        assert "object-oriented programming" in prompt
        assert "JSON format" in prompt
        assert "skill_area" in prompt
        assert "overall_level" in prompt
        assert "confidence_score" in prompt
    
    def test_build_learning_path_prompt_basic(self, prompt_builder):
        """Test building learning path prompt without user context"""
        current_skills = {
            "python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6)
        }
        
        prompt = prompt_builder.build_learning_path_prompt("Learn web development", current_skills)
        
        assert "Learn web development" in prompt
        assert "python: beginner" in prompt
        assert "JSON format" in prompt
        assert "milestones" in prompt
        assert "resources" in prompt
    
    def test_build_learning_path_prompt_with_context(self, prompt_builder, sample_user_context):
        """Test building learning path prompt with user context"""
        current_skills = {
            "python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6)
        }
        
        prompt = prompt_builder.build_learning_path_prompt(
            "Become a full-stack developer", 
            current_skills, 
            sample_user_context
        )
        
        assert "Become a full-stack developer" in prompt
        assert "python: beginner" in prompt
        assert "Learning style: visual" in prompt
        assert "Time commitment: 2-3 hours/week" in prompt
        assert "Budget preference: free" in prompt
    
    def test_build_resume_review_prompt(self, prompt_builder):
        """Test building resume review prompt"""
        resume_text = "John Doe\nSoftware Developer\nPython, JavaScript, React"
        target_role = "Frontend Developer"
        
        prompt = prompt_builder.build_resume_review_prompt(resume_text, target_role)
        
        assert "John Doe" in prompt
        assert "Frontend Developer" in prompt
        assert "Overall Impression" in prompt
        assert "Strengths" in prompt
        assert "Areas for Improvement" in prompt
    
    def test_build_interview_prep_prompt(self, prompt_builder):
        """Test building interview preparation prompt"""
        prompt = prompt_builder.build_interview_prep_prompt(
            "Software Developer",
            "Recent bootcamp graduate with Python experience",
            "entry"
        )
        
        assert "Software Developer" in prompt
        assert "entry" in prompt
        assert "bootcamp graduate" in prompt
        assert "Common Questions" in prompt
        assert "Technical Questions" in prompt
        assert "Behavioral Question" in prompt
    
    def test_build_content_recommendation_prompt(self, prompt_builder, sample_user_context):
        """Test building content recommendation prompt"""
        prompt = prompt_builder.build_content_recommendation_prompt("JavaScript", sample_user_context)
        
        assert "JavaScript" in prompt
        assert "visual" in prompt
        assert "2-3 hours/week" in prompt
        assert "free" in prompt
    
    def test_format_skills_summary_empty(self, prompt_builder):
        """Test formatting empty skills summary"""
        summary = prompt_builder._format_skills_summary({})
        assert "complete beginner" in summary
    
    def test_format_skills_summary_with_skills(self, prompt_builder):
        """Test formatting skills summary with skills"""
        skills = {
            "python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6),
            "javascript": SkillLevel("javascript", SkillLevelEnum.INTERMEDIATE, 0.8)
        }
        
        summary = prompt_builder._format_skills_summary(skills)
        
        assert "python: beginner (confidence: 0.6)" in summary
        assert "javascript: intermediate (confidence: 0.8)" in summary
    
    def test_build_user_context_summary(self, prompt_builder, sample_user_context):
        """Test building user context summary"""
        summary = prompt_builder._build_user_context_summary(sample_user_context)
        
        assert "test-user-123" in summary
        assert "become a software developer" in summary
        assert "python (beginner)" in summary
        assert "visual" in summary
        assert "2-3 hours/week" in summary
        assert "free" in summary
    
    def test_build_conversation_context_empty(self, prompt_builder):
        """Test building conversation context with no history"""
        context = UserContext(user_id="test", conversation_history=[])
        conv_context = prompt_builder._build_conversation_context(context)
        
        assert "start of a new conversation" in conv_context
    
    def test_build_conversation_context_with_history(self, prompt_builder, sample_user_context):
        """Test building conversation context with history"""
        conv_context = prompt_builder._build_conversation_context(sample_user_context)
        
        assert "Recent conversation context" in conv_context
        assert "Hello" in conv_context
        assert "I want to learn Python" in conv_context
    
    def test_format_responses(self, prompt_builder):
        """Test formatting user responses"""
        responses = ["First response", "Second response", "Third response"]
        formatted = prompt_builder._format_responses(responses)
        
        assert "1. First response" in formatted
        assert "2. Second response" in formatted
        assert "3. Third response" in formatted


class TestSkillAssessmentQuestionGenerator:
    """Test cases for SkillAssessmentQuestionGenerator"""
    
    @pytest.fixture
    def question_generator(self):
        """Create SkillAssessmentQuestionGenerator instance for testing"""
        return SkillAssessmentQuestionGenerator()
    
    def test_get_assessment_questions_programming(self, question_generator):
        """Test getting programming assessment questions"""
        questions = question_generator.get_assessment_questions("programming", 3)
        
        assert len(questions) == 3
        assert all(isinstance(q, str) for q in questions)
        assert any("programming" in q.lower() for q in questions)
    
    def test_get_assessment_questions_web_development(self, question_generator):
        """Test getting web development assessment questions"""
        questions = question_generator.get_assessment_questions("web development", 4)
        
        assert len(questions) == 4
        assert all(isinstance(q, str) for q in questions)
        assert any("html" in q.lower() or "css" in q.lower() or "javascript" in q.lower() for q in questions)
    
    def test_get_assessment_questions_data_science(self, question_generator):
        """Test getting data science assessment questions"""
        questions = question_generator.get_assessment_questions("data science", 2)
        
        assert len(questions) == 2
        assert all(isinstance(q, str) for q in questions)
        assert any("data" in q.lower() for q in questions)
    
    def test_get_assessment_questions_unknown_area(self, question_generator):
        """Test getting questions for unknown skill area"""
        questions = question_generator.get_assessment_questions("unknown skill", 3)
        
        # Should fall back to programming questions
        assert len(questions) == 3
        assert all(isinstance(q, str) for q in questions)
    
    def test_get_assessment_questions_more_than_available(self, question_generator):
        """Test requesting more questions than available"""
        questions = question_generator.get_assessment_questions("programming", 100)
        
        # Should return all available questions
        assert len(questions) > 0
        assert len(questions) <= 10  # Reasonable upper bound
    
    def test_generate_followup_question_beginner(self, question_generator):
        """Test generating follow-up question for beginner response"""
        response = "I'm a complete beginner and just started learning"
        followup = question_generator.generate_followup_question("Python", response)
        
        assert isinstance(followup, str)
        assert len(followup) > 10
        assert "motivated" in followup.lower() or "start" in followup.lower()
    
    def test_generate_followup_question_project(self, question_generator):
        """Test generating follow-up question for project response"""
        response = "I built a web scraper project using Python"
        followup = question_generator.generate_followup_question("Python", response)
        
        assert isinstance(followup, str)
        assert "project" in followup.lower()
        assert "challenging" in followup.lower() or "overcome" in followup.lower()
    
    def test_generate_followup_question_difficulty(self, question_generator):
        """Test generating follow-up question for difficulty response"""
        response = "I find object-oriented programming very difficult"
        followup = question_generator.generate_followup_question("Python", response)
        
        assert isinstance(followup, str)
        assert "challenging" in followup.lower() or "aspects" in followup.lower()
    
    def test_generate_followup_question_general(self, question_generator):
        """Test generating follow-up question for general response"""
        response = "I have some experience with Python programming"
        followup = question_generator.generate_followup_question("Python", response)
        
        assert isinstance(followup, str)
        assert "example" in followup.lower() or "applied" in followup.lower()


class TestConvenienceFunctions:
    """Test cases for convenience functions"""
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context for testing"""
        preferences = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week",
            budget_preference="free"
        )
        
        context = UserContext(
            user_id="test-user-123",
            career_goals=["become a software developer"],
            learning_preferences=preferences
        )
        
        context.add_skill("python", SkillLevelEnum.BEGINNER, 0.6)
        return context
    
    def test_build_conversation_prompt_function(self, sample_user_context):
        """Test convenience function for building conversation prompt"""
        prompt = build_conversation_prompt("Hello", sample_user_context)
        
        assert isinstance(prompt, str)
        assert "EdAgent" in prompt
        assert "Hello" in prompt
        assert "test-user-123" in prompt
    
    def test_build_skill_assessment_prompt_function(self):
        """Test convenience function for building skill assessment prompt"""
        responses = ["I know Python basics", "I've built simple scripts"]
        prompt = build_skill_assessment_prompt("Python", responses)
        
        assert isinstance(prompt, str)
        assert "Python" in prompt
        assert "Python basics" in prompt
        assert "JSON format" in prompt
    
    def test_build_learning_path_prompt_function(self):
        """Test convenience function for building learning path prompt"""
        skills = {"python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6)}
        prompt = build_learning_path_prompt("Learn web development", skills)
        
        assert isinstance(prompt, str)
        assert "Learn web development" in prompt
        assert "python: beginner" in prompt
        assert "milestones" in prompt
    
    def test_get_assessment_questions_function(self):
        """Test convenience function for getting assessment questions"""
        questions = get_assessment_questions("programming", 3)
        
        assert isinstance(questions, list)
        assert len(questions) == 3
        assert all(isinstance(q, str) for q in questions)


class TestPromptQuality:
    """Test cases for prompt quality and consistency"""
    
    @pytest.fixture
    def prompt_builder(self):
        """Create PromptBuilder instance for testing"""
        return PromptBuilder()
    
    def test_prompts_are_not_empty(self, prompt_builder):
        """Test that all generated prompts are not empty"""
        context = UserContext(user_id="test")
        
        # Test conversation prompt
        conv_prompt = prompt_builder.build_conversation_prompt("Hello", context)
        assert len(conv_prompt.strip()) > 100
        
        # Test skill assessment prompt
        assessment_prompt = prompt_builder.build_skill_assessment_prompt("Python", ["I know basics"])
        assert len(assessment_prompt.strip()) > 100
        
        # Test learning path prompt
        skills = {"python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6)}
        path_prompt = prompt_builder.build_learning_path_prompt("Learn Python", skills)
        assert len(path_prompt.strip()) > 100
    
    def test_prompts_contain_required_elements(self, prompt_builder):
        """Test that prompts contain required structural elements"""
        context = UserContext(user_id="test")
        
        # Conversation prompt should have system context and user message
        conv_prompt = prompt_builder.build_conversation_prompt("Hello", context)
        assert "EdAgent" in conv_prompt
        assert "User message:" in conv_prompt
        
        # Assessment prompt should have JSON structure requirements
        assessment_prompt = prompt_builder.build_skill_assessment_prompt("Python", ["I know basics"])
        assert "JSON" in assessment_prompt
        assert "skill_area" in assessment_prompt
        assert "overall_level" in assessment_prompt
        
        # Learning path prompt should have milestone structure
        skills = {"python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6)}
        path_prompt = prompt_builder.build_learning_path_prompt("Learn Python", skills)
        assert "milestones" in path_prompt
        assert "resources" in path_prompt
    
    def test_prompts_are_consistent_across_calls(self, prompt_builder):
        """Test that prompts are consistent across multiple calls"""
        context = UserContext(user_id="test")
        
        # Multiple calls should produce identical prompts
        prompt1 = prompt_builder.build_conversation_prompt("Hello", context)
        prompt2 = prompt_builder.build_conversation_prompt("Hello", context)
        assert prompt1 == prompt2
        
        # Assessment prompts should be consistent
        responses = ["I know basics"]
        assessment1 = prompt_builder.build_skill_assessment_prompt("Python", responses)
        assessment2 = prompt_builder.build_skill_assessment_prompt("Python", responses)
        assert assessment1 == assessment2