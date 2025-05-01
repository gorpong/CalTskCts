from typing import Dict, List, Optional, Any
from state_manager import StateManagerBase


class ContactData(Dict[str, Any]):
    """Type for contact data with expected fields."""
    first_name: str
    last_name: str
    title: Optional[str]
    company: Optional[str]
    work_phone: Optional[str]
    mobile_phone: Optional[str]
    home_phone: Optional[str]
    email: Optional[str]


class Contacts(StateManagerBase[ContactData]):
    """Manages lists of contacts and their information such as email, phone numbers, etc."""
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate contact data before adding/updating.
        
        Args:
            item: Contact data to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ["first_name", "last_name"]
        for field in required_fields:
            if field not in item:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate email format if provided
        if item.get("email"):
            if "@" not in item["email"]:
                raise ValueError("Invalid email format")
        
        # Validate phone numbers if provided
        phone_fields = ["work_phone", "mobile_phone", "home_phone"]
        for field in phone_fields:
            raw_value = item.get(field)
            if raw_value:
                cleaned_value = (
                    raw_value
                    .replace("-", "")
                    .replace(".", "")
                    .replace("(", "")
                    .replace(")", "")
                    .replace(" ", "")
                )
                if not cleaned_value.isdigit():
                    raise ValueError(f"Invalid phone number format in {field}")
        
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
        if not contact_id:
            contact_id = self.get_next_id()
        
        contact_data = {
            "first_name": first_name,
            "last_name": last_name,
            "title": title,
            "company": company,
            "work_phone": work_phone,
            "mobile_phone": mobile_phone,
            "home_phone": home_phone,
            "email": email,
        }
        
        # Validate data before adding
        self.validate_item(contact_data)
        
        if self.add_item(contact_id, contact_data):
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
        """
        Update an existing contact.
        
        Args:
            contact_id: The ID of the contact to update
            first_name: New first name
            last_name: New last name
            company: New company name
            title: New job title
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
            "first_name": first_name,
            "last_name": last_name,
            "company": company,
            "title": title,
            "work_phone": work_phone,
            "mobile_phone": mobile_phone,
            "home_phone": home_phone,
            "email": email,
        }
        
        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}
        
        # Create merged data for validation
        merged_data = {**current_data, **updates}
        self.validate_item(merged_data)
        
        if self.update_item(contact_id, updates):
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
        fields = [
            "first_name",
            "last_name",
            "email",
            "work_phone",
            "mobile_phone",
            "home_phone"
        ]
        return self.search_items(query, fields)

    def list_contacts(self) -> Dict[int, Any]:
        """
        List all calendar events.
        
        Returns:
            List of all tasks
        """
        return self.list_items()

    def get_contact(self, contact_id: int) -> Dict[int, Any]:
        """
        Get a specific contact based on the contact ID.
        
        Args:
            contact_id: The integer ID for the contact
        
        Returns:
            Specific contact that matches the ID
        """
        return self.get_item(contact_id)