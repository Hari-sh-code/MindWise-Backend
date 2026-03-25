"""
Job Description Processing Service.
Handles pasted job descriptions from user input.
"""

import logging

logger = logging.getLogger(__name__)


class JobDescriptionProcessor:

    MIN_JD_LENGTH = 100
    MAX_JD_LENGTH = 8000

    def process(self, job_description: str) -> str:

        try:

            if not job_description or len(job_description.strip()) < self.MIN_JD_LENGTH:
                raise ValueError(
                    "Job description is too short. Please paste the full job description."
                )

            cleaned_description = self._clean_text(job_description)

            cleaned_description = self._limit_text(cleaned_description)

            logger.info(f"Processed job description length: {len(cleaned_description)}")

            return cleaned_description

        except Exception as e:
            logger.error(f"Failed to process job description: {e}")
            raise ValueError(f"Invalid job description: {str(e)}")

    def _clean_text(self, text: str) -> str:

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        cleaned_lines = []
        prev_line = None

        for line in lines:
            if line != prev_line:
                cleaned_lines.append(line)
                prev_line = line

        return "\n".join(cleaned_lines)

    def _limit_text(self, text: str) -> str:

        if len(text) > self.MAX_JD_LENGTH:
            return text[: self.MAX_JD_LENGTH]

        return text


job_processor = JobDescriptionProcessor()