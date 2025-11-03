# NASA API Data Explorer README

This project is a Python script for exploring NASA APIs, including APOD and Curiosity rover images.

## Flowchart

Below is a simplified flowchart of the script's structure and CLI flow:

NASA API Data Explorer Flowchart (Simplified)

                   +-------------------+
                   |       Start       |
                   +-------------------+
                             |
                             v
                   +-------------------+
                   | Load .env & Config|
                   +-------------------+
                             |
                             v
                   +-------------------+
                   |   Main Menu CLI   |
                   | Display Options:  |
                   | 1: APOD           |
                   | 2: Curiosity Lib  |
                   | 3: Curiosity RSS  |
                   | Q: Quit           |
                   +-------------------+
                             |
                             v
                   +-------------------+
                   |   Input Choice    |
                   +-------------------+
                             |
              +--------------+--------------+--------------+
              |                             |              |
              v                             v              v
      +---------------+             +---------------+     +---------------+
      | Choice == "1" |             | Choice == "2" |     | Choice == "3" |
      +---------------+             +---------------+     +---------------+
              |                             |              |
              v                             v              v
      +---------------+             +---------------+     +---------------+
      | fetch_apod()  |             | Input: cam,   |     | Input: cam,   |
      | - safe_request|             | year_start,   |     | start_date,   |
      | - Print info  |             | year_end      |     | end_date      |
      | - Optional    |             +---------------+     +---------------+
      |   download    |                     |                      |
      +---------------+                     v                      v
              |                     +---------------+      +---------------+
              |                     | fetch_curiosity|      | fetch_rss_    |
              |                     | _images_via_  |      | recent_by_    |
              |                     | library()     |      | filters()     |
              |                     | - Build params|      | - Loop pages  |
              |                     | - safe_request|      | - If empty,   |
              |                     | - Extract &   |      |   fallback to |
              |                     |   print items |      |   library     |
              |                     | - Optional    |      | - Filter &    |
              |                     |   plot        |      |   print       |
              |                     +---------------+      | - Optional    |
              |                                            |   plot        |
              |                                            +---------------+
              |                             |              |
              +--------------+--------------+--------------+
                             |
                             v
                   +-------------------+
                   | Invalid Choice?   |
                   | Print error &     |
                   | back to menu      |
                   +-------------------+
                             |
                    (Loop until Q)
                             |
                             v
                   +-------------------+
                   |        End        |
                   +-------------------+

Note: Helper functions like safe_request() handle retries and errors.
save_image() downloads images if chosen.
Plots use pandas/matplotlib for summaries.

## Usage

Run the script with `python script_name.py` (replace with your actual filename). Follow the menu prompts.

## Requirements

- Python 3.x
- Libraries: requests, pandas, matplotlib, python-dotenv
- NASA API key in a `.env` file (optional; defaults to demo key).

For more details, see the source code.
