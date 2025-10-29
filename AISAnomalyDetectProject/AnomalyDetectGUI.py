"""
Act as a prompt engineer and develop a prompt that will design a GUI that takes input from a user and updates a file called config.ini.  It should have an Section named "Inquiery"" that asks for a date range via a date dropdown calendar selector, allows the user to select multiple "Ship Types" (radio buttons with names from 70-89 inclusive), and define a latitude and longitude "center point" selected by clibking on a map of the world.
It should have a Tab called "Data Directory" that asks for the "Path to Data Folder".
It should have a Tab called "Imagery", That asks the user to select either "Data Directory Path" and then ask for the "Imagery Data Directory", OR select "Use API" and then ask for an "API user_name", "Authentication", and "URL".
It should have a tab called Data Storage Location and ask the user if they would like to use the default  storage folder or "Define My Own" to define a storage location (URL).
The config file the value "UseDefaultFolder" is either True or False based on the choice, and if the user inputs their own data storage location URL it should store that as "DataStorageLocation".
This GUI must be able to run on Windows 10/11, Mac, Linux, iOS and Android devices.

Model

Here is a prompt designed to generate the GUI you've described:
Prompt:
"Create a cross-platform graphical user interface (GUI) application that functions as a configuration tool. This application must be capable of running on Windows 10/11, macOS, Linux, iOS, and Android. The primary function of this GUI is to gather user input and use it to generate and update a configuration file named config.ini.
The GUI should be organized into the following tabs and sections:
Main Window:
The main window should contain a tabbed interface to organize the different configuration sections.
"Inquiry" Tab:
This tab will gather the primary parameters for an inquiry. It should contain the following elements:
Date Range: Two date dropdown calendar selectors, one for the "Start Date" and one for the "End Date".
Ship Types: A set of radio buttons labeled with numbers from 70 to 89, inclusive. The user must be able to select multiple options.
Center Point: An interactive map of the world where the user can click to select a specific point. The latitude and longitude of the selected point should be captured.
"Data Directory" Tab:
This tab is for specifying the location of the primary data. It should contain:
Path to Data Folder: A text input field, preferably with a "Browse" button that opens a file/directory dialog to select a folder path.
"Imagery" Tab:
This tab provides two options for sourcing imagery data. The user must select one of the following, and the GUI should dynamically display the relevant input fields:
Option 1: "Data Directory Path"
If selected, a text input field for the "Imagery Data Directory" should appear, allowing the user to specify a local path. A "Browse" button should be included.
Option 2: "Use API"
If selected, the following text input fields should appear:
"API user_name"
"Authentication" (this field should obscure the entered text for security)
"URL"
"Data Storage Location" Tab:
This tab allows the user to define where data should be stored. It should have the following options:
"Use Default Storage Folder": A selectable option (e.g., a checkbox or radio button).
"Define My Own": A selectable option that, when chosen, reveals a text input field for the user to enter a "Storage Location (URL)".
config.ini File Generation:
The application must write the user's selections to a config.ini file with the following structure and logic:

"""
#code
#Ini
[Inquiry]
StartDate = YYYY-MM-DD
EndDate = YYYY-MM-DD
ShipTypes = selected_ship_type_1,selected_ship_type_2,...
CenterPointLatitude = selected_latitude
CenterPointLongitude = selected_longitude

[Data Directory]
PathToDataFolder = /path/to/data

[Imagery]
SourceType = Data Directory Path OR Use API
ImageryDataDirectory = /path/to/imagery/data (only if SourceType is "Data Directory Path")
APIUserName = user_name (only if SourceType is "Use API")
Authentication = authentication_token (only if SourceType is "Use API")
URL = api_url (only if SourceType is "Use API")

[Data Storage Location]
UseDefaultFolder = True OR False
DataStorageLocation = /path/to/storage (only if UseDefaultFolder is False)
Cross-Platform Framework:
Please use a framework such as Kivy, BeeWare, or another suitable alternative that allows the application to be packaged and run natively on Windows 10/11, macOS, Linux, iOS, and Android from a single Python codebase. The solution should include the necessary code structure and an explanation of how to run and package the application for these platforms."

"""
Model



Thank you for the clear and detailed responses. Based on your clarifications, here is a comprehensive plan and the initial code structure for creating the cross-platform GUI application.
Framework Selection
For this project, Kivy is an excellent choice. It’s a mature, open-source Python library for developing multi-touch applications. Its single codebase can be deployed across Windows, macOS, Linux, iOS, and Android, and it has strong support for the custom UI elements required, including an interactive map.
Project Structure
A well-organized project structure will make development and maintenance easier. Here is a recommended layout:
"""
# code

# Code
config_gui/
├── main.py             # Main application entry point
├── config_gui.kv       # Kivy language file for UI layout and styling
├── world_map.py        # Custom widget for the interactive map
├── assets/             # Folder for images, icons, etc.
│   └── icon.png
└── config.ini          # The configuration file (will be created on first run)

