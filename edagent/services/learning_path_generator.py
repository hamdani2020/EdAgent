"""
Enhanced learning path generation service for EdAgent
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from ..models.user_context import UserContext, SkillLevel, SkillLevelEnum
from ..models.learning import LearningPath, Milestone, DifficultyLevel
from .ai_service import GeminiAIService
from .prompt_engineering import PromptBuilder
from .response_processing import StructuredResponseHandler


logger = logging.getLogger(__name__)


class LearningPathValidator:
    """Validates learning path quality and completeness"""
    
    @staticmethod
    def validate_learning_path_quality(learning_path: LearningPath) -> Tuple[bool, List[str]]:
        """
        Validate learning path quality and return validation results
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check basic structure
        if not learning_path.title or len(learning_path.title.strip()) < 5:
            issues.append("Learning path title is too short or missing")
        
        if not learning_path.description or len(learning_path.description.strip()) < 20:
            issues.append("Learning path description is too short or missing")
        
        if not learning_path.goal or len(learning_path.goal.strip()) < 5:
            issues.append("Learning path goal is too short or missing")
        
        # Check milestones
        if not learning_path.milestones:
            issues.append("Learning path has no milestones")
        elif len(learning_path.milestones) < 2:
            issues.append("Learning path should have at least 2 milestones")
        elif len(learning_path.milestones) > 12:
            issues.append("Learning path has too many milestones (max 12 recommended)")
        
        # Validate milestone progression
        if learning_path.milestones:
            issues.extend(LearningPathValidator._validate_milestone_progression(learning_path.milestones))
        
        # Check time estimates
        if not learning_path.estimated_duration:
            issues.append("Learning path missing overall time estimate")
        elif learning_path.estimated_duration.days < 7:
            issues.append("Learning path duration seems too short (minimum 1 week recommended)")
        elif learning_path.estimated_duration.days > 365:
            issues.append("Learning path duration seems too long (maximum 1 year recommended)")
        
        # Check target skills
        if not learning_path.target_skills:
            issues.append("Learning path should specify target skills")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def _validate_milestone_progression(milestones: List[Milestone]) -> List[str]:
        """Validate that milestones progress logically"""
        issues = []
        
        # Check milestone ordering
        for i, milestone in enumerate(milestones):
            if milestone.order_index != i:
                issues.append(f"Milestone {i} has incorrect order_index: {milestone.order_index}")
        
        # Check difficulty progression (should not decrease significantly)
        difficulty_values = {"beginner": 1, "intermediate": 2, "advanced": 3}
        
        for i in range(1, len(milestones)):
            prev_difficulty = difficulty_values.get(milestones[i-1].difficulty_level.value, 1)
            curr_difficulty = difficulty_values.get(milestones[i].difficulty_level.value, 1)
            
            if curr_difficulty < prev_difficulty - 1:
                issues.append(f"Milestone {i} difficulty decreases too much from previous milestone")
        
        # Check prerequisite consistency
        all_skills = set()
        for i, milestone in enumerate(milestones):
            # Check if prerequisites are covered by previous milestones
            for prereq in milestone.prerequisites:
                if prereq not in all_skills and i > 0:
                    issues.append(f"Milestone {i} prerequisite '{prereq}' not covered by previous milestones")
            
            # Add current milestone skills to available skills
            all_skills.update(milestone.skills_to_learn)
        
        # Check milestone completeness
        for i, milestone in enumerate(milestones):
            milestone_issues = LearningPathValidator._validate_milestone_completeness(milestone, i)
            issues.extend(milestone_issues)
        
        return issues
    
    @staticmethod
    def _validate_milestone_completeness(milestone: Milestone, index: int) -> List[str]:
        """Validate individual milestone completeness"""
        issues = []
        
        # Check basic fields
        if not milestone.title or len(milestone.title.strip()) < 5:
            issues.append(f"Milestone {index} title is too short")
        
        if not milestone.description or len(milestone.description.strip()) < 20:
            issues.append(f"Milestone {index} description is too short")
        
        # Check skills and learning objectives
        if not milestone.skills_to_learn:
            issues.append(f"Milestone {index} has no defined skills to learn")
        
        # Check time estimates
        if not milestone.estimated_duration:
            issues.append(f"Milestone {index} missing time estimate")
        elif milestone.estimated_duration.days < 1:
            issues.append(f"Milestone {index} duration too short (minimum 1 day)")
        elif milestone.estimated_duration.days > 30:
            issues.append(f"Milestone {index} duration too long (maximum 30 days recommended)")
        
        # Check assessment criteria
        if not milestone.assessment_criteria:
            issues.append(f"Milestone {index} has no assessment criteria")
        
        # Check resources
        if not milestone.resources:
            issues.append(f"Milestone {index} has no learning resources")
        else:
            free_resources = [r for r in milestone.resources if r.get("is_free", False)]
            if not free_resources:
                issues.append(f"Milestone {index} has no free resources")
        
        return issues


