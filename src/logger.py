"""src/logger.py — Colored terminal output (same as original)"""

class Logger:
    CYAN  = '\033[96m'
    GREEN = '\033[92m'
    YELLOW= '\033[93m'
    RED   = '\033[91m'
    BOLD  = '\033[1m'
    DIM   = '\033[2m'
    RESET = '\033[0m'

    def header(self, msg):
        print(f"\n{self.BOLD}{self.CYAN}{'='*54}{self.RESET}")
        print(f"{self.BOLD}{self.CYAN}  {msg}{self.RESET}")
        print(f"{self.BOLD}{self.CYAN}{'='*54}{self.RESET}\n")

    def info(self, msg):    print(f"  {self.DIM}{msg}{self.RESET}")
    def success(self, msg): print(f"  {self.GREEN}✓ {msg}{self.RESET}")
    def warn(self, msg):    print(f"  {self.YELLOW}⚠ {msg}{self.RESET}")
    def error(self, msg):   print(f"  {self.RED}✗ {msg}{self.RESET}")
    def debug(self, msg):   print(f"  {self.DIM}› {msg}{self.RESET}")
