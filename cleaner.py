import datetime

raw_time_start = 11
raw_line_start = 27
time_end = 9
line_start = 17

def clean_ports_from_IP(text: str):
    IP_pos = text.find("[", time_end)
    port_pos = text.find(":", IP_pos)
    port_end_pos = text.find("]", port_pos)
    if port_pos != -1:
        port = text[port_pos:port_end_pos]
        if port[1:].isnumeric() and port[0] == ":":
            text = text.replace(port, "")
    return text

def check_for_IP_at_index(text: str, index: int):
    IP_index = text.find("/", time_end)
    if IP_index != -1:
        IP_str = text[IP_index:IP_index + 3]
        if IP_str[1:].isnumeric() and IP_str[0] == "/":
            return IP_index == index
    return False

def clean_login(text: str, raw_text: str):
    coords = []

    username_index = time_end
    username_end_index = text.find(" ", username_index)
    username_IP_end_index = text.find("]", username_index) + 1

    coord_start_index = text.find("(", time_end) + 1
    for i in range(3):
        coord_end = text.find(".", coord_start_index)
        coords.append(text[coord_start_index:coord_end])
        coord_start_index = text.find(" ", coord_end) + 1

    username_IP = text[username_index:username_IP_end_index]
    username_IP = username_IP.replace("/", "")

    username = text[username_index:username_end_index]
    year = int(raw_text[:4])
    month = int(raw_text[5:7])
    day = int(raw_text[8:10])
    hour = int(text[:2])
    minute = int(text[3:5])
    second = int(text[6:8])
    players_login_times[username] = datetime.datetime(year = year, month = month, day = day, hour = hour, minute = minute, second = second)

    clean_text = text[:time_end] + "  LOGIN " + username_IP + " at ({},{},{})\n".format(coords[0], coords[1], coords[2])
    return clean_text

def clean_logout(text: str, raw_text: str):
    username_index = time_end
    username_end_index = text.find(" ", username_index)
    username = text[username_index:username_end_index]

    year = int(raw_text[:4])
    month = int(raw_text[5:7])
    day = int(raw_text[8:10])
    hour = int(text[:2])
    minute = int(text[3:5])
    second = int(text[6:8])
    current_time = datetime.datetime(year = year, month = month, day = day, hour = hour, minute = minute, second = second)
    time_spent = current_time - players_login_times[username]
    time_spent = str(time_spent)
    if time_spent[0] == "0":
        time_spent = time_spent[2:]

    players_login_times.pop(username)

    clean_text = text[:time_end] + " LOGOUT " + username + " after {} minutes\n".format(time_spent)
    return clean_text

def clean_chat(text: str):
    opening_bracket_pos = text.find("<", line_start)
    closing_bracket_pos = text.find(">", line_start)
    if opening_bracket_pos != -1 and closing_bracket_pos != -1:
        # get longest name and center conversation around that
        longest_name = 0
        for player_name in players_login_times:
            length = player_name.__len__()
            if longest_name < length:
                longest_name = length

        opening_bracket_garbage = text[opening_bracket_pos:opening_bracket_pos + 4]
        closing_bracket_garbage = text[closing_bracket_pos - 3:closing_bracket_pos + 2]

        username = text[opening_bracket_pos:closing_bracket_pos + 2]
        username = username.replace(opening_bracket_garbage, "")
        username = username.replace(closing_bracket_garbage, "")
        missing_length = longest_name - username.__len__()

        compensation = ""
        for i in range(missing_length):
            compensation = compensation.__add__(" ")

        text = text.replace(opening_bracket_garbage, "- " + compensation)
        text = text.replace(closing_bracket_garbage, ": ")
    return text


filter = [
    "Unknown console command.",
    "Starting NSSS server",
    "Loading properties",
    "Starting Minecraft server on",
    "WARNING",
    "Preparing level",
    "Preparing start region for",
    "For help, type",
    "Stopping server",
    "Saving chunks",
    "Forcing save",
    "Save complete",
    "Stopping the server",
    "Uwaga",
    "Maxcraft",
    "Disconnecting"
]

print("Opening files...")

raw_log = open('server.log', 'r')
cleaned_log = open('cleaned.log', 'w')

raw_lines = raw_log.readlines()
cleaned_lines = []

print("Begin filtration")

players_login_times = {}
day_timestamp = ""
iteration = 0
for line in raw_lines:
    # check if the line should be filtered out
    found_illegal = False
    for item in filter:
        low_line = line.lower()
        if low_line.__contains__(item.lower()) or check_for_IP_at_index(low_line, raw_line_start):
            found_illegal = True

    # what should be done if it's not filtered out
    if not found_illegal:
        if day_timestamp != line[:raw_time_start - 1]:
            day_timestamp = line[:raw_time_start - 1]
            cleaned_lines.append("========================================== {} ==========================================\n".format(day_timestamp))

        clean_line = line[raw_time_start:]
        clean_line = clean_line.replace("[INFO] ", "")
        clean_line = clean_ports_from_IP(clean_line)

        if clean_line.__contains__("logged in with entity id"):
            clean_line = clean_login(clean_line, line)
        elif clean_line.__contains__("lost connection"):
            clean_line = clean_logout(clean_line, line)
        else:
            clean_line = clean_line[:time_end] + "        " + clean_line[time_end:]
            clean_line = clean_chat(clean_line)

        cleaned_lines.append(clean_line)

        iteration += 1

print("Filter completed!")
print("Writing new file")

cleaned_log.writelines(cleaned_lines)
cleaned_log.close()

print("All done!")