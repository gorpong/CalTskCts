import re
from typing import Dict, List, Optional
from state_manager import StateManager


class Contacts:
    """The ctc.* functions for managing lists of contacts and information such as email, phone numbers, etc."""
    
    def __init__(self, state_file: str):
        self.state_manager = StateManager(state_file)

    @property
    def contacts(self) -> Dict[str, Dict]:
        """Access contacts data through state manager"""
        return self.state_manager.state

    def add_contact(
        self,
        contact_id: Optional[int] = None,
        first_name: str = "",
        last_name: str = "",
        title: Optional[str] = None,
        company: Optional[str] = None,
        work_phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        home_phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        """Add a new contact."""
        if not contact_id:
            contact_id = self.state_manager.get_next_id()  # Assign next available ID
        
        contact_data = {
            "first_name": first_name,
            "last_name": last_name,
            "company": company,
            "title": title,
            "work_phone": work_phone,
            "mobile_phone": mobile_phone,
            "home_phone": home_phone,
            "email": email,
        }
        
        if self.state_manager.add_item(contact_id, contact_data):
            return f"Contact {contact_id} added"
        else:
            raise ValueError(f"Contact with ID {contact_id} already exists.")

    def update_contact(
        self,
        contact_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        title: Optional[str] = None,
        work_phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        home_phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        """Update an existing contact."""
        updates = {}
        if first_name is not None:
            updates["first_name"] = first_name
        if last_name is not None:
            updates["last_name"] = last_name
        if company is not None:
            updates["company"] = company
        if title is not None:
            updates["title"] = title
        if work_phone is not None:
            updates["work_phone"] = work_phone
        if mobile_phone is not None:
            updates["mobile_phone"] = mobile_phone
        if home_phone is not None:
            updates["home_phone"] = home_phone
        if email is not None:
            updates["email"] = email
        
        if self.state_manager.update_item(contact_id, updates):
            return f"Contact {contact_id} updated"
        else:
            raise ValueError(f"Contact with ID {contact_id} does not exist.")

    def delete_contact(self, contact_id: int) -> str:
        """Delete a contact."""
        if self.state_manager.delete_item(contact_id):
            return f"Contact {contact_id} deleted"
        else:
            raise ValueError(f"Contact with ID {contact_id} does not exist.")

    def list_contacts(self) -> Dict[int, Dict]:
        """List all contacts with integer keys."""
        return self.state_manager.list_items()

    def get_contact(self, contact_id: int) -> Dict:
        """Retrieve a contact by ID."""
        contact_data = self.state_manager.get_item(contact_id)
        if contact_data:
            return contact_data
        else:
            return f"Contact {contact_id} does not exist"

    def search_contacts(self, query: str) -> List[Dict]:
        """Search contacts by name, email, or phone number using a regex pattern."""
        try:
            query_regex = re.compile(query, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return [
            {"contact_id": contact_id, **contact}
            for contact_id, contact in self.contacts.items()
            if query_regex.search(contact.get("first_name", "") or "")
            or query_regex.search(contact.get("last_name", "") or "")
            or query_regex.search(contact.get("email", "") or "")
            or query_regex.search(contact.get("work_phone", "") or "")
            or query_regex.search(contact.get("mobile_phone", "") or "")
            or query_regex.search(contact.get("home_phone", "") or "")
        ]
