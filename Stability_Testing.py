import os
import time
import datetime
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Configuration
PING_INTERVAL = 5  # Ping interval in seconds
LOG_DIR = "C:\\Logs"  # Directory to store logs
GENERAL_LOG_FILE = os.path.join(LOG_DIR, "stability_test_log.txt")
TEST_DURATION = 100  # Test duration: 1 week in seconds

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
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", sta_ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return sta_ip, result.returncode == 0  # Return the IP and reachability status
    except Exception as e:
        print(f"Error pinging {sta_ip}: {e}")
        return sta_ip, False

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
    Check the stability of all STAs concurrently and log the results.
    Track disconnections and reconnections with durations.
    """
    global sta_states

    current_time = datetime.datetime.now()

    # Use ThreadPoolExecutor to ping all STAs concurrently
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(ping_sta, sta_ips))

    for sta_ip, reachable in results:
        if sta_ip not in sta_states:
            sta_states[sta_ip] = {"reachable": True, "last_unreachable_time": None}

        if reachable:
            if not sta_states[sta_ip]["reachable"]:  # STA was previously unreachable
                last_unreachable_time = sta_states[sta_ip]["last_unreachable_time"]
                disconnection_duration = current_time - last_unreachable_time
                reconnection_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                disconnection_time = last_unreachable_time.strftime("%Y-%m-%d %H:%M:%S")

                # Log the disconnection details
                log_message(f"STA {sta_ip} reconnected after being down for {disconnection_duration}.")
                log_disconnection(sta_ip, disconnection_time, reconnection_time, disconnection_duration)

                # Update the state
                sta_states[sta_ip]["reachable"] = True
                sta_states[sta_ip]["last_unreachable_time"] = None
            log_message(f"STA {sta_ip} is reachable.")
        else:
            if sta_states[sta_ip]["reachable"]:  # STA was previously reachable
                sta_states[sta_ip]["reachable"] = False
                sta_states[sta_ip]["last_unreachable_time"] = current_time
                disconnection_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
                log_message(f"STA {sta_ip} is NOT reachable! Disconnection started at {disconnection_time}.")
            log_message(f"STA {sta_ip} is still unreachable.")

def run_test(sta_ips):
    """
    Run the stability test for the specified duration.
    """
    start_time = time.time()
    log_message("Stability test started.")

    while time.time() - start_time < TEST_DURATION:
        check_stability(sta_ips)
        time.sleep(PING_INTERVAL)

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
