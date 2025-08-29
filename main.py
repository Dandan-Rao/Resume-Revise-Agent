#!/usr/bin/env python3
import asyncio

from manager import ResumeImprovementManager, Config

custom_config = Config(
    max_iterations=3, expression_score_threshold=8, content_score_threshold=8
)


async def main() -> None:
    await ResumeImprovementManager(custom_config).run(
        "./target_resume.docx",
        "https://jobright.ai/jobs/info/689181264c7e851b90acf534",
        "./converted_resume/reference_resume.md",
    )


if __name__ == "__main__":
    asyncio.run(main())