"""
Core Components and Logic
Here is a breakdown of how each requirement will be addressed:
config.ini Handling: Python's built-in configparser library will be used to read and write to the config.ini file. When the application starts, it will check for an existing config.ini. If found, the application will parse it and populate the UI fields. A "Save" button will trigger the function to write the current UI state back to the file.
Cross-Platform UI with Kivy: The UI will be defined in a config_gui.kv file. This approach separates the application's logic from its presentation, making the code cleaner.
Interactive Map with Landmass Validation:
Map Widget: A Kivy-compatible map widget, such as kivy_garden.mapview, will be used to display an interactive OpenStreetMap.
Landmass Check: A library like geopy combined with a point-in-polygon check or an offline library such as global-land-mask will be used to determine if the selected coordinates are on land. When a user clicks on a landmass, a popup will appear with the message "That is not a valid selection."
Dynamic UI Elements:
In the "Imagery" and "Data Storage Location" tabs, the visibility of certain input fields will be controlled by the state of the checkboxes or radio buttons. Kivy's property binding system makes this straightforward to implement.
Validation:
Date Validation: A function will be tied to the date selectors to ensure the "End Date" is not earlier than the "Start Date." A visual cue or a popup will alert the user if the validation fails.
URL Validation: A regular expression can be used to perform a basic check on the format of the URL fields.
Initial Code Implementation
Here is a starting point for the main.py and config_gui.kv files. This code sets up the main application window, the tabbed interface, and placeholders for the widgets.
"""

# main.py

# code
# Python

import configparser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import os
# A library to check if coordinates are on land
from global_land_mask import globe

class ConfigRoot(BoxLayout):
    # Properties to bind to the UI widgets
    start_date = StringProperty("")
    end_date = StringProperty("")
    ship_types = ListProperty([])
    center_point_lat = NumericProperty(0)
    center_point_lon = NumericProperty(0)
    path_to_data_folder = StringProperty("")
    imagery_source_type = StringProperty("Data Directory Path")
    imagery_data_directory = StringProperty("")
    api_user_name = StringProperty("")
    api_authentication = StringProperty("")
    api_url = StringProperty("")
    use_default_folder = BooleanProperty(True)
    data_storage_location = StringProperty("")

    def __init__(self, **kwargs):
        super(ConfigRoot, self).__init__(**kwargs)
        self.load_config()

    def load_config(self):
        if not os.path.exists('config.ini'):
            return

        config = configparser.ConfigParser()
        config.read('config.ini')

        if 'Inquiry' in config:
            self.start_date = config['Inquiry'].get('StartDate', '')
            self.end_date = config['Inquiry'].get('EndDate', '')
            # Further logic needed to set checkboxes from comma-separated string
            self.center_point_lat = float(config['Inquiry'].get('CenterPointLatitude', 0))
            self.center_point_lon = float(config['Inquiry'].get('CenterPointLongitude', 0))

        # ... (load other sections)

    def save_config(self):
        config = configparser.ConfigParser()

        config['Inquiry'] = {
            'StartDate': self.start_date,
            'EndDate': self.end_date,
            'ShipTypes': ",".join(self.ship_types),
            'CenterPointLatitude': self.center_point_lat,
            'CenterPointLongitude': self.center_point_lon
        }
        
        # ... (save other sections)

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def check_map_point(self, lat, lon):
        is_on_land = globe.is_land(lat, lon)
        if is_on_land:
            popup = Popup(title='Invalid Selection',
                          content=Label(text='That is not a valid selection.'),
                          size_hint=(None, None), size=(400, 200))
            popup.open()
        else:
            self.center_point_lat = lat
            self.center_point_lon = lon


class ConfigGUIApp(App):
    def build(self):
        return ConfigRoot()


if __name__ == '__main__':
    ConfigGUIApp().run()
config_gui.kv (Abridged for clarity)
code
Kv
#:import MapView kivy_garden.mapview.MapView

<ConfigRoot>:
    orientation: 'vertical'
    TabbedPanel:
        do_default_tab: False
        TabbedPanelItem:
            text: 'Inquiry'
            GridLayout:
                cols: 2
                # Date Pickers would be custom widgets here
                Label:
                    text: 'Start Date:'
                TextInput:
                    id: start_date
                    text: root.start_date
                Label:
                    text: 'End Date:'
                TextInput:
                    id: end_date
                    text: root.end_date

                # Checkboxes for Ship Types
                # ... A scrollview with a grid of checkboxes would go here

                # Map for Center Point
                MapView:
                    lat: 50.6394
                    lon: 3.057
                    zoom: 3
                    on_touch_down:
                        lat, lon = self.get_latlon_at(args[1].x, args[1].y)
                        root.check_map_point(lat, lon)
        
        TabbedPanelItem:
            text: 'Data Directory'
            # ... Widgets for this tab

        TabbedPanelItem:
            text: 'Imagery'
            # ... Widgets for this tab with dynamic visibility

        TabbedPanelItem:
            text: 'Data Storage Location'
            # ... Widgets for this tab

    Button:
        text: 'Save Configuration'
        size_hint_y: None
        height: '48dp'
        on_release: root.save_config()