class PrerequisiteAnalyzer:
    """Analyzes and manages learning path prerequisites"""
    
    @staticmethod
    def analyze_prerequisites(goal: str, current_skills: Dict[str, SkillLevel]) -> Dict[str, Any]:
        """
        Analyze what prerequisites are needed for a learning goal
        
        Returns:
            Dictionary with prerequisite analysis
        """
        goal_lower = goal.lower()
        
        # Define common prerequisite mappings
        prerequisite_map = {
            "web developer": {
                "essential": ["basic computer skills", "internet navigation"],
                "recommended": ["basic math", "logical thinking"],
                "technical": ["html basics", "css basics"]
            },
            "data scientist": {
                "essential": ["basic math", "statistics fundamentals"],
                "recommended": ["programming basics", "excel proficiency"],
                "technical": ["python basics", "sql basics"]
            },
            "software developer": {
                "essential": ["basic computer skills", "logical thinking"],
                "recommended": ["basic math", "problem solving"],
                "technical": ["programming fundamentals"]
            },
            "ui/ux designer": {
                "essential": ["basic computer skills", "visual design principles"],
                "recommended": ["user psychology", "basic research methods"],
                "technical": ["design software basics"]
            },
            "digital marketer": {
                "essential": ["basic computer skills", "internet navigation"],
                "recommended": ["writing skills", "basic analytics"],
                "technical": ["social media platforms", "basic seo"]
            }
        }
        
        # Find matching prerequisites
        prerequisites = {"essential": [], "recommended": [], "technical": [], "missing": []}
        
        for career, prereqs in prerequisite_map.items():
            if career in goal_lower or any(word in goal_lower for word in career.split()):
                prerequisites.update(prereqs)
                break
        
        # If no specific match, use general prerequisites
        if not any(prerequisites.values()):
            prerequisites = {
                "essential": ["basic computer skills", "internet navigation"],
                "recommended": ["logical thinking", "problem solving"],
                "technical": ["basic technical literacy"],
                "missing": []
            }
        
        # Check which prerequisites user already has
        user_skill_names = [skill.lower() for skill in current_skills.keys()]
        
        for category in ["essential", "recommended", "technical"]:
            missing_prereqs = []
            for prereq in prerequisites[category]:
                if not any(skill_word in prereq.lower() for skill_word in user_skill_names):
                    missing_prereqs.append(prereq)
            prerequisites["missing"].extend(missing_prereqs)
        
        return prerequisites
    
    @staticmethod
    def create_prerequisite_milestones(missing_prerequisites: List[str]) -> List[Milestone]:
        """Create milestones for missing prerequisites"""
        milestones = []
        
        if not missing_prerequisites:
            return milestones
        
        # Group prerequisites by category
        basic_skills = [p for p in missing_prerequisites if any(word in p.lower() 
                       for word in ["basic", "fundamental", "computer", "internet"])]
        
        technical_skills = [p for p in missing_prerequisites if any(word in p.lower() 
                           for word in ["programming", "coding", "software", "technical"])]
        
        domain_skills = [p for p in missing_prerequisites if p not in basic_skills + technical_skills]
        
        # Create milestone for basic skills
        if basic_skills:
            milestone = Milestone(
                title="Foundation Skills",
                description="Build essential foundation skills needed for your learning journey",
                skills_to_learn=basic_skills,
                estimated_duration=timedelta(days=7),
                difficulty_level=DifficultyLevel.BEGINNER,
                assessment_criteria=[
                    "Demonstrate comfortable use of computer and internet",
                    "Complete basic digital literacy assessment"
                ],
                order_index=0
            )
            
            milestone.add_resource(
                title="Computer Basics Course",
                url="https://www.youtube.com/results?search_query=computer+basics+tutorial",
                resource_type="video",
                is_free=True,
                duration=timedelta(hours=3)
            )
            
            milestones.append(milestone)
        
        # Create milestone for technical skills
        if technical_skills:
            milestone = Milestone(
                title="Technical Foundations",
                description="Learn basic technical concepts and skills",
                skills_to_learn=technical_skills,
                prerequisites=basic_skills,
                estimated_duration=timedelta(days=14),
                difficulty_level=DifficultyLevel.BEGINNER,
                assessment_criteria=[
                    "Understand basic technical terminology",
                    "Complete introductory technical exercises"
                ],
                order_index=len(milestones)
            )
            
            milestone.add_resource(
                title="Technical Literacy Course",
                url="https://www.youtube.com/results?search_query=technical+literacy+beginners",
                resource_type="video",
                is_free=True,
                duration=timedelta(hours=5)
            )
            
            milestones.append(milestone)
        
        # Create milestone for domain-specific skills
        if domain_skills:
            milestone = Milestone(
                title="Domain Knowledge",
                description="Learn domain-specific knowledge and concepts",
                skills_to_learn=domain_skills,
                prerequisites=basic_skills + technical_skills,
                estimated_duration=timedelta(days=10),
                difficulty_level=DifficultyLevel.BEGINNER,
                assessment_criteria=[
                    "Demonstrate understanding of domain concepts",
                    "Complete domain knowledge quiz"
                ],
                order_index=len(milestones)
            )
            
            milestone.add_resource(
                title="Domain Introduction",
                url="https://www.google.com/search?q=" + "+".join(domain_skills),
                resource_type="article",
                is_free=True,
                duration=timedelta(hours=4)
            )
            
            milestones.append(milestone)
        
        return milestones


