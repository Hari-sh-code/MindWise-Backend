"""
PDF Resume Generation Service.
Converts resume JSON data to HTML and generates downloadable PDFs using WeasyPrint.
"""
import logging
import re
from typing import Dict, Any, Optional
from io import BytesIO

logger = logging.getLogger(__name__)

# Try to import WeasyPrint, provide helpful error if missing
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint not installed. PDF generation will not be available. "
                  "Install with: pip install weasyprint")


LAYOUT_CONFIGS = [
    {
        "name": "spacious",
        "font": 11.5,
        "line_height": 1.4,
        "section_gap": 10,
        "trim": 120
    },
    {
        "name": "balanced",
        "font": 11,
        "line_height": 1.35,
        "section_gap": 8,
        "trim": 100
    },
    {
        "name": "compact",
        "font": 10.5,
        "line_height": 1.3,
        "section_gap": 6,
        "trim": 85
    }
]


class PDFService:
    """Service for generating resume PDFs from resume data."""
    
    # HTML template for premium FAANG-level resume
    RESUME_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resume</title>
        <style>
            @page {{
                size: A4;
                margin: 15mm 15mm;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
                color: #111;
                background-color: #fff;
                page-break-inside: avoid;
            }}
            
            /* DYNAMIC FONTS & SPACING INJECTED HERE */
            {dynamic_css}
            
            p {{
                orphans: 3;
                widows: 3;
            }}
            
            .cert-list {{
                line-height: 1.4;
                word-break: break-word;
            }}
            
            .container {{
                max-width: 100%;
                margin: 0;
                background: white;
            }}
            
            /* Header / Personal Info */
            .header {{
                text-align: center;
                margin-bottom: 12px;
            }}
            
            .name {{
                font-size: 20px;
                font-weight: 700;
                letter-spacing: 0.5px;
                color: #111;
                margin-bottom: 4px;
                text-transform: uppercase;
            }}
            
            .contact-info {{
                font-size: 12px;
                color: #111;
            }}
            
            .contact-info a {{
                color: #111;
                text-decoration: none;
            }}
            
            /* Typography elements */
            .separator {{
                margin: 0 4px;
                color: #444;
            }}
            
            /* Sections */
            .section {{
                page-break-inside: avoid;
            }}
            
            .section-title {{
                font-size: 14px;
                font-weight: 700;
                color: #000;
                text-transform: uppercase;
                letter-spacing: 1px;
                border-bottom: 1px solid #ccc;
                padding-bottom: 2px;
                margin-bottom: 6px;
            }}
            
            /* Experience / Projects / Education */
            .item {{
                margin-bottom: 4px;
                page-break-inside: avoid;
            }}
            
            .item-header {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                margin-bottom: 2px;
            }}
            
            .item-title {{
                font-weight: 700;
                color: #111;
            }}
            
            .company {{
                font-style: italic;
                color: #444;
            }}
            
            .item-date {{
                font-size: 12px;
                color: #111;
                white-space: nowrap;
            }}
            
            /* Bullets */
            .bullets {{
                list-style-type: none;
                margin: 0;
                padding-left: 0;
            }}
            
            .bullets li {{
                margin-bottom: 2px;
                padding-left: 12px;
                position: relative;
            }}
            
            .bullets li::before {{
                content: "•";
                position: absolute;
                left: 2px;
                color: #111;
            }}
            
            /* Layout structures */
            .columns::after {{
                content: "";
                display: table;
                clear: both;
            }}
            
            .col {{
                float: left;
                width: 48%; /* Leave 4% gap */
            }}
            
            .col:last-child {{
                float: right;
            }}
            
            /* Print optimizations */
            @media print {{
                body {{
                    margin: 0;
                    padding: 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div class="name">{name}</div>
                <div class="contact-info">{contact_info}</div>
            </div>
            
            <!-- Summary -->
            {summary_section}
            
            <!-- Skills -->
            {skills_section}
            
            <!-- Experience -->
            {experience_section}
            
            <!-- Projects -->
            {projects_section}
            
            <!-- Education & Certifications -->
            <div class="columns">
                <div class="col">{education_section}</div>
                <div class="col">{certifications_section}</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    @staticmethod
    def clean_text(text: Any) -> str:
        """Strip weird unicode, broken spacings, and return clean strings safely."""
        if not text:
            return ""
        text = str(text).replace("\uFFFD", "")
        # Remove weird unicode dots, dashes
        text = text.replace('\u2022', '').replace('\u2013', '-').replace('\u2014', '-')
        # Clean extra spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def smart_trim(text: str, limit: int) -> str:
        """Dynamically trim text elegantly based on layout constraints without abrupt slicing."""
        if not text:
            return ""
        text = PDFService.clean_text(text)
        if len(text) <= limit:
            return text
        return text[:limit].rsplit(" ", 1)[0] + "..."

    @staticmethod
    def estimate_content_size(resume_data: Dict[str, Any]) -> int:
        """Estimate the volume of characters inside the resume for calculating layout flow."""
        size = 0
        size += len(resume_data.get("summary", ""))

        for exp in resume_data.get("experience", []):
            size += len(exp.get("description", ""))

        for proj in resume_data.get("projects", []):
            size += len(proj.get("description", ""))

        size += len(resume_data.get("skills", [])) * 10
        return size

    @staticmethod
    def choose_layout(resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize into Spacious, Balanced, or Compact based strictly on estimated density limit bounds."""
        size = PDFService.estimate_content_size(resume_data)
        if size < 600:
            return LAYOUT_CONFIGS[0]
        elif size < 1000:
            return LAYOUT_CONFIGS[1]
        else:
            return LAYOUT_CONFIGS[2]

    @staticmethod
    def build_dynamic_css(layout: Dict[str, Any]) -> str:
        """Generate safe, dynamic CSS dimensions tailored exactly to the active Layout block."""
        return f"""
        body {{
            font-size: {layout['font']}px;
            line-height: {layout['line_height']};
        }}

        .section {{
            margin-bottom: {layout['section_gap']}px;
        }}
        """

    def generate_pdf(self, resume_data: Dict[str, Any]) -> Optional[bytes]:
        """
        Generate premium FAANG-level ATS-friendly PDF dynamically adapting sizes and trims to strictly fit onto 1-page bounds.
        """
        if not WEASYPRINT_AVAILABLE:
            logger.error("WeasyPrint is not installed. Cannot generate PDF.")
            return None
        
        try:
            if not resume_data:
                logger.error("Resume data is empty")
                return None
            
            # Select Adaptive layout limits dynamically
            layout = self.choose_layout(resume_data)
            logger.info(f"Using layout mode dynamically: {layout['name']}")
            
            # Extract data sections natively
            personal_info = resume_data.get("personal_info", {})
            social_links = resume_data.get("social_links", {})
            summary = resume_data.get("summary", "")
            skills = resume_data.get("skills", [])
            experience = resume_data.get("experience", [])
            projects = resume_data.get("projects", [])
            education = resume_data.get("education", [])
            certifications = resume_data.get("certifications", [])
            
            # Build Layout-Dependent HTML parts
            dynamic_css = self.build_dynamic_css(layout)
            
            name = self._build_name(personal_info)
            contact_info = self._build_contact_info(personal_info, social_links)
            
            summary_section = self._build_summary_section(summary, layout)
            skills_section = self._build_skills_section(skills)
            experience_section = self._build_experience_section(experience, layout)
            projects_section = self._build_projects_section(projects, layout)
            education_section = self._build_education_section(education)
            certifications_section = self._build_certifications_section(certifications)
            
            # Fill the template dynamically combining configurations seamlessly
            html_content = self.RESUME_TEMPLATE.format(
                dynamic_css=dynamic_css,
                name=name,
                contact_info=contact_info,
                summary_section=summary_section,
                skills_section=skills_section,
                experience_section=experience_section,
                projects_section=projects_section,
                education_section=education_section,
                certifications_section=certifications_section
            )
            
            # Final Generation output
            logger.info("Generating PDF from HTML with WeasyPrint")
            pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
            
            logger.info(f"PDF generated successfully: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate PDF dynamically config: {e}")
            return None
    
    # ========================================================================
    # HTML BUILDERS / TEMPORARY EXTENSIONS
    # ========================================================================
    
    def _build_name(self, personal_info: Dict[str, Any]) -> str:
        first_name = self.clean_text(personal_info.get("first_name"))
        last_name = self.clean_text(personal_info.get("last_name"))
        return f"{first_name} {last_name}".strip() or "Professional"
    
    def _build_contact_info(self, personal_info: Dict[str, Any], social_links: Dict[str, Any]) -> str:
        contact_items = []
        email = self.clean_text(personal_info.get("email"))
        if email:
            contact_items.append(f'<a href="mailto:{email}">{email}</a>')
            
        phone = self.clean_text(personal_info.get("phone"))
        if phone:
            contact_items.append(f'<a href="tel:{phone}">{phone}</a>')
             
        if social_links:
            linkedin = self.clean_text(social_links.get("linkedin"))
            if linkedin:
                display = linkedin.replace("https://", "").replace("www.", "").strip("/")
                contact_items.append(f'<a href="{linkedin}">{display}</a>')
                
            github = self.clean_text(social_links.get("github"))
            if github:
                display = github.replace("https://", "").replace("www.", "").strip("/")
                contact_items.append(f'<a href="{github}">{display}</a>')
                
        return " | ".join(contact_items)
    
    def _build_summary_section(self, summary: str, layout: Dict[str, Any]) -> str:
        # We multiply the layout trim by 4 here since it defines the length of a single short bullet
        # The summary is a full paragraph, so it safely deserves a larger allowance than a generic bullet node
        max_summary_length = layout["trim"] * 4
        summary_text = self.smart_trim(summary, max_summary_length)
        if not summary_text:
            return ""
        return f'''
        <div class="section">
            <div class="section-title">Summary</div>
            <div>{summary_text}</div>
        </div>
        '''
    
    def _build_skills_section(self, skills: list) -> str:
        if not skills:
            return ""
        skills_list = []
        for skill in skills:
            if isinstance(skill, dict):
                skill_name = self.clean_text(skill.get("name"))
            else:
                skill_name = self.clean_text(skill)
            if skill_name:
                skills_list.append(skill_name)
        
        if not skills_list:
            return ""
        skills_text = ", ".join(skills_list)
        return f'''
        <div class="section">
            <div class="section-title">Skills</div>
            <div>{skills_text}</div>
        </div>
        '''
    
    def _build_experience_section(self, experience: list, layout: Dict[str, Any]) -> str:
        if not experience:
            return ""
        experience = experience[:3]  # Strict constraint: max 3 roles to secure page sizing securely 
        experience_html = []
        for job in experience:
            role = self.clean_text(job.get("role") or "Role")
            company = self.clean_text(job.get("company_name") or "Company")
            
            start = self.clean_text(job.get("start_date"))
            if start and len(start) >= 7: start = start[:7]
            end = "Present" if job.get("is_current") else self.clean_text(job.get("end_date"))
            if end and len(end) >= 7 and end != "Present": end = end[:7]
            date_str = f"{start} - {end}" if start and end else (start or end)
            
            desc = self.clean_text(job.get("description"))
            bullets = [b.strip().strip('-*• ') for b in desc.split('\\n') if b.strip()]
            bullets = bullets[:3]  # Dynamic allowance capped gracefully 
            
            bullets_html = ""
            if bullets:
                bullets_html = '<ul class="bullets">'
                for b in bullets:
                    # layout['trim'] is strictly implemented per user directives 
                    bullet_text = self.smart_trim(b, layout["trim"])
                    bullets_html += f"<li>{bullet_text}</li>"
                bullets_html += '</ul>'
            
            job_html = f'''
            <div class="item">
                <div class="item-header">
                    <div><span class="item-title">{role}</span></div>
                    <div class="item-date">{date_str}</div>
                </div>
                <div class="company" style="margin-bottom: 2px;">{company}</div>
                {bullets_html}
            </div>
            '''
            experience_html.append(job_html)
        
        return f'''
        <div class="section">
            <div class="section-title">Experience</div>
            {"".join(experience_html)}
        </div>
        '''
    
    def _build_projects_section(self, projects: list, layout: Dict[str, Any]) -> str:
        if not projects:
            return ""
        projects = projects[:3]  # Strict constraint: max 3 projects
        projects_html = []
        for project in projects:
            title = self.clean_text(project.get("title"))
            if not title:
                continue
            tech_stack = project.get("tech_stack", [])
            tech_text = ""
            if tech_stack:
                if isinstance(tech_stack, list):
                    tech_list = [self.clean_text(str(t)) for t in tech_stack if t]
                    tech_text = ", ".join(tech_list[:4])
                else:
                    tech_text = self.clean_text(tech_stack)
            
            desc = self.clean_text(project.get("description"))
            bullets = [b.strip().strip('-*• ') for b in desc.split('\\n') if b.strip()]
            
            bullets_html = ""
            if bullets:
                # Apply dynamic layout trimming scaling proportionally 
                bullet_text = self.smart_trim(bullets[0] if bullets else desc, layout["trim"] * 2)
                bullets_html = f'<ul class="bullets"><li>{bullet_text}</li></ul>'
            
            tech_line = f'<div class="company" style="margin-bottom: 2px;">Technologies: {tech_text}</div>' if tech_text else ''
            
            proj_html = f'''
            <div class="item">
                <div class="item-header">
                    <div><span class="item-title">{title}</span></div>
                </div>
                {tech_line}
                {bullets_html}
            </div>
            '''
            projects_html.append(proj_html)
        
        return f'''
        <div class="section">
            <div class="section-title">Projects</div>
            {"".join(projects_html)}
        </div>
        '''
    
    def _build_education_section(self, education: list) -> str:
        if not education:
            return ""
        education = education[:2]
        education_html = []
        for school in education:
            college = self.clean_text(school.get("college") or school.get("school") or "School")
            degree = self.clean_text(school.get("degree") or "Degree")
            year = self.clean_text(school.get("year", ""))
            
            edu_html = f'''
            <div class="item">
                <div class="item-header">
                    <div><span class="item-title">{degree}</span></div>
                </div>
                <div style="margin-bottom: 1px;">{college}</div>
                <div class="company" style="font-size: 12px;">Graduated: {year}</div>
            </div>
            '''
            education_html.append(edu_html)
        return f'''
        <div class="section">
            <div class="section-title">Education</div>
            {"".join(education_html)}
        </div>
        '''
    
    def _build_certifications_section(self, certifications: list) -> str:
        if not certifications:
            return ""
        certifications = certifications[:4]  # Enforce hard limits conservatively 
        certs_html = []
        for cert in certifications:
            if isinstance(cert, dict):
                title = self.clean_text(cert.get("title"))
                issuer = self.clean_text(cert.get("issuer", ""))
            else:
                title = self.clean_text(cert)
                issuer = ""
            if not title:
                continue
            item_html = f'''
            <div class="item">
                <div class="item-header">
                    <div><span class="item-title">{title}</span></div>
                </div>
                <div class="company" style="font-size: 12px;">{issuer}</div>
            </div>
            '''
            certs_html.append(item_html)
        
        if not certs_html:
            return ""
            
        return f'''
        <div class="section">
            <div class="section-title">Certifications</div>
            {"".join(certs_html)}
        </div>
        '''

# Singleton instance exported 
pdf_service = PDFService()