"""
Explanation for Running and Packaging
To Run the Application for Development:
1. Install Python: Ensure you have Python installed on your system.
2. Install Kivy and Dependencies: You will need to install Kivy and the other required libraries.
"""
# code
# Bash
pip install kivy
pip install kivy_garden.mapview
pip install global-land-mask

# 3. Run the App: Navigate to the config_gui directory and run:

# code
# Bash
python main.py

"""
To Package for Different Platforms:
A tool like Buildozer is typically used to package Kivy applications for desktop and mobile platforms.
Install Buildozer:
"""

# code
# Bash

pip install buildozer

# Initialize Buildozer: In your project directory, run:
# code
# Bash
buildozer init

"""
This will create a buildozer.spec file, which you will need to edit to configure the build for each platform.
Configure buildozer.spec:
Set the title, package.name, and package.domain.
In the requirements section, add python3, kivy, kivy_garden.mapview, global-land-mask.

Build for Android:
"""

# code
# Bash
buildozer android debug

#This will download the necessary Android SDK and NDK components and build an APK file.

# 5. Build for iOS: Building for iOS requires a macOS machine with Xcode installed.

#code
#Bash
buildozer ios debug

"""
6. Build for Windows/macOS/Linux: For desktop platforms, you can use PyInstaller, which is integrated with Buildozer. You would specify the target platform in the buildozer.spec file.
This provides a solid foundation for the application. The next steps would involve fully implementing the UI widgets in the .kv file, writing the logic for populating the UI from the config.ini file, and fleshing out the validation functions.

Model


Of course. Here is the complete and unabridged code for the config_gui.kv file.
This file defines the entire layout and widget structure for your application, separating the visual design from the application logic in your main.py file. It includes the dynamic UI elements and bindings to the properties defined in the ConfigRoot class.
"""

#config_gui.kv

#code
#Kv

#:import MapView kivy_garden.mapview.MapView