class TimeEstimator:
    """Estimates time requirements for learning paths and milestones"""
    
    @staticmethod
    def estimate_milestone_duration(milestone: Milestone, user_context: Optional[UserContext] = None) -> timedelta:
        """
        Estimate realistic duration for a milestone based on content and user context
        """
        base_hours = 0
        
        # Base time for skills to learn (2-4 hours per skill)
        skills_count = len(milestone.skills_to_learn)
        base_hours += skills_count * 3  # Average 3 hours per skill
        
        # Add time for resources
        for resource in milestone.resources:
            if "duration" in resource and resource["duration"]:
                base_hours += resource["duration"] / 3600  # Convert seconds to hours
            else:
                # Default time estimates by resource type
                resource_type = resource.get("type", "article")
                type_hours = {
                    "video": 2,
                    "course": 8,
                    "article": 1,
                    "interactive": 4,
                    "book": 10,
                    "tutorial": 3
                }
                base_hours += type_hours.get(resource_type, 2)
        
        # Adjust based on difficulty level
        difficulty_multipliers = {
            DifficultyLevel.BEGINNER: 1.0,
            DifficultyLevel.INTERMEDIATE: 1.3,
            DifficultyLevel.ADVANCED: 1.6
        }
        
        multiplier = difficulty_multipliers.get(milestone.difficulty_level, 1.0)
        adjusted_hours = base_hours * multiplier
        
        # Adjust based on user context
        if user_context and user_context.learning_preferences:
            prefs = user_context.learning_preferences
            
            # Adjust for time commitment
            if "part-time" in prefs.time_commitment.lower():
                adjusted_hours *= 1.2  # Part-time learners need more calendar time
            elif "full-time" in prefs.time_commitment.lower():
                adjusted_hours *= 0.8  # Full-time learners can be more efficient
        
        # Convert to days (assuming 2-3 hours of study per day)
        study_hours_per_day = 2.5
        days = max(1, int(adjusted_hours / study_hours_per_day))
        
        return timedelta(days=days)
    
    @staticmethod
    def estimate_learning_path_duration(learning_path: LearningPath) -> timedelta:
        """Estimate total duration for a learning path"""
        total_days = 0
        
        for milestone in learning_path.milestones:
            if milestone.estimated_duration:
                total_days += milestone.estimated_duration.days
            else:
                # Use default estimate if not set
                estimated = TimeEstimator.estimate_milestone_duration(milestone)
                total_days += estimated.days
        
        # Add buffer time (10-20% depending on complexity)
        buffer_multiplier = 1.1 if len(learning_path.milestones) <= 5 else 1.15
        total_days = int(total_days * buffer_multiplier)
        
        return timedelta(days=total_days)


