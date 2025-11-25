"""
NLP-based chatbot for querying alumni data.

This module provides a simple chatbot interface that can:
- Parse natural language queries about alumni
- Extract search criteria (company, job title, batch, location)
- Return relevant alumni records from the database
"""

import re
from typing import Optional

from ..database.connection import get_db_context
from ..database.crud import get_all_alumni, search_alumni
from ..database.models import Alumni
from .config import MAX_RESULTS


class AlumniChatbot:
    """
    Simple NLP chatbot for querying alumni data.
    
    Uses keyword matching and basic NLP patterns to understand
    user queries and return relevant alumni information.
    """

    # Intent patterns
    INTENT_PATTERNS = {
        "find_by_company": [
            r"who\s+works?\s+(?:at|for|in)\s+(.+?)(?:\?|$|\.)",
            r"alumni\s+(?:at|from|in)\s+(.+?)(?:\?|$|\.)",
            r"(?:find|show|list|get)\s+(?:alumni\s+)?(?:working\s+)?(?:at|for|in)\s+(.+?)(?:\?|$|\.)",
            r"people\s+(?:at|from|in)\s+(.+?)(?:\?|$|\.)",
        ],
        "find_by_title": [
            r"who\s+(?:is|are)\s+(?:a\s+)?(.+?)(?:\?|$|\.)",
            r"(?:find|show|list|get)\s+(?:all\s+)?(.+?)s?(?:\?|$|\.)",
            r"alumni\s+with\s+(?:title|position|role)\s+(.+?)(?:\?|$|\.)",
        ],
        "find_by_batch": [
            r"(?:from|in)\s+batch\s+(\d{4})",
            r"batch\s+(\d{4})\s+alumni",
            r"(\d{4})\s+(?:batch|graduates?)",
        ],
        "find_by_location": [
            r"who\s+(?:is|are)\s+(?:in|at|from)\s+(.+?)(?:\?|$|\.)",
            r"alumni\s+(?:in|at|from)\s+(.+?)(?:\?|$|\.)",
            r"(?:find|show|list|get)\s+(?:alumni\s+)?(?:in|at|from)\s+(.+?)(?:\?|$|\.)",
        ],
        "general_search": [
            r"(?:find|search|show|list|get)\s+(.+?)(?:\?|$|\.)",
            r"who\s+is\s+(.+?)(?:\?|$|\.)",
        ],
        "count": [
            r"how\s+many\s+alumni",
            r"count\s+(?:of\s+)?alumni",
            r"total\s+(?:number\s+of\s+)?alumni",
        ],
        "help": [
            r"help",
            r"what\s+can\s+you\s+do",
            r"how\s+(?:do\s+i|to)\s+use",
        ],
    }

    # Common job titles to recognize
    JOB_TITLES = [
        "software engineer",
        "data scientist",
        "product manager",
        "analyst",
        "consultant",
        "developer",
        "designer",
        "manager",
        "director",
        "engineer",
        "scientist",
        "researcher",
        "associate",
        "intern",
        "founder",
        "ceo",
        "cto",
        "cfo",
    ]

    # Common companies to recognize
    KNOWN_COMPANIES = [
        "google",
        "microsoft",
        "amazon",
        "meta",
        "facebook",
        "apple",
        "netflix",
        "uber",
        "airbnb",
        "linkedin",
        "twitter",
        "salesforce",
        "oracle",
        "ibm",
        "deloitte",
        "mckinsey",
        "bcg",
        "bain",
        "goldman sachs",
        "morgan stanley",
        "jpmorgan",
        "tcs",
        "infosys",
        "wipro",
        "flipkart",
        "paytm",
        "ola",
        "zomato",
        "swiggy",
    ]

    def __init__(self):
        """Initialize the chatbot."""
        self._last_query = None
        self._last_results = None

    def process_query(self, query: str) -> dict:
        """
        Process a natural language query about alumni.
        
        Args:
            query: User's natural language query.
        
        Returns:
            Dictionary containing response text and matching alumni data.
        """
        query_lower = query.lower().strip()
        self._last_query = query

        # Check for help intent
        if self._match_intent(query_lower, "help"):
            return self._get_help_response()

        # Check for count intent
        if self._match_intent(query_lower, "count"):
            return self._get_count_response(query_lower)

        # Try to extract search criteria
        criteria = self._extract_criteria(query_lower)

        if criteria:
            return self._search_and_respond(criteria, query)

        # Fallback to general search
        return self._general_search_response(query_lower)

    def _match_intent(self, query: str, intent: str) -> Optional[str]:
        """
        Check if query matches an intent pattern.
        
        Args:
            query: User query (lowercase).
            intent: Intent name to check.
        
        Returns:
            Matched group if found, None otherwise.
        """
        patterns = self.INTENT_PATTERNS.get(intent, [])
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else True
        return None

    def _extract_criteria(self, query: str) -> dict:
        """
        Extract search criteria from the query.
        
        Args:
            query: User query (lowercase).
        
        Returns:
            Dictionary of search criteria.
        """
        criteria = {}

        # Check for company
        company_match = self._match_intent(query, "find_by_company")
        if company_match:
            criteria["company"] = company_match.strip()
        else:
            # Check for known companies in query
            for company in self.KNOWN_COMPANIES:
                if company in query:
                    criteria["company"] = company
                    break

        # Check for batch
        batch_match = self._match_intent(query, "find_by_batch")
        if batch_match:
            criteria["batch"] = batch_match

        # Check for location
        location_match = self._match_intent(query, "find_by_location")
        if location_match and "company" not in criteria:
            criteria["location"] = location_match.strip()

        # Check for job title
        title_match = self._match_intent(query, "find_by_title")
        if title_match:
            title_lower = title_match.lower()
            for job_title in self.JOB_TITLES:
                if job_title in title_lower:
                    criteria["designation"] = job_title
                    break

        return criteria

    def _search_and_respond(self, criteria: dict, original_query: str) -> dict:
        """
        Search for alumni and generate response.
        
        Args:
            criteria: Search criteria dictionary.
            original_query: Original user query.
        
        Returns:
            Response dictionary with alumni data.
        """
        try:
            with get_db_context() as db:
                results = get_all_alumni(
                    db,
                    limit=MAX_RESULTS,
                    **criteria,
                )

                self._last_results = results

                if not results:
                    return {
                        "response": self._generate_no_results_message(criteria),
                        "alumni": [],
                        "count": 0,
                        "criteria": criteria,
                    }

                response_text = self._generate_results_message(results, criteria)

                return {
                    "response": response_text,
                    "alumni": [self._alumni_to_dict(a) for a in results],
                    "count": len(results),
                    "criteria": criteria,
                }

        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error while searching: {str(e)}",
                "alumni": [],
                "count": 0,
                "error": str(e),
            }

    def _general_search_response(self, query: str) -> dict:
        """
        Perform a general search based on query.
        
        Args:
            query: User query.
        
        Returns:
            Response dictionary.
        """
        try:
            with get_db_context() as db:
                # Extract search term
                search_term = self._extract_search_term(query)
                
                if search_term:
                    results = search_alumni(db, search_term, limit=MAX_RESULTS)
                else:
                    results = get_all_alumni(db, limit=MAX_RESULTS)

                self._last_results = results

                if not results:
                    return {
                        "response": "I couldn't find any alumni matching your query. "
                                   "Try being more specific or ask for help.",
                        "alumni": [],
                        "count": 0,
                    }

                response_text = f"I found {len(results)} alumni"
                if search_term:
                    response_text += f" matching '{search_term}'"
                response_text += "."

                return {
                    "response": response_text,
                    "alumni": [self._alumni_to_dict(a) for a in results],
                    "count": len(results),
                }

        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "alumni": [],
                "count": 0,
                "error": str(e),
            }

    def _extract_search_term(self, query: str) -> Optional[str]:
        """Extract search term from query."""
        # Remove common words
        stop_words = {
            "find", "show", "list", "get", "search", "for", "me", "the",
            "a", "an", "all", "any", "please", "can", "you", "alumni",
            "who", "is", "are", "where", "what", "which",
        }
        
        words = query.split()
        search_words = [w for w in words if w.lower() not in stop_words]
        
        if search_words:
            return " ".join(search_words)
        return None

    def _get_help_response(self) -> dict:
        """Generate help response."""
        help_text = """
I can help you find alumni information. Here are some things you can ask:

**By Company:**
- "Who works at Google?"
- "Find alumni at Microsoft"
- "Show me people from Amazon"

**By Job Title:**
- "Who is a Software Engineer?"
- "Find all Data Scientists"
- "Show Product Managers"

**By Batch:**
- "Alumni from batch 2020"
- "Show 2019 graduates"

**By Location:**
- "Alumni in Bangalore"
- "Who is in New York?"

**General:**
- "Search for John"
- "Find alumni named Smith"
- "How many alumni do we have?"

Just type your question and I'll do my best to help!
        """
        return {
            "response": help_text.strip(),
            "alumni": [],
            "count": 0,
            "type": "help",
        }

    def _get_count_response(self, query: str) -> dict:
        """Generate count response."""
        try:
            with get_db_context() as db:
                # Check for filters in count query
                batch_match = self._match_intent(query, "find_by_batch")
                company_match = None
                
                for company in self.KNOWN_COMPANIES:
                    if company in query:
                        company_match = company
                        break

                criteria = {}
                if batch_match:
                    criteria["batch"] = batch_match
                if company_match:
                    criteria["company"] = company_match

                results = get_all_alumni(db, limit=10000, **criteria)
                count = len(results)

                response = f"We have {count} alumni"
                if criteria:
                    filters = []
                    if "batch" in criteria:
                        filters.append(f"from batch {criteria['batch']}")
                    if "company" in criteria:
                        filters.append(f"at {criteria['company'].title()}")
                    response += " " + " and ".join(filters)
                response += " in the database."

                return {
                    "response": response,
                    "alumni": [],
                    "count": count,
                    "type": "count",
                }

        except Exception as e:
            return {
                "response": f"Sorry, I couldn't get the count: {str(e)}",
                "alumni": [],
                "count": 0,
                "error": str(e),
            }

    def _generate_results_message(self, results: list[Alumni], criteria: dict) -> str:
        """Generate response message for search results."""
        count = len(results)
        message_parts = [f"I found {count} alumni"]

        if "company" in criteria:
            message_parts.append(f"at {criteria['company'].title()}")
        if "designation" in criteria:
            message_parts.append(f"with role '{criteria['designation'].title()}'")
        if "batch" in criteria:
            message_parts.append(f"from batch {criteria['batch']}")
        if "location" in criteria:
            message_parts.append(f"in {criteria['location'].title()}")

        message = " ".join(message_parts) + "."

        if count > MAX_RESULTS:
            message += f" (Showing first {MAX_RESULTS} results)"

        return message

    def _generate_no_results_message(self, criteria: dict) -> str:
        """Generate message when no results found."""
        message = "I couldn't find any alumni"

        if "company" in criteria:
            message += f" at {criteria['company'].title()}"
        if "designation" in criteria:
            message += f" with role '{criteria['designation'].title()}'"
        if "batch" in criteria:
            message += f" from batch {criteria['batch']}"
        if "location" in criteria:
            message += f" in {criteria['location'].title()}"

        message += ". Try a different search or check the spelling."
        return message

    def _alumni_to_dict(self, alumni: Alumni) -> dict:
        """Convert Alumni model to dictionary."""
        return {
            "id": alumni.id,
            "name": alumni.name,
            "batch": alumni.batch,
            "roll_number": alumni.roll_number,
            "current_company": alumni.current_company,
            "current_designation": alumni.current_designation,
            "location": alumni.location,
            "personal_email": alumni.personal_email,
            "linkedin_url": alumni.linkedin_url,
        }


# Global chatbot instance
_chatbot: Optional[AlumniChatbot] = None


def get_chatbot() -> AlumniChatbot:
    """
    Get the global chatbot instance.
    
    Returns:
        AlumniChatbot instance.
    """
    global _chatbot
    if _chatbot is None:
        _chatbot = AlumniChatbot()
    return _chatbot


def process_chat_query(query: str) -> dict:
    """
    Convenience function to process a chat query.
    
    Args:
        query: User's natural language query.
    
    Returns:
        Response dictionary.
    """
    chatbot = get_chatbot()
    return chatbot.process_query(query)