# This is the root widget that contains the entire GUI.
# It corresponds to the ConfigRoot class in the main.py file.
<ConfigRoot>:
    orientation: 'vertical'
    spacing: 10
    padding: 10

    TabbedPanel:
        do_default_tab: False
        tab_pos: 'top_mid'

        # ====================================================================
        # INQUIRY TAB
        # ====================================================================
        TabbedPanelItem:
            text: 'Inquiry'
            GridLayout:
                cols: 2
                spacing: 10
                padding: 10

                # --- Date Range ---
                Label:
                    text: 'Start Date (YYYY-MM-DD):'
                    halign: 'right'
                    valign: 'middle'
                    text_size: self.size
                TextInput:
                    id: start_date
                    text: root.start_date
                    on_text: root.start_date = self.text
                    multiline: False
                    write_tab: False

                Label:
                    text: 'End Date (YYYY-MM-DD):'
                    halign: 'right'
                    valign: 'middle'
                    text_size: self.size
                TextInput:
                    id: end_date
                    text: root.end_date
                    on_text: root.end_date = self.text
                    multiline: False
                    write_tab: False
                
                # --- Spacer ---
                Widget:
                    size_hint_y: None
                    height: 20
                Widget:
                    size_hint_y: None
                    height: 20

                # --- Ship Types ---
                Label:
                    text: 'Ship Types:'
                    halign: 'right'
                    valign: 'top'
                    text_size: self.size
                
                ScrollView:
                    GridLayout:
                        id: ship_types_grid
                        cols: 5
                        spacing: 10
                        size_hint_y: None
                        height: self.minimum_height
                        # In main.py, you would need a loop to add the checkboxes
                        # to this grid, as KV language doesn't support loops.
                        # For example:
                        # for i in range(70, 90):
                        #     cb = CheckBox()
                        #     self.ids.ship_types_grid.add_widget(cb)
                        #     ...

                # --- Spacer ---
                Widget:
                    size_hint_y: None
                    height: 20
                Widget:
                    size_hint_y: None
                    height: 20

                # --- Center Point Map ---
                Label:
                    text: 'Center Point (Click Map):'
                    halign: 'right'
                    valign: 'top'
                    text_size: self.size
                
                BoxLayout:
                    orientation: 'vertical'
                    MapView:
                        id: world_map
                        lat: 20  # Default latitude
                        lon: 0   # Default longitude
                        zoom: 2  # Zoom out to see the world
                        on_touch_down:
                            if self.collide_point(*args[1].pos): root.check_map_point(*self.get_latlon_at(args[1].x, args[1].y))

                    GridLayout:
                        cols: 2
                        size_hint_y: None
                        height: 30
                        Label:
                            text: 'Lat: {:.4f}'.format(root.center_point_lat)
                        Label:
                            text: 'Lon: {:.4f}'.format(root.center_point_lon)


        # ====================================================================
        # DATA DIRECTORY TAB
        # ====================================================================
        TabbedPanelItem:
            text: 'Data Directory'
            GridLayout:
                cols: 3
                spacing: 10
                padding: 10
                Label:
                    text: 'Path to Data Folder:'
                    size_hint_x: 0.3
                TextInput:
                    id: data_folder_path
                    text: root.path_to_data_folder
                    on_text: root.path_to_data_folder = self.text
                    multiline: False
                Button:
                    text: 'Browse...'
                    size_hint_x: 0.2
                    # on_release: root.browse_data_folder() # This function would be in main.py

        # ====================================================================
        # IMAGERY TAB
        # ====================================================================
        TabbedPanelItem:
            text: 'Imagery'
            BoxLayout:
                orientation: 'vertical'
                spacing: 10
                padding: 10
                
                # --- Selection ---
                BoxLayout:
                    size_hint_y: None
                    height: 40
                    Label:
                        text: 'Imagery Source:'
                    CheckBox:
                        id: imagery_from_dir
                        group: 'imagery_source'
                        active: root.imagery_source_type == 'Data Directory Path'
                        on_active: root.imagery_source_type = 'Data Directory Path' if self.active else root.imagery_source_type
                    Label:
                        text: 'Data Directory Path'
                    CheckBox:
                        id: imagery_from_api
                        group: 'imagery_source'
                        active: root.imagery_source_type == 'Use API'
                        on_active: root.imagery_source_type = 'Use API' if self.active else root.imagery_source_type
                    Label:
                        text: 'Use API'

                # --- Option 1: Data Directory Path ---
                GridLayout:
                    cols: 3
                    spacing: 10
                    disabled: not imagery_from_dir.active
                    opacity: 1 if self.disabled == False else 0
                    
                    Label:
                        text: 'Imagery Data Directory:'
                        size_hint_x: 0.3
                    TextInput:
                        id: imagery_data_directory
                        text: root.imagery_data_directory
                        on_text: root.imagery_data_directory = self.text
                        multiline: False
                    Button:
                        text: 'Browse...'
                        size_hint_x: 0.2
                        # on_release: root.browse_imagery_folder()

                # --- Option 2: Use API ---
                GridLayout:
                    cols: 2
                    spacing: 10
                    disabled: not imagery_from_api.active
                    opacity: 1 if self.disabled == False else 0

                    Label:
                        text: 'API User Name:'
                    TextInput:
                        id: api_user_name
                        text: root.api_user_name
                        on_text: root.api_user_name = self.text
                        multiline: False
                    Label:
                        text: 'Authentication:'
                    TextInput:
                        id: api_auth
                        text: root.api_authentication
                        on_text: root.api_authentication = self.text
                        password: True
                        multiline: False
                    Label:
                        text: 'URL:'
                    TextInput:
                        id: api_url
                        text: root.api_url
                        on_text: root.api_url = self.text
                        multiline: False

        # ====================================================================
        # DATA STORAGE LOCATION TAB
        # ====================================================================
        TabbedPanelItem:
            text: 'Data Storage Location'
            BoxLayout:
                orientation: 'vertical'
                padding: 10
                spacing: 10

                # --- Selection ---
                BoxLayout:
                    size_hint_y: None
                    height: 40
                    CheckBox:
                        id: use_default_storage
                        group: 'storage_location'
                        active: root.use_default_folder
                        on_active: root.use_default_folder = self.active
                    Label:
                        text: 'Use Default Storage Folder'
                    
                    CheckBox:
                        id: use_custom_storage
                        group: 'storage_location'
                        active: not root.use_default_folder
                        on_active: root.use_default_folder = not self.active
                    Label:
                        text: 'Define My Own'
                
                # --- Custom Location Input ---
                GridLayout:
                    cols: 2
                    spacing: 10
                    disabled: use_default_storage.active
                    opacity: 1 if self.disabled == False else 0

                    Label:
                        text: 'Storage Location (URL):'
                    TextInput:
                        id: custom_storage_location
                        text: root.data_storage_location
                        on_text: root.data_storage_location = self.text
                        multiline: False
    
    # ====================================================================
    # SAVE BUTTON
    # ====================================================================
    Button:
        text: 'Save Configuration'
        size_hint_y: None
        height: '48dp'
        on_release: root.save_config()