class DifficultyAssessor:
    """Assesses and manages difficulty levels for learning paths"""
    
    @staticmethod
    def assess_milestone_difficulty(milestone: Milestone, previous_milestones: List[Milestone]) -> DifficultyLevel:
        """
        Assess appropriate difficulty level for a milestone based on content and progression
        """
        # Start with current difficulty or beginner
        current_difficulty = milestone.difficulty_level or DifficultyLevel.BEGINNER
        
        # Analyze skills complexity
        complex_keywords = [
            "advanced", "expert", "professional", "enterprise", "architecture",
            "optimization", "performance", "scalability", "security", "deployment"
        ]
        
        intermediate_keywords = [
            "framework", "library", "api", "database", "testing", "debugging",
            "integration", "workflow", "automation", "responsive"
        ]
        
        # Check skills for complexity indicators
        all_skills_text = " ".join(milestone.skills_to_learn + [milestone.description]).lower()
        
        complex_count = sum(1 for keyword in complex_keywords if keyword in all_skills_text)
        intermediate_count = sum(1 for keyword in intermediate_keywords if keyword in all_skills_text)
        
        # Determine base difficulty
        if complex_count > 0:
            suggested_difficulty = DifficultyLevel.ADVANCED
        elif intermediate_count > 1:
            suggested_difficulty = DifficultyLevel.INTERMEDIATE
        else:
            suggested_difficulty = DifficultyLevel.BEGINNER
        
        # Ensure logical progression
        if previous_milestones:
            max_prev_difficulty = max(
                m.difficulty_level for m in previous_milestones
            )
            
            difficulty_values = {
                DifficultyLevel.BEGINNER: 1,
                DifficultyLevel.INTERMEDIATE: 2,
                DifficultyLevel.ADVANCED: 3
            }
            
            max_prev_value = difficulty_values[max_prev_difficulty]
            suggested_value = difficulty_values[suggested_difficulty]
            
            # Don't jump more than one level
            if suggested_value > max_prev_value + 1:
                for level, value in difficulty_values.items():
                    if value == max_prev_value + 1:
                        suggested_difficulty = level
                        break
        
        return suggested_difficulty
    
    @staticmethod
    def assess_learning_path_difficulty(learning_path: LearningPath) -> DifficultyLevel:
        """Assess overall difficulty level for a learning path"""
        if not learning_path.milestones:
            return DifficultyLevel.BEGINNER
        
        # Count difficulty levels
        difficulty_counts = {
            DifficultyLevel.BEGINNER: 0,
            DifficultyLevel.INTERMEDIATE: 0,
            DifficultyLevel.ADVANCED: 0
        }
        
        for milestone in learning_path.milestones:
            difficulty_counts[milestone.difficulty_level] += 1
        
        total_milestones = len(learning_path.milestones)
        
        # Determine overall difficulty based on distribution
        if difficulty_counts[DifficultyLevel.ADVANCED] > total_milestones * 0.3:
            return DifficultyLevel.ADVANCED
        elif difficulty_counts[DifficultyLevel.INTERMEDIATE] > total_milestones * 0.4:
            return DifficultyLevel.INTERMEDIATE
        else:
            return DifficultyLevel.BEGINNER


