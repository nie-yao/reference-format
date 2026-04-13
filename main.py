#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 27 19:15:23 2025

@author: ynie
"""

import os
import sys
import glob
import argparse
import re
import bibtexparser
from titlecase import titlecase



TERM = {'Kalman', 'Markov', 'Bayesian', 'Gaussian'}
ABBR = {'UAV', 'GPS', 'VB', 'PMU', 'UWB', 'IMU', 'SOC', 'IMM', 'CPS', 'DoS'}
UPPER_WORDS = set.union(TERM, ABBR)
ORG_NAMES = {"IEEE", "ACM", "CAA", "MIT"}

BRACE_PATTERN = re.compile(r'\{.*?\}')
MATH_PATTERN = re.compile(r'\$(?:[^$]|\{[^{}]+\})+\$')
ACRONYM_PATTERN = re.compile(r'[A-Z]{2,}')

SPECIAL_MATH_MAP = {
    r'H∞': r'$H_\infty$',
    r'H1': r'$H_1$',
    r'H2': r'$H_2$',
    r'$ H\_$\backslash$infty $': r'$H_\infty$',
    r'$H\_$\backslash$infty$': r'$H_\infty$',
}

def extract_main_text(file_path):
    """
    Extract the main text content from a file.

    Args:
        file_path (str): Path to the input file.
    """
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content
    
    except FileNotFoundError:
        print(f"Error: File not found in {file_path}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def extract_references(file_path):
    """
    Extract all bibliography entries from a file.

    Args:
        file_path (str): Path to the input file.

    Returns:
        list of str: A list of extracted reference entries as strings.
    """
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            bib_database = bibtexparser.load(f)

        return bib_database.entries
    
    except FileNotFoundError:
        print(f"Error: File not found in {file_path}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def format_authors(authors):
    """
    Format a BibTeX-style author string into abbreviated names.

    Converts "LastName, FirstName" entries into initials + last name (e.g., "John Smith" -> "J.~Smith") 
    and joins multiple authors using standard formatting rules.

    Args:
        authors (str): Author string separated by 'and'.

    Returns:
        str: Formatted author string.

    Raises:
        ValueError: If the input is empty, without <,>, or contains <others>.
    """
    if not authors or not authors.strip():
        raise ValueError(f"Author list is empty")
    
    # Step 1: Split the input string into individual authors using 'and'
    authors = [a.strip() for a in authors.split(' and ')]
    
    formatted_authors = []
    for author in authors:
        # Handle the special 'others' keyword
        if author == 'others':
            raise ValueError(f"The 'others' keyword is currently not supported")  # 'et al.'?
            
        # Split the author's name by ',' to separate last name and first name(s)
        # Expected format from BibTeX: "LastName, FirstName"
        parts = [p.strip() for p in author.split(',')]
        if len(parts) != 2:
            raise ValueError(f"Invalid author format: '{author}', Expected 'LastName, FirstName>'")
        
        # Format the last name: Capitalize the first letter, lowercase the rest
        last_name = parts[0].capitalize()
        
        # Format the first name(s): Abbreviate
        first_names = parts[1].replace('-', ' ').split()  # Replace hyphens, and split
        first_names = [f"{name[0].upper()}." for name in first_names]  # Convert each first/middle name to its initial

        # Combine initials and last name with a non-breaking space (~)
        # Example output: T.~Ba\c{s}ar
        formatted_name = '~'.join(first_names + [last_name])
        formatted_authors.append(formatted_name)
    
    # Step 3: Merge all formatted authors into a single final string    
    if len(formatted_authors) == 1:  # For 1 author, use "A"
        return formatted_authors[0], authors
    elif len(formatted_authors) == 2:  # For 2 authors, use "A and B"
        return f"{formatted_authors[0]} and {formatted_authors[1]}", authors
    else:  # For 3 or more authors, use "A, B, and C" (Oxford comma format)
        return ', '.join(formatted_authors[:-1]) + ', and ' + formatted_authors[-1], authors
        
    
def format_title(title):
    """
    Format a title string into sentence case with special handling.

    Preserves brace-protected text, LaTeX math expressions,
    predefined acronyms and proper nouns, while converting other words to sentence case.

    Args:
        title (str): Input title string.

    Returns:
        str: Formatted title string.
    """

    # Replace special symbols globally before tokenization, e.g., H∞ -> $H_\\infty$
    for bad_str, good_str in SPECIAL_MATH_MAP.items():
        title = title.replace(bad_str, good_str)

    words = title.split()
    formatted_words = []
    
    for i, word in enumerate(words):
        # Rule 1: Handle brace protection {...}
        # If a word contains braces, remove them and preserve the original casing
        if BRACE_PATTERN.search(word):
            clean_word = re.sub(r'[{}]', '', word)
            formatted_words.append(clean_word)
            continue

        # Rule 2: Protect LaTeX math formulas (e.g., $H_2$)
        if MATH_PATTERN.search(word):
            formatted_words.append(word)
            continue
        
        # Rule 3: Protect domain-specific acronyms and proper nouns (e.g., UAV, Kalman)
        if any(substring in word for substring in UPPER_WORDS):
            formatted_words.append(word)
            continue
        
        # Rule 3.5: Auto-protect acronyms (e.g., ECO-DKF, LSTM)
        if ACRONYM_PATTERN.search(word):
            formatted_words.append(word)
            print(f"  [Title Acronym] Preserving: {word}")
            continue

        # Rule 4: Apply Sentence Case formatting
        # Capitalize the first word, OR the word immediately following a colon/punctuation
        if i == 0 or (i > 0 and words[i-1].endswith((':', '?', '!'))):
            formatted_words.append(word.capitalize())
        else:
            formatted_words.append(word.lower())
    
    return ' '.join(formatted_words)

    
def format_journal(journal_name):
    def custom_callback(word, **kwargs):
        # Rule 1: Handle Organization Names (e.g., IEEE, ACM)
        if any(org in word.upper() for org in ORG_NAMES):
            return word.upper()
        
        # Rule 2: Handle arXiv (e.g., arXiv:2101.12345)
        if 'arxiv' in word.lower():
            return re.sub(r"arxiv", "arXiv", word, flags=re.IGNORECASE)
        
        # Rule 3: Handle specific technical abbreviations (Optional)
        # If the word is already all caps and long, keep it (e.g., SCADA)
        if ACRONYM_PATTERN.search(word):
            print(f"  [Journal Acronym] Preserving: {word}")
            return word
            
        return None

    # titlecase will automatically handle LOWER_WORDS logic
    return titlecase(journal_name, callback=custom_callback)


def format_booktitle(booktitle_name):
    def custom_callback(word, **kwargs):
        # Rule 1: Handle Organization Names (e.g., IEEE, ACM)
        if any(org in word.upper() for org in ORG_NAMES):
            return word.upper()
        
        # Rule 3: Handle specific technical abbreviations (Optional)
        # If the word is already all caps and long, keep it (e.g., SCADA)
        if ACRONYM_PATTERN.search(word):
            print(f"  [Booktitle Acronym] Preserving: {word}")
            return word
            
        return None

    # titlecase will automatically handle LOWER_WORDS logic
    return titlecase(booktitle_name, callback=custom_callback)


def format_publisher(publisher_name):
    def custom_callback(word, **kwargs):
        # Rule 1: Handle Organization Names (e.g., IEEE, ACM)
        if any(org in word.upper() for org in ORG_NAMES):
            return word.upper()
        
        # Rule 3: Handle specific technical abbreviations (Optional)
        # If the word is already all caps and long, keep it (e.g., SCADA)
        if ACRONYM_PATTERN.search(word):
            print(f"  [Publisher Acronym] Preserving: {word}")
            return word
            
        return None

    # titlecase will automatically handle LOWER_WORDS logic
    return titlecase(publisher_name, callback=custom_callback)

def format_bib_entry(entry):
    
    """
    处理单个bibitem条目的函数（占位符）
    
    Args:
        bibitem (str): 单个bibitem条目字典
    
    Returns:
        str: 处理后的结果
    
    Note:
        这是一个占位符函数，具体的处理逻辑需要根据实际需求实现
        可能的处理包括：
        - 解析作者、标题、期刊等信息
        - 格式转换
        - 数据清理
        - 信息提取
        等等
    """
    
    # Handle the specific entry type and identifiers
    if 'ENTRYTYPE' not in entry:
        raise ValueError("Missing 'ENTRYTYPE' field in entry")   
    
    entry_type = entry.get('ENTRYTYPE').lower()

    if 'author' not in entry:
        raise ValueError("Missing author field")

    if 'title' not in entry:
        raise ValueError("Missing title field")
    
    if entry_type == 'article' and 'journal' not in entry:
        raise ValueError(f"Missing <journal> field in <article> entry")
    
    if entry_type == 'inproceedings' and 'booktitle' not in entry:
        raise ValueError(f"Missing <booktitle> field in <inproceedings> entry")
    
    if entry_type == 'book' and 'publisher' not in entry:
        raise ValueError(f"Missing <publisher> field in <book> entry")
    
    if entry_type != 'article' and entry_type != 'inproceedings' and entry_type != 'book':
        print('!!!')
        print(entry)
    
    authors, entry['author'] = format_authors(entry['author'])
    entry['title'] = format_title(entry['title'])
    
    if 'journal' in entry: entry['journal'] = format_journal(entry['journal'])
    if 'booktitle' in entry: entry['booktitle'] = format_booktitle(entry['booktitle'])
    if 'publisher' in entry: entry['publisher'] = format_publisher(entry['publisher'])
    
    ## Start building the LaTeX code
    label = entry.get('ID', 'unknown_id')
    bib_code = f"\\bibitem{{{label}}}\n"
    
    bib_code += authors + ', '
    bib_code += entry['title'] + ', '
    # bib_code += "``" + bibitem['title'] + ",''"

    if entry_type == 'article':
        bib_code += f"\\emph{{{entry['journal']}}}, "
    elif entry_type == 'inproceedings':
        bib_code += f"\\emph{{{entry['booktitle']}}}, "
    elif entry_type == 'book':
        bib_code += f"\\emph{{{entry['publisher']}}}, "  
    
    # Collect other metadata
    details = []
    if 'volume' in entry: 
        details.append(f"vol.~{entry['volume']}")
    if 'number' in entry: 
        details.append(f"no.~{entry['number']}")
    if 'pages' in entry: 
        if '-' in entry['pages']:  # If the field contains a hyphen, treat it as a page range (e.g., 123--145)
            entry['pages'] = re.sub(r'\s*-+\s*', '--', entry['pages'])
            details.append(f"pp.~{entry['pages']}")
        else:  # Otherwise, treat it as a single article number (e.g., 123456)
            details.append(f"Art.~no.~{entry['pages']}")
    if 'year' in entry: 
        details.append(entry['year'])
    
    bib_code += ", ".join(details) + "."
    
    return {'code': bib_code, 'meta': entry}


def deduplicate(bibitems_list):
    seen_titles = set()
    unique_list = []
    removed_list = []
    
    for entry in bibitems_list:
        raw_title = entry.get('meta', {}).get('title')
        normalized_title = re.sub(r'\W+', '', str(raw_title).lower())

        if normalized_title not in seen_titles:
            seen_titles.add(normalized_title)
            unique_list.append(entry)
        else:
            removed_list.append(entry)

            max_len = 100
            short_title = raw_title[:max_len] + "..." if len(raw_title) > max_len else raw_title
            print(f"  [Deduplicate] Removed: {short_title}")
    
    return unique_list, removed_list


def sort(bibitems_list):
    
    def extract_surname(authors):
        """
        Extract the surname from the author list.
        
        Args:
            authors (list): List of author strings in "LastName, FirstName" format.
        
        Returns:
            str: Normalized surname string for sorting.
        """
        
        # Get the first author from the list
        first_author = authors[0]
        
        # Extract the surname (in BibTeX format, the surname always precedes the comma, e.g., Zhang, San)
        surname = first_author.split(',')[0]

        # Cleanup: Remove non-alphabetic characters (e.g., LaTeX symbols like \c{s} or spaces)
        clean_surname = re.sub(r'[^a-zA-Z]', '', surname)
        
        return clean_surname.lower()
    
    def extract_year(year_data):
        """Defensively extract the year to prevent crashes from formats like '2026a' or 'in press'."""
        match = re.search(r'\d{4}', str(year_data))
        return int(match.group()) if match else 9999
    
    # Perform multi-level sorting
    return sorted(
        bibitems_list,
        key=lambda x: (
            # 1. Sort by the first author's surname
            extract_surname(x.get('meta', {}).get('author')),
            # 2. For the same surname, sort by publication year (older references first)
            extract_year(x.get('meta', {}).get('year', ''))
        )
    )


def remove_uncited(content, bibitems_list):
    """
    Precisely extracts citation keys from LaTeX content using regex 
    and removes bibliography entries that are not cited.
    """

    # Step 1: Extract citation keys from LaTeX using Regex
    # Matches \cite{...}, \citep{...}, \citet{...}, etc., and captures the content inside braces.
    # [a-zA-Z]* allows for variations like \cite, \citet, \citep, \citeauthor, etc.
    cite_matches = re.findall(r'\\cite[a-zA-Z]*\{([^}]+)\}', content)
    
    # Use a set to store all cited labels for O(1) lookup speed
    cited_labels = set()
    for match_group in cite_matches:
        # Handle multiple citations in one command, e.g., \cite{Lee2026, Wang2025}
        for label in match_group.split(','):
            cited_labels.add(label.strip())
            
    # Step 2: Safely filter the bibliography list
    filtered_list = []
    
    print("\n--- [Uncited Check] ---")
    for bibitem in bibitems_list:
        label = bibitem.get('ID')
        
        if label in cited_labels:
            filtered_list.append(bibitem)
        else:
            print(f"  [Uncited] Removed: {label}")
            
    return filtered_list
    


if __name__ == "__main__":
    
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Parse content from TeX and Bib files.")
    
    # Define command-line arguments
    parser.add_argument('-t', '--tex', type=str, help='Path to the target .tex file')
    parser.add_argument('-b', '--bib', type=str, help='Path to the target .bib file')
    parser.add_argument('-ru', '--remove-uncited', action='store_true', help='Remove bibliography entries not cited in the TeX file')
    
    args = parser.parse_args()
    
    # Assign to descriptive variables
    tex_file_path = args.tex
    bib_file_path = args.bib

    # Fallback logic: If no .bib file is provided via arguments, search the current directory
    if not bib_file_path:
        bib_files = glob.glob('*.bib')
        if bib_files:
            bib_file_path = bib_files[0]
        else:
            print("Error: No .bib file specified via -b/--bib, and no default .bib file found in the current directory.")
            sys.exit(1)

    # Fallback logic: If no .tex file is provided via arguments, search the current directory
    if not tex_file_path:
        tex_files = glob.glob('*.tex')
        if tex_files:
            tex_file_path = tex_files[0]
        else:
            tex_file_path = None
            if args.remove_uncited:
                print("Error: The -ru/--remove-uncited flag requires a .tex file, but none was provided or found in the current directory.")
                sys.exit(1)
            else:
                print("Warning: No .tex file found. Features requiring main text (like unused citation removal) will be disabled.")
            
    # Output the resolved paths for user confirmation
    print(f"Using BIB file: {bib_file_path}")
    if tex_file_path:
        print(f"Using TEX file: {tex_file_path}")

    # Execute extraction using the resolved paths
    reference_list = extract_references(bib_file_path)
    if tex_file_path:
        tex_content = extract_main_text(tex_file_path)
    
    formatted_results = []
    
    print(f"Processing {len(reference_list)} bibliography entries...")
    
    for i, raw_entry in enumerate(reference_list, 1):
        try:
            formatted_entry = format_bib_entry(raw_entry)
            formatted_results.append(formatted_entry)
                
        except Exception as e:
            # Log the error and skip this entry
            print(f"Error processing reference #{i:2}: {e}")
            continue
    
    print(f"Formatting complete. Processed {len(formatted_results)} entries in total.")

    deduplicated_results, _ = deduplicate(formatted_results)
    print(f"Duplicates removed. {len(deduplicated_results)} unique entries remaining.")

    sorted_results = sort(deduplicated_results)
    print("Sorting completed.")
    final_results = sorted_results
    
    if args.remove_uncited and tex_content:
        final_results = remove_uncited(tex_content, final_results)
        print(f"Uncited entries removed. {len(final_results)} valid entries remaining.")
    
    name, ext = os.path.splitext(bib_file_path)
    save_path = f"{name}_formatted.txt"
    with open(save_path, 'w', encoding='utf-8') as f:
        # Write the header
        f.write("\\begin{thebibliography}{99}\n\n")
        
        # Write each entry, separated by a blank line
        for item in final_results:
            f.write(f"{item['code']}\n\n")
        
        # Write the footer
        f.write("\\end{thebibliography}")
    
    print("Task Completed Successfully!")
    print(f"Output saved to: {os.path.abspath(save_path)}")
        
        