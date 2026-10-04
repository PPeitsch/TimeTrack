import datetime
import unittest
from unittest.mock import MagicMock, patch

from app.utils.time_calculator import calculate_daily_hours
from app.utils.validators import (
    is_workday,
    validate_date,
    validate_entries,
    validate_time_format,
)


class TestTimeCalculator(unittest.TestCase):
    def test_calculate_daily_hours(self):
        # Test with a single entry
        entries = [{"entry": "09:00", "exit": "17:00"}]
        self.assertEqual(calculate_daily_hours(entries), 8.0)

        # Test with multiple entries
        entries = [
            {"entry": "09:00", "exit": "12:00"},
            {"entry": "13:00", "exit": "18:00"},
        ]
        self.assertEqual(calculate_daily_hours(entries), 8.0)

        # Test with empty entries
        entries = []
        self.assertEqual(calculate_daily_hours(entries), 0.0)

        # Test with invalid entries
        entries = [{"entry": "", "exit": ""}]
        self.assertEqual(calculate_daily_hours(entries), 0.0)

    def test_calculate_daily_hours_across_midnight(self):
        # The exit is earlier than the entry: the range ends the next day
        self.assertEqual(
            calculate_daily_hours([{"entry": "22:00", "exit": "06:00"}]), 8.0
        )
        entries = [
            {"entry": "14:00", "exit": "18:00"},
            {"entry": "22:30", "exit": "00:15"},
        ]
        self.assertEqual(calculate_daily_hours(entries), 5.75)

    def test_validate_time_format(self):
        # Valid time formats
        self.assertTrue(validate_time_format("09:00"))
        self.assertTrue(validate_time_format("23:59"))

        # Invalid time formats
        self.assertFalse(validate_time_format(""))
        self.assertFalse(validate_time_format("9:00"))  # Missing leading zero
        self.assertFalse(validate_time_format("24:00"))  # Invalid hour
        self.assertFalse(validate_time_format("09:60"))  # Invalid minute
        self.assertFalse(validate_time_format("09-00"))  # Wrong separator
        self.assertFalse(validate_time_format("abc"))

    def test_validate_entries(self):
        # Valid entries
        entries = [{"entry": "09:00", "exit": "17:00"}]
        is_valid, _ = validate_entries(entries)
        self.assertTrue(is_valid)

        # Invalid entries - exit equal to entry
        entries = [{"entry": "09:00", "exit": "09:00"}]
        is_valid, error = validate_entries(entries)
        self.assertFalse(is_valid)
        self.assertEqual(error, "Exit time must be different from entry time")

        # Invalid entries - empty
        entries = []
        is_valid, error = validate_entries(entries)
        self.assertFalse(is_valid)
        self.assertEqual(error, "No entries provided")

        # Invalid entries - missing time
        entries = [{"entry": "", "exit": "17:00"}]
        is_valid, error = validate_entries(entries)
        self.assertFalse(is_valid)
        self.assertIn("time", error.lower())

    def test_validate_entries_across_midnight(self):
        # A range that ends the next day is valid when it starts last
        entries = [
            {"entry": "14:00", "exit": "18:00"},
            {"entry": "22:00", "exit": "02:00"},
        ]
        self.assertTrue(validate_entries(entries)[0])

        # Order in the list does not matter, the start time does
        self.assertTrue(validate_entries(list(reversed(entries)))[0])

        # A range that starts after the overnight one would overlap it
        entries = [
            {"entry": "20:00", "exit": "01:00"},
            {"entry": "21:00", "exit": "22:00"},
        ]
        is_valid, error = validate_entries(entries)
        self.assertFalse(is_valid)
        self.assertEqual(
            error, "Only the last time range of the day can end after midnight"
        )

        # Two ranges cannot both end the next day
        entries = [
            {"entry": "20:00", "exit": "01:00"},
            {"entry": "23:00", "exit": "02:00"},
        ]
        is_valid, error = validate_entries(entries)
        self.assertFalse(is_valid)
        self.assertEqual(error, "Only one time range can end after midnight")

    def test_validate_date(self):
        # Valid date formats
        self.assertTrue(validate_date("2025-03-16"))

        # Invalid date formats
        self.assertFalse(validate_date(""))
        self.assertFalse(validate_date("16-03-2025"))  # Wrong format
        self.assertFalse(validate_date("2025/03/16"))  # Wrong separator
        self.assertFalse(validate_date("2025-13-16"))  # Invalid month
        self.assertFalse(validate_date("2025-03-32"))  # Invalid day

    def test_is_workday(self):
        # Test workdays (Monday to Friday)
        monday = datetime.date(2025, 3, 10)
        for i in range(5):
            day = monday + datetime.timedelta(days=i)
            self.assertTrue(is_workday(day))

        # Test weekend (Saturday and Sunday)
        saturday = datetime.date(2025, 3, 15)
        sunday = datetime.date(2025, 3, 16)
        self.assertFalse(is_workday(saturday))
        self.assertFalse(is_workday(sunday))

    def test_validate_entries_invalid_time_values(self):
        """Test validate_entries with times that fail strptime."""
        # Entry time that looks valid format but causes ValueError
        entries = [{"entry": "25:00", "exit": "17:00"}]
        is_valid, error = validate_entries(entries)
        self.assertFalse(is_valid)
        # Should fail on format check due to regex not matching 25:xx
        self.assertIn("time", error.lower())

    def test_validate_entries_invalid_format_error(self):
        """Test validate_entries with format that fails validation."""
        entries = [{"entry": "09:60", "exit": "17:00"}]  # Invalid minute
        is_valid, error = validate_entries(entries)
        self.assertFalse(is_valid)
        self.assertIn("time", error.lower())


if __name__ == "__main__":
    unittest.main()