class EnhancedLearningPathGenerator:
    """Enhanced learning path generator with comprehensive workflow"""
    
    def __init__(self):
        self.ai_service = GeminiAIService()
        self.prompt_builder = PromptBuilder()
        self.response_handler = StructuredResponseHandler()
        self.validator = LearningPathValidator()
        self.prerequisite_analyzer = PrerequisiteAnalyzer()
        self.time_estimator = TimeEstimator()
        self.difficulty_assessor = DifficultyAssessor()
    
    async def create_comprehensive_learning_path(
        self, 
        goal: str, 
        current_skills: Dict[str, SkillLevel],
        user_context: Optional[UserContext] = None
    ) -> LearningPath:
        """
        Create a comprehensive learning path with enhanced workflow
        """
        try:
            logger.info(f"Creating comprehensive learning path for goal: {goal}")
            
            # Step 1: Analyze prerequisites
            prerequisite_analysis = self.prerequisite_analyzer.analyze_prerequisites(goal, current_skills)
            
            # Step 2: Generate base learning path using AI
            base_learning_path = await self.ai_service.create_learning_path(goal, current_skills)
            
            # Step 3: Add prerequisite milestones if needed
            if prerequisite_analysis["missing"]:
                prerequisite_milestones = self.prerequisite_analyzer.create_prerequisite_milestones(
                    prerequisite_analysis["missing"]
                )
                
                # Insert prerequisite milestones at the beginning
                for i, milestone in enumerate(prerequisite_milestones):
                    milestone.order_index = i
                
                # Adjust order indices for existing milestones
                for milestone in base_learning_path.milestones:
                    milestone.order_index += len(prerequisite_milestones)
                
                # Combine milestones
                base_learning_path.milestones = prerequisite_milestones + base_learning_path.milestones
            
            # Step 4: Enhance time estimates
            for milestone in base_learning_path.milestones:
                if not milestone.estimated_duration:
                    milestone.estimated_duration = self.time_estimator.estimate_milestone_duration(
                        milestone, user_context
                    )
            
            # Update overall duration
            base_learning_path.estimated_duration = self.time_estimator.estimate_learning_path_duration(
                base_learning_path
            )
            
            # Step 5: Assess and adjust difficulty levels
            for i, milestone in enumerate(base_learning_path.milestones):
                previous_milestones = base_learning_path.milestones[:i]
                milestone.difficulty_level = self.difficulty_assessor.assess_milestone_difficulty(
                    milestone, previous_milestones
                )
            
            # Update overall difficulty
            base_learning_path.difficulty_level = self.difficulty_assessor.assess_learning_path_difficulty(
                base_learning_path
            )
            
            # Step 6: Validate learning path quality
            is_valid, issues = self.validator.validate_learning_path_quality(base_learning_path)
            
            if not is_valid:
                logger.warning(f"Learning path validation issues: {issues}")
                # Try to fix common issues
                base_learning_path = self._fix_common_issues(base_learning_path, issues)
            
            # Step 7: Final validation
            is_valid, remaining_issues = self.validator.validate_learning_path_quality(base_learning_path)
            
            if remaining_issues:
                logger.warning(f"Remaining learning path issues: {remaining_issues}")
            
            logger.info(f"Successfully created learning path: {base_learning_path.title}")
            return base_learning_path
            
        except Exception as e:
            logger.error(f"Error creating comprehensive learning path: {e}")
            # Return fallback learning path
            return self.response_handler._create_fallback_learning_path(goal)
    
    def _fix_common_issues(self, learning_path: LearningPath, issues: List[str]) -> LearningPath:
        """Fix common issues in learning paths"""
        
        # Fix missing assessment criteria
        for milestone in learning_path.milestones:
            if not milestone.assessment_criteria:
                milestone.assessment_criteria = [
                    f"Complete all learning materials for {milestone.title}",
                    f"Demonstrate understanding of {', '.join(milestone.skills_to_learn[:2])}",
                    "Pass milestone assessment quiz"
                ]
        
        # Fix missing target skills
        if not learning_path.target_skills:
            all_skills = set()
            for milestone in learning_path.milestones:
                all_skills.update(milestone.skills_to_learn)
            learning_path.target_skills = list(all_skills)
        
        # Fix short descriptions
        if len(learning_path.description) < 20:
            learning_path.description = (
                f"A comprehensive learning path to help you achieve your goal of {learning_path.goal}. "
                f"This path includes {len(learning_path.milestones)} milestones designed to build your skills progressively."
            )
        
        # Fix milestone descriptions
        for milestone in learning_path.milestones:
            if len(milestone.description) < 20:
                milestone.description = (
                    f"In this milestone, you will learn {', '.join(milestone.skills_to_learn[:3])} "
                    f"and build practical skills through hands-on exercises and projects."
                )
        
        return learning_path