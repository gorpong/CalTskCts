import unittest

from caltskcts.validation_utils import (
    validate_required_fields,
    validate_date_format,
    validate_numeric_range,
    validate_list_type,
    validate_email_format,
)

class TestValidationUtils(unittest.TestCase):
    """Unit tests for the shared validation utilities."""

    def test_validate_required_fields_success(self):
        """All required keys present and non‐empty should pass."""
        validate_required_fields({"a": 1, "b": "x"}, ["a", "b"])

    def test_validate_required_fields_missing_key(self):
        with self.assertRaises(ValueError) as cm:
            validate_required_fields({"a": 1}, ["a", "b"])
        self.assertEqual(str(cm.exception), "Missing required field: b")

    def test_validate_required_fields_empty_value(self):
        # Even if the key is present, falsy values (0, "", []) should fail
        with self.assertRaises(ValueError) as cm:
            validate_required_fields({"a": 0, "b": []}, ["a", "b"])
        # It will catch the first missing/empty field
        self.assertEqual(str(cm.exception), "Missing required field: a")

    def test_validate_date_format_success(self):
        """Good strings parse without error."""
        validate_date_format("12/31/2023", "%m/%d/%Y")
        validate_date_format("01/01/2023 14:30", "%m/%d/%Y %H:%M")

    def test_validate_date_format_invalid(self):
        """Badly‐formatted strings raise with a helpful message."""
        with self.assertRaises(ValueError) as cm:
            validate_date_format("2023-12-31", "%m/%d/%Y")
        self.assertIn("MM/DD/YYYY", str(cm.exception))

    def test_validate_date_format_type_error(self):
        """Non‐string inputs also produce the same ValueError."""
        with self.assertRaises(ValueError):
            validate_date_format(None, "%m/%d/%Y") # type: ignore

    def test_validate_numeric_range_type(self):
        """Non‐numeric values always reject."""
        with self.assertRaises(ValueError) as cm:
            validate_numeric_range("foo", "Field", 0, 10)
        self.assertEqual(str(cm.exception), "Field must be a number")

    def test_validate_numeric_range_below_min(self):
        with self.assertRaises(ValueError) as cm:
            validate_numeric_range(-1, "Field", 0, 100)
        self.assertEqual(str(cm.exception), "Field must be a number between 0 and 100")

    def test_validate_numeric_range_above_max(self):
        with self.assertRaises(ValueError) as cm:
            validate_numeric_range(101, "Field", 0, 100)
        self.assertEqual(str(cm.exception), "Field must be a number between 0 and 100")

    def test_validate_numeric_range_success(self):
        """Values on the boundary and in between pass."""
        for v in (0, 50, 100):
            validate_numeric_range(v, "Field", 0, 100)

    def test_validate_numeric_range_numericType_error(self):
        """Test passing a float but needing an int"""
        with self.assertRaises(ValueError) as cm:
            validate_numeric_range(10.0, "Field", 0, 100, int)
        self.assertEqual(str(cm.exception), "Field must be a number")

    def test_validate_list_type_success_and_failure(self):
        validate_list_type([1, 2, 3], "ListField")
        with self.assertRaises(ValueError) as cm:
            validate_list_type("not a list", "ListField")
        self.assertEqual(str(cm.exception), "ListField must be a list")

    def test_validate_email_format_success(self):
        """Common valid addresses pass."""
        for email in [
            "simple@example.com",
            "user.name+tag@sub.domain.co.uk",
            '"quoted"@example.com',
        ]:
            validate_email_format(email)

    def test_validate_email_format_invalid(self):
        """Badly‐shaped strings reject."""
        for bad in ["plainaddress", "@no-local-part.com", "user@.com", "user@site"]:
            with self.assertRaises(ValueError) as cm:
                validate_email_format(bad)
            self.assertEqual(str(cm.exception), "Invalid email format")

if __name__ == "__main__":
    unittest.main()
