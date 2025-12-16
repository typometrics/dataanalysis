"""
Data utilities for loading and managing Google Sheets metadata and language mappings.
"""

import pandas as pd

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from gspread_formatting import CellFormat, Color, TextFormat, format_cell_range
except ImportError:
    gspread = None
    ServiceAccountCredentials = None
    CellFormat = None
    Color = None
    TextFormat = None
    format_cell_range = None


def load_google_sheets(credentials_file='typometrics-c4750cac2e21.json', 
                       spreadsheet_url='https://docs.google.com/spreadsheets/d/1IP3ebsNNVAsQ5sxmBnfEAmZc4f0iotAL9hd4aqOOcEg/edit?usp=sharing'):
    """
    Load all Google Sheets data for language metadata.
    
    Parameters
    ----------
    credentials_file : str
        Path to the Google service account credentials JSON file
    spreadsheet_url : str
        URL of the Google Spreadsheet
        
    Returns
    -------
    dict
        Dictionary containing:
        - 'client': gspread client
        - 'spreadsheet': spreadsheet object
        - 'sheets': dict of worksheet objects
        - 'dataframes': dict of pandas DataFrames
    """
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Add your service account credentials
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    
    # Authorize the client
    client = gspread.authorize(creds)
    
    # Open the Google Spreadsheet by its URL
    spreadsheet = client.open_by_url(spreadsheet_url)
    
    # Get the sheets
    my_language_sheet = spreadsheet.get_worksheet(0)
    language_to_group_sheet = spreadsheet.get_worksheet(1)
    appearance_sheet = spreadsheet.get_worksheet(2)
    all_languages_code_sheet = spreadsheet.get_worksheet(3)
    
    # Get all values from the sheets
    my_language_data = my_language_sheet.get_all_values()
    language_to_group_data = language_to_group_sheet.get_all_values()
    appearance_data = appearance_sheet.get_all_values()
    all_languages_code_data = all_languages_code_sheet.get_all_values()
    
    # Convert the data to pandas DataFrames
    my_language_df = pd.DataFrame(my_language_data[1:], columns=my_language_data[0]).iloc[:, :2]
    language_to_group_df = pd.DataFrame(language_to_group_data[1:], columns=language_to_group_data[0]).iloc[:, :6]
    appearance_df = pd.DataFrame(appearance_data[1:], columns=appearance_data[0]).iloc[:, :2]
    all_languages_code_df = pd.DataFrame(all_languages_code_data[1:], columns=all_languages_code_data[0]).iloc[:, :2]
    
    return {
        'client': client,
        'spreadsheet': spreadsheet,
        'sheets': {
            'my_language': my_language_sheet,
            'language_to_group': language_to_group_sheet,
            'appearance': appearance_sheet,
            'all_languages_code': all_languages_code_sheet
        },
        'dataframes': {
            'my_language': my_language_df,
            'language_to_group': language_to_group_df,
            'appearance': appearance_df,
            'all_languages_code': all_languages_code_df
        }
    }


def create_language_mappings(sheets_data):
    """
    Create language name and group mappings from Google Sheets data.
    
    Parameters
    ----------
    sheets_data : dict
        Dictionary returned by load_google_sheets()
        
    Returns
    -------
    dict
        Dictionary containing:
        - 'langNames': dict mapping language codes to full names
        - 'langnameGroup': dict mapping language names to groups
        - 'group2lang': dict mapping groups to lists of languages
        - 'appearance_dict': dict mapping groups to colors
    """
    dataframes = sheets_data['dataframes']
    
    # Create langNames dictionary
    all_languages_code_df = dataframes['all_languages_code']
    my_language_df = dataframes['my_language']
    
    langNames = all_languages_code_df.set_index('code').to_dict()['language']
    mylangNames = my_language_df.set_index('code').to_dict()['displayName']
    langNames = dict(langNames, **mylangNames)  # merge the two dictionaries
    
    # Create langnameGroup dictionary
    language_to_group_df = dataframes['language_to_group']
    langnameGroup = language_to_group_df.set_index('Language').to_dict()['Simple Group']
    
    # Create group2lang dictionary
    group2lang = {group: [] for group in langnameGroup.values()}
    for lang, group in langnameGroup.items():
        group2lang[group].append(lang)
    
    # Create appearance dictionary (group to color mapping)
    appearance_df = dataframes['appearance']
    appearance_dict = {}
    for index, row in appearance_df.iterrows():
        appearance_dict[row['Group']] = row['Default Color']
    
    return {
        'langNames': langNames,
        'langnameGroup': langnameGroup,
        'group2lang': group2lang,
        'appearance_dict': appearance_dict
    }


def update_sheet_validation(sheet, column, data, is_error=True):
    """
    Update a validation column in a Google Sheet.
    
    Parameters
    ----------
    sheet : gspread.Worksheet
        The worksheet to update
    column : int
        Column number (1-indexed)
    data : list
        List of strings to write
    is_error : bool
        If True, format as red/bold. If False, format as black/plain
    """
    red_bold = CellFormat(textFormat=TextFormat(bold=True, foregroundColor=Color(1, 0, 0)))
    black_plain = CellFormat(textFormat=TextFormat(bold=False, foregroundColor=Color(0, 0, 0)))
    
    cell_format = red_bold if is_error else black_plain
    
    # Update cells
    for i, value in enumerate(data, start=1):
        sheet.update_cell(i, column, value)
    
    # Format the range
    column_letter = chr(64 + column)  # Convert column number to letter (A=1, B=2, etc.)
    format_cell_range(sheet, f'{column_letter}1:{column_letter}{len(data)}', cell_format)


def save_metadata(mappings, filename='data/metadata.pkl'):
    """
    Save language mappings to a pickle file.
    
    Parameters
    ----------
    mappings : dict
        Dictionary from create_language_mappings()
    filename : str
        Output filename
    """
    import pickle
    import os
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'wb') as f:
        pickle.dump(mappings, f)
    
    print(f"Saved metadata to {filename}")


def load_metadata(filename='data/metadata.pkl'):
    """
    Load language mappings from a pickle file.
    
    Parameters
    ----------
    filename : str
        Input filename
        
    Returns
    -------
    dict
        Dictionary with langNames, langnameGroup, group2lang, appearance_dict
    """
    import pickle
    
    with open(filename, 'rb') as f:
        mappings = pickle.load(f)
    
    print(f"Loaded metadata from {filename}")
    return mappings
