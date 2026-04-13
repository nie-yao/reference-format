import bibtexparser
import re
import os
from format import BibliographyFormatter

class BibliographyManager:
    """
    """
    
    def __init__(self, formatter=None):
        self.formatter = formatter or BibliographyFormatter()
        self.entries = []
        self.content = ''

    def load_main_text(self, file_path):
        """
        Extract the main text content from a file.

        Args:
            file_path (str): Path to the input file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()

        except FileNotFoundError:
            print(f"Error: File not found in {file_path}")
        except Exception as e:
            print(f"Error: {e}")
    
    def load_references(self, file_path):
        """
        Extract all bibliography entries from a file.

        Args:
            file_path (str): Path to the input file.

        Returns:
            list of str: A list of extracted reference entries as strings.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                bib_database = bibtexparser.load(f)
            self.entries = bib_database.entries
            print(f"Processing {len(self.entries)} bibliography entries...")
        
        except FileNotFoundError:
            print(f"Error: File not found in {file_path}")
        except Exception as e:
            print(f"Error: {e}")

    def format_all(self):
        formatted_list = []

        for i, raw_entry in enumerate(self.entries, 1):
            try:
                formatted_entry = self.formatter.format(raw_entry)
                formatted_list.append(formatted_entry)
            except Exception as e:
                print(f"Error processing reference #{i:2}: {e}")
        
        self.entries = formatted_list
        print(f"Formatting complete. Processed {len(formatted_list)} entries in total.")

    def deduplicate(self):
        seen_titles = set()
        unique_list, removed_list = [], []
        
        for entry in self.entries:
            raw_title = entry['meta']['title']
            normalized_title = re.sub(r'\W+', '', str(raw_title).lower())

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_list.append(entry)
            else:
                removed_list.append(entry)
                short_title = raw_title[:100] + "..." if len(raw_title) > 100 else raw_title
                print(f"  [Deduplicate] Removed: {short_title}")
        
        self.entries = unique_list
        print(f"Duplicates removed. {len(unique_list)} unique entries remaining.")

    def sort(self):
        def extract_surname(author_list):
            first_author = author_list[0]  # Get the first author from the list
            surname = first_author.split(',')[0]  # Extract the surname (e.g., Zhang, San)
            clean_surname = re.sub(r'[^a-zA-Z]', '', surname)  # Remove non-alphabetic characters (e.g., \c{s} or -)
            return clean_surname.lower()
    
        def safe_extract_year(year_data):
            match = re.search(r'\d{4}', str(year_data))
            return int(match.group()) if match else 9999
        
        self.entries.sort(
            key=lambda x: (
                # 1. Sort by the first author's surname
                extract_surname(x.get('meta').get('author')),
                # 2. For the same surname, sort by publication year (older references first)
                safe_extract_year(x.get('meta').get('year', ''))
            )
        )

        print("Sorting completed.")

    def remove_uncited(self):
        # Step 1: Extract citation keys from LaTeX using Regex
        # Matches \cite{...}, \citep{...}, \citet{...}, etc., and captures the content inside braces.
        cite_matches = re.findall(r'\\cite[a-zA-Z]*\{([^}]+)\}', self.content)
        cited_labels = set()  # for O(1) lookup speed
        
        for match_group in cite_matches:
            # Handle multiple citations, e.g., \cite{Lee2026, Wang2025}
            for label in match_group.split(','):
                cited_labels.add(label.strip())

        # Step 2: filter the bibliography list    
        print("Starting uncited check...")
        
        filtered_list = []
        for entry in self.entries:
            label = entry['meta']['ID']
            if label in cited_labels:
                filtered_list.append(entry)
            else:
                print(f"  [Uncited] Removed: {label}")
                
        self.entries = filtered_list
        print(f"Uncited entries removed. {len(filtered_list)} valid entries remaining.")

    def save_to_file(self):
        save_path = f"reference_formatted.txt"
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write("\\begin{thebibliography}{99}\n\n")
            for item in self.entries:
                f.write(f"{item['code']}\n\n")
            f.write("\\end{thebibliography}")
            
        return save_path
    
    def get_bibnumber(self):
        return len(self.entries)