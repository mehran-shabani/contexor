"""
Unit tests for PII redaction.
"""
import pytest
from ai.pii import PIIRedactor, redact_pii, restore_pii


class TestPIIRedactor:
    """Test PII redaction and restoration."""
    
    def test_redact_phone_numbers(self):
        """Test Iranian phone number redaction."""
        redactor = PIIRedactor()
        
        # Test various phone formats
        texts = [
            "تماس با 09123456789 بگیرید",
            "شماره من +989123456789 است",
            "کال کنید به 9123456789",
            "تلفن: 09123456789 و 09876543210"
        ]
        
        for text in texts:
            redacted, warnings = redactor.redact(text)
            
            # Check that phone numbers are redacted
            assert '0912345678' not in redacted
            assert '+989123456789' not in redacted
            assert '9123456789' not in redacted
            
            # Check warnings
            assert 'phone' in warnings
            
            # Check placeholders exist
            assert '[PHONE_' in redacted
    
    def test_redact_emails(self):
        """Test email address redaction."""
        redactor = PIIRedactor()
        
        text = "ایمیل من test@example.com و info@company.ir است"
        redacted, warnings = redactor.redact(text)
        
        # Check that emails are redacted
        assert 'test@example.com' not in redacted
        assert 'info@company.ir' not in redacted
        
        # Check warnings
        assert 'email' in warnings
        
        # Check placeholders
        assert '[EMAIL_' in redacted
    
    def test_redact_iban(self):
        """Test Iranian IBAN redaction."""
        redactor = PIIRedactor()
        
        text = "شماره حساب من IR123456789012345678901234 است"
        redacted, warnings = redactor.redact(text)
        
        # Check that IBAN is redacted
        assert 'IR123456789012345678901234' not in redacted
        
        # Check warnings
        assert 'iban' in warnings
        
        # Check placeholder
        assert '[IBAN_' in redacted
    
    def test_redact_national_id(self):
        """Test national ID redaction."""
        redactor = PIIRedactor()
        
        text = "کد ملی من 1234567890 است"
        redacted, warnings = redactor.redact(text, redact_national_id=True)
        
        # Check that national ID is redacted
        assert '1234567890' not in redacted
        
        # Check warnings
        assert 'national_id' in warnings
        
        # Check placeholder
        assert '[NATIONAL_ID_' in redacted
    
    def test_restore_pii(self):
        """Test PII restoration."""
        redactor = PIIRedactor()
        
        original = "تماس با 09123456789 یا test@example.com"
        redacted, _ = redactor.redact(original)
        restored = redactor.restore(redacted)
        
        # Restored should match original
        assert '09123456789' in restored
        assert 'test@example.com' in restored
    
    def test_mask_unmask_consistency(self):
        """Test that mask/unmask are consistent."""
        redactor = PIIRedactor()
        
        original = "شماره 09123456789 و ایمیل test@example.com و IBAN IR123456789012345678901234"
        redacted, warnings = redactor.redact(original)
        restored = redactor.restore(redacted)
        
        # All PII should be present in restored
        assert '09123456789' in restored
        assert 'test@example.com' in restored
        assert 'IR123456789012345678901234' in restored
    
    def test_multiple_same_pii(self):
        """Test handling of multiple instances of same PII."""
        redactor = PIIRedactor()
        
        text = "شماره 09123456789 و دوباره 09123456789"
        redacted, warnings = redactor.redact(text)
        
        # Same placeholder should be used for same PII
        placeholders = [p for p in redacted.split() if p.startswith('[PHONE_')]
        assert len(placeholders) == 2
        assert placeholders[0] == placeholders[1]
        
        # Restore should work correctly
        restored = redactor.restore(redacted)
        assert restored.count('09123456789') == 2
    
    def test_has_pii(self):
        """Test PII detection."""
        redactor = PIIRedactor()
        
        # Text with PII
        assert redactor.has_pii("شماره 09123456789")
        assert redactor.has_pii("ایمیل test@example.com")
        assert redactor.has_pii("IBAN IR123456789012345678901234")
        
        # Text without PII
        assert not redactor.has_pii("سلام این یک متن ساده است")
        assert not redactor.has_pii("")
    
    def test_empty_text(self):
        """Test handling of empty text."""
        redactor = PIIRedactor()
        
        redacted, warnings = redactor.redact("")
        assert redacted == ""
        assert warnings == {}
        
        redacted, warnings = redactor.redact(None)
        assert redacted is None
        assert warnings == {}
    
    def test_helper_functions(self):
        """Test helper functions."""
        text = "شماره 09123456789"
        
        redacted_text, warnings, redactor = redact_pii(text)
        
        assert '09123456789' not in redacted_text
        assert 'phone' in warnings
        
        restored = restore_pii(redacted_text, redactor)
        assert '09123456789' in restored


@pytest.mark.django_db
class TestPIIIntegration:
    """Integration tests for PII with content generation."""
    
    def test_pii_warning_in_content(self):
        """Test that PII warnings are stored in content."""
        from contentmgmt.models import Content, Project
        from accounts.models import Workspace, Organization, User
        
        # Create test data
        org = Organization.objects.create(name="Test Org", slug="test-org")
        workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
            organization=org
        )
        user = User.objects.create_user(phone_number="09121111111")
        project = Project.objects.create(
            name="Test Project",
            slug="test-project",
            workspace=workspace,
            created_by=user
        )
        
        # Create content with PII in metadata
        content = Content.objects.create(
            title="Test Content with PII",
            project=project,
            created_by=user,
            prompt_variables={
                'topic': 'تماس با 09123456789',
                'keywords': 'test@example.com'
            }
        )
        
        # PII detection would happen in the task
        from ai.pii import PIIRedactor
        redactor = PIIRedactor()
        
        text = content.prompt_variables['topic'] + ' ' + content.prompt_variables['keywords']
        _, warnings = redactor.redact(text)
        
        if warnings:
            content.has_pii = True
            content.pii_warnings = warnings
            content.save()
        
        content.refresh_from_db()
        assert content.has_pii is True
        assert 'phone' in content.pii_warnings or 'email' in content.pii_warnings
