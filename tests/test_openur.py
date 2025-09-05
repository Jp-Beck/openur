"""
Tests for OpenUR main module.
"""
import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from openur import OpenUR
from openur.exceptions import ValidationError, ConfigurationError, ConnectionError

class TestOpenUR(unittest.TestCase):
    """Test cases for OpenUR class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'rtde_configuration.xml')
        self.create_test_config()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_config(self):
        """Create a test RTDE configuration file."""
        config_content = '''<?xml version="1.0"?>
<rtde_config>
    <recipe key="rco">
        <field name="actual_q" type="VECTOR6D"/>
    </recipe>
    <recipe key="rci">
        <field name="speed_slider_mask" type="UINT32"/>
    </recipe>
</rtde_config>'''
        with open(self.config_file, 'w') as f:
            f.write(config_content)

    def test_invalid_ip_address(self):
        """Test that invalid IP addresses raise ValidationError."""
        with self.assertRaises(ValidationError):
            OpenUR('invalid_ip', self.config_file)

    def test_missing_config_file(self):
        """Test that missing config file raises ConfigurationError."""
        with self.assertRaises(ConfigurationError):
            OpenUR('192.168.1.11', 'nonexistent.xml')

    @patch('openur.RTDECommands')
    @patch('openur.Dashboard')
    @patch('openur.URClient')
    def test_successful_initialization(self, mock_ur_client, mock_dashboard, mock_rtde):
        """Test successful initialization with valid parameters."""
        # Mock the connection objects
        mock_rtde_instance = Mock()
        mock_rtde_instance.connect.return_value = True
        mock_rtde_instance.is_connected.return_value = True
        mock_rtde.return_value = mock_rtde_instance

        mock_dashboard_instance = Mock()
        mock_dashboard_instance.connect.return_value = True
        mock_dashboard_instance.is_connected.return_value = True
        mock_dashboard.return_value = mock_dashboard_instance

        mock_ur_client_instance = Mock()
        mock_ur_client_instance.connect.return_value = True
        mock_ur_client_instance.is_connected.return_value = True
        mock_ur_client.return_value = mock_ur_client_instance

        # Test initialization
        robot = OpenUR('192.168.1.11', self.config_file)

        # Verify connections were made
        self.assertEqual(robot.ip_address, '192.168.1.11')
        self.assertTrue(robot.is_connected())

        # Clean up
        robot.close()

    def test_context_manager(self):
        """Test context manager functionality."""
        with patch('openur.RTDECommands') as mock_rtde, \
             patch('openur.Dashboard') as mock_dashboard, \
             patch('openur.URClient') as mock_ur_client:

            # Mock the connection objects
            mock_rtde_instance = Mock()
            mock_rtde_instance.connect.return_value = True
            mock_rtde_instance.is_connected.return_value = True
            mock_rtde.return_value = mock_rtde_instance

            mock_dashboard_instance = Mock()
            mock_dashboard_instance.connect.return_value = True
            mock_dashboard_instance.is_connected.return_value = True
            mock_dashboard.return_value = mock_dashboard_instance

            mock_ur_client_instance = Mock()
            mock_ur_client_instance.connect.return_value = True
            mock_ur_client_instance.is_connected.return_value = True
            mock_ur_client.return_value = mock_ur_client_instance

            # Test context manager
            with OpenUR('192.168.1.11', self.config_file) as robot:
                self.assertTrue(robot.is_connected())

            # Verify close was called
            mock_rtde_instance.close.assert_called_once()
            mock_dashboard_instance.close.assert_called_once()
            mock_ur_client_instance.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
