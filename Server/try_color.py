from colorama import Fore, Style, init
from time import sleep

e = "hello"

while True:
    print(f"{Fore.RED} {e} {Style.RESET_ALL}")

    sleep(2)
