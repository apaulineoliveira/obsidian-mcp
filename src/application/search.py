from core.frontmatter import FrontmatterParser
from core.ports import NoteRepository
from core.search import NoteMatch, SearchQuery, SearchResult, find_matches, matches_frontmatter, rank
from core.tags import has_all_tags, note_tags

from .documents import load_documents


class SearchService:
    def __init__(self, repository: NoteRepository, parser: FrontmatterParser):
        self.repository = repository
        self.parser = parser

    def search(self, query: SearchQuery) -> SearchResult:
        query.validate()
        pattern = query.pattern()
        found = []

        for doc in load_documents(self.repository, self.parser, query.folder):
            if not matches_frontmatter(doc.metadata, query.frontmatter):
                continue

            tags = note_tags(doc.metadata, doc.body)
            if query.tags and not has_all_tags(tags, query.tags):
                continue

            matches, match_count = [], 0
            if pattern:
                matches, match_count = find_matches(doc.content, pattern, query.match_limit)
                if not match_count:
                    continue

            found.append(NoteMatch(doc.path, tags, match_count, matches))

        return rank(found, query.result_limit)
