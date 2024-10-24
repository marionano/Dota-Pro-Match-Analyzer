import requests
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk  # For dropdown menus
import webbrowser
import pyperclip
from datetime import datetime, timezone
import time  # For adding a delay

# Function to fetch and analyze pro match stats with year filtering and pagination
def get_pro_match_stats():
    selected_year = int(year_var.get())  # Get the selected year
    
    url = 'https://api.opendota.com/api/proMatches'
    total_game_time = 0
    num_matches = 0
    longest_game_time = 0
    shortest_game_time = float('inf')
    long_games_count = 0
    medium_games_count = 0
    short_games_count = 0
    total_kills = 0
    radiant_kills = 0
    dire_kills = 0
    short_kills = 0
    medium_kills = 0
    long_kills = 0
    longest_game_id = None
    shortest_game_id = None
    start_dates = []
    last_match_id = None

    # Continue fetching matches until no more matches fit the year
    while True:
        params = {}
        if last_match_id:
            params['less_than_match_id'] = last_match_id
        
        response = requests.get(url, params=params)
        
        if response.status_code == 429:
            # Wait if rate-limited
            time.sleep(2)  # Wait for 2 seconds before retrying
            continue
        
        response.raise_for_status()
        pro_matches = response.json()

        if not pro_matches:
            break

        for match in pro_matches:
            match_time = datetime.fromtimestamp(match['start_time'], timezone.utc)
            match_year = match_time.year

            # Filter matches by the selected year
            if match_year == selected_year:
                num_matches += 1
                game_time = match['duration']
                total_game_time += game_time

                # Calculate kills
                total_kills += match['radiant_score'] + match['dire_score']
                radiant_kills += match['radiant_score']
                dire_kills += match['dire_score']

                # Longest and shortest games
                if game_time > longest_game_time:
                    longest_game_time = game_time
                    longest_game_id = match['match_id']
                if game_time < shortest_game_time:
                    shortest_game_time = game_time
                    shortest_game_id = match['match_id']

                # Categorize games by duration and count kills
                if game_time < 1800:  # Short games (< 30 minutes)
                    short_games_count += 1
                    short_kills += match['radiant_score'] + match['dire_score']
                elif 1800 <= game_time <= 2400:  # Medium games (30 to 40 minutes)
                    medium_games_count += 1
                    medium_kills += match['radiant_score'] + match['dire_score']
                else:  # Long games (> 40 minutes)
                    long_games_count += 1
                    long_kills += match['radiant_score'] + match['dire_score']

                # Collect start dates
                start_dates.append(match['start_time'])

            # Update the last_match_id for pagination
            last_match_id = match['match_id']

        # If no more matches fit the selected year, stop fetching
        if match_year < selected_year:
            break

    if num_matches == 0:
        messagebox.showinfo("No Data", f"No matches found for the year {selected_year}.")
        return

    # Calculating averages
    average_game_time_minutes = (total_game_time / num_matches) / 60
    average_total_kills = total_kills / num_matches
    average_radiant_kills = radiant_kills / num_matches
    average_dire_kills = dire_kills / num_matches

    # Averages for each category
    short_avg_kills = short_kills / short_games_count if short_games_count else 0
    medium_avg_kills = medium_kills / medium_games_count if medium_games_count else 0
    long_avg_kills = long_kills / long_games_count if long_games_count else 0

    # Percentages of long and short games
    short_game_percentage = (short_games_count / num_matches) * 100
    medium_game_percentage = (medium_games_count / num_matches) * 100
    long_game_percentage = (long_games_count / num_matches) * 100

    # Convert start times to human-readable dates and get the range
    start_dates = [datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%d') for ts in start_dates]
    date_range = f"{min(start_dates)} to {max(start_dates)}"

    # Display results
    results = (
        f"Date range of matches analyzed: {date_range}\n"
        f"Number of games analyzed: {num_matches}\n"
        f"Average game time: {average_game_time_minutes:.2f} minutes\n"
        f"Longest game: {longest_game_time / 60:.2f} minutes (Match ID: {longest_game_id})\n"
        f"Shortest game: {shortest_game_time / 60:.2f} minutes (Match ID: {shortest_game_id})\n"
        f"Short games (<30 mins): {short_games_count} ({short_game_percentage:.2f}%) | Avg kills: {short_avg_kills:.2f}\n"
        f"Medium games (30-40 mins): {medium_games_count} ({medium_game_percentage:.2f}%) | Avg kills: {medium_avg_kills:.2f}\n"
        f"Long games (>40 mins): {long_games_count} ({long_game_percentage:.2f}%) | Avg kills: {long_avg_kills:.2f}\n"
        f"Average total kills: {average_total_kills:.2f}\n"
        f"Average Radiant kills: {average_radiant_kills:.2f}\n"
        f"Average Dire kills: {average_dire_kills:.2f}"
    )

    display_results(results, longest_game_id, shortest_game_id)

# Function to display results in the GUI
def display_results(results, longest_game_id, shortest_game_id):
    text_area.config(state='normal')  # Make the text box writable
    text_area.delete(1.0, tk.END)  # Clear previous results
    text_area.insert(tk.END, results)
    text_area.config(state='disabled')  # Make it read-only again

    # Update clickable match links
    longest_link.config(text=f"View Longest Match: {longest_game_id}", command=lambda: open_match_link(longest_game_id))
    shortest_link.config(text=f"View Shortest Match: {shortest_game_id}", command=lambda: open_match_link(shortest_game_id))

# Function to open the match link in a browser
def open_match_link(match_id):
    match_url = f"https://www.opendota.com/matches/{match_id}"
    webbrowser.open(match_url)

# Function to copy all stats to clipboard
def copy_all_stats():
    pyperclip.copy(text_area.get(1.0, tk.END))
    messagebox.showinfo("Copied", "All stats copied to clipboard.")

# Create the main application window
root = tk.Tk()
root.title("Dota Pro Match Analyzer")
root.geometry("700x600")  # Set window size to avoid scrolling

# Dropdown menu for year selection
years = [2020, 2021, 2022, 2023, 2024]
year_var = tk.StringVar(value="2020")

year_label = tk.Label(root, text="Select Year:")
year_label.pack(pady=5)
year_menu = ttk.Combobox(root, textvariable=year_var, values=years)
year_menu.pack(pady=5)

# Button to fetch stats
analyze_button = tk.Button(root, text="Fetch Pro Match Stats", command=get_pro_match_stats)
analyze_button.pack(pady=10)

# Text box to display results 
text_area = tk.Text(root, wrap=tk.WORD, width=80, height=20)
text_area.pack(padx=10, pady=10)
text_area.config(state='disabled')  # Make it read-only

# Create clickable buttons for the match IDs
longest_link = tk.Button(root, text="View Longest Match", fg="blue", cursor="hand2")
longest_link.pack(pady=5)

shortest_link = tk.Button(root, text="View Shortest Match", fg="blue", cursor="hand2")
shortest_link.pack(pady=5)

# Button to copy all stats to clipboard
copy_stats_button = tk.Button(root, text="Copy All Stats", command=copy_all_stats)
copy_stats_button.pack(pady=5)

# Start the Tkinter event loop
root.mainloop()
