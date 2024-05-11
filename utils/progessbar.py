def print_progress(current_step, max_steps, bar_length=80, existing_bar=None):
    progress = current_step / max_steps
    num_blocks = int(progress * bar_length)
    bar = "[" + "#" * num_blocks + " " * (bar_length - num_blocks) + "]"
    percent_complete = progress * 100

    if existing_bar:
        print(f"\rProgress: {bar} {percent_complete:.2f}%", end="")
    else:
        print(f"Progress: {bar} {percent_complete:.2f}%")
