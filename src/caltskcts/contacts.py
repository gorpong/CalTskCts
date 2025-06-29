from typing import Dict, List, Optional, Any, MutableMapping
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import ValidationError
from caltskcts.state_manager import Base, StateManagerBase
from caltskcts.schemas import ContactModel


class ContactData(Base):
    __tablename__ = "contacts"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    first_name:   Mapped[str]           = mapped_column(String, nullable=False)
    last_name:    Mapped[str]           = mapped_column(String, nullable=False)
    title:        Mapped[Optional[str]] = mapped_column(String, nullable=True)
    company:      Mapped[Optional[str]] = mapped_column(String, nullable=True)
    work_phone:   Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mobile_phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    home_phone:   Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email:        Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Contacts(StateManagerBase[ContactData]):
    """Manages lists of contacts and their information such as email, phone numbers, etc."""

    Model = ContactData

    def _validate_item(self, item: MutableMapping[str, Any]) -> bool:
        """
        Validate contact data before adding/updating.
        
        Args:
            item: Contact data to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If validation fails
        """
        try:
            ContactModel(**item)
        except ValidationError as ve:
            raise ValueError(str(ve))
        return True

    def add_contact(
        self,
        first_name: str = "",
        last_name: str = "",
        title: Optional[str] = None,
        company: Optional[str] = None,
        work_phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        home_phone: Optional[str] = None,
        email: Optional[str] = None,
        contact_id: Optional[int] = None,
    ) -> str:
        """
        Add a new contact.
        
        Args:
            first_name: Contact's first name
            last_name: Contact's last name
            title: Job title
            company: Company name
            work_phone: Work phone number
            mobile_phone: Mobile phone number
            home_phone: Home phone number
            email: Email address
            contact_id: Optional specific ID to use
            
        Returns:
            Success message
            
        Raises:
            ValueError: If contact_id already exists or validation fails
        """
        if contact_id is None:
            contact_id = self._get_next_id()

        contact_data: MutableMapping[str, Any] = {
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "company": company,
            "work_phone": work_phone,
            "mobile_phone": mobile_phone,
            "home_phone": home_phone,
            "email": email,
        }

        if self.add_item(contact_id, contact_data):  # type: ignore
            return f"Contact {contact_id} added"
        else:
            raise ValueError(f"Contact with ID {contact_id} already exists.")

    def update_contact(
        self,
        contact_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        title: Optional[str] = None,
        company: Optional[str] = None,
        work_phone: Optional[str] = None,
        mobile_phone: Optional[str] = None,
        home_phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        """
        Update an existing contact.
        
        Args:
            contact_id: The ID of the contact to update
            first_name: New first name
            last_name: New last name
            title: New job title
            company: New company name
            work_phone: New work phone
            mobile_phone: New mobile phone
            home_phone: New home phone
            email: New email address
            
        Returns:
            Success message
            
        Raises:
            ValueError: If contact doesn't exist or validation fails
        """
        current_data = self.get_item(contact_id)
        if not current_data:
            raise ValueError(f"Contact with ID {contact_id} does not exist.")

        updates = {
            k: v
            for k, v in {
                "first_name": first_name,
                "last_name": last_name,
                "title": title,
                "company": company,
                "work_phone": work_phone,
                "mobile_phone": mobile_phone,
                "home_phone": home_phone,
                "email": email,
            }.items()
            if v is not None
        }

        if self.update_item(contact_id, updates):  # type: ignore
            return f"Contact {contact_id} updated"
        else:
            raise ValueError(f"Failed to update contact {contact_id}")

    def delete_contact(self, contact_id: int) -> str:
        """
        Delete a contact.
        
        Args:
            contact_id: ID of contact to delete
            
        Returns:
            Success message
            
        Raises:
            ValueError: If contact doesn't exist
        """
        if self.delete_item(contact_id):
            return f"Contact {contact_id} deleted"
        else:
            raise ValueError(f"Contact with ID {contact_id} does not exist.")

    def search_contacts(self, query: str) -> List[Dict[str, Any]]:
        """
        Search contacts by name, email, or phone number.
        
        Args:
            query: Search query (regex pattern)
            
        Returns:
            List of matching contacts with their IDs included
        """
        search_fields = [
            "first_name", "last_name", "email", "company",
            "work_phone", "mobile_phone", "home_phone"
        ]
        return self.search_items(query, search_fields)

    def list_contacts(self) -> Dict[int, Any]:
        """
        List all contacts.
        
        Returns:
            Dictionary of all contacts with integer keys
        """
        return self.list_items()

    def get_contact(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific contact based on the contact ID.
        
        Args:
            contact_id: The integer ID for the contact
        
        Returns:
            Specific contact that matches the ID or None if not found
        """
        return self.get_item(contact_id)
