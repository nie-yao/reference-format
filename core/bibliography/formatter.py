#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from titlecase import titlecase


class BibliographyFormatter:
    """
    """
    
    PROPER_NOUNS = {'Kalman', 'Markov', 'Bayesian', 'Gaussian', 'DoS'}
    ORG_NAMES = {"IEEE", "ACM", "CAA", "MIT"}

    BRACE_PATTERN = re.compile(r'\{.*?\}')
    MATH_PATTERN = re.compile(r'\$(?:[^$]|\{[^{}]+\})+\$')
    ACRONYM_PATTERN = re.compile(r'[A-Z]{2,}')

    MATH_MAP = {
        r'H∞': r'$H_\infty$',
        r'H1': r'$H_1$',
        r'H2': r'$H_2$',
        r'$ H\_$\backslash$infty $': r'$H_\infty$',
        r'$H\_$\backslash$infty$': r'$H_\infty$',
    }

    def __init__(self):
        self.authors = ''
        self.title = ''
        self.container_title = ''
        self.volume = ''
        self.number = ''
        self.pages = ''
        self.year = ''

        self.meta = {}

    def reset(self):
        self.__dict__.update({
            'authors': '',
            'title': '',
            'container_title': '',
            'volume': '',
            'number': '',
            'pages': '',
            'year': '',
            'meta': {}
        })

    def format_authors(self):
        """
        Format a BibTeX-style author string into abbreviated names.
        (e.g., "John, Smith" -> "J.~Smith")
        (e.g., "John, Smith and Zhand, San" -> "J.~Smith and S.~Zhang")
        (e.g., "John, Smith and Zhand, San and Li, Si" -> "J.~Smith, S.~Zhang, and S.~Li")

        Args:
            authors (str): Author string separated by 'and'.

        Returns:
            str: Formatted author string.

        Raises:
            ValueError: If the input is empty, without <,>, or contains <others>.
        """
        author_data = self.meta['author']

        if not author_data or not author_data.strip():
            raise ValueError(f"Author field is empty")
        
        # Step 1: Split the input string into individual authors using 'and'
        author_list = [a.strip() for a in author_data.split(' and ')]
        formatted_authors = []
        
        for author in author_list:
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
        
        # Step 3: Merge all formatted authors into a final string    
        # For 1 author, use "A"
        if len(formatted_authors) == 1:
            author_str = formatted_authors[0]
        # For 2 authors, use "A and B"
        elif len(formatted_authors) == 2:
            author_str = f"{formatted_authors[0]} and {formatted_authors[1]}"
        # For 3 or more authors, use "A, B, and C" (Oxford comma format)
        else:
            author_str = ', '.join(formatted_authors[:-1]) + ', and ' + formatted_authors[-1]
        
        self.authors = author_str
        self.meta['author'] = author_list

    def format_title(self):
        """
        Format a title string into sentence case with special handling.

        Preserves brace-protected text, LaTeX math expressions,
        predefined acronyms and proper nouns, while converting other words to sentence case.

        Args:
            title (str): Input title string.

        Returns:
            str: Formatted title string.
        """
        title = self.meta['title']

        # Replace special symbols globally before tokenization, e.g., H∞ -> $H_\\infty$
        for bad_str, good_str in self.MATH_MAP.items():
            title = title.replace(bad_str, good_str)

        words = title.split()
        formatted_words = []
        
        for i, word in enumerate(words):
            # Rule 1: Handle brace protection {...}
            # If a word contains braces, remove them and preserve the original casing
            if self.BRACE_PATTERN.search(word):
                clean_word = re.sub(r'[{}]', '', word)
                formatted_words.append(clean_word)
                continue

            # Rule 2: Protect LaTeX math formulas (e.g., $H_2$)
            if self.MATH_PATTERN.search(word):
                formatted_words.append(word)
                continue

            # Rule 3: Auto-protect acronyms (e.g., ECO-DKF, LSTM)
            if self.ACRONYM_PATTERN.search(word):
                formatted_words.append(word)
                print(f"  [Title Acronym] Preserving: {word}")
                continue
            
            # Rule 4: Protect proper nouns (e.g., Kalman)
            if any(substring in word for substring in self.PROPER_NOUNS):
                formatted_words.append(word)
                continue

            # Rule 5: Apply Sentence Case formatting
            # Capitalize the first word, OR the word immediately following a colon/punctuation
            if i == 0 or (i > 0 and words[i-1].endswith((':', '?', '!'))):
                formatted_words.append(word.capitalize())
            else:
                formatted_words.append(word.lower())
        
        self.title = ' '.join(formatted_words)

    def _titlecase_callback(self, word, container=""):        
        # Rule 1: Handle Organization Names (e.g., IEEE, ACM)
        if any(org in word.upper() for org in self.ORG_NAMES):
            return word.upper()
        
        # Rule 2: Handle arXiv (e.g., arXiv:2101.12345)
        if 'arxiv' in word.lower():
            return re.sub(r"arxiv", "arXiv", word, flags=re.IGNORECASE)
        
        # Rule 3: Handle specific technical abbreviations (Optional)
        # If the word is already all caps and long, keep it (e.g., SCADA)
        if self.ACRONYM_PATTERN.search(word):
            print(f"  [{container} Acronym] Preserving: {word}")
            return word
        
        return None

    def format_journal(self):
        self.container_title = titlecase(
            self.meta['journal'], 
            callback=lambda w, **kw: self._titlecase_callback(w, "Journal"))

    def format_booktitle(self):
        self.container_title = titlecase(
            self.meta['booktitle'], 
            callback=lambda w, **kw: self._titlecase_callback(w, "Booktitle"))

    def format_publisher(self):
        self.container_title = titlecase(
            self.meta['publisher'], 
            callback=lambda w, **kw: self._titlecase_callback(w, "Publisher"))

    def format_details(self):
        if 'volume' in self.meta:
            self.volume = self.meta['volume']
        if 'number' in self.meta:
            self.number = self.meta['number']
        if 'pages' in self.meta:
            self.pages = re.sub(r'\s*-+\s*', '--', self.meta['pages'])
        if 'year' in self.meta:
            self.year = self.meta['year']

    def format_label(self):
        if 'ID' in self.meta:
            self.label = self.meta['ID']
        else:
            raise ValueError("Missing <ID> field")  
            surname = self.meta['author'][0].split(',')[0].lower()
            year = re.search(r'\d{4}', str(self.meta['year'])).group()
            first_word = self.meta['title'].split(' ')[0].lower()
            self.label = surname + year + first_word
            self.meta['ID'] = self.label

    def format(self, entry):
        if 'ENTRYTYPE' not in entry or 'author' not in entry or 'title' not in entry:
            raise ValueError("Missing core fields (<ENTRYTYPE>, <author>, or <title>)")   
        
        entry_type = entry.get('ENTRYTYPE').lower()
        
        if entry_type == 'article' and 'journal' not in entry:
            raise ValueError("Missing <journal> field in article-type entry")
        if entry_type == 'inproceedings' and 'booktitle' not in entry:
            raise ValueError("Missing <booktitle> field in inproceedings-type entry")
        if entry_type == 'book' and 'publisher' not in entry:
            raise ValueError("Missing <publisher> field in book-type entry")
        
        self.meta = entry
        
        self.format_authors()
        self.format_title()
        
        if 'journal' in entry: self.format_journal()
        elif 'booktitle' in entry: self.format_booktitle()
        elif 'publisher' in entry: self.format_publisher()

        self.format_details()
        self.format_label()

        # Start building LaTeX code
        bib_code = f"\\bibitem{{{self.label}}}\n{self.authors}, {self.title}, \\emph{{{self.container_title}}}, "
        # bib_code = f"\\bibitem{{{label}}}\n{self.authors}, ``{self.title},'' \\emph{{{self.container_title}}}, "
        
        details = []
        if self.volume: details.append(f"vol.~{self.volume}")
        if self.number: details.append(f"no.~{self.number}")
        if self.pages: 
            if '-' in self.pages:
                details.append(f"pp.~{self.pages}")
            else:
                details.append(f"Art.~no.~{self.pages}")
        if self.year: details.append(self.year)
        
        bib_code += ", ".join(details) + "."
        return {'code': bib_code, 'meta': self.meta}
