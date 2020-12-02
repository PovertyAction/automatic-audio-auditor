import pandas as pd

def save_df_to_excel(saving_path, df_to_save, short_entries_cols_index=None, medium_entries_cols_index=None, long_entries_cols_index=None, sort_descending_by=None):
    # In addition to saving df to excel, we will give style to the xlsx spreadsheet
    # Different columns will have different widths, specified as arguments

    #Sort df
    if sort_descending_by is not None:
        df_to_save.sort_values(by=sort_descending_by, ascending=False, inplace=True)

    #Create ExcelWriter instance
    writer = pd.ExcelWriter(saving_path, engine='xlsxwriter')

    # Convert the dataframe to an XlsxWriter Excel object.
    df_to_save.to_excel(writer, sheet_name='Sheet1', index=False)

    # Get the xlsxwriter workbook and worksheet objects to define style
    workbook  = writer.book
    worksheet = writer.sheets['Sheet1']

    #Freeze first row
    worksheet.freeze_panes(1,0)

    # Add a header format.
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1})

    # Write the column headers with the defined format.
    for col_num, value in enumerate(df_to_save.columns.values):
        worksheet.write(0, col_num, value, header_format)

    #Format for all other rows
    workbook_format = workbook.add_format({
      'text_wrap': True,
      'align': 'justify'})

    # Set the column width and format.
    # We will have 3 widths for columns: columns with very small entries (size 10),
    # columns with medium size entries (size 20) and columns with long entries (size 40)
    for (entries_index, size_of_column) in \
        [(short_entries_cols_index,10),(medium_entries_cols_index,20),(long_entries_cols_index,40)]:
        if entries_index:
            for col in entries_index:
                worksheet.set_column(col, col, size_of_column, workbook_format)

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
