# AI Slop Guard

A simple Python checker for finding small issues in AI-generated code.

I built this because AI coding tools are useful, but the first version of the code is not always the best one. Sometimes everything works, but there are small things left behind:

- imports that are never used;
- debug prints;
- unnecessary code;
- exception handling that hides errors.

These things are easy to miss when looking through generated code quickly.

AI Slop Guard does a small static check and shows places that might need attention.

It does not try to be a replacement for normal linters. Tools like Ruff or Pylint already do a great job. This project has a different purpose: checking patterns that appear often when code is written with AI assistance.

## Current rules

The project currently checks:
