"""
Validation Utilities for EdAgent Streamlit Application

This module provides comprehensive validation functions for forms,
user input, and data integrity checks with consistent error handling.
"""

import re
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union, Callable, Pattern
from dataclasses import dataclass
from enum import Enum
import email_validator

from ..core.logger import get_logger


class ValidationError(Exception):
    """Custom validation error with detailed information"""
    
    def __init__(self, message: str, field: Optional[str] = None, code: Optional[str] = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class ValidationType(Enum):
    """Types of validation rules"""
    REQUIRED = "required"
    EMAIL = "email"
    PASSWORD = "password"
    PHONE = "phone"
    URL = "url"
    NUMERIC = "numeric"
    DATE = "date"
    LENGTH = "length"
    PATTERN = "pattern"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """Validation rule configuration"""
    type: ValidationType
    message: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    validator: Optional[Callable[[Any], bool]] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}


class FormValidator:
    """
    Comprehensive form validation with built-in rules and custom validators
    """
    
    def __init__(self):
        self.logger = get_logger("form_validator")
        
        # Common regex patterns
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'),
            'url': re.compile(r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'),
            'alphanumeric': re.compile(r'^[a-zA-Z0-9]+$'),
            'alpha': re.compile(r'^[a-zA-Z]+$'),
            'numeric': re.compile(r'^[0-9]+$'),
            'password_strong': re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
        }
        
        # Default error messages
        self.default_messages = {
            ValidationType.REQUIRED: "This field is required",
            ValidationType.EMAIL: "Please enter a valid email address",
            ValidationType.PASSWORD: "Password does not meet requirements",
            ValidationType.PHONE: "Please enter a valid phone number",
            ValidationType.URL: "Please enter a valid URL",
            ValidationType.NUMERIC: "Please enter a valid number",
            ValidationType.DATE: "Please enter a valid date",
            ValidationType.LENGTH: "Input length is invalid",
            ValidationType.PATTERN: "Input format is invalid"
        }
    
    def validate_field(self, value: Any, rules: List[ValidationRule], field_name: str = "") -> List[ValidationError]:
        """Validate a single field against multiple rules"""
        errors = []
        
        for rule in rules:
            try:
                if not self._apply_rule(value, rule):
                    message = rule.message or self.default_messages.get(rule.type, "Validation failed")
                    errors.append(ValidationError(message, field_name, rule.type.value))
            except Exception as e:
                self.logger.error(f"Validation error for field {field_name}: {e}")
                errors.append(ValidationError(f"Validation error: {str(e)}", field_name, "validation_error"))
        
        return errors
    
    def validate_form(self, data: Dict[str, Any], rules: Dict[str, List[ValidationRule]]) -> Dict[str, List[ValidationError]]:
        """Validate entire form data against rules"""
        all_errors = {}
        
        for field_name, field_rules in rules.items():
            field_value = data.get(field_name)
            field_errors = self.validate_field(field_value, field_rules, field_name)
            
            if field_errors:
                all_errors[field_name] = field_errors
        
        return all_errors
    
    def _apply_rule(self, value: Any, rule: ValidationRule) -> bool:
        """Apply a single validation rule"""
        if rule.type == ValidationType.REQUIRED:
            return self._validate_required(value)
        
        # Skip validation for empty values unless required
        if not value and value != 0:
            return True
        
        if rule.type == ValidationType.EMAIL:
            return self._validate_email(value)
        elif rule.type == ValidationType.PASSWORD:
            return self._validate_password(value, rule.params)
        elif rule.type == ValidationType.PHONE:
            return self._validate_phone(value)
        elif rule.type == ValidationType.URL:
            return self._validate_url(value)
        elif rule.type == ValidationType.NUMERIC:
            return self._validate_numeric(value, rule.params)
        elif rule.type == ValidationType.DATE:
            return self._validate_date(value, rule.params)
        elif rule.type == ValidationType.LENGTH:
            return self._validate_length(value, rule.params)
        elif rule.type == ValidationType.PATTERN:
            return self._validate_pattern(value, rule.params)
        elif rule.type == ValidationType.CUSTOM:
            return self._validate_custom(value, rule.validator)
        
        return True
    
    def _validate_required(self, value: Any) -> bool:
        """Validate required field"""
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return bool(value)
    
    def _validate_email(self, value: str) -> bool:
        """Validate email address"""
        if not isinstance(value, str):
            return False
        
        try:
            # Use email-validator library for comprehensive validation
            email_validator.validate_email(value)
            return True
        except email_validator.EmailNotValidError:
            # Fallback to regex pattern
            return bool(self.patterns['email'].match(value))
    
    def _validate_password(self, value: str, params: Dict[str, Any]) -> bool:
        """Validate password strength"""
        if not isinstance(value, str):
            return False
        
        min_length = params.get('min_length', 8)
        max_length = params.get('max_length', 128)
        require_uppercase = params.get('require_uppercase', True)
        require_lowercase = params.get('require_lowercase', True)
        require_digit = params.get('require_digit', True)
        require_special = params.get('require_special', True)
        special_chars = params.get('special_chars', '!@#$%^&*()_+-=[]{}|;:,.<>?')
        
        # Length check
        if len(value) < min_length or len(value) > max_length:
            return False
        
        # Character type checks
        if require_uppercase and not any(c.isupper() for c in value):
            return False
        
        if require_lowercase and not any(c.islower() for c in value):
            return False
        
        if require_digit and not any(c.isdigit() for c in value):
            return False
        
        if require_special and not any(c in special_chars for c in value):
            return False
        
        return True
    
    def _validate_phone(self, value: str) -> bool:
        """Validate phone number"""
        if not isinstance(value, str):
            return False
        
        # Remove common formatting characters
        cleaned = re.sub(r'[-.\s()]+', '', value)
        
        # Check if it matches phone pattern
        return bool(self.patterns['phone'].match(value)) or len(cleaned) >= 10
    
    def _validate_url(self, value: str) -> bool:
        """Validate URL"""
        if not isinstance(value, str):
            return False
        
        return bool(self.patterns['url'].match(value))
    
    def _validate_numeric(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate numeric value"""
        try:
            num_value = float(value)
            
            min_value = params.get('min_value')
            max_value = params.get('max_value')
            integer_only = params.get('integer_only', False)
            
            if min_value is not None and num_value < min_value:
                return False
            
            if max_value is not None and num_value > max_value:
                return False
            
            if integer_only and not isinstance(value, int) and not str(value).isdigit():
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_date(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate date value"""
        if isinstance(value, (date, datetime)):
            date_value = value.date() if isinstance(value, datetime) else value
        elif isinstance(value, str):
            try:
                date_formats = params.get('formats', ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'])
                date_value = None
                
                for fmt in date_formats:
                    try:
                        date_value = datetime.strptime(value, fmt).date()
                        break
                    except ValueError:
                        continue
                
                if date_value is None:
                    return False
            except ValueError:
                return False
        else:
            return False
        
        # Check date range
        min_date = params.get('min_date')
        max_date = params.get('max_date')
        
        if min_date and date_value < min_date:
            return False
        
        if max_date and date_value > max_date:
            return False
        
        return True
    
    def _validate_length(self, value: Any, params: Dict[str, Any]) -> bool:
        """Validate length constraints"""
        if value is None:
            return False
        
        length = len(str(value)) if not isinstance(value, (list, dict)) else len(value)
        
        min_length = params.get('min_length')
        max_length = params.get('max_length')
        exact_length = params.get('exact_length')
        
        if exact_length is not None:
            return length == exact_length
        
        if min_length is not None and length < min_length:
            return False
        
        if max_length is not None and length > max_length:
            return False
        
        return True
    
    def _validate_pattern(self, value: str, params: Dict[str, Any]) -> bool:
        """Validate against regex pattern"""
        if not isinstance(value, str):
            return False
        
        pattern = params.get('pattern')
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        elif isinstance(pattern, Pattern):
            pass
        else:
            return False
        
        return bool(pattern.match(value))
    
    def _validate_custom(self, value: Any, validator: Callable[[Any], bool]) -> bool:
        """Apply custom validation function"""
        if not validator:
            return True
        
        try:
            return validator(value)
        except Exception as e:
            self.logger.error(f"Custom validator error: {e}")
            return False
    
    # Convenience methods for common validations
    
    def create_required_rule(self, message: Optional[str] = None) -> ValidationRule:
        """Create required field rule"""
        return ValidationRule(ValidationType.REQUIRED, message)
    
    def create_email_rule(self, message: Optional[str] = None) -> ValidationRule:
        """Create email validation rule"""
        return ValidationRule(ValidationType.EMAIL, message)
    
    def create_password_rule(
        self, 
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        message: Optional[str] = None
    ) -> ValidationRule:
        """Create password validation rule"""
        params = {
            'min_length': min_length,
            'require_uppercase': require_uppercase,
            'require_lowercase': require_lowercase,
            'require_digit': require_digit,
            'require_special': require_special
        }
        return ValidationRule(ValidationType.PASSWORD, message, params)
    
    def create_length_rule(
        self, 
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        exact_length: Optional[int] = None,
        message: Optional[str] = None
    ) -> ValidationRule:
        """Create length validation rule"""
        params = {}
        if min_length is not None:
            params['min_length'] = min_length
        if max_length is not None:
            params['max_length'] = max_length
        if exact_length is not None:
            params['exact_length'] = exact_length
        
        return ValidationRule(ValidationType.LENGTH, message, params)
    
    def create_numeric_rule(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        integer_only: bool = False,
        message: Optional[str] = None
    ) -> ValidationRule:
        """Create numeric validation rule"""
        params = {
            'min_value': min_value,
            'max_value': max_value,
            'integer_only': integer_only
        }
        return ValidationRule(ValidationType.NUMERIC, message, params)
    
    def create_pattern_rule(self, pattern: Union[str, Pattern], message: Optional[str] = None) -> ValidationRule:
        """Create pattern validation rule"""
        params = {'pattern': pattern}
        return ValidationRule(ValidationType.PATTERN, message, params)
    
    def create_custom_rule(self, validator: Callable[[Any], bool], message: Optional[str] = None) -> ValidationRule:
        """Create custom validation rule"""
        return ValidationRule(ValidationType.CUSTOM, message, validator=validator)
    
    # Utility methods
    
    def get_error_summary(self, errors: Dict[str, List[ValidationError]]) -> str:
        """Get human-readable error summary"""
        if not errors:
            return "No validation errors"
        
        error_messages = []
        for field, field_errors in errors.items():
            for error in field_errors:
                error_messages.append(f"{field}: {error.message}")
        
        return "; ".join(error_messages)
    
    def has_errors(self, errors: Dict[str, List[ValidationError]]) -> bool:
        """Check if there are any validation errors"""
        return bool(errors)
    
    def get_field_errors(self, errors: Dict[str, List[ValidationError]], field: str) -> List[str]:
        """Get error messages for specific field"""
        field_errors = errors.get(field, [])
        return [error.message for error in field_errors]


# Convenience functions for common validation scenarios

def validate_registration_form(data: Dict[str, Any]) -> Dict[str, List[ValidationError]]:
    """Validate user registration form"""
    validator = FormValidator()
    
    rules = {
        'name': [
            validator.create_required_rule("Name is required"),
            validator.create_length_rule(min_length=2, max_length=100, message="Name must be 2-100 characters")
        ],
        'email': [
            validator.create_required_rule("Email is required"),
            validator.create_email_rule("Please enter a valid email address")
        ],
        'password': [
            validator.create_required_rule("Password is required"),
            validator.create_password_rule(message="Password must be at least 8 characters with uppercase, lowercase, digit, and special character")
        ],
        'confirm_password': [
            validator.create_required_rule("Password confirmation is required"),
            validator.create_custom_rule(
                lambda x: x == data.get('password'),
                "Passwords do not match"
            )
        ]
    }
    
    return validator.validate_form(data, rules)


def validate_login_form(data: Dict[str, Any]) -> Dict[str, List[ValidationError]]:
    """Validate user login form"""
    validator = FormValidator()
    
    rules = {
        'email': [
            validator.create_required_rule("Email is required"),
            validator.create_email_rule("Please enter a valid email address")
        ],
        'password': [
            validator.create_required_rule("Password is required")
        ]
    }
    
    return validator.validate_form(data, rules)


def validate_profile_form(data: Dict[str, Any]) -> Dict[str, List[ValidationError]]:
    """Validate user profile form"""
    validator = FormValidator()
    
    rules = {
        'name': [
            validator.create_length_rule(min_length=2, max_length=100, message="Name must be 2-100 characters")
        ],
        'bio': [
            validator.create_length_rule(max_length=500, message="Bio must be less than 500 characters")
        ],
        'website': [
            ValidationRule(ValidationType.URL, "Please enter a valid URL")
        ] if data.get('website') else [],
        'phone': [
            ValidationRule(ValidationType.PHONE, "Please enter a valid phone number")
        ] if data.get('phone') else []
    }
    
    return validator.validate_form(data, rules)