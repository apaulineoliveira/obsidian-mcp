import re
from typing import Optional

from core.frontmatter import Frontmatter
from core.ports import NoteRepository
from core.search import (
    NoteMatch,
    SearchQuery,
    SearchResult,
    compile_search_pattern,
    find_matching_lines,
    metadata_matches,
    rank_by_relevance,
)
from core.tags import has_all_tags, note_tags

from .vault_notes import VaultNote, read_vault_notes


class SearchService:
    def __init__(self, repository: NoteRepository, frontmatter: Frontmatter):
        self.repository = repository
        self.frontmatter = frontmatter

    def search(self, query: SearchQuery) -> SearchResult:
        query.validate()
        pattern = _compile_pattern(query)

        matches = []
        for note in read_vault_notes(self.repository, self.frontmatter, query.folder):
            match = self._match_note(note, query, pattern)
            if match:
                matches.append(match)

        return rank_by_relevance(matches, query.results_limit)

    def _match_note(self, note: VaultNote, query: SearchQuery, pattern: Optional[re.Pattern]) -> Optional[NoteMatch]:
        if not metadata_matches(note.metadata, query.frontmatter):
            return None

        tags = note_tags(note.metadata, note.body)
        if query.tags and not has_all_tags(tags, query.tags):
            return None

        if pattern is None:
            return NoteMatch(note.path, tags)

        matching_lines = find_matching_lines(note.content, pattern)
        if not matching_lines:
            return None
        return NoteMatch(note.path, tags, len(matching_lines), matching_lines[:query.matches_per_note_limit])


def _compile_pattern(query: SearchQuery) -> Optional[re.Pattern]:
    if not query.query:
        return None
    return compile_search_pattern(query.query, query.regex, query.case_sensitive)
