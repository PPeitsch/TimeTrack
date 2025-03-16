import datetime
import unittest
from unittest.mock import patch

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

    @patch("app.utils.time_calculator.calculate_daily_hours")
    def test_calculate_weekly_hours(self, mock_daily_hours):
        # Mock calculate_daily_hours to return fixed values
        mock_daily_hours.return_value = 8.0

        # Create mock entries for a week
        monday = datetime.date(2025, 3, 10)  # A Monday
        entries = []

        # 5 work days
        for i in range(5):
            entry = unittest.mock.Mock()
            entry.date = monday + datetime.timedelta(days=i)
            entry.absence_code = None
            entry.entries = [{"entry": "09:00", "exit": "17:00"}]
            entries.append(entry)

        # 2 weekend days
        for i in range(5, 7):
            entry = unittest.mock.Mock()
            entry.date = monday + datetime.timedelta(days=i)
            entry.absence_code = None
            entry.entries = []
            entries.append(entry)

        result = calculate_weekly_hours(entries)
        self.assertEqual(result["total"], 40.0)  # 5 days × 8 hours
        self.assertEqual(result["required"], 40.0)  # 5 work days × 8 hours
        self.assertEqual(result["difference"], 0.0)

    @patch("app.utils.time_calculator.calculate_daily_hours")
    def test_calculate_monthly_hours(self, mock_daily_hours):
        # Mock calculate_daily_hours to return fixed values
        mock_daily_hours.return_value = 8.0

        # Create mock entries for a month (assuming 20 work days)
        first_day = datetime.date(2025, 3, 1)
        entries = []

        # Generate entries for all days in a month (31 days)
        for i in range(31):
            day = first_day + datetime.timedelta(days=i)
            entry = unittest.mock.Mock()
            entry.date = day
            entry.absence_code = None
            entry.entries = [{"entry": "09:00", "exit": "17:00"}]
            entries.append(entry)

        result = calculate_monthly_hours(entries)

        # The number of required hours depends on work days in the month
        # so we can't assert exact values, but we can test the structure
        self.assertIn("total", result)
        self.assertIn("required", result)
        self.assertIn("difference", result)


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


if __name__ == "__main__":
    unittest.main()