"""
Model

Of course. After a thorough review of both the main.py and config_gui.kv files, I have identified several key areas that are incomplete or contain logical errors that would prevent the application from functioning as intended.
Summary of Errors and Omissions
Incomplete load_config() Function (main.py): The function only loads the [Inquiry] section and is missing the logic to load the [Data Directory], [Imagery], and [Data Storage Location] sections. It also doesn't handle populating the ship type checkboxes from the saved config file.
Incomplete save_config() Function (main.py): Similar to loading, the saving function only handles the [Inquiry] section. It omits the other three sections. The logic for handling the conditional [Imagery] section (API vs. Directory) is missing.
Missing Ship Type CheckBox Logic (main.py and config_gui.kv): The .kv file correctly notes that the checkboxes for ship types (70-89) cannot be created in a loop within the KV language itself. The Python code is missing the logic to dynamically create these checkboxes and add them to the grid. Furthermore, there's no logic to gather which boxes are checked when saving the configuration.
Missing "Browse" Button Functions (main.py): The .kv file has "Browse..." buttons, but the corresponding functions (browse_data_folder, browse_imagery_folder) are not defined in the ConfigRoot class.
Missing Input Validation (main.py): The user requested validation (e.g., End Date after Start Date), which has not been implemented in the save_config function.
Minor Logical Flaw in KV Binding: The on_touch_down event for the MapView could be triggered even if dragging the map, which is not ideal. It's better to use on_map_relocated to get the center or a more robust touch event. However, for a simple click, the provided code is a reasonable starting point and not a critical error. The collide_point check correctly mitigates this.
Corrected Code
Here are the corrected versions of main.py and config_gui.kv. The new main.py is fully implemented to handle all loading, saving, validation, and dynamic widget creation. The config_gui.kv has been slightly adjusted to better support this logic.
Corrected main.py
This version dynamically creates the checkboxes, fully implements saving and loading for all sections, and adds the required validation.
"""

# code
# Python

import configparser
import os
from datetime import datetime

# A library to check if coordinates are on land
from global_land_mask import globe

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock

class ConfigRoot(BoxLayout):
    # Properties to bind to the UI widgets
    start_date = StringProperty("")
    end_date = StringProperty("")
    # This will now be populated by the checkboxes' state, not directly
    # ship_types = ListProperty([]) 
    center_point_lat = NumericProperty(0)
    center_point_lon = NumericProperty(0)
    path_to_data_folder = StringProperty("")
    imagery_source_type = StringProperty("Data Directory Path")
    imagery_data_directory = StringProperty("")
    api_user_name = StringProperty("")
    api_authentication = StringProperty("")
    api_url = StringProperty("")
    use_default_folder = BooleanProperty(True)
    data_storage_location = StringProperty("")

    def __init__(self, **kwargs):
        super(ConfigRoot, self).__init__(**kwargs)
        # We must wait for the kv file to be parsed before accessing ids
        Clock.schedule_once(self.post_kv_init)

    def post_kv_init(self, dt):
        """Called after the kv file is loaded."""
        self.create_ship_type_checkboxes()
        self.load_config()

    def create_ship_type_checkboxes(self):
        """Dynamically creates checkboxes for ship types 70-89."""
        grid = self.ids.ship_types_grid
        for i in range(70, 90):
            # Add a container for each checkbox and its label
            container = BoxLayout(size_hint_y=None, height=30)
            checkbox = CheckBox(size_hint_x=0.2)
            checkbox.bind(active=self.on_checkbox_active) # Bind to a callback
            checkbox.ship_type_id = str(i) # Store the ID
            label = Label(text=str(i))
            container.add_widget(checkbox)
            container.add_widget(label)
            grid.add_widget(container)

    def on_checkbox_active(self, checkbox, value):
        """A callback for when any checkbox changes state."""
        # This function is essential for tracking selections, but the main logic will be to iterate through them during the save operation.
        pass

    def load_config(self):
        """Loads configuration from config.ini and populates the GUI."""
        if not os.path.exists('config.ini'):
            return

        config = configparser.ConfigParser()
        config.read('config.ini')

        # Inquiry Section
        if 'Inquiry' in config:
            inquiry = config['Inquiry']
            self.start_date = inquiry.get('StartDate', '')
            self.end_date = inquiry.get('EndDate', '')
            self.center_point_lat = float(inquiry.get('CenterPointLatitude', 0))
            self.center_point_lon = float(inquiry.get('CenterPointLongitude', 0))
            
            selected_ship_types = inquiry.get('ShipTypes', '').split(',')
            # Set checkboxes based on loaded values
            for container in self.ids.ship_types_grid.children:
                checkbox = container.children[1] # The CheckBox widget
                if checkbox.ship_type_id in selected_ship_types:
                    checkbox.active = True

        # Data Directory Section
        if 'Data Directory' in config:
            self.path_to_data_folder = config['Data Directory'].get('PathToDataFolder', '')

        # Imagery Section
        if 'Imagery' in config:
            imagery = config['Imagery']
            self.imagery_source_type = imagery.get('SourceType', 'Data Directory Path')
            self.imagery_data_directory = imagery.get('ImageryDataDirectory', '')
            self.api_user_name = imagery.get('APIUserName', '')
            self.api_authentication = imagery.get('Authentication', '')
            self.api_url = imagery.get('URL', '')

        # Data Storage Location Section
        if 'Data Storage Location' in config:
            storage = config['Data Storage Location']
            self.use_default_folder = storage.getboolean('UseDefaultFolder', True)
            self.data_storage_location = storage.get('DataStorageLocation', '')

    def save_config(self):
        """Gathers data from GUI, validates it, and saves to config.ini."""
        # --- Validation ---
        try:
            datetime.strptime(self.start_date, '%Y-%m-%d')
            datetime.strptime(self.end_date, '%Y-%m-%d')
            if self.start_date > self.end_date:
                self.show_popup('Validation Error', 'Start Date cannot be after End Date.')
                return
        except ValueError:
            self.show_popup('Validation Error', 'Dates must be in YYYY-MM-DD format.')
            return

        # --- Data Gathering ---
        config = configparser.ConfigParser()

        # Gather selected ship types
        selected_types = []
        for container in self.ids.ship_types_grid.children:
            checkbox = container.children[1]
            if checkbox.active:
                selected_types.append(checkbox.ship_type_id)

        config['Inquiry'] = {
            'StartDate': self.start_date,
            'EndDate': self.end_date,
            'ShipTypes': ",".join(selected_types),
            'CenterPointLatitude': self.center_point_lat,
            'CenterPointLongitude': self.center_point_lon
        }

        config['Data Directory'] = {
            'PathToDataFolder': self.path_to_data_folder
        }

        config['Imagery'] = {
            'SourceType': self.imagery_source_type
        }
        if self.imagery_source_type == 'Data Directory Path':
            config['Imagery']['ImageryDataDirectory'] = self.imagery_data_directory
        else: # Use API
            config['Imagery']['APIUserName'] = self.api_user_name
            config['Imagery']['Authentication'] = self.api_authentication
            config['Imagery']['URL'] = self.api_url

        config['Data Storage Location'] = {
            'UseDefaultFolder': self.use_default_folder,
            'DataStorageLocation': '' if self.use_default_folder else self.data_storage_location
        }
        
        # --- Writing to File ---
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
        self.show_popup('Success', 'Configuration saved successfully.')

    def check_map_point(self, lat, lon):
        """Checks if the clicked map point is on land."""
        is_on_land = globe.is_land(lat, lon)
        if is_on_land:
            self.show_popup('Invalid Selection', 'That is not a valid selection.\nPlease select a point in the water.')
        else:
            self.center_point_lat = lat
            self.center_point_lon = lon
    
    def show_popup(self, title, text):
        """Helper function to show a popup message."""
        popup = Popup(title=title,
                      content=Label(text=text),
                      size_hint=(None, None), size=(400, 200))
        popup.open()

    # --- Placeholder Functions for Browse Buttons ---
    def browse_data_folder(self):
        self.show_popup('Not Implemented', 'File browser functionality is not yet implemented.')

    def browse_imagery_folder(self):
        self.show_popup('Not Implemented', 'File browser functionality is not yet implemented.')


class ConfigGUIApp(App):
    def build(self):
        return ConfigRoot()


if __name__ == '__main__':
    ConfigGUIApp().run()

"""
Corrected config_gui.kv
This version simplifies the checkbox on_active logic and ensures the "Browse" buttons are linked to their new placeholder functions.
"""

# code
# Kv

import MapView kivy_garden.mapview.MapView

<ConfigRoot>:
    orientation: 'vertical'
    spacing: 10
    padding: 10

    TabbedPanel:
        do_default_tab: False
        tab_pos: 'top_mid'

        # ====================================================================
        # INQUIRY TAB
        # ====================================================================
        TabbedPanelItem:
            text: 'Inquiry'
            GridLayout:
                cols: 2
                spacing: 10
                padding: 10

                Label:
                    text: 'Start Date (YYYY-MM-DD):'
                    halign: 'right'
                    valign: 'middle'
                    text_size: self.size
                TextInput:
                    text: root.start_date
                    on_text: root.start_date = self.text
                    multiline: False
                    write_tab: False

                Label:
                    text: 'End Date (YYYY-MM-DD):'
                    halign: 'right'
                    valign: 'middle'
                    text_size: self.size
                TextInput:
                    text: root.end_date
                    on_text: root.end_date = self.text
                    multiline: False
                    write_tab: False
                
                Widget: {size_hint_y: None, height: 20}
                Widget: {size_hint_y: None, height: 20}

                Label:
                    text: 'Ship Types:'
                    halign: 'right'
                    valign: 'top'
                    text_size: self.size
                
                ScrollView:
                    GridLayout:
                        id: ship_types_grid
                        cols: 5
                        spacing: 10
                        size_hint_y: None
                        height: self.minimum_height
                
                Widget: {size_hint_y: None, height: 20}
                Widget: {size_hint_y: None, height: 20}

                Label:
                    text: 'Center Point (Click Map):'
                    halign: 'right'
                    valign: 'top'
                    text_size: self.size
                
                BoxLayout:
                    orientation: 'vertical'
                    MapView:
                        id: world_map
                        lat: 20
                        lon: 0
                        zoom: 2
                        on_touch_down:
                            if self.collide_point(*args[1].pos): root.check_map_point(*self.get_latlon_at(args[1].x, args[1].y))

                    GridLayout:
                        cols: 2
                        size_hint_y: None
                        height: 30
                        Label:
                            text: 'Lat: {:.4f}'.format(root.center_point_lat)
                        Label:
                            text: 'Lon: {:.4f}'.format(root.center_point_lon)

        # ====================================================================
        # DATA DIRECTORY TAB
        # ====================================================================
        TabbedPanelItem:
            text: 'Data Directory'
            GridLayout:
                cols: 3
                spacing: 10
                padding: 10
                Label:
                    text: 'Path to Data Folder:'
                    size_hint_x: 0.3
                TextInput:
                    text: root.path_to_data_folder
                    on_text: root.path_to_data_folder = self.text
                    multiline: False
                Button:
                    text: 'Browse...'
                    size_hint_x: 0.2
                    on_release: root.browse_data_folder()

        # ====================================================================
        # IMAGERY TAB
        # ====================================================================
        TabbedPanelItem:
            text: 'Imagery'
            BoxLayout:
                orientation: 'vertical'
                spacing: 10
                padding: 10
                
                BoxLayout:
                    size_hint_y: None
                    height: 40
                    Label:
                        text: 'Imagery Source:'
                    CheckBox:
                        id: imagery_from_dir
                        group: 'imagery_source'
                        active: root.imagery_source_type == 'Data Directory Path'
                        on_active: if self.active: root.imagery_source_type = 'Data Directory Path'
                    Label:
                        text: 'Data Directory Path'
                    CheckBox:
                        id: imagery_from_api
                        group: 'imagery_source'
                        active: root.imagery_source_type == 'Use API'
                        on_active: if self.active: root.imagery_source_type = 'Use API'
                    Label:
                        text: 'Use API'

                GridLayout:
                    cols: 3
                    spacing: 10
                    disabled: not imagery_from_dir.active
                    opacity: 1 if not self.disabled else 0
                    
                    Label:
                        text: 'Imagery Data Directory:'
                        size_hint_x: 0.3
                    TextInput:
                        text: root.imagery_data_directory
                        on_text: root.imagery_data_directory = self.text
                        multiline: False
                    Button:
                        text: 'Browse...'
                        size_hint_x: 0.2
                        on_release: root.browse_imagery_folder()

                GridLayout:
                    cols: 2
                    spacing: 10
                    disabled: not imagery_from_api.active
                    opacity: 1 if not self.disabled else 0

                    Label: {text: 'API User Name:'}
                    TextInput:
                        text: root.api_user_name
                        on_text: root.api_user_name = self.text
                        multiline: False
                    Label: {text: 'Authentication:'}
                    TextInput:
                        text: root.api_authentication
                        on_text: root.api_authentication = self.text
                        password: True
                        multiline: False
                    Label: {text: 'URL:'}
                    TextInput:
                        text: root.api_url
                        on_text: root.api_url = self.text
                        multiline: False

        # ====================================================================
        # DATA STORAGE LOCATION TAB
        # ====================================================================
        TabbedPanelItem:
            text: 'Data Storage Location'
            BoxLayout:
                orientation: 'vertical'
                padding: 10
                spacing: 10

                BoxLayout:
                    size_hint_y: None
                    height: 40
                    CheckBox:
                        id: use_default_storage
                        group: 'storage_location'
                        active: root.use_default_folder
                        on_active: root.use_default_folder = self.active
                    Label: {text: 'Use Default Storage Folder'}
                    
                    CheckBox:
                        group: 'storage_location'
                        active: not root.use_default_folder
                        on_active: root.use_default_folder = not self.active
                    Label: {text: 'Define My Own'}
                
                GridLayout:
                    cols: 2
                    spacing: 10
                    disabled: use_default_storage.active
                    opacity: 1 if not self.disabled else 0

                    Label: {text: 'Storage Location (URL):'}
                    TextInput:
                        text: root.data_storage_location
                        on_text: root.data_storage_location = self.text
                        multiline: False
    
    # ====================================================================
    # SAVE BUTTON
    # ====================================================================
    Button:
        text: 'Save Configuration'
        size_hint_y: None
        height: '48dp'



