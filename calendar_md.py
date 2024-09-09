#!/usr/bin/env python3
""" Generate a markdown calendar for a given month and year.
    The calendar is generated in a collapsible markdown format.
"""
import calendar
import argparse
from datetime import datetime, date


def generate_calendar_md(
    year,
    month,
    locale="en_US",
    link_style="/backups/%Y/%m/%d",
    output_format="md",
    start_sunday=False,
):

    SUPPORTED_LOCALES = ["en_US"]

    assert 1 <= year <= 99999, "[Error] Invalid year"
    assert 1 <= month <= 12, "[Error] Invalid month"
    assert locale in SUPPORTED_LOCALES, "[Error] Locale is not supported"

    def linkify(year, month, day=1, style=link_style):
        return f"[{day:02}]({datetime(year, month, day).strftime(style)})"

    locale_weekdays = [
        {"en_US": "Mon"},
        {"en_US": "Tue"},
        {"en_US": "Wed"},
        {"en_US": "Thu"},
        {"en_US": "Fri"},
        {"en_US": "Sat"},
        {"en_US": "Sun"},
    ]

    weekdays = [locale_weekdays[i][locale] for i in range(6)]
    weekdays = (
        [locale_weekdays[6][locale]] + weekdays
        if start_sunday
        else weekdays + [locale_weekdays[6][locale]]
    )

    calendar.setfirstweekday(calendar.SUNDAY if start_sunday else calendar.MONDAY)
    raw_calendar = calendar.monthcalendar(year, month)

    if output_format == "csv":
        output = (
            ",".join(weekdays)
            + "\n"
            + "\n".join(
                [
                    ",".join(
                        [
                            linkify(year=year, month=month, day=d) if d != 0 else ""
                            for d in w
                        ]
                    )
                    for w in raw_calendar
                ]
            )
        )

    elif output_format == "md":
        width = len(linkify(year=year, month=month, day=10))
        output = (
            "| "
            + " | ".join([day.ljust(width, " ") for day in weekdays])
            + " |\n"
            + ("| " + "-" * width + " ") * 7
            + "|\n"
            + "\n".join(
                [
                    "| "
                    + " | ".join(
                        [
                            (
                                linkify(year=year, month=month, day=d).ljust(width, " ")
                                if d != 0
                                else "".ljust(width, " ")
                            )
                            for d in w
                        ]
                    )
                    + " |"
                    for w in raw_calendar
                ]
            )
        )
        month_text = date(1900, month, 1).strftime("%B")
        markdown_text = f"""
<details>
    <summary>{month_text} {year}</summary>

{ output }

</details>
        """
    return markdown_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates calendar of given month, year in markdown format"
    )

    curr_year = datetime.today().year
    curr_month = datetime.today().month
    DEFAULT_LINK_STYLE = "/backups/%Y/%m/%d"
    DEFAULT_LOCALE = "en_US"
    DEFAULT_FORMAT = "md"

    parser.add_argument(
        "--year",
        type=int,
        default=curr_year,
        help="Integer specifying the year. Default value is the current year.",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=curr_month,
        help="Integer specifying the month. Default value is the current month.",
    )
    parser.add_argument(
        "--locale",
        type=str,
        default=DEFAULT_LOCALE,
        help='String specifying the locale. Default value is "en_US". ',
    )
    parser.add_argument(
        "--link_style",
        type=str,
        default=DEFAULT_LINK_STYLE,
        help='String specifying the style of the hyperlink. Default value is "/backups/%Y/%m/%d".',
    )
    parser.add_argument(
        "--format",
        type=str,
        default=DEFAULT_FORMAT,
        help='String specifying the output format. Default value is "md". "csv" is also available.',
    )
    parser.add_argument(
        "--start_sunday",
        default=False,
        action="store_true",
        help="Flag that specifys whether a week starts from Sunday.",
    )

    args = parser.parse_args()
    text = generate_calendar_md(
        args.year,
        args.month,
        args.locale,
        args.link_style,
        args.format,
        args.start_sunday,
    )
    with open("calendar_test.md", "w") as f:
        f.write(text)
    print("Wrote to calendar_test.md")
