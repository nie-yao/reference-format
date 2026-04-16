import bibtexparser
import re
from core.bibliography.formatter import BibliographyFormatter


class BibliographyManager:
    """
    """
    
    def __init__(self, formatter=None):
        self.formatter = formatter or BibliographyFormatter()
        self.entries = []
        self.content = ''
        self.errors = []
        self.stats = {
            'loaded_entries': 0,
            'formatted_entries': 0,
            'removed_duplicates': 0,
            'removed_uncited': 0,
        }

    def _add_error(self, stage, message, entry_index=None):
        error = {
            'stage': stage,
            'message': str(message),
        }
        if entry_index is not None:
            error['entry_index'] = entry_index
        self.errors.append(error)
        return error

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
            error = self._add_error('load_main_text', f"File not found in {file_path}")
            print(f"Error: {error['message']}")
        except Exception as e:
            error = self._add_error('load_main_text', e)
            print(f"Error: {error['message']}")
    
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
            self.stats['loaded_entries'] = len(self.entries)
            print(f"Processing {len(self.entries)} bibliography entries...")
        
        except FileNotFoundError:
            error = self._add_error('load_references', f"File not found in {file_path}")
            print(f"Error: {error['message']}")
        except Exception as e:
            error = self._add_error('load_references', e)
            print(f"Error: {error['message']}")

    def format_all(self):
        formatted_list = []

        for i, raw_entry in enumerate(self.entries, 1):
            try:
                formatted_entry = self.formatter.format(raw_entry)
                formatted_list.append(formatted_entry)
            except Exception as e:
                error = self._add_error('format_all', e, entry_index=i)
                print(f"Error processing reference #{i:2}: {error['message']}")
        
        self.entries = formatted_list
        self.stats['formatted_entries'] = len(formatted_list)
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
        self.stats['removed_duplicates'] = len(removed_list)
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
        removed_count = 0
        for entry in self.entries:
            label = entry['meta']['ID']
            if label in cited_labels:
                filtered_list.append(entry)
            else:
                removed_count += 1
                print(f"  [Uncited] Removed: {label}")
                
        self.entries = filtered_list
        self.stats['removed_uncited'] = removed_count
        print(f"Uncited entries removed. {len(filtered_list)} valid entries remaining.")

    def save_to_file(self, save_path="reference_formatted.txt"):
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write("\\begin{thebibliography}{99}\n\n")
            for item in self.entries:
                f.write(f"{item['code']}\n\n")
            f.write("\\end{thebibliography}")
            
        return save_path
    
    def get_bibnumber(self):
        return len(self.entries)

    def get_error_count(self):
        return len(self.errors)

    def get_stats(self):
        return {
            **self.stats,
            'final_entries': len(self.entries),
            'error_count': self.get_error_count(),
        }
