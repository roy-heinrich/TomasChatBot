"""
Structured Response Framework for Complex Procedural Queries
==========================================================

This module provides a framework for generating structured, organized responses
to complex procedural queries. It handles multi-step processes, requirements,
and administrative procedures with clear formatting and organization.

Key Features:
- Step-by-step procedural responses
- Multi-section informational responses
- Requirements and checklist formatting
- Timeline and deadline organization
- Contact and location information
"""

from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime, timedelta

class ResponseType(Enum):
    """Types of structured responses."""
    PROCEDURAL = "procedural"           # Step-by-step processes
    INFORMATIONAL = "informational"     # Multi-section information
    REQUIREMENTS = "requirements"       # Lists of requirements/documents
    TIMELINE = "timeline"              # Time-based procedures
    CONTACT_INFO = "contact_info"      # Contact and location information
    FAQ = "faq"                       # Frequently asked questions
    COMPARISON = "comparison"          # Comparing options/programs

@dataclass
class ResponseSection:
    """A section within a structured response."""
    title: str
    content: str
    section_type: str = "default"
    order: int = 0
    
class ResponseStep:
    """A step in a procedural response."""
    def __init__(self, step_number: int, title: str, description: str, 
                 requirements: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 estimated_time: Optional[str] = None):
        self.step_number = step_number
        self.title = title
        self.description = description
        self.requirements = requirements or []
        self.notes = notes
        self.estimated_time = estimated_time

class RequirementItem:
    """An item in a requirements list."""
    def __init__(self, item: str, required: bool = True, 
                 description: Optional[str] = None,
                 alternative: Optional[str] = None):
        self.item = item
        self.required = required
        self.description = description
        self.alternative = alternative

class ContactInfo:
    """Contact information structure."""
    def __init__(self, name: str, phone: Optional[str] = None, 
                 email: Optional[str] = None, office: Optional[str] = None,
                 hours: Optional[str] = None):
        self.name = name
        self.phone = phone
        self.email = email
        self.office = office
        self.hours = hours

class StructuredResponse:
    """Base class for structured responses."""
    
    def __init__(self, response_type: ResponseType, title: str, 
                 language: str = "english"):
        self.response_type = response_type
        self.title = title
        self.language = language
        self.sections: List[ResponseSection] = []
        self.steps: List[ResponseStep] = []
        self.requirements: List[RequirementItem] = []
        self.contacts: List[ContactInfo] = []
        self.notes: List[str] = []
        self.metadata: Dict = {}
        
    def add_section(self, title: str, content: str, section_type: str = "default", order: int = 0):
        """Add a section to the response."""
        section = ResponseSection(title, content, section_type, order)
        self.sections.append(section)
        
    def add_step(self, step_number: int, title: str, description: str, 
                 requirements: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 estimated_time: Optional[str] = None):
        """Add a step to procedural response."""
        step = ResponseStep(step_number, title, description, requirements, notes, estimated_time)
        self.steps.append(step)
        
    def add_requirement(self, item: str, required: bool = True, 
                       description: Optional[str] = None,
                       alternative: Optional[str] = None):
        """Add a requirement item."""
        req = RequirementItem(item, required, description, alternative)
        self.requirements.append(req)
        
    def add_contact(self, name: str, phone: Optional[str] = None, 
                   email: Optional[str] = None, office: Optional[str] = None,
                   hours: Optional[str] = None):
        """Add contact information."""
        contact = ContactInfo(name, phone, email, office, hours)
        self.contacts.append(contact)
        
    def add_note(self, note: str):
        """Add a note or important information."""
        self.notes.append(note)
        
    def format_response(self) -> str:
        """Format the structured response into readable text."""
        if self.language.lower() in ['tagalog', 'filipino']:
            return self._format_tagalog()
        elif self.language.lower() in ['hiligaynon', 'ilonggo']:
            return self._format_hiligaynon()
        else:
            return self._format_english()
    
    def _format_english(self) -> str:
        """Format response in English with engaging structure."""
        lines = []
        
        # Add engaging header
        lines.append(f"📋 {self.title}")
        lines.append("=" * len(f"📋 {self.title}"))
        lines.append("")
        
        # Add main information from sections with engaging formatting
        sorted_sections = sorted(self.sections, key=lambda x: x.order)
        for section in sorted_sections:
            lines.append(f"## {section.title}")
            lines.append(section.content)
            lines.append("")
        
        # Add contact information with engaging format
        if self.contacts:
            lines.append("## 📞 Contact Information")
            for contact in self.contacts:
                lines.append(f"**{contact.name}**")
                if contact.office:
                    lines.append(f"  📍 Office: {contact.office}")
                if contact.phone:
                    lines.append(f"  📞 Phone: {contact.phone}")
                if contact.email:
                    lines.append(f"  📧 Email: {contact.email}")
                if contact.hours:
                    lines.append(f"  🕐 Hours: {contact.hours}")
                lines.append("")
        
        # Add steps with engaging format
        if self.steps:
            lines.append("## 📋 Step-by-Step Process")
            for step in sorted(self.steps, key=lambda x: x.step_number):
                lines.append(f"### Step {step.step_number}: {step.title}")
                lines.append(step.description)
                
                if step.requirements:
                    lines.append("**Required documents:**")
                    for req in step.requirements:
                        lines.append(f"  • {req}")
                
                if step.estimated_time:
                    lines.append(f"**Estimated time:** {step.estimated_time}")
                
                if step.notes:
                    lines.append(f"**Note:** {step.notes}")
                
                lines.append("")
        
        # Add requirements with engaging format
        if self.requirements:
            lines.append("## 📄 Requirements")
            required_items = [r for r in self.requirements if r.required]
            optional_items = [r for r in self.requirements if not r.required]
            
            if required_items:
                lines.append("### Required Documents:")
                for req in required_items:
                    line = f"• {req.item}"
                    if req.description:
                        line += f" - {req.description}"
                    lines.append(line)
                lines.append("")
            
            if optional_items:
                lines.append("### Optional Documents:")
                for req in optional_items:
                    line = f"• {req.item}"
                    if req.description:
                        line += f" - {req.description}"
                    if req.alternative:
                        line += f" (Alternative: {req.alternative})"
                    lines.append(line)
                lines.append("")
        
        # Add notes with engaging format
        if self.notes:
            lines.append("## ⚠️ Important Notes")
            for note in self.notes:
                lines.append(f"• {note}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_tagalog(self) -> str:
        """Format response in Tagalog with engaging structure."""
        lines = []
        
        # Add engaging header
        lines.append(f"📋 {self.title}")
        lines.append("=" * len(f"📋 {self.title}"))
        lines.append("")
        
        # Add main information from sections with engaging formatting
        sorted_sections = sorted(self.sections, key=lambda x: x.order)
        for section in sorted_sections:
            lines.append(f"## {section.title}")
            lines.append(section.content)
            lines.append("")
        
        # Add contact information with engaging format
        if self.contacts:
            lines.append("## 📞 Impormasyon ng Contact")
            for contact in self.contacts:
                lines.append(f"**{contact.name}**")
                if contact.office:
                    lines.append(f"  📍 Opisina: {contact.office}")
                if contact.phone:
                    lines.append(f"  📞 Telepono: {contact.phone}")
                if contact.email:
                    lines.append(f"  📧 Email: {contact.email}")
                if contact.hours:
                    lines.append(f"  🕐 Oras: {contact.hours}")
                lines.append("")
        
        # Add steps with engaging format
        if self.steps:
            lines.append("## 📋 Mga Hakbang")
            for step in sorted(self.steps, key=lambda x: x.step_number):
                lines.append(f"### Hakbang {step.step_number}: {step.title}")
                lines.append(step.description)
                
                if step.requirements:
                    lines.append("**Kailangang dokumento:**")
                    for req in step.requirements:
                        lines.append(f"  • {req}")
                
                if step.estimated_time:
                    lines.append(f"**Tinatayang oras:** {step.estimated_time}")
                
                if step.notes:
                    lines.append(f"**Tandaan:** {step.notes}")
                
                lines.append("")
        
        # Add requirements with engaging format
        if self.requirements:
            lines.append("## 📄 Mga Kailangan")
            required_items = [r for r in self.requirements if r.required]
            optional_items = [r for r in self.requirements if not r.required]
            
            if required_items:
                lines.append("### Kinakailangang Dokumento:")
                for req in required_items:
                    line = f"• {req.item}"
                    if req.description:
                        line += f" - {req.description}"
                    lines.append(line)
                lines.append("")
            
            if optional_items:
                lines.append("### Opsyonal na Dokumento:")
                for req in optional_items:
                    line = f"• {req.item}"
                    if req.description:
                        line += f" - {req.description}"
                    if req.alternative:
                        line += f" (Alternatibo: {req.alternative})"
                    lines.append(line)
                lines.append("")
        
        # Add notes with engaging format
        if self.notes:
            lines.append("## ⚠️ Mahalagang Tala")
            for note in self.notes:
                lines.append(f"• {note}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_hiligaynon(self) -> str:
        """Format response in Hiligaynon/Aklanon with engaging structure."""
        lines = []
        
        # Add engaging header
        lines.append(f"📋 {self.title}")
        lines.append("=" * len(f"📋 {self.title}"))
        lines.append("")
        
        # Add main information from sections with engaging formatting
        sorted_sections = sorted(self.sections, key=lambda x: x.order)
        for section in sorted_sections:
            lines.append(f"## {section.title}")
            lines.append(section.content)
            lines.append("")
        
        # Add contact information with engaging format
        if self.contacts:
            lines.append("## 📞 Impormasyon sang Contact")
            for contact in self.contacts:
                lines.append(f"**{contact.name}**")
                if contact.office:
                    lines.append(f"  📍 Opisina: {contact.office}")
                if contact.phone:
                    lines.append(f"  📞 Telepono: {contact.phone}")
                if contact.email:
                    lines.append(f"  📧 Email: {contact.email}")
                if contact.hours:
                    lines.append(f"  🕐 Oras: {contact.hours}")
                lines.append("")
        
        # Add steps with engaging format
        if self.steps:
            lines.append("## 📋 Mga Tikang")
            for step in sorted(self.steps, key=lambda x: x.step_number):
                lines.append(f"### Tikang {step.step_number}: {step.title}")
                lines.append(step.description)
                
                if step.requirements:
                    lines.append("**Kinahanglan nga dokumento:**")
                    for req in step.requirements:
                        lines.append(f"  • {req}")
                
                if step.estimated_time:
                    lines.append(f"**Banabana nga oras:** {step.estimated_time}")
                
                if step.notes:
                    lines.append(f"**Timan-i:** {step.notes}")
                
                lines.append("")
        
        # Add requirements with engaging format
        if self.requirements:
            lines.append("## 📄 Mga Kinahanglan")
            required_items = [r for r in self.requirements if r.required]
            optional_items = [r for r in self.requirements if not r.required]
            
            if required_items:
                lines.append("### Kinahanglan nga Dokumento:")
                for req in required_items:
                    line = f"• {req.item}"
                    if req.description:
                        line += f" - {req.description}"
                    lines.append(line)
                lines.append("")
            
            if optional_items:
                lines.append("### Opsyonal nga Dokumento:")
                for req in optional_items:
                    line = f"• {req.item}"
                    if req.description:
                        line += f" - {req.description}"
                    if req.alternative:
                        line += f" (Alternatibo: {req.alternative})"
                    lines.append(line)
                lines.append("")
        
        # Add notes with engaging format
        if self.notes:
            lines.append("## ⚠️ Importante nga Tala")
            for note in self.notes:
                lines.append(f"• {note}")
            lines.append("")
        
        return "\n".join(lines)

class StructuredResponseBuilder:
    """Builder class for creating structured responses."""
    
    def __init__(self):
        self.response: Optional[StructuredResponse] = None
        
    def create_response(self, response_type: ResponseType, title: str, language: str = "english") -> 'StructuredResponseBuilder':
        """Create a new structured response."""
        self.response = StructuredResponse(response_type, title, language)
        return self
        
    def add_section(self, title: str, content: str, section_type: str = "default", order: int = 0) -> 'StructuredResponseBuilder':
        """Add a section to the response."""
        if self.response:
            self.response.add_section(title, content, section_type, order)
        return self
        
    def add_step(self, step_number: int, title: str, description: str, 
                 requirements: Optional[List[str]] = None,
                 notes: Optional[str] = None,
                 estimated_time: Optional[str] = None) -> 'StructuredResponseBuilder':
        """Add a step to the response."""
        if self.response:
            self.response.add_step(step_number, title, description, requirements, notes, estimated_time)
        return self
        
    def add_requirement(self, item: str, required: bool = True, 
                       description: Optional[str] = None,
                       alternative: Optional[str] = None) -> 'StructuredResponseBuilder':
        """Add a requirement to the response."""
        if self.response:
            self.response.add_requirement(item, required, description, alternative)
        return self
        
    def add_contact(self, name: str, phone: Optional[str] = None, 
                   email: Optional[str] = None, office: Optional[str] = None,
                   hours: Optional[str] = None) -> 'StructuredResponseBuilder':
        """Add contact information to the response."""
        if self.response:
            self.response.add_contact(name, phone, email, office, hours)
        return self
        
    def add_note(self, note: str) -> 'StructuredResponseBuilder':
        """Add a note to the response."""
        if self.response:
            self.response.add_note(note)
        return self
        
    def build(self) -> str:
        """Build and format the final response."""
        if self.response:
            return self.response.format_response()
        return "No response configured."