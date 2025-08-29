from __future__ import annotations
from rich.console import Console
from printer import Printer
from agents import Runner, gen_trace_id, trace

import traceback
from urllib.parse import urlparse
import json

import os
import sys

# Add current path to sys.path
sys.path.append(os.getcwd())
from printer import Printer

from helper_agents.resume_parser_agent import (
    resume_parser_agent,
    ResumeItem,
    file_to_markdown,
)
from helper_agents.jd_parser_agent import jd_parser_agent, web_scraper_tool, JDItem
from helper_agents.content_revise_agent import content_revise_agent
from helper_agents.expression_revise_agent import expression_revise_agent
from helper_agents.evaluation_agent import evaluation_agent, EvaluationResult

from dataclasses import dataclass


@dataclass
class Config:
    max_iterations: int = 3
    content_score_threshold: int = 8
    expression_score_threshold: int = 9
    # conversion_dir: str = "./converted_resume"
    converted_resume_target_path: str = "./converted_resume/target_resume.md"
    converted_resume_reference_path: str = "./converted_resume/reference_resume.md"
    converted_resume_store_path: str = "./converted_resume/"

    def __post_init__(self):
        os.makedirs(self.converted_resume_store_path, exist_ok=True)


class ResumeImprovementManager:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.console = Console()
        self.printer = Printer(self.console)

    async def run(
        self, target_resume_file_path, jd_website, reference_resume_file_path: str
    ) -> None:
        try:
            # Validate inputs
            self._validate_inputs(
                target_resume_file_path, jd_website, reference_resume_file_path
            )
        except Exception as e:
            self.printer.update_item("error", f"Process failed: {str(e)}")
            return None

        # Generate a unique trace ID for this session
        trace_id = gen_trace_id()
        with trace("Resume Improvement trace", trace_id=trace_id):
            self.printer.update_item(
                "trace_id",
                f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}",
                is_done=True,
                hide_checkmark=True,
            )

            self.printer.update_item(
                "starting",
                "Starting research...",
                is_done=True,
                hide_checkmark=True,
            )
            # Read JD, and parse it to main components
            jd_components = await self._get_jd_components(jd_website)

            # If jd_components is empty, handle it
            if not jd_components:
                self.printer.update_item("getting_jd", "No job description found.")
                return None

            # Get target resume and reference resume
            target_resume_component, reference_resume_component = (
                await self._convert_resume_files(
                    target_resume_file_path, reference_resume_file_path
                )
            )

            revised_resume = target_resume_component
            # At most 3 iterations
            for i in range(self.config.max_iterations):
                score = await self._evaluate_resume(
                    revised_resume, reference_resume_component, jd_components
                )
                if not score:
                    self.printer.update_item(
                        "iteration",
                        f"Iteration {i+1}: Failed to evaluate resume.",
                        is_done=True,
                        hide_checkmark=True,
                    )
                    break
                if (
                    score.content_score >= self.config.content_score_threshold
                    and score.expression_score >= self.config.expression_score_threshold
                ):
                    self.printer.update_item(
                        "iteration",
                        f"Iteration {i+1}: Content Score {score.content_score}, Expression Score {score.expression_score}",
                        is_done=True,
                        hide_checkmark=True,
                    )
                    break
                self.printer.update_item(
                    "iteration",
                    f"Iteration {i+1}: Content Score {score.content_score}, Expression Score {score.expression_score}",
                    is_done=True,
                    hide_checkmark=True,
                )
                if score.content_score < self.config.content_score_threshold:
                    revised_resume = await self._revise_resume_content(
                        revised_resume, jd_components
                    )
                    if not revised_resume:
                        self.printer.update_item(
                            "iteration",
                            f"Iteration {i+1}: Failed to revise resume content.",
                            is_done=True,
                            hide_checkmark=True,
                        )
                        break
                if score.expression_score < 9:
                    revised_resume = await self._revise_resume_expression(
                        revised_resume, reference_resume_component
                    )
                    if not revised_resume:
                        self.printer.update_item(
                            "iteration",
                            f"Iteration {i+1}: Failed to revise resume expression.",
                            is_done=True,
                            hide_checkmark=True,
                        )
                        break

            final_report = f"Final Revised Resume\n\n{revised_resume.model_dump()}"
            self.printer.update_item("final_report", final_report, is_done=True)
            self.printer.end()

        # print("\n\n=====REPORT=====\n\n")
        # print(f"Report: {revised_resume.model_dump()}")

    def _validate_inputs(
        self, target_resume_path: str, jd_website: str, reference_resume_path: str
    ) -> None:
        # Check file existence
        for path in [target_resume_path, reference_resume_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")

        # Validate URL
        parsed = urlparse(jd_website)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {jd_website}")

    async def _convert_resume_files(
        self, target_resume_file_path, reference_resume_file_path
    ):
        self.printer.update_item("converting", "Converting resume files...")
        # Convert both resume to markdown file if they are not
        converted_resume_target_path = self.config.converted_resume_target_path
        converted_resume_reference_path = self.config.converted_resume_reference_path

        outputmessage1 = await file_to_markdown(
            target_resume_file_path, converted_resume_target_path
        )
        self.printer.update_item("converting", outputmessage1)
        outputmessage2 = await file_to_markdown(
            reference_resume_file_path, converted_resume_reference_path
        )
        self.printer.update_item("converting", outputmessage2)

        with open(converted_resume_target_path, "r") as file:
            target_resume_content = file.read()
        with open(converted_resume_reference_path, "r") as file:
            reference_resume_content = file.read()

        # Get target resume components
        target_resume_components = await Runner.run(
            starting_agent=resume_parser_agent,
            input=f"Resume content: {target_resume_content}",
        )
        # Get reference resume components
        reference_resume_components = await Runner.run(
            starting_agent=resume_parser_agent,
            input=f"Resume content: {reference_resume_content}",
        )
        self.printer.mark_item_done("converting")

        # Return both resume components
        return target_resume_components.final_output_as(
            ResumeItem
        ), reference_resume_components.final_output_as(ResumeItem)

    async def _get_jd_components(self, jd_website: str):
        self.printer.update_item("getting_jd", "Analyzing job description...")
        try:
            job_description = web_scraper_tool(jd_website)
        except Exception as e:
            self.printer.update_item("getting_jd", f"Error: {e}")
            # End the agent
            return None

        jd_components = await Runner.run(
            starting_agent=jd_parser_agent,
            input=f"Job description: {job_description}",
        )
        self.printer.mark_item_done("getting_jd")
        return jd_components.final_output_as(JDItem)

    async def _revise_resume_content(
        self, target_resume_components: ResumeItem, jd_components: JDItem
    ) -> ResumeItem:
        self.printer.update_item("revising_resume", "Revising resume content...")
        try:
            revised_resume = await Runner.run(
                starting_agent=content_revise_agent,
                input=json.dumps(
                    {
                        "target_resume_components": target_resume_components.model_dump(),
                        "jd_components": jd_components.model_dump(),
                    }
                ),
            )
            self.printer.mark_item_done("revising_resume")
            return revised_resume.final_output_as(ResumeItem)
        except Exception as e:
            self.printer.update_item("revising_resume", f"Error: {e}")
            traceback.print_exc()
            return None

    async def _evaluate_resume(
        self,
        target_resume_components: ResumeItem,
        reference_resume_components: ResumeItem,
        jd_components: JDItem,
    ) -> EvaluationResult:
        self.printer.update_item("evaluating", "Evaluating resume...")
        result = await Runner.run(
            starting_agent=evaluation_agent,
            input=json.dumps(
                {
                    "target_resume_components": target_resume_components.model_dump(),
                    "reference_resume_components": reference_resume_components.model_dump(),
                    "job_description": jd_components.model_dump(),
                }
            ),
        )
        self.printer.mark_item_done("evaluating")
        return result.final_output_as(EvaluationResult)

    async def _revise_resume_expression(
        self,
        target_resume_components: ResumeItem,
        reference_resume_components: ResumeItem,
    ) -> ResumeItem:
        self.printer.update_item(
            "revising_expression", "Revising resume's expression..."
        )
        try:
            revised_resume = await Runner.run(
                starting_agent=expression_revise_agent,
                input=json.dumps(
                    {
                        "target_resume_components": target_resume_components.model_dump(),
                        "reference_resume_components": reference_resume_components.model_dump(),
                    }
                ),
            )
            self.printer.mark_item_done("revising_expression")
            return revised_resume.final_output_as(ResumeItem)
        except Exception as e:
            self.printer.update_item("revising_expression", f"Error: {e}")
            return None
