import datetime
import unittest
from unittest.mock import MagicMock, patch

from app.utils.time_calculator import (
    calculate_daily_hours,
    calculate_monthly_hours,
    calculate_weekly_hours,
)
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

    def test_calculate_weekly_hours(self):
        # Create mock entries for a week
        monday = datetime.date(2025, 3, 10)  # A Monday
        entries = []

        # 5 work days
        for i in range(5):
            entry = MagicMock()
            entry.date = monday + datetime.timedelta(days=i)
            entry.absence_code = None
            entry.entries = []  # Empty entries initially
            entries.append(entry)

        # 2 weekend days
        for i in range(5, 7):
            entry = MagicMock()
            entry.date = monday + datetime.timedelta(days=i)
            entry.absence_code = None
            entry.entries = []
            entries.append(entry)

        # Mock the calculate_daily_hours function
        with patch("app.utils.time_calculator.calculate_daily_hours", return_value=8.0):
            result = calculate_weekly_hours(entries)
            self.assertEqual(result["total"], 40.0)  # 5 days × 8 hours
            self.assertEqual(result["required"], 40.0)  # 5 work days × 8 hours
            self.assertEqual(result["difference"], 0.0)

    def test_calculate_monthly_hours(self):
        # Create mock entries for a month (assuming 20 work days)
        first_day = datetime.date(2025, 3, 1)
        entries = []

        # Generate entries for all days in a month (31 days)
        for i in range(31):
            day = first_day + datetime.timedelta(days=i)
            entry = MagicMock()
            entry.date = day
            entry.absence_code = None
            entry.entries = []  # Empty entries initially
            entries.append(entry)

        # Mock the calculate_daily_hours function
        with patch("app.utils.time_calculator.calculate_daily_hours", return_value=8.0):
            result = calculate_monthly_hours(entries)

            # We should expect the number of weekdays in March 2025
            weekdays = sum(
                1
                for i in range(31)
                if (first_day + datetime.timedelta(days=i)).weekday() < 5
            )

            self.assertEqual(result["total"], weekdays * 8.0)
            self.assertEqual(result["required"], weekdays * 8.0)
            self.assertEqual(result["difference"], 0.0)


class TestValidators(unittest.TestCase):
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

        # Invalid entries - exit before entry
        entries = [{"entry": "09:00", "exit": "08:00"}]
        is_valid, error = validate_entries(entries)
        self.assertFalse(is_valid)
        self.assertEqual(error, "Exit time must be after entry time")

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
