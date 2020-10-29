# TODO: 

v - Recognize completion of rows in progress

- Redesign filters - especially FilterListWidget
v   > Improve performance for large tables
v   > Use delegate or model's data method to populate the filter list widget
  > Remove the last 'empty' data row from the filters

- Implement Undo/Redo

- Implement editing multiple cells at the same time

- Implement statusbar or maybe some snackbar messaging system

- Memorize selections, so that insert row works on consecutive rows, 
  if they are selected individually.

- When double clicking cell in nullable column, editor must take focus 
  (and perhaps a selecting current data should be the default)

- Investigate entering edit mode, when user starts typing over cell

- Experiment with 'formula bar' to make multi-cell editing easier

# Known BUGS:

- after column resizing, cursor remains in 'resize' mode, 
  and not changing the mouse pointer back to the normal arrow
  
- clicking filter button when filter menu is visible, should close the menu, now it's
  showing new menu

