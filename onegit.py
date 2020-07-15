import colorama
import os
import sys

colorama.init()

try:
    msg = sys.argv[1]
    branch = sys.argv[2]
except:
    print(colorama.Fore.RED + "Usage: onegit [message] [branch]" + colorama.Style.RESET_ALL)
    sys.exit(-1)

def run(cmd):
    print(colorama.Fore.GREEN + "running {}".format(cmd) + colorama.Style.RESET_ALL)

    os.system(cmd)

stage = "git stage ."
run(stage)

commit = "git commit -m \"{}\"".format(msg)
run(commit)

push = "git push -u origin {}".format(branch)
run(push)
