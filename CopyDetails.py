class CopyDetails:

    src = None  # Source file or directory
    dest = None  # Destination file or directory

    init_mod_timestamp = None  # Timestamp of source before any operations occur
    pre_copy_mod_timestamp = None  # Tiemstamp of source immediately before copy (only if a copy takes place)
    last_mod_timestamp = None  # Timestamp of the previous copy attempt

    start_time = None  # Start time of the copy
    end_time = None  # End tome of the copy

    start_timestamp = None  # Timestamp at the start of the copy
    end_timestamp = None  # Timestamp at the end of the copy

    skipped = None  # Whether the copy was skipped
    copy_result = None  # Result of the copy
    result = None  # Overall result
    code = None  # Code for result (see constants.py)