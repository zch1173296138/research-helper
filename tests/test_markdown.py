from pathlib import Path

from backend.app.services.markdown import clean_markdown, format_markdown_for_display, rewrite_image_paths, split_markdown


def test_split_markdown_preserves_sections_and_pages() -> None:
    markdown = "# Title\n\n<!-- page:1 -->\n\n## Method\n\n" + ("method text " * 300)
    chunks = split_markdown(markdown, Path("full.md"), target_tokens=120, overlap_tokens=20)
    assert chunks
    assert chunks[0].page_start == 1
    assert any(chunk.section_title == "Method" for chunk in chunks)
    assert any(chunk.section_type == "method" for chunk in chunks)


def test_split_markdown_tracks_structure_and_references() -> None:
    markdown = """# Paper

## Abstract

This paper introduces a system.

## 2. Method

![architecture](fig.png)

Figure 1: System architecture.

The method has three stages.

## References

[1] A reference that should not be searched.
"""
    chunks = split_markdown(markdown, Path("full.md"), target_tokens=300, overlap_tokens=0)

    method = next(chunk for chunk in chunks if chunk.section_type == "method")
    references = next(chunk for chunk in chunks if chunk.section_type == "references")
    assert method.section_path == "Paper > Method"
    assert "Figure 1" in method.text
    assert references.is_reference is True


def test_rewrite_image_paths() -> None:
    markdown = "![fig](images/a.png)"
    rewritten = rewrite_image_paths(markdown, "lib", "paper")
    assert "/api/libraries/lib/papers/paper/assets/images/a.png" in rewritten


def test_rewrite_image_paths_encodes_spaces() -> None:
    markdown = "![fig](images/my figure.png)"
    rewritten = rewrite_image_paths(markdown, "lib", "paper")
    assert "/api/libraries/lib/papers/paper/assets/images/my%20figure.png" in rewritten


def test_clean_markdown_removes_repeated_short_lines() -> None:
    raw = "\n".join(["Journal Header", "Body text"] * 6)
    cleaned = clean_markdown(raw)
    assert cleaned.count("Journal Header") <= 3


def test_clean_markdown_removes_publisher_front_matter_noise() -> None:
    raw = """# TinyOS

## Abstract

Useful abstract text.

*This work is supported, in part, by the Defense Advanced Research Projects Agency.

Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee.

ASPLOS-IX 11/00 Cambridge, MA, USA

Copyright 2000 ACM 0-89791-88-6/97/05 ..$5.00

## 1. Introduction

The actual introduction continues here.
"""
    cleaned = clean_markdown(raw)

    assert "This work is supported" not in cleaned
    assert "Permission to make digital" not in cleaned
    assert "ASPLOS-IX" not in cleaned
    assert "Copyright 2000 ACM" not in cleaned
    assert "The actual introduction continues here." in cleaned


def test_format_markdown_for_display_normalizes_references() -> None:
    markdown = """# Title

# 8. REFERENCES

[20] D. Culler, J. Singh, and A. Gupta. Parallel computer

architecture a hardware/software approach, 1999.
[2] Atmel AVR 8-Bit RISC processor.
[10] RF Monolithics.
"""
    formatted = format_markdown_for_display(markdown)

    assert "# References" in formatted
    assert "- **[2]** Atmel AVR 8-Bit RISC processor." in formatted
    assert "- **[10]** RF Monolithics." in formatted
    assert "- **[20]** D. Culler, J. Singh, and A. Gupta. Parallel computer architecture a hardware/software approach, 1999." in formatted
    assert formatted.index("**[2]**") < formatted.index("**[10]**") < formatted.index("**[20]**")
