"""Shared evaluation scenarios for IITM BS/ES agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class EvaluationCase:
    """Single evaluation example for an agent."""

    id: str
    question: str
    ground_truth: str
    contexts: Sequence[str]
    reference_answer: str
    metadata: Dict[str, str] = field(default_factory=dict)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# Question + context fixtures per agent. These serve as deterministic prompts
# for evaluation runs and double as regression data for the first recorded run.
EVALUATION_DATA: Dict[str, List[EvaluationCase]] = {
    "ds_foundation": [
        EvaluationCase(
            id="ds_foundation_credit_timeline",
            question=(
                "What workload and timeline should learners expect at the "
                "foundation level of the IITM BS Data Science program?"
            ),
            ground_truth=(
                "The foundation level spans eight courses worth 32 credits, "
                "and most learners take between one and three years to finish "
                "it depending on pace."
            ),
            contexts=[
                (
                    "Foundation Level: 32 credits | 8 courses. The curriculum "
                    "covers computational thinking, Python programming, "
                    "English, mathematics, and statistics fundamentals."
                ),
                (
                    "Expected engagement is roughly 10 hours per course each "
                    "week, and the institute notes that learners usually take "
                    "between one and three years to complete the foundation "
                    "stage before moving on."
                ),
            ],
            reference_answer=(
                "It is an eight-course block totalling 32 credits. Learners "
                "typically commit about 10 hours per course each week and "
                "finish the foundation stage in roughly one to three years."
            ),
            metadata={
                "source": "IITM Academics page (scraped sample)",
                "program": "data_science",
                "level": "foundation",
            },
        )
    ],
    "ds_diploma": [
        EvaluationCase(
            id="ds_diploma_tracks",
            question=(
                "Describe the credit structure of the diploma level in the "
                "IITM BS Data Science program."
            ),
            ground_truth=(
                "The diploma level is offered in two tracks-Programming and "
                "Data Science-and each track comprises 27 credits made up of "
                "six courses plus two project courses."
            ),
            contexts=[
                (
                    "Diploma Level: Programming track totals 27 credits split "
                    "across six courses and two project components."
                ),
                (
                    "Diploma Level: Data Science track mirrors the Programming "
                    "track with 27 credits that include six advanced courses "
                    "and two projects to deepen applied analytics."
                ),
            ],
            reference_answer=(
                "Both diploma pathways run 27 credits. Each includes six "
                "courses and a pair of project modules, whether you choose the "
                "Programming or the Data Science track."
            ),
            metadata={
                "source": "IITM Academics page (scraped sample)",
                "program": "data_science",
                "level": "diploma",
            },
        )
    ],
    "ds_degree": [
        EvaluationCase(
            id="ds_degree_credit_totals",
            question=(
                "How many credits are required to complete the BSc and BS "
                "degree levels in the IITM BS Data Science program?"
            ),
            ground_truth=(
                "Both the BSc and the BS degree levels require 28 credits "
                "each, lifting the running total to 114 credits for the BSc "
                "and 142 credits for the full BS degree."
            ),
            contexts=[
                (
                    "BSc Degree Level: 28 credits. BS Degree Level: 28 credits. "
                    "Learners build advanced electives and capstone work at "
                    "this stage."
                ),
                (
                    "Total credits to be earned: BSc Degree 114 credits. BS "
                    "Degree 142 credits. Completing the BS track adds advanced "
                    "specialisations on top of the BSc milestone."
                ),
            ],
            reference_answer=(
                "The institute keeps both degree stages at 28 credits. "
                "Crossing the BSc milestone brings you to 114 credits overall, "
                "and completing the BS capstone lifts the total to 142 credits."
            ),
            metadata={
                "source": "IITM Academics page (scraped sample)",
                "program": "data_science",
                "level": "degree",
            },
        )
    ],
    "es_foundation": [
        EvaluationCase(
            id="es_foundation_focus",
            question=(
                "Which skill areas are emphasised at the foundation level of "
                "the IITM BS Electronic Systems program?"
            ),
            ground_truth=(
                "Learners cement fundamentals in circuit theory, digital "
                "systems, signals, and embedded programming while gaining "
                "confidence through hardware lab practice."
            ),
            contexts=[
                (
                    "The Electronic Systems foundation level revisits physics "
                    "and mathematics essentials while introducing circuit "
                    "theory, digital systems, and embedded programming."
                ),
                (
                    "Hands-on hardware labs run alongside lectures so learners "
                    "practice prototyping, measurement, and debugging early in "
                    "the program."
                ),
            ],
            reference_answer=(
                "It is all about electronic fundamentals-analog circuits, "
                "digital design, signals, and embedded coding-anchored by "
                "weekly labs that build hardware confidence."
            ),
            metadata={
                "source": "Program overview notes (to be replaced with live data)",
                "program": "electronic_systems",
                "level": "foundation",
            },
        )
    ],
    "es_diploma": [
        EvaluationCase(
            id="es_diploma_specialisations",
            question=(
                "What structure does the diploma level follow in the IITM BS "
                "Electronic Systems program?"
            ),
            ground_truth=(
                "The diploma stage deepens hardware design with focus areas "
                "such as embedded systems, signal processing, and control, "
                "delivered through six build courses and two design projects."
            ),
            contexts=[
                (
                    "During the diploma stage learners pick focus areas like "
                    "embedded systems, signal processing, or control while "
                    "reinforcing hardware design skills."
                ),
                (
                    "The curriculum blends six core build courses with two "
                    "design projects that stress board-level implementation "
                    "and firmware integration."
                ),
            ],
            reference_answer=(
                "It deepens hardware work: six advanced build courses lead "
                "into two design projects, and the focus areas span embedded, "
                "signal processing, and control oriented topics."
            ),
            metadata={
                "source": "Program overview notes (to be replaced with live data)",
                "program": "electronic_systems",
                "level": "diploma",
            },
        )
    ],
    "es_degree": [
        EvaluationCase(
            id="es_degree_capstone",
            question=(
                "What themes define the degree level of the IITM BS Electronic "
                "Systems program?"
            ),
            ground_truth=(
                "The degree level concentrates on system integration, advanced "
                "electronics manufacturing, and industry-guided capstone work "
                "across areas like robotics, IoT, VLSI, and power electronics."
            ),
            contexts=[
                (
                    "The Electronic Systems degree level emphasises system "
                    "integration and advanced electronics manufacturing topics."
                ),
                (
                    "Learners tackle industry-partnered capstone projects in "
                    "domains such as robotics, IoT, VLSI, and power electronics "
                    "to deliver production-grade platforms."
                ),
            ],
            reference_answer=(
                "System integration dominates the final stage-think advanced "
                "manufacturing plus capstone collaborations in robotics, IoT, "
                "VLSI, and power electronics."
            ),
            metadata={
                "source": "Program overview notes (to be replaced with live data)",
                "program": "electronic_systems",
                "level": "degree",
            },
        )
    ],
}


AGENT_REGISTRY: Dict[str, Dict[str, object]] = {
    "ds_foundation": {
        "label": "Data Science - Foundation",
        "program": "ds",
        "level": "foundation",
        "module_path": PROJECT_ROOT / "agents" / "ds" / "foundation" / "agent.py",
        "agent_attr": "root_agent",
        "runner_app_name": "agents",
    },
    "ds_diploma": {
        "label": "Data Science - Diploma",
        "program": "ds",
        "level": "diploma",
        "module_path": PROJECT_ROOT / "agents" / "ds" / "diploma" / "agent.py",
        "agent_attr": "root_agent",
        "runner_app_name": "agents",
    },
    "ds_degree": {
        "label": "Data Science - Degree",
        "program": "ds",
        "level": "degree",
        "module_path": PROJECT_ROOT / "agents" / "ds" / "degree" / "agent.py",
        "agent_attr": "root_agent",
        "runner_app_name": "agents",
    },
    "es_foundation": {
        "label": "Electronic Systems - Foundation",
        "program": "es",
        "level": "foundation",
        "module_path": PROJECT_ROOT / "agents" / "es" / "foundation" / "agent.py",
        "agent_attr": "root_agent",
        "runner_app_name": "agents",
    },
    "es_diploma": {
        "label": "Electronic Systems - Diploma",
        "program": "es",
        "level": "diploma",
        "module_path": PROJECT_ROOT / "agents" / "es" / "diploma" / "agent.py",
        "agent_attr": "root_agent",
        "runner_app_name": "agents",
    },
    "es_degree": {
        "label": "Electronic Systems - Degree",
        "program": "es",
        "level": "degree",
        "module_path": PROJECT_ROOT / "agents" / "es" / "degree" / "agent.py",
        "agent_attr": "root_agent",
        "runner_app_name": "agents",
    },
}


def list_agents() -> Sequence[str]:
    """Return agent keys that have evaluation coverage."""

    return tuple(EVALUATION_DATA.keys())
