"""
Validation functions for checking language codes, groups, and computing basic statistics.
"""

from statConll_fast import checkLangCode, checkLangGroups, getAllConllFiles
from gspread_formatting import CellFormat, Color, TextFormat, format_cell_range


def validate_language_codes(langConllFiles, langNames, my_language_sheet):
    """
    Validate language codes and update Google Sheet with any issues.
    
    Parameters
    ----------
    langConllFiles : dict
        Dictionary mapping language codes to CoNLL file lists
    langNames : dict
        Dictionary mapping language codes to full names
    my_language_sheet : gspread.Worksheet
        Google Sheet worksheet for language names
        
    Returns
    -------
    tuple
        (names_with_space, to_add) - lists of problematic entries
    """
    names_with_space, to_add = checkLangCode(langConllFiles, langNames)
    
    red_bold = CellFormat(textFormat=TextFormat(bold=True, foregroundColor=Color(1, 0, 0)))
    black_plain = CellFormat(textFormat=TextFormat(bold=False, foregroundColor=Color(0, 0, 0)))
    
    # Prepare data for column E (5th column)
    if names_with_space or to_add:
        combined_data = ["todo"]
        if names_with_space:
            combined_data += ["names with spaces:"] + names_with_space
        if to_add:
            combined_data += ["to add:"] + to_add
        cell_format = red_bold
    else:
        combined_data = ["OK"] + 10 * [""]
        cell_format = black_plain
    
    # Update the sheet
    for i, value in enumerate(combined_data, start=1):
        my_language_sheet.update_cell(i, 5, value)
    format_cell_range(my_language_sheet, f'E1:E{len(combined_data)}', cell_format)
    
    return names_with_space, to_add


def validate_language_groups(langConllFiles, langNames, langnameGroup, language_to_group_sheet):
    """
    Validate language group assignments and update Google Sheet.
    
    Parameters
    ----------
    langConllFiles : dict
        Dictionary mapping language codes to CoNLL file lists
    langNames : dict
        Dictionary mapping language codes to full names
    langnameGroup : dict
        Dictionary mapping language names to groups
    language_to_group_sheet : gspread.Worksheet
        Google Sheet worksheet for language groups
        
    Returns
    -------
    list
        List of (code, name) tuples for languages missing group assignments
    """
    to_add = checkLangGroups(langConllFiles, langNames, langnameGroup)
    
    red_bold = CellFormat(textFormat=TextFormat(bold=True, foregroundColor=Color(1, 0, 0)))
    black_plain = CellFormat(textFormat=TextFormat(bold=False, foregroundColor=Color(0, 0, 0)))
    
    # Prepare data for column H (8th column)
    if to_add:
        combined_data = ["TODO"] + [f"{la}: {language}" for la, language in to_add]
        cell_format = red_bold
    else:
        combined_data = ["OK"] + 10 * [""]
        cell_format = black_plain
    
    print(combined_data)
    
    # Update the sheet
    for i, lalanguage in enumerate(combined_data, start=1):
        language_to_group_sheet.update_cell(i, 8, lalanguage)
    format_cell_range(language_to_group_sheet, f'H1:H{len(combined_data)}', cell_format)
    
    # Append missing languages to the sheet
    for language in to_add:
        language_to_group_sheet.append_row([language[1]])
    
    return to_add


def compute_basic_statistics(langConllFiles, langNames, langnameGroup):
    """
    Compute basic statistics for each language in the corpus.
    
    Parameters
    ----------
    langConllFiles : dict
        Dictionary mapping language codes to CoNLL file lists
    langNames : dict
        Dictionary mapping language codes to full names
    langnameGroup : dict
        Dictionary mapping language names to groups
        
    Returns
    -------
    pandas.DataFrame
        DataFrame with columns: language, nConllFiles, nSentences, nTokens, avgSentenceLength
    """
    import pandas as pd
    from tqdm.notebook import tqdm
    
    langData = []
    
    for lang in tqdm(langConllFiles, desc="Computing statistics"):
        langDict = {}
        langDict['language'] = lang
        langDict['languageName'] = langNames.get(lang, lang)
        langDict['group'] = langnameGroup.get(langNames.get(lang, lang), 'Unknown')
        langDict['nConllFiles'] = len(langConllFiles[lang])
        
        # Read all CoNLL files for this language
        all_conll = '\n\n'.join([open(conllFile).read() for conllFile in langConllFiles[lang]])
        langDict['nSentences'] = all_conll.count('\n\n')
        langDict['nTokens'] = all_conll.count('\n') - langDict['nSentences']
        langDict['avgSentenceLength'] = langDict['nTokens'] / langDict['nSentences'] if langDict['nSentences'] > 0 else 0
        
        langData.append(langDict)
    
    langTable = pd.DataFrame(langData)
    return langTable


def get_file_tree_counts(langConllFiles):
    """
    Compute the number of trees (sentences) per CoNLL file.
    
    Parameters
    ----------
    langConllFiles : dict
        Dictionary mapping language codes to CoNLL file lists
        
    Returns
    -------
    dict
        Dictionary mapping file paths to tree counts
    """
    conllfile2treenb = {}
    
    for lang in langConllFiles:
        for conllFile in langConllFiles[lang]:
            with open(conllFile) as f:
                conll = f.read()
            conllfile2treenb[conllFile] = conll.count('\n\n')
    
    return conllfile2treenb
