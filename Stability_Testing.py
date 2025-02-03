import os
import time
import datetime
import subprocess

# Configuration
CHECK_INTERVAL = 5  # Check interval in seconds
LOG_DIR = "C:\\Logs"  # Directory to store logs
GENERAL_LOG_FILE = os.path.join(LOG_DIR, "stability_test_log.txt")
TEST_DURATION = 7 * 24 * 60 * 60   # Test duration: 1 week in seconds

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Dictionary to track the state of each STA
sta_states = {}

def get_sta_ips():
    """
    Prompt the user to provide the IP addresses of all STAs.
    """
    print("Please provide the IP addresses of all STAs (stations) you want to monitor.")
    sta_ips = []
    while True:
        ip = input("Enter an STA IP address (or type 'done' to finish): ").strip()
        if ip.lower() == "done":
            break
        if ip:
            sta_ips.append(ip)
    return sta_ips

def ping_sta(sta_ip):
    """
    Ping a single STA and return True if reachable, False otherwise.
    """
    try:
        # Use the 'ping' command with 1 packet and a timeout of 1 second
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", sta_ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0  # Return True if ping is successful
    except Exception as e:
        print(f"Error pinging {sta_ip}: {e}")
        return False

def log_message(message):
    """
    Log a message to the general log file with a timestamp.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(GENERAL_LOG_FILE, "a") as log:
        log.write(log_entry)
    print(log_entry.strip())  # Print to console as well

def log_disconnection(sta_ip, disconnection_time, reconnection_time, duration):
    """
    Log disconnection details to a separate file for the specific STA.
    """
    sta_log_file = os.path.join(LOG_DIR, f"{sta_ip}_disconnections.log")
    log_entry = (
        f"PC-NAME: {sta_ip}\n"
        f"- Disconnection Time: {disconnection_time}\n"
        f"- Reconnection Time: {reconnection_time}\n"
        f"- Duration: {duration}\n\n"
    )
    with open(sta_log_file, "a") as log:
        log.write(log_entry)

def check_stability(sta_ips):
    """
    Check the stability of all STAs and log the results.
    Track disconnections and reconnections with durations.
    """
    global sta_states

    # Update the states of existing STAs and add new ones
    for sta in sta_ips:
        if sta not in sta_states:
            sta_states[sta] = {"reachable": True, "last_unreachable_time": None}

    # Remove STAs that are no longer in the provided list
    disconnected_stas = [sta for sta in sta_states if sta not in sta_ips]
    for sta in disconnected_stas:
        del sta_states[sta]

    # Check the stability of all connected STAs
    for sta in sta_ips:
        reachable = ping_sta(sta)
        current_time = datetime.datetime.now()

        if reachable:
            if not sta_states[sta]["reachable"]:  # STA was previously unreachable
                # Calculate the duration of disconnection
                last_unreachable_time = sta_states[sta]["last_unreachable_time"]
                disconnection_duration = current_time - last_unreachable_time
                reconnection_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                disconnection_time = last_unreachable_time.strftime("%Y-%m-%d %H:%M:%S")

                # Log the disconnection details
                log_message(f"STA {sta} reconnected after being down for {disconnection_duration}.")
                log_disconnection(sta, disconnection_time, reconnection_time, disconnection_duration)

                # Update the state
                sta_states[sta]["reachable"] = True
                sta_states[sta]["last_unreachable_time"] = None
            log_message(f"STA {sta} is reachable.")
        else:
            if sta_states[sta]["reachable"]:  # STA was previously reachable
                # Record the time when the STA became unreachable
                sta_states[sta]["reachable"] = False
                sta_states[sta]["last_unreachable_time"] = current_time
                disconnection_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                log_message(f"STA {sta} is NOT reachable! Disconnection started at {disconnection_time}.")
            log_message(f"STA {sta} is still unreachable.")

def run_test(sta_ips):
    """
    Run the stability test for the specified duration.
    """
    start_time = time.time()
    log_message("Stability test started.")

    while time.time() - start_time < TEST_DURATION:
        check_stability(sta_ips)
        time.sleep(CHECK_INTERVAL)  # Wait for the specified interval before checking again

    log_message("Stability test completed.")

if __name__ == "__main__":
    # Clear the general log file before starting
    if os.path.exists(GENERAL_LOG_FILE):
        os.remove(GENERAL_LOG_FILE)

    # Step 1: Get STA IP addresses from the user
    print("=== Step 1: Provide STA IP Addresses ===")
    sta_ips = get_sta_ips()
    if not sta_ips:
        print("No STA IP addresses provided. Exiting.")
        exit(1)

    print(f"\nMonitoring the following STAs: {', '.join(sta_ips)}")

    # Step 2: Confirm before starting the stability test
    print("\n=== Step 2: Starting Stability Test ===")
    confirmation = input("Do you want to proceed with the stability test? (yes/no): ").strip().lower()
    if confirmation != "yes":
        print("Test aborted by the user.")
        exit(0)

    # Step 3: Start the stability test
    print("\n=== Stability Test Running ===")
    run_test(sta_ips)
