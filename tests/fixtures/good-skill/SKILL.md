---
name: good-skill
description: Extracts tables from PDF files and saves them as CSV. Use when the user asks to pull tables, convert PDF tables, or export tabular data from a document.
license: MIT
metadata:
  author: test
  version: "1.0.0"
  status: active
  last_reviewed: "2026-10-01"
---

# Good Skill

## When to use

Use when the user has a PDF with tables and wants structured data.

## Steps

1. Read the PDF.
2. Detect tables.
3. Write a CSV.
4. Verify the row count.

## Output

A CSV file and a short note about skipped pages.
