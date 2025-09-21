"""
Response Templates for Common Procedural Queries
==============================================

This module contains pre-built templates for common procedural responses
that can be customized based on the specific query and database information.
"""

from typing import Dict, Any, Optional
from structured_response import StructuredResponseBuilder, ResponseType

class ResponseTemplates:
    """Collection of response templates for common procedural queries."""
    
    def __init__(self):
        self.templates = {
            "enrollment": self._create_enrollment_template,
            "transfer": self._create_transfer_template,
            "graduation": self._create_graduation_template,
            "documents": self._create_document_request_template,
            "financial": self._create_financial_template,
            "programs": self._create_programs_template,
            "requirements": self._create_requirements_template,
            "offices": self._create_office_info_template,
            "deadlines": self._create_deadlines_template,
            "contact_info": self._create_contact_template
        }
    
    def get_template(self, template_name: str, language: str = "english", **kwargs) -> str:
        """Get a formatted template response."""
        if template_name in self.templates:
            return self.templates[template_name](language, **kwargs)
        return self._create_generic_template(language, **kwargs)
    
    def _create_enrollment_template(self, language: str = "english", **kwargs) -> str:
        """Create elementary school enrollment procedure template."""
        if language.lower() in ['tagalog', 'filipino']:
            title = "📚 Proseso ng Pag-enroll sa Elementary School"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.PROCEDURAL, title, language
            )
            
            builder.add_section(
                "📋 Pangkalahatang Impormasyon",
                "Ang enrollment sa Tomas SM. Bautista Elementary School ay para sa mga batang "
                "magaaral mula Kindergarten hanggang Grade 6. Sundin ang mga hakbang na ito.",
                order=1
            )
            
            builder.add_step(
                1, "Maghanda ng mga Dokumento ng Bata",
                "Tipunin ang lahat ng kinakailangang dokumento para sa inyong anak.",
                requirements=[
                    "Birth Certificate (PSA Copy)",
                    "Form 137 (School Records) - kung galing sa ibang school",
                    "Medical Certificate/Health Record",
                    "2x2 ID Pictures ng bata (4 pieces)",
                    "Certificate of Good Moral Character (para sa transferee)"
                ],
                estimated_time="1-2 araw"
            )
            
            builder.add_step(
                2, "Pumunta sa School Office",
                "Magsubmit ng mga dokumento at kumpletuhin ang enrollment form.",
                estimated_time="30-45 minuto"
            )
            
            builder.add_step(
                3, "Assessment (kung kinakailangan)",
                "Para sa ibang grade level, maaaring may simple assessment.",
                estimated_time="30 minuto"
            )
            
            builder.add_step(
                4, "Bayad ng School Fees",
                "Magbayad ng enrollment fee at iba pang school fees.",
                estimated_time="15-30 minuto"
            )
            
            builder.add_contact(
                "📞 School Office",
                phone="(036) 269-6345",
                office="Main School Building",
                hours="8:00 AM - 5:00 PM (Lunes-Biyernes)"
            )
            
            builder.add_note("⚠️ Magdala ng kopya ng lahat ng dokumento.")
            builder.add_note("• Para sa Kindergarten: Minimum age requirement ay 5 taong gulang.")
            builder.add_note("• Enrollment period ay limitado - mag-enroll ng maaga.")
            
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = "📚 Proseso sang Pag-enroll sa Elementary School"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.PROCEDURAL, title, language
            )
            
            builder.add_section(
                "📋 Kinatibuk-an nga Impormasyon",
                "Ang enrollment sa Tomas SM. Bautista Elementary School para sa mga bata "
                "halin sa Kindergarten tubtob sa Grade 6. Sunda-i ini nga mga tikang.",
                order=1
            )
            
            builder.add_step(
                1, "Pag-andam sang mga Dokumento",
                "Tipuna ang tanan nga kinahanglan nga dokumento para sa enrollment.",
                requirements=[
                    "Form 138 (High School Report Card)",
                    "Birth Certificate (PSA Copy)",
                    "Medical Certificate",
                    "2x2 ID Pictures (4 ka piraso)"
                ],
                estimated_time="1-2 ka adlaw"
            )
            
            builder.add_step(
                2, "Kadto sa Admissions Office",
                "Isumite ang mga dokumento kag kumpletuha ang application form.",
                estimated_time="30-45 ka minuto"
            )
            
            builder.add_step(
                3, "Assessment kag Entrance Exam",
                "Apil sa entrance examination (kon kinahanglan).",
                estimated_time="2-3 ka oras"
            )
            
            builder.add_step(
                4, "Bayad sang Enrollment Fee",
                "Magbayad sa Cashier's Office pagkatapos sang assessment.",
                estimated_time="15-30 ka minuto"
            )
            
            builder.add_contact(
                "Admissions Office",
                phone="(036) 269-6345",
                office="Ground Floor, Admin Building",
                hours="8:00 AM - 5:00 PM (Lunes-Biyernes)"
            )
            
            builder.add_note("Magdala sang kopya sang tanan nga dokumento.")
            builder.add_note("Enrollment period limitado - mag-enroll sing maayo.")
            
        else:  # English
            title = "📚 Elementary School Enrollment Process"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.PROCEDURAL, title, language
            )
            
            builder.add_section(
                "📋 Overview",
                "Enrollment at Tomas SM. Bautista Elementary School is for students from "
                "Kindergarten through Grade 6. Follow these steps for successful enrollment.",
                order=1
            )
            
            builder.add_step(
                1, "Prepare Required Documents for Your Child",
                "Gather all necessary documents for your child's enrollment application.",
                requirements=[
                    "Birth Certificate (PSA Copy)",
                    "Form 137 (School Records) - if transferring from another school",
                    "Medical Certificate/Health Record",
                    "2x2 ID Pictures of the child (4 pieces)",
                    "Certificate of Good Moral Character (for transferees)"
                ],
                estimated_time="1-2 days"
            )
            
            builder.add_step(
                2, "Visit the School Office",
                "Submit documents and complete the enrollment form.",
                estimated_time="30-45 minutes"
            )
            
            builder.add_step(
                3, "Assessment (if required)",
                "Some grade levels may require a simple assessment.",
                estimated_time="30 minutes"
            )
            
            builder.add_step(
                4, "Payment of School Fees",
                "Pay enrollment fee and other school fees.",
                estimated_time="15-30 minutes"
            )
            
            builder.add_contact(
                "📞 School Office",
                phone="(036) 269-6345",
                office="Main School Building",
                hours="8:00 AM - 5:00 PM (Monday-Friday)"
            )
            
            builder.add_note("⚠️ Bring photocopies of all documents.")
            builder.add_note("• For Kindergarten: Minimum age requirement is 5 years old.")
            builder.add_note("• Enrollment period is limited - enroll early.")
        
        return builder.build()
    
    def _create_transfer_template(self, language: str = "english", **kwargs) -> str:
        """Create transfer procedure template."""
        if language.lower() in ['tagalog', 'filipino']:
            title = "Proseso ng Transfer"
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = "Proseso sang Transfer"
        else:
            title = "Transfer Process"
        
        builder = StructuredResponseBuilder().create_response(
            ResponseType.PROCEDURAL, title, language
        )
        
        if language.lower() in ['tagalog', 'filipino']:
            builder.add_section(
                "Tungkol sa Transfer",
                "Para sa mga estudyanteng gustong mag-transfer sa aming university.",
                order=1
            )
            
            builder.add_step(
                1, "Kumuha ng Transfer Credentials",
                "Humingi ng Transfer Credentials sa dating school.",
                requirements=[
                    "Transcript of Records (TOR)",
                    "Certificate of Good Moral Character",
                    "Course Syllabus/Curriculum"
                ],
                estimated_time="1-2 linggo"
            )
            
            builder.add_step(
                2, "Credential Evaluation",
                "Ipasuri ang mga subjects sa Registrar's Office.",
                estimated_time="3-5 araw"
            )
            
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            builder.add_section(
                "Parte sang Transfer",
                "Para sa mga estudyante nga gusto mag-transfer sa amon university.",
                order=1
            )
            
            builder.add_step(
                1, "Pagkuha sang Transfer Credentials",
                "Pangayo sang Transfer Credentials sa daan nga eskwelahan.",
                requirements=[
                    "Transcript of Records (TOR)",
                    "Certificate of Good Moral Character",
                    "Course Syllabus/Curriculum"
                ],
                estimated_time="1-2 ka semana"
            )
            
            builder.add_step(
                2, "Credential Evaluation",
                "Pasuria ang mga subject sa Registrar's Office.",
                estimated_time="3-5 ka adlaw"
            )
            
        else:  # English
            builder.add_section(
                "About Transfer",
                "For students wanting to transfer to our university.",
                order=1
            )
            
            builder.add_step(
                1, "Obtain Transfer Credentials",
                "Request transfer credentials from your previous school.",
                requirements=[
                    "Transcript of Records (TOR)",
                    "Certificate of Good Moral Character",
                    "Course Syllabus/Curriculum"
                ],
                estimated_time="1-2 weeks"
            )
            
            builder.add_step(
                2, "Credential Evaluation",
                "Have your subjects evaluated at the Registrar's Office.",
                estimated_time="3-5 days"
            )
        
        builder.add_contact(
            "Registrar's Office",
            phone="(036) 269-6345",
            office="2nd Floor, Admin Building"
        )
        
        return builder.build()
    
    def _create_document_request_template(self, language: str = "english", **kwargs) -> str:
        """Create document request template."""
        doc_type = kwargs.get('document_type', 'transcript')
        
        if language.lower() in ['tagalog', 'filipino']:
            title = f"Paghiling ng {doc_type.title()}"
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = f"Paghangyo sang {doc_type.title()}"
        else:
            title = f"{doc_type.title()} Request Process"
        
        builder = StructuredResponseBuilder().create_response(
            ResponseType.PROCEDURAL, title, language
        )
        
        # Add steps based on document type
        if doc_type.lower() in ['transcript', 'tor']:
            builder.add_requirement("Accomplished Request Form")
            builder.add_requirement("Valid ID (Photocopy)")
            builder.add_requirement("Payment Receipt")
            
        builder.add_contact(
            "Registrar's Office",
            phone="(036) 269-6345",
            office="2nd Floor, Admin Building"
        )
        
        return builder.build()
    
    def _create_programs_template(self, language: str = "english", **kwargs) -> str:
        """Create academic programs template."""
        if language.lower() in ['tagalog', 'filipino']:
            title = "Mga Available na Program"
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = "Mga Available nga Program"
        else:
            title = "Available Academic Programs"
        
        builder = StructuredResponseBuilder().create_response(
            ResponseType.INFORMATIONAL, title, language
        )
        
        return builder.build()
    
    def _create_contact_template(self, language: str = "english", **kwargs) -> str:
        """Create contact information template."""
        office_name = kwargs.get('office', 'University')
        
        if language.lower() in ['tagalog', 'filipino']:
            title = f"📋 Contact Information - {office_name}"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.CONTACT_INFO, title, language
            )
            
            builder.add_section("📞 Main Contact Details", 
                               "• Phone: (036) 269-6345\n• 📧 Email: info@university.edu.ph\n• 📍 Location: Admin Building")
            
            builder.add_section("⏰ Office Hours", 
                               "• Monday - Friday: 8:00 AM - 5:00 PM\n• Saturday: 8:00 AM - 12:00 PM")
            
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = f"📋 Contact Information - {office_name}"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.CONTACT_INFO, title, language
            )
            
            builder.add_section("📞 Main Contact Details", 
                               "• Phone: (036) 269-6345\n• 📧 Email: info@university.edu.ph\n• 📍 Location: Admin Building")
            
            builder.add_section("⏰ Office Hours", 
                               "• Lunes - Biernes: 8:00 AM - 5:00 PM\n• Sabado: 8:00 AM - 12:00 PM")
            
        else:
            title = f"📋 Contact Information - {office_name}"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.CONTACT_INFO, title, language
            )
            
            builder.add_section("📞 Main Contact Details", 
                               "• Phone: (036) 269-6345\n• 📧 Email: info@university.edu.ph\n• 📍 Location: Admin Building")
            
            builder.add_section("⏰ Office Hours", 
                               "• Monday - Friday: 8:00 AM - 5:00 PM\n• Saturday: 8:00 AM - 12:00 PM")
        
        return builder.build()
    
    def _create_financial_template(self, language: str = "english", **kwargs) -> str:
        """Create financial/payment template."""
        if language.lower() in ['tagalog', 'filipino']:
            title = "💰 Proseso ng Pagbabayad ng School Fees"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.PROCEDURAL, title, language
            )
            
            builder.add_section(
                "📋 Impormasyon sa Bayarin",
                "Ang Tomas SM. Bautista Elementary School ay may iba't ibang bayarin para sa mga estudyante.",
                order=1
            )
            
            builder.add_step(
                1, "Kumuha ng Fee Statement",
                "Pumunta sa Cashier's Office upang makakuha ng detalyadong fee statement.",
                estimated_time="10-15 minuto"
            )
            
            builder.add_step(
                2, "Mga Mode ng Pagbabayad",
                "Piliin ang pinakamadaling paraan ng pagbabayad para sa inyo.",
                requirements=[
                    "Cash payment sa Cashier's Office",
                    "Bank payment o money transfer",
                    "Installment plan (kung available)"
                ],
                estimated_time="15-30 minuto"
            )
            
            builder.add_step(
                3, "Mga Kailangan sa Pagbabayad",
                "Magdala ng mga dokumentong kailangan sa pagbabayad.",
                requirements=[
                    "Student ID o School ID",
                    "Previous receipt (kung may installment)",
                    "Valid ID ng magbabayad"
                ]
            )
            
            builder.add_contact(
                "💰 Cashier's Office",
                phone="(036) 269-6345",
                office="Main School Building",
                hours="8:00 AM - 5:00 PM (Lunes-Biyernes)"
            )
            
            builder.add_note("💡 Para sa scholarship programs o financial assistance, makipag-ugnayan sa Guidance Office.")
            builder.add_note("⚠️ Panatilihin ang lahat ng receipt para sa record.")
            
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = "💰 Proseso sang Pagbayad sang School Fees"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.PROCEDURAL, title, language
            )
            
            builder.add_section(
                "📋 Impormasyon sa Bayad",
                "Ang Tomas SM. Bautista Elementary School may lain-lain nga bayad para sa mga estudyante.",
                order=1
            )
            
            builder.add_step(
                1, "Pagkuha sang Fee Statement",
                "Kadto sa Cashier's Office para makakuha sang detalyado nga fee statement.",
                estimated_time="10-15 ka minuto"
            )
            
            builder.add_step(
                2, "Mga Paagi sang Pagbayad",
                "Pilia ang pinaka-madali nga paagi sang pagbayad para sa inyo.",
                requirements=[
                    "Cash payment sa Cashier's Office",
                    "Bank payment ukon money transfer",
                    "Installment plan (kon available)"
                ],
                estimated_time="15-30 ka minuto"
            )
            
            builder.add_contact(
                "💰 Cashier's Office",
                phone="(036) 269-6345",
                office="Main School Building",
                hours="8:00 AM - 5:00 PM (Lunes-Biyernes)"
            )
            
        else:  # English
            title = "💰 School Fees Payment Process"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.PROCEDURAL, title, language
            )
            
            builder.add_section(
                "📋 Payment Information",
                "Tomas SM. Bautista Elementary School has various fees for students from Kindergarten through Grade 6.",
                order=1
            )
            
            builder.add_step(
                1, "Get Fee Statement",
                "Visit the Cashier's Office to obtain a detailed fee statement.",
                estimated_time="10-15 minutes"
            )
            
            builder.add_step(
                2, "Payment Methods",
                "Choose the most convenient payment method for your family.",
                requirements=[
                    "Cash payment at Cashier's Office",
                    "Bank payment or money transfer",
                    "Installment plan (if available)"
                ],
                estimated_time="15-30 minutes"
            )
            
            builder.add_step(
                3, "Required Documents for Payment",
                "Bring necessary documents when making payment.",
                requirements=[
                    "Student ID or School ID",
                    "Previous receipt (for installment)",
                    "Valid ID of the person paying"
                ]
            )
            
            builder.add_contact(
                "💰 Cashier's Office",
                phone="(036) 269-6345",
                office="Main School Building",
                hours="8:00 AM - 5:00 PM (Monday-Friday)"
            )
            
            builder.add_note("💡 For scholarship programs or financial assistance, contact the Guidance Office.")
            builder.add_note("⚠️ Keep all receipts for your records.")
        
        return builder.build()
    
    def _create_graduation_template(self, language: str = "english", **kwargs) -> str:
        """Create graduation procedure template."""
        if language.lower() in ['tagalog', 'filipino']:
            title = "Proseso ng Pagtatapos"
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = "Proseso sang Pagtipos"
        else:
            title = "Graduation Process"
        
        builder = StructuredResponseBuilder().create_response(
            ResponseType.PROCEDURAL, title, language
        )
        
        return builder.build()
    
    def _create_requirements_template(self, language: str = "english", **kwargs) -> str:
        """Create requirements template."""
        req_type = kwargs.get('requirement_type', 'general')
        
        if language.lower() in ['tagalog', 'filipino']:
            title = f"📋 Mga Kailangan - {req_type.title()}"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.REQUIREMENTS, title, language
            )
            
            builder.add_section(
                "📝 Pangkalahatang mga Kailangan",
                "Mga dokumento at requirements na karaniwang kailangan sa elementary school.",
                order=1
            )
            
            # For enrollment requirements
            if req_type.lower() in ['enrollment', 'general', 'admission']:
                builder.add_requirement(
                    "Birth Certificate (PSA Copy)",
                    description="Original PSA-issued birth certificate ng bata",
                    required=True
                )
                
                builder.add_requirement(
                    "School Records (Form 137)",
                    description="Para sa mga transferee mula sa ibang school",
                    required=True
                )
                
                builder.add_requirement(
                    "Medical Certificate",
                    description="Health record mula sa licensed physician",
                    required=True
                )
                
                builder.add_requirement(
                    "2x2 ID Pictures",
                    description="4 pieces na recent pictures ng bata",
                    required=True
                )
                
                builder.add_requirement(
                    "Certificate of Good Moral Character",
                    description="Para sa mga transferee students",
                    required=False
                )
            
            # For graduation requirements
            elif req_type.lower() in ['graduation', 'completion']:
                builder.add_requirement(
                    "Complete Academic Records",
                    description="Lahat ng subjects ay dapat completed",
                    required=True
                )
                
                builder.add_requirement(
                    "Cleared School Fees",
                    description="Walang pending na school fees",
                    required=True
                )
                
                builder.add_requirement(
                    "Library Clearance",
                    description="Walang pending na library books",
                    required=True
                )
            
            builder.add_contact(
                "📞 School Office",
                phone="(036) 269-6345",
                office="Main School Building",
                hours="8:00 AM - 5:00 PM (Lunes-Biyernes)"
            )
            
            builder.add_note("⚠️ Magdala ng kopya ng lahat ng dokumento.")
            builder.add_note("💡 Para sa kumpletong lista, makipag-ugnayan sa School Office.")
            
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = f"📋 Mga Kinahanglan - {req_type.title()}"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.REQUIREMENTS, title, language
            )
            
            builder.add_section(
                "📝 Kinatibuk-an nga mga Kinahanglan",
                "Mga dokumento kag requirements nga kinahanglan sa elementary school.",
                order=1
            )
            
            # Similar structure but in Hiligaynon
            if req_type.lower() in ['enrollment', 'general', 'admission']:
                builder.add_requirement(
                    "Birth Certificate (PSA Copy)",
                    description="Original PSA-issued birth certificate sang bata",
                    required=True
                )
                
                builder.add_requirement(
                    "School Records (Form 137)",
                    description="Para sa mga transferee halin sa iban nga school",
                    required=True
                )
            
            builder.add_contact(
                "📞 School Office",
                phone="(036) 269-6345",
                office="Main School Building",
                hours="8:00 AM - 5:00 PM (Lunes-Biyernes)"
            )
            
        else:  # English
            title = f"📋 Requirements - {req_type.title()}"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.REQUIREMENTS, title, language
            )
            
            builder.add_section(
                "📝 General Requirements",
                "Documents and requirements commonly needed for elementary school processes.",
                order=1
            )
            
            # For enrollment requirements
            if req_type.lower() in ['enrollment', 'general', 'admission']:
                builder.add_requirement(
                    "Birth Certificate (PSA Copy)",
                    description="Original PSA-issued birth certificate of the child",
                    required=True
                )
                
                builder.add_requirement(
                    "School Records (Form 137)",
                    description="For transferees from other schools",
                    required=True
                )
                
                builder.add_requirement(
                    "Medical Certificate",
                    description="Health record from a licensed physician",
                    required=True
                )
                
                builder.add_requirement(
                    "2x2 ID Pictures",
                    description="4 pieces of recent pictures of the child",
                    required=True
                )
                
                builder.add_requirement(
                    "Certificate of Good Moral Character",
                    description="For transferee students",
                    required=False
                )
            
            # For graduation requirements
            elif req_type.lower() in ['graduation', 'completion']:
                builder.add_requirement(
                    "Complete Academic Records",
                    description="All subjects must be completed",
                    required=True
                )
                
                builder.add_requirement(
                    "Cleared School Fees",
                    description="No pending school fees",
                    required=True
                )
                
                builder.add_requirement(
                    "Library Clearance",
                    description="No pending library books",
                    required=True
                )
            
            builder.add_contact(
                "📞 School Office",
                phone="(036) 269-6345",
                office="Main School Building",
                hours="8:00 AM - 5:00 PM (Monday-Friday)"
            )
            
            builder.add_note("⚠️ Bring photocopies of all documents.")
            builder.add_note("💡 For complete list, contact the School Office.")
        
        return builder.build()
    
    def _create_office_info_template(self, language: str = "english", **kwargs) -> str:
        """Create office information template."""
        office_name = kwargs.get('office', 'Office')
        
        if language.lower() in ['tagalog', 'filipino']:
            title = f"📋 Impormasyon ng {office_name}"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.INFORMATIONAL, title, language
            )
            
            builder.add_section("📍 Location", "• Admin Building, Ground Floor")
            
            builder.add_section("⏰ Office Hours", 
                               "• Monday - Friday: 8:00 AM - 5:00 PM\n• Saturday: 8:00 AM - 12:00 PM")
            
            builder.add_section("📞 Contact", "• Phone: (036) 269-6345")
            
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = f"📋 Impormasyon sang {office_name}"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.INFORMATIONAL, title, language
            )
            
            builder.add_section("📍 Location", "• Admin Building, Ground Floor")
            
            builder.add_section("⏰ Office Hours", 
                               "• Lunes - Biernes: 8:00 AM - 5:00 PM\n• Sabado: 8:00 AM - 12:00 PM")
            
            builder.add_section("📞 Contact", "• Phone: (036) 269-6345")
            
        else:
            title = f"📋 {office_name} Information"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.INFORMATIONAL, title, language
            )
            
            builder.add_section("📍 Location", "• Admin Building, Ground Floor")
            
            builder.add_section("⏰ Office Hours", 
                               "• Monday - Friday: 8:00 AM - 5:00 PM\n• Saturday: 8:00 AM - 12:00 PM")
            
            builder.add_section("📞 Contact", "• Phone: (036) 269-6345")
        
        return builder.build()
    
    def _create_deadlines_template(self, language: str = "english", **kwargs) -> str:
        """Create deadlines/timeline template."""
        if language.lower() in ['tagalog', 'filipino']:
            title = "📋 Mga Deadline at Timeline"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.TIMELINE, title, language
            )
            
            builder.add_section("📅 Important Dates", 
                               "• Enrollment Period: May - June\n• Classes Start: July\n• Final Exams: March")
            
            builder.add_section("⚠️ Reminder", 
                               "• Submit requirements early\n• Check official website for updates")
            
        elif language.lower() in ['hiligaynon', 'ilonggo']:
            title = "📋 Mga Deadline kag Timeline"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.TIMELINE, title, language
            )
            
            builder.add_section("📅 Important Dates", 
                               "• Enrollment Period: May - June\n• Classes Start: July\n• Final Exams: March")
            
            builder.add_section("⚠️ Reminder", 
                               "• Submit requirements early\n• Check official website for updates")
            
        else:
            title = "📋 Deadlines and Timeline"
            builder = StructuredResponseBuilder().create_response(
                ResponseType.TIMELINE, title, language
            )
            
            builder.add_section("📅 Important Dates", 
                               "• Enrollment Period: May - June\n• Classes Start: July\n• Final Exams: March")
            
            builder.add_section("⚠️ Reminder", 
                               "• Submit requirements early\n• Check official website for updates")
        
        return builder.build()
    
    def _create_generic_template(self, language: str = "english", **kwargs) -> str:
        """Create a generic structured template."""
        title = kwargs.get('title', 'Information')
        
        builder = StructuredResponseBuilder().create_response(
            ResponseType.INFORMATIONAL, title, language
        )
        
        return builder.build()
    
    def customize_template(self, template_name: str, language: str, database_info: Dict[str, Any]) -> str:
        """Customize a template with information from the database."""
        base_template = self.get_template(template_name, language)
        
        # Here you would integrate database information into the template
        # This is a placeholder for the integration logic
        
        return base_template