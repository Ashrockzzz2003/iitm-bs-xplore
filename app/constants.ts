import { Developer } from './types';

export const API_URL = "https://iitm-bs-xplore-296465730011.europe-west1.run.app";
export const AGENT_APP_NAME = "iitm_advisor_agent";
export const APP_NAME = "IITM BS Xplore";
export const APP_VERSION = "v2.0.0";
export const MODEL_NAME = "gemini-3-pro-preview";

export const DEVELOPERS: Developer[] = [
  {
    name: "Ashwin Narayanan S",
    rollNumber: "21f3001600",
    email: "21f3001600@ds.study.iitm.ac.in"
  },
  {
    name: "Hritik Gupta",
    rollNumber: "21f1000564",
    email: "21f1000564@ds.study.iitm.ac.in"
  },
  {
    name: "Chauhan Parth Ramesh",
    rollNumber: "21f2000991",
    email: "21f2000991@ds.study.iitm.ac.in"
  }
];

export const SUGGESTIONS = [
  "What are the eligibility criteria for the qualifier exam?",
  "How is GPA calculated?",
  "List all Foundation Level courses with 4 credits",
  "What is the grading scale?",
  "Show me the syllabus for BSMA1001",
  "Give me a complete overview of the IITM BS program",
];