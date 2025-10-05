"""
PII (Personally Identifiable Information) redaction and restoration.
"""
import re
import uuid
import logging
from typing import Tuple, Dict, List

logger = logging.getLogger(__name__)


class PIIRedactor:
    """
    Handles PII redaction and restoration with secure mapping.
    """
    
    # Iranian phone number pattern: +98 or 0 followed by 9 and 9 digits
    PHONE_PATTERN = re.compile(r'(?:\+?98|0)?9\d{9}')
    
    # Email pattern (RFC 5322 simplified)
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Iranian IBAN pattern: IR followed by 24 digits
    IBAN_PATTERN = re.compile(r'\bIR[0-9]{24}\b')
    
    # National ID (کد ملی) pattern: 10 digits
    NATIONAL_ID_PATTERN = re.compile(r'\b\d{10}\b')
    
    def __init__(self):
        """Initialize with empty mapping."""
        self.mapping: Dict[str, str] = {}
        self.reverse_mapping: Dict[str, str] = {}
    
    def _generate_placeholder(self, pii_type: str) -> str:
        """
        Generate a unique placeholder for redacted PII.
        
        Args:
            pii_type: Type of PII (phone, email, iban, national_id)
            
        Returns:
            Unique placeholder string
        """
        unique_id = str(uuid.uuid4())[:8]
        return f"[{pii_type.upper()}_{unique_id}]"
    
    def _redact_pattern(self, text: str, pattern: re.Pattern, pii_type: str) -> str:
        """
        Redact all matches of a pattern in text.
        
        Args:
            text: Text to redact
            pattern: Regex pattern to match
            pii_type: Type of PII
            
        Returns:
            Text with redacted PII
        """
        def replace_match(match):
            original = match.group(0)
            if original not in self.mapping:
                placeholder = self._generate_placeholder(pii_type)
                self.mapping[original] = placeholder
                self.reverse_mapping[placeholder] = original
            return self.mapping[original]
        
        return pattern.sub(replace_match, text)
    
    def redact(self, text: str, redact_national_id: bool = False) -> Tuple[str, Dict[str, List[str]]]:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact
            redact_national_id: Whether to redact national IDs (disabled by default 
                               to avoid false positives)
        
        Returns:
            Tuple of (redacted_text, pii_warnings_dict)
        """
        if not text:
            return text, {}
        
        # Reset mappings
        self.mapping = {}
        self.reverse_mapping = {}
        
        redacted_text = text
        pii_warnings = {}
        
        # Redact Iranian phone numbers
        phone_matches = self.PHONE_PATTERN.findall(text)
        if phone_matches:
            redacted_text = self._redact_pattern(redacted_text, self.PHONE_PATTERN, 'phone')
            pii_warnings['phone'] = [f"Found {len(phone_matches)} phone number(s)"]
            logger.info(f"Redacted {len(phone_matches)} phone numbers")
        
        # Redact emails
        email_matches = self.EMAIL_PATTERN.findall(text)
        if email_matches:
            redacted_text = self._redact_pattern(redacted_text, self.EMAIL_PATTERN, 'email')
            pii_warnings['email'] = [f"Found {len(email_matches)} email address(es)"]
            logger.info(f"Redacted {len(email_matches)} email addresses")
        
        # Redact IBANs
        iban_matches = self.IBAN_PATTERN.findall(text)
        if iban_matches:
            redacted_text = self._redact_pattern(redacted_text, self.IBAN_PATTERN, 'iban')
            pii_warnings['iban'] = [f"Found {len(iban_matches)} IBAN(s)"]
            logger.info(f"Redacted {len(iban_matches)} IBANs")
        
        # Optionally redact national IDs
        if redact_national_id:
            national_id_matches = self.NATIONAL_ID_PATTERN.findall(text)
            if national_id_matches:
                redacted_text = self._redact_pattern(
                    redacted_text, 
                    self.NATIONAL_ID_PATTERN, 
                    'national_id'
                )
                pii_warnings['national_id'] = [
                    f"Found {len(national_id_matches)} potential national ID(s)"
                ]
                logger.info(f"Redacted {len(national_id_matches)} national IDs")
        
        return redacted_text, pii_warnings
    
    def restore(self, text: str) -> str:
        """
        Restore PII in redacted text using the mapping.
        
        Args:
            text: Redacted text with placeholders
            
        Returns:
            Text with restored PII
        """
        if not text or not self.reverse_mapping:
            return text
        
        restored_text = text
        for placeholder, original in self.reverse_mapping.items():
            restored_text = restored_text.replace(placeholder, original)
        
        return restored_text
    
    def get_mapping(self) -> Dict[str, str]:
        """
        Get the current PII mapping.
        
        Returns:
            Dictionary mapping original PII to placeholders
        """
        return self.mapping.copy()
    
    def get_reverse_mapping(self) -> Dict[str, str]:
        """
        Get the reverse mapping (placeholders to original).
        
        Returns:
            Dictionary mapping placeholders to original PII
        """
        return self.reverse_mapping.copy()
    
    def clear_mapping(self):
        """Clear all mappings."""
        self.mapping.clear()
        self.reverse_mapping.clear()
    
    def has_pii(self, text: str) -> bool:
        """
        Check if text contains any PII.
        
        Args:
            text: Text to check
            
        Returns:
            True if PII found, False otherwise
        """
        if not text:
            return False
        
        patterns = [
            self.PHONE_PATTERN,
            self.EMAIL_PATTERN,
            self.IBAN_PATTERN,
        ]
        
        for pattern in patterns:
            if pattern.search(text):
                return True
        
        return False


def redact_pii(text: str, redact_national_id: bool = False) -> Tuple[str, Dict[str, List[str]], PIIRedactor]:
    """
    Helper function to redact PII from text.
    
    Args:
        text: Text to redact
        redact_national_id: Whether to redact national IDs
        
    Returns:
        Tuple of (redacted_text, pii_warnings, redactor_instance)
    """
    redactor = PIIRedactor()
    redacted_text, pii_warnings = redactor.redact(text, redact_national_id)
    return redacted_text, pii_warnings, redactor


def restore_pii(text: str, redactor: PIIRedactor) -> str:
    """
    Helper function to restore PII in text.
    
    Args:
        text: Redacted text
        redactor: PIIRedactor instance with mapping
        
    Returns:
        Text with restored PII
    """
    return redactor.restore(text)
