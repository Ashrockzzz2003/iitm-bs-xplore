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
        ),
        EvaluationCase(
            id="foundation_level_3_terms_plan",
            question=(
                "I aim to complete the Foundation Level of the IITM BS Data Science programme within three terms. "
                "How many courses should I take each term to achieve this?"
            ),
            ground_truth=(
                "The Foundation Level comprises 8 courses (32 credits) and must be completed before moving to the Diploma Level. "
                "Since each term allows registration of up to 4 courses, a three-term plan would typically involve taking 3 courses in Term 1, 3 in Term 2, and 2 in Term 3 (or 3-3-2) to finish all 8 within three terms."
            ),
            contexts=[
                "Foundation Level: 32 credits | 8 courses.",
                "Every year is divided into three terms of four months each – January, May and September.",
                "In each term, a learner may register for up to 4 courses depending on their CCC (Credit Clearing Capability).",
                "Level Progression Requirements: Foundation Level: All 8 courses must be successfully completed before enrolling in any Diploma Level course."
            ],
            reference_answer=(
                "To finish the 8-course foundation level in three terms, you could schedule it as follows: Term 1 – take 3 courses, Term 2 – take 3 courses, Term 3 – take the remaining 2 courses. "
                "This is within the maximum of 4 per term and ensures you complete all 8 by the end of the third term, enabling you to proceed to the Diploma Level."
            ),
            metadata={
                "source": "IITM DS Academics page",
                "program": "data_science",
                "level": "foundation",
                "planning_horizon": "3 terms"
            }
        ),
        EvaluationCase(
            id="ds_foundation_to_diploma_promotion_criteria",
            question=(
                "What is the minimum CGPA required to move from the Foundation Level to the Diploma Level in the IITM BS Data Science and Applications program?"
            ),
            ground_truth=(
                "There is no minimum CGPA requirement to move from the Foundation to the Diploma level. "
                "Learners simply need to pass all eight Foundation courses individually, "
                "with at least 40 marks in each course, before registering for Diploma Level courses."
            ),
            contexts=[
                "Promotion criteria: Learners must complete and pass all Foundation Level courses to progress to the Diploma Level.",
                "Each Foundation course requires a minimum score of 40 marks to be considered passed.",
                "No cumulative grade or CGPA threshold is specified for level progression in the IITM BS Data Science program."
            ],
            reference_answer=(
                "You don’t need any minimum CGPA to move to the Diploma Level. "
                "You just need to pass all Foundation courses individually with at least 40 marks in each."
            ),
            metadata={
                "source": "IITM BS Academics page",
                "program": "data_science",
                "level": "foundation",
                "policy_type": "progression_criteria"
            }
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
        ),
        EvaluationCase(
            id="diploma_dual_enrollment_policy",
            question=(
                "Can I start pursuing a second diploma while I am still completing the first one in the IITM BS Data Science program?"
            ),
            ground_truth=(
                "Yes. Learners who have completed the Foundation Level can register for courses from both the Diploma in Programming "
                "and Diploma in Data Science simultaneously. They may complete the two diplomas in parallel or sequentially. "
                "After completing both, they become eligible to proceed to the BSc Degree Level."
            ),
            contexts=[
                "Diploma Level: There are two sections – Diploma in Programming and Diploma in Data Science. "
                "Each comprises 5 core courses, 2 projects, and 1 skill enhancement course.",
                "Learners who complete all courses and projects in both diplomas can proceed to the BSc Degree Level.",
                "It is possible for learners to exit with one or both diplomas after completing the required credits."
            ],
            reference_answer=(
                "Yes, you can pursue both diplomas together after finishing the Foundation Level. "
                "You may choose to take courses from the second diploma while finishing the first, and once both are complete, "
                "you’ll be eligible to move to the BSc Degree Level."
            ),
            metadata={
                "source": "IITM BS Academics page",
                "program": "data_science",
                "level": "diploma",
                "policy_type": "dual_diploma_enrollment"
            }
        ),
        EvaluationCase(
            id="ds_diploma_coding_project_courses",
            question=(
                "Which Data Science Diploma-level courses include substantial coding assignments or project work in the IITM BS Data Science & Applications programme?"
            ),
            ground_truth=(
                "On the Diploma in Data Science pathway (27 credits: 6 courses + 2 projects) the following courses include substantial coding-assignments or project work: ‚“Machine Learning Practice” (4 credits) includes a dedicated project course “Machine Learning Practice – Project” (2 credits). Also, in the optional track you can choose “Introduction to Deep Learning and Generative AI” (4 credits) followed by its project “Deep Learning and Generative AI – Project” (2 credits). „“Tools in Data Science” (3 credits) includes take-home project style work (2 take-home projects) alongside online assignments. Thus, these courses incorporate hands-on coding and project work."
            ),
            contexts=[
                "Diploma in Data Science: 6 courses + 2 project courses for 27 credits (1-2 years) in IITM BS Data Science & Applications programme. :contentReference[oaicite:1]{index=1}",
                "Course page for “Tools in Data Science” (BSSE2002) states: ‘… online assignments for each module, … 2 take home projects’ in addition to in-person end-term exam. :contentReference[oaicite:2]{index=2}",
                "Programme page shows for Diploma in Data Science: “Machine Learning Practice – Project” (2 credits) listed as part of the track. :contentReference[oaicite:3]{index=3}"
            ],
            reference_answer=(
                "The Diploma in Data Science has built-in hands-on courses and project work. Specifically: • “Tools in Data Science” (BSSE2002) includes two take-home projects and coding assignments. • “Machine Learning Practice” has a dedicated project component “Machine Learning Practice – Project”. • In the optional track you may pick “Introduction to Deep Learning & Generative AI” followed by its project. So yes — several courses in the diploma level actively include substantial coding and project-based assignments."
            ),
            metadata={
                "source": "IITM BS Data Science Academics page",
                "program": "data_science",
                "level": "diploma",
                "policy_type": "coding_project_courses"
            }
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
        ),
        EvaluationCase(
            id="degree_elective_with_core_parallel",
            question=(
                "Can I register for elective courses before completing all the core courses at the Degree Level of the IITM BS Data Science program?"
            ),
            ground_truth=(
                "Yes. Once a learner becomes eligible for the Degree Level after completing both diplomas, "
                "they can register for core and elective courses in any order, depending on term offerings and prerequisites. "
                "It is not mandatory to finish all core courses before taking electives."
            ),
            contexts=[
                "Degree Level: Learners who have completed both diplomas become eligible for the BSc Degree Level.",
                "At the Degree Level, students can take a mix of core and elective courses as long as prerequisites are met.",
                "The Degree Level curriculum includes core courses, elective courses, and a project, which may be taken in flexible order based on course availability."
            ],
            reference_answer=(
                "No, it’s not required to complete all core courses before starting electives. "
                "Once you reach the Degree Level, you may take core and elective courses in parallel, "
                "depending on what is offered that term and any prerequisite requirements."
            ),
            metadata={
                "source": "IITM BS Academics page",
                "program": "data_science",
                "level": "degree",
                "policy_type": "core_and_elective_registration"
            }
        ),
        EvaluationCase(
            id="ds_degree_industry4_eligibility_missing_first_assignment",
            question=(
                "I have taken the Industry 4.0 course in the current term but failed to submit the first assignment. "
                "Is it still possible to continue the course and pass it?"
            ),
            ground_truth=(
                "Yes, it is still possible to continue and pass the course. "
                "To be eligible for the final exam in Industry 4.0, a learner must submit at least one of the first three assignments "
                "(Assignments 1–3), attend at least one of the two quizzes, and also participate in the game or submit the project. "
                "Failing to submit only the first assignment does not make you ineligible, "
                "as long as you submit either Assignment 2 or 3 and meet the other requirements. "
                "Additionally, you must attend the end-term exam to receive a final course grade."
            ),
            contexts=[
                "Industry 4.0 – Grading Policy: Eligibility for final exam requires submission of at least one of the first three assignments "
                "(Asgn 1, Asgn 2, Asgn 3), attendance in at least one of the two quizzes, and participation in either the game or project submission.",
                "Eligibility for final course grade: attending the end-term exam.",
                "Therefore, missing Assignment 1 alone does not disqualify a learner, "
                "as long as Assignment 2 or 3 is submitted and other conditions are fulfilled."
            ],
            reference_answer=(
                "Yes. Missing the first assignment alone doesn’t make you ineligible. "
                "You can still continue and pass the course if you submit either Assignment 2 or 3, "
                "attend at least one quiz, and complete either the game or project. "
                "You must also attend the end-term exam to receive a final grade."
            ),
            metadata={
                "source": "Industry 4.0 course grading policy, IITM BS Data Science degree level",
                "program": "data_science",
                "level": "degree",
                "course": "Industry 4.0",
                "policy_type": "eligibility_and_passing_criteria"
            }
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
        ),
        EvaluationCase(
            id="es_foundation_EE1101_topics",
            question=(
                "What are the main topics covered in the EE1101 in the IITM BS Electronic Systems programme?"
            ),
            ground_truth=(
                "The course EE1101 covers fundamental ideas of electronic systems thinking and basic circuits. Key topics include: circuit elements (resistors, capacitors, inductors), Kirchhoff’s laws, simple circuit analysis; understanding how electronic systems are built, thinking about signals and systems, basic analog behaviour, introduction to digital vs analog circuits; how circuits implement system functionalities; and how these fit into larger electronic systems context."
            ),
            contexts=[
                "Foundation level of BS in Electronic Systems: course list includes “Electronic Systems Thinking and Circuits” (code EE1101) among theory courses.",
                "The programme emphasises electronics, embedded programming, digital systems, and control engineering."
            ],
            reference_answer=(
                "In EE1101 you learn how to think of electronic systems as a whole and how basic circuits build up those systems. You’ll study the behaviour of passive and active circuit components (resistors, capacitors, inductors), apply circuit laws like KCL and KVL, analyse simple analog circuits, understand differences between analog/digital signals, and see how circuits form the building blocks of electronics systems. This gives you a systems-level view as well as solid grounding in circuit fundamentals."
            ),
            metadata={
                "source": "IITM BS Electronic Systems Academics page",
                "program": "electronic_systems",
                "level": "foundation",
                "course_code": "EE1101"
            }
        ),
        EvaluationCase(
            id="es_foundation_coreq_electronic_systems_thinking_lab",
            question=(
                "Do I need to complete the Electronic Systems Thinking and Circuits theory course before registering for the Electronic Systems Thinking and Circuits Lab in the IITM BS Electronic Systems program?"
            ),
            ground_truth=(
                "No, you don’t need to complete the theory course beforehand. "
                "The Electronic Systems Thinking and Circuits Lab is a corequisite to the theory course, "
                "which means it can be taken in the same term or in a later term, but not before the theory course."
            ),
            contexts=[
                "According to the IITM BS Electronic Systems Foundation Level curriculum, "
                "‘Electronic Systems Thinking and Circuits (EE1101)’ and "
                "‘Electronic Systems Thinking and Circuits Lab (EE1102)’ are listed as corequisites.",
                "Corequisite means that both courses can be taken together in the same term or the lab can be taken after the theory course, "
                "but the lab cannot be taken before completing or registering for the theory course."
            ],
            reference_answer=(
                "You don’t need to finish the theory course first. "
                "The lab is a corequisite, so you can take it in the same term or later, "
                "but not before the theory course."
            ),
            metadata={
                "source": "IITM BS Electronic Systems Academics page",
                "program": "electronic_systems",
                "level": "foundation",
                "policy_type": "course_corequisite"
            }
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
        ),
        EvaluationCase(
            id="es_diploma_project_courses",
            question=(
                "Are there project-based courses in the Diploma level of the IITM BS Electronic Systems programme?"
            ),
            ground_truth=(
                "Yes. At the Diploma level of the BS in Electronic Systems, there are two dedicated project courses (each of 2 credits) alongside theory and laboratory courses."
            ),
            contexts=[
                "Diploma Level: 43 credits | 8 Theory + 3 Labs + 2 Project courses.",
                "Courses listed for Diploma level include: “Electronics System Project (2 credits, EE3999)” and “Signals and Systems Project (2 credits, EE4999)”."
            ],
            reference_answer=(
                "Yes — the Diploma level includes 2 project-based courses (2 credits each) in addition to theory and lab courses, giving you hands-on experience before you progress to the Degree level."
            ),
            metadata={
                "source": "IIT Madras BS Electronic Systems Academics page",
                "program": "electronic_systems",
                "level": "diploma",
                "policy_type": "project_course_availability"
            }
        ),
        EvaluationCase(
            id="es_diploma_best_order_courses",
            question=(
                "What is the best order to take the Diploma-Level courses in the BS in Electronic Systems programme for a smooth progression?"
            ),
            ground_truth=(
                "For the Diploma level (8 theory + 3 labs + 2 projects, 43 credits) in the ES programme, a smooth order is to start with courses that have minimal prerequisites (e.g., “Electronic Testing and Measurement” EE4108, “Computer Organisation” EE4104), then take foundational signal/analog courses (“Signals and Systems” EE2101, “Analog Electronic Systems” EE2102) along with their labs, then move to design/lab integration courses (“Digital System Design” EE2103 and lab EE2902), then take advanced courses (“Digital Signal Processing” EE3101, “Sensors and Applications” EE3103 and its lab EE3901), and only after those, undertake the two project courses (“Electronics System Project” EE3999, “Signals and Systems Project” EE4999). This leverages the prerequisites listed (e.g., EE2102 requires EE2101; DSP requires EE2101) and helps build skills gradually."
            ),
            contexts=[
                "Diploma Level: 8 Theory + 3 Laboratories + 2 Project courses, 43 credits.",
                "Course list with prerequisites in ES Diploma: e.g., “Signals and Systems” EE2101 has prerequisite EE1103 (Elect. & Electronic Circuits) from Foundation; “Analog Electronic Systems” EE2102 has prereq EE2101.",
                "“Digital System Design” EE2103 has prerequisite EE1102 (Digital Systems) from Foundation."
            ],
            reference_answer=(
                "A suggested smooth order is: 1) EE4108 (Electronic Testing & Measurement) and EE4104 (Computer Organisation) first, 2) EE2101 (Signals & Systems) → EE2102 (Analog Electronic Systems) + analog lab, 3) EE2103 (Digital System Design) + digital lab, 4) EE3101 (Digital Signal Processing) & EE3103 (Sensors & Applications) + sensors lab, and finally tackling the two project courses EE3999 & EE4999. This order respects prerequisites and builds up to the projects."
            ),
            metadata={
                "source": "IITM BS Electronic Systems Academics page",
                "program": "electronic_systems",
                "level": "diploma",
                "policy_type": "course_ordering_guidance"
            }
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
        ),
        EvaluationCase(
            id="es_degree_remaining_courses_after_core",
            question=(
                "After completing all core courses at the Degree Level of the BS in Electronic Systems programme, how many more courses do I need to take to complete the degree?"
            ),
            ground_truth=(
                "At the Degree Level of the BS in Electronic Systems programme, there are 12 courses plus an optional apprenticeship. A total of 56 credits are required for this level."
            ),
            contexts=[
                "Degree Level (Electronic Systems): “BS Degree Level … 12 courses + Apprenticeship (Optional)”",
                "The BS in Electronic Systems has the following credit structure: Foundation Level ~44 credits; Diploma Level ~42 credits; Degree Level ~56 credits (12 courses)",
                "Completion of 142 total credits across all levels (Foundation + Diploma + Degree) is required for the BS degree."
            ],
            reference_answer=(
                "Once you have completed the core courses at the Degree Level, you still need to complete a total of 12 courses (for the Degree Level) which together yield ~56 credits, plus any required electives or optional apprenticeship as per the programme. Thus, you’re essentially completing all those 12 courses for the Degree Level to earn your BS degree."
            ),
            metadata={
                "source": "IIT Madras BS Electronic Systems – Academics / FAQ",
                "program": "electronic_systems",
                "level": "degree",
                "policy_type": "degree_course_count"
            }
        ),
        EvaluationCase(
            id="es_degree_embedded_systems_career_courses",
            question=(
                "Which degree-level courses in the BS in Electronic Systems programme at IIT M are best suited for building a career in embedded systems development?"
            ),
            ground_truth=(
                "Key degree level courses well-suited for embedded systems development include: • “Embedded Linux and FPGAs” (EE4101) + its lab (EE4901) – builds hands-on with embedded platforms and FPGA systems. “Electronic Product Design” (EE4102) – covers design of electronics systems and productisation. Department elective “Internet of Things (IoT)” (EE5101) – directly aligned with embedded & connected systems. Department elective “Digital IC Design” (EE5102) – for hardware/firmware interplay in embedded systems. Department elective “Power Management for Electronic Systems” (EE5103) – relevant for low-power embedded device design. These courses combined give strong foundations in hardware-software co-design, embedded platforms, system integration and product development – ideal for a career in embedded systems."
            ),
            contexts=[
                "Degree Level (Electronic Systems): Core Courses include Embedded Linux and FPGAs (EE4101) + Lab (EE4901), Electronic Product Design (EE4102), Electromagnetic Fields and Transmission Lines (EE3104), Control Engineering (EE3102).",
                "Department Electives at degree level: Internet of Things (IoT) EE5101, Digital IC Design EE5102, Power Management for Electronic Systems EE5103, Biomedical Electronic Systems EE5104, etc.",
                "Programme focus: ‘The emphasis is on electronics, embedded programming, digital systems, and control engineering’."
            ],
            reference_answer=(
                "For a strong path into embedded systems development, focus on the degree-level courses such as Embedded Linux and FPGAs + lab, Electronic Product Design, and electives like IoT, Digital IC Design, or Power Management. These build essential skills in hardware-software integration, device architecture, productisation and low-power embedded design."
            ),
            metadata={
                "source": "IITM BS Electronic Systems Academics page",
                "program": "electronic_systems",
                "level": "degree",
                "policy_type": "career_course_alignment"
            }
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
