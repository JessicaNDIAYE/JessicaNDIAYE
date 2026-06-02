import requests
import json
from datetime import datetime, timedelta
import math
import sys

USERNAME = "JessicaNDIAYE"

# Fetch contributions via GitHub GraphQL API
def fetch_contributions(token):
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"bearer {token}"}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": USERNAME}},
        headers=headers
    )
    data = response.json()
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append(day)
    return days

def count_to_level(count):
    if count == 0: return 0
    if count <= 2: return 1
    if count <= 5: return 2
    if count <= 9: return 3
    return 4

def draw_flower(x, y, level, date_str):
    """Draw a flower SVG at position x,y based on contribution level"""
    if level == 0:
        # Empty spot - tiny dot
        return f'<circle cx="{x+6}" cy="{y+6}" r="1.2" fill="#ebedf0" opacity="0.5"/>'

    # Colors per level
    petal_colors = ["", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
    center_colors = ["", "#f9e4a0", "#f5c842", "#e8a020", "#c97010"]
    
    color = petal_colors[level]
    center = center_colors[level]
    
    # Flower size grows with level
    sizes = [0, 2.5, 3.5, 4.5, 5.5]
    petal_r = sizes[level]
    center_r = petal_r * 0.45
    num_petals = [0, 4, 5, 6, 8][level]
    
    cx, cy = x + 6, y + 6
    petals = ""
    for i in range(num_petals):
        angle = (2 * math.pi / num_petals) * i
        px = cx + math.cos(angle) * petal_r * 1.1
        py = cy + math.sin(angle) * petal_r * 1.1
        petals += f'<ellipse cx="{px:.2f}" cy="{py:.2f}" rx="{petal_r:.2f}" ry="{petal_r*0.6:.2f}" fill="{color}" transform="rotate({math.degrees(angle):.1f},{px:.2f},{py:.2f})" opacity="0.9"/>'
    
    stem = ""
    if level >= 2:
        stem = f'<line x1="{cx}" y1="{cy+center_r:.2f}" x2="{cx}" y2="{cy+petal_r+2:.2f}" stroke="#57a55a" stroke-width="0.8" opacity="0.6"/>'
    
    tooltip = f'<title>{date_str}: {["no","1-2","3-5","6-9","10+"][level]} contributions</title>'
    
    return f'<g>{tooltip}{stem}{petals}<circle cx="{cx}" cy="{cy}" r="{center_r:.2f}" fill="{center}"/></g>'

def generate_svg(days):
    # Group by week
    weeks = []
    week = []
    for day in days:
        week.append(day)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        weeks.append(week)

    cell_size = 13
    padding = 4
    width = len(weeks) * (cell_size + padding) + 60
    height = 7 * (cell_size + padding) + 60

    svg_parts = [f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #57606a; }}
  </style>
  <rect width="{width}" height="{height}" fill="#ffffff" rx="8"/>
  <text x="30" y="20" font-size="11" font-weight="600" fill="#24292f">🌸 Jessica\'s Contribution Garden</text>
''']

    # Day labels
    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    for i, label in enumerate(day_labels):
        if label:
            y_pos = 40 + i * (cell_size + padding) + cell_size // 2
            svg_parts.append(f'  <text x="8" y="{y_pos}" font-size="9">{label}</text>')

    # Month labels
    prev_month = ""
    for wi, week in enumerate(weeks):
        first_day = week[0]
        month = datetime.strptime(first_day["date"], "%Y-%m-%d").strftime("%b")
        if month != prev_month:
            x_pos = 35 + wi * (cell_size + padding)
            svg_parts.append(f'  <text x="{x_pos}" y="34" font-size="9">{month}</text>')
            prev_month = month

    # Flowers
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            x = 35 + wi * (cell_size + padding)
            y = 40 + di * (cell_size + padding)
            level = count_to_level(day["contributionCount"])
            flower = draw_flower(x, y, level, day["date"])
            svg_parts.append(f"  {flower}")

    # Legend
    legend_x = 35
    legend_y = height - 18
    svg_parts.append(f'  <text x="{legend_x}" y="{legend_y}" font-size="9">Less</text>')
    for i in range(5):
        lx = legend_x + 28 + i * (cell_size + 2)
        flower = draw_flower(lx, legend_y - 10, i, "")
        svg_parts.append(f"  {flower}")
    svg_parts.append(f'  <text x="{legend_x + 28 + 5*(cell_size+2) + 2}" y="{legend_y}" font-size="9">More</text>')

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else ""
    days = fetch_contributions(token)
    svg = generate_svg(days)
    with open("contribution-garden.svg", "w") as f:
        f.write(svg)
    print("✅ Garden SVG generated!")
