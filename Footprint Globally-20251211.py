#!/usr/bin/env python3
"""
Create on: 2025/12/10
Update on: 2025/12/11
"""

import folium
import pandas as pd
import json
import os
from geopy.geocoders import Nominatim
from typing import List, Dict, Optional
import webbrowser
from datetime import datetime, timedelta
import warnings
from dateutil import parser
import re

warnings.filterwarnings('ignore')


class PersonalizedWorldMap:
    def __init__(self, user_name: str = "visitor"):
        """
        Initialize personalized map
        Args:
            user_name: User name for personalization
        """
        self.user_name = user_name
        self.map = None
        self.cities = []
        self.geolocator = Nominatim(user_agent="personal_world_map")
        self.colors = ['red', 'blue', 'green', 'purple', 'orange',
                       'darkred', 'lightred', 'beige', 'darkblue',
                       'darkgreen', 'cadetblue', 'darkpurple',
                       'white', 'pink', 'lightblue', 'lightgreen']

        # Create user-specific directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"maps/{user_name}_{timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"Hi, {user_name}! Mark your footprint and record your travel.")
        print("=" * 50)

    def _create_base_map(self):
        """Create base world map"""
        self.map = folium.Map(
            location=[0, 180],  # Center of world map
            zoom_start=2,  # Initial zoom level
            control_scale=True,  # Show scale (default)
            tiles='OpenStreetMap',
            width='100%',  # Map container size
            height='100%'
        )

        # Add multiple map layers
        tile_layers = {
            'OpenStreetMap': 'OpenStreetMap',
            'Satellite Image': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            'Topographic Map': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            'Dark Theme': 'CartoDB dark_matter'
        }

        for name, tile in tile_layers.items():
            folium.TileLayer(
                tile,
                name=name,
                attr='Map data © OpenStreetMap contributors'
            ).add_to(self.map)

    def get_coordinates(self, city_name: str) -> Optional[tuple]:
        """
        Get city coordinates (auto-complete country information)

        Args:
            city_name: City name (can include country, e.g., "Beijing, China")

        Returns:
            (latitude, longitude) or None
        """
        try:
            # Try direct query
            location = self.geolocator.geocode(city_name, timeout=10)

            # If not found, try adding country information
            if not location and ',' not in city_name:
                # Common country suffixes
                location = self.geolocator.geocode(f"{city_name}, China", timeout=10)
                if not location:
                    location = self.geolocator.geocode(f"{city_name}, USA", timeout=10)
                if not location:
                    location = self.geolocator.geocode(f"{city_name}", timeout=10)

            if location:
                return (location.latitude, location.longitude)
            else:
                print(f"⚠️ Could not find {city_name}")
                return None

        except Exception as e:
            print(f"❌ Error when searching for {city_name}: {e}")
            return None

    def _parse_timestamp_string(self, timestamp_str: str) -> Dict:
        """
        Parse timestamp string with multiple format support

        Args:
            timestamp_str: The timestamp string to parse

        Returns:
            Dict containing parsed time information
        """
        timestamp_str = str(timestamp_str).strip()
        original_str = timestamp_str

        # Debug information
        print(f"  🔍 Parsing timestamp: '{original_str}'")

        # 1. Check if it's a year range (e.g., "2020-2023")
        year_range_match = re.match(r'^(\d{4})\s*-\s*(\d{4})$', timestamp_str)
        if year_range_match:
            start_year = int(year_range_match.group(1))
            end_year = int(year_range_match.group(2))
            visit_date = datetime(start_year, 1, 1)
            return {
                'visit_date': visit_date,
                'visit_year': start_year,
                'visit_month': 1,
                'display_date': f"{start_year}-{end_year}",
                'is_range': True,
                'original_timestamp': original_str
            }

        # 2. Check if it's just a year (e.g., "2023")
        if timestamp_str.isdigit() and len(timestamp_str) == 4:
            year = int(timestamp_str)
            visit_date = datetime(year, 1, 1)
            return {
                'visit_date': visit_date,
                'visit_year': year,
                'visit_month': 1,
                'display_date': f"{year}",
                'is_range': False,
                'original_timestamp': original_str
            }

        # 3. Check if it's a Unix timestamp (numeric)
        if timestamp_str.replace('.', '', 1).isdigit():
            try:
                timestamp_float = float(timestamp_str)
                visit_date = datetime.fromtimestamp(timestamp_float)
                return {
                    'visit_date': visit_date,
                    'visit_year': visit_date.year,
                    'visit_month': visit_date.month,
                    'display_date': visit_date.strftime("%B %d, %Y"),
                    'is_range': False,
                    'original_timestamp': original_str
                }
            except (ValueError, OSError):
                pass

        # 4. Try multiple datetime formats
        datetime_formats = [
            # ISO formats
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%SZ',

            # Standard formats
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',

            # Slash formats
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d',

            # Day-first formats
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',

            # Month-first (US) formats
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            '%m/%d/%Y',

            # Year-month format
            '%Y-%m',
            '%Y/%m',

            # Text month formats
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
        ]

        for fmt in datetime_formats:
            try:
                visit_date = datetime.strptime(timestamp_str, fmt)
                # Determine display format based on what was parsed
                if fmt == '%Y-%m' or fmt == '%Y/%m':
                    display_date = visit_date.strftime("%B %Y")
                elif fmt == '%Y':
                    display_date = visit_date.strftime("%Y")
                else:
                    display_date = visit_date.strftime("%B %d, %Y")

                return {
                    'visit_date': visit_date,
                    'visit_year': visit_date.year,
                    'visit_month': visit_date.month,
                    'display_date': display_date,
                    'is_range': False,
                    'original_timestamp': original_str
                }
            except ValueError:
                continue

        # 5. Try using dateutil parser as fallback
        try:
            visit_date = parser.parse(timestamp_str, fuzzy=True)
            return {
                'visit_date': visit_date,
                'visit_year': visit_date.year,
                'visit_month': visit_date.month,
                'display_date': visit_date.strftime("%B %d, %Y"),
                'is_range': False,
                'original_timestamp': original_str
            }
        except:
            pass

        # 6. If all parsing fails, use current date with warning
        print(f"  ⚠️ Could not parse timestamp '{original_str}', using current date")
        visit_date = datetime.now()
        return {
            'visit_date': visit_date,
            'visit_year': visit_date.year,
            'visit_month': visit_date.month,
            'display_date': visit_date.strftime("%B %d, %Y") + " (estimated)",
            'is_range': False,
            'original_timestamp': original_str
        }

    def _get_visit_time(self, city_name: str) -> Dict:
        """
        Get user visit time

        Args:
            city_name: City name

        Returns:
            Dict: Information containing visit date and timestamp
        """
        print(f"\n📅 Record visit time for {city_name}")
        print("-" * 40)

        while True:
            print("\nSelect time input method:")
            print("  1. Enter specific date (YYYY-MM-DD)")
            print("  2. Enter year and month (YYYY-MM)")
            print("  3. Enter year only (YYYY)")
            print("  4. Use current time")
            print("  5. Time range (YYYY-YYYY)")

            time_choice = input("Choose (1-5, default: 4): ").strip()

            try:
                if time_choice == '1':
                    # Enter specific date
                    date_str = input("Enter visit date (YYYY-MM-DD, e.g., 2023-05-20): ").strip()
                    time_info = self._parse_timestamp_string(date_str)
                    if time_info['display_date'].endswith("(estimated)"):
                        # Re-prompt if parsing failed
                        print("❌ Invalid date format, please try again")
                        continue

                elif time_choice == '2':
                    # Enter year and month
                    month_str = input("Enter visit month (YYYY-MM, e.g., 2023-05): ").strip()
                    time_info = self._parse_timestamp_string(month_str)
                    if time_info['display_date'].endswith("(estimated)"):
                        print("❌ Invalid month format, please try again")
                        continue

                elif time_choice == '3':
                    # Enter year only
                    year_str = input("Enter visit year (YYYY, e.g., 2023): ").strip()
                    time_info = self._parse_timestamp_string(year_str)
                    if time_info['display_date'].endswith("(estimated)"):
                        print("❌ Invalid year format, please try again")
                        continue

                elif time_choice == '5':
                    # Time range
                    range_str = input("Enter visit time range (YYYY-YYYY, e.g., 2020-2023): ").strip()
                    time_info = self._parse_timestamp_string(range_str)
                    if not time_info.get('is_range', False):
                        print("❌ Invalid range format, please try again")
                        continue

                else:
                    # Use current time (default)
                    visit_date = datetime.now()
                    time_info = {
                        'visit_date': visit_date,
                        'visit_year': visit_date.year,
                        'visit_month': visit_date.month,
                        'display_date': visit_date.strftime("%B %d, %Y"),
                        'is_range': False,
                        'original_timestamp': visit_date.isoformat()
                    }

                # Confirm time input
                print(f"\n✅ Recorded time: {time_info['display_date']}")
                confirm = input("Confirm time? (y/n, default: y): ").strip().lower()

                if confirm != 'n':
                    # Add timestamp for consistency
                    time_info['timestamp'] = time_info['visit_date'].timestamp()
                    return time_info

            except Exception as e:
                print(f"❌ Time format error: {e}")
                print("Please try again...")

    def _generate_year_marker(self, city_name: str, lat: float, lon: float,
                              visit_year: int, color: str, note: str = "") -> folium.Marker:
        """
        Generate marker with year indicator

        Args:
            city_name: City name
            lat: Latitude
            lon: Longitude
            visit_year: Visit year
            color: Marker color
            note: Note

        Returns:
            folium.Marker: Marker with year indicator
        """
        # Create custom icon with year
        icon_html = f"""
        <div style="background-color: {color}; 
                    width: 40px; 
                    height: 40px; 
                    border-radius: 50%; 
                    border: 2px solid white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-family: Arial, sans-serif;">
            {str(visit_year)[-2:]}
        </div>
        """

        # Create popup window
        popup_html = f"""
        <div style="width: 250px;">
            <div style="background-color:{color}; padding:8px; border-radius:5px; margin-bottom:10px;">
                <h3 style="color:white; margin:0; font-size:16px;">📍 {city_name}</h3>
            </div>
            <div style="margin-bottom:10px;">
                <p><b>📅 Visit Time:</b><br>{visit_year}</p>
                <p><b>📍 Coordinates:</b><br>{lat:.4f}, {lon:.4f}</p>
                <p><b>👤 User:</b><br>{self.user_name}</p>
            </div>
            <div style="background-color:#f5f5f5; padding:8px; border-radius:3px; margin:10px 0;">
                <p style="margin:0; font-size:12px;"><b>📝 Note:</b><br>{note if note else 'No note'}</p>
            </div>
            <hr style="margin:10px 0;">
            <p style="font-size:11px; color:#666; text-align:center;">
                <i>Global Footprints • Lasting Memories</i>
            </p>
        </div>
        """

        # Create custom icon
        icon = folium.DivIcon(
            html=icon_html,
            icon_size=(40, 40),
            icon_anchor=(20, 20)
        )

        # Create marker
        return folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{city_name} ({visit_year})",
            icon=icon
        )

    def _add_city_marker_with_time(self, city_name: str, lat: float, lon: float,
                                   color: str, time_info: Dict, note: str = ""):
        """Add city marker with time information to map"""
        if not self.map:
            self._create_base_map()

        # Create popup window with time information
        popup_html = f"""
        <div style="width: 250px;">
            <div style="background-color:{color}; padding:8px; border-radius:5px; margin-bottom:10px;">
                <h3 style="color:white; margin:0; font-size:16px;">📍 {city_name}</h3>
            </div>
            <div style="margin-bottom:10px;">
                <p><b>📅 Visit Time:</b><br>{time_info['display_date']}</p>
                <p><b>📍 Coordinates:</b><br>{lat:.4f}, {lon:.4f}</p>
                <p><b>👤 User:</b><br>{self.user_name}</p>
            </div>
            <div style="background-color:#f5f5f5; padding:8px; border-radius:3px; margin:10px 0;">
                <p style="margin:0; font-size:12px;"><b>📝 Note:</b><br>{note if note else 'No note'}</p>
            </div>
            <hr style="margin:10px 0;">
            <p style="font-size:11px; color:#666; text-align:center;">
                <i>Global Footprints • Lasting Memories</i>
            </p>
        </div>
        """

        # Use default icon
        marker = folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{city_name} ({time_info['display_date']})",
            icon=folium.Icon(color=color, icon='glyphicon glyphicon-map-marker', prefix='glyphicon')
        )

        # Add year marker if year information exists
        if 'visit_year' in time_info and time_info['visit_year']:
            year_marker = self._generate_year_marker(city_name, lat, lon,
                                                     time_info['visit_year'], color, note)
            year_marker.add_to(self.map)

        marker.add_to(self.map)

    def add_city_interactive(self) -> bool:
        """
        Interactive city marking (including visit time)

        Returns:
            bool: Whether to continue adding
        """
        print("\n" + "=" * 50)
        print("Choose your city (input 'q': exit, 'l': check marked cities)")
        print("=" * 50)

        while True:
            city_input = input("\n🌍 Enter city name (e.g., Beijing, Chicago): ").strip()

            if city_input.lower() == 'q':
                return False
            elif city_input.lower() == 'l':
                self.show_selected_cities()
                continue
            elif not city_input:
                continue

            # Get coordinates
            print(f"🔍 Searching for {city_input}...")
            coordinates = self.get_coordinates(city_input)

            if coordinates:
                lat, lon = coordinates
                print(f"✅ Found: {city_input} - Coordinates: ({lat:.4f}, {lon:.4f})")

                # Get visit time
                time_info = self._get_visit_time(city_input)

                # Let user choose marker style
                print("\n🎨 Choose marker color:")
                for i, color in enumerate(self.colors[:10], 1):
                    print(f"  {i}. {color}")

                color_choice = input("Choose color (1-10, default: 1): ").strip()
                try:
                    color_idx = int(color_choice) - 1 if color_choice else 0
                    color = self.colors[min(max(color_idx, 0), 9)]
                except:
                    color = 'red'

                # Add marker
                self._add_city_marker_with_time(city_input, lat, lon, color, time_info)

                # Ask to add note
                note = input("📝 Add a note (optional, press Enter to skip): ").strip()

                # Add to city list
                city_data = {
                    'name': city_input,
                    'latitude': lat,
                    'longitude': lon,
                    'color': color,
                    'note': note,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'visit_date': time_info['visit_date'].strftime("%Y-%m-%d"),
                    'visit_year': time_info['visit_year'],
                    'display_date': time_info['display_date'],
                    'is_range': time_info.get('is_range', False),
                    'original_timestamp': time_info.get('original_timestamp', '')
                }

                if time_info.get('visit_month'):
                    city_data['visit_month'] = time_info['visit_month']

                self.cities.append(city_data)

                print(f"✅ Marked city: {city_input} ({time_info['display_date']})")

                # Ask to continue
                continue_add = input("\nContinue marking cities? (y/n, default: y): ").strip().lower()
                if continue_add == 'n':
                    return False
            else:
                print(f"❌ Not found: {city_input}")
                retry = input("Try again? (y/n, default: y): ").strip().lower()
                if retry == 'n':
                    continue_add = input("Continue marking other cities? (y/n, default: y): ").strip().lower()
                    if continue_add == 'n':
                        return False

    def show_selected_cities(self):
        """Show list of selected cities (including time information)"""
        if not self.cities:
            print("📭 No cities marked yet")
            return

        print("\n📋 Marked cities:")
        print("=" * 80)
        print(f"{'ID':<4} {'City':<20} {'Visit Time':<15} {'Latitude':<10} {'Longitude':<10} {'Note':<15}")
        print("-" * 80)

        for i, city in enumerate(self.cities, 1):
            name = city['name'][:18] + '..' if len(city['name']) > 18 else city['name']
            visit_time = city['display_date'][:13] + '..' if len(city['display_date']) > 13 else city['display_date']
            note = city['note'][:13] + '..' if len(city['note']) > 13 else city['note']
            print(f"{i:<4} {name:<20} {visit_time:<15} {city['latitude']:<10.4f} {city['longitude']:<10.4f} {note:<15}")
        print("=" * 80)

    def add_cities_from_file(self, file_path: str):
        """Import cities in bulk from file with enhanced timestamp parsing"""
        try:
            # Create base map first
            if not self.map:
                self._create_base_map()

            print(f"📂 Loading file: {file_path}")
            print("=" * 60)

            if file_path.endswith('.csv'):
                # Read CSV file
                df = pd.read_csv(file_path)

                # Check required columns
                required_columns = ['name', 'latitude', 'longitude', 'color', 'note', 'timestamp']

                for col in required_columns:
                    if col not in df.columns:
                        print(f"❌ Missing required column: {col}")
                        print(f"   Available columns: {', '.join(df.columns)}")
                        return

                print(f"✅ CSV file loaded successfully. Found {len(df)} cities.")
                print("\nSupported timestamp formats:")
                print("  • YYYY-MM-DD HH:MM:SS (e.g., 2023-05-15 10:30:00)")
                print("  • YYYY-MM-DD (e.g., 2023-05-15)")
                print("  • YYYY (e.g., 2023)")
                print("  • YYYY-YYYY (e.g., 2020-2023 for time range)")
                print("  • Unix timestamp (e.g., 1684146600)")
                print("  • Various date formats with / separator")
                print("=" * 60)

                for index, row in df.iterrows():
                    try:
                        # Extract data from row
                        city_name = str(row['name']).strip()
                        lat = float(row['latitude'])
                        lon = float(row['longitude'])
                        color = str(row['color']).strip().lower()

                        # Validate color
                        if color not in self.colors:
                            print(f"\n⚠️ Color '{color}' not in predefined colors, using 'blue'")
                            color = 'blue'

                        note = str(row['note']) if pd.notna(row['note']) else ""

                        # Parse timestamp using the unified parser
                        timestamp_str = str(row['timestamp'])
                        time_info = self._parse_timestamp_string(timestamp_str)

                        # Validate parsed year
                        current_year = datetime.now().year
                        if time_info['visit_year'] < 1900 or time_info['visit_year'] > current_year + 1:
                            print(f"  ⚠️ Unreasonable year {time_info['visit_year']}, adjusting to {current_year}")
                            time_info['visit_date'] = time_info['visit_date'].replace(year=current_year)
                            time_info['visit_year'] = current_year
                            time_info['display_date'] = f"{current_year} (adjusted)"

                        # Create complete time_info for marker
                        marker_time_info = {
                            'timestamp': time_info['visit_date'].timestamp(),
                            'visit_date': time_info['visit_date'],
                            'visit_year': time_info['visit_year'],
                            'visit_month': time_info['visit_month'],
                            'display_date': time_info['display_date'],
                            'is_range': time_info.get('is_range', False)
                        }

                        # Add marker to map
                        self._add_city_marker_with_time(city_name, lat, lon, color, marker_time_info, note)

                        # Add to cities list
                        city_data = {
                            'name': city_name,
                            'latitude': lat,
                            'longitude': lon,
                            'color': color,
                            'note': note,
                            'timestamp': timestamp_str,
                            'visit_date': time_info['visit_date'].strftime("%Y-%m-%d"),
                            'visit_year': time_info['visit_year'],
                            'visit_month': time_info['visit_month'],
                            'display_date': time_info['display_date'],
                            'is_range': time_info.get('is_range', False),
                            'original_timestamp': time_info.get('original_timestamp', timestamp_str)
                        }

                        self.cities.append(city_data)

                        print(
                            f"  ✅ {index + 1:3d}. {city_name:<20} → Year: {time_info['visit_year']:4d} | Display: {time_info['display_date']}")

                    except Exception as e:
                        print(f"  ❌ Error processing row {index + 1}: {e}")
                        continue

            elif file_path.endswith('.json'):
                # Read JSON file
                with open(file_path, 'r', encoding='utf-8') as f:
                    cities_data = json.load(f)

                print(f"✅ JSON file loaded successfully. Found {len(cities_data)} cities.")
                print("=" * 60)

                for index, city in enumerate(cities_data):
                    try:
                        # Extract data from JSON
                        city_name = str(city['name']).strip()
                        lat = float(city['latitude'])
                        lon = float(city['longitude'])
                        color = str(city['color']).strip().lower()

                        # Validate color
                        if color not in self.colors:
                            print(f"\n⚠️ Color '{color}' not in predefined colors, using 'blue'")
                            color = 'blue'

                        note = str(city['note']) if 'note' in city else ""

                        # Parse timestamp
                        timestamp_str = str(city['timestamp'])
                        time_info = self._parse_timestamp_string(timestamp_str)

                        # Validate parsed year
                        current_year = datetime.now().year
                        if time_info['visit_year'] < 1900 or time_info['visit_year'] > current_year + 1:
                            print(f"  ⚠️ Unreasonable year {time_info['visit_year']}, adjusting to {current_year}")
                            time_info['visit_date'] = time_info['visit_date'].replace(year=current_year)
                            time_info['visit_year'] = current_year
                            time_info['display_date'] = f"{current_year} (adjusted)"

                        # Create complete time_info for marker
                        marker_time_info = {
                            'timestamp': time_info['visit_date'].timestamp(),
                            'visit_date': time_info['visit_date'],
                            'visit_year': time_info['visit_year'],
                            'visit_month': time_info['visit_month'],
                            'display_date': time_info['display_date'],
                            'is_range': time_info.get('is_range', False)
                        }

                        # Add marker to map
                        self._add_city_marker_with_time(city_name, lat, lon, color, marker_time_info, note)

                        # Add to cities list
                        city_data = {
                            'name': city_name,
                            'latitude': lat,
                            'longitude': lon,
                            'color': color,
                            'note': note,
                            'timestamp': timestamp_str,
                            'visit_date': time_info['visit_date'].strftime("%Y-%m-%d"),
                            'visit_year': time_info['visit_year'],
                            'visit_month': time_info['visit_month'],
                            'display_date': time_info['display_date'],
                            'is_range': time_info.get('is_range', False),
                            'original_timestamp': time_info.get('original_timestamp', timestamp_str)
                        }

                        self.cities.append(city_data)

                        print(
                            f"  ✅ {index + 1:3d}. {city_name:<20} → Year: {time_info['visit_year']:4d} | Display: {time_info['display_date']}")

                    except Exception as e:
                        print(f"  ❌ Error processing city {index + 1}: {e}")
                        continue
            else:
                print("❌ Unsupported file format. Please use CSV or JSON.")
                return

            print("\n" + "=" * 60)
            print(f"✅ Successfully imported {len(self.cities)} cities from {file_path}")

            # Show import summary
            if self.cities:
                years = [city['visit_year'] for city in self.cities if 'visit_year' in city]
                if years:
                    print(f"📊 Import Summary:")
                    print(f"  • Earliest year: {min(years)}")
                    print(f"  • Latest year: {max(years)}")
                    print(f"  • Time ranges: {sum(1 for city in self.cities if city.get('is_range', False))}")
                    print(f"  • Unique years: {len(set(years))}")

        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
        except pd.errors.EmptyDataError:
            print("❌ The file is empty")
        except Exception as e:
            print(f"❌ Failed to import file: {e}")
            import traceback
            traceback.print_exc()

    def save_map(self):
        """Save personalized map and related data"""
        if not self.cities:
            print("⚠️ No cities marked yet, cannot save map")
            return

        # Add layer control
        folium.LayerControl().add_to(self.map)

        # Add title
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; 
                    left: 50px; 
                    z-index: 1000; 
                    background-color: white; 
                    padding: 10px; 
                    border-radius: 5px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                    font-family: Arial, sans-serif;">
            <h3 style="margin: 0; color: #333;">🌍 {self.user_name}'s Footprint Map</h3>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 12px;">
                Marked {len(self.cities)} cities • Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </p>
        </div>
        '''
        self.map.get_root().html.add_child(folium.Element(title_html))

        # Add timeline legend
        if any('visit_year' in city for city in self.cities):
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; 
                        right: 50px; 
                        z-index: 1000; 
                        background-color: white; 
                        padding: 10px; 
                        border-radius: 5px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                        font-family: Arial, sans-serif;
                        font-size: 12px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">📍 Timeline Legend</h4>
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="width: 20px; height: 20px; border-radius: 50%; background-color: red; margin-right: 10px;"></div>
                    <span>Number inside circle shows last two digits of visit year</span>
                </div>
            </div>
            '''
            self.map.get_root().html.add_child(folium.Element(legend_html))

        # Generate filenames
        map_filename = f"{self.output_dir}/{self.user_name}_World_Footprint_Map.html"
        data_filename = f"{self.output_dir}/{self.user_name}_City_Data.json"
        csv_filename = f"{self.output_dir}/{self.user_name}_City_Data.csv"

        # Save map
        self.map.save(map_filename)

        # Save data
        with open(data_filename, 'w', encoding='utf-8') as f:
            json.dump(self.cities, f, ensure_ascii=False, indent=2)

        # Save CSV with all columns including timestamp
        df = pd.DataFrame(self.cities)
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')

        print("\n" + "=" * 50)
        print("✅ Successfully generated your footprint map!")
        print("=" * 50)
        print(f"📁 Files saved to: {self.output_dir}/")
        print(f"🗺️ Interactive map: {map_filename}")
        print(f"📊 Data files: {data_filename} and {csv_filename}")
        print(f"📍 Total marked cities: {len(self.cities)}")
        print("=" * 50)

        # Automatically open in browser
        try:
            webbrowser.open(f"file://{os.path.abspath(map_filename)}")
            print("🌐 Opening map in browser...")
        except:
            print("💡 Double-click the HTML file in File Explorer to open the map")

    def run(self):
        """Run main program"""
        print("""
Welcome to the Global Footprint Marking System!

Features:
1. Search and mark any city worldwide
2. Record visit time (year/month/specific date)
3. Customize marker colors and styles
4. Add personal notes
5. Generate personalized timeline map
6. Export map and data files
7. Import cities from CSV/JSON files

        """)

        # Show supported timestamp formats
        print("📅 Supported timestamp formats for CSV/JSON import:")
        print("=" * 60)
        print("1. Standard:        2023-05-15 10:30:00")
        print("2. Date only:       2023-05-15")
        print("3. Year only:       2023")
        print("4. Year range:      2020-2023")
        print("5. Unix timestamp:  1684146600")
        print("6. ISO format:      2023-05-15T10:30:00")
        print("7. Slash format:    2023/05/15 10:30:00")
        print("8. US format:       05/15/2023 10:30:00")
        print("=" * 60)
        print()

        # Choose input method
        print("Choose city input method:")
        print("  1. Manual input (interactive)")
        print("  2. Import from file (CSV/JSON)")
        choice = input("Choose (1/2, default: 1): ").strip()

        if choice == '2':
            file_path = input("Enter file path (CSV or JSON): ").strip()
            if os.path.exists(file_path):
                # Import cities from file
                self.add_cities_from_file(file_path)

                # Ask if user wants to add more cities manually
                if self.cities:
                    add_more = input("\nDo you want to add more cities manually? (y/n, default: n): ").strip().lower()
                    if add_more == 'y':
                        # Create base map if not already created
                        if not self.map:
                            self._create_base_map()
                        # Interactive city adding
                        self.add_city_interactive()
            else:
                print(f"❌ File does not exist: {file_path}")
                print("Switching to manual input mode")
                choice = '1'

        if choice == '1' or choice == '':
            # Create base map
            self._create_base_map()

            # Interactive city adding
            self.add_city_interactive()

        # Save results
        if self.cities:
            self.save_map()

            # Display statistics
            print("\n📈 Statistics:")
            if self.cities:
                df = pd.DataFrame(self.cities)
                # Sort by visit year
                if 'visit_year' in df.columns:
                    df = df.sort_values('visit_year')
                    print("\nSorted by visit year:")
                    print(df[['name', 'visit_year', 'display_date', 'color']].to_string(index=False))

                    # Year statistics
                    print(f"\n📅 Visit year distribution:")
                    year_counts = df['visit_year'].value_counts().sort_index()
                    for year, count in year_counts.items():
                        print(f"  {year}: {count} cities")
        else:
            print("\n⚠️ No cities marked, exiting program")


# ========== Main Program Entry ==========
def main():
    """Main function"""
    print("=" * 60)
    print("🌍 Global Footprints - Personal Travel Recording System")
    print("=" * 60)

    # Get user information
    user_name = input("Enter your name to create a personalized footprint map: ").strip()
    if not user_name:
        user_name = "Visitor"

    # Create and run system
    map_system = PersonalizedWorldMap(user_name)
    map_system.run()

    print("\nYour footprint map has been saved in the 'maps/' directory")
    print("Share your HTML file with friends to showcase your travel footprints!")


if __name__ == "__main__":
    # Ensure necessary libraries are installed
    try:
        import folium
        import pandas
        from geopy.geocoders import Nominatim
        from dateutil import parser
    except ImportError:
        print("Installing necessary libraries...")
        import subprocess
        import sys

        libraries = ['folium', 'pandas', 'geopy', 'python-dateutil']
        for lib in libraries:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

        print("Libraries installed successfully, please run the program again")
        exit(0)

    main()