"""Additional work
Align to existing code variables:

Currently in Script:
[Inquiry]
StartDate = YYYY-MM-DD
EndDate = YYYY-MM-DD
ShipTypes = selected_ship_type_1,selected_ship_type_2,...
CenterPointLatitude = selected_latitude
CenterPointLongitude = selected_longitude

[Data Directory]
PathToDataFolder = /path/to/data 
# ****Change name to DATA_DIRECTORY****

[Imagery]
SourceType = Data Directory Path OR Use API
ImageryDataDirectory = /path/to/imagery/data (only if SourceType is "Data Directory Path")
APIUserName = user_name (only if SourceType is "Use API")
Authentication = authentication_token (only if SourceType is "Use API")
URL = api_url (only if SourceType is "Use API")

[Data Storage Location]
UseDefaultFolder = True OR False
DataStorageLocation = /path/to/storage (only if UseDefaultFolder is False)
Cross-Platform Framework:
Please use a framework such as Kivy, BeeWare, or another suitable alternative that allows the application to be packaged and run natively on Windows 10/11, macOS, Linux, iOS, and Android from a single Python codebase. The solution should include the necessary code structure and an explanation of how to run and package the application for these platforms."

To Be Added:

[CDSE]
API_KEY = your_cdse_api_key_here
API_SECRET = your_cdse_api_secret_here

# For an S3 storage location
[S3_STORAGE]
AWS_ACCESS_KEY_ID = your_aws_access_key_here
AWS_SECRET_ACCESS_KEY = your_aws_secret_key_here
REGION_NAME = us-east-1
RESULTS_BUCKET_NAME = your-s3-bucket-name

#Github if needed this will have to built out
[Github_Repository Informaiton]

# This current Variable needs to be modified to ensure it takes all the values from the StartDate and EndDate Variables instead.
num_days_to_analyze: This is the most direct user input requested by the script when it is run. The line days_input = input(f"Enter the number of days to analyze (e.g., 5): ") explicitly prompts the user to enter the number of recent days of AIS data they wish to analyze for anomalies.


[Configuration Variables (Hardcoded values that a user would need to change):]
These variables are set at the beginning of the script in the "Configuration" section. For the script to be adapted to different datasets or analysis requirements, a user would need to modify these values in the code itself.
DATA_DIRECTORY: The user must specify the file path to the directory where the AIS data .csv files are stored. The current value is "C:\\AIS_Data".
REQUIRED_COLUMNS: While less likely to change if the data format is consistent, a user might need to modify this list of column names if their AIS data files use different headers.

# ****This needs to be updated to ensure that it takes the specific ship type numbers from the GUI****
SHIP_TYPE_MIN and SHIP_TYPE_MAX: These variables define the range of ship types to be included in the analysis. A user would change these to focus on different categories of vessels (e.g., cargo ships, tankers, fishing boats). The current range is set from 70 to 89.

MIN_TRAVEL_NM and MAX_TRAVEL_NM: These thresholds determine what is considered an anomalous travel distance for a vessel between two consecutive days. A user would adjust these values based on the expected behavior of the ships they are analyzing. Currently, travel less than 200 nautical miles is flagged as "Slow" and more than 550 nautical miles as "Fast".
TIMESTAMP_FORMAT: This string specifies the format of the timestamp data in the input CSV files. If the date and time format in the user's data is different from 'YYYY-%m-%d %H-%M-%S', this variable must be updated to match it for correct parsing.

[Additional File Paths and Directories]:
ANOMALY_REPORTS_DIR: The absolute path to the directory on your local machine where the input AIS anomaly CSV files are stored (e.g., "C:\\MyData\\AIS_Anomalies").
S3_TEMP_DOWNLOAD_DIR: The name of the local folder where temporary files (like downloaded SAR images) will be stored. The default is "temp_sar_downloads", which is usually sufficient.

[Computer Vision Model Parameters:]
YOLO_MODEL_PATH: The path to the pre-trained YOLOv8 model file. The default is "yolov8n.pt", which is the small "nano" model. You might change this if you have a custom-trained model for ship detection on SAR imagery (e.g., "best_sar_ship_model.pt").
CV_CONFIDENCE_THRESHOLD: The minimum confidence level (from 0.0 to 1.0) for the model to consider a detection as a valid ship. The default is 0.2. You can raise this to reduce false positives or lower it to potentially find more ships at the risk of more noise.

[SAR Image Search Parameters:]
SAR_POLARIZATION: The desired SAR polarization. The default is "VV VH", which prioritizes dual polarization. If you consistently work in areas where only single polarization is available, you might change this to "VV".
SAR_ACQUISITION_MODE: The Sentinel-1 acquisition mode. The default, "IW" (Interferometric Wide), is the most common and generally the best choice. It's unlikely you would need to change this.

