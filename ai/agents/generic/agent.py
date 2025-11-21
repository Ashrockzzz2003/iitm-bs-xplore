"""Expose the IITM BS Policies & Handbook agent at the generic/ root."""

from .policies.agent import root_agent as policy_root_agent

# Alias so ADK can discover root_agent directly under generic/
root_agent = policy_root_agent

