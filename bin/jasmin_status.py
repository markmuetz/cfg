import requests
import requests
import json
import textwrap

URL = "https://raw.githubusercontent.com/cedadev/ceda-status/main/status.json"

STATUS_WIDTH = 11
MSG_WIDTH = 80


def fetch_status(url):
    response = requests.get(url)
    data = response.json()
    return data


def format_status(data):
    print('\033[36m', end='')
    print("********************************************************************************")
    print("                                Latest Incidents                                ")
    print("********************************************************************************")
    print('\033[0m', end='')

    for item in data:
        status = item['status']

        # Define color codes
        if status == "resolved":
            color = "\033[32m"  # Green
        elif status == "degraded":
            color = "\033[33m"  # Yellow
        else:
            color = "\033[0m"   # Default (white)

        print(f"[{color}{status}\033[0m] Services: {item['affectedServices']}")
        print(textwrap.fill(f"{item['summary']}", initial_indent=' ' * STATUS_WIDTH))
        print("")

        for update in item['updates']:
            update_date = update['date']
            details_lines = textwrap.wrap(
                update['details'],
                width=MSG_WIDTH - STATUS_WIDTH - len(update_date) - 1
            )
            date_filler = ' ' * (len(update_date) + 1)
            date_lines = (
                [' ' * STATUS_WIDTH + update_date + ' '] +
                [' ' * (STATUS_WIDTH + len(update_date) + 1)] * (len(details_lines) - 1)
            )
            for l1, l2 in zip(date_lines, details_lines):
                print(l1 + l2)
        print("————————————————————————————————————————————————————————————————————————————————")


def main():
    data = fetch_status(URL)
    format_status(data)


if __name__ == "__main__":
    main()

