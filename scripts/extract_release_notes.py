"""Extracts release notes for a specific version from a CHANGELOG.md file."""

import re
import sys
from typing import Optional


def get_version_section(content: str, version_number: str) -> Optional[str]:
    """
    Find and return the content for a specific version section in the changelog.

    Args:
        content: The full content of the changelog file.
        version_number: The version string to look for (e.g., "1.0.2").

    Returns:
        The content of the version section if found, otherwise None.
    """
    # Regex to find the start of the version section: "## [version]"
    # It captures everything until the next "## [" (start of another version)
    # or the end of the string (\Z).
    escaped_version_number = re.escape(version_number)
    pattern = re.compile(
        r"##\s*\[" + escaped_version_number + r"\][^\n]*\n(.*?)(?=\n##\s*\[|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return None


def main(version_number: str, changelog_filepath: str, output_filepath: str) -> None:
    """
    Read a changelog, extract notes for a version, and write them to an output file.

    Args:
        version_number: The version to extract notes for.
        changelog_filepath: Path to the CHANGELOG.md file.
        output_filepath: Path where the extracted notes will be written.
    """
    try:
        with open(changelog_filepath, "r", encoding="utf-8") as f_changelog:
            changelog_content = f_changelog.read()
    except FileNotFoundError:
        print(f"Error: Changelog file not found at '{changelog_filepath}'.")
        sys.exit(1)

    extracted_notes = get_version_section(changelog_content, version_number)

    if extracted_notes:
        try:
            with open(output_filepath, "w", encoding="utf-8") as f_output:
                f_output.write(extracted_notes)
            print(f"Successfully extracted release notes for version {version_number}.")
        except IOError as e:
            print(f"Error writing extracted notes to '{output_filepath}': {e}")
            sys.exit(1)
    else:
        print(f"Warning: Version section for '{version_number}' not found.")
        try:
            with open(output_filepath, "w", encoding="utf-8") as f_output:
                f_output.write(
                    f"Release notes for version {version_number} not found in {changelog_filepath}."
                )
        except IOError as e:
            print(f"Error writing placeholder message to '{output_filepath}': {e}")
        # We exit with an error because a release should not be created
        # without proper release notes.
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python extract_release_notes.py <version_without_v> "
            "<changelog_path> <output_path>"
        )
        print(
            "Example: python scripts/extract_release_notes.py 1.0.2 "
            "CHANGELOG.md RELEASE_NOTES.md"
        )
        sys.exit(1)

    script_version = sys.argv[1]
    script_changelog = sys.argv[2]
    script_output = sys.argv[3]

    main(script_version, script_changelog, script_output)
