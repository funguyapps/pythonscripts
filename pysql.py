import argparse
import os
from rich.traceback import install
from rich.console import Console
from rich.table import Column, Table
from rich import box
import sqlite3


def main():
    # set rich as default backtrace logger
    install()

    console = Console()

    # set up parser for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", metavar="mode", type=str, help="The type of operation to be performed on the database: create, delete, or access")
    parser.add_argument("source", metavar="source", type=str, help="The path to the database file to be accessed or created")
    parser.add_argument("--query", type=str, help="If accessing the database, this must be provided as the query to be run")
    parser.add_argument("--infinite", action="store_true", help="Set this flag to open a session to the database to run multiple queries")
    parser.add_argument("--embedded", action="store_true", help="Set this flag to only output JSON for use in other applications")
    args = vars(parser.parse_args())

    # main logic occurs -- split based on mode
    mode = args["mode"].lower()
    source = args["source"]
    if mode == "create":
        create(source)
    elif mode == "delete":
        delete(source, console)
    elif mode == "access":
        access(source, args["query"], args["infinite"], args["embedded"], console)


def create(db):
    connection = sqlite3.connect(db)
    connection.close()


def delete(db, console):
    try:
        # the file must be a database file
        extension = os.path.splitext(db)[1]
        if extension != ".db":
            console.print("[reverse red]Error:[/reverse red] %s not a valid database file" % db)
            return
        
        os.remove(db)
    except FileNotFoundError:
        console.print("[reverse red]Error:[/reverse red] Database file %s not found" % db)


def access(db, query, infinite, embedded, console):
    connection = sqlite3.connect(db)
    # only enter infinite mode if not in embedded mode -- embedded trumps all
    if infinite and not embedded:
        while True:
            query = console.input("[bold green]SQL query to run (q to quit):[/bold green] ")
            if query.lower() == "q":
                break
            run_query(connection, query, console, embedded=False)
    else: # only running one query
        run_query(connection, query, console, embedded)

    connection.close()


def run_query(connection, query, console, embedded):
    try:
        # special logic for outputting select results
        if query.lower().startswith("select"):
             # run the query to get the data
            cursor = connection.execute(query)
            if embedded: # output json
                output_embedded(cursor)
            else: # human-readable output
                output_default(cursor, console)
        # if the query is not a select, no need to output anything
        else:
            connection.execute(query)
            connection.commit()
    # if there is some SQL error, output it cleanly
    except sqlite3.OperationalError as error:
        console.print("[reverse red]SQL Error:[/reverse red] %s" % error)


def output_default(cursor, console):
    # set up the table
    table = Table(show_header=True, header_style="bold green")

    # set headers via the connection's descriptions
    headers = next(zip(*cursor.description))
    for title in headers:
        table.add_column(title, justify="center")

    # finally, set all the content
    for row in cursor:
        # have to modify the content, so list the tuple
        row = list(row)
        # go through and make sure everything is a string
        for i, field in enumerate(row):
            row[i] = str(field)

        # actually add the row to the tuple via destructuring the list
        table.add_row(*row)

    console.print(table)


def output_embedded(cursor):
    # set headers via the connection's descriptions
    headers = next(zip(*cursor.description))

    # default Python JSON parser cannot handle the complex object this creates
    # so it has to be manually created via string building
    # start the process with the bracket -- it's an array of objects
    json_str = "[ "

    for row in cursor:
        # create a new object in the array for each row
        json_str += "{ "
        # for each column in the row
        for i, field in enumerate(row):
            key = "\"%s\"" % headers[i]

            value = ""
            # maintain JS number types as are -- convert everything else to str
            if type(field) is int or type(field) is float:
                value = field
            else:
                value = "\"%s\"" % field
            # add the column name & value to the object
            json_str += "%s: %s, " % (key, value)

        # complete the object
        json_str = remove_comma(json_str)
        json_str += " }, "

    # complete the json string
    json_str = remove_comma(json_str)
    json_str += " ]"

    # output JSON to stdout for consumption by other applications
    print(json_str)


def remove_comma(in_string):
    # this seems inefficient -- it returns a string slice from the beginning
    # to the second to last char in the string in order to remove the trailing comma
    return in_string[0:len(in_string) - 2]

if __name__ == "__main__":
    main()
