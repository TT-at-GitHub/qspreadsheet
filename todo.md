# TODO: 

v - Recognize completion of rows in progress

# FILTERS: 
    
    v   -- Improve performance for large tables
    v   -- Use delegate or model's data method to populate the filter list widget
    v   -- Remove the last 'empty' data row from the filters
    v   -- update filter button's icon when filtering
    v   -- Add `Clear filter From ... (column name)` to remove the filter from current column, not the entire filter
    v   -- `Clear filter` to update filter icon for all columns

    -- The line edit in the list filter action widget to take focus, when the menu is shown  
    -- Implement on_rows_inserted/removed in the SortFilterProxyModel and
        allow remove/add rows when the data is filtered
    -- Redesign filters - especially FilterListWidget

# SORTING: 
   -- Create custom sorting on the model to not sort the virtual bottom row

# TABLE
  -- Deal with empty tables. For example:
      typing into the virtual bottom row in an empty table adds row, but
      won't let you delete it

  - allow updating table's mutable state at runtime

  - Implement Undo/Redo

  - Memorize selections, so that insert row works on consecutive rows, 
    if they are selected individually.

  - Implement editing multiple cells at the same time

# OTHER
  - Address all FIXME lines

  - Implement statusbar or maybe some snackbar messaging system

  - Investigate using paint in delegates, instead of display_data

  - Investigate making all delegate editors a line edits with validators

  - When double clicking cell in nullable column, editor must take focus 
    (and perhaps a selecting current data should be the default)

  - Investigate entering edit mode, when user starts typing over cell

  - Experiment with 'formula bar' to make multi-cell editing easier

# Known BUGS:

- after column resizing, cursor remains in 'resize' mode, 
  and not changing the mouse pointer back to the normal arrow
  
- clicking filter button when filter menu is visible, should close the menu, now it's
  showing new menu

- for large filter lists, marking a checkbox, scrolls the list to near the top
