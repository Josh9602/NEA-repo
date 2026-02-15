def validate_spinbox_integer(value, minimum, maximum):
    """
    Validate spinbox input - only allow integers within range.
    Called on every keystroke to prevent invalid input.
    
    Args:
        value: Current text in spinbox
        minimum: Minimum allowed value
        maximum: Maximum allowed value
    
    Returns:
        True if valid, False to block the keystroke
    """
    if value == "":
        return True  # Allow empty during editing
    
    try:
        number = int(value)
        return minimum <= number <= maximum
    except ValueError:
        return False  # Block non-integer input

def create_spinbox_fixer(spinbox_variable, minimum, maximum, default):
    """
    Create a function that auto-corrects spinbox values when focus is lost.
    If value is too low, sets to minimum. If too high, sets to maximum.
    
    Args:
        spinbox_variable: The IntVar or StringVar connected to spinbox
        minimum: Minimum allowed value
        maximum: Maximum allowed value
        default: Default value if current value is invalid
    
    Returns:
        Function that can be bound to FocusOut event
    """
    def fix_value(event=None):
        try:
            current_value = spinbox_variable.get()
            
            if current_value < minimum:
                spinbox_variable.set(minimum)
            elif current_value > maximum:
                spinbox_variable.set(maximum)
        except:
            # If something went wrong, reset to default
            spinbox_variable.set(default)
    
    return fix_